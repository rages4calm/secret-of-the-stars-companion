package org.secretstars.companion;

import android.app.Activity;
import android.os.Bundle;
import android.content.Intent;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.File;
import java.io.ByteArrayOutputStream;
import java.io.FileOutputStream;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.security.MessageDigest;

/** Local ROM picker. The game is not bundled and nothing is uploaded. */
public final class SetupActivity extends Activity {
    private TextView status;
    @Override public void onCreate(Bundle state){
        super.onCreate(state);LinearLayout page=new LinearLayout(this);page.setOrientation(1);
        status=new TextView(this);status.setText("Secret of the Stars - Android preview. Choose your own clean USA ROM.");page.addView(status);
        Button select=new Button(this);select.setText("Choose ROM");select.setOnClickListener(v->{Intent pick=new Intent(Intent.ACTION_OPEN_DOCUMENT);pick.setType("*/*");pick.addCategory(Intent.CATEGORY_OPENABLE);startActivityForResult(pick,1);});page.addView(select);
        Button play=new Button(this);play.setText("Play imported ROM");play.setOnClickListener(v->play());page.addView(play);setContentView(page);
    }
    private File directory(){File dir=getExternalFilesDir(null);if(dir==null)throw new IllegalStateException("App storage unavailable");return dir;}
    private void writeDefault(String name,String value)throws Exception{File p=new File(directory(),name);if(!p.exists())Files.write(p.toPath(),value.getBytes(StandardCharsets.UTF_8));}
    private void play(){try{
        File rom=new File(directory(),"game.sfc");if(!rom.isFile())throw new IllegalStateException("Choose a ROM first");
        writeDefault("config.ini","[Graphics]\nRenderer=opengles2\nFullscreen=0\nVSync=1\nNewRenderer=1\nWidescreen=0\n[Sound]\nEnableAudio=1\nAudioFreq=32040\n[General]\nAutosave=0\nSkipLauncher=1\n");
        writeDefault("foundation.ini","EnhancedPixels=1\nExperimentalFieldWide=1\nExperimentalFieldActors=1\nJournal=1\nNavigationMap=1\nMovementSpeedPercent=200\n");
        startActivity(new Intent(this,GameActivity.class).putExtra("rom",rom.getAbsolutePath()));
    }catch(Exception e){status.setText(e.getMessage());}}
    @Override protected void onActivityResult(int request,int result,Intent data){super.onActivityResult(request,result,data);if(request!=1||result!=RESULT_OK||data==null)return;
        try(InputStream in=getContentResolver().openInputStream(data.getData())){
            ByteArrayOutputStream bytes=new ByteArrayOutputStream();byte[] chunk=new byte[16384];int count;while((count=in.read(chunk))!=-1){if(bytes.size()+count>1572864)throw new IllegalArgumentException("ROM too large");bytes.write(chunk,0,count);}byte[] rom=bytes.toByteArray();if(rom.length!=1572864)throw new IllegalArgumentException("Requires clean unheadered USA ROM (1572864 bytes)");
            byte[] hash=MessageDigest.getInstance("SHA-256").digest(rom);StringBuilder hex=new StringBuilder();for(byte b:hash)hex.append(String.format("%02x",b&255));
            if(!hex.toString().equals("7da4a3cfa5de4bb4722a6e2a42c26aae322b5e668f1645d8c870fb99e6080600"))throw new IllegalArgumentException("Unsupported ROM identity");
            try(FileOutputStream out=new FileOutputStream(new File(directory(),"game.sfc"))){out.write(rom);}status.setText("ROM imported locally. Controls button hides/shows touch controls; gamepads use native SDL input.");
        }catch(Exception e){status.setText(e.getMessage());}
    }
}
