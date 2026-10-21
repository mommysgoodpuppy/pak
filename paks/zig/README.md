# Zig

The package program discovers stable releases and the current development build
from Zig's official download index. Each candidate carries the exact platform
URL as its `ref`, alongside the index's SHA-256. Pakman records that ref in the
lock and supplies it to `make`; the installation plan does not reconstruct
filenames or distinguish stable/dev download paths.

The tree remains under `.local/lib/zig`, with `.local/bin/zig` pointing to its
binary. Discovery and installation planning can be run independently:

```sh
wm run paks/zig/pak.wm -- versions
wm run paks/zig/pak.wm -- make 0.14.1 \
  "https://ziglang.org/download/0.14.1/zig-x86_64-linux-0.14.1.tar.xz"
```

Use the selected candidate's ref for other versions. Existing Zig locks with an
empty ref need `wm pakman resolve zig` (with the same `--root` if applicable)
before building; the definition reports this explicitly. The lock format and
manager API are unchanged.

Validated on 2026-10-13: all 24 platform candidates matched the official index's
URL/checksum, and installation operations matched the previous definition. Two
offline fixtures exercise stable and development builds with irregular URLs:
`wm test paks/zig/pak.test.wm`. Empty refs fail with a re-resolve instruction.
No live lock, installation, or package version was changed during this refactor.
