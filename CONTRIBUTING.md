# Contributing

Focused contributions and small reproducible checks are welcome. Start with
[BUILDING.md](BUILDING.md), [ROADMAP.md](ROADMAP.md) and the latest
[host-buffer release notes](docs/FOUNDATION-HOST-BUFFER-RELEASE-2026-10-09.md).

Use your own clean supported ROM locally. Keep ROMs, generated CPU bodies,
extracted assets/audio, saves, checkpoints, raw memory dumps and private
research caches out of Git, issues and PRs. Do not contribute unlicensed ROM-hack
source. The existing native/Companion manifests identify authored snapshot
files; update the corresponding hashes when deliberately changing those files.

For a change, explain the original trigger, resulting behavior, relevant source
contract and exact checks run. Separate real gameplay from host synthetic
fixtures, compilation from gameplay, virtual input from physical controllers,
and host frame rate from guest update rate. A narrow verified case is useful;
do not describe it as a full-campaign result.

Renderer changes must preserve the original 256-pixel center, original guest
state/timing and original actor activation/collision. Require source/packet
lineage for private margins; refuse unknown states instead of inventing scene
data. Test cache reset, cold restore and rollback. Audible pacing checks must
exclude synchronous forensic dumps; capture parity separately.

Test with fresh profiles or verified copies of saves. Never reset another
developer's intentionally modified runtime or install over their player profile.
The public build helper stops on unexpected runtime modifications.

For bugs, include OS, source commit/build hash, renderer, active enhancement
flags, input device and a short route from a known state. Describe whether the
problem appears in original view too. Share sanitized log excerpts, not ROMs or
raw private dumps. A controller's presence does not prove gameplay input works.

Preserve [license boundaries and notices](THIRD_PARTY_NOTICES.md). Contributions
to the native/tools/docs areas use the repository's PolyForm Noncommercial
terms; Companion contributions use its MIT terms, subject to retained upstream
material. Discuss substantial third-party code or asset imports before adding
them so provenance and compatibility can be established.
