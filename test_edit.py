# -*- coding: utf-8 -*-
import shutil, os
import rpgdata

SRC = r'D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3\Save07.rvdata2'
GD = r'D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3\Data'

gd = rpgdata.GameData(GD)
print('items:', {k: gd.items[k] for k in sorted(gd.items)[:5]})
print('weapons:', {k: gd.weapons[k] for k in sorted(gd.weapons)[:5]})
print('actors:', gd.actors)

sf = rpgdata.SaveFile(SRC, gd)
p = sf.read_party()
print('gold=', p['gold'], 'steps=', p['steps'], 'items=', p['items'],
      'weapons=', p['weapons'], 'armors=', p['armors'])

# also check second stream
p1 = sf.read_party(1)
print('stream1 gold=', p1['gold'], 'items=', p1['items'])

actors = sf.read_actors()
for i, a in enumerate(actors):
    if a:
        name = gd.actors.get(a['actor_id'], {}).get('name', '?')
        print('actor[%d] id=%d %r lv=%d exp=%d hp=%d mp=%d params=%s skills=%s'
              % (i, a['actor_id'], name, a['level'], a['exp'], a['hp'], a['mp'],
                 a['param_plus'], a['skills']))

# ---- edit
sf.set_gold(999999)
sf.set_item(13, 99)      # update existing (13 -> 21)
sf.set_item(16, 0)       # remove item 16
sf.set_item(500, 3)      # add new item 500
sf.set_actor_attr(1, 'level', 50)
sf.set_actor_attr(1, 'exp', 99999)
sf.set_actor_attr(1, 'hp', 9999)
sf.set_actor_attr(1, 'param_plus_0', 100)

tmp = os.path.join(os.environ.get('TEMP', '.'), 'save_test.rvdata2')
sf.save(tmp)
print('\nsaved to', tmp, 'size', os.path.getsize(tmp))

# re-read and verify
sf2 = rpgdata.SaveFile(tmp, gd)
p = sf2.read_party()
print('new gold=', p['gold'], 'items=', p['items'])
actors = sf2.read_actors()
a1 = actors[1]
print('actor1 lv=%d exp=%d hp=%d param_plus=%s' % (
    a1['level'], a1['exp'], a1['hp'], a1['param_plus']))

# round-trip check: parse original again, ensure unmodified parts unchanged
import rmarshal
data = open(SRC, 'rb').read()
out = open(tmp, 'rb').read()
# find first diff
n = min(len(data), len(out))
d = None
for i in range(n):
    if data[i] != out[i]:
        d = i
        break
print('first diff vs original at byte', d, '(orig %d new %d)' % (len(data), len(out)))
