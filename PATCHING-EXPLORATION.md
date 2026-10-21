# Package-managed patches: OSCGoesBrrr case study

Exploration on 2026-10-08. Nothing here changes the installed package, lock,
generation, or running applications. This is a tested patch proposal, not an
implemented pakman feature.

The subsequent [prior-art review](BUILD-PRIOR-ART.md) grounds the build design
in Ellie's Arch and PS2 recipes. Following Ellie's clarification, it favors
package-controlled build programs with composable APIs. Common phases are
optional helpers, not a manager-enforced lifecycle.

## The concrete problem

The installed OSCGoesBrrr 2.1.30 initiates a Bluetooth discovery cycle through
Intiface every 10–11 seconds, even after devices are connected. Each cycle
starts scanning, waits 10 seconds, then stops scanning. There is no existing
configuration switch for this behavior.

Ellie's ASUS Bluetooth controller repeatedly times out on Inquiry Cancel and
disconnects from USB. The matching firmware patch loaded correctly but did
not resolve the failures. A temporary USB autosuspend test also had a failure.
OSCGoesBrrr scanning is a plausible trigger, **not a proven root cause**.
See the VR hub's [hardware investigation](../vrlinux/HARDWARE.md).

The desired local variant leaves discovery to Intiface Central and keeps
OSCGoesBrrr's connection and output control. The smallest source change removes
the call to `startScanTimer()` from `IntifaceSession.connect()`.

- [Source patch](paks/oscgoesbrrr/patches/no-automatic-scanning.patch)
- [Offline proof](experiments/oscgoesbrrr-no-autoscan/proof.py)
- Upstream source: <https://github.com/OscToys/OscGoesBrrr/blob/v2.1.30/src/main/IntifaceSession.ts>

## What pakman already provides

The package in `paks/oscgoesbrrr/pak.wm` installs the upstream AppImage unchanged
at `.local/lib/oscgoesbrrr/oscgoesbrrr.AppImage`. It is User scope.

In wm-mini's `tooling/pakman/src/`:

| Component | Existing behavior | Relevant extension |
|---|---|---|
| `model.wm` | `Source` is a download URL; install operations copy, extract, write, link and mkdir | Local input files and explicit build transformations |
| `plan.wm` | Versioned JSON protocol between sandboxed recipes and manager | Encode/decode the new inputs and operations; bump protocol |
| `resolve.wm`, `lock.wm` | Download hashes are pinned and cached | Snapshot local patches and transform files into that same cache |
| `store.wm` | Hashes sources and ordered install operations, stages output, freezes it into a new store entry | Hash patch contents and transform semantics; execute before freeze |
| `host.ts`, `io.wm` | Host side performs side effects; extraction uses bsdtar | Bounded patch/archive operations or a separately sandboxed build runner |
| `install.wm`, `apply.wm` | Ownership checks, normal activation, generations and rollback | Reuse without introducing an unmanaged post-install patch hook |

`PAKMAN_PKGS` already supports ordered local recipe directories: first matching
package name wins. This could provide an initial user override without adding a
variant selector yet. It shadows the whole recipe; there is no existing patch
overlay or automatic recipe inheritance.

The current design anticipates source builds when there is a patch to carry,
but has not implemented build support. Existing `make` is a pure description.
That is the current protocol, not a requirement that every future package
entry point be pure: the same custom version-manager program could have an
effectful build/realization entry point under a restricted execution context.

## Proposed first implementation

Keep the first change focused on declared local inputs, a package-controlled
build entry point and composable tools for producing staged output. It does
not need a fixed phase sequence or a separate plugin system.
The following is proposed notation, **not currently valid pakman syntax**:

```wm
-- An explicit local input, resolved by the manager relative to the recipe.
localSource("no-auto-scan.patch", "patches/no-automatic-scanning.patch")

-- The package program uses workspace, patch and command helpers to build.
-- Exact APIs and protocol entry points remain to be decided.
```

Resolution should resolve local paths relative to the selected package
directory, reject paths/symlinks escaping it, hash the bytes and snapshot them
in the source cache. The lock records provenance as local rather than claiming
upstream verification. Build uses the snapshot, not mutable recipe files.
Editing a patch requires resolve; do not silently build newly edited bytes
under an old lock.

The store identity must cover the upstream input hashes, patch/transform
hashes, package/builder code and transitive imports, tool/helper identities,
selected options and platform settings. Otherwise changing program behavior
or fixing a helper could accidentally reuse an old result. Ordered operations
remain sufficient only for the existing declarative install path.
Keep upstream version `2.1.30`; identify the local difference through the
store identity and patch metadata, not an invented upstream release number.

Run transforms unprivileged in a private workspace. A package-controlled
runner needs a separate sandbox with declared tools, read-only inputs, a
writable work/output directory, no network by default, and no access to the
user's app settings or live installation. Named command arguments avoid shell
interpolation but do **not** replace that sandbox. Do not expose a manager's
unrestricted `runCapture` directly as package build permission.

Validate output paths and symlinks before creating a store entry. Build failure
must leave the current generation untouched. A user should be able to inspect
the local patch, resulting plan and build report before activating it.

## Why this binary package needs more than `patch -p1`

The app is JavaScript shipped inside Electron's ASAR, inside SquashFS, inside
an AppImage. The source patch alone cannot change the installed binary.
There are two valid realization routes:

1. Build tagged source with the patch. This follows the existing design's
   source-build direction, but requires a locked dependency/vendor step and
   a controlled Electron build toolchain that pakman does not have yet.
2. Transform the verified upstream AppImage. Unpack its data, locate the
   bundled `IntifaceSession` code, apply an exact guarded modification,
   rebuild ASAR and SquashFS, and retain the AppImage runtime and installed
   path. This is a smaller practical experiment for this one patch.

For route 2, do not edit compressed bytes or overwrite a managed store entry.
Recompute ASAR sizes, offsets and integrity metadata as required; check whether
the shipped Electron runtime enforces embedded ASAR integrity. Preserve
unpacked native modules, executable modes and symlinks. Use deterministic
archive ordering and timestamps, and declare the archive tools as build
inputs. Repacked output no longer has the upstream binary's checksum or
signature: upstream verification applies to its input; the derivative has
its own hash and provenance.

The bundled module's filename changes between builds. Match the module
structurally and require exactly one patch context plus the expected preimage
hash for this version. On a future version mismatch, fail with an actionable
review/rebase message. Never skip a failed patch and activate unpatched output
as if it were the local variant.

Initially, an explicit local override recipe is sufficient. A subsequent
variant/options feature could let users select automatic scanning without
duplicating the package definition. It should still enter the lock and store
identity. Intiface discovery settings and the user's OSC/device configuration
remain runtime settings, outside the package patch.

## Proof and limits

The existing user lock records a verified upstream AppImage input:

```
version: 2.1.30
sha256: 10e87dc675187accd3cda82bd526167e1c2dbfa139a9c592e7d0158568b86196
```

Run the offline proof without installing or launching Electron:

```sh
python experiments/oscgoesbrrr-no-autoscan/proof.py \
  ~/.local/state/pakman/sources/10e87dc675187accd3cda82bd526167e1c2dbfa139a9c592e7d0158568b86196
```

It verifies the pinned binary hash, finds the SquashFS payload, reads the ASAR
main module with `unsquashfs -cat`, and requires exactly one startup call.
The modified module passes Node syntax checking. A test using the actual
bundled session class with a mocked transport confirms:

- Original connect starts both the reporting timer and scan timer.
- Patched connect starts only the reporting timer.
- Handshake and initial device-list requests still occur.
- Initial device-list notification and output-command routing remain intact.
- Disposal clears the remaining timers.

The source patch also applied to the tagged `v2.1.30` source with zero fuzz.
Neither test proves hardware stability, notification behavior for newly added
devices, nor a working rebuilt Electron artifact. An end-to-end proof still
needs ASAR/AppImage reconstruction, an isolated Electron launch, pakman store
realization and activation/rollback tests, then a user Bluetooth trial.

## Acceptance tests for the manager feature

- A changed local patch produces a different store entry after resolve; an
  unchanged lock rebuilds from the same cached patch bytes.
- An input outside the selected recipe directory or a traversal destination
  is refused, including symlink escapes.
- A changed upstream preimage fails before activation rather than using fuzz
  or omitting the patch.
- Sandbox tests demonstrate that transforms cannot modify the user's live
  installation, app settings or existing store entries.
- Repeated builds with the declared tools produce the same artifact bytes.
- Activation installs the derivative under normal ownership checks; rollback
  restores the original generation and original AppImage bytes.
- Existing recipes and upstream checksum verification continue to work.

No pakman core source, recipe, lock or installed app was modified for this
exploration. The new source patch is not yet referenced by `pak.wm`.
