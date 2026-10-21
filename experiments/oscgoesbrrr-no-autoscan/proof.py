"""Offline proof against pakman's cached 2.1.30 binary; never installs or launches it.

Usage: python proof.py /path/to/pakman/sources/10e87...
Requires unsquashfs and Node. Outputs a JSON report, not a modified application.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

EXPECTED = "10e87dc675187accd3cda82bd526167e1c2dbfa139a9c592e7d0158568b86196"
image = Path(sys.argv[1]).read_bytes()
if hashlib.sha256(image).hexdigest() != EXPECTED:
    raise SystemExit("Refusing input: expected the locked upstream 2.1.30 AppImage")
offsets = []
cursor = 0
while (index := image.find(b"hsqs", cursor)) >= 0:
    cursor = index + 4
    if index + 96 <= len(image):
        version = struct.unpack_from("<HH", image, index + 28)
        used = struct.unpack_from("<Q", image, index + 40)[0]
        if version == (4, 0) and 96 < used <= len(image) - index:
            offsets.append(index)
if len(offsets) != 1:
    raise SystemExit("Expected exactly one valid SquashFS payload")
asar = subprocess.check_output([
    "unsquashfs", "-cat", "-offset", str(offsets[0]), sys.argv[1], "resources/app.asar"
])
header = json.loads(asar[16:16 + struct.unpack_from("<I", asar, 12)[0]])
base = 8 + struct.unpack_from("<I", asar, 4)[0]
files = header["files"]["out"]["files"]["main"]["files"]
matches = [(name, entry) for name, entry in files.items() if name.startswith("main-") and name.endswith(".js")]
if len(matches) != 1:
    raise SystemExit("Expected exactly one bundled main module")
name, entry = matches[0]
start = base + int(entry["offset"])
original = asar[start:start + entry["size"]].decode()
anchor = "        this.startScanTimer();"
if original.count(anchor) != 1:
    raise SystemExit("Scan patch context drifted; manual review required")
patched = original.replace(anchor, "        // Discovery is managed manually in Intiface Central.", 1)
begin = original.index("class IntifaceSession extends TypedEventEmitter {")
end = original.index("\n}\n", begin) + 2
session = original[begin:end]
patched_session = session.replace(anchor, "        // Discovery is managed manually in Intiface Central.", 1)
test = r'''
import assert from 'node:assert/strict';
import {EventEmitter} from 'node:events';
import vm from 'node:vm';
const sources = SOURCES;
for (const [name, source] of Object.entries(sources)) {
    const timers = new Map(); let nextTimer = 1;
    const context = vm.createContext({
        TypedEventEmitter: EventEmitter, AbortSignal,
        WebSocket$1: class { readyState = 1; OPEN = 1; terminate() {} },
        setInterval: (fn, delay) => { const id = nextTimer++; timers.set(id, {fn, delay}); return id; },
        clearInterval: id => timers.delete(id),
        setTimeout: fn => { fn(); return 0; }, clearTimeout: () => {},
    });
    const Session = vm.runInContext(source + '\nIntifaceSession', context);
    const s = new Session('ws://unused.invalid', {log() {}});
    s.attachSocketHandlers = () => {};
    s.waitForOpen = async () => {};
    const requests = [];
    s.request = async message => { requests.push(message.type); };
    s.initialDeviceList = {};
    let listEvents = 0; s.on('deviceList', () => listEvents++);
    await s.connect(new AbortController().signal);
    assert.deepEqual(requests, ['RequestServerInfo', 'RequestDeviceList']);
    assert.equal(listEvents, 1); assert.equal(s.isReady(), true);
    assert.equal(timers.size, name === 'original' ? 2 : 1);
    // Exercise the actual output entry point, mocking only serialization/transport.
    let sent;
    s.preparePacket = message => ({id: 1, packet: message});
    s.sendPacket = packet => { sent = packet; };
    assert.equal(s.sendAndForget({type: 'OutputCmd'}), 1);
    assert.equal(sent.type, 'OutputCmd');
    s.dispose(); assert.equal(timers.size, 0);
}
console.log('PASS: original starts the scan timer; patched session does not; handshake, initial list, output routing and cleanup retained (mock transport).');
'''.replace("SOURCES", json.dumps({"original": session, "patched": patched_session}))
with tempfile.TemporaryDirectory(prefix="pak-scan-proof-") as tmp:
    syntax = Path(tmp) / "main.mjs"
    syntax.write_text(patched)
    subprocess.run(["node", "--check", str(syntax)], check=True)
    tests = Path(tmp) / "test.mjs"
    tests.write_text(test)
    result = subprocess.check_output(["node", str(tests)], text=True).strip()
print(json.dumps({
    "upstream_sha256": EXPECTED,
    "appimage_offset": offsets[0],
    "asar_entry": "out/main/" + name,
    "original_module_sha256": hashlib.sha256(original.encode()).hexdigest(),
    "patched_module_sha256": hashlib.sha256(patched.encode()).hexdigest(),
    "validation": result,
    "installed": False,
    "limits": "No ASAR/AppImage repack, Electron launch, hardware test or pakman activation was performed."
}, indent=2))
