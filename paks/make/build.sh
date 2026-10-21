#!/bin/sh
set -eu
checksums=$1
out=$2
ulimit -c 0
ulimit -d 16384
ulimit -v 65536
export CC=/usr/bin/gcc AR=/usr/bin/ar RANLIB=/usr/bin/ranlib
export CFLAGS='-O0 -g0 -std=gnu17 -ftrack-macro-expansion=0 --param ggc-min-expand=5 --param ggc-min-heapsize=1024'
export LDFLAGS='-Wl,--reduce-memory-overheads -Wl,--hash-size=1021'
if test -n "${PAKMAN_MAKE_SOURCE:-}"; then
  cp "$PAKMAN_MAKE_SOURCE" make-4.4.1.tar.gz
else
  /usr/bin/curl -fsSL --connect-timeout 15 --max-time 300 https://ftp.gnu.org/gnu/make/make-4.4.1.tar.gz -o make-4.4.1.tar.gz
fi
/usr/bin/sha256sum -c "$checksums"
tar xzf make-4.4.1.tar.gz
cd make-4.4.1
# Feature answers from the matching cross-built PS2/musl profile.
# Native configure still detects and executes the compiler itself.
cache=${PAKMAN_MAKE_CONFIG_CACHE:-$3}
if test "$cache" != none; then cp "$cache" config.cache; fi
if ! ./configure --cache-file=config.cache --prefix=/__pakman_make --without-guile --disable-nls --disable-dependency-tracking > configure-ps2.log 2>&1; then
  tail -n 60 configure-ps2.log >&2; exit 1
fi
if ! /usr/bin/make -j1 > build-ps2.log 2>&1; then tail -n 60 build-ps2.log >&2; exit 1; fi
mkdir -p "$out"
cp make "$out/make"
/usr/bin/strip "$out/make"
cp src/gnumake.h "$out/make.h"
cp COPYING "$out/COPYING"
cat > smoke.mk <<'MAKE_TEST'
all:
	@printf '%s\n' MAKE_NATIVE_OK
MAKE_TEST
./make -rR -f smoke.mk > smoke-ps2.log 2>&1
grep -q MAKE_NATIVE_OK smoke-ps2.log
