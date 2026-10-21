# Fresh editor

Port of `cachy-packages-main/packages/fresh-editor-bin`, using the official
`sinelaw/fresh` GNU/Linux x86_64 tarball. Stable `vX.Y.Z` releases with that
asset are discovered automatically; pakman applies its three-day age gate and
verifies GitHub's published asset digest.

Installs the binary at `/usr/share/fresh-editor/fresh` with `/usr/bin/fresh`
pointing to it, plus upstream's desktop entry, all icon sizes, documentation,
and license. A package-managed `install-receipt.toml` replaces the tarball's
self-updating receipt: `managed = true`, `self_update = false`. Updates belong
to pakman. Runtime requirements are the binary's libc, libm, and libgcc files;
`xz` is an extraction tool, not a runtime dependency.

The license metadata is GPL-3.0-or-later, matching the change in upstream 0.5.2.
Older releases ship their own earlier license in the archive.

Validated on 2026-10-13 with isolated pakman state and a temporary root:

- Automatic resolution selected **0.5.2** and held **0.5.3** behind the age gate.
- Download SHA-256 matched GitHub and the original PKGBUILD:
  `d7c6600cdd5c813bcd118d84fbcc0559fe9396756a46fd0b7b0c1bf6c5cf8fd6`.
- Build and temporary installation succeeded (16 package files, nine icons).
- Installed `fresh --version` returned `fresh 0.5.2`; no linked libraries were
  missing. The symlink and managed receipt were checked.
- Desktop validation passed, with only upstream's multiple-main-category hint.
- The 0.5.3 archive has the same layout and its SHA-256 also matched GitHub.

Interactive editing and LSP behavior have not been tested. No live system
installation or removal of the existing Arch package was performed.

```sh
wm pakman versions fresh-editor
wm pakman resolve fresh-editor
wm pakman build fresh-editor
wm pakman install fresh-editor
```

For a system migration, remove the existing pacman-owned `fresh-editor-bin`
or `fresh-git` package first; pakman refuses to overwrite its files. Review
that removal separately before running the install command.

To skip the age gate for one install, use:

```sh
wm pakman install --force fresh-editor@latest
```

This follows the default channel afterward. A subsequent ordinary install or
update may downgrade to the newest age-eligible release. To freeze a version,
explicitly use `wm pakman install --pin fresh-editor@0.5.3`. The flags preserve
checksum and ownership checks; remove the old Arch package before a live
migration as above.
