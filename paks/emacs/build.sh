#!/bin/sh
set -eu
checksums=$1
patch_file=$2
launcher=$3
out=$4
profile=$5
# This is an explicit development prerequisite, separate from the Emacs source.
ncurses=${PAKMAN_EMACS_NCURSES:-/home/ellie/git/pak/.build/emacs-probe/ncurses}
test -f "$ncurses/lib/libncurses.a" && test -f "$ncurses/include/termcap.h" || {
  echo 'Emacs requires ncurses development files; set PAKMAN_EMACS_NCURSES.' >&2
  exit 1
}
# Keep compiler allocation bounded on the 27 MiB console; never parallelize.
ulimit -d 16384
ulimit -v 65536
if test -n "${PAKMAN_EMACS_SOURCE:-}"; then
  cp "$PAKMAN_EMACS_SOURCE" emacs-20.7.tar.gz
else
  /usr/bin/curl -fsSL --connect-timeout 15 --max-time 300 \
    https://ftp.gnu.org/old-gnu/emacs/emacs-20.7.tar.gz -o emacs-20.7.tar.gz
fi
/usr/bin/sha256sum -c "$checksums"
tar xzf emacs-20.7.tar.gz
cd emacs-20.7
chmod -R u+w .
patch -p1 < "$patch_file"
# GCC's normal preprocessor destroys the Makefile's line continuations.
sed -e 's/\$CPP \$undefs/\$CPP -traditional-cpp \$undefs/g' -e 's/egrep /grep -E /g' -e 's/fgrep /grep -F /g' configure > configure-ps2
# The manager remains resident while a build runs. Give each compiler/linker
# the same 16 MiB data budget as the editor process.
cat > ../ps2-cc.sh <<'PS2_CC'
#!/bin/sh
ulimit -d 16384
exec /usr/bin/gcc "$@"
PS2_CC
chmod 755 ../ps2-cc.sh
export CC="$PWD/../ps2-cc.sh" INSTALL=/usr/bin/install
export CFLAGS='-O0 -g0 -ftrack-macro-expansion=0 -fno-diagnostics-show-caret -Wno-builtin-declaration-mismatch -std=gnu89 -fcommon -fwrapv -fno-strict-aliasing -fno-pie -Wno-error=implicit-function-declaration -Wno-error=int-conversion -Wno-error=incompatible-pointer-types --param ggc-min-expand=5 --param ggc-min-heapsize=1024'
export CPPFLAGS="-I$ncurses/include"
export LDFLAGS="-no-pie -L$ncurses/lib -Wl,--reduce-memory-overheads -Wl,--hash-size=1021"
# This target profile avoids repeated compiler loads over the NFS root.
# "none" requests every probe; an explicit path can supply native answers.
cache=${PAKMAN_EMACS_CONFIG_CACHE:-$profile}
if test "$cache" != none; then
  sed -e '/^ac_cv_prog_CC=/d' -e '/^ac_cv_prog_CPP=/d' \
      -e '/^ac_cv_prog_cc_/d' "$cache" > config.cache
fi
# The launcher supplies the eventual prefix, so the build is relocatable.
if ! sh ./configure-ps2 --host=mips-unknown-linux-gnu --without-x --prefix=/__pakman_emacs20 > configure-ps2.log 2>&1; then
  tail -n 80 configure-ps2.log >&2
  test ! -f config.log || tail -n 80 config.log >&2
  exit 1
fi
export EMACSLOADPATH="$PWD/lisp" EMACSDATA="$PWD/etc" EMACSDOC="$PWD/etc" EMACSPATH="$PWD/lib-src"
if ! make -j1 > build-ps2.log 2>&1; then
  tail -n 100 build-ps2.log >&2
  exit 1
fi
mkdir -p "$out/exec/helpers" "$out/share/lisp" "$out/share/etc" "$out/share/info"
cp src/emacs "$out/exec/emacs"
strip "$out/exec/emacs"
for helper in emacsserver emacsclient etags ctags b2m movemail fakemail hexl profile digest-doc sorted-doc cvtmail yow rcs2log vcdiff rcs-checkin; do
  test ! -f "lib-src/$helper" || cp "lib-src/$helper" "$out/exec/helpers/$helper"
done
# Preserve the complete standard Lisp/data/manual distribution. Symlinks in
# the source are dereferenced here; pakman refuses symlinks in the payload.
cp -RL lisp/. "$out/share/lisp/"
cp -RL etc/. "$out/share/etc/"
cp -RL info/. "$out/share/info/"
cp COPYING "$out/COPYING"
cp "$launcher" "$out/emacs.sh"
# A real Lisp/editing check before the manager installs any files.
if ! EMACSLOADPATH="$PWD/lisp" EMACSDATA="$PWD/etc" EMACSDOC="$PWD/etc" EMACSPATH="$PWD/lib-src" \
  ./src/emacs -batch --eval '(progn (unless (= (+ 20 22) 42) (error "integer arithmetic failed")) (with-temp-buffer (insert "PS2 Emacs Lisp works\n") (write-region (point-min) (point-max) "../emacs-smoke.txt" nil 0)) (princ "EMACS_NATIVE_OK\n"))' \
  > smoke-ps2.log 2>&1; then
  tail -n 60 smoke-ps2.log >&2
  exit 1
fi
if ! grep -q EMACS_NATIVE_OK smoke-ps2.log; then
  tail -n 60 smoke-ps2.log >&2
  exit 1
fi
