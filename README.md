# pak

wm lang docs /home/ellie/git/wm-mini/docs/

Local patching exploration: [OSCGoesBrrr case study](PATCHING-EXPLORATION.md),
with an offline scan-loop proof and a source patch. This is not yet a pakman
feature or an installed package change.
The [build prior-art review](BUILD-PRIOR-ART.md) compares the existing Arch and
PS2 packaging flows and derives requirements for pakman build support.

Packages for pakman (`wm pakman`, in [wm-mini](../wm-mini/tooling/pakman)). Each package is a folder under `paks/` holding `pak.wm`, a
standalone Workman program that is the version manager for one piece of software:

```sh
wm run paks/zig/pak.wm -- versions        # what upstream offers
wm run paks/zig/pak.wm -- make 0.14.1 \
  "https://ziglang.org/download/0.14.1/zig-x86_64-linux-0.14.1.tar.xz"
```

pakman runs these in a sandbox and does everything else: policy, locks, verified downloads, the
store, generations and rollback. See `../wm-mini/tooling/pakman/DESIGN.md`.

Packages install where the software expects to live. `System` packages are rooted at `/` (pakman
uses sudo for the final copy), `User` packages at your home directory (no root).

| package | scope | upstream | notes |
|---|---|---|---|
| `aimp` | system | aimp.ru native Linux beta | upstream's Arch payload as is; version from a redirect |
| `gale` | system | GitHub releases, `.deb` | the `.deb` payload as is; checksums from GitHub digests |
| `t3-code` | user | GitHub nightly prereleases, AppImage | checksums from GitHub digests |
| `zig` | user | ziglang.org index | stable and dev channels; exact tarball URL and checksum from the index |
| `wayvr` | system | GitHub releases, binaries | desktop file and icons from the repo at the tag |
| `vesktop` | system | GitHub releases, `.deb` | the `.deb` payload plus its `/usr/bin` link |
| `xrizer` | system | GitHub releases, zip | `/opt/xrizer` like the AUR package |
| `xr-hardware` | system | freedesktop GitLab tags | the committed udev rules file |
| `android-build-tools` | system | Google SDK repository | archive name travels as the ref; no sha256 upstream |
| `appimagelauncher` | system | GitHub releases, `.deb` | `.deb` name travels as the ref |
| `envision` | user | GitLab CI AppImages from main | CI job id travels as the ref |
| `oscgoesbrrr` | user | GitHub releases, AppImage | logo and license from the repo at the tag |
| `intiface-central` | system | GitHub releases, zip | `/opt/intiface-central`; tag (`v3.2.2+46`) travels as the ref; zip layout varies per release |
| `alcom` | system | vrc-get GUI releases, `.deb` | native VPM client; selects `gui-v` stable releases, verifies GitHub digests |
| `unityhub` | system | Unity's official Debian repository | index SHA-256, artifact age gate; Hub manages the editor separately |
| `fresh-editor` | system | GitHub releases, GNU/Linux x86_64 tarball | `/usr/bin/fresh`, desktop entry and icons; managed receipt disables self-updates |

The first build API is implemented; see [BUILD-IMPLEMENTATION.md](BUILD-IMPLEMENTATION.md)
for the package-controlled callback, backend limits, and validated OSCGoesBrrr artifact.

## Native PS2 recipes

[Kilo](paks/kilo/README.md) is the first upstream-source recipe for the separate
[SubsetML pakman profile](../wm-mini/tooling/pakman-subsetml/README.md). Its WM
package program downloads a pinned commit, checks both source/license hashes
and invokes native GCC on the PS2. The PS2 catalog uses the same
`~/git/pak/paks/kilo/pak.wm` layout. This recipe targets the native profile;
the WM/JS package interface above remains separate.


[GNU Emacs 20.7](paks/emacs/README.md) adds the first larger native source
package, using the PS2/musl target profile and checked directory-tree payloads.
Its native build/installation is being validated; see the recipe README for
current status and the explicit ncurses development prerequisite.

Native PS2 experiments also have recipes for [GNU Make](paks/make/README.md)
and [zlib development files](paks/zlib/README.md). Their validation status is
recorded in each recipe README. Cross-built/binary providers are planned in
`wm-mini/tooling/pakman-subsetml/BUILD-PROVIDERS.md`; the current manager
executes local build operations.
