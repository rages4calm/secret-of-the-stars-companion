"""Create the shared Gradle frontend for a private build or the setup shell."""
import json
import re
from pathlib import Path
from shutil import copyfile

ANDROID = Path(__file__).resolve().parent / 'android'


def android_sdl_sources(sdl):
    java = sdl / 'android-project/app/src/main/java'
    if not (java / 'org/libsdl/app/SDLActivity.java').is_file():
        raise ValueError('SDL3 Java source missing')
    version = (sdl / 'include/SDL3/SDL_version.h').read_text(encoding='utf-8')
    parts = re.findall(r'^\s*#define SDL_(?:MAJOR|MINOR|MICRO)_VERSION\s+(\d+)', version, re.M)
    if parts != ['3', '4', '10']:
        raise ValueError('Expected pinned SDL3 3.4.10 sources')
    return java


def write_android_project(out, sdl, cmake_project, arguments, target, *, local_module=False,
                          phone_capsule=None, native_tools=None, capsule_sha256=''):
    sdl_java = android_sdl_sources(sdl)
    quote = lambda value: json.dumps(str(value).replace('\\', '/'))
    app = out / 'app'
    main = app / 'src/main'
    main.mkdir(parents=True)
    (out / 'settings.gradle').write_text('''pluginManagement {
    repositories { google(); mavenCentral(); gradlePluginPortal() }
    resolutionStrategy {
        eachPlugin {
            if (requested.id.id == 'com.android.application') {
                useModule("com.android.tools.build:gradle:${requested.version}")
            }
        }
    }
}
dependencyResolutionManagement { repositories { google(); mavenCentral() } }
rootProject.name = 'SecretStarsAndroid'
include ':app'
''', encoding='utf-8')
    (out / 'build.gradle').write_text("plugins { id 'com.android.application' version '8.10.1' apply false }\n", encoding='utf-8')
    has_phone_tools = phone_capsule is not None
    if has_phone_tools and (not local_module or native_tools is None or len(capsule_sha256) != 64):
        raise ValueError('Incomplete Android phone toolchain')
    package_suffix = '.preview' if has_phone_tools else ('.setupdev' if local_module else '')
    local_flag = 'true' if local_module else 'false'
    toolchain_flag = 'true' if has_phone_tools else 'false'
    version_code = 2 if has_phone_tools else 1
    version_name = '0.1-preview.2' if has_phone_tools else '0.1-preview'
    argument_list = ', '.join(quote(value) for value in arguments)
    (app / 'build.gradle').write_text(f'''plugins {{ id 'com.android.application' }}

android {{
    namespace 'org.secretstars.companion'
    compileSdk 36
    ndkVersion '28.2.13676358'
    buildFeatures {{ buildConfig = true }}
    defaultConfig {{
        applicationId 'org.secretstars.companion{package_suffix}'
        minSdk 26
        targetSdk 36
        versionCode {version_code}
        versionName '{version_name}'
        buildConfigField 'boolean', 'LOAD_LOCAL_MODULE', '{local_flag}'
        buildConfigField 'boolean', 'HAS_PHONE_TOOLCHAIN', '{toolchain_flag}'
        buildConfigField 'String', 'SETUP_CAPSULE_SHA256', '\"{capsule_sha256}\"'
        ndk {{ abiFilters 'arm64-v8a' }}
        externalNativeBuild {{ cmake {{ arguments {argument_list}; targets '{target}' }} }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }}
    sourceSets {{ main {{ java.srcDirs = [{quote(ANDROID / 'java')}, {quote(sdl_java)}] }} }}
    packaging {{
        jniLibs {{
            useLegacyPackaging = true
            keepDebugSymbols += ['**/libzig.so', '**/libanalyzer.so', '**/libpython-launcher.so',
                                 '**/libpython3.14.so', '**/libcrypto_python.so',
                                 '**/libssl_python.so', '**/libsqlite3.so']
        }}
    }}
    externalNativeBuild {{ cmake {{ path {quote(cmake_project)} }} }}
}}
''', encoding='utf-8')
    label = 'Secret of the Stars Setup Lab' if local_module and not has_phone_tools else 'Secret of the Stars Preview'
    (main / 'AndroidManifest.xml').write_text(f'''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-feature android:glEsVersion="0x00020000"/>
    <uses-feature android:name="android.hardware.touchscreen" android:required="false"/>
    <application android:label="{label}" android:allowBackup="false">
        <activity android:name="org.secretstars.companion.GameActivity" android:screenOrientation="sensorLandscape"
            android:configChanges="keyboard|keyboardHidden|orientation|screenSize|smallestScreenSize|uiMode" android:exported="false"/>
        <activity android:name="org.secretstars.companion.SetupActivity" android:exported="true">
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
    </application>
</manifest>
''', encoding='utf-8')
    notices = main / 'assets/licenses'
    notices.mkdir(parents=True)
    copyfile(sdl / 'LICENSE.txt', notices / 'SDL3.txt')
    if has_phone_tools:
        from shutil import copytree
        copyfile(phone_capsule, main / 'assets/ondevice.zip')
        copytree(native_tools, main / 'jniLibs/arm64-v8a')
