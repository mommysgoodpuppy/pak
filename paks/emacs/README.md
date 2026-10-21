# GNU Emacs on the native PS2 pakman profile

`pak.wm` describes GNU Emacs **20.7-ps2.1**, built from GNU's original
20.7 release archive with native GCC and serial Make on PS2 Linux/musl.
This is a terminal-only port, including Emacs Lisp, standard Lisp libraries,
data and Info manuals. The older `/home/ellie/git/emacs` tree is untouched.

The full native build is deferred at the user's request. R5900 emulation can
load the complete Lisp startup and evaluate arithmetic. The physical PS2
build completed the helper stage and three core objects before cancellation
during `xdisp.c`; no Emacs package was installed. Source, completed objects
and diagnostics remain in
`~/git/pak/.state/store/pakman-tmpnam_oPIGaf-0/work/emacs-20.7`.
A new `pakman install` currently starts a fresh store entry; automatic resume
is not implemented. Do not treat this as a successfully installed package.

## Inputs and prerequisites

GNU's archive URL is https://ftp.gnu.org/old-gnu/emacs/emacs-20.7.tar.gz .
`SHA256SUMS` pins the exact archive; it was downloaded independently and
compared with the archive already on the console. The recipe downloads it
itself, or accepts `PAKMAN_EMACS_SOURCE=/absolute/path/emacs-20.7.tar.gz`
for an offline copy, checked against the same hash.

`ps2-musl.cache` is an explicit target feature profile derived from compile/
link tests against the matching R5900 GCC 15.2.0/musl/ncurses toolchain, plus
configure's conservative `localtime` runtime answer. It is **not** a claim
that every configure test ran on the physical PS2. Native configure detects
and executes the compiler afresh, then uses these answers to avoid dozens of
compiler reloads over NFS. Every Emacs C file is compiled on the console.
Set `PAKMAN_EMACS_CONFIG_CACHE=none` for all native feature probes, or supply
a path to answers previously generated on this same PS2/libc/toolchain.
The recipe copies any supplied profile, leaving the original unchanged.

The target needs GCC, binutils, Make, curl, sha256sum, patch, tar and the
usual shell tools. It also needs **ncurses development files**: set
`PAKMAN_EMACS_NCURSES` to a directory containing `include/termcap.h` and
`lib/libncurses.a`. The initial experiment reuses the existing PS2 ncurses
6.5 development build, copied under
`/home/ellie/git/pak/.build/emacs-probe/ncurses`. That prerequisite was
cross-built earlier; it is not a native ncurses build or resolved pakman
dependency. No system prefix is modified.

## PS2/musl changes

* Build as little-endian MIPS ELF using the GCC driver and ordinary CRT.
* Disable `unexec` dumping. Startup loads the supplied standard bytecompiled
  Lisp files each time. This avoids unsupported libc heap snapshotting.
* Back Emacs's own GNU allocator with an **8 MiB bounded BSS arena**, rather
  than `sbrk`, which musl cannot grow. A non-PIE executable keeps Lisp pointers
  within Emacs 20's representable address range. BSS reserves address space;
  unused arena pages need not occupy physical RAM. Eight MiB limits the
  allocator's total arena, not the editor's total RSS or kernel/page cache.
* Remove obsolete fixed MIPS data-segment bits; use musl `__fpending`,
  POSIX termios, integer wait statuses and `strsignal`.
* Correct Emacs 20's inverted `--no-loadup` check, and honor the launcher's
  `EMACSLOADPATH` before checking compiled-in paths.
* Retain Makefile continuations with GCC's traditional preprocessor. Replace
  `egrep`/`fgrep` configure calls with `grep -E`/`grep -F` for this BusyBox root.

`build.sh` uses `-O0 -g0`, GCC garbage collection with 5% managed-heap growth, one Make job,
16 MiB data and 64 MiB address-space limits, and small linker hash tables.
The compiler driver uses the same 16 MiB data budget. Initial 8 MiB and 12 MiB compiler
budgets failed cleanly while compiling `regex.c`; no Emacs files were installed.
Macro-expansion diagnostic tracking is disabled (`-ftrack-macro-expansion=0`),
and legacy builtin-declaration warning excerpts are reduced to limit diagnostic
memory and NFS log writes. The failing standalone `regex.c` unit subsequently compiled successfully on
PS2 at 16 MiB; `ps2-regex-16m.log` records the native 62,504-byte object.
A desktop compiler comparison on `etags.c` found that 0% heap growth made
compilation about 21 times slower than 5%, with identical object bytes and
similar sampled peak RSS. This is a desktop comparison, not a PS2 memory
measurement. The current native retry began at 0%; subsequent compiler
invocations use 5% after a recorded live wrapper adjustment, while the
16 MiB data limit and 4 MiB global reserve remain in force.
The retry enables `PAKMAN_KEEP_FAILED_BUILDS=1` so failures preserve diagnostics
and completed objects rather than deleting the entire build directory.
Those are allocation backstops, not a bound on combined descendant RSS or
NFS cache pressure. A build takes substantially longer than the prototype's
default 90-second watchdog; use an appropriate explicit timeout and monitor
available memory on the physical console.

`emacs.sh` finds the isolated installation prefix and sets the Lisp/data/doc/
helper/manual paths. It does not depend on the retained build directory.
Directory trees enter pakman's normal per-file ownership transaction, with
symlinks and overlapping file destinations rejected.

## Validation required before calling the port complete

1. Native configure and full C compilation on PS2.
2. Native Emacs Lisp smoke test (the recipe runs this before installation).
3. Native SubsetML/MLWorks package program and updated manager.
4. Pakman install/list/ownership verification in `~/git/pak/.local`.
5. Terminal edit/save/exit, plus an installed batch Lisp check.

GNU Emacs is GPL-2.0-or-later; the installed package includes `COPYING`.
