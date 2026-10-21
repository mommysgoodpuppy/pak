# Kilo on PS2

This recipe uses the native SubsetML pakman profile, rather than the desktop
WM/JS profile. Its layout is still `pak/paks/kilo/pak.wm`.

Upstream: <https://github.com/antirez/kilo>, BSD-2-Clause.
Pinned commit: `323d93b29bd89a2cb446de90c4ed4fea1764176e`.
Package version: `0.0.1-323d93b29bd8`.

Pakman invokes the separately compiled WM package program, downloads `kilo.c`
and `LICENSE` from that immutable commit over HTTPS, verifies both against
`SHA256SUMS`, and builds with the PS2's `/usr/bin/gcc`. It installs the native
binary and upstream license into the selected isolated prefix. A different
requested version is rejected because the plan reports this pinned version.

The native prototype permits these trusted build commands; it does not yet
provide a process sandbox or the desktop profile's download policy. The
checksums here are explicit recipe pins, not a signature from upstream.

On the prepared PS2 workspace:

```sh
cd /home/ellie/git/pak
. ./env.sh
pakman install kilo 0.0.1-323d93b29bd8
kilo /path/to/file
```

Kilo uses Ctrl-S to save, Ctrl-Q to quit, and Ctrl-F to search. It needs a
terminal; it is not a batch filter. This first build uses `-O0` to reduce the
native compiler's memory requirements.

On 2026-10-17 this recipe fetched, verified, built and installed Kilo on the
physical PS2. Its 32,208-byte MIPS executable was opened in an SSH terminal;
editing, saving and quitting passed, and the saved file was checked exactly.
An injected bad source checksum was rejected before installation, without
leaving a root lock or ownership record.
The working catalog/prefix commands are documented in
`wm-mini/tooling/pakman-subsetml/NATIVE-WORKSPACE.md`.
