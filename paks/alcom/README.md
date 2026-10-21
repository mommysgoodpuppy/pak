# ALCOM

Packages the official native amd64 Debian payload from `vrc-get/vrc-get`.
Only non-prerelease `gui-vX.Y.Z` tags with the matching Debian asset are
candidates; plain `vX.Y.Z` tags are CLI releases and are ignored. Pakman applies
its usual three-day age gate and verifies GitHub's asset digest.

The payload installs `/usr/bin/alcom`, its desktop entry (including the VCC URL
handler), icons, and Debian copyright information. It uses the host's GTK 3 and
WebKitGTK 4.1. Both are already present on Ellie's machine. ALCOM is an unofficial
VCC alternative, not Unity or the VRChat SDK itself.

GUI 1.1.7 and newer use `data.tar.zst`; older GUI releases use `data.tar.gz`.
The package now discovers the actual payload member rather than choosing its
compression from the version. Archive headers were checked for 1.1.6, 1.1.7, and 1.1.8; a complete build and
temporary installation were verified for **1.1.8** on 2026-10-12.

Source SHA-256 checked against GitHub's published digest:
`11ec00c57ae9e83d920998152c37a34816b9d8f3fbc616455b5593b994047402`.
Desktop entry validation passed and the binary has no missing linked libraries.
Live GUI/project management remains untested. No live system installation was
made during package authoring.

```sh
wm pakman resolve alcom
wm pakman build alcom
wm pakman install alcom
```

Register the transferred Linux Unity project after making a verified working
copy. Do not copy Windows VCC settings wholesale: drive paths need translating.
