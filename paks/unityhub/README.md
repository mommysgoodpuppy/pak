# Unity Hub

Uses Unity's official stable amd64 Debian repository. The pure `upstream.ts`
helper parses, validates, and numerically orders index entries. The Workman
finder dates the newest eight artifacts from their Last-Modified headers and
returns the index's SHA-256 checksums. Pakman applies the usual three-day age
gate and verifies downloads before building.

The finder allows both `hub.unity3d.com` and its observed redirect host
`hub-dist.unity3d.com`. No APT repository or Debian maintainer script is run.
Current Forge packages are extracted unchanged under `/usr/lib/unityhub`,
including their `/usr/bin/unityhub` symlink, desktop entry, icons, and licensing
client. The recipe also handles the older fpm filename/layout convention.

## Validation, 2026-10-12

- Resolved and built Hub **3.22.2** in an isolated pakman state.
- Source SHA-256 checked against Unity's index:
  `a0523a62fc6f221a9cea272ca347719671fcd519b8b1d9ff833a3914dec12220`.
- Installed with ALCOM into a temporary root; launcher symlink resolves correctly.
- Desktop entry and shell launcher syntax pass validation.
- Hub binary and licensing client have no missing libraries on this host.
- Three parser tests pass (numeric order, invalid metadata, Debian text format).
- Live GUI launch, account sign-in, and editor installation remain untested.

The repository checksum was obtained over upstream HTTPS; APT metadata signatures
were not independently verified by this recipe.

```sh
wm pakman resolve unityhub
wm pakman build unityhub
wm pakman install unityhub
```

After installation, use Hub to sign in and install the editor. Ellie's Velle2025
project and VRChat's checked requirements use **2022.3.22f1**. Hub itself can
update independently; this package does not automatically upgrade Unity projects
or install editor modules.
