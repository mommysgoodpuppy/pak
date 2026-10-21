"""Offline, version-specific AppImage transform. Called by the Workman build.

Keep ASAR entry lengths unchanged, update its integrity hashes, rebuild the
SquashFS payload and retain the original type-2 AppImage runtime. Never launch.
"""
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys

EXPECTED = '10e87dc675187accd3cda82bd526167e1c2dbfa139a9c592e7d0158568b86196'
source, output = map(Path, sys.argv[1:])
image = source.read_bytes()
if hashlib.sha256(image).hexdigest() != EXPECTED:
    raise SystemExit('Expected the reviewed upstream 2.1.30 AppImage; refusing drift')
offsets = []
pos = 0
while (idx := image.find(b'hsqs', pos)) >= 0:
    pos = idx + 4
    if idx + 96 <= len(image) and struct.unpack_from('<HH', image, idx + 28) == (4, 0):
        used = struct.unpack_from('<Q', image, idx + 40)[0]
        if 96 < used <= len(image) - idx:
            offsets.append(idx)
if len(offsets) != 1:
    raise SystemExit('Expected one SquashFS payload')
offset = offsets[0]
root = Path('/work/appdir')
subprocess.run(['/usr/bin/unsquashfs', '-no-progress', '-processors', '2', '-offset', str(offset), '-d', str(root), str(source)], check=True)
asar_path = root / 'resources/app.asar'
asar = bytearray(asar_path.read_bytes())
header_size = struct.unpack_from('<I', asar, 12)[0]
header_raw = bytes(asar[16:16+header_size])
header = json.loads(header_raw)
base = 8 + struct.unpack_from('<I', asar, 4)[0]
files = header['files']['out']['files']['main']['files']
entries = [(name, entry) for name, entry in files.items() if name.startswith('main-') and name.endswith('.js')]
if len(entries) != 1:
    raise SystemExit('Expected one main module')
name, entry = entries[0]
start = base + int(entry['offset'])
original = bytes(asar[start:start+entry['size']])
anchor = b'        this.startScanTimer();'
if original.count(anchor) != 1:
    raise SystemExit('Patch context drift; refusing build')
patched = original.replace(anchor, b' ' * len(anchor), 1)
asar[start:start+len(patched)] = patched
# ASAR offsets and pickle lengths stay unchanged. Rewrite only the reviewed
# module's integrity values, preserving every other header field and entry.
if json.dumps(header, separators=(',', ':'), ensure_ascii=False).encode() != header_raw:
    raise SystemExit('Unexpected ASAR header encoding')
if 'integrity' in entry:
    integrity = entry['integrity']
    if integrity['algorithm'] != 'SHA256':
        raise SystemExit('Unknown ASAR integrity algorithm')
    block = integrity['blockSize']
    integrity['hash'] = hashlib.sha256(patched).hexdigest()
    integrity['blocks'] = [hashlib.sha256(patched[i:i+block]).hexdigest() for i in range(0, len(patched), block)]
new_header = json.dumps(header, separators=(',', ':'), ensure_ascii=False).encode()
if len(new_header) != header_size:
    raise SystemExit('ASAR integrity changed header size')
asar[16:16+header_size] = new_header
asar_path.write_bytes(asar)
# All unmodified ASAR bytes outside the header and module are retained.
syntax = Path('/work/main.mjs')
syntax.write_bytes(patched)
# Node is not required here: semantic and syntax checks are separate from this
# transform, using the offline proof in experiments/oscgoesbrrr-no-autoscan.
squash = Path('/work/payload.squashfs')
subprocess.run(['/usr/bin/mksquashfs', str(root), str(squash), '-noappend', '-no-progress', '-processors', '2', '-all-root', '-comp', 'xz'], check=True)
output.parent.mkdir(parents=True, exist_ok=True)
with output.open('wb') as dest:
    dest.write(image[:offset])
    dest.write(squash.read_bytes())
output.chmod(0o755)
# Read the finished artifact through SquashFS to verify the staged result.
roundtrip = subprocess.check_output(['/usr/bin/unsquashfs', '-cat', '-offset', str(offset), str(output), 'resources/app.asar'])
if roundtrip != asar:
    raise SystemExit('Repacked ASAR did not round-trip')
print(json.dumps({'upstream_sha256': EXPECTED, 'output_sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'module': 'out/main/'+name, 'patched_module_sha256': hashlib.sha256(patched).hexdigest(), 'offset': offset}))
