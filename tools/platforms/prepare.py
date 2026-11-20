"""Configure a platform build using an existing verified private source build.
No generation, ROM loading, cleanup, installation or publication.
Configuration may let CMake fetch its pinned build dependencies.
"""
from pathlib import Path
import argparse, hashlib, json, platform, subprocess, re
from pathlib import PureWindowsPath

HERE = Path(__file__).resolve().parent

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-build',type=Path,required=True,help='Private output from public foundation helper, including first compilation receipt')
    p.add_argument('--runtime',type=Path,required=True,help='Matching pinned patched runtime, with submodules')
    p.add_argument('--platform',choices=['linux','android'],required=True)
    p.add_argument('--output',type=Path,required=True,help='Fresh private platform output; existing paths refused')
    p.add_argument('--sdl-source',type=Path,help='Matching SDL3 source including android-project Java')
    p.add_argument('--cmake',default='cmake')
    p.add_argument('--configure',action='store_true',help='Linux: execute configuration; Android: write Gradle project, build separately')
    args=p.parse_args();base=args.source_build.resolve();runtime=args.runtime.resolve();out=args.output.absolute()
    receipt=base/'source-build-receipt.json';r=json.loads(receipt.read_bytes());project=base/'project'
    if r.get('status')!='compiled_unqualified' or not r.get('public_build'):p.error('Supply an actual public-helper compilation receipt; qualification stays separate')
    for name,digest in r['authored_inputs'].items():
        if name!='recomp/funcs.h' and sha(project/name)!=digest:p.error('Authored input changed: '+name)
    cache=json.loads((project/'src/gen/.snesrecomp-cache.json').read_bytes())
    for name,digest in cache['outputs'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(project/'src/gen'/name)!=digest:p.error('Generated input changed: '+name)
    arch=base/'arch_native'/PureWindowsPath(r['architectural_native_generation']['output']).name
    if sha(arch)!=r['architectural_native_generation']['output_sha256']:p.error('Architectural native C differs')
    provenance=r['runtime_source_provenance']
    for name,digest in provenance['patched_sources'].items():
        if sha(runtime/name)!=digest:p.error('Patched runtime input differs: '+name)
    actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=runtime,text=True).strip()
    if actual!=r['runtime_pin']:p.error('Runtime revision differs')
    if out.exists():p.error('Output already exists; preserve it and choose a fresh path')
    if args.platform=='linux' and args.configure and platform.system()!='Linux':p.error('Run Linux configuration on Linux; Windows is not a Linux compiler')
    if args.platform=='android':
        if not args.sdl_source:p.error('Android requires --sdl-source (matching SDL3 donor sources)')
        sdl=args.sdl_source.resolve();java=sdl/'android-project/app/src/main/java'
        if not (java/'org/libsdl/app/SDLActivity.java').is_file():p.error('SDL3 Java source missing')
        version=(sdl/'include/SDL3/SDL_version.h').read_text()
        if tuple(int(re.search(r'#define SDL_'+key+r'_VERSION\s+(\d+)',version).group(1))for key in ('MAJOR','MINOR','MICRO'))!=(3,4,10):p.error('Expected pinned SDL3 3.4.10 sources')
        if not (project/'platforms/application.cmake').is_file():p.error('Prepared source predates Android shared target adapter; use next public-helper source build')
    out.mkdir(parents=True)
    definitions=['-DCMAKE_BUILD_TYPE=Release','-DSNESRECOMP_ROOT='+str(runtime),'-DSOTS_ARCH_NATIVE_SOURCE='+str(arch),'-DSNESRECOMP_FRAME_IMPL=HLE','-DSNESRECOMP_EXECUTION_DEFAULT=off']
    command=[args.cmake,'-S',str(project),'-B',str(out/'build'),'-G','Ninja',*definitions]
    if args.platform=='android':
        (out/'settings.gradle').write_text("pluginManagement { repositories { google(); mavenCentral(); gradlePluginPortal() } }\ndependencyResolutionManagement { repositories { google(); mavenCentral() } }\nrootProject.name='SecretStarsAndroid'\ninclude ':app'\n")
        (out/'build.gradle').write_text("plugins { id 'com.android.application' version '8.10.1' apply false }\n")
        app=out/'app';(app/'src/main').mkdir(parents=True)
        # JSON literals also quote portable forward-slash paths for Groovy.
        literal=lambda x:json.dumps(str(x).replace('\\','/'))
        arguments=', '.join(literal(x) for x in definitions[1:]+['-DANDROID_STL=c++_static','-DSNESRECOMP_SDL3_SOURCE_DIR='+str(sdl),'-DSDL_SHARED=ON','-DSDL_STATIC=OFF'])
        (app/'build.gradle').write_text("plugins { id 'com.android.application' }\nandroid {\nnamespace 'org.secretstars.companion'\ncompileSdk 36\nndkVersion '28.2.13676358'\ndefaultConfig { applicationId 'org.secretstars.companion'; minSdk 26; targetSdk 36; versionCode 1; versionName '0.1-preview'; ndk { abiFilters 'arm64-v8a' }; externalNativeBuild { cmake { arguments "+arguments+"; targets 'SecretOfTheStarsSNESRecomp' } } }\nsourceSets { main { java.srcDirs = ["+literal(HERE/'android/java')+", "+literal(java)+"] } }\nexternalNativeBuild { cmake { path "+literal(project/'CMakeLists.txt')+" } }\n}\n")
        (app/'src/main/AndroidManifest.xml').write_text('<manifest xmlns:android="http://schemas.android.com/apk/res/android"><uses-feature android:glEsVersion="0x00020000"/><uses-feature android:name="android.hardware.touchscreen" android:required="false"/><application android:label="Secret of the Stars Preview" android:allowBackup="false"><activity android:name=".GameActivity" android:screenOrientation="sensorLandscape" android:configChanges="keyboard|keyboardHidden|orientation|screenSize|smallestScreenSize|uiMode" android:exported="false"/><activity android:name=".SetupActivity" android:exported="true"><intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter></activity></application></manifest>')
        command=['gradle','--project-dir',str(out),'assembleDebug']
    plan={'platform':args.platform,'source_receipt_sha256':sha(receipt),'native_generated_sha256':sha(arch),'command':command,'compiled':False,'playable_qualified':False,'scope':'Private native source reuse, not a released platform build. No game data uploaded or bundled by this tool.'}
    (out/'platform-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
    if args.configure and args.platform=='linux':subprocess.run(command,check=True)
    print(json.dumps(plan,indent=2))

if __name__=='__main__':main()
