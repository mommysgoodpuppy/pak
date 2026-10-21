# First package-controlled build API — 2026-10-08

Implemented in `/home/ellie/git/wm-mini/tooling/pakman/`. A package includes
`Build(id, tools)` in its pure plan and supplies its own ordinary Workman
`BuildContext -> Task<Void, String>` function to `serveWithBuild`. The callback
chooses its own operations and order. Optional helpers live in `src/build.wm`;
there is no mandatory phase runner or command DSL.

The manager provides locked inputs, scratch space, staged output, an offline
Bubblewrap host environment, code/tool identity in the store hash, and existing
generation installation/rollback. `file://` sources support local scripts and
patches through the same source cache and lock as downloads. Editing a locked
local file requires resolving again. Package constructor signatures are intact;
the program protocol is now 6.

The backend currently uses the read-only host `/usr` and requires an Arch
package database. Direct launches are declared absolute tools; subprocesses can
use the rest of `/usr`. The store identity includes the compiled Workman program,
its literal local JS imports, locked sources, selected ref, declared tool bytes,
Deno/Bubblewrap, host architecture/OS, and pacman's installed database. Manual
changes to undeclared `/usr` files are outside its cache contract. This is not
yet a hermetic tool closure or PS2 build environment. Independent build-package
dependencies and explicit cross toolchains remain follow-up work.

## OSCGoesBrrr first case

`paks/oscgoesbrrr/pak.wm` now supplies a Workman callback that invokes a locked
local Python transform. The transform requires the reviewed upstream 2.1.30
AppImage hash, removes precisely the automatic scan-timer call in its bundled
main module, preserves ASAR entry lengths/offsets, updates ASAR integrity hashes,
rebuilds SquashFS, and preserves the original AppImage runtime prefix. Other
versions fail closed pending review. The earlier TypeScript source patch remains
as the source-level expression of the change.

A real offline `wm pakman build` succeeded using an isolated state and a test
lock derived from the existing installed upstream source hashes plus the local
script hash. It did not resolve or modify the live profile lock. The artifact is:

`/tmp/pakman-osc-build/store/e6a824b5a0778e899ea5f60d1d9ddbd0-oscgoesbrrr-2.1.30/.local/lib/oscgoesbrrr/oscgoesbrrr.AppImage`

Output SHA-256:
`996104b4ced27ef8c67304a2143e32724a3fe9c110cd86abefb6138bb7d9df31`.

`experiments/oscgoesbrrr-no-autoscan/validate-repack.py` verifies the resulting
AppImage by reading its actual ASAR: original runtime prefix, module patch,
ASAR integrity, Node syntax, and the transport-mocked IntifaceSession behavior
check. The patched session retains handshake, initial device list, output command
routing and cleanup; it does not create the automatic scanning timer. The result
is recorded in `repack-result.json`.

At the initial isolated-build check, the installed AppImage still matched the
original upstream hash. No Electron
launch, activation, or Bluetooth hardware verification has been performed.
The live lock initially needed a new resolve to include the script. Launch
compatibility and the hardware outcome remain to be tested.

## Validation

- Workman package-manager suite: 44 passed, including native compile/check/stage,
  partial-build rejection, existing installation and rollback.
- Host tests: 5 passed, covering sandbox denial of child network/host writes/private reads, code
  and tool identity invalidation, local source snapshots, output rejection, and
  recompilation after imported Workman helper changes with restored mtimes.
- TypeScript host boundary checked with `deno check`.
- Built and independently validated the OSCGoesBrrr artifact offline; a second
  build reused the same store entry.

No commits or external publication were made.

## Live installation and same-version resolver repair

Ellie's install attempt exposed a resolver bug: keeping the same version skipped
`make` and reused the entire old source list. Even the suggested `resolve` command
could not incorporate the new script. Resolution now reevaluates the current
plan, preserves matching locked remote inputs, downloads new/changed sources,
refreshes local file inputs, removes obsolete sources, and records matching
published checksums on reused remote pins. Its output distinguishes an unchanged
version with refreshed inputs.

The repaired resolver refreshed the live 2.1.30 lock, and `wm pakman install
oscgoesbrrr` completed successfully: user generation **3**, five files placed.
The installed AppImage SHA-256 now matches the validated patched artifact above.
No process was stopped or launched by this installation; launch compatibility
and Bluetooth behavior remain untested. A running instance must restart to use
the replacement file.

Validation after the resolver repair: **47 Workman tests passed**, including
three regressions for new inputs, edited local files and reused checksum pins.

## Initial live launch check

Ellie launched the installed patch at 22:55:42 EEST. The running mounted ASAR
matches the validated patched module, and the main process remained alive.
Intiface connected without resuming automatic scanning: zero new scan starts
in a 72-second observation, with BlueZ powered and not discovering. No new HCI
timeout or adapter USB reset appeared since launch. Sustained hardware stability
and device output behavior remain to be verified.
