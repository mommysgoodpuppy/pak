# Build support: prior art from Ellie's packaging systems

Read-only source review on 2026-10-08 of `cachy-packages-main` and
`psx-pi-smbshare/research`, compared with current pakman. Their local work was
preserved. No recipes were run, packages installed, or artifacts published.
These findings describe the checked local files, not a claim that every recipe
currently builds or is fully reproducible.

## Shared model to retain

Both systems already distinguish source/work directories from a staged
installation tree. Build may patch, compile, generate files, or transform a
binary bundle; packaging selects the files that will actually be installed.
Pakman should retain this boundary and feed the staged tree into its own
store/generation machinery, without introducing APK or pacman as intermediates.

| Concern | Local Arch packaging | PS2 research packaging | Implication for pakman |
|---|---|---|---|
| Lifecycle | `prepare()`, `build()`, `package()` through makepkg | Recipe `build()` and `package()` through `pkgbuild.sh` | Useful optional conventions, not a mandatory package-program lifecycle |
| Workspace | makepkg `srcdir`, `pkgdir`; recipes choose private build directories | Explicit `srcdir`, `builddir`, `pkgdir`, `recipedir` | A stable build context with separate source/work/output locations |
| Patches/assets | Local files in `source=()` with checksums | Recipe-relative patches, configs and wrappers | Local inputs are first-class, locked bytes |
| Language dependencies | Fresh fetches its Cargo lock in prepare; vLLM installs a private locked runtime | GCC Rust components use offline Cargo and existing caches | Separate dependency acquisition from offline build |
| Build tools | `makedepends`, compiler flags and recipe environment | Cross-toolchain PATH, triplet, sysroot, build-time generators | Model tools and platform roles explicitly |
| Build prerequisites | Host-provided libraries and tools | Manual dependency order and previous staging roots | Build dependencies need a graph and reusable artifacts |
| Validation | Optional `validateBuiltPackage` before repository registration | Recipe assertions and target tests shipped in the payload | Checks before activation; target execution may be separate |
| Output | Arch package archives; local repository | APK payload, signing and indexing | Pakman keeps its existing store output and generations |

## Concrete examples

### A small patch is already an ordinary build input

[MicroQuickJS](../psx-pi-smbshare/research/packages/mquickjs/recipe.sh)
copies source into its build directory, applies
`0001-default-heap-8mb.patch`, runs make, then stages the executable and tests.
The patch changes a default for this machine; it is intentionally local.
This is the closest precedent for the OSCGoesBrrr scan-policy patch.

The same recipe demonstrates two executable architectures in one build:
`HOST_CC` generators run on the desktop, while `CROSS_PREFIX` produces PS2
code. `MQJS_BUILD_FLAGS=-m32` makes the generators emit target-sized data; it
does not mean the host needs a 32-bit executable toolchain.

### Network dependency acquisition is a distinct responsibility

[Fresh](../cachy-packages-main/packages/fresh-git/PKGBUILD) fetches dependencies
with `cargo fetch --locked` in `prepare()`, sets a private `CARGO_HOME`, then
builds with `CARGO_NET_OFFLINE=true` and `cargo build --frozen`. This is a
useful lifecycle precedent; exact toolchain/input coverage still determines
whether the complete result is reproducible.

[Yabridge](../cachy-packages-main/packages/yabridge-vst2-compat/PKGBUILD)
declares pinned, checksummed C++ dependency archives, assembles Meson
subprojects in `prepare()`, and builds with `--wrap-mode=nodownload`. Its
package combines newly built Wine hosts with an upstream management utility.
A package therefore may mix source-built and prebuilt outputs.

[vLLM](../cachy-packages-main/packages/python-vllm-rocm/PKGBUILD) uses a
reviewed `requirements.lock`, a package-private Python runtime, explicit ROCm
compiler/architecture settings, and wheel compilation. It currently acquires
language dependencies during `build()`, not an isolated vendor phase. For
pakman, preserve the private dependency environment while separating that
acquisition from offline compilation. Do not copy its `python-*` package naming
or host site-packages assumptions into pakman's application-only model.

### Build dependencies are not runtime dependencies

[curl](../psx-pi-smbshare/research/packages/curl/recipe.sh) consumes staged
Mbed TLS and zlib inputs. It emits a development staging tree with headers,
`libcurl.a` and `curl-config` for the later Git build, but its runtime package
contains only the executable.

[git-minimal](../psx-pi-smbshare/research/packages/git-minimal/recipe.sh)
consumes that development tree and other static libraries. The existing
builder does not resolve this automatically: recipes rely on prior build
order and mutable `BUILDROOT/work/...` paths. Pakman should record those
prerequisite artifact identities rather than treating them as incidental
filesystem access. Build artifacts can be retained for dependent builds
without being installed into a runtime generation.

[zsh](../psx-pi-smbshare/research/packages/zsh/recipe.sh) similarly consumes
ncurses's static archive and verifies the expected terminal fallback before
configuring. Its configure checks detect incorrect feature decisions, not
just compiler errors. Checks therefore need to support inspection of build
data, not only running a final program.

### Platform roles cannot be one `target` flag

[GCC Rust](../psx-pi-smbshare/research/packages/gccrs15/recipe.sh) explicitly
distinguishes `--build`, `--host`, `--target`, `CC_FOR_BUILD` and
`CC_FOR_TARGET`. The desktop builds a compiler that runs on the PS2 and
generates PS2 code. Build-time desktop programs must stay executable on the
desktop while Rust/C++ components are compiled for the PS2.

[GDC](../psx-pi-smbshare/research/packages/gdc15/recipe.sh) combines outputs
from two existing build trees because a cross-build cannot run its newly
built PS2 compiler. The compiler and runtime can therefore be separate build
nodes assembled into one runtime package. Its current absolute paths are
useful evidence of the requirement, not paths to bake into pakman's API.

### Building and validation must respect the actual machine

[Low-memory build notes](../psx-pi-smbshare/research/LOW-MEMORY-BUILDS.md)
describe native builds exhausting the PS2's available memory. A universal
`-j$(nproc)` or desktop sandbox/runtime requirement would undermine pakman's
eventual native PS2 goal. Build context should provide a chosen job budget;
platform-specific execution/isolation backends should implement the contract.

Cross-built tests can be included in the package, as MicroQuickJS does, and
run on target later. A host check must not silently run target binaries or
pretend that skipping them verifies runtime behavior.

## Useful limitations exposed by the current builders

The PS2 source cache is keyed by URL basename and the general builder does not
verify a declared source checksum. Recipes and previous staging trees can
change without an automatically different artifact identity. Pakman already
has content-addressed sources; extend that to patches, scripts and prerequisite
artifacts rather than importing these weaknesses.

`mkapk.py` sorts entries and normalizes archive ownership, timestamps and gzip
headers, but its control metadata includes `builddate = int(time.time())`.
Thus normalized payloads do not establish byte-identical complete APKs. For
pakman, distinguish a hash of declared build inputs, a hash of produced content,
and demonstrated reproducibility. They are different properties.

The Arch helper delegates builds to `makepkg -Csf`, then calls an optional
package-specific `validateBuiltPackage` before repository registration.
It cleans `src/` and `pkg/` unless `--keep-build` is supplied. Pakman can retain
that useful validation/debugging boundary while using its own activation and
ownership checks. This source inspection did not execute those commands.

## Revised direction for pakman

Ellie's architectural clarification: each package is a **custom version-manager
program**, not a passive recipe in a manager-owned lifecycle. The prior-art
phases describe useful workflows to make easy; they should not become a
mandatory sequence that limits what package programs can express.

Prefer a **package-controlled build program with composable tools/APIs**.
The program chooses whether to use upstream binaries, compile source, patch
either form, combine artifacts, run checks, or delegate to another build tool.
Loops, conditions, helper functions and custom ordering remain ordinary
Workman program logic. AppImage/ASAR handling belongs in a reusable helper or
package-specific program, not a compulsory pakman pipeline.

Useful API capabilities, not a proposed fixed syntax:

- Obtain a locked input or snapshot a declared recipe-local file.
- Make a workspace; unpack/copy inputs and apply an exact checked patch.
- Obtain build tools and prerequisite artifacts, with platform roles.
- Run a tool with arguments, environment and working directory; inspect its
  output or exit status and decide the next action.
- Stage files and validate the result, with optional common helpers for
  configure/make, Cargo, archive repacking and prepare/build/check conventions.

A locked input can be obtained when the program needs it. The manager's
contract is that its bytes match the lock and its access is permitted, not that
all fetches must occur in a mandatory named phase. A separate vendor helper can
snapshot language dependencies for offline builds without being compulsory
for packages that do not need it.

Pakman owns the execution boundary: permissions, input snapshots, build
identity, validated store output, and generation activation/rollback. The
package owns how that output is produced. This does not mean granting a build
program the manager's unrestricted filesystem/network access. Child commands
must obey the execution contract too; argv-only invocation is not a sandbox.

Current `make` is a pure plan producer. That existing protocol can remain
compatible while a separate effectful realization/build command is added to
the same package program. Whether realization is reached through a command,
callback or declared builder entry point is still open; purity of every future
package entry point is not an architectural requirement. Package tools should
also be usable with an appropriate execution context when the custom version
manager is run directly, preserving its standalone value.

The cache identity needs the executed package/builder code and its transitive
imports, helper implementation identities, locked inputs, tools, platform
settings and selected options. Hashing only a list of manager-owned operations
would miss behavior implemented in the package program. Record the actual
execution and output as a build receipt without claiming that arbitrary code
is automatically reproducible.

Existing declarative binary recipes should remain short and keep working.
Shell/Python/other builder scripts can be declared inputs when useful; they
are an interoperability option, not a requirement to move build logic out of
Workman. Optional phase combinators must not be the only supported workflow.

The build graph is separate from the runtime graph. A desktop tool used to
build a PS2 package must not become a runtime PS2 dependency. Likewise, static
development artifacts should not be installed merely because a build uses
them. The current same-scope runtime dependency restriction does not solve
cross-platform build dependencies.

For tools supplied by the host, decide explicitly how identities are recorded:
`Base("/usr/bin/gcc")` proves existence, not which compiler produced an output.
Locked pakman tool artifacts give stronger cache identities; an initial host-
tool mode can record a build-environment receipt and state its weaker guarantees.

## Small implementation sequence

Start with hashed local inputs, an isolated host execution context, composable
build helpers and staged output, using OSCGoesBrrr as the binary-transform test.
Keep its orchestration in the custom package program. Then use MicroQuickJS
as the patch + desktop-generator + cross-compiler test. Use curl/Git as the
prerequisite development-artifact test before designing the complete compiler
bootstrap graph. Existing lightweight binary packages are regression cases.

Do not need variants, APK signing, publishing, a remote executor or the entire
PS2 toolchain bootstrap in the first increment. Avoid API choices that make
those existing real recipes impossible later.
