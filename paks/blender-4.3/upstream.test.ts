import { versionsFromIndex, checksumFor } from "./upstream.ts";

function equal(actual: unknown, expected: unknown) {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) throw new Error(`Unexpected result: ${JSON.stringify(actual)}`);
}

Deno.test("Blender finder stays on 4.3, selects Linux x64, and orders patches numerically", () => {
  const files = ["4.3.2-linux-x64.tar.xz", "4.3.10-linux-x64.tar.xz", "4.3.2-windows-x64.zip",
    "4.4.0-linux-x64.tar.xz", "4.3.1-linux-x64.tar.xz", "4.3.2-linux-x64.tar.xz", "4.3.3-linux-arm64.tar.xz"];
  equal(versionsFromIndex(files.map((f) => `<a href="blender-${f}">download</a>`).join("\n")), ["4.3.10", "4.3.2", "4.3.1"]);
});

Deno.test("Checksum finder requires an exact filename and a complete SHA-256", () => {
  const hash = "a".repeat(64);
  const filename = "blender-4.3.2-linux-x64.tar.xz";
  equal(checksumFor(`${"b".repeat(64)}  ${filename}.bad\r\n${hash.toUpperCase()} *${filename}\r\n`, filename), hash);
  equal(checksumFor(`bad-hash  ${filename}\n`, filename), "");
  equal(checksumFor(`${hash}  blender-4.3.2-windows-x64.zip\n`, filename), "");
});
