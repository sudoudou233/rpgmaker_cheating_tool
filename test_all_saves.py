# -*- coding: utf-8 -*-
import os
import rmarshal
import rpgdata

GAME = r'D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3'
DATA = os.path.join(GAME, 'Data')
gd = rpgdata.GameData(DATA)

saves = sorted(f for f in os.listdir(GAME)
               if f.lower().startswith('save') and f.lower().endswith('.rvdata2'))
print('validating %d saves...' % len(saves))
fails = 0
for s in saves:
    path = os.path.join(GAME, s)
    try:
        sf = rpgdata.SaveFile(path, gd)
        p = sf.read_party(0)
        p1 = sf.read_party(1)
        actors = sf.read_actors(0)
        switches = sf.read_var('switches', 0)
        variables = sf.read_var('variables', 0)
        # apply an edit to both streams, then save to temp and re-parse
        sf.set_gold(p['gold'] + 1)
        sf.save(path + '.tmpcheck')
        sf2 = rpgdata.SaveFile(path + '.tmpcheck', gd)
        assert sf2.read_party(0)['gold'] == p['gold'] + 1
        assert sf2.read_party(1)['gold'] == p['gold'] + 1
        os.remove(path + '.tmpcheck')
        print('  OK %-12s gold=%7s items=%2d actors=%d sw=%d vars=%d' % (
            s, p['gold'], len(p['items']), sum(1 for a in actors if a),
            len(switches), len(variables)))
    except Exception as e:
        fails += 1
        print('  FAIL %s: %r' % (s, e))
print('\nfailures:', fails)
