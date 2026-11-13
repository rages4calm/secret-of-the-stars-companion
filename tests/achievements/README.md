# ROM-free achievement checks

These C tests use the actual game-authored adapter/browser and verified SDL3. They contain no ROM, game assets, generated game code or checkpoints.

Compile `adapter_test.c` with the test `include` directory first, then `native/foundation/src`, the CompanionAchievements core and cJSON include paths, and SDL3 headers. Link unchanged `companion_achievements.c`, `cJSON.c` and the matching SDL3 library. Run the executable with two NEW absolute output directories: normal progress, then diagnostic progress. It asserts transition guards, counters, persistence/restore and no diagnostic writes. Do not supply an owner profile.

Compile `ui_test.c` with test `include` first, the verified runtime `runner/src` and `runner/src/desktop`, and SDL3 headers/library. It pushes real SDL keyboard/controller events through the actual event watch and checks opening, browsing, closing, input release masking and speculative-frame handling. It does not replace physical controller/gameplay testing.

The host generation/speculation queries and drawing functions are stubbed only for these ROM-free checks. The runtime core is not simulated, and these tests do not certify campaign progression or all native paths.
