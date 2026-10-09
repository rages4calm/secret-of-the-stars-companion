/* Private portable host test driver. Contexts/records are explicitly synthetic. */
#include "foundation_large_actor_canary.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
static void Read(const char *path, void *out, size_t size) {
    FILE *f = fopen(path,"rb");
    if (!f || fread(out,1,size,f)!=size || fgetc(f)!=EOF) exit(2);
    fclose(f);
}
static unsigned R16(const uint8_t *ram,unsigned at) {return ram[at]|(unsigned)ram[at+1]<<8;}
static void W16(uint8_t *ram,unsigned at,unsigned value){ram[at]=value;ram[at+1]=value>>8;}
static LargeSeam Seam(const LargeView *view,unsigned family,unsigned index) {
    const uint8_t *ram=view->ram;unsigned at=(family?0x4100:0x4000)+index*(family?25:18);
    LargeSeam seam={0};seam.pc=family?0x1db68:0x1d989;seam.caller=family?0x1d86f:0x1d865;
    seam.pb=seam.db=seam.x=1;seam.d=0xe00;seam.s=0x1ed0;seam.y=3;seam.base=R16(ram,at+(family?5:3));
    seam.record_pointer=0x7e0000+at;seam.descriptor=0xe9800+seam.base*8+ram[at]*4;
    seam.mask=ram[0x400]?0xefff:0xffff;seam.coordinate_x=R16(ram,at+1)-R16(ram,0x2ad);
    seam.coordinate_y=R16(ram,at+3)-R16(ram,0x2af);return seam;
}
int main(int argc,char **argv) {
    if(argc!=15)return 2;
    uint8_t *rom=malloc(1572864),*ram=malloc(131072),initial[544],final[544];
    uint16_t *vram=malloc(65536),*cgram=malloc(512);LargeReplay state={0};
    Read(argv[2],rom,1572864);Read(argv[3],ram,131072);Read(argv[4],vram,65536);Read(argv[5],cgram,512);
    LargeView view={ram,131072,vram,cgram,32768,256,3,0,0,1};
    if(!LargeBindRom(rom,1572864))return 3;
    if(!strcmp(argv[1],"decode")) {
        FILE *f=fopen(argv[6],"rb"),*out=fopen(argv[8],"wb");if(!f||!out)return 2;
        uint16_t word,pixels[256];unsigned count=0;
        while(fread(&word,2,1,f)==1){if(!LargeDecode(&view,word,pixels))return 4;fwrite(pixels,2,256,out);++count;}
        fclose(f);fclose(out);printf("{\"words\":%u,\"pixels\":%u}\n",count,count*256);return 0;
    }
    Read(argv[6],initial,544);Read(argv[7],final,544);
    unsigned family=atoi(argv[9]),index=atoi(argv[10]),second=atoi(argv[11]),secondindex=atoi(argv[12]),guard=atoi(argv[13]);
    (void)argv[14];LargeSeam seam=Seam(&view,family,index);
    if(guard==1)seam.db=0;if(guard==2)seam.pc++;if(guard==3)seam.caller++;
    if(guard==4)seam.decimal=1;if(guard==5)seam.emulation=1;if(guard==6)seam.m=1;
    if(guard==7)seam.x=0;if(guard==8)seam.d++;if(guard==9)seam.y++;
    if(guard==10)seam.record_pointer++;if(guard==11)seam.base++;if(guard==12)seam.mask^=1;
    if(guard==13)seam.coordinate_x++;if(guard==14)seam.coordinate_y++;if(guard==15)seam.descriptor++;
    if(guard==16)view.obsel=0x23;if(guard==17)view.rotation=1;if(guard==18)view.setini=1;
    if(guard==19)view.field_eligible=0;if(guard==20)view.ram_size--;
    if(guard==21)ram[0x407]=1;if(guard==22)W16(ram,0x471,1);if(guard==23)ram[0x401]=14;
    if(guard==24)ram[(family?0x4100:0x4000)+index*(family?25:18)]=255;
    if(guard==25){unsigned at=(family?0x4100:0x4000)+index*(family?25:18);W16(ram,at+(family?5:3),0xa8);seam=Seam(&view,family,index);}
    if(guard==38)view.vram_words--;if(guard==39)view.cgram_words--;
    if(guard==49)view.ram_size=SIZE_MAX;if(guard==50)view.vram_words=SIZE_MAX;if(guard==51)view.cgram_words=SIZE_MAX;
    if(guard==52)view.ram=NULL;if(guard==53)view.vram=NULL;if(guard==54)view.cgram=NULL;
    if(guard==71){uint8_t *bad=malloc(1572864);memcpy(bad,rom,1572864);bad[0]^=1;if(LargeBindRom(bad,1572864))return 6;}
    if(guard==72 && LargeBindRom(rom,1572863))return 6;
    if(guard==73 && LargeBindRom(NULL,0))return 6;
    uint8_t *inputs=malloc(1572864+131072+65536+512+1088),*next=inputs;
    memcpy(next,rom,1572864);next+=1572864;memcpy(next,ram,131072);next+=131072;
    memcpy(next,vram,65536);next+=65536;memcpy(next,cgram,512);next+=512;
    memcpy(next,initial,544);next+=544;memcpy(next,final,544);
    int stage=0,accepted=LargeBegin(&state,&view,initial,544);
    if(accepted){stage=1;accepted=LargeCapture(guard==63?NULL:&state,&view,guard==60?NULL:&seam,guard==62?2:family,guard==61?(family?19:5):index);}
    if(accepted && second<=1){LargeSeam later=Seam(&view,second,secondindex);accepted=LargeCapture(&state,&view,&later,second,secondindex);}
    uint8_t packet[544];memcpy(packet,final,544);
    if(guard==26)packet[2]^=1;if(guard==27)packet[512]^=2;
    if(accepted){stage=2;accepted=LargeSeal(&state,guard==70?NULL:packet,guard==56?SIZE_MAX:guard==28?543:544);}
    LargeTransfer transfer={7,0x7e,0x2200,544,4,0,0,0,0,1};
    if(guard==29)transfer.channel=6;if(guard==30)transfer.bank=0x7f;if(guard==31)transfer.address++;
    if(guard==32)transfer.size=543;if(guard==43)transfer.b_address=5;if(guard==44)transfer.mode=1;
    if(guard==45)transfer.from_b=1;if(guard==46)transfer.fixed=1;if(guard==47)transfer.decrement=1;if(guard==48)transfer.complete=0;
    if(accepted){stage=3;accepted=LargeComplete(&state,&transfer,guard==69?NULL:guard==33?initial:packet,guard==55?SIZE_MAX:544);}
    LargePiece pieces[2];uint16_t pixels[2][256];unsigned count=0;
    if(accepted){stage=4;count=LargePrepare(&state,&view,packet,544,0,0,80,pieces,pixels);}
    if(guard>=34 && guard<=37 && accepted) {
        if(guard==37)ram[0x40e]^=1;
        count=LargePrepare(&state,&view,packet,544,guard==36?INT_MIN:0,0,guard==34?0:guard==35?225:80,pieces,pixels);
        if(guard==37)ram[0x40e]^=1;
        accepted=count!=0;
    }
    if(guard==40 && accepted)accepted=LargeDecode(&view,state.last.pieces[0].word,vram);
    if(guard==41 && accepted)accepted=LargePrepare(&state,&view,packet,544,0,0,80,(LargePiece*)ram,pixels)!=0;
    if(guard==42 && accepted){LargeReset(&state);accepted=LargePrepare(&state,&view,packet,544,0,0,80,pieces,pixels)!=0;}
    if(guard>=57 && guard<=59 && accepted)accepted=LargePrepare(&state,&view,packet,544,guard==57?INT_MAX:0,guard==58?INT_MIN:guard==59?INT_MAX:0,80,pieces,pixels)!=0;
    if(guard==64 && accepted)accepted=LargeDecode(&view,state.last.pieces[0].word,NULL);
    if(guard>=65 && guard<=68 && accepted)accepted=LargePrepare(&state,&view,guard==67?NULL:packet,guard==68?SIZE_MAX:544,0,0,80,guard==65?NULL:pieces,guard==66?NULL:pixels)!=0;
    if(guard==74 && accepted)accepted=LargeDecode(&view,state.last.pieces[0].word,(uint16_t*)rom);
    next=inputs;unsigned unchanged=!memcmp(next,rom,1572864);next+=1572864;
    unchanged&=!memcmp(next,ram,131072);next+=131072;unchanged&=!memcmp(next,vram,65536);next+=65536;
    unchanged&=!memcmp(next,cgram,512);next+=512;unchanged&=!memcmp(next,initial,544);next+=544;unchanged&=!memcmp(next,final,544);
    if(!unchanged)return 5;
    printf("{\"accepted\":%s,\"stage\":%d,\"writers\":%u,\"collision\":%u,\"source_inputs_unchanged\":true,\"margin_parts_at_line80\":%u,\"last_family\":%u,\"last_index\":%u,\"descriptor\":%u,\"pieces\":[",accepted?"true":"false",stage,state.writers,state.collision,count,state.last.family,state.last.index,state.last.descriptor);
    for(unsigned p=0;p<2;++p)printf("%s{\"x\":%d,\"y\":%d,\"word\":%u,\"emitted\":%u,\"slot\":%u}",p?",":"",state.last.pieces[p].x,state.last.pieces[p].y,state.last.pieces[p].word,state.last.pieces[p].emitted,state.last.pieces[p].slot);
    puts("]}");return 0;
}
