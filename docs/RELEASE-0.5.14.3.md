# Secret of the Stars 0.5.14.3

The proven native CPU path and the 0.5.14.2 pacing fix remain. Experimental
lookup caches did not demonstrate a gameplay performance benefit and are not
included. The owner closed the affected-laptop performance investigation;
no claim that its slowdown or thermal behavior has been fixed is made.

Coherent field mosaic effects now expand using the actual PPU sample row for
each layer. Completely black loading rows no longer invalidate wide scenery.
Original center comparison and unknown visible resource/layout refusal remain;
unsupported actor effects keep their existing guards. Ordinary fade support and
the clearer early journal advice from 0.5.14.2 remain.

Linux and Android build preparation is included as development source, with
Android exact-ROM import and hideable touch controls. Neither platform is a
published, gameplay-qualified binary. See PLATFORMS.md for commands and limits.
The Windows package remains ROM-free authored source and Companion0.3.8.

The affected laptop's overheating is player-reported, not a measured sole cause.
Its prior samples showed dominant CPU game/raster work and very little GPU
presentation time; Vulkan alone is unlikely to resolve that measured cost.
No guarantee of 60FPS on that laptop is made.
