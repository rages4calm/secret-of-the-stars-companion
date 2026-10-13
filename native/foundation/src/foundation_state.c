/* Local clean-USA fixture schema, tied to the pinned runtime and execution policy.
 * Guest hardware alone cannot resume the beam driver's native/interpreter CPU.
 * This is a build-specific checkpoint, not a portable campaign-save format. */
#include "foundation_state.h"
#include "foundation_wide.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "beam_frame_driver.h"
#include "snes/saveload.h"
#include "snes/snes.h"
#include "snes/ppu.h"
#include <string.h>

#define FOUNDATION_MAGIC 0x53544F53u
#define FOUNDATION_VERSION 3u
extern Snes *g_snes;
static uint32_t loaded_pc, loaded_wai;
static bool loaded_valid;
static uint32_t loaded_schema;
static uint64_t loaded_audio_clock[4];
/* Generic PPU snapshots omit VRAM access latches. Persist them explicitly;
 * never reconstruct a partially completed port transfer from final VRAM. */
static uint32_t loaded_vram_port[2];
static bool ValidVramPort(const uint32_t port[2]) {
  unsigned increment = (port[1] >> 16) & 255;
  return !(port[1] & 0xff00fcfeu) &&
         (increment == 1 || increment == 32 || increment == 128);
}

const char *FoundationStateIdentity(void) { return "sots-clean-foundation-v1"; }

void FoundationStateSave(SaveLoadInfo *sli) {
  uint32_t header[2] = {FOUNDATION_MAGIC, FOUNDATION_VERSION};
  uint32_t position[2];
  snes_beam_frame_driver_get_position(&position[0], &position[1]);
  sli->func(sli, header, sizeof(header));
  RtlSaveExecutionState(sli);
  uint64_t audio_clock[4];
  RtlGetAudioFrameClock(audio_clock);
  sli->func(sli, audio_clock, sizeof(audio_clock));
  const Ppu *ppu = g_snes->ppu;
  uint32_t vram_port[2] = {
    ppu->vramPointer | (uint32_t)ppu->vramReadBuffer << 16,
    (uint32_t)ppu->vramIncrementOnHigh | (uint32_t)ppu->vramRemapMode << 8 |
      (uint32_t)ppu->vramIncrement << 16
  };
  sli->func(sli, vram_port, sizeof(vram_port));
  sli->func(sli, position, sizeof(position));
}

void FoundationStateLoad(SaveLoadInfo *sli, uint32_t version) {
  /* Extra-state reads, including failed reads, cannot retain task ancestry.
   * The common load entry also cancels it before any guest-memory mutation. */
  cpu_source_suspend_reset(CPU_SOURCE_SUSPEND_LOAD_BEGIN);
  (void)version;
  uint32_t header[2] = {0}, position[2] = {0};
  loaded_valid = false;
  sli->func(sli, header, sizeof(header));
  if (header[0] != FOUNDATION_MAGIC || (header[1] < 1 || header[1] > FOUNDATION_VERSION) ||
      !RtlLoadExecutionState(sli)) {
    RtlStateStreamFail(sli);
    return;
  }
  loaded_schema = header[1];
  if (loaded_schema >= 2) sli->func(sli, loaded_audio_clock, sizeof(loaded_audio_clock));
  if (loaded_schema >= 3) {
    sli->func(sli, loaded_vram_port, sizeof(loaded_vram_port));
    if (!ValidVramPort(loaded_vram_port)) {
      RtlStateStreamFail(sli);
      return;
    }
  }
  sli->func(sli, position, sizeof(position));
  if (position[0] > 0xffffffu || position[1] > 1u) {
    RtlStateStreamFail(sli);
    return;
  }
  loaded_pc = position[0]; loaded_wai = position[1]; loaded_valid = true;
}

void FoundationStateApply(uint32_t version) {
  (void)version;
  if (!loaded_valid) return;
  RtlApplyExecutionState();
  if (loaded_schema >= 2) RtlSetAudioFrameClock(loaded_audio_clock);
  else RtlRecoverLegacyAudioFrameClock();
  if (loaded_schema >= 3) {
    Ppu *ppu = g_snes->ppu;
    ppu->vramPointer = (uint16_t)loaded_vram_port[0];
    ppu->vramReadBuffer = (uint16_t)(loaded_vram_port[0] >> 16);
    ppu->vramIncrementOnHigh = (loaded_vram_port[1] & 1) != 0;
    ppu->vramRemapMode = (uint8_t)(loaded_vram_port[1] >> 8);
    ppu->vramIncrement = (uint8_t)(loaded_vram_port[1] >> 16);
  }
  snes_beam_frame_driver_set_position(loaded_pc, loaded_wai);
  /* Host terrain/actor lineage is never serialized as guest state. Wait for a
   * fresh qualified OAM packet after every cold/rollback restore. */
  FoundationWideReset();
  loaded_valid = false;
}

typedef struct { SaveLoadInfo base; size_t size; } Counter;
static void CountBytes(SaveLoadInfo *sli, void *data, size_t size) {
  (void)data;
  ((Counter *)sli)->size += size;
}
bool FoundationStatePreflight(const void *data, size_t size) {
  uint32_t version, header[2], position[2];
  size_t guest = RtlSnapshotGuestSize(&version);
  Counter count = {{&CountBytes, NULL}, 0};
  FoundationStateSave(&count.base);
  if (size < guest + sizeof(header)) return false;
  memcpy(header, data, sizeof(header));
  if (header[1] != version) return false;
  memcpy(header, (const uint8_t *)data + guest, sizeof(header));
  memcpy(position, (const uint8_t *)data + size - sizeof(position), sizeof(position));
  bool layout = (header[1] == FOUNDATION_VERSION && size == guest + count.size) ||
                (header[1] == 2 && size == guest + count.size - sizeof(loaded_vram_port)) ||
                (header[1] == 1 && size == guest + count.size - sizeof(loaded_audio_clock) - sizeof(loaded_vram_port));
  if (layout && header[1] >= 3) {
    uint32_t port[2];
    memcpy(port, (const uint8_t *)data + size - sizeof(position) - sizeof(port), sizeof(port));
    if (!ValidVramPort(port)) return false;
  }
  return header[0] == FOUNDATION_MAGIC && layout &&
         position[0] <= 0xffffffu && position[1] <= 1u;
}
