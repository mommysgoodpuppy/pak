"""Validate a pakman-built artifact without launching or installing Electron."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile

original = Path(sys.argv[1])
artifact = Path(sys.argv[2])
def module(path):
    image = path.read_bytes()
    offsets = []
    pos = 0
    while (idx := image.find(b'hsqs', pos)) >= 0:
        pos = idx + 4
        if idx+96 <= len(image) and struct.unpack_from('<HH', image, idx+28) == (4, 0):
            if 96 < struct.unpack_from('<Q', image, idx+40)[0] <= len(image)-idx:
                offsets.append(idx)
    assert len(offsets) == 1
    offset = offsets[0]
    asar = subprocess.check_output(['unsquashfs', '-cat', '-offset', str(offset), str(path), 'resources/app.asar'])
    header = json.loads(asar[16:16+struct.unpack_from('<I', asar, 12)[0]])
    entries = [(name, entry) for name, entry in header['files']['out']['files']['main']['files'].items() if name.startswith('main-') and name.endswith('.js')]
    assert len(entries) == 1
    name, entry = entries[0]
    start = 8 + struct.unpack_from('<I', asar, 4)[0] + int(entry['offset'])
    data = asar[start:start+entry['size']]
    if 'integrity' in entry:
        integrity = entry['integrity']; block = integrity['blockSize']
        assert hashlib.sha256(data).hexdigest() == integrity['hash']
        assert [hashlib.sha256(data[i:i+block]).hexdigest() for i in range(0, len(data), block)] == integrity['blocks']
    return image, offset, data.decode(), name

old, offset, original_module, name = module(original)
new, new_offset, patched_module, patched_name = module(artifact)
assert hashlib.sha256(old).hexdigest() == '10e87dc675187accd3cda82bd526167e1c2dbfa139a9c592e7d0158568b86196'
assert new_offset == offset and old[:offset] == new[:offset], 'runtime changed'
anchor = '        this.startScanTimer();'
assert patched_name == name
assert patched_module == original_module.replace(anchor, ' '*len(anchor), 1)
def session(text):
    begin = text.index('class IntifaceSession extends TypedEventEmitter {')
    return text[begin:text.index('\n}\n', begin)+2]
# Reuse the prior transport-mocked behavior test, now against the repacked file.
proof = Path(__file__).with_name('proof.py').read_text()
test = re.search(r"test = r'''(.*?)'''", proof, re.S)[1].replace('SOURCES', json.dumps({'original':session(original_module), 'patched':session(patched_module)}))
with tempfile.TemporaryDirectory(prefix='pak-repack-check-') as tmp:
    syntax = Path(tmp)/'main.mjs'; syntax.write_text(patched_module)
    subprocess.run(['node', '--check', str(syntax)], check=True)
    behavior = Path(tmp)/'test.mjs'; behavior.write_text(test)
    result = subprocess.check_output(['node', str(behavior)], text=True).strip()
installed = Path.home()/'.local/lib/oscgoesbrrr/oscgoesbrrr.AppImage'
assert hashlib.sha256(installed.read_bytes()).digest() == hashlib.sha256(old).digest()
print(json.dumps(dict(artifact=str(artifact), upstream_sha256=hashlib.sha256(old).hexdigest(), output_sha256=hashlib.sha256(new).hexdigest(), patched_module_sha256=hashlib.sha256(patched_module.encode()).hexdigest(), validation=result, runtime_preserved=True, asar_integrity_valid=True, installed_changed=False, limits='No Electron launch, activation or hardware test'), indent=2))
