import json, sys
from pathlib import Path
P = Path(__file__).parent
r = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
M, need = r['models'], ['SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài', 'SVR log-mel bỏ độ dài',
    'SVR log-mel + trọng số', 'LR phân loại cân bằng', 'RF phân loại cân bằng', 'SVR wav2vec 2.0',
    'SVR wav2vec + độ dài', 'LR phân loại cân bằng (wav2vec)', 'Ngẫu nhiên / hằng số']
assert all(k in M for k in need), set(need) - set(M)
assert set(r['cv_table']) == set(need) - {'Ngẫu nhiên / hằng số'}, 'cv_table thiếu mô hình'
for k, v in r['cv_table'].items():
    assert len(v['recall20']) == 2 and 0.5 < v['recall20'][0] < 1.0, k
h = r['halves']
assert abs(h['fast']['n'] + h['slow']['n'] - 2500) <= 1
assert h['fast']['n_below6'] + h['slow']['n_below6'] == 330
assert h['threshold_sec_per_word'] > 0
for side in ('fast', 'slow'):
    for m in ('length', 'w2v'):
        assert 0 <= h[side]['recall20'][m] <= 1, (side, m)
lt = r['low_total']
assert lt['n'] == 12 and set(lt['pred_mean']) == {'SVR log-mel', 'SVR chỉ độ dài', 'SVR wav2vec 2.0'}
assert r['target_check']['floor_median'] == 5000 and r['below6']['test'] == [330, 2500]
assert len(r['worst5']) == 5 and all(w['total'] < 6 for w in r['worst5'])
# worst5 phải trùng khớp tuần 10 (nhóm đang nghe đúng 5 câu cũ)
w10 = json.loads((P.parent / 'week10_work' / 'week10_results.json').read_text(encoding='utf-8'))
assert [w['id'] for w in r['worst5']] == [w['id'] for w in w10['worst5']], 'worst5 lệch tuần 10 — DỪNG, báo người dùng'
print('verify_week11 OK')
