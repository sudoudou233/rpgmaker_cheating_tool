# -*- coding: utf-8 -*-
import os, sys, glob
import rmarshal

def roundtrip_one(data):
    nodes = rmarshal.load_streams(data)
    out = b''
    for off, node in nodes:
        out += rmarshal.dumps(node)
    return out == data, len(data), len(out)

ok = fail = 0
for root in [
    r"D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3\Data",
    r"D:\gamess\踏勇\践踏勇者\整合\整合-1\1.12.3",
    r"D:\gamess\JIANTATA\1-6\PC-1\ToT 1.16.2.2 CN1.0\Data",
]:
    for path in glob.glob(os.path.join(root, '*.rvdata2')):
        with open(path, 'rb') as f:
            data = f.read()
        try:
            same, a, b = roundtrip_one(data)
        except Exception as e:
            print('ERROR  %s : %r' % (os.path.basename(path), e))
            fail += 1
            continue
        if same:
            ok += 1
        else:
            print('MISMATCH %s (orig %d, new %d)' % (os.path.basename(path), a, b))
            fail += 1
print('\n%d ok, %d failed' % (ok, fail))
