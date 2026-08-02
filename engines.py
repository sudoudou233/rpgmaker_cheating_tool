# -*- coding: utf-8 -*-
"""RPG Maker engine detection + save/data discovery for supported engines."""
import os
import re

ENGINES = {
    'mz': 'RPG Maker MZ',
    'mv': 'RPG Maker MV',
    'vxace': 'RPG Maker VX Ace',
    'vx': 'RPG Maker VX',
    'xp': 'RPG Maker XP',
    '2k3': 'RPG Maker 2000/2003',
}

SAVE_PATTERNS = {
    'vxace': (r'^Save\d+\.rvdata2$', 'Save*.rvdata2'),
    'vx': (r'^Save\d+\.rvdata$', 'Save*.rvdata'),
    'xp': (r'^Save\d+\.rxdata$', 'Save*.rxdata'),
    'mv': (r'^file\d+\.rpgsave$', 'file*.rpgsave'),
    'mz': (r'^file\d+\.rmmzsave$', 'file*.rmmzsave'),
}


def _find(root, names, maxdepth=2):
    """Find any of `names` under root (limited depth), return full path."""
    for dirpath, dirs, files in os.walk(root):
        depth = dirpath[len(root):].count(os.sep)
        if depth > maxdepth:
            dirs[:] = []
            continue
        for f in files:
            if f in names:
                return os.path.join(dirpath, f)
    return None


def detect_engine(game_dir):
    """Detect the RPG Maker engine of a game directory.

    Returns dict: {engine, label, data_dir, save_dir, ext, standard, layout}
    or None if nothing is recognized.
    """
    g = os.path.abspath(game_dir)
    if not os.path.isdir(g):
        return None

    def has_data(sub):
        return os.path.isdir(os.path.join(g, sub))

    # MV / MZ (NW.js games): www/ layout or bare js/ layout
    if has_data('www'):
        www = os.path.join(g, 'www')
        if os.path.exists(os.path.join(www, 'js', 'rmmz_core.js')):
            return _mvmz('mz', www)
        if os.path.exists(os.path.join(www, 'js', 'rpg_core.js')):
            return _mvmz('mv', www)
    if os.path.exists(os.path.join(g, 'js', 'rmmz_core.js')):
        return _mvmz('mz', g)
    if os.path.exists(os.path.join(g, 'js', 'rpg_core.js')):
        return _mvmz('mv', g)

    # RGSS games: Data/*.rvdata2 / .rvdata / .rxdata
    data_dir = os.path.join(g, 'Data')
    if os.path.isdir(data_dir):
        try:
            names = set(os.listdir(data_dir))
        except OSError:
            names = set()
        if any(n.endswith('.rvdata2') for n in names):
            return _rgss('vxace', g, data_dir, '.rvdata2', standard=False,
                         layout='hash')
        if any(n.endswith('.rvdata') for n in names):
            return _rgss('vx', g, data_dir, '.rvdata', standard=True,
                         layout='contents')
        if any(n.endswith('.rxdata') for n in names):
            return _rgss('xp', g, data_dir, '.rxdata', standard=True,
                         layout='contents')

    # 2k/2k3 (LCF)
    if _find(g, {'RPG_RT.ini', 'RPG_RT.exe'}, maxdepth=1) or \
            _find(g, {'RPG_RT.ini', 'RPG_RT.exe'}, maxdepth=2):
        return {'engine': '2k3', 'label': ENGINES['2k3'],
                'data_dir': g, 'save_dir': g, 'ext': '.lsd',
                'standard': None, 'layout': None, 'supported': False}
    return None


def _mvmz(engine, root):
    data_dir = os.path.join(root, 'data')
    save_dir = os.path.join(root, 'save')
    ext = '.rmmzsave' if engine == 'mz' else '.rpgsave'
    return {'engine': engine, 'label': ENGINES[engine],
            'data_dir': data_dir, 'save_dir': save_dir, 'ext': ext,
            'standard': False, 'layout': 'json', 'supported': True}


def _rgss(engine, g, data_dir, ext, standard, layout):
    return {'engine': engine, 'label': ENGINES[engine],
            'data_dir': data_dir, 'save_dir': g, 'ext': ext,
            'standard': standard, 'layout': layout, 'supported': True}


def list_saves(info, game_dir=None):
    """List save file names for an engine info dict."""
    if not info or not info.get('supported'):
        return []
    save_dir = info['save_dir'] or game_dir
    if not os.path.isdir(save_dir):
        return []
    pat, _ = SAVE_PATTERNS.get(info['engine'], (None, None))
    if not pat:
        return []
    rx = re.compile(pat)
    return sorted(f for f in os.listdir(save_dir) if rx.match(f))


def make_game_data(info):
    """Build the GameData object for an engine."""
    from rpgdata import GameData
    from mvdata import GameDataMV
    if info['engine'] in ('mv', 'mz'):
        return GameDataMV(info['data_dir'])
    if info['engine'] in ('xp', 'vx', 'vxace'):
        return GameData(info['data_dir'], standard=bool(info['standard']))
    return None


def make_save_file(info, path, gamedata=None):
    """Build the SaveFile object for an engine."""
    from rpgdata import SaveFile
    from mvdata import SaveFileMV
    if info['engine'] in ('mv', 'mz'):
        return SaveFileMV(path, gamedata, engine=info['engine'])
    if info['engine'] in ('xp', 'vx', 'vxace'):
        return SaveFile(path, gamedata, standard=bool(info['standard']),
                        layout=info['layout'])
    return None
