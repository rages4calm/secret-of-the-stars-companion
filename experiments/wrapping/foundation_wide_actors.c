/* Validated field draw-record cache. No guest reads through bus helpers, writes,
 * opcode redirects, actor activation or clock changes. Metadata becomes live
 * only with the original complete OAM packet, never at producer-frame time. */
#include "foundation_wide_actors.h"
#include "foundation_field.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "sha256.h"
#include "snes/cart.h"
#include "snes/dma.h"
#include "snes/interp_bridge.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

extern Snes *g_snes;
extern Ppu *g_ppu;
enum { kParty = 5, kRegular = 19, kAppendRegular = 17, kActors = kParty + kRegular,
       kPieces = kActors * 4, kPacketBytes = 544 };
typedef struct Actor {
    uint16_t world_x, world_y, base, words[4];
    int16_t screen_x, screen_y;
    uint8_t present, flags, phase, party;
    uint32_t descriptor;
} Actor;
typedef struct Packet {
    Actor actors[kActors];
    uint8_t bytes[kPacketBytes];
    uint32_t seen, expected, epoch, producer_frame;
    unsigned count;
    unsigned start_slot, party_end_slot, reserved_end_slot, mask;
    uint8_t resource[48];
    int camera_x, camera_y, valid;
} Packet;
static Packet producing, queued, transfer, displayed;
static int configured, enabled, initialized, installed, identity, sequence, sequence_done, party_done;
static int transfer_valid;
static unsigned generation, next_epoch, frame_pieces, frame_pixels, total_captured, total_packets;
static unsigned total_pieces, total_pixels, rejects;
static uint64_t drawn_piece_bits[2];
static const uint8_t *bound_rom;
static size_t bound_size;
static FILE *trace;
static PpuExtraObject objects[kPieces];
static uint16_t colors[kPieces][64];
static const uint8_t clean_hash[32] = {
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00
};

static unsigned R16(unsigned at) { return g_ram[at] | (unsigned)g_ram[at + 1] << 8; }
static unsigned R24(unsigned at) { return R16(at) | (unsigned)g_ram[at + 2] << 16; }
static int Signed(unsigned word) { return (int16_t)word; }
static uint16_t RomWord(unsigned at) {
    unsigned offset = (at >> 16) * 0x8000 + (at & 0x7fff);
    return g_rom[offset] | (unsigned)g_rom[offset + 1] << 8;
}
static int Gate(int value, unsigned stop) {
    unsigned v = (uint16_t)value;
    return v >= 0xfff1 || v < stop;
}
static int PartyGate(int value, unsigned stop) {
    unsigned v = (uint16_t)value;
    return v >= 0x1f9 || v < stop;
}
/* Original DAxx gate adds the world period only in A, never in DP16/18.
 * Packet validation therefore retains raw coordinates even on this branch. */
static int RegularGate(int value, unsigned stop, int wrap) {
    unsigned raw = (uint16_t)value;
    if (raw >= 0xfff1) return 1;
    if (wrap && raw >= 0x8000) raw = (raw + 3584) & 0xffff;
    return raw < stop;
}
static int WorldDistance(int value, int center) {
    int d = value - center;
    if (d < -1792) d += 3584;
    if (d >= 1792) d -= 3584;
    return d;
}
static int WrappingResource(const Ppu *ppu) {
    if (!g_ram[0x407]) return 0;
    if (!ppu || !g_snes || !g_snes->dma || R16(0x40e) || g_ram[0x407] != 1 ||
        g_ram[0x400] || g_ram[0x5372] != 17 || (g_ram[0x5361] & 0x40) ||
        R16(0x46d) != 0x0e0e || R16(0x46f) != 0x0404 ||
        R24(0x500) != 0x038758 || R24(0x503) != 0x038f58 ||
        R24(0x506) != 0x0a8418 || R24(0x509) != 0x0a8818 ||
        R24(0x513) != 0x09a85c || R24(0x516) != 0x099700 ||
        R24(0x537) != 0x098110 || R24(0x55c) != 0x098210 ||
        ppu->bgmode != 9 || PPU_mosaicSize(ppu) > 1 || ppu->setini) return 0;
    for (unsigned i = 0; i < 8; ++i)
        if (g_snes->dma->channel[i].hdmaActive) return 0;
    /* No arbitrary other ordinary allocations become qualified by flags. */
    for (unsigned i = 0; i < kRegular; ++i) {
        unsigned at = 0x4100 + 25 * i;
        if (i < 2) {
            if (g_ram[at] != (i ? 0 : 2) || R16(at + 1) != 1536 ||
                R16(at + 3) != (i ? 544 : 528) || R16(at + 5) != 0x0598) return 0;
        } else if (g_ram[at] != 255) return 0;
    }
    return 1;
}
static int Period512(int value, int center) {
    return ((value - center + 256) & 511) + center - 256;
}

static void Row(const char *event, const Packet *packet, const CpuState *cpu, int match) {
    if (!trace) return;
    const Actor *target = &packet->actors[kParty + 3];
    unsigned party_count = 0;
    for (unsigned i = 0; i < kParty; ++i) party_count += packet->actors[i].present != 0;
    const Actor *member = &packet->actors[0];
    fprintf(trace, "%s,%u,%u,%u,%d,%u,%u,%u,%u,%u,%u,%u,%u,%d,%d,%u,%u,%u,%u,%d,%u,%u,%u,%u,%u,%u,%u,%u,%u,%d,%d,%u",
        event, snes_frame_counter, generation, packet->epoch, packet->valid, packet->count,
        packet->seen, frame_pieces, frame_pixels, 0x414b, target->flags, target->phase,
        target->descriptor, target->screen_x, target->screen_y,
        cpu ? cpu->D : 0, cpu ? cpu->DB : 0, cpu ? cpu->m_flag : 0,
        cpu ? cpu->x_flag : 0, match, packet->producer_frame,
        packet->resource[28] | (unsigned)packet->resource[29] << 8,
        packet->start_slot, packet->mask, g_ppu ? PPU_objPriority(g_ppu) : 0,
        party_count, packet->seen & 31u, packet->party_end_slot, member->descriptor,
        member->screen_x, member->screen_y, member->phase);
    const Actor *r0 = &packet->actors[kParty], *r1 = &packet->actors[kParty + 1];
    uint8_t packet_hash[32];
    sha256_compute(packet->bytes, sizeof(packet->bytes), packet_hash);
    fprintf(trace, ",%d,%d,%u,%u,%u,%u,", packet->camera_x, packet->camera_y,
        r0->descriptor, r0->phase, r1->descriptor, r1->phase);
    for (unsigned i = 0; i < 32; ++i) fprintf(trace, "%02x", packet_hash[i]);
    fputc('\n', trace);
    fflush(trace);
}

void FoundationWideActorsReset(void) {
    memset(&producing, 0, sizeof(producing));
    memset(&queued, 0, sizeof(queued));
    memset(&transfer, 0, sizeof(transfer));
    memset(&displayed, 0, sizeof(displayed));
    sequence = sequence_done = party_done = transfer_valid = 0;
    bound_rom = NULL; bound_size = 0; identity = 0;
    if (g_snes && g_snes->dma) dma_reset_transfer_notify_state(g_snes->dma);
    ++generation;
    Row("reset", &displayed, NULL, 0);
}

void FoundationWideActorsSetEnabled(int value) {
    configured = value == 1;
    if (initialized) {
        const char *env = getenv("SNESRECOMP_FOUNDATION_WIDE_ACTORS");
        enabled = env ? !strcmp(env, "1") : configured;
    }
}
int FoundationWideActorsEnabled(void) { return enabled; }

static int Scene(const Ppu *ppu) {
    return identity && ppu && FoundationFieldSceneEligible(ppu) && ppu->obsel == 3 &&
        !PPU_objPriority(ppu) &&
        g_ram[0x401] == 12 && (!g_ram[0x407] || WrappingResource(ppu)) &&
        !R16(0x471) && !R16(0x473);
}

static void Resource(const Ppu *ppu, uint8_t key[48]) {
    /* Exact loaded-resource identity, without mutable camera/task/pose bytes.
     * An eligible-to-eligible map change must discard the previous packet too. */
    memset(key, 0, 48);
    memcpy(key, g_ram + 0x500, 12); /* both tile and cell definition pointers */
    memcpy(key + 12, g_ram + 0x513, 6); /* both segment-grid pointers */
    memcpy(key + 18, g_ram + 0x537, 3); /* primary metatile attributes */
    memcpy(key + 21, g_ram + 0x55c, 3); /* secondary metatile attributes */
    memcpy(key + 24, g_ram + 0x46d, 4); /* layer segment dimensions */
    memcpy(key + 28, g_ram + 0x40e, 2); /* actual scene selector */
    key[30] = g_ram[0x407]; key[31] = !!g_ram[0x400]; key[32] = g_ram[0x401];
    key[33] = ppu->obsel; key[34] = ppu->bgmode;
    memcpy(key + 35, ppu->bgXsc, 3);
    key[38] = ppu->bgTileAdr & 255; key[39] = ppu->bgTileAdr >> 8;
}

static int SameResource(const Ppu *ppu, const Packet *packet) {
    uint8_t key[48];
    if (!ppu) return 0;
    Resource(ppu, key);
    return !memcmp(key, packet->resource, sizeof(key));
}

void FoundationWideActorsBeforeFrame(void) {
    if (!enabled && !trace) return;
    size_t size = g_snes && g_snes->cart ? g_snes->cart->romImageSize : 0;
    if (g_rom != bound_rom || size != bound_size) {
        FoundationWideActorsReset(); bound_rom = g_rom; bound_size = size;
        if (g_rom && size == 1572864) {
            uint8_t hash[32]; sha256_compute(g_rom, size, hash);
            identity = !memcmp(hash, clean_hash, sizeof(hash));
        }
    }
    if ((sequence || queued.valid || transfer_valid || displayed.valid) &&
        (!Scene(g_ppu) || (sequence && !SameResource(g_ppu, &producing)) ||
         (queued.valid && !SameResource(g_ppu, &queued)) ||
         (transfer_valid && !SameResource(g_ppu, &transfer)) ||
         (displayed.valid && !SameResource(g_ppu, &displayed)))) {
        /* A lost resource/context invalidates presentation, never guest state. */
        Row("reject_scene", &displayed, NULL, 0);
        memset(&producing, 0, sizeof(producing)); memset(&queued, 0, sizeof(queued));
        memset(&transfer, 0, sizeof(transfer)); memset(&displayed, 0, sizeof(displayed));
        sequence = sequence_done = party_done = transfer_valid = 0; ++generation;
    }
}

static int Context(const CpuState *cpu, unsigned caller, int widths) {
    return Scene(g_ppu) && cpu && !cpu->emulation && !cpu->_flag_D &&
        cpu->PB == 1 && cpu->DB == 1 && cpu->D == 0x0e00 && cpu->S < 0x1ffd &&
        R24(cpu->S + 1) == caller &&
        (!widths || (!cpu->m_flag && cpu->x_flag));
}

static void Reject(const char *why, const CpuState *cpu) {
    ++rejects; sequence = sequence_done = party_done = 0;
    producing.valid = queued.valid = 0;
    Row(why, &producing, cpu, 0);
}

static void Observe(CpuState *cpu, uint32_t pc) {
    if ((!enabled && !trace) || !identity) return;
    if (pc == 0x01d8b1) {
        memset(&producing, 0, sizeof(producing)); sequence_done = party_done = 0;
        producing.epoch = ++next_epoch; producing.producer_frame = snes_frame_counter;
        producing.camera_x = Signed(R16(0x2ad)); producing.camera_y = Signed(R16(0x2af));
        sequence = Context(cpu, 0x01d865, 0);
        unsigned cursor = R16(0x46b);
        producing.start_slot = 12;
        producing.mask = g_ram[0x400] ? 0xefff : 0xffff;
        if (cursor != 0x30 || R16(0x0e34) != 0x10 || R16(0x0e38) != 0x201 ||
            R16(0x0e10) != producing.mask) sequence = 0;
        if (g_ppu) Resource(g_ppu, producing.resource);
        for (unsigned i = 0; i < kParty; ++i) {
            unsigned at = 0x4000 + i * 18;
            if (g_ram[at] != 255) {
                unsigned base = R16(at + 3), gfx = base + g_ram[at] * 2 + (g_ram[at + 10] >> 7);
                if (g_ram[at] > 3 || base == 0xb0 || (gfx & 0xfff8) == 0xa8 ||
                    gfx >= (0xd800 - 0x9800) / 8) sequence = 0;
                else producing.expected |= 1u << i;
            }
        }
        for (unsigned i = 0; i < kRegular; ++i) {
            unsigned at = 0x4100 + i * 25;
            if (g_ram[at] != 255) {
                unsigned base = R16(at + 5), gfx = base + g_ram[at] * 2 + (g_ram[0x475] >> 7);
                if (g_ram[at] > 3 || base == 0xb0 ||
                    gfx >= (0xd800 - 0x9800) / 8) sequence = 0;
                else producing.expected |= 1u << (kParty + i);
            }
        }
        Row("party_begin", &producing, cpu, sequence);
        if (!sequence) Reject("reject_begin", cpu);
        return;
    }
    if (!sequence) return;
    if (!SameResource(g_ppu, &producing)) { Reject("reject_resource", cpu); return; }
    if (pc == 0x01d917) {
        unsigned index = g_ram[0x0e13], at = 0x4000 + index * 18;
        if (party_done || !Context(cpu, 0x01d865, 1) || index >= kParty || cpu->Y != 2 ||
            R24(0x0e1c) != 0x7e0000 + at || R16(0x0e1a) != R16(at + 3) ||
            !(producing.expected & (1u << index)) || (producing.seen & (1u << index))) {
            Reject("reject_party_capture", cpu); return;
        }
        Actor *actor = &producing.actors[index];
        actor->present = actor->party = 1; actor->flags = g_ram[at];
        actor->phase = g_ram[at + 10] >> 7; actor->base = R16(at + 3);
        actor->world_x = g_ram[at + 1] | ((g_ram[at + 5] & 1) << 8);
        actor->world_y = g_ram[at + 2] | ((g_ram[at + 5] & 2) << 7);
        actor->screen_x = Signed(R16(0x0e16)); actor->screen_y = Signed(R16(0x0e18));
        unsigned gfx = actor->base + actor->flags * 2 + actor->phase;
        actor->descriptor = 0x0e9800 + gfx * 8;
        if (actor->screen_x != Signed(actor->world_x) ||
            actor->screen_y != Signed(actor->world_y - 1) || actor->base == 0xb0 ||
            (gfx & 0xfff8) == 0xa8 || actor->flags > 3 ||
            actor->descriptor < 0x0e9800 || actor->descriptor + 8 > 0x0ed800 ||
            R16(0x0e10) != producing.mask) {
            Reject("reject_party_descriptor", cpu); return;
        }
        for (unsigned part = 0; part < 4; ++part)
            actor->words[part] = RomWord(actor->descriptor + part * 2) & producing.mask;
        producing.seen |= 1u << index; ++producing.count; ++total_captured;
        Row("party_capture", &producing, cpu, 1);
    } else if (pc == 0x01d988) {
        if (!Context(cpu, 0x01d865, 0) || g_ram[0x0e13] != kParty ||
            (producing.seen & 31u) != (producing.expected & 31u)) {
            Reject("reject_party_sequence", cpu); return;
        }
        unsigned slot = 12;
        for (unsigned index = 0; index < kParty; ++index) {
            const Actor *actor = &producing.actors[index];
            if (actor->present && PartyGate(actor->screen_x, 255) && PartyGate(actor->screen_y, 239))
                slot += 4;
        }
        if (R16(0x46b) != slot * 4) { Reject("reject_party_cursor", cpu); return; }
        producing.party_end_slot = slot; party_done = 1;
        Row("party_end", &producing, cpu, 1);
    } else if (pc == 0x01da56) {
        if (!party_done || !Context(cpu, 0x01d86f, 0) ||
            R16(0x46b) != producing.party_end_slot * 4 || R16(0x0e10) != producing.mask) {
            Reject("reject_regular_begin", cpu); return;
        }
        producing.start_slot = R16(0x46b) / 4;
        Row("begin", &producing, cpu, 1);
    } else if (pc == 0x01dab6) {
        unsigned index = g_ram[0x0e14], at = 0x4100 + index * 25;
        unsigned rank = kParty + index;
        if (!party_done || !Context(cpu, 0x01d86f, 1) || index >= kRegular || cpu->Y != 3 ||
            R24(0x0e1c) != 0x7e0000 + at || R16(0x0e1a) != R16(at + 5) ||
            !(producing.expected & (1u << rank)) || producing.seen & (1u << rank)) {
            Reject("reject_capture", cpu); return;
        }
        Actor *actor = &producing.actors[rank];
        actor->present = 1; actor->flags = g_ram[at]; actor->phase = g_ram[0x475] >> 7;
        actor->base = R16(at + 5); actor->world_x = R16(at + 1); actor->world_y = R16(at + 3);
        actor->screen_x = Signed(R16(0x0e16)); actor->screen_y = Signed(R16(0x0e18));
        unsigned gfx = actor->base + actor->flags * 2 + actor->phase;
        actor->descriptor = 0x0e9800 + gfx * 8;
        if (actor->screen_x != Signed(actor->world_x - producing.camera_x) ||
            actor->screen_y != Signed(actor->world_y - producing.camera_y) ||
            actor->flags > 3 || actor->base == 0xb0 ||
            actor->descriptor < 0x0e9800 || actor->descriptor + 8 > 0x0ed800 ||
            R16(0x0e10) != producing.mask) {
            Reject("reject_descriptor", cpu); return;
        }
        for (unsigned part = 0; part < 4; ++part)
            actor->words[part] = RomWord(actor->descriptor + part * 2) & producing.mask;
        producing.seen |= 1u << rank; ++producing.count; ++total_captured;
        Row("capture", &producing, cpu, 1);
    } else if (pc == 0x01db2c) {
        if (!Context(cpu, 0x01d86f, 0) || g_ram[0x0e14] != 19 ||
            producing.seen != producing.expected || !producing.count) {
            Reject("reject_sequence", cpu); return;
        }
        sequence_done = 1; Row("sequence_end", &producing, cpu, 1);
    } else if (pc == 0x01de29) {
        if (!sequence_done || !Context(cpu, 0x01d873, 0)) {
            Reject("reject_staging", cpu); return;
        }
        unsigned slot = 12;
        for (unsigned index = 0; index < kParty + kAppendRegular; ++index) {
            Actor *actor = &producing.actors[index];
            if (index == kParty && slot != producing.start_slot) { Reject("reject_party_regular_cursor", cpu); return; }
            if (!actor->present) continue;
            if (actor->party ? (!PartyGate(actor->screen_x, 255) || !PartyGate(actor->screen_y, 239)) :
                               (!RegularGate(actor->screen_x, 255, producing.resource[30]) ||
                                !RegularGate(actor->screen_y, 239, producing.resource[30]))) continue;
            if (slot >= 124) { Reject("reject_capacity", cpu); return; }
            for (unsigned part = 0; part < 4; ++part, ++slot) {
                int x = actor->screen_x + ((part & 1) * 8);
                int y = actor->screen_y - !actor->party + ((part >> 1) * 8);
                unsigned at = 0x2200 + slot * 4;
                unsigned high = (g_ram[0x2400 + slot / 4] >> (slot % 4 * 2)) & 3;
                if (g_ram[at] != (x & 255) || g_ram[at + 1] != (y & 255) ||
                    R16(at + 2) != actor->words[part] || high != ((x >> 8) & 1)) {
                    Reject("reject_staging_piece", cpu); return;
                }
            }
        }
        if (R16(0x46b) != slot * 4) { Reject("reject_cursor", cpu); return; }
        /* DE82 has its own compact cursor: ordinary records 17/18 fill
         * reserved slots 4..11 without advancing append cursor 046B. */
        unsigned reserved_slot = 4;
        for (unsigned index = kParty + kAppendRegular; index < kActors; ++index) {
            const Actor *actor = &producing.actors[index];
            if (!actor->present || !RegularGate(actor->screen_x, 255, producing.resource[30]) ||
                !RegularGate(actor->screen_y, 239, producing.resource[30])) continue;
            for (unsigned part = 0; part < 4; ++part, ++reserved_slot) {
                int x = actor->screen_x + ((part & 1) * 8);
                int y = actor->screen_y - 1 + ((part >> 1) * 8);
                unsigned at = 0x2200 + reserved_slot * 4;
                unsigned high = (g_ram[0x2400 + reserved_slot / 4] >> (reserved_slot % 4 * 2)) & 3;
                if (g_ram[at] != (x & 255) || g_ram[at + 1] != (y & 255) ||
                    R16(at + 2) != actor->words[part] || high != ((x >> 8) & 1)) {
                    Reject("reject_reserved_piece", cpu); return;
                }
            }
        }
        producing.reserved_end_slot = reserved_slot;
        if (R16(0x0e34) != reserved_slot * 4 ||
            R16(0x0e38) != 0x201 + (reserved_slot - 4) / 4) {
            Reject("reject_reserved_cursor", cpu); return;
        }
        for (; reserved_slot < 12; ++reserved_slot) {
            unsigned at = 0x2200 + reserved_slot * 4;
            unsigned high = (g_ram[0x2400 + reserved_slot / 4] >> (reserved_slot % 4 * 2)) & 3;
            if (R16(at) != 0xf080 || high != 1) {
                Reject("reject_reserved_park", cpu); return;
            }
        }
        memcpy(producing.bytes, g_ram + 0x2200, kPacketBytes);
        producing.valid = 1; queued = producing; sequence = sequence_done = 0;
        Row("staging_ready", &queued, cpu, 1);
    }
}

static int PacketMatches(const Ppu *ppu, const uint8_t *bytes) {
    for (unsigned i = 0; i < 256; ++i)
        if (ppu->oam[i] != (bytes[i * 2] | (unsigned)bytes[i * 2 + 1] << 8)) return 0;
    return !memcmp(ppu->highOam, bytes + 512, 32);
}

static void NotifyDma(const Dma *dma, int channel, const DmaChannel *start, bool complete) {
    if ((!enabled && !trace) || !start || start->bAdr != 4) return;
    if (!complete) {
        transfer_valid = Scene(g_ppu) && channel == 7 && start->aBank == 0x7e &&
            start->aAdr == 0x2200 && start->size == kPacketBytes && !start->mode &&
            !start->fromB && !start->fixed && !start->decrement && queued.valid &&
            SameResource(g_ppu, &queued) &&
            !memcmp(queued.bytes, g_ram + 0x2200, kPacketBytes);
        if (transfer_valid) transfer = queued;
        else memset(&displayed, 0, sizeof(displayed));
        Row("dma_start", transfer_valid ? &transfer : &queued, NULL, transfer_valid);
    } else {
        int match = transfer_valid && dma && dma->snes && Scene(dma->snes->ppu) &&
            SameResource(dma->snes->ppu, &transfer) && PacketMatches(dma->snes->ppu, transfer.bytes);
        if (match) { displayed = transfer; ++total_packets; }
        else memset(&displayed, 0, sizeof(displayed));
        Row("dma_complete", match ? &displayed : &transfer, NULL, match);
        transfer_valid = 0; queued.valid = 0;
    }
}

void FoundationWideActorsInit(void) {
    if (initialized) return;
    initialized = 1;
    const char *env = getenv("SNESRECOMP_FOUNDATION_WIDE_ACTORS");
    enabled = env ? !strcmp(env, "1") : configured;
    const char *path = getenv("SNESRECOMP_FOUNDATION_ACTORS_TRACE");
    if (path) trace = fopen(path, "w");
    if (trace) fputs("event,frame,generation,epoch,packet_valid,cached_actors,seen_mask,side_pieces,side_pixels,target_record,target_flags,target_phase,target_descriptor,target_x,target_y,cpu_d,cpu_db,cpu_m,cpu_x,packet_match,producer_frame,scene,start_slot,mask,rotation,party_count,party_seen,party_end_slot,party0_descriptor,party0_x,party0_y,party0_phase,packet_camera_x,packet_camera_y,regular0_descriptor,regular0_phase,regular1_descriptor,regular1_phase,packet_sha256\n", trace);
    if (enabled || trace) {
        installed = interp_bridge_add_pre_opcode_hook(0x01d8b1, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01d917, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01d988, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01da56, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01dab6, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01db2c, Observe) &&
            interp_bridge_add_pre_opcode_hook(0x01de29, Observe);
        if (installed) dma_set_transfer_notify_hook(NotifyDma);
        else enabled = 0;
    }
    fprintf(stderr, "[foundation] experimental_field_actors=%d observer=%d\n", enabled, installed);
}

void FoundationWideActorsBeginDraw(void) {
    frame_pieces = frame_pixels = 0;
    memset(drawn_piece_bits, 0, sizeof(drawn_piece_bits));
}

unsigned FoundationWideActorsPrepareLine(const Ppu *source, unsigned line, Ppu *picture) {
    if (!enabled || !displayed.valid || !source || !picture || source == picture || line < 1 || line > 224 ||
        !Scene(source) || !SameResource(source, &displayed) || !PacketMatches(source, displayed.bytes)) return 0;
    int cx = displayed.camera_x + ((source->hScroll[0] - (displayed.camera_x & 1023) + 512) & 1023) - 512;
    int cy = displayed.camera_y + ((source->vScroll[0] - (displayed.camera_y & 1023) + 512) & 1023) - 512;
    int dx = cx - displayed.camera_x, dy = cy - displayed.camera_y;
    int wrap = displayed.resource[30] != 0;
    if (wrap) {
        /* Authenticate the live raster against its wrapped primary reference.
         * The displayed actor records and packet remain immutable. Reject an
         * unknown raster offset rather than unwrap against stale packet lows. */
        int live_x = R16(0x2ad), live_y = R16(0x2af);
        if (live_x >= 3584 || live_y >= 3584 ||
            displayed.camera_x < 0 || displayed.camera_x >= 3584 ||
            displayed.camera_y < 0 || displayed.camera_y >= 3584) return 0;
        /* The interior fixture does not qualify stale-packet raster timing
         * across an actual world edge. Refuse that jump until an edge proof. */
        if (live_x - displayed.camera_x < -8 || live_x - displayed.camera_x > 8 ||
            live_y - displayed.camera_y < -8 || live_y - displayed.camera_y > 8) return 0;
        int latch_dx = ((source->hScroll[0] - (live_x & 1023) + 512) & 1023) - 512;
        int latch_dy = ((source->vScroll[0] - (live_y & 1023) + 512) & 1023) - 512;
        if (latch_dx < -8 || latch_dx > 8 || latch_dy < -8 || latch_dy > 8) return 0;
        cx = live_x + latch_dx; cy = live_y + latch_dy;
        dx = WorldDistance(live_x, displayed.camera_x) + latch_dx;
        dy = WorldDistance(live_y, displayed.camera_y) + latch_dy;
        if (dx < -8 || dx > 8 || dy < -8 || dy > 8) return 0;
    }
    unsigned count = 0;
    for (unsigned index = 0; index < kActors; ++index) {
        const Actor *actor = &displayed.actors[index];
        if (!actor->present) continue;
        for (unsigned part = 0; part < 4; ++part) {
            int x = (actor->party ? Period512(actor->screen_x, 128) - dx :
                     wrap ? WorldDistance(actor->world_x - cx, 128) + 128 :
                            Signed(actor->world_x - cx)) + ((part & 1) * 8);
            int y = (actor->party ? Period512(actor->screen_y, 112) - dy :
                     wrap ? WorldDistance(actor->world_y - cy, 112) + 111 :
                            Signed(actor->world_y - cy) - 1) + ((part >> 1) * 8);
            if ((int)line - 1 < y || (int)line - 1 >= y + 8 || x >= 328 || x + 8 <= -72 ||
                (x >= 0 && x + 8 <= 256)) continue;
            unsigned bits_index = index * 4 + part;
            uint16_t word = actor->words[part];
            unsigned palette = 128 + 16 * ((word >> 9) & 7);
            unsigned base = (word & 256) ? PPU_objTileAdr2(source) : PPU_objTileAdr1(source);
            for (unsigned row = 0; row < 8; ++row) {
                unsigned sy = (word & 0x8000) ? 7 - row : row;
                unsigned at = (base + (word & 255) * 16 + sy) & 0x7fff;
                const uint16_t *vram = source->renderVram ? source->renderVram : source->vram;
                uint32_t planes = vram[at] | (uint32_t)vram[(at + 8) & 0x7fff] << 16;
                for (unsigned col = 0; col < 8; ++col) {
                    unsigned bit = (word & 0x4000) ? col : 7 - col;
                    unsigned pixel = ((planes >> bit) & 1) | ((planes >> (bit + 7)) & 2) |
                        ((planes >> (bit + 14)) & 4) | ((planes >> (bit + 21)) & 8);
                    colors[count][row * 8 + col] = pixel ? 0x8000 | (source->cgram[palette + pixel] & 0x7fff) : 0;
                }
            }
            unsigned virtual_slot = index >= kParty + kAppendRegular ?
                4 + (index - kParty - kAppendRegular) * 4 + part : 12 + bits_index;
            objects[count] = (PpuExtraObject){ .x = x, .y = y, .width = 8, .height = 8, .stride = 8,
                .priority = (word >> 12) & 3, .math = (word & 0x0800) != 0,
                /* Private OAM is empty; virtual slots preserve constructor
                 * order even for culled records. Rotation is guarded off. */
                .oamSlot = virtual_slot,
                .order = virtual_slot + 1, .pixels = colors[count] };
            ++count;
            uint64_t bit = (uint64_t)1 << (bits_index & 63);
            if (!(drawn_piece_bits[bits_index >> 6] & bit)) {
                drawn_piece_bits[bits_index >> 6] |= bit; ++frame_pieces; ++total_pieces;
            }
        }
    }
    if (!count) return 0;
    /* This PPU is the private margin picture. Never promote stale native OAM
     * there. Original guest OBJ evaluation already ran at authentic width. */
    for (unsigned i = 0; i < 128; ++i) picture->oam[i * 2] = 0xf080;
    memset(picture->highOam, 0, sizeof(picture->highOam));
    PpuSetExtraObjects(picture, objects, count);
    picture->screenEnabled[0] |= source->screenEnabled[0] & 16;
    picture->screenEnabled[1] |= source->screenEnabled[1] & 16;
    return count;
}

void FoundationWideActorsDrawResult(unsigned pixels) { frame_pixels += pixels; total_pixels += pixels; }
void FoundationWideActorsEndDraw(void) { Row("frame", &displayed, NULL, displayed.valid); }

void FoundationWideActorsShutdown(void) {
    fprintf(stderr, "[foundation_wide_actors] captured=%u packets=%u side_pieces=%u side_pixels=%u rejects=%u resets=%u\n",
            total_captured, total_packets, total_pieces, total_pixels, rejects, generation);
    if (trace) fclose(trace);
    trace = NULL;
}
