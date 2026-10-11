/* Read-only original 01:C564 exits and 01:C88C/02:9DCE location-name data.
 * Only clean-title current scene0 town entrances are exposed. */
#include "foundation_map_points.h"
#include "sha256.h"
#include <string.h>

enum { ImageSize=1572864, RamSize=0x20000, MaxPoints=32, MaxExits=512 };
static const uint8_t clean_identity[32]={
    0x7d,0xa4,0xa3,0xcf,0xa5,0xde,0x4b,0xb4,0x72,0x2a,0x6e,0x2a,0x42,0xc2,0x6a,0xae,
    0x32,0x2b,0x5e,0x66,0x8f,0x16,0x45,0xd8,0xc8,0x70,0xfb,0x99,0xe6,0x08,0x06,0x00};
typedef struct Image {const uint8_t *rom; size_t size;} Image;
static int Read(const Image *image,unsigned address,unsigned size,unsigned *value) {
    unsigned bank=address>>16,low=address&0xffff;
    if(bank>=0x30||low<0x8000||!size||size>3||low+size>0x10000)return 0;
    size_t offset=(size_t)bank*0x8000+low-0x8000;
    if(!image->rom||offset>image->size||size>image->size-offset)return 0;
    *value=0;for(unsigned i=0;i<size;++i)*value|=(unsigned)image->rom[offset+i]<<(8*i);
    return 1;
}
static unsigned Story(const uint8_t *ram,unsigned selector,unsigned nibble) {
    if(selector<0x78)return ram[0x5360+((selector>>3)&1)]&(0x80u>>(selector&7));
    if(selector==0x7e)return ram[0x5361]&15;
    if(selector==255){unsigned v=ram[0x5362+(nibble>>1)];return nibble&1?v&15:v>>4;}
    return ram[0x5362+((selector&127)>>3)]&(0x80u>>(selector&7));
}
static int Condition(const uint8_t *ram,unsigned selector,unsigned a,unsigned b) {
    unsigned stage=ram[0x5372];
    switch(selector){
    case 0:return stage<a||(stage==a&&!Story(ram,b,b));
    case 1:return stage==a&&Story(ram,b,b);
    case 2:return stage<=a;
    case 3:return stage==a&&Story(ram,0x7e,0)==b;
    case 4:return Story(ram,a|128,b)!=0;
    case 5:return Story(ram,a|128,b)==0;
    case 6:return Story(ram,255,a)==b;
    case 7:return (ram[0x4b6]&128)!=0;
    case 255:return 1;
    default:return 0;
    }
}
static int Selected(const Image *image,const uint8_t *ram,unsigned scene,unsigned *stream) {
    unsigned pointer;
    if(scene>=337||!Read(image,0x088000+scene*2,2,&pointer))return 0;
    pointer|=0x080000;
    for(unsigned n=0;n<52;++n){
        unsigned selector,a=0,b=0,value;
        if(pointer<0x0882a2||pointer>=0x0887e5||!Read(image,pointer,1,&selector)||(selector!=255&&selector>7))return 0;
        unsigned size=selector==255?3:5;
        if(pointer+size>0x0887e5)return 0;
        if(selector!=255&&(!Read(image,pointer+1,1,&a)||!Read(image,pointer+2,1,&b)))return 0;
        if(!Read(image,pointer+size-2,2,&value))return 0;
        if(Condition(ram,selector,a,b)){
            *stream=0x080000|value;
            return *stream>=0x0887e5&&*stream+15<=0x08aa00;
        }
        pointer+=size;
    }
    return 0;
}
static int Take(const Image *image,unsigned *cursor,unsigned size,unsigned *value) {
    if(*cursor+size>0x08aa00||!Read(image,*cursor,size,value))return 0;
    *cursor+=size;return 1;
}
/* Match original StreamMatches consumption, including the secondary map's
 * velocity-only branch (no dimension byte). Names are current-state selected. */
static int NameIndex(const Image *image,const uint8_t *ram,unsigned scene,int *index) {
    unsigned stream,flags,value,mode,cursor;
    if(!Selected(image,ram,scene,&stream)||!Read(image,stream,2,&flags))return 0;
    cursor=stream+15;
    const unsigned masks[]={0x6000,0x1000,0x80,0x40,0x20,0x10};
    const unsigned sizes[]={2,1,2,1,1,2};
    for(unsigned i=0;i<6;++i)if((flags&masks[i])&&!Take(image,&cursor,sizes[i],&value))return 0;
    if(flags&8){
        if(!Take(image,&cursor,1,&mode)||!Take(image,&cursor,1,&value)||!Take(image,&cursor,2,&value))return 0;
        if(mode&128){if(!Take(image,&cursor,1,&value))return 0;}
        else if(!Take(image,&cursor,2,&value)||!Take(image,&cursor,2,&value))return 0;
    }
    if((flags&4)&&!Take(image,&cursor,2,&value))return 0;
    *index=-1;
    if(flags&2){if(!Take(image,&cursor,1,&value)||value>=64)return 0;*index=(int)value;}
    if((flags&1)&&!Take(image,&cursor,1,&value))return 0;
    return 1;
}
static int Label(const Image *image,const uint8_t *ram,unsigned index,char text[24]) {
    /* Original029DB3 selects the current mutable town-name buffer for name0;
     * original028DF7 initializes it from the owned ROM. A missing buffer can
     * use that original default; unreadable current text refuses metadata. */
    if(index==0&&ram[0x546a]!=0&&ram[0x546a]!=255){
        unsigned n=0;
        for(unsigned i=0;i<24;++i){unsigned value=ram[0x546a+i];
            if(value==255){while(n&&text[n-1]==' ')--n;text[n]=0;return n!=0;}
            if(n>=23||(value!=0x80&&(value<0x81||value>0x9a)))return 0;
            text[n++]=value==0x80?' ':(char)('A'+value-0x81);
        }
        return 0;
    }
    unsigned pointer,value;
    if(index>=23||!Read(image,0x04c200+index*2,2,&pointer)||pointer<0xc280)return 0;
    pointer|=0x040000;
    unsigned n=0;
    for(unsigned i=0;i<24;++i){
        if(!Read(image,pointer+i,1,&value))return 0;
        if(value==0||value==255){while(n&&text[n-1]==' ')--n;text[n]=0;return n!=0;}
        if(n>=23||(value!=0x80&&(value<0x81||value>0x9a)))return 0;
        text[n++]=value==0x80?' ':(char)('A'+value-0x81);
    }
    return 0;
}
typedef struct Group {
    unsigned destination,name,xsum,ysum,count,minx,maxx,miny,maxy;
    unsigned objective;char label[24];
} Group;
/* At most one original exit hop from a named world town. Conditional/nonzero
 * flags are excluded; ambiguity never produces an objective pin. */
static int TownContains(const Image *image,const uint8_t *ram,unsigned scene,unsigned destination) {
    unsigned stream,index,pointer,end=0x090000,dims,value;
    if(!Selected(image,ram,scene,&stream)||!Read(image,stream+5,1,&dims)||
       !Read(image,stream+10,2,&index)||index>=384||!Read(image,0x08aa00+index*2,2,&pointer)||pointer<0xad00)return -1;
    pointer|=0x080000;
    for(unsigned i=0;i<384;++i){
        if(!Read(image,0x08aa00+i*2,2,&value)||value<0xad00)return -1;
        value|=0x080000;if(value>pointer&&value<end)end=value;
    }
    int found=0;
    for(unsigned n=0;n<MaxExits;++n,pointer+=8){
        unsigned first,x,y,flags,dest,entry;
        if(pointer+2>end||!Read(image,pointer,2,&first))return -1;
        if(first==0xffff)return found;
        if(pointer+8>end||!Read(image,pointer,1,&x)||!Read(image,pointer+1,1,&y)||
           !Read(image,pointer+2,1,&flags)||!Read(image,pointer+3,2,&dest)||!Read(image,pointer+5,3,&entry)||
           x>=(dims>>4)*16||y>=(dims&15)*16||(dest&0x3fff)>=337)return -1;
        (void)entry;
        if(!flags&&(dest&0x3fff)==destination)found=1;
    }
    return -1;
}
static int Build(const Image *image,const uint8_t *ram,unsigned scene,unsigned width,unsigned height,
                 int destination,FoundationMapPoint *output,size_t capacity,size_t *count) {
    FoundationMapPoint result[MaxPoints];Group groups[MaxPoints];size_t used=0;
    if(scene>=337||width==0||height==0||width>3840||height>3840||width%256||height%256)return 0;
    if(scene!=0){*count=0;return 1;}
    unsigned stream,dimensions,index,pointer,end=0x090000,first;
    if(!Selected(image,ram,scene,&stream)||!Read(image,stream+5,1,&dimensions)||
       (dimensions>>4)*256!=width||(dimensions&15)*256!=height||
       !Read(image,stream+10,2,&index)||index>=384||!Read(image,0x08aa00+index*2,2,&pointer)||pointer<0xad00)return 0;
    pointer|=0x080000;
    for(unsigned i=0;i<384;++i){unsigned value;
        if(!Read(image,0x08aa00+i*2,2,&value)||value<0xad00)return 0;
        value|=0x080000;if(value>pointer&&value<end)end=value;
    }
    unsigned terminated=0;
    for(unsigned records=0;records<MaxExits;++records,pointer+=8){
        if(pointer+2>end||!Read(image,pointer,2,&first))return 0;
        if(first==0xffff){terminated=1;break;}
        unsigned x,y,flags,dest,entry;
        if(pointer+8>end||!Read(image,pointer,1,&x)||!Read(image,pointer+1,1,&y)||
           !Read(image,pointer+2,1,&flags)||!Read(image,pointer+3,2,&dest)||
           !Read(image,pointer+5,3,&entry)||x*16>=width||y*16>=height)return 0;
        (void)flags;(void)entry;dest&=0x3fff;
        int name;
        if(!NameIndex(image,ram,dest,&name))return 0;
        if(flags)return 0;
        int objective=destination>=0&&(unsigned)destination==dest;
        if((name<0||name>=23)&&!objective)continue;
        size_t group=0;for(;group<used;++group)if(groups[group].destination==dest)break;
        if(group==used){
            if(used>=MaxPoints)return 0;
            Group *g=&groups[used++];memset(g,0,sizeof(*g));g->destination=dest;g->name=(unsigned)name;
            g->minx=g->maxx=x;g->miny=g->maxy=y;g->objective=(unsigned)objective;
            if(name>=0&&name<23){if(!Label(image,ram,(unsigned)name,g->label))return 0;}
            else memcpy(g->label,"CURRENT OBJECTIVE",18);
        }
        Group *g=&groups[group];
        if(g->name!=(unsigned)name||g->count>=4)return 0;
        g->xsum+=x;g->ysum+=y;++g->count;
        if(x<g->minx)g->minx=x;if(x>g->maxx)g->maxx=x;
        if(y<g->miny)g->miny=y;if(y>g->maxy)g->maxy=y;
        if(g->maxx-g->minx>1||g->maxy-g->miny>1)return 0;
    }
    if(!terminated)return 0;
    int objective_group=-1,ambiguous=0;
    if(destination>=0){
        for(size_t i=0;i<used;++i)if(groups[i].objective){if(objective_group>=0)ambiguous=1;objective_group=(int)i;}
        if(objective_group<0){
            for(size_t i=0;i<used;++i)if(groups[i].name<23){
                int contains=TownContains(image,ram,groups[i].destination,(unsigned)destination);
                if(contains>0){if(objective_group>=0)ambiguous=1;objective_group=(int)i;}
            }
        }
    }
    size_t output_count=0;
    for(size_t i=0;i<used;++i){
        if(groups[i].name>=23)continue;
        if(output_count>=MaxPoints)return 0;
        FoundationMapPoint *point=&result[output_count++];memset(point,0,sizeof(*point));
        point->x=(int)(groups[i].xsum*16/groups[i].count+8);
        point->y=(int)(groups[i].ysum*16/groups[i].count+8);
        memcpy(point->label,groups[i].label,24);
    }
    if(objective_group>=0&&!ambiguous){
        if(output_count>=MaxPoints)return 0;
        FoundationMapPoint *point=&result[output_count++];Group *g=&groups[objective_group];memset(point,0,sizeof(*point));
        point->x=(int)(g->xsum*16/g->count+8);point->y=(int)(g->ysum*16/g->count+8);point->objective=1;
        memcpy(point->label,g->label,24);
    }
    if(output_count>capacity)return 0;
    if(output_count)memcpy(output,result,output_count*sizeof(*result));*count=output_count;return 1;
}
int FoundationMapPointsBuild(const uint8_t *rom,size_t rom_size,const uint8_t *ram,size_t ram_size,
    unsigned scene,unsigned width,unsigned height,int verified_destination,FoundationMapPoint *output,size_t capacity,size_t *count) {
    if(!count)return 0;*count=0;
    if(!rom||rom_size!=ImageSize||!ram||ram_size!=RamSize||!output||capacity>MaxPoints||verified_destination>=337||verified_destination<-1)return 0;
    uint8_t hash[32];sha256_compute(rom,rom_size,hash);
    if(memcmp(hash,clean_identity,32))return 0;
    Image image={rom,rom_size};return Build(&image,ram,scene,width,height,verified_destination,output,capacity,count);
}

#ifndef FOUNDATION_MAP_POINTS_STANDALONE
#include "common_rtl.h"
#include "snes/snes.h"
#include "snes/cart.h"
extern Snes *g_snes;
static uint8_t cached_story[0x82];
static uint8_t cached_town_name[24];
static unsigned cached_scene,cached_width,cached_height,cached_party;
static int cached_destination,cached_valid;
static const uint8_t *bound_image;
static size_t bound_size;
static int bound_identity;
void FoundationMapPointsReset(void){cached_valid=0;memset(cached_story,0,sizeof(cached_story));memset(cached_town_name,0,sizeof(cached_town_name));}
void FoundationMapPointsInit(void){bound_image=NULL;bound_size=0;bound_identity=0;FoundationMapPointsReset();}
void FoundationMapPointsAfterFrame(int verified_destination){
    if(verified_destination==0xffff)verified_destination=-1;
    if(!FoundationMapVisible())return;
    unsigned scene,width,height;
    if(!FoundationMapBounds(&scene,&width,&height)){cached_valid=0;return;}
    if(cached_valid&&g_snes&&g_snes->cart&&bound_image==g_rom&&bound_size==g_snes->cart->romImageSize&&
       cached_scene==scene&&cached_width==width&&cached_height==height&&cached_destination==verified_destination&&
       cached_party==g_ram[0x4b6]&&!memcmp(cached_story,g_ram+0x5360,sizeof(cached_story))&&
       !memcmp(cached_town_name,g_ram+0x546a,sizeof(cached_town_name)))return;
    FoundationMapPoint points[MaxPoints];size_t count=0;
    if(g_snes&&g_snes->cart&&g_rom){
        size_t size=g_snes->cart->romImageSize;
        /* Title image storage is immutable. No global field/cache bind here;
         * hash only first use or a changed image pointer/size. Init invalidates
         * identity on title load; checkpoint Reset discards derived points. */
        if(bound_image!=g_rom||bound_size!=size){
            bound_image=g_rom;bound_size=size;bound_identity=0;
            if(size==ImageSize){uint8_t hash[32];sha256_compute(g_rom,size,hash);bound_identity=!memcmp(hash,clean_identity,32);}
        }
        Image image={g_rom,size};
        if(bound_identity&&verified_destination>=-1&&verified_destination<337)
            (void)Build(&image,g_ram,scene,width,height,verified_destination,points,MaxPoints,&count);
    }
    FoundationMapSetPoints(scene,points,count);
    cached_scene=scene;cached_width=width;cached_height=height;cached_destination=verified_destination;
    cached_party=g_ram[0x4b6];memcpy(cached_story,g_ram+0x5360,sizeof(cached_story));memcpy(cached_town_name,g_ram+0x546a,sizeof(cached_town_name));cached_valid=1;
}
#endif
