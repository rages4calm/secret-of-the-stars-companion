#pragma once

/* Diagnostic-only observer of the clean-USA VRAM-clear/direct-column loops. No guest writes,
 * redirects, cycle charges, input, or scheduling changes. Disabled unless the
 * private CSV path SNESRECOMP_FOUNDATION_LOADING_TRACE (clear) or
 * SNESRECOMP_FOUNDATION_COLUMNS_TRACE (columns) is explicitly supplied. */
void FoundationLoadingInit(void);
void FoundationLoadingBeforeFrame(void);
void FoundationLoadingReset(void);
void FoundationLoadingShutdown(void);
