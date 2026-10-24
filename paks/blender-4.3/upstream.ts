// Only Blender 4.3 Linux x64 archives are candidates; other series stay separate.
export function versionsFromIndex(text: string): string[] {
  return [...new Set([...text.matchAll(/href="blender-(4\.3\.\d+)-linux-x64\.tar\.xz"/g)].map((m) => m[1]))]
    .sort((a, b) => Number(b.split(".")[2]) - Number(a.split(".")[2]));
}

export function checksumFor(text: string, filename: string): string {
  for (const line of text.split(/\r?\n/)) {
    const match = /^([a-fA-F0-9]{64})[ \t]+\*?(.+)$/.exec(line);
    if (match && match[2] === filename) return match[1].toLowerCase();
  }
  return "";
}
