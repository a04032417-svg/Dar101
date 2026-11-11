#!/usr/bin/env python3
"""recalc.py <file.xlsx> [timeout] — LibreOffice opens the workbook, recalculates every formula and saves it; then each cell is scanned for
an error value. Prints {"status","total_formulas","total_errors","error_summary":{err:{"count","locations"}}} (the shape verify.py reads).
The engine's own recalculator (2026-11-07), so the factory's verification worker needs nothing but LibreOffice."""
import os, sys, json, shutil, subprocess, tempfile, time
from openpyxl import load_workbook

ERRS = ('#REF!', '#VALUE!', '#NAME?', '#DIV/0!', '#N/A', '#NUM!', '#NULL!')
MACRO = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script:module PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "module.dtd">
<script:module xmlns:script="http://openoffice.org/2000/script" script:name="Module1" script:language="StarBasic">
Sub Recalc
  ThisComponent.calculateAll()
  ThisComponent.store()
  ThisComponent.close(True)
End Sub
</script:module>'''
XLB = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "library.dtd">
<library:library xmlns:library="http://openoffice.org/2000/library" library:name="Standard" library:readonly="false" library:passwordprotected="false">
 <library:element library:name="Module1"/>
</library:library>'''


def soffice():
    for c in ('soffice', 'libreoffice', '/usr/bin/soffice', '/usr/lib/libreoffice/program/soffice', '/opt/libreoffice/program/soffice'):
        p = shutil.which(c) or (c if os.path.exists(c) else None)
        if p: return p
    raise SystemExit(json.dumps({'error': 'LibreOffice (soffice) not found'}))


def profile(base, timeout):
    """a private LibreOffice profile holding the macro (made once per process directory)."""
    prof = os.path.join(base, 'lo-profile'); url = 'file://' + prof
    std = os.path.join(prof, 'user', 'basic', 'Standard')
    if not os.path.exists(os.path.join(std, 'Module1.xba')):
        subprocess.run([soffice(), f'-env:UserInstallation={url}', '--headless', '--terminate_after_init'], capture_output=True, timeout=timeout + 60)
        os.makedirs(std, exist_ok=True)
        open(os.path.join(std, 'Module1.xba'), 'w').write(MACRO); open(os.path.join(std, 'script.xlb'), 'w').write(XLB)
        if not os.path.exists(os.path.join(std, 'dialog.xlb')):
            open(os.path.join(std, 'dialog.xlb'), 'w').write('<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD OfficeDocument 1.0//EN" "library.dtd">\n'
                                                            '<library:library xmlns:library="http://openoffice.org/2000/library" library:name="Standard" library:readonly="false"/>')
    return url


def recalc(path, timeout=300):
    path = os.path.abspath(path); base = os.environ.get('FX_LO_HOME') or os.path.join(tempfile.gettempdir(), f'fx-lo-{os.getpid()}')
    url = profile(base, timeout); t0 = time.time()
    r = subprocess.run([soffice(), f'-env:UserInstallation={url}', '--headless', '--norestore',
                        'vnd.sun.star.script:Standard.Module1.Recalc?language=Basic&location=application', path],
                       capture_output=True, text=True, timeout=timeout + 30)
    try: wf = load_workbook(path); wv = load_workbook(path, data_only=True)
    except Exception as x: return {'error': f'could not read the recalculated file: {x}'}
    nform = 0; summ = {}
    for ws in wf.worksheets:
        vs = wv[ws.title]
        for row in ws.iter_rows():
            for c in row:
                if isinstance(c.value, str) and c.value.startswith('='):
                    nform += 1; v = vs[c.coordinate].value
                    if isinstance(v, str) and (v in ERRS or v.startswith('Err:')):
                        e = summ.setdefault(v, {'count': 0, 'locations': []}); e['count'] += 1
                        if len(e['locations']) < 50: e['locations'].append(f"'{ws.title}'!{c.coordinate}")
    n = sum(x['count'] for x in summ.values())
    return {'status': 'success' if not n else 'errors_found', 'total_formulas': nform, 'total_errors': n, 'error_summary': summ,
            'seconds': round(time.time() - t0, 1), **({'soffice_stderr': r.stderr[-300:]} if r.returncode else {})}


if __name__ == '__main__':
    print(json.dumps(recalc(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 300), ensure_ascii=False))
