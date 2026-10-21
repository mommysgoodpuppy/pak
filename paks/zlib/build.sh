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
if test -n "${PAKMAN_ZLIB_SOURCE:-}"; then
  cp "$PAKMAN_ZLIB_SOURCE" zlib-1.3.1.tar.gz
else
  /usr/bin/curl -fsSL --connect-timeout 15 --max-time 300 https://zlib.net/fossils/zlib-1.3.1.tar.gz -o zlib-1.3.1.tar.gz
fi
/usr/bin/sha256sum -c "$checksums"
tar xzf zlib-1.3.1.tar.gz
cd zlib-1.3.1
if ! ./configure --static --prefix=/__pakman_zlib > configure-ps2.log 2>&1; then tail -n 60 configure-ps2.log >&2; exit 1; fi
if ! /usr/bin/make -j1 static > build-ps2.log 2>&1; then tail -n 60 build-ps2.log >&2; exit 1; fi
if ! /usr/bin/make -j1 teststatic > smoke-ps2.log 2>&1; then tail -n 60 smoke-ps2.log >&2; exit 1; fi
mkdir -p "$out"
cp libz.a zlib.h zconf.h LICENSE "$out/"
# A relocatable development package, independent of the retained build path.
sed 's|^prefix=.*|prefix=${pcfiledir}/../..|' zlib.pc > "$out/zlib.pc"
