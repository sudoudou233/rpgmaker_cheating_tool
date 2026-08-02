# -*- coding: utf-8 -*-
"""GUI smoke test across engines: MV game + VX Ace game."""
import os
import shutil
import tempfile
import tkinter as tk

import engines
import main as appmod

MV = r'D:\gamess\zhoukai\诅咒铠甲2\PC\PC-1\V5.9'
VXA = r'D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3'

for gdir in [MV, VXA]:
    print('=' * 40, gdir)
    root = tk.Tk()
    root.withdraw()
    app = appmod.App(root)
    app.game_dir_var.set(gdir)
    app._load_game_data()
    assert app.gd is not None, 'game data failed'
    assert app.engine_info, 'engine detect failed'
    print('engine:', app.engine_info['label'])
    saves = app.save_combo['values']
    print('saves listed:', len(saves), saves[:4])
    if not saves:
        root.destroy()
        continue
    app.save_combo.current(len(saves) - 1)
    app._load_save()
    assert app.sf is not None
    print('gold field:', app.gold_var.get())
    print('item rows:', len(app.inv_tree_items.get_children()),
          'actor rows:', len(app.actor_tree.get_children()))

    # edit via handlers and save to temp
    app.gold_var.set('888888')
    app._apply_party()
    app.inv_id_var.set('1')
    app.inv_count_var.set('33')
    app._apply_inv('items', app.inv_tree_items)
    tmp = os.path.join(tempfile.gettempdir(),
                       'gui_verify' + app.engine_info['ext'])
    shutil.copy2(app.current_save_path, tmp)
    app.current_save_path = tmp
    app._save_save()
    sf2 = engines.make_save_file(app.engine_info, tmp, app.gd)
    p2 = sf2.read_party()
    print('saved gold=%s item1=%s' % (p2['gold'], p2.get('items', {}).get(1)))
    assert p2['gold'] == 888888
    assert p2.get('items', {}).get(1) == 33
    os.remove(tmp)
    root.destroy()
print('GUI multi-engine smoke test OK')
