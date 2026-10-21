# zlib native PS2 package

Version 1.3.1-ps2.1, pinned to the existing custom distro source.
The physical PS2 compiled the static library and test programs, passed
upstream `teststatic`, and pakman installed the five development files.
A separate installed-header/library consumer test is pending. The package installs only under
pakman's isolated prefix. Uses one native compiler job, a 16 MiB data limit
and 64 MiB address-space limit. Run with the shared available-memory watchdog.

Installs static development library, headers and relocatable pkg-config data.
The build runs upstream static compression/decompression checks natively.
