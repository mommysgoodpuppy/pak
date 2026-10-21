import { packages } from "./upstream.ts";

const hash = "a".repeat(64);
function entry(version: string, overrides: Record<string, string> = {}): string {
  const fields = {
    Package: "unityhub", Architecture: "amd64", Version: version,
    Filename: `pool/main/u/unity/UnityHubSetup-${version}-amd64.deb`,
    SHA256: hash, ...overrides,
  };
  return Object.entries(fields).map(([key, value]) => `${key}: ${value}`).join("\n");
}
function equal(actual: unknown, expected: unknown): void {
  if (JSON.stringify(actual) !== JSON.stringify(expected)) {
    throw new Error(`expected ${JSON.stringify(expected)}, got ${JSON.stringify(actual)}`);
  }
}

Deno.test("Hub finder sorts versions numerically regardless of index order", () => {
  const index = [entry("3.9.1"), entry("3.22.2"), entry("3.10.0"), entry("3.22.1")].join("\n\n");
  equal(packages(index).map((p) => p.version), ["3.22.2", "3.22.1", "3.10.0", "3.9.1"]);
  equal(packages(index)[0].sha256, hash);
});

Deno.test("Hub finder rejects unrelated packages and unsafe or incomplete metadata", () => {
  const invalid: Record<string, string>[] = [
    { Package: "another-app" }, { Architecture: "arm64" }, { Version: "3.23.0-beta.1" },
    { Filename: "https://other.example/payload.deb" }, { Filename: "pool/../payload.deb" },
    { SHA256: "" }, { SHA256: "not-a-hash" },
  ];
  equal(packages(invalid.map((fields) => entry("3.22.2", fields)).join("\n\n")), []);
});

Deno.test("Hub finder handles CRLF and Debian continuation lines", () => {
  const index = `${entry("3.22.2")}\nDescription: The Official Unity Hub\n more details\n\n`.replaceAll("\n", "\r\n");
  equal(packages(index), [{ version: "3.22.2", filename: "pool/main/u/unity/UnityHubSetup-3.22.2-amd64.deb", sha256: hash }]);
});
