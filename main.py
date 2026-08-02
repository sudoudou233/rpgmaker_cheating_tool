# -*- coding: utf-8 -*-
"""RPG Maker 存档修改器 (multi-engine: MV / MZ / VX Ace / VX / XP)

GUI (tkinter) editor that:
  - auto-detects the RPG Maker engine of a game directory
  - reads the game's data tables (items / weapons / armors / actors / classes)
  - reads a save file (gold, inventory, character attributes, variables/switches)
  - lets you modify quantities & attributes in real time and save back.
"""
import os
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import engines

GAME_DIR = r"D:\gamess\zhoukai\诅咒铠甲2\PC\PC-1\V5.9"
APP_TITLE = 'RPG Maker 存档修改器'


class App:
    def __init__(self, root):
        self.root = root
        self.gd = None
        self.sf = None
        self.current_save_path = None
        self.engine_info = None
        root.title(APP_TITLE)
        root.geometry('1080x700')

        self._build_top()
        self._build_notebook()
        self._status('未加载。请选择游戏目录并读取游戏数据。')
        if os.path.isdir(GAME_DIR):
            self.root.after(50, self._load_game_data)

    # ------------------------------------------------------------- top bar
    def _build_top(self):
        bar = ttk.Frame(self.root, padding=(8, 6))
        bar.pack(fill='x')
        ttk.Label(bar, text='游戏目录:').pack(side='left')
        self.game_dir_var = tk.StringVar(value=GAME_DIR)
        e = ttk.Entry(bar, textvariable=self.game_dir_var, width=46)
        e.pack(side='left', padx=(4, 0))
        ttk.Button(bar, text='浏览', command=self._browse_game_dir).pack(side='left', padx=2)
        ttk.Button(bar, text='读取游戏数据', command=self._load_game_data).pack(side='left', padx=2)

        ttk.Label(bar, text='  存档:').pack(side='left')
        self.save_combo = ttk.Combobox(bar, state='readonly', width=30)
        self.save_combo.pack(side='left', padx=(4, 0))
        self.save_combo.bind('<<ComboboxSelected>>', lambda e: self._load_save())
        ttk.Button(bar, text='浏览存档', command=self._browse_save).pack(side='left', padx=2)
        ttk.Button(bar, text='加载', command=self._load_save).pack(side='left', padx=2)
        ttk.Button(bar, text='保存存档', command=self._save_save).pack(side='left', padx=(12, 2))

    # ------------------------------------------------------------- notebook
    def _build_notebook(self):
        self.nb = ttk.Notebook(self.root)
        self.nb.pack(fill='both', expand=True, padx=8, pady=4)
        self._build_party_tab()
        self._build_inv_tab('道具', '@items', 'items')
        self._build_inv_tab('武器', '@weapons', 'weapons')
        self._build_inv_tab('防具', '@armors', 'armors')
        self._build_actors_tab()
        self._build_var_tab('开关', 'switches')
        self._build_var_tab('变量', 'variables')

    # ------------------------------------------------------------- party tab
    def _build_party_tab(self):
        f = ttk.Frame(self.nb, padding=8)
        self.nb.add(f, text='队伍/金币')
        ttk.Label(f, text='金币:').grid(row=0, column=0, sticky='e', pady=3)
        self.gold_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.gold_var, width=16).grid(row=0, column=1, sticky='w')
        ttk.Label(f, text='步数:').grid(row=1, column=0, sticky='e', pady=3)
        self.steps_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.steps_var, width=16).grid(row=1, column=1, sticky='w')
        ttk.Button(f, text='应用金币/步数', command=self._apply_party).grid(row=2, column=1, sticky='w', pady=6)

        ttk.Label(f, text='队伍成员 (actor_id):').grid(row=3, column=0, sticky='e')
        self.party_ids_var = tk.StringVar()
        ttk.Entry(f, textvariable=self.party_ids_var, width=30).grid(row=3, column=1, sticky='w')

        self.party_info = tk.Text(f, height=12, width=90)
        self.party_info.grid(row=4, column=0, columnspan=2, sticky='nsew', pady=6)
        f.columnconfigure(1, weight=1)
        f.rowconfigure(4, weight=1)

    # ------------------------------------------------------------- inventory
    def _build_inv_tab(self, title, ivar_key, kind):
        f = ttk.Frame(self.nb, padding=8)
        self.nb.add(f, text=title)

        cols = ('id', 'name', 'count')
        tree = ttk.Treeview(f, columns=cols, show='headings', height=18)
        tree.heading('id', text='ID')
        tree.heading('name', text='名称')
        tree.heading('count', text='数量')
        tree.column('id', width=60, anchor='center')
        tree.column('name', width=320)
        tree.column('count', width=90, anchor='center')
        tree.pack(fill='both', expand=True)

        bar = ttk.Frame(f, padding=(0, 6))
        bar.pack(fill='x')
        ttk.Label(bar, text='ID:').pack(side='left')
        self.inv_id_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.inv_id_var, width=8).pack(side='left', padx=(2, 6))
        ttk.Label(bar, text='数量:').pack(side='left')
        self.inv_count_var = tk.StringVar()
        ttk.Entry(bar, textvariable=self.inv_count_var, width=8).pack(side='left', padx=(2, 6))
        ttk.Button(bar, text='设置数量', command=lambda: self._apply_inv(kind, tree)).pack(side='left', padx=4)
        ttk.Button(bar, text='选中行应用', command=lambda: self._fill_from_selection(kind, tree)).pack(side='left', padx=4)
        ttk.Button(bar, text='数量+1', command=lambda: self._incr_inv(kind, tree, 1)).pack(side='left', padx=4)
        ttk.Button(bar, text='数量+10', command=lambda: self._incr_inv(kind, tree, 10)).pack(side='left', padx=4)
        ttk.Button(bar, text='清零', command=lambda: self._clear_inv(kind)).pack(side='left', padx=4)
        setattr(self, 'inv_tree_' + kind, tree)

    # ------------------------------------------------------------- actors tab
    def _build_actors_tab(self):
        f = ttk.Frame(self.nb, padding=8)
        self.nb.add(f, text='角色')
        cols = ('actor', 'name', 'class', 'level', 'exp', 'hp', 'mp')
        tree = ttk.Treeview(f, columns=cols, show='headings', height=14)
        for c, w, anc in [('actor', 60, 'center'), ('name', 160, 'w'),
                          ('class', 100, 'w'), ('level', 60, 'center'),
                          ('exp', 90, 'center'), ('hp', 80, 'center'), ('mp', 80, 'center')]:
            tree.heading(c, text=c if c != 'actor' else 'ID')
            tree.column(c, width=w, anchor=anc)
        tree.pack(fill='both', expand=True)
        tree.bind('<<TreeviewSelect>>', self._on_actor_select)
        self.actor_tree = tree

        ed = ttk.LabelFrame(f, text='编辑属性', padding=6)
        ed.pack(fill='x', pady=4)
        ed.columnconfigure(1, weight=1)
        ed.columnconfigure(3, weight=1)
        self.actor_id_var = tk.StringVar()
        self.actor_fields = {}
        labels = [('level', '等级'), ('exp', '经验'), ('hp', 'HP'),
                  ('mp', 'MP'), ('tp', 'TP')]
        for i, (key, label) in enumerate(labels):
            r, c = divmod(i, 2)
            ttk.Label(ed, text=label).grid(row=r, column=c * 2, sticky='e', padx=(8, 2), pady=2)
            var = tk.StringVar()
            ttk.Entry(ed, textvariable=var, width=14).grid(row=r, column=c * 2 + 1, sticky='w')
            self.actor_fields[key] = var
        r = (len(labels) + 1) // 2
        ttk.Label(ed, text='属性+').grid(row=r, column=0, sticky='e', padx=(8, 2), pady=2)
        self.actor_param_var = tk.StringVar()
        self.actor_param_var.set('0')
        ttk.Entry(ed, textvariable=self.actor_param_var, width=6).grid(row=r, column=1, sticky='w')
        self.actor_param_idx_var = tk.StringVar()
        self.actor_param_idx_var.set('0')
        ttk.Label(ed, text='索引(0-7)').grid(row=r, column=2, sticky='e', padx=(8, 2))
        ttk.Entry(ed, textvariable=self.actor_param_idx_var, width=5).grid(row=r, column=3, sticky='w')
        ttk.Button(ed, text='应用', command=self._apply_actor).grid(
            row=r + 1, column=1, sticky='w', pady=4)
        self.actor_skills_var = tk.StringVar()
        ttk.Label(ed, text='技能ID(逗号分隔)').grid(row=r + 2, column=0, sticky='e', padx=(8, 2))
        ttk.Entry(ed, textvariable=self.actor_skills_var, width=40).grid(row=r + 2, column=1, columnspan=3, sticky='w')
        ttk.Button(ed, text='应用技能', command=self._apply_actor_skills).grid(
            row=r + 3, column=1, sticky='w', pady=4)

    # ------------------------------------------------------------- var tab
    def _build_var_tab(self, title, key):
        f = ttk.Frame(self.nb, padding=8)
        self.nb.add(f, text=title)
        cols = ('id', 'val')
        tree = ttk.Treeview(f, columns=cols, show='headings', height=20)
        tree.heading('id', text='ID')
        tree.heading('val', text='值')
        tree.column('id', width=70, anchor='center')
        tree.column('val', width=220)
        tree.pack(fill='both', expand=True)
        bar = ttk.Frame(f, padding=(0, 6))
        bar.pack(fill='x')
        ttk.Label(bar, text='ID:').pack(side='left')
        vid = tk.StringVar()
        ttk.Entry(bar, textvariable=vid, width=8).pack(side='left', padx=(2, 6))
        ttk.Label(bar, text='值:').pack(side='left')
        vval = tk.StringVar()
        ttk.Entry(bar, textvariable=vval, width=14).pack(side='left', padx=(2, 6))
        ttk.Button(bar, text='设置', command=lambda: self._apply_var(key, tree, vid, vval)).pack(side='left', padx=4)
        setattr(self, 'var_tree_' + key, tree)
        setattr(self, 'var_id_' + key, vid)
        setattr(self, 'var_val_' + key, vval)

    # ------------------------------------------------------------- actions
    def _status(self, msg):
        if not hasattr(self, '_status_label'):
            self._status_label = ttk.Label(self.root, text='', relief='sunken',
                                           anchor='w', padding=(6, 2))
            self._status_label.pack(side='bottom', fill='x')
        self._status_label.config(text=msg)

    def _browse_game_dir(self):
        d = filedialog.askdirectory(initialdir=self.game_dir_var.get())
        if d:
            self.game_dir_var.set(d)
            self._load_game_data()

    def _load_game_data(self):
        d = self.game_dir_var.get().strip()
        info = engines.detect_engine(d)
        if info is None:
            self._status('无法识别该目录的 RPG Maker 引擎: %s' % d)
            return
        if not info.get('supported'):
            self._status('检测到 %s，但该引擎存档格式暂不支持' % info['label'])
            return
        self.engine_info = info
        try:
            self.gd = engines.make_game_data(info)
        except Exception as e:
            messagebox.showerror('错误', '读取游戏数据失败:\n%r' % e)
            return
        saves = engines.list_saves(info, d)
        if saves:
            self.save_combo['values'] = saves
            self.save_combo.current(0)
            self._status('引擎: %s | 已读取: %d 道具, %d 武器, %d 防具, %d 角色'
                         % (info['label'], len(self.gd.items), len(self.gd.weapons),
                            len(self.gd.armors), len(self.gd.actors)))
            self._load_save()
        else:
            self.save_combo['values'] = []
            self._status('引擎: %s | 游戏数据已读取 (%d 道具)。当前没有存档文件——'
                         '请先在游戏中新开并保存一次，存档出现后再来修改。'
                         % (info['label'], len(self.gd.items)))

    def _browse_save(self):
        info = self.engine_info
        ext = info['ext'] if info else '*.rvdata2'
        p = filedialog.askopenfilename(
            initialdir=self.game_dir_var.get(),
            filetypes=[('RPG Maker 存档', '*%s' % ext), ('所有文件', '*.*')])
        if p:
            self.current_save_path = p
            self._load_save_path(p)

    def _load_save(self):
        if not self.gd:
            self._status('请先读取游戏数据')
            return
        name = self.save_combo.get()
        if not name:
            return
        save_dir = self.engine_info['save_dir'] or self.game_dir_var.get().strip()
        p = os.path.join(save_dir, name)
        self.current_save_path = p
        self._load_save_path(p)

    def _load_save_path(self, path):
        if not self.gd or not self.engine_info:
            self._status('请先读取游戏数据')
            return
        try:
            self.sf = engines.make_save_file(self.engine_info, path, self.gd)
        except Exception as e:
            messagebox.showerror('错误', '读取存档失败:\n%r' % e)
            return
        self._refresh_all()
        self._status('已加载: %s' % path)

    def _refresh_all(self):
        self._refresh_party()
        self._refresh_inv('items')
        self._refresh_inv('weapons')
        self._refresh_inv('armors')
        self._refresh_actors()
        self._refresh_var('switches')
        self._refresh_var('variables')

    def _refresh_party(self):
        p = self.sf.read_party(0)
        self.gold_var.set(str(p.get('gold', 0)))
        self.steps_var.set(str(p.get('steps', 0)))
        self.party_ids_var.set(','.join(str(x) for x in p.get('party_ids', [])))
        info = []
        info.append('金币: %s    步数: %s    队伍成员ID: %s' % (p.get('gold'), p.get('steps'), p.get('party_ids')))
        info.append('道具: %s' % self._fmt_hash(p.get('items')))
        info.append('武器: %s' % self._fmt_hash(p.get('weapons')))
        info.append('防具: %s' % self._fmt_hash(p.get('armors')))
        self.party_info.delete('1.0', 'end')
        self.party_info.insert('1.0', '\n'.join(info))

    def _fmt_hash(self, h):
        if not h:
            return '(空)'
        return ', '.join('%d:%d' % (k, v) for k, v in sorted(h.items()))

    def _refresh_inv(self, kind):
        tree = getattr(self, 'inv_tree_' + kind)
        for it in tree.get_children():
            tree.delete(it)
        if not self.sf:
            return
        counts = self.sf.read_party(0).get(kind, {})
        table = self.gd.items if kind == 'items' else (
            self.gd.weapons if kind == 'weapons' else self.gd.armors)
        for oid in sorted(table):
            name = table[oid]
            tree.insert('', 'end', values=(oid, name, counts.get(oid, 0)))

    def _apply_party(self):
        if not self.sf:
            return
        try:
            self.sf.set_gold(int(self.gold_var.get()))
            self.sf.set_steps(int(self.steps_var.get()))
        except ValueError:
            messagebox.showerror('错误', '金币/步数必须是整数')
            return
        self._refresh_party()
        self._status('金币/步数已修改 (尚未保存)')

    def _get_inv_id(self):
        try:
            return int(self.inv_id_var.get())
        except ValueError:
            messagebox.showerror('错误', 'ID 必须是整数')
            return None

    def _apply_inv(self, kind, tree):
        if not self.sf:
            return
        oid = self._get_inv_id()
        if oid is None:
            return
        try:
            count = int(self.inv_count_var.get())
        except ValueError:
            messagebox.showerror('错误', '数量必须是整数')
            return
        self.sf.set_item(oid, count, kind)
        self._refresh_inv(kind)
        self._status('%s %d 数量 -> %d (尚未保存)' % (kind, oid, count))

    def _fill_from_selection(self, kind, tree):
        sel = tree.selection()
        if sel:
            vals = tree.item(sel[0], 'values')
            self.inv_id_var.set(vals[0])

    def _incr_inv(self, kind, tree, delta):
        if not self.sf:
            return
        oid = self._get_inv_id()
        if oid is None:
            return
        cur = self.sf.read_party(0).get(kind, {}).get(oid, 0)
        self.sf.set_item(oid, cur + delta, kind)
        self._refresh_inv(kind)
        self._status('%s %d -> %d' % (kind, oid, cur + delta))

    def _clear_inv(self, kind):
        if not self.sf:
            return
        table = self.gd.items if kind == 'items' else (
            self.gd.weapons if kind == 'weapons' else self.gd.armors)
        for oid in table:
            self.sf.set_item(oid, 0, kind)
        self._refresh_inv(kind)
        self._status('%s 已全部清零' % kind)

    def _refresh_actors(self):
        tree = self.actor_tree
        for it in tree.get_children():
            tree.delete(it)
        if not self.sf:
            return
        actors = self.sf.read_actors(0)
        for i, a in enumerate(actors):
            if not a:
                continue
            aid = a['actor_id']
            name = (self.gd.actors.get(aid, {}).get('name', '') or '角色%d' % aid)
            cls = self.gd.classes.get(a['class_id'], '职业%d' % a['class_id'])
            tree.insert('', 'end', iid=str(aid), values=(
                aid, name, cls, a['level'], a['exp'], a['hp'], a['mp']))

    def _on_actor_select(self, event):
        sel = self.actor_tree.selection()
        if not sel:
            return
        aid = int(sel[0])
        self.actor_id_var.set(str(aid))
        actors = self.sf.read_actors(0)
        if aid < len(actors) and actors[aid]:
            a = actors[aid]
            self.actor_fields['level'].set(str(a['level']))
            self.actor_fields['exp'].set(str(a['exp']))
            self.actor_fields['hp'].set(str(a['hp']))
            self.actor_fields['mp'].set(str(a['mp']))
            self.actor_fields['tp'].set(str(a.get('tp', 0)))
            self.actor_skills_var.set(','.join(str(x) for x in a['skills']))

    def _apply_actor(self):
        if not self.sf:
            return
        try:
            aid = int(self.actor_id_var.get())
        except ValueError:
            messagebox.showerror('错误', '角色ID必须是整数')
            return
        for key, var in self.actor_fields.items():
            try:
                v = int(var.get())
            except ValueError:
                messagebox.showerror('错误', '%s 必须是整数' % key)
                return
            self.sf.set_actor_attr(aid, key, v)
        try:
            idx = int(self.actor_param_idx_var.get())
            pv = int(self.actor_param_var.get())
        except ValueError:
            messagebox.showerror('错误', '属性索引/值必须是整数')
            return
        self.sf.set_actor_attr(aid, 'param_plus_%d' % idx, pv)
        self._refresh_actors()
        self._status('角色 %d 属性已修改 (尚未保存)' % aid)

    def _apply_actor_skills(self):
        if not self.sf:
            return
        try:
            aid = int(self.actor_id_var.get())
        except ValueError:
            messagebox.showerror('错误', '角色ID必须是整数')
            return
        try:
            skills = [int(x.strip()) for x in self.actor_skills_var.get().split(',') if x.strip()]
        except ValueError:
            messagebox.showerror('错误', '技能ID必须是整数，逗号分隔')
            return
        self.sf.set_actor_skills(aid, skills)
        self._refresh_actors()
        self._status('角色 %d 技能已修改 (尚未保存)' % aid)

    def _refresh_var(self, key):
        tree = getattr(self, 'var_tree_' + key)
        for it in tree.get_children():
            tree.delete(it)
        if not self.sf:
            return
        data = self.sf.read_var(key)
        for i, v in enumerate(data):
            if i == 0:
                continue
            tree.insert('', 'end', values=(i, v))

    def _apply_var(self, key, tree, vid, vval):
        if not self.sf:
            return
        try:
            i = int(vid.get())
            v = int(vval.get())
        except ValueError:
            messagebox.showerror('错误', 'ID/值必须是整数')
            return
        self.sf.set_var(key, i, v)
        self._refresh_var(key)
        self._status('%s[%d] -> %d (尚未保存)' % (key, i, v))

    def _save_save(self):
        if not self.sf:
            return
        path = self.current_save_path or filedialog.asksaveasfilename(
            defaultextension='.rvdata2', filetypes=[('存档', '*.rvdata2')])
        if not path:
            return
        bak = path + '.bak'
        try:
            shutil.copy2(path, bak)
        except OSError:
            pass
        try:
            self.sf.save(path)
        except Exception as e:
            messagebox.showerror('错误', '保存失败:\n%r' % e)
            return
        self._status('已保存: %s (备份: %s)' % (path, bak))


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == '__main__':
    main()
