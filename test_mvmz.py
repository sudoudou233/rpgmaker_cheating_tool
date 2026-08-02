# -*- coding: utf-8 -*-
import os
import json
import shutil
import tempfile
import zlib
import lzstring

import engines
from mvdata import GameDataMV, SaveFileMV

MV = r'D:\gamess\zhoukai\诅咒铠甲2\PC\PC-1\V5.9'
MZ_ROOT = None
import os as _os
base = r'D:\gamess'
for d in _os.listdir(base):
    if 'Kimochi' in d:
        MZ_ROOT = _os.path.join(base, d, d)
        break

for root, engine_name in [(MV, 'mv'), (MZ_ROOT, 'mz')]:
    print('=' * 40, engine_name)
    info = engines.detect_engine(root)
    print('detected:', info['label'] if info else None, info['engine'] if info else '')
    gd = engines.make_game_data(info)
    print('items:', len(gd.items), 'weapons:', len(gd.weapons),
          'armors:', len(gd.armors), 'actors:', len(gd.actors),
          'title:', gd.title[:20])
    saves = engines.list_saves(info, root)
    print('saves:', saves[:6], '... total', len(saves))
    if not saves:
        continue
    path = os.path.join(info['save_dir'] or root, saves[0])
    sf = engines.make_save_file(info, path, gd)
    p = sf.read_party()
    print('gold=%s steps=%s items=%s' % (p['gold'], p['steps'], p.get('items')))
    actors = sf.read_actors()
    n = 0
    for a in actors:
        if a:
            n += 1
            if n <= 2:
                print('actor id=%s lv=%s hp=%s mp=%s exp=%s skills=%s params=%s' % (
                    a['actor_id'], a['level'], a['hp'], a['mp'], a['exp'],
                    a['skills'], a['param_plus']))
    print('actors present:', n)

    # ---- edit
    tmp = os.path.join(tempfile.gettempdir(), 'mvtest' + ('.rmmzsave' if engine_name == 'mz' else '.rpgsave'))
    shutil.copy2(path, tmp)
    sf2 = engines.make_save_file(info, tmp, gd)
    sf2.set_gold(123456)
    sf2.set_item(1, 99)
    sf2.set_item(9999, 7)
    sf2.set_actor_attr(1, 'level', 88)
    sf2.set_actor_attr(1, 'hp', 7777)
    sf2.set_actor_attr(1, 'param_plus_0', 300)
    sf2.set_var('variables', 5, 555)
    sf2.save(tmp)

    # re-read
    sf3 = engines.make_save_file(info, tmp, gd)
    p3 = sf3.read_party()
    a3 = sf3.read_actors()
    print('after edit: gold=%s items=%s' % (p3['gold'], p3['items']))
    print('actor1 lv=%s hp=%s params=%s vars5=%s' % (
        a3[1]['level'], a3[1]['hp'], a3[1]['param_plus'],
        sf3.read_var('variables')[5] if len(sf3.read_var('variables')) > 5 else 'NA'))
    assert p3['gold'] == 123456
    assert p3['items'].get(1) == 99 and p3['items'].get(9999) == 7
    assert a3[1]['level'] == 88 and a3[1]['hp'] == 7777
    assert a3[1]['param_plus'][0] == 300
    assert sf3.read_var('variables')[5] == 555
    os.remove(tmp)
    print('MV/MZ edit test OK')
