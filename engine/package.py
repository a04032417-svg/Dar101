#!/usr/bin/env python3
"""The buyer's package: a ZIP of the 15 language workbooks + the English demo + README.txt, and its encrypted form pkg.fxp
(SPEC.md "Package format"):  b"FXP1" · u16 big-endian N · N bytes = 32-byte AES key wrapped with RSA-OAEP (SHA-1, MGF1-SHA-1) ·
12-byte IV · 16-byte GCM tag · AES-256-GCM ciphertext of the ZIP (no associated data).
CLI: python3 package.py --selftest        (makes an RSA-3072 key pair, encrypts, decrypts, compares)"""
import os, sys, io, zipfile, struct, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import LANGS, LANG_NAMES, file_base
try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.asymmetric import padding, rsa
    from cryptography.hazmat.primitives import hashes, serialization
except ImportError:  # pip install cryptography --break-system-packages
    raise SystemExit('package.py needs the "cryptography" module: pip install cryptography --break-system-packages')

MAGIC = b'FXP1'
OAEP = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA1(), label=None)


def readme(spec):
    base = file_base(spec); xl = any(f in json_dump(spec) for f in ('MAXIFS', 'MINIFS', 'TEXTJOIN'))
    lines = [f'{spec["name"]}', spec['tagline'], '',
             'FILES',
             *[f'  {base}_{l.upper()}.xlsx   {LANG_NAMES[l]}' for l in LANGS],
             f'  {base}_EN_DEMO-sample-data.xlsx   English copy filled with sample data, to see every feature working', '',
             'HOW TO START',
             '  1. Open the file in your language and read the Start sheet.',
             '  2. Type your settings on the Start sheet (yellow cells).',
             '  3. Type your own data in the white cells; gray cells calculate by themselves.',
             '  4. Choose a value from the drop-downs wherever a cell offers one.', '',
             'FILE FORMAT',
             '  Standard .xlsx files for Microsoft Excel and LibreOffice Calc (tested in LibreOffice Calc). No macros.',
             '  The formulas calculate when the file opens; if your app asks, allow it to update.', '',
             'Personal use licence: one business may use the files; please do not resell or share them.']
    return '\r\n'.join(lines) + '\r\n'


def json_dump(spec):
    import json
    return json.dumps(spec, ensure_ascii=False)


def make_zip(spec, templates, demo, out_zip):
    """templates: {lang: path}; demo: path of the English demo workbook."""
    base = file_base(spec)
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for l in LANGS: z.write(templates[l], f'{base}_{l.upper()}.xlsx')
        z.write(demo, f'{base}_EN_DEMO-sample-data.xlsx')
        z.writestr('README.txt', readme(spec))
    return out_zip


def encrypt(zip_bytes, pubkey_pem):
    """-> FXP1 bytes. pubkey_pem: PEM text or bytes of the RSA public key (Dar's pubkey.pem)."""
    pub = serialization.load_pem_public_key(pubkey_pem.encode() if isinstance(pubkey_pem, str) else pubkey_pem)
    key = AESGCM.generate_key(bit_length=256); iv = os.urandom(12)
    ct_tag = AESGCM(key).encrypt(iv, zip_bytes, None); ct, tag = ct_tag[:-16], ct_tag[-16:]
    wrapped = pub.encrypt(key, OAEP)
    return MAGIC + struct.pack('>H', len(wrapped)) + wrapped + iv + tag + ct


def decrypt(blob, privkey_pem):
    """The reverse of encrypt (what Dar's PHP does) — used by the self-test."""
    if blob[:4] != MAGIC: raise ValueError('not an FXP1 package')
    n = struct.unpack('>H', blob[4:6])[0]; p = 6
    wrapped = blob[p:p + n]; p += n; iv = blob[p:p + 12]; p += 12; tag = blob[p:p + 16]; p += 16
    priv = serialization.load_pem_private_key(privkey_pem.encode() if isinstance(privkey_pem, str) else privkey_pem, password=None)
    key = priv.decrypt(wrapped, OAEP)
    return AESGCM(key).decrypt(iv, blob[p:] + tag, None)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''): h.update(chunk)
    return h.hexdigest()


def selftest(data=None):
    priv = rsa.generate_private_key(public_exponent=65537, key_size=3072)
    pub_pem = priv.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    priv_pem = priv.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
    data = data if data is not None else os.urandom(200_000)
    blob = encrypt(data, pub_pem)
    ok = decrypt(blob, priv_pem) == data
    n = struct.unpack('>H', blob[4:6])[0]
    bad = bytearray(blob); bad[-1] ^= 1
    try: decrypt(bytes(bad), priv_pem); tamper = False
    except Exception: tamper = True
    return {'ok': ok and n == 384 and tamper, 'wrapped_key_bytes': n, 'size': len(blob), 'overhead': len(blob) - len(data), 'tamper_detected': tamper}


if __name__ == '__main__':
    if '--selftest' in sys.argv:
        import json
        r = selftest(open(sys.argv[2], 'rb').read() if len(sys.argv) > 2 and os.path.exists(sys.argv[2]) else None)
        print(json.dumps(r)); sys.exit(0 if r['ok'] else 1)
    print(__doc__)
