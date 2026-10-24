# Blender 4.3 for avatar authoring

The `blender-4.3` recipe packages Blender's official portable Linux x64 bundle.
It discovers only stable **4.3.x** archives, orders patch versions numerically,
and verifies the archive against the publisher's version-specific `.sha256` file.
The ordinary pakman age gate applies. Updating this package cannot select 4.4
or 5.x.

This series matches Ellie's Windows Blender 4.3 installation and three of the
four Blender source files in Velle2025. The configured Arch repository currently
offers Blender 5.2.2 rather than 4.3 (checked 2026-10-21).

```sh
wm pakman resolve blender-4.3
wm pakman install blender-4.3
blender-4.3 --version
```

Scope is **User**, so installation needs no sudo. The bundle lives at
`~/.local/lib/blender-4.3`. The recipe provides `~/.local/bin/blender-4.3` and
`~/.local/bin/blender`, plus a Blender 4.3 application-menu entry. Unity invokes
`blender` through PATH for `.blend` imports; ensure `~/.local/bin` is on the
environment inherited by the editor. The generic launcher makes this the
default Blender for that PATH. Pakman refuses to overwrite files it does not own.

The portable bundle contains its own Python and libraries. Add-ons and user
preferences belong in Blender's user configuration, separately from the managed
bundle. No Windows preference files or add-ons are installed by this package.

## Validation on 2026-10-21

- Resolved **4.3.2** from `https://download.blender.org/release/Blender4.3/`.
- Verified publisher SHA-256:
  `4da1c956673c0485e63054e563ee69198cc8f80d8157dd7592dffc8a6a5592e6`.
- Built and installed into `/tmp/vrunity-blender43-validation/root` with an
  isolated pakman state: 5,721 files placed. No live installation performed.
- `blender --version` reports 4.3.2; no missing linked libraries on this machine.
- Successfully ran Unity 2022.3.22f1's actual `Unity-BlenderToFBX.py` exporter
  against a transferred Blender 4.3 file, producing a nonempty FBX. Used factory
  preferences and disabled automatic execution of embedded scripts; did not
  resave the source.
- Two parser tests pass, covering architecture/series filtering, numeric patch
  ordering, and exact checksum-file selection.
- GUI use and Windows add-on migration remain untested.
