import json, sys
from pathlib import Path
from docx import Document

P = Path(__file__).parent
docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'report_before_embed.docx'
R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
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
assert '[[OBJECTS]]' in full, 'thiếu đoạn [[OBJECTS]] ở phụ lục'
assert 'Group05_Week11_Report' in full, 'thiếu tên file Week11'
assert 'Week09' not in full, 'còn nhãn Week09 trong báo cáo'
titles = [p.text for p in D.paragraphs if 'Báo cáo tiến độ' in p.text]
assert titles and 'Tuần 11' in titles[0], f'tiêu đề không đúng Tuần 11: {titles}'

# 2) Bốn con số neo phải khớp JSON
w = R['models']['SVR wav2vec 2.0']['test']['recall20']
assert pct(w) in full, f'thiếu recall@20 test wav2vec {pct(w)}'
cvl = R['cv_table']['SVR chỉ độ dài']['recall20'][0]
assert pct(cvl) in full, f'thiếu recall@20 CV chỉ-độ-dài {pct(cvl)}'
assert f"{R['low_total']['n']} câu" in full, 'thiếu số câu nhóm total <= 2'
thr = vn(R['halves']['threshold_sec_per_word'], 2)
assert thr in full, f'thiếu ngưỡng trung vị giây/từ {thr}'

# 3) Bảng worst5 + bảng ghi chú nghe: nội dung phải khớp listening_notes.json (không bịa audio)
tbl = next((t for t in D.tables if t.rows and t.rows[0].cells[0].text.strip() == 'Mã câu'), None)
assert tbl is not None, 'thiếu bảng 5 câu sai nặng nhất'
assert len(tbl.rows) == 6, f'bảng worst5 phải có 5 dòng dữ liệu, thấy {len(tbl.rows)-1}'
notes = {}
np = P / 'listening_notes.json'
if np.exists():
    notes = json.loads(np.read_text(encoding='utf-8-sig'))
ntbl = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 3 and t.rows[0].cells[1].text.strip() == 'Nghe 1'), None)
if ntbl is None:
    # Bản cũ: hai cột ghi chú nằm cuối bảng điểm 9 cột.
    ntbl = tbl; offset = -2
else:
    offset = 1
assert len(ntbl.rows) == 6, f'bảng ghi chú phải có 5 dòng, thấy {len(ntbl.rows)-1}'
ids = [x['id'] for x in R['worst5']]
for row, uid in zip(ntbl.rows[1:], ids):
    assert row.cells[0].text.strip() == uid, f'sai mã câu ở bảng ghi chú: {row.cells[0].text}'
    for j, who in enumerate(['nghe1', 'nghe2']):
        expected = str(notes.get(uid, {}).get(who, '')).strip()
        assert row.cells[offset + j].text.strip() == expected, f'ghi chú {who} câu {uid} không khớp JSON'
all_listened = all(str(notes.get(uid, {}).get(w, '')).strip() for uid in ids for w in ['nghe1', 'nghe2'])
assert ('Kết quả nghe.' if all_listened else 'Trạng thái phần nghe.') in full

print('verify_docx OK')
