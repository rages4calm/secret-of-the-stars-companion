# Companion launcher direction

The owner asked whether this port will use the EarthBound/Zelda launcher.
The accepted direction is to reuse their Companion approach and suitable shared
code, adapted to Secret of the Stars. The current CMD/PowerShell foundation
launchers remain useful fixture entry points; they are not the final launcher.

Read-only focused source inspection:

- EarthBound: `C:/Users/crono/Desktop/Projects/eb/github-repo/Companion/Companion.csproj`
  and the application/main-form initialization in `Program.cs`. WinForms,
  .NET 8, self-contained single-file publishing; sidebar pages, Apply settings
  and play/resume lifecycle. EarthBound-specific randomizer, story conversion,
  game packs and soundtrack manifests are not generic dependencies.
- Zelda: `C:/Users/crono/Desktop/Projects/TheLegendOfZeldaALinkToThePast-SnesrevZelda3Launcher/github-repo/Companion/Companion.csproj`.
  WinForms, .NET 10, with a separate Companion.Core project.
- Local .NET SDKs 8.0.100, 8.0.411, 9.0.305 and 10.0.300 are available.

The game-facing adapter must map to this port's actual config.ini, keybinds.ini
and foundation.ini, support Play/title and explicit Resume separately, preserve
custom bindings and newest owner progress, and launch the qualified artifact.
Keep display, audio, controller and enhancement settings understandable.
Unavailable content/features must not be represented as working toggles.
MSU-1 needs a verified compatible title driver/pack before a music toggle becomes
functional. Existing opt-in HD menu frames and the separate bounded terrain
preview should retain accurate coverage labels.

Next launcher step: inspect reusable settings/launch widgets and the local
licenses, then build a title-specific adapter in this workspace. Do not modify
either reference game's source, installations, saves or progress. Familiar
Companion structure is approved; wholesale EarthBound feature transplantation
and a completed graphical launcher are not claimed by this assessment.
