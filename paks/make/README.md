# make native PS2 package

Version 4.4.1-ps2.1, pinned to the existing custom distro source.
Build and installed validation are pending. The package installs only under
pakman's isolated prefix. Uses one native compiler job, a 16 MiB data limit
and 64 MiB address-space limit. Run with the shared available-memory watchdog.

The default configure cache contains feature answers from the matching
R5900/musl cross build, not a complete native configure-probe run. Set
`PAKMAN_MAKE_CONFIG_CACHE=none` to probe everything natively.
