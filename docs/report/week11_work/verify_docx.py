import json, sys
from pathlib import Path
from docx import Document

P = Path(__file__).parent
docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'report_before_embed.docx'
R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
C = json.loads((P / 'week11_completeness.json').read_text(encoding='utf-8'))
D = Document(str(docx_path))
pct = lambda v: f'{v*100:.0f}%'
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')

paras = [p.text for p in D.paragraphs]
text = '\n'.join(paras)
all_text = [text]
for t in D.tables:
    for row in t.rows:
        for c in row.cells:
            all_text.append(c.text)
full = '\n'.join(all_text)

# 1) Cấu trúc chung
import zipfile as _zf
_has_ole = any('/embeddings/' in n for n in _zf.ZipFile(str(docx_path)).namelist())
assert ('[[OBJECTS]]' in full) != _has_ole, \
    ('[[OBJECTS]] phải có khi chưa nhúng, phải biến mất khi đã nhúng OLE', _has_ole)
assert 'Group05_Week11_Report' in full, 'thiếu tên file Week11'
assert 'Week09' not in full, 'còn nhãn Week09 trong báo cáo'
assert 'Ghi chu thu' not in full, 'còn chữ giả của ghi chú nghe trong báo cáo'
titles = [p.text for p in D.paragraphs if 'Báo cáo tiến độ' in p.text]
assert titles and 'Tuần 11' in titles[0], f'tiêu đề không đúng Tuần 11: {titles}'
assert 'completeness' in text.lower(), 'thiếu phần completeness'
assert 'Kết quả chính tuần này' in full, 'thiếu khung kết quả chính'

# 2) Con số neo phải khớp JSON
w = R['models']['SVR wav2vec 2.0']['test']['recall20']
assert pct(w) in full, f'thiếu recall@20 test wav2vec {pct(w)}'
cvl = R['cv_table']['SVR chỉ độ dài']['recall20'][0]
assert pct(cvl) in full, f'thiếu recall@20 CV chỉ-độ-dài {pct(cvl)}'
assert f"{R['low_total']['n']} câu" in full, 'thiếu số câu nhóm total <= 2'
thr = vn(R['halves']['threshold_sec_per_word'], 2)
assert thr in full, f'thiếu ngưỡng trung vị giây/từ {thr}'
CZ = C['compl_zero']
num = lambda n: f'{n:,}'.replace(',', '.')
assert f"{CZ['n']}/{num(CZ['n_test'])}" in full, 'thiếu nhóm completeness = 0'
assert vn(CZ['mean_pred_logmel'], 2) in full and vn(CZ['mean_pred_w2v'], 2) in full, 'thiếu mean pred nhóm compl 0'

# 3) Bảng 12 câu total <= 2 — đủ 12 dòng, khớp JSON (cột compl)
lt2 = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 9 and t.rows[0].cells[1].text.strip() == 'Năm điểm'), None)
assert lt2 is not None, 'thiếu bảng 12 câu total <= 2'
assert len(lt2.rows) == 13, f'bảng 12 câu phải có 12 dòng dữ liệu, thấy {len(lt2.rows)-1}'
for row, x in zip(lt2.rows[1:], C['low_total2']):
    assert row.cells[0].text.strip() == x['id'], f'sai mã câu bảng 12 câu: {row.cells[0].text} khác {x["id"]}'
    assert row.cells[4].text.strip() == vn(x['compl'], 1), f'compl câu {x["id"]} không khớp JSON'

# 4) Bảng worst5: 5 dòng, cột Compl khớp JSON
tbl = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 9 and t.rows[0].cells[1].text.strip() == 'Câu đọc'), None)
assert tbl is not None, 'thiếu bảng 5 câu sai nặng nhất'
assert len(tbl.rows) == 6, f'bảng worst5 phải có 5 dòng dữ liệu, thấy {len(tbl.rows)-1}'
for row, x in zip(tbl.rows[1:], C['worst5']):
    assert row.cells[0].text.strip() == x['id'], f'sai mã câu bảng worst5: {row.cells[0].text}'
    assert row.cells[5].text.strip() == vn(x['compl'], 1), f'compl worst5 câu {x["id"]} không khớp JSON'

# 5) Bảng số đo tự động: khớp JSON acoustic
act = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 5 and t.rows[0].cells[1].text.strip() == 'Biên độ đỉnh'), None)
assert act is not None, 'thiếu bảng số đo tự động'
for row, x in zip(act.rows[1:], C['worst5']):
    assert row.cells[0].text.strip() == x['id'], f'sai mã câu bảng acoustic: {row.cells[0].text}'
    assert row.cells[2].text.strip() == vn(x['acoustic']['rms_dbfs'], 1), f'rms câu {x["id"]} không khớp JSON'

# 6) Bảng ghi chú nghe: phải khớp listening_notes.json (chưa nghe -> trống)
notes = {}
np = P / 'listening_notes.json'
if np.exists():
    notes = json.loads(np.read_text(encoding='utf-8-sig'))
ntbl = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 3 and t.rows[0].cells[1].text.strip() == 'Nghe 1'), None)
assert ntbl is not None, 'thiếu bảng nghe của hai người'
assert len(ntbl.rows) == 6, f'bảng ghi chú phải có 5 dòng, thấy {len(ntbl.rows)-1}'
ids = [x['id'] for x in R['worst5']]
for row, uid in zip(ntbl.rows[1:], ids):
    assert row.cells[0].text.strip() == uid, f'sai mã câu ở bảng ghi chú: {row.cells[0].text}'
    for j, who in enumerate(['nghe1', 'nghe2']):
        expected = str(notes.get(uid, {}).get(who, '')).strip()
        assert row.cells[j + 1].text.strip() == expected, f'ghi chú {who} câu {uid} không khớp JSON'
all_listened = all(str(notes.get(uid, {}).get(w, '')).strip() for uid in ids for w in ['nghe1', 'nghe2'])
assert ('Kết quả nghe.' if all_listened else 'Trạng thái phần nghe.') in full

print('verify_docx OK')
