#include "foundation_journal.h"
#include <stdio.h>
#include <string.h>

static unsigned checks;
static int Check(int good) { ++checks; return good; }
int main(void) {
    static unsigned char ram[0x20000], original[0x20000];
    memset(ram, 0xff, sizeof(ram));
    if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 0) ||
        !Check(JournalPossessionGroups(NULL, sizeof(ram)) == 0) ||
        !Check(JournalPossessionGroups(ram, 0x53b2) == 0)) return 1;
    for (unsigned group = 0; group < 2; ++group) {
        for (unsigned slot = 0; slot < 32; ++slot) {
            unsigned index = 0x5373 + group * 32 + slot;
            ram[index] = 0x40;
            memcpy(original, ram, sizeof(ram));
            if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 1u << group) ||
                !Check(!memcmp(original, ram, sizeof(ram)))) return 1;
            ram[index] = 0xff;
            if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 0)) return 1;
        }
    }
    ram[0x5373] = ram[0x53b2] = 0x40;
    if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 3)) return 1;
    ram[0x5373] = 0xff;
    if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 2)) return 1;
    ram[0x53b2] = 0xff;
    ram[0x5360] = ram[0x5372] = ram[0x5372 - 1] = 0x40;
    ram[0x53b3] = 0x40;
    if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 0)) return 1;
    memset(ram + 0x5373, 0x3f, 64);
    if (!Check(JournalPossessionGroups(ram, sizeof(ram)) == 0)) return 1;
    printf("{\"passed\":true,\"checks\":%u,\"historical_completion\":false}\n", checks);
    return 0;
}
