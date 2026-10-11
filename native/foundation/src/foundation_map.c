/* Optional current-area terrain map from the original selected resource and
 * loaded SNES tile/palette data. It reveals that area's terrain while open,
 * with verified towns/current destinations; no enemies, items or history. */
#include "foundation_map.h"
#include "foundation_field.h"
#include <string.h>

static unsigned Word(const uint8_t *ram, unsigned at) {
    return ram[at] | (unsigned)ram[at + 1] << 8;
}

int FoundationMapPosition(const uint8_t *ram, size_t size, int *x, int *y) {
    if (!ram || size != 0x20000 || !x || !y || x == y || ram[0x20] != 1 ||
        !(ram[0x401] & 4) || ram[0x4000] > 3 || (ram[0x4005] & 3) ||
        !ram[0x46d] || !ram[0x46e] ||
        ram[0x46d] > 15 || ram[0x46e] > 15 || Word(ram, 0x471) || Word(ram, 0x473)) return 0;
    /* Original 01:94D7/94F9 takes the first active party record's screen
     * anchor, AND #00F0, and calls 00:FF35 with the primary camera/dimension.
     * 01:96D7 stores its ordinary 7080 screen anchor. This is the original
     * navigation/collision anchor, not a guessed sprite centre or follower. */
    int px = (int16_t)Word(ram, 0x2ad) + (ram[0x4001] & 0xf0);
    int py = (int16_t)Word(ram, 0x2af) + (ram[0x4002] & 0xf0);
    int width = ram[0x46d] * 256, height = ram[0x46e] * 256;
    if (ram[0x407]) {
        px %= width; py %= height;
        if (px < 0) px += width;
        if (py < 0) py += height;
    }
    if (px < 0 || py < 0 || px >= width || py >= height) return 0;
    *x = px; *y = py;
    return 1;
}

static unsigned TilePixel(uint16_t word, const uint16_t *vram, int x, int y) {
    unsigned row = (unsigned)y & 7, col = (unsigned)x & 7;
    if (word & 0x8000) row ^= 7;
    if (word & 0x4000) col ^= 7;
    unsigned at = (word & 1023u) * 16 + row, bit = 7 - col;
    unsigned lo = vram[at], hi = vram[at + 8];
    return ((lo >> bit) & 1) | ((lo >> (bit + 7)) & 2) |
        ((hi >> (bit - 0)) & 1) * 4 | ((hi >> (bit + 8)) & 1) * 8;
}

int FoundationMapSample(const uint8_t *ram, size_t size, const uint16_t *vram,
                        size_t words, const uint16_t *cgram, size_t colors,
                        int x, int y, uint32_t *color) {
    if (!ram || size != 0x20000 || !vram || words != 0x8000 ||
        !cgram || colors != 256 || !color || !FoundationFieldLayerActive(0)) return 0;
    uint16_t tile[2] = {0,0}; unsigned index[2] = {0,0};
    for (int layer = 0; layer < 2; ++layer) {
        if (!FoundationFieldLayerActive(layer)) continue;
        int lx=x, ly=y;
        if (layer) {
            lx+=(int16_t)(Word(ram,0x2b1)-Word(ram,0x2ad));
            ly+=(int16_t)(Word(ram,0x2b3)-Word(ram,0x2af));
        }
        if (!FoundationFieldResolve(layer, lx, ly, &tile[layer])) return 0;
        index[layer] = TilePixel(tile[layer], vram, lx, ly);
        if (index[layer]) index[layer] += ((tile[layer] >> 10) & 7) * 16;
    }
    /* Mode1 terrain: BG1 high, BG2 high, BG1 low, BG2 low; transparent
     * original tile pixels expose the lower layer/backdrop. No OBJ/UI/math. */
    unsigned selected = index[0] && (tile[0] & 0x2000) ? index[0] :
        index[1] && (tile[1] & 0x2000) ? index[1] : index[0] ? index[0] : index[1];
    unsigned rgb = cgram[selected];
    unsigned r = rgb & 31, g = (rgb >> 5) & 31, b = (rgb >> 10) & 31;
    *color = 0xff000000u | ((r * 255 / 31) << 16) | ((g * 255 / 31) << 8) | b * 255 / 31;
    return 1;
}

#ifndef FOUNDATION_MAP_STANDALONE
#include "common_rtl.h"
#include "foundation_hotkeys.h"
#include "foundation_journal.h"
#include "snes/ppu.h"
#include "snes/snes.h"
#include "snes_overlay_draw.h"
#include <stdio.h>
#include <stdlib.h>
extern Ppu *g_ppu;
/* Each legend label shares the exact ink of its corresponding marker. */
#define MAP_PLAYER_INK 0xffffdf78u
#define MAP_TOWN_INK 0xff67e6efu
#define MAP_OBJECTIVE_INK 0xffff86e9u
static int enabled, objective_enabled, visible, eligible, ready, failed, building;
static unsigned completed, generations, samples;
static unsigned snapshot_frame, snapshot_writes, host_frame, point_scene;
static size_t point_count;
static FoundationMapPoint points[32];
static uint8_t resource_key[0x200], current_key[0x200];
static uint16_t palette[256], graphics[0x8000];
static uint32_t terrain[FOUNDATION_MAP_WIDTH * FOUNDATION_MAP_HEIGHT];
static uint32_t front[FOUNDATION_MAP_WIDTH * FOUNDATION_MAP_HEIGHT];
static unsigned map_width, map_height, canvas_width, canvas_height;
static FILE *trace;

void FoundationMapReset(void) {
    visible = eligible = ready = failed = building = 0; completed = 0;
    point_count = 0;
    memset(resource_key, 0, sizeof(resource_key));
}
void FoundationMapInit(void) {
    enabled = 1;
    objective_enabled = 1;
    char line[128], key[64]; int value;
    FILE *file = fopen("foundation.ini", "r");
    if (file) {
        while (fgets(line, sizeof(line), file)) {
            if (sscanf(line, " %63[^=]=%d", key, &value) != 2) continue;
            size_t n = strlen(key);
            while (n && (key[n-1] == ' ' || key[n-1] == '\t')) key[--n] = 0;
            if (!strcmp(key, "NavigationMap")) enabled = value == 1;
            if (!strcmp(key, "NavigationMapObjective")) objective_enabled = value == 1;
        }
        fclose(file);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_NAVIGATION_MAP");
    if (env) enabled = !strcmp(env, "1");
    env = getenv("SNESRECOMP_FOUNDATION_NAVIGATION_MAP_OBJECTIVE");
    if (env) objective_enabled = !strcmp(env, "1");
    env = getenv("SNESRECOMP_FOUNDATION_MAP_TRACE");
    if (env && *env) trace = fopen(env, "w");
    if (trace) fputs("frame,enabled,visible,eligible,ready,completed,generations,samples,player_valid,player_x,player_y\n",trace);
    FoundationMapReset();
}
void FoundationMapBeforeFrame(void) {}
int FoundationMapVisible(void) { return enabled && visible; }
void FoundationMapHide(void) { visible = 0; }
int FoundationMapBounds(unsigned *scene, unsigned *width, unsigned *height) {
    if (!eligible || !scene || !width || !height) return 0;
    *scene=Word(g_ram,0x40e); *width=map_width; *height=map_height;
    return 1;
}
void FoundationMapSetPoints(unsigned scene, const FoundationMapPoint *input, size_t count) {
    point_count=0; point_scene=scene;
    if (!input || count>32) return;
    for (size_t i=0; i<count; ++i)
        if (input[i].x>=0 && input[i].y>=0 && input[i].x<(int)map_width && input[i].y<(int)map_height)
        {
            points[point_count]=input[i];
            points[point_count].label[23]=0;
            for (unsigned j=0; j<23 && points[point_count].label[j]; ++j)
                if ((unsigned char)points[point_count].label[j]<32 || (unsigned char)points[point_count].label[j]>126)
                    points[point_count].label[j]='?';
            ++point_count;
        }
}

static void Key(void) {
    /* Resource/conditional selectors; camera, animation and scratch tasks are
     * excluded. Field eligibility independently authenticates the full stream. */
    memset(current_key, 0, sizeof(current_key));
    memcpy(current_key, g_ram + 0x400, 4);
    /* Original01:93B8 stores the current-cell attribute low nibble in0402.
     * Movement changes it, while selected full terrain is unchanged;
     * field eligibility authenticates the attribute stream independently. Keep
     *0400/0401/0403 and every resource/story guard. */
    current_key[2] = 0;
    /* Original0404/0405 animation scalars change on the steady Likado field.
     * They are not selected terrain identity. Keep topology/wrap0406/0407;
     * graphics changes use the bounded120-frame snapshot refresh below. */
    current_key[6] = g_ram[0x406]; current_key[7] = g_ram[0x407];
    memcpy(current_key + 8, g_ram + 0x453, 6);
    memcpy(current_key + 14, g_ram + 0x46d, 4);
    /* Original01:B248 updates051C/051D as the camera streaming cursor.
     * It does not select terrain: Field eligibility independently authenticates
     * resources, and moving this cursor preserves the full overview tile words.
     * Keep resource/selectors0500..051B; graphics retain bounded refresh. */
    memcpy(current_key + 18, g_ram + 0x500, 28);
    memcpy(current_key + 48, g_ram + 0x537, 3);
    memcpy(current_key + 51, g_ram + 0x55c, 3);
    memcpy(current_key + 54, g_ram + 0x5360, 19);
    memcpy(current_key + 73, g_ram + 0x53f9, 256);
    current_key[329] = g_ram[0x4b6];
    current_key[330] = g_ram[0x40e]; current_key[331] = g_ram[0x40f];
    unsigned dx=(uint16_t)(Word(g_ram,0x2b1)-Word(g_ram,0x2ad));
    unsigned dy=(uint16_t)(Word(g_ram,0x2b3)-Word(g_ram,0x2af));
    current_key[332]=(uint8_t)dx; current_key[333]=(uint8_t)(dx>>8);
    current_key[334]=(uint8_t)dy; current_key[335]=(uint8_t)(dy>>8);
}

void FoundationMapAfterFrame(const SnesDesktopHostFrameStats *stats) {
    host_frame=stats->frame;
    if (FoundationHotkeysConsumeMap() && enabled) {
        visible = !visible;
        fprintf(stderr,"[foundation] frame %u map %s\n",stats->frame,visible ? "shown" : "hidden");
        if (visible) FoundationJournalHide();
    }
    int px = 0, py = 0, player = 0;
    eligible = enabled && visible && g_ppu && FoundationFieldSceneEligible(g_ppu) && FoundationFieldLayerActive(0);
    if (eligible) {
        Key();
        if (memcmp(resource_key,current_key,sizeof(resource_key))) {
            memcpy(resource_key,current_key,sizeof(resource_key));
            memcpy(graphics,g_ppu->vram,sizeof(graphics));
            memcpy(palette,g_ppu->cgram,sizeof(palette));
            map_width = g_ram[0x46d] * 256; map_height = g_ram[0x46e] * 256;
            canvas_width = FOUNDATION_MAP_WIDTH;
            canvas_height = map_height * canvas_width / map_width;
            if (canvas_height > FOUNDATION_MAP_HEIGHT) {
                canvas_height = FOUNDATION_MAP_HEIGHT;
                canvas_width = map_width * canvas_height / map_height;
            }
            completed = 0; ready = failed = 0; building=1; ++generations;
            snapshot_frame=stats->frame; snapshot_writes=g_ppu->vramWriteCount;
        }
        /* Animated colors/tiles refresh at most every120 host frames and only
         * after the previous bounded job finishes. Keep the complete old map
         * visible until the new snapshot is complete, avoiding flicker/stalls. */
        if (ready && !building && (unsigned)(stats->frame-snapshot_frame)>=120 &&
            (snapshot_writes!=g_ppu->vramWriteCount || memcmp(palette,g_ppu->cgram,sizeof(palette)))) {
            memcpy(graphics,g_ppu->vram,sizeof(graphics));
            memcpy(palette,g_ppu->cgram,sizeof(palette));
            snapshot_frame=stats->frame; snapshot_writes=g_ppu->vramWriteCount;
            completed=0; building=1; ++generations;
        }
        /* Bounded incremental work: at most1024 output samples per host frame.
         * Once ready, terrain work is zero until reopen/resource/story change. */
        for (unsigned budget = 0; building && !failed && budget < 1024; ++budget) {
            unsigned at = completed, x = at % canvas_width, y = at / canvas_width;
            int wx = (int)((2*x+1)*map_width/(2*canvas_width));
            int wy = (int)((2*y+1)*map_height/(2*canvas_height));
            if (!FoundationMapSample(g_ram,0x20000,graphics,0x8000,palette,256,wx,wy,&terrain[at])) { failed = 1; break; }
            ++completed; ++samples;
            if (completed == canvas_width * canvas_height) {
                memcpy(front,terrain,completed*sizeof(front[0]));
                ready=1; building=0;
            }
        }
        player = FoundationMapPosition(g_ram,0x20000,&px,&py);
    } else if (visible) { ready = 0; completed = 0; memset(resource_key,0,sizeof(resource_key)); }
    if (trace) fprintf(trace,"%u,%d,%d,%d,%d,%u,%u,%u,%d,%d,%d\n",stats->frame,enabled,visible,eligible,ready,completed,generations,samples,player,px,py);
}

void FoundationMapDraw(uint8_t *dst, size_t pitch, int w, int h) {
    if (!enabled || !visible || !dst || w < 256 || h < 212 || pitch < (size_t)w*4 || pitch%4) return;
    uint32_t *pixels = (uint32_t *)dst; int stride = (int)(pitch/4);
    int x = (w-240)/2, y = (h-196)/2;
    snes_ovl_fill_rect(pixels,stride,h,x,y,240,196,0xff080e1c);
    snes_ovl_stroke_rect(pixels,stride,h,x,y,240,196,0xff809bc8);
    snes_ovl_draw_text(pixels,stride,h,x+8,y+8,"AREA MAP",0xffffdf78,1);
    snes_ovl_draw_text(pixels,stride,h,x+8,y+22,"CURRENT AREA TERRAIN",0xffa7b9d8,1);
    if (!eligible || failed) {
        snes_ovl_draw_text(pixels,stride,h,x+8,y+76,"MAP UNAVAILABLE HERE",0xfff0f3fa,1);
        snes_ovl_draw_text(pixels,stride,h,x+8,y+92,"RETURN TO ORDINARY FIELD",0xffa7b9d8,1);
    } else if (!ready) {
        char loading[32]; snprintf(loading,sizeof(loading),"DRAWING MAP: %u%%",completed*100/(canvas_width*canvas_height));
        snes_ovl_draw_text(pixels,stride,h,x+8,y+76,loading,0xfff0f3fa,1);
    } else {
        int left=x+8+(FOUNDATION_MAP_WIDTH-(int)canvas_width)/2;
        int top=y+38+(FOUNDATION_MAP_HEIGHT-(int)canvas_height)/2;
        for (unsigned row=0; row<canvas_height; ++row)
            memcpy(pixels+(top+(int)row)*stride+left,front+row*canvas_width,canvas_width*4);
        if (point_scene==Word(g_ram,0x40e)) for (size_t i=0; i<point_count; ++i) {
            if (points[i].objective && (!objective_enabled || (host_frame/30)%2)) continue;
            int mx=left+points[i].x*(int)canvas_width/(int)map_width;
            int my=top+points[i].y*(int)canvas_height/(int)map_height;
            if (mx<left+2) mx=left+2;
            if (mx>left+(int)canvas_width-3) mx=left+(int)canvas_width-3;
            if (my<top+2) my=top+2;
            if (my>top+(int)canvas_height-3) my=top+(int)canvas_height-3;
            uint32_t ink=points[i].objective ? MAP_OBJECTIVE_INK : MAP_TOWN_INK;
            snes_ovl_fill_rect(pixels,stride,h,mx-2,my-2,5,5,0xff050914);
            snes_ovl_stroke_rect(pixels,stride,h,mx-1,my-1,3,3,ink);
        }
        int px,py;
        int player = FoundationMapPosition(g_ram,0x20000,&px,&py);
        if (player) {
            int mx = left+px*(int)canvas_width/(int)map_width;
            int my = top+py*(int)canvas_height/(int)map_height;
            /* The marker stays within the terrain at its edges. */
            if (mx<left+2) mx=left+2;
            if (mx>left+(int)canvas_width-3) mx=left+(int)canvas_width-3;
            if (my<top+2) my=top+2;
            if (my>top+(int)canvas_height-3) my=top+(int)canvas_height-3;
            snes_ovl_fill_rect(pixels,stride,h,mx-2,my-2,5,5,0xff050914);
            snes_ovl_fill_rect(pixels,stride,h,mx-1,my-1,3,3,MAP_PLAYER_INK);
            if (point_scene==Word(g_ram,0x40e)) {
                unsigned nearest=0xffffffffu; const char *label=NULL;
                for (size_t i=0; i<point_count; ++i) if (!points[i].objective && points[i].label[0]) {
                    int dx=px-points[i].x,dy=py-points[i].y;
                    if (g_ram[0x407]) {
                        if (dx<0) dx=-dx;
                        if (dy<0) dy=-dy;
                        if (dx>(int)map_width/2) dx=(int)map_width-dx;
                        if (dy>(int)map_height/2) dy=(int)map_height-dy;
                    }
                    unsigned distance=(unsigned)(dx*dx+dy*dy);
                    if (distance<nearest) { nearest=distance; label=points[i].label; }
                }
                if (label) {
                    char caption[32]; snprintf(caption,sizeof(caption),"CLOSEST: %.19s",label);
                    snes_ovl_fill_rect(pixels,stride,h,x+8,y+22,224,8,0xff080e1c);
                    snes_ovl_draw_text(pixels,stride,h,x+8,y+22,caption,0xffa7b9d8,1);
                }
            }
        }
        if (player) {
            snes_ovl_draw_text(pixels,stride,h,x+8,y+170,"GOLD: YOU",MAP_PLAYER_INK,1);
            snes_ovl_draw_text(pixels,stride,h,x+96,y+170,"CYAN: TOWNS",MAP_TOWN_INK,1);
        } else snes_ovl_draw_text(pixels,stride,h,x+8,y+170,"PLAYER POSITION UNAVAILABLE",0xffffdf78,1);
    }
    const char *foot="POSITION + TOWNS";
    int objective_legend=0;
    if (objective_enabled && point_scene==Word(g_ram,0x40e))
        for (size_t i=0; i<point_count; ++i) if (points[i].objective) { foot="PINK BLINK: NEXT OBJECTIVE"; objective_legend=1; break; }
    if (objective_legend)
        snes_ovl_draw_text(pixels,stride,h,x+8,y+184,foot,MAP_OBJECTIVE_INK,1);
    else {
        snes_ovl_draw_text(pixels,stride,h,x+8,y+184,"POSITION",MAP_PLAYER_INK,1);
        snes_ovl_draw_text(pixels,stride,h,x+72,y+184," + ",0xffa7b9d8,1);
        snes_ovl_draw_text(pixels,stride,h,x+96,y+184,"TOWNS",MAP_TOWN_INK,1);
    }
}
void FoundationMapShutdown(void) {
    if (trace) { fclose(trace); trace=NULL; }
    FoundationMapReset();
}
#endif
