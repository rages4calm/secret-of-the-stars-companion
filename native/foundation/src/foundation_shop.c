/* Original loaders, item inventory, price display, purchase, sale and wallet
 * remain game-owned. Modify only the result of the two original BUY lookups.
 * The immutable original item record is never edited. */
#include "foundation_shop.h"
#include "common_rtl.h"
#include "cpu_state.h"
#include "snes/interp_bridge.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int initialized, enabled = 1, ready, trace;
typedef struct StarterGear {
    unsigned item, shop, pointer, half_price;
} StarterGear;
static const StarterGear gear[] = {
    {0x03,0,0xb131,15}, {0x04,0,0xb13f,40}, {0x07,0,0xb169,60},
    {0x35,1,0xb3eb,40}, {0x36,1,0xb3f7,50}, {0x38,1,0xb40f,160},
    {0x4e,1,0xb517,20}
};
static unsigned Word(unsigned a) {
    return g_ram[a] | (unsigned)g_ram[a+1] << 8;
}
static int Bytes(unsigned pc, const unsigned char *expected, size_t size) {
    const unsigned char *p = RomPtr(pc);
    return p && !memcmp(p,expected,size);
}
uint16_t FoundationShopDiscountHalfPrice(uint16_t original) {
    /* BUY doubles this value. Round up to preserve original SELL <= new BUY.
     * Knife: original BUY30/SELL15 -> BUY16/SELL15. Other six prices halve. */
    return (uint16_t)(((unsigned)original + 1u) / 2u);
}
static void BeforePriceReturn(CpuState *cpu, uint32_t pc) {
    unsigned canonical = pc & 0x7fffff;
    int display = canonical == 0x029fbb;
    int purchase = canonical == 0x02fdef;
    if (!ready || !enabled || (!display && !purchase)) return;
    /* Both genuine readers just completed a 16-bit LDA [$57],Y with Y=2.
     * The display reader has its own PHP above the JSR return pair. */
    if ((cpu->PB & 0x7f) != 2 || cpu->emulation || cpu->m_flag ||
        !cpu->x_flag || cpu->_flag_D || cpu->Y != 2 ||
        cpu->D > 0x1fa6 || cpu->S < 0x100 || cpu->S > 0x1ffc ||
        cpu_wram_offset(cpu->DB,0x049f) != 0x049f) return;
    unsigned ret = Word(cpu->S + (display ? 2 : 1));
    if (ret != (display ? 0x9a28 : 0xeba2)) return;
    if (Word(0x040e) != 6) return;
    unsigned shop = g_ram[0x49f], pointer = Word(cpu->D+0x57);
    if (g_ram[cpu->D+0x59] != 4) return;
    for (size_t i=0; i<sizeof(gear)/sizeof(gear[0]); ++i) {
        const StarterGear *g = &gear[i];
        if (g->shop != shop || g->pointer != pointer ||
            cpu->X != g->item*2 || cpu->A != g->half_price) continue;
        if (display && g_ram[cpu->D+0x0b] != g->item) return;
        if (purchase && g_ram[0x49b] != g->item) return;
        cpu->A = FoundationShopDiscountHalfPrice((uint16_t)cpu->A);
        /* Preserve the flags of the just-completed LDA. The display PLP then
         * restores its caller flags normally; purchase ASL owns carry later. */
        cpu->_flag_Z = cpu->A == 0;
        cpu->_flag_N = !!(cpu->A & 0x8000);
        cpu->P = (uint8_t)((cpu->P & ~(CPU_P_Z|CPU_P_N)) |
            (cpu->_flag_Z ? CPU_P_Z : 0) | (cpu->_flag_N ? CPU_P_N : 0));
        if (trace) fprintf(stderr,
            "[foundation_shop] pc=%06X shop=%u item=%02X original_buy=%u new_buy=%u sell=%u D=%04X DB=%02X S=%04X\n",
            pc,shop,g->item,g->half_price*2,cpu->A*2,g->half_price,
            cpu->D,cpu->DB,cpu->S);
        return;
    }
}
void FoundationShopInit(void) {
    if (initialized) return;
    initialized = 1;
    FILE *f = fopen("foundation.ini","r");
    char line[160], key[80]; int value;
    if (f) {
        while (fgets(line,sizeof(line),f)) {
            if (sscanf(line," %79[^=]=%d",key,&value) != 2) continue;
            size_t n = strlen(key);
            while (n && (key[n-1]==' ' || key[n-1]=='\t')) key[--n]=0;
            if (!strcmp(key,"StartingShopDiscount")) enabled = value == 1;
        }
        fclose(f);
    }
    const char *env = getenv("SNESRECOMP_FOUNDATION_STARTING_SHOP_DISCOUNT");
    if (env) enabled = !strcmp(env,"1");
    trace = getenv("SNESRECOMP_FOUNDATION_SHOP_TRACE") != NULL;
    static const unsigned char shop0[] = {3,3,4,7};
    static const unsigned char shop1[] = {4,0x35,0x36,0x38,0x4e};
    static const unsigned char shop_ptr[] = {0x82,0xa5,0x86,0xa5};
    static const unsigned char display[] = {0xa5,0x0b,0xa0,0x02,0x20,0x99,0x9f,0x64,0x0c,0xc2,0x20,0x0a,0x85,0x0a};
    static const unsigned char purchase[] = {0xad,0x9b,0x04,0x8d,0x32,0x04,0x9c,0x2e,0x04,0xa0,0x02,0x20,0xce,0xfd,0xc2,0x20,0x0a,0x8d,0x2c,0x04,0xe2,0x20,0x2e,0x2e,0x04};
    static const unsigned char reader[] = {0x08,0xc2,0x30,0x29,0xff,0x00,0xc9,0xff,0x00,0xd0,0x05,0xa9,0x00,0x00,0x80,0x12,0x0a,0xaa,0xbf,0x00,0xb0,0x04,0x85,0x57,0xe2,0x30,0xa9,0x04,0x85,0x59,0xc2,0x20,0xb7,0x57,0x28,0x60};
    static const unsigned char reader2[] = {0xc2,0x30,0x29,0xff,0x00,0xc9,0xff,0x00,0xd0,0x05,0xa9,0x00,0x00,0x80,0x12,0x0a,0xaa,0xbf,0x00,0xb0,0x04,0x85,0x57,0xe2,0x30,0xa9,0x04,0x85,0x59,0xc2,0x20,0xb7,0x57,0x60};
    static const unsigned char chain0[] = {0xc3,0x82};
    static const unsigned char chain1[] = {0xff,0xb2,0x88};
    static const unsigned char chain2[] = {0x0c,0x11,0x66,0x95,0x00,0x11,0x00,0x0d,0x05,0x07,0x0a,0x00,0x0d,0x00,0xff,0x04,0x80,0x66,0xba,0x00,0x22,0x02,0x00};
    static const unsigned char chain3[] = {0x05,0xda};
    static const unsigned char chain4[] = {0x02,0x01,0x00,0x82,0xe0,0xff,0x65,0xe1};
    static const unsigned char chain5[] = {0x07,0x08,0xe4,0x01,0xff,0x00,0x00,0x08,0x08,0xf8,0x04,0x40,0x00,0x00,0x09,0x04,0xe8,0x01,0xff,0x00,0x00,0x09,0x05,0xf8,0x04,0x51,0x00,0x00,0xff,0xff};
    static const unsigned char chain6[] = {0xb7,0xda};
    static const unsigned char chain7[] = {0x55,0xdd};
    /* Only original control bytes are authored here; dialogue stays local. */
    static const unsigned char chain8[] = {0xf4,0x01,0x00};
    static const unsigned char chain9[] = {0xf4,0x01,0x01};
    static const unsigned char message_prefix[] = {0xfd,0xea,0x00};
    static const unsigned char chain10[] = {0xe2,0x30,0xa4,0x83,0xe6,0x83,0xb7,0x84,0xc9,0xe0,0x90,0x0d,0xc9,0xff,0xf0,0x09,0x38,0xe9,0xe0,0x22,0x06,0x91,0x02};
    static const unsigned char chain11[] = {0x4c,0x03,0xac};
    static const unsigned char chain12[] = {0x22,0x20,0xff,0x00};
    static const unsigned char chain13[] = {0xe2,0xaf};
    static const unsigned char chain14[] = {0xe2,0x20,0xa9,0x01,0x22,0x03,0xff,0x00,0xe2,0x30,0x68,0x68,0x68,0xa4,0x83,0xe6,0x83,0xc2,0x20,0xb7,0x84,0x85,0x00,0x6b};
    static const unsigned char chain15[] = {0xc2,0x20,0xa5,0x00,0xeb,0x22,0x0f,0xc0,0x02,0x60};
    static const unsigned char chain16[] = {0x4c,0x1a,0xea};
    static const unsigned char chain17[] = {0xe2,0x30,0x8d,0x9f,0x04};
    int valid = Bytes(0x08800c,chain0,sizeof(chain0)) &&
        Bytes(0x0882c3,chain1,sizeof(chain1)) &&
        Bytes(0x0888b2,chain2,sizeof(chain2)) &&
        Bytes(0x0ad808,chain3,sizeof(chain3)) &&
        Bytes(0x0ada05,chain4,sizeof(chain4)) &&
        Bytes(0x0ae082,chain5,sizeof(chain5)) &&
        Bytes(0x04d080,chain6,sizeof(chain6)) &&
        Bytes(0x04d0a2,chain7,sizeof(chain7)) &&
        Bytes(0x04dab7,message_prefix,sizeof(message_prefix)) &&
        Bytes(0x04dae1,chain8,sizeof(chain8)) &&
        Bytes(0x04dd55,message_prefix,sizeof(message_prefix)) &&
        Bytes(0x04dd7f,chain9,sizeof(chain9)) &&
        Bytes(0x02aa87,chain10,sizeof(chain10)) &&
        Bytes(0x029106,chain11,sizeof(chain11)) &&
        Bytes(0x02ac03,chain12,sizeof(chain12)) &&
        Bytes(0x02ac2f,chain13,sizeof(chain13)) &&
        Bytes(0x02afe2,chain14,sizeof(chain14)) &&
        Bytes(0x02a99c,chain15,sizeof(chain15)) &&
        Bytes(0x02c00f,chain16,sizeof(chain16)) &&
        Bytes(0x02ea1a,chain17,sizeof(chain17)) &&
        Bytes(0x04a500,shop_ptr,sizeof(shop_ptr)) &&
        Bytes(0x04a582,shop0,sizeof(shop0)) && Bytes(0x04a586,shop1,sizeof(shop1)) &&
        Bytes(0x029a22,display,sizeof(display)) &&
        Bytes(0x02eb95,purchase,sizeof(purchase)) &&
        Bytes(0x029f99,reader,sizeof(reader)) && Bytes(0x02fdce,reader2,sizeof(reader2));
    for (size_t i=0; valid && i<sizeof(gear)/sizeof(gear[0]); ++i) {
        const StarterGear *g = &gear[i];
        unsigned char pointer[] = {(unsigned char)g->pointer,(unsigned char)(g->pointer>>8)};
        unsigned char price[] = {(unsigned char)g->half_price,(unsigned char)(g->half_price>>8)};
        valid = Bytes(0x04b000+2*g->item,pointer,2) && Bytes(0x040002+g->pointer,price,2);
    }
    ready = valid && (enabled || trace) &&
        interp_bridge_add_pre_opcode_hook(0x029fbb,BeforePriceReturn) &&
        interp_bridge_add_pre_opcode_hook(0x02fdef,BeforePriceReturn);
    fprintf(stderr,"[foundation_shop] enabled=%d ready=%d\n",enabled,ready);
}
