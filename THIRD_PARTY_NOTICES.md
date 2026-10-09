# Licensing and third-party notices

This is a **mixed-license source-available project**, not a uniformly MIT-licensed
repository.

| Scope | License / notices |
| --- | --- |
| Authored native foundation, runtime patch, project tools and documentation | [PolyForm Noncommercial 1.0.0](LICENSE); Copyright (c) 2026 Carl Prewitt Jr.; retained scaffold/runtime Copyright (c) 2026 Matthew Stanley |
| Companion source | MIT, Carl Prewitt Jr.; [original reuse notice](Companion/THIRD-PARTY-NOTICES.md) and [directory license](Companion/LICENSE) |
| Runtime's original source | [Verbatim upstream PolyForm license](licenses/SNESRECOMP-POLYFORM-NONCOMMERCIAL-1.0.0.txt), Matthew Stanley |
| Runtime's identified upstream material | [Verbatim retained attribution and license texts](licenses/SNESRECOMP-THIRD-PARTY-ATTRIBUTION.md); original MIT/ISC/other terms continue to apply to their identified scope |
| Color lookup lineage | [Original scope description](licenses/color-lut/README.md), plus the verbatim MIT, Apache 2.0 and PolyForm notices in that directory |
| .NET / Windows Desktop | [DOTNET-LICENSE.txt](licenses/DOTNET-LICENSE.txt), [WINDOWS-DESKTOP-LICENSE.txt](licenses/WINDOWS-DESKTOP-LICENSE.txt), [DOTNET-THIRD-PARTY-NOTICES.txt](licenses/DOTNET-THIRD-PARTY-NOTICES.txt) |
| SDL3, fetched at build time | zlib license, Sam Lantinga and contributors; [pinned upstream license](https://github.com/libsdl-org/SDL/blob/release-3.4.10/LICENSE.txt) |

Runtime source is fetched separately by the developer helper. The patch keeps
the runtime's license/provenance; it does not relicense third-party upstream
material. Future binary packages must carry the licenses of the dependencies
they actually bundle, including SDL and self-contained .NET notices.

The preserved upstream attribution may contain historical review notes and
relative paths referring to the upstream tree. It is retained verbatim; the
project credit summary does not replace that legal record.

No original game content, generated CPU bodies, patched image or cached
unlicensed ROM-hack source is distributed. Original game rights are separate
from these source licenses. See [CREDITS.md](CREDITS.md) for named contributors,
algorithms and research references.
