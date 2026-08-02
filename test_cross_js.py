# -*- coding: utf-8 -*-
"""Cross-validate edited saves against the game's own JS decoder (node)."""
import os
import shutil
import subprocess
import tempfile

import engines

JS = r'C:\Users\tudou\AppData\Local\Temp\opencode\verify_save.js'
NODE = r'C:\Users\tudou\AppData\Local\pnpm\node.exe'

MV = r'D:\gamess\zhoukai\诅咒铠甲2\PC\PC-1\V5.9'
base = r'D:\gamess'
mz = [x for x in os.listdir(base) if 'Kimochi' in x][0]
MZ = os.path.join(base, mz, mz)

for root, kind in [(MV, 'mv'), (MZ, 'mz')]:
    info = engines.detect_engine(root)
    gd = engines.make_game_data(info)
    saves = engines.list_saves(info, root)
    src = os.path.join(info['save_dir'], saves[0])
    tmp = os.path.join(tempfile.gettempdir(),
                       'verify_edited' + info['ext'])
    shutil.copy2(src, tmp)
    sf = engines.make_save_file(info, tmp, gd)
    sf.set_gold(987654)
    sf.set_item(1, 55)
    sf.set_actor_attr(1, 'level', 66)
    sf.set_actor_attr(1, 'hp', 4321)
    sf.save(tmp)
    r = subprocess.run([NODE, JS, kind, tmp], capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    print(kind.upper(), 'node output:', r.stdout.strip() or r.stderr.strip())
    os.remove(tmp)
