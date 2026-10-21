// Parse Unity's Debian Packages index without depending on its entry order.
// This helper is pure: only the Workman finder performs network requests.
export function packages(text: string): { version: string; filename: string; sha256: string }[] {
  const entries = [];
  for (const block of text.replaceAll("\r\n", "\n").split(/\n\n+/)) {
    const fields = new Map<string, string>();
    for (const line of block.split("\n")) {
      const match = /^([A-Za-z0-9-]+):[ \t]*(.*)$/.exec(line);
      if (match) fields.set(match[1], match[2]);
    }
    if (fields.get("Package") !== "unityhub" || fields.get("Architecture") !== "amd64") continue;
    const version = fields.get("Version") ?? "";
    const filename = fields.get("Filename") ?? "";
    const sha256 = fields.get("SHA256") ?? "";
    if (!/^\d+\.\d+\.\d+$/.test(version)) continue;
    if (!/^pool\/[A-Za-z0-9_./-]+\.deb$/.test(filename) || filename.split("/").includes("..")) continue;
    if (!/^[a-f0-9]{64}$/.test(sha256)) continue;
    entries.push({ version, filename, sha256 });
  }
  return entries.sort((a, b) => {
    const left = a.version.split(".").map(Number);
    const right = b.version.split(".").map(Number);
    for (let i = 0; i < 3; i++) if (left[i] !== right[i]) return right[i] - left[i];
    return 0;
  });
}
