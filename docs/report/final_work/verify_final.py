# -*- coding: utf-8 -*-
import json, sys, zipfile
from pathlib import Path
from docx import Document

P = Path(__file__).parent
docx_path = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'report_before_embed.docx'
R = json.loads((P.parent / 'week11_work' / 'week11_results.json').read_text(encoding='utf-8'))
C = json.loads((P.parent / 'week11_work' / 'week11_completeness.json').read_text(encoding='utf-8'))
FC = json.loads((P / 'final_contributions.json').read_text(encoding='utf-8-sig'))
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

# 1) Cấu trúc: đủ 6 mục paper + phụ lục, OLE XOR [[OBJECTS]]
import zipfile as _zf
_has_ole = any('/embeddings/' in n for n in _zf.ZipFile(str(docx_path)).namelist())
assert ('[[OBJECTS]]' in full) != _has_ole, ('[[OBJECTS]] phải có khi chưa nhúng, phải biến mất khi đã nhúng OLE', _has_ole)
for sec_title in ['1. Tóm tắt và giới thiệu', '2. Dữ liệu và phương pháp', '3. Thiết lập thí nghiệm',
                  '4. Kết quả và phân tích lỗi', '5. Thảo luận và kết luận', '6. Tài liệu tham khảo',
                  'Phụ lục A.', 'Phụ lục B.', 'Phụ lục C.']:
    assert sec_title in full, f'thiếu mục {sec_title}'
assert 'BÁO CÁO CUỐI KỲ' in full, 'thiếu tiêu đề báo cáo cuối kỳ'
assert 'Group05_Final_Report' in full or 'Group05_Final_Evidence' in full, 'thiếu tên file final'

# 2) Không còn placeholder đóng góp/AI
for bad in ['(ĐIỀN TÊN)', '(ĐIỀN MSSV)', '(ĐIỀN NỘI DUNG)']:
    assert bad not in full, f'còn placeholder {bad} — phải điền final_contributions.json thật trước khi nộp'
assert len(FC['members']) >= 1 and FC['members'][0]['contributions'], 'final_contributions.json rỗng'

# 3) Con số neo khớp JSON lần chạy 9/11
w = R['models']['SVR wav2vec 2.0']['test']['recall20']
assert pct(w) in full, f'thiếu recall@20 test wav2vec {pct(w)}'
assert '253/330' in full and '253/500' in full, 'thiếu recall/precision@20% minh bạch'
assert vn(R['models']['SVR wav2vec 2.0']['test']['MAE'], 3) in full, 'thiếu MAE wav2vec'
assert f"{R['low_total']['n']} câu" in full, 'thiếu nhóm total <= 2'
cz = C['compl_zero']
num = lambda n: f'{n:,}'.replace(',', '.')
assert f"{cz['n']}/{num(cz['n_test'])}" in full, 'thiếu nhóm completeness = 0'
assert vn(cz['mean_pred_logmel'], 2) in full and vn(cz['mean_pred_w2v'], 2) in full, 'thiếu mean pred nhóm compl 0'
assert '0,00–10,00' in full, 'thiếu thang completeness đo được'
thr = vn(R['halves']['threshold_sec_per_word'], 2)
assert thr in full, f'thiếu ngưỡng giây/từ {thr}'
# 3b) Phân bố + chất lượng dữ liệu (Mục 2)
AG = R['ages']
assert f"{AG['child']['speakers']} trẻ em" in full and f"{AG['adult']['speakers']} người lớn" in full, 'thiếu phân bố tuổi'
Q = json.loads((P / 'final_data_checks.json').read_text(encoding='utf-8'))
assert 'missingness' in Q and 'duplicates' in Q, 'final_data_checks.json thiếu khoá'
assert f"{Q['duplicates']['n_texts_repeated']} câu chữ xuất hiện 2 lần" in full, 'thiếu số câu chữ lặp'
assert 'không có giá trị thiếu' in full, 'thiếu kết luận missingness'
assert 'final_data_checks.py' in full, 'thiếu nhãn nguồn kiểm tra chất lượng dữ liệu'

# 4) Bảng 12 câu total <= 2 khớp JSON
lt2 = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 7 and t.rows[0].cells[1].text.strip() == 'Năm điểm'), None)
assert lt2 is not None, 'thiếu bảng 12 câu total <= 2'
assert len(lt2.rows) == 13, f'bảng 12 câu phải có 12 dòng dữ liệu, thấy {len(lt2.rows)-1}'
for row, x in zip(lt2.rows[1:], C['low_total2']):
    assert row.cells[0].text.strip() == x['id'], f'sai mã câu bảng 12 câu: {row.cells[0].text} khác {x["id"]}'
    assert row.cells[4].text.strip() == vn(x['compl'], 1), f'compl câu {x["id"]} không khớp JSON'

# 5) Bảng nghe 2 người khớp listening_notes.json
notes = json.loads((P.parent / 'week11_work' / 'listening_notes.json').read_text(encoding='utf-8-sig'))
ntbl = next((t for t in D.tables if t.rows and len(t.rows[0].cells) == 3 and t.rows[0].cells[1].text.strip() == 'Nghe 1'), None)
assert ntbl is not None, 'thiếu bảng nghe'
assert len(ntbl.rows) == 6, f'bảng nghe phải có 5 dòng, thấy {len(ntbl.rows)-1}'
for row, x in zip(ntbl.rows[1:], C['worst5']):
    assert row.cells[0].text.strip() == x['id'], f'sai mã câu bảng nghe: {row.cells[0].text}'
    for j, who in enumerate(['nghe1', 'nghe2']):
        expected = str(notes.get(x['id'], {}).get(who, '')).strip()
        assert row.cells[j + 1].text.strip() == expected, f'ghi chú {who} câu {x["id"]} không khớp JSON'

# 6) Bảng đóng góp: mỗi thành viên có tên thật (không khớp placeholder đã check ở trên)
n_mem = len(FC['members'])
found = sum(1 for m in FC['members'] if str(m.get('name', '')).strip() in full)
assert found == n_mem, f'chỉ thấy {found}/{n_mem} tên thành viên trong báo cáo'

print('verify_final OK')
