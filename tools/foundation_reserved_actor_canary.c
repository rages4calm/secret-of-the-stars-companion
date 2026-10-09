/* Authored host canary: external natural packet data, synthetic observer CPU seam calls.
 * No guest execution, save writes or installed-module changes. */
#include "foundation_wide_actors.c"
uint8 g_ram[0x20000]; const uint8 *g_rom; Snes *g_snes; Ppu *g_ppu;
int snes_frame_counter = 1; unsigned char g_snesrecomp_last_hdmaen;
static unsigned hook_count, readonly_calls, test_case;
static struct { uint32_t pc; InterpPreOpcodeHook callback; } hooks[8];
static DmaTransferNotifyHook notify_hook;
bool interp_bridge_add_pre_opcode_hook(uint32_t pc, InterpPreOpcodeHook hook) {
    if(hook_count>=8)return false;
    hooks[hook_count].pc=pc;hooks[hook_count].callback=hook;++hook_count;return true;
}
void dma_set_transfer_notify_hook(DmaTransferNotifyHook hook) { notify_hook=hook; }
void dma_reset_transfer_notify_state(Dma *dma) { (void)dma; }
static void readfile(const char *path, void *dst, size_t size) {
    FILE *file = fopen(path, "rb");
    if (!file || fread(dst, 1, size, file) != size || fgetc(file) != EOF) exit(2);
    fclose(file);
}
static void W16(unsigned at, unsigned value) { g_ram[at] = value; g_ram[at+1] = value >> 8; }
static void W24(unsigned at, unsigned value) { W16(at, value); g_ram[at+2] = value >> 16; }
static void caller(CpuState *cpu, unsigned pc) { W24(cpu->S + 1, pc); }
static void observe(CpuState *cpu, unsigned pc) {
    uint8_t *ram = malloc(sizeof(g_ram)); Ppu *ppu = malloc(sizeof(Ppu));
    CpuState before = *cpu; memcpy(ram, g_ram, sizeof(g_ram)); memcpy(ppu, g_ppu, sizeof(Ppu));
    unsigned found=0;
    for(unsigned i=0;i<hook_count;i++)if(hooks[i].pc==pc){hooks[i].callback(cpu,pc);found=1;break;}
    if(!found)exit(30);
    if (memcmp(ram, g_ram, sizeof(g_ram)) || memcmp(ppu, g_ppu, sizeof(Ppu)) ||
        memcmp(&before, cpu, sizeof(CpuState))) { fprintf(stderr,"Observermutatedguest\n"); exit(3); }
    free(ram); free(ppu); ++readonly_calls;
}
static void notify(const Dma *dma,int channel,const DmaChannel *start,bool complete) {
    uint8_t *ram=malloc(sizeof(g_ram));Ppu *ppu=malloc(sizeof(Ppu));Dma before=*dma;
    memcpy(ram,g_ram,sizeof(g_ram));memcpy(ppu,g_ppu,sizeof(Ppu));
    if(!notify_hook)exit(31);notify_hook(dma,channel,start,complete);
    if(memcmp(ram,g_ram,sizeof(g_ram))||memcmp(ppu,g_ppu,sizeof(Ppu))||memcmp(&before,dma,sizeof(Dma)))exit(32);
    free(ram);free(ppu);++readonly_calls;
}
/* Replay the bounded original seam contexts; guest routine is not executed. */
static int produce(CpuState *cpu) {
    caller(cpu, 0x1d865); cpu->m_flag = cpu->x_flag = 1;
    W16(0x46b, 0x30); W16(0xe34,0x10); W16(0xe38,0x201);
    W16(0xe10, g_ram[0x400] ? 0xefff : 0xffff);
    if(test_case==58)W16(0x42ae,0xa0);
    observe(cpu, 0x1d8b1);
    if (!sequence) return 0;
    unsigned cursor = 0x30, reserved_cursor=0x10;
    for (unsigned i = 0; i < 5; ++i) {
        unsigned at = 0x4000 + i * 18;
        if (g_ram[at] == 255) continue;
        unsigned x = g_ram[at+1] | ((g_ram[at+5]&1)<<8);
        unsigned y = (g_ram[at+2] | ((g_ram[at+5]&2)<<7)) - 1;
        g_ram[0xe13] = i; W24(0xe1c,0x7e0000+at); W16(0xe1a,R16(at+3));
        W16(0xe16,x); W16(0xe18,y); cpu->m_flag=0; cpu->Y=2;
        if(test_case==12)W24(0xe1c,0x7e0000+at+1);
        if(test_case==15)cpu->m_flag=1;
        if(test_case==16)g_ram[0x40e]^=1;
        if(test_case==19)g_ram[0xe10]^=1;
        observe(cpu, 0x1d917); if (!sequence) return 0;
        if (PartyGate(x,255) && PartyGate(y,239)) cursor += 16;
    }
    W16(0x46b,cursor+(test_case==13?4:0)); g_ram[0xe13]=5; cpu->m_flag=1;
    observe(cpu,0x1d988); if (!sequence || !party_done) return 0;
    if(test_case==14)W16(0x46b,cursor+16);
    caller(cpu,0x1d86f); observe(cpu,0x1da56); if (!sequence) return 0;
    for (unsigned i = 0; i < 19; ++i) {
        unsigned at=0x4100+i*25; if (g_ram[at]==255) continue;
        int x=Signed(R16(at+1)-R16(0x2ad)), y=Signed(R16(at+3)-R16(0x2af));
        g_ram[0xe14]=i; W24(0xe1c,0x7e0000+at); W16(0xe1a,R16(at+5));
        W16(0xe16,x); W16(0xe18,y); cpu->m_flag=0; cpu->Y=3;
        if(i==17 && test_case==57)continue;
        if(i==17 && test_case==53)W24(0xe1c,0x7e0000+at+1);
        if(i==17 && test_case==54){W16(at+5,0xb0);W16(0xe1a,0xb0);}
        if(i==17 && test_case==55){W16(at+5,0xa8);W16(0xe1a,0xa8);g_ram[at]=0;}
        if(i==17 && test_case==58){W16(at+5,0xa8);W16(0xe1a,0xa8);}
        if(i==17 && test_case==60){W16(at+5,2048);W16(0xe1a,2048);}
        if(i==17 && test_case==56)g_ram[0xe10]^=1;
        observe(cpu,0x1dab6); if (!sequence) return 0;
        if(i==17 && test_case==52){observe(cpu,0x1dab6);if(!sequence)return 0;}
        if (Gate(x,255) && Gate(y,239)) {
            if(i<17)cursor+=16;else reserved_cursor+=16;
        }
    }
    W16(0x46b,cursor+(test_case==50?16:0));
    W16(0xe34,reserved_cursor+(test_case==48?4:0));
    W16(0xe38,0x201+(reserved_cursor-0x10)/16+(test_case==49?1:0));
    g_ram[0xe14]=19; cpu->m_flag=1;
    observe(cpu,0x1db2c); if (!sequence_done) return 0;
    caller(cpu,0x1d873); observe(cpu,0x1de29);
    return queued.valid;
}
static void stage_synthetic(void) {
    memset(g_ram+0x2200,0,kPacketBytes); unsigned slot=12,reserved_slot=4;
    for(unsigned i=0;i<12;i++)W16(0x2200+i*4,0xf080);
    memset(g_ram+0x2400,0x55,3);
    for (unsigned family=0;family<2;++family) {
        for(unsigned i=0;i<(family?19:5);++i) {
            unsigned at=(family?0x4100:0x4000)+i*(family?25:18);
            if(g_ram[at]==255)continue;
            int x=family?Signed(R16(at+1)-R16(0x2ad)):(g_ram[at+1]|((g_ram[at+5]&1)<<8));
            int y=family?Signed(R16(at+3)-R16(0x2af)):(int)(g_ram[at+2]|((g_ram[at+5]&2)<<7))-1;
            if(family?(!Gate(x,255)||!Gate(y,239)):(!PartyGate(x,255)||!PartyGate(y,239)))continue;
            unsigned base=R16(at+(family?5:3)), phase=g_ram[family?0x475:at+10]>>7;
            unsigned desc=0xe9800+(base+g_ram[at]*2+phase)*8;
            unsigned *cursor=(family&&i>=17)?&reserved_slot:&slot;
            for(unsigned part=0;part<4;++part,++*cursor) {
                int xx=x+(part&1)*8, yy=y-!!family+(part>>1)*8;
                unsigned word=RomWord(desc+part*2)&(g_ram[0x400]?0xefff:0xffff);
                unsigned target=*cursor,shift=target%4*2;
                g_ram[0x2200+target*4]=xx; g_ram[0x2201+target*4]=yy; W16(0x2202+target*4,word);
                g_ram[0x2400+target/4]=(g_ram[0x2400+target/4]&~(3u<<shift))|(((xx>>8)&1)<<shift);
            }
        }
    }
}
static void scanout(Ppu *ppu,const uint8_t bytes[544]) {
    for(unsigned i=0;i<256;++i)ppu->oam[i]=bytes[i*2]|(unsigned)bytes[i*2+1]<<8;
    memcpy(ppu->highOam,bytes+512,32);
}
/* Preserve the derived virtual ranks, then use deliberately overlapping
 * opaque host control pixels to test the public PPU tie-order seam. */
static unsigned priority_control(Ppu *source,Ppu *picture) {
    memcpy(picture,source,sizeof(Ppu));
    unsigned count=FoundationWideActorsPrepareLine(source,80,picture),found=0;
    PpuExtraObject selected[3]; uint16_t pixels[3][64];
    unsigned slots[3]={5,9,12};
    for(unsigned k=0;k<3;k++) {
        unsigned matched=0;
        for(unsigned j=0;j<count;j++)if(objects[j].oamSlot==slots[k]) {
            selected[k]=objects[j];matched=1;break;
        }
        if(!matched)return 0;
        selected[k].x=300;selected[k].y=79;selected[k].width=8;selected[k].height=8;
        selected[k].stride=8;selected[k].priority=2;selected[k].math=0;
        for(unsigned p=0;p<64;p++)pixels[k][p]=0x8001+k;
        selected[k].pixels=pixels[k];++found;
    }
    PpuExtraObject order_input[3]={selected[2],selected[1],selected[0]};
    uint16_t depth[8]={0},colors_out[8]={0};uint64_t order_out[8];
    for(unsigned j=0;j<8;j++)order_out[j]=UINT64_MAX;
    if(!PpuComposeExtraObjects(order_input,3,79,300,8,0,depth,colors_out,order_out))return 0;
    for(unsigned j=0;j<8;j++)if(colors_out[j]!=0x8001 || (order_out[j]>>32)!=5)return 0;
    for(unsigned j=0;j<8;j++){order_out[j]=UINT64_MAX;colors_out[j]=0;depth[j]=0;}
    if(!PpuComposeExtraObjects(order_input,2,79,300,8,0,depth,colors_out,order_out))return 0;
    for(unsigned j=0;j<8;j++)if(colors_out[j]!=0x8002 || (order_out[j]>>32)!=9)return 0;
    return found==3;
}
int main(int argc,char **argv) {
    if(argc!=8)return 2;
    unsigned scenario=atoi(argv[7]); test_case=scenario;
    uint8_t actual[544],*rom=malloc(1572864),*initial=malloc(sizeof(g_ram));
    Ppu *source=ppu_init(),*picture=calloc(1,sizeof(Ppu)); g_ppu=source;
    Snes snes={0};Cart cart={0};Dma dma={0};CpuState cpu={0};
    snes.cart=&cart;snes.ppu=source;snes.dma=&dma;cart.romImageSize=1572864;dma.snes=&snes;g_snes=&snes;g_rom=rom;
    readfile(argv[1],rom,1572864);readfile(argv[2],g_ram,sizeof(g_ram));readfile(argv[3],source->vram,65536);
    readfile(argv[4],source->cgram,512);readfile(argv[5],actual,544);memcpy(initial,g_ram,sizeof(g_ram));
    source->inidisp=15;source->bgmode=9;source->obsel=3;source->bgXsc[0]=0x49;source->bgXsc[1]=0x59;source->bgXsc[2]=0x51;
    source->bgTileAdr=0x400;source->screenEnabled[0]=0x17;source->windowsel=0x10011;source->screenWindowed[0]=0x17;
    source->window1left=source->window2left=1;source->hScroll[0]=R16(0x2ad)&1023;source->vScroll[0]=R16(0x2af)&1023;
    cpu.D=0xe00;cpu.DB=cpu.PB=1;cpu.S=0x1ed0;
    FoundationWideActorsSetEnabled(1);FoundationWideActorsInit();
    if(!enabled||hook_count!=7||!notify_hook)return 33;
    FoundationWideActorsBeforeFrame();
    if(!Scene(source))return 10;
    unsigned natural_stage_match=!memcmp(initial+0x2200,actual,544);
    if(!scenario && !natural_stage_match)return 11;
    if(scenario) {
        for(unsigned i=0;i<5;++i)g_ram[0x4000+i*18]=255;
        for(unsigned i=0;i<19;++i)g_ram[0x4100+i*25]=255;
        memcpy(g_ram+0x4000,initial+0x4000,18);
        g_ram[0x4000]=0;g_ram[0x4001]=300&255;g_ram[0x4002]=80;g_ram[0x4005]=1;g_ram[0x400a]=0;
        if(scenario==1) { memcpy(g_ram+0x4012,g_ram+0x4000,18);g_ram[0x4013]=505&255;g_ram[0x401c]=128; }
        if(scenario==2)W16(0x4003,0xb0);
        if(scenario==3)W16(0x4003,0xa8);
        if(scenario==4)g_ram[0x4000]=4;
        if(scenario==5)g_ram[0x401]=14;
        if(scenario==6)g_ram[0x407]=1;
        if(scenario==7)W16(0x471,1);
        if(scenario==8)g_ram[0x4100+17*25]=0;
        if(scenario==9){g_ram[0x400a]=128;g_ram[0x475]=0;}
        if(scenario==10){g_ram[0x4001]=100;g_ram[0x4005]=0;}
        if(scenario==11)cpu.DB=0;
        if(scenario==18)source->bgmode=1;
        if(scenario==20){g_ram[0x4000]=1;W16(0x4003,0xa7);}
        if(scenario==21) {
            memcpy(g_ram+0x4100,initial+0x414b,25);g_ram[0x4100]=0;W16(0x4105,0xa8);
            W16(0x4101,R16(0x2ad)+254);W16(0x4103,R16(0x2af)+80);
        }
        if(scenario>=30) {
            for(unsigned j=0;j<2;j++) {
                unsigned at=0x4100+(17+j)*25;
                memcpy(g_ram+at,initial+0x414b,25);g_ram[at]=j?1:2;W16(at+5,j?0x268:0xa0);
                W16(at+1,R16(0x2ad)+254);W16(at+3,R16(0x2af)+80);
            }
            if(scenario==31)g_ram[0x42a9]=255;
            if(scenario==32)W16(0x42aa,R16(0x2ad)+288);
            if(scenario==33){W16(0x42aa,R16(0x2ad)+288);W16(0x42c3,R16(0x2ad)-40);}
            if(scenario==34)W16(0x42c3,R16(0x2ad)-40);
            if(scenario==35)g_ram[0x42c2]=255;
            if(scenario==36){W16(0x42aa,R16(0x2ad)+240);W16(0x42c3,R16(0x2ad)+240);}
            if(scenario==40)W16(0x42ae,0xb0);
            if(scenario==41)W16(0x42c7,0xb0);
            if(scenario==42){W16(0x42ae,0xa8);g_ram[0x42a9]=0;}
            if(scenario==43){W16(0x42c7,0xa8);g_ram[0x42c2]=0;}
            if(scenario==58){W16(0x42ae,0xa8);g_ram[0x42a9]=0;}
            if(scenario==59)W16(0x42ae,2048);
            if(scenario==44)g_ram[0x42a9]=4;
            if(scenario==51)g_ram[0x42a9]=255;
        }
        stage_synthetic();memcpy(actual,g_ram+0x2200,544);
        if(scenario==10)g_ram[0x2232]^=1;
        if(scenario==45)g_ram[0x2210]^=1;
        if(scenario==46)g_ram[0x2212]^=1;
        if(scenario==47)g_ram[0x2401]^=2;
        if(scenario==51)g_ram[0x2220]^=1;
    }
    unsigned accepted=produce(&cpu),expect=(!scenario||scenario==1||scenario==8||scenario==9||scenario==21||scenario==42||scenario==43||scenario==58||(scenario>=30&&scenario<=36));
    if(accepted!=expect)return 12;
    if(!accepted){printf("{\"accepted\":false,\"negative_guard_passed\":true,\"readonly_calls\":%u}\n",readonly_calls);return 0;}
    DmaChannel channel={0};channel.bAdr=4;channel.aBank=0x7e;channel.aAdr=0x2200;channel.size=544;
    notify(&dma,7,&channel,false);if(!transfer_valid||displayed.valid)return 13;
    scanout(source,actual);notify(&dma,7,&channel,true);if(!displayed.valid)return 14;
    unsigned party_count=0,party_seen=displayed.seen&31u,side_count=0,party_side_count=0,regular_count=0,reserved_count=0,reserved_side_count=0;
    if(scenario==9 && (displayed.actors[0].phase!=1 || displayed.actors[0].descriptor!=
        0xe9800+(R16(0x4003)+1)*8))return 21;
    if(FoundationWideActorsPrepareLine(source,0,picture)||FoundationWideActorsPrepareLine(source,225,picture)||
        FoundationWideActorsPrepareLine(source,80,source))return 22;
    for(unsigned i=0;i<kParty;++i)party_count+=displayed.actors[i].present;
    for(unsigned i=kParty;i<kActors;++i)regular_count+=displayed.actors[i].present;
    for(unsigned i=kParty+kAppendRegular;i<kActors;++i)reserved_count+=displayed.actors[i].present;
    for(unsigned line=1;line<=224;++line){
        memcpy(picture,source,sizeof(Ppu));unsigned count=FoundationWideActorsPrepareLine(source,line,picture);
        unsigned party_line=0,reserved_line=0;
        for(unsigned i=0;i<count;++i){
            if(objects[i].oamSlot<4||objects[i].oamSlot>99)return 15;
            reserved_line+=objects[i].oamSlot<12;
            party_line+=objects[i].oamSlot>=12&&objects[i].oamSlot<32;
        }
        if(count>side_count)side_count=count;
        if(party_line>party_side_count)party_side_count=party_line;
        if(reserved_line>reserved_side_count)reserved_side_count=reserved_line;
    }
    unsigned reserved_end=displayed.reserved_end_slot,append_end=R16(0x46b)/4;
    unsigned priority_checked=scenario==30?priority_control(source,picture):0;
    if(scenario==30&&!priority_checked)return 34;
    if(scenario==21 && (displayed.actors[kParty].base!=0xa8 || displayed.actors[kParty].descriptor!=0xe9d40 || append_end!=16))return 35;
    unsigned a8_checked=scenario==21||scenario==42||scenario==43||scenario==58;
    if(a8_checked) {
        unsigned at=scenario==21?kParty:scenario==43?kParty+18:kParty+17;
        if(displayed.actors[at].base!=0xa8||displayed.actors[at].descriptor!=0xe9d40)return 36;
    }
    if(scenario>=30&&scenario<=36) {
        unsigned expected_reserved=(scenario==30||scenario==36)?12:scenario==33?4:8;
        if(reserved_end!=expected_reserved||append_end!=12||R16(0xe34)!=reserved_end*4||R16(0xe38)!=0x201+(reserved_end-4)/4)return 25;
        if(scenario!=36&&!reserved_side_count)return 26;
        /* Transfer captures its producer token. A new byte-identical queued
         * producer must not replace the already started DMA's identity. */
        unsigned old_epoch=displayed.epoch;
        if(!produce(&cpu))return 27;
        notify(&dma,7,&channel,false);unsigned transfer_epoch=transfer.epoch;
        if(!produce(&cpu)||queued.epoch==transfer_epoch)return 28;
        scanout(source,actual);notify(&dma,7,&channel,true);
        if(!displayed.valid||displayed.epoch!=transfer_epoch||displayed.epoch==queued.epoch||displayed.epoch==old_epoch)return 29;
    }
    if(Period512(300,128)!=300||Period512(505,128)!=-7||Period512(0xffff,112)!=-1)return 16;
    if(scenario==1 && (!side_count||party_count!=2||party_seen!=3||displayed.start_slot!=16))return 17;
    if(scenario==1) {
        memcpy(picture,source,sizeof(Ppu));unsigned count=FoundationWideActorsPrepareLine(source,80,picture);
        unsigned seen300=0,seen308=0,seenminus7=0;
        for(unsigned i=0;i<count;++i){seen300+=objects[i].x==300;seen308+=objects[i].x==308;seenminus7+=objects[i].x==-7;}
        if(count!=3||seen300!=1||seen308!=1||seenminus7!=1)return 23;
        source->hScroll[0]=(source->hScroll[0]+2)&1023;
        memcpy(picture,source,sizeof(Ppu));count=FoundationWideActorsPrepareLine(source,80,picture);
        unsigned seen298=0,seen306=0,seenminus9=0,seenminus1=0;
        for(unsigned i=0;i<count;++i){seen298+=objects[i].x==298;seen306+=objects[i].x==306;seenminus9+=objects[i].x==-9;seenminus1+=objects[i].x==-1;}
        if(count!=4||seen298!=1||seen306!=1||seenminus9!=1||seenminus1!=1)return 24;
        source->hScroll[0]=(source->hScroll[0]-2)&1023;
    }
    unsigned good_epoch=displayed.epoch;source->oam[0]^=1;
    if(FoundationWideActorsPrepareLine(source,80,picture))return 18;source->oam[0]^=1;
    channel.size=543;notify(&dma,7,&channel,false);if(displayed.valid||transfer_valid)return 19;
    FoundationWideActorsReset();if(displayed.valid||queued.valid||producing.count)return 20;
    printf("{\"accepted\":true,\"natural_stage_matches_actual_scanout\":%s,\"party_count\":%u,\"regular_count\":%u,\"party_seen\":%u,\"max_side_pieces_per_line\":%u,\"max_party_side_pieces_per_line\":%u,\"completed_epoch\":%u,\"readonly_calls\":%u,\"coordinate_checks\":3,\"packet_and_restore_guards\":6,\"synthetic_raster_delta_checked\":%s,\"reserved_count\":%u,\"reserved_end_slot\":%u,\"append_end_slot\":%u,\"max_reserved_side_pieces_per_line\":%u,\"synthetic_priority_control_checked\":%s,\"regular_A8_descriptor_checked\":%s}\n",natural_stage_match?"true":"false",party_count,regular_count,party_seen,side_count,party_side_count,good_epoch,readonly_calls,scenario==1?"true":"false",reserved_count,reserved_end,append_end,reserved_side_count,priority_checked?"true":"false",a8_checked?"true":"false");
    (void)argv[6]; return 0;
}
