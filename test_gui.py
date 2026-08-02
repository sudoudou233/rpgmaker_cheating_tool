# -*- coding: utf-8 -*-
"""Smoke test: build GUI, load game data + a save, apply an edit, save, verify."""
import os, sys, shutil
import tkinter as tk

import rpgdata
import main as appmod

GAME_DIR = r"D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3"

root = tk.Tk()
root.withdraw()
app = appmod.App(root)

app.game_dir_var.set(GAME_DIR)
app._load_game_data()
assert app.gd is not None
print('game data loaded:', len(app.gd.items), 'items,', len(app.gd.actors), 'actors')

# pick the biggest save
saves = sorted([f for f in os.listdir(GAME_DIR) if f.lower().startswith('save') and f.lower().endswith('.rvdata2')])
big = max(saves, key=lambda s: os.path.getsize(os.path.join(GAME_DIR, s)))
app.save_combo.set(big)
app._load_save()
assert app.sf is not None
print('save loaded:', big, 'gold=', app.gold_var.get())

# exercise edits via GUI handlers
app.gold_var.set('123456')
app._apply_party()
app.inv_id_var.set('1')
app.inv_count_var.set('5')
app._apply_inv('items', app.inv_tree_items)

# save to a temp file
tmp = os.path.join(os.environ['TEMP'], 'gui_test_save.rvdata2')
shutil.copy2(os.path.join(GAME_DIR, big), tmp)
app.current_save_path = tmp
app._save_save()

# verify
sf = rpgdata.SaveFile(tmp, app.gd)
p = sf.read_party()
print('saved gold=', p['gold'], 'items=', p.get('items'))
assert p['gold'] == 123456
assert p['items'].get(1) == 5
# round-trip check: the saved file must re-parse cleanly into both streams
import rmarshal
out = open(tmp, 'rb').read()
nodes = rmarshal.load_streams(out)
assert len(nodes) == 2, len(nodes)
print('OK - saved file re-parses into %d streams, edits verified' % len(nodes))
root.destroy()
