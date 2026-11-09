from pathlib import Path
import json, datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# Bao cao Tuan 11 (ban moi sau buoi phong van 4/11): cau truc bam 3 diem feedback
# [FB1] dinh nghia mot ban ghi, nam diem giam khao -> total, kiem chung tren mot ban ghi, nguoi noi tach roi;
# [FB2] dinh nghia ba loai dac trung (do dai, log-mel, wav2vec), so sanh tren cung phep danh gia,
#       recall@20% tinh ro tu danh sach duoc chon va tong so bai under 6;
# [FB3] tu nghe 5 cau loi nang nhat, chi phan biet doc lac/im lang khi so lieu ho tro.
# Trong tam cua ban nay la completeness (yeu cau cua nguoi dung + FB3).
# Moi so lay tu week11_results.json + week11_completeness.json + figure_stats.json cua lan chay co anh Terminal.
P = Path(__file__).parent
R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
C_ = json.loads((P / 'week11_completeness.json').read_text(encoding='utf-8'))
CZ, L2, W5C = C_['compl_zero'], C_['low_total2'], C_['worst5']
_t = datetime.datetime.fromtimestamp((P / 'week11_run.log').stat().st_mtime)
RUN = _t.strftime('%H:%M') + ' ngày ' + f'{_t.day}/{_t.month}/{_t.year}'
RUN_DATE = f'{_t.day:02d}/{_t.month:02d}/{_t.year}'
M, CVT, H, LT, B6 = R['models'], R['cv_table'], R['halves'], R['low_total'], R['below6']
# Ghi chu nghe: dien vao listening_notes.json (nghe1/nghe2 cho tung ma cau). Chua nghe -> de trong.
_notes_path = P / 'listening_notes.json'
NOTES = json.loads(_notes_path.read_text(encoding='utf-8-sig')) if _notes_path.exists() else {}
note = lambda uid, who: str(NOTES.get(uid, {}).get(who, '')).strip()
ALL_LISTENED = all(note(x['id'], 'nghe1') and note(x['id'], 'nghe2') for x in R['worst5'])
T = lambda k: M[k]['test']
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
pct = lambda v: f'{v*100:.0f}%'
num = lambda n: f'{n:,}'.replace(',', '.')
sgn = lambda v, n: ('+' if v > 0 else '−' if v < 0 else '') + vn(abs(v), n)
five_str = lambda fs: ' · '.join(vn(v, 0) if v == int(v) else vn(v, 1) for v in fs)

D = Document(); sec = D.sections[0]
sec.page_width, sec.page_height = Cm(21), Cm(29.7)
sec.top_margin = sec.bottom_margin = Cm(1.8); sec.left_margin = sec.right_margin = Cm(2.2)
for name in ['Normal', 'Caption', 'Heading 1', 'Title', 'Subtitle']:
    st = D.styles[name]; st.font.name = 'Times New Roman'; st.font.color.rgb = RGBColor(0, 0, 0)
    st.paragraph_format.line_spacing = 1.5
D.styles['Normal'].font.size = Pt(12); D.styles['Normal'].paragraph_format.space_after = Pt(4)
h1 = D.styles['Heading 1']; h1.font.size = Pt(14); h1.font.bold = True
h1.paragraph_format.space_before = Pt(10); h1.paragraph_format.space_after = Pt(4); h1.paragraph_format.keep_with_next = True
cap = D.styles['Caption']; cap.font.size = Pt(10); cap.font.italic = True; cap.font.bold = False
D.core_properties.title = 'Báo cáo tuần 11 về chấm điểm phát âm'; D.core_properties.author = 'Nhóm 05'

def border(el, edges, sz, color='000000'):
    b = OxmlElement('w:pBdr' if el.tag == qn('w:pPr') else 'w:tcBorders')
    for e in edges:
        x = OxmlElement('w:' + e); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), str(sz)); x.set(qn('w:space'), '1'); x.set(qn('w:color'), color); b.append(x)
    el.append(b)
def p(text='', style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    para = D.add_paragraph(text, style); para.alignment = align; return para
def lead(label, text):
    para = p(); para.add_run(label + ' ').bold = True; para.add_run(text); return para
def h(text):
    para = D.add_heading(text, 1); border(para._p.get_or_add_pPr(), ['bottom'], 6, '7F7F7F'); return para
def link(label, url):
    para = p(align=WD_ALIGN_PARAGRAPH.LEFT); e = OxmlElement('w:hyperlink'); e.set(qn('r:id'), para.part.relate_to(url, RT.HYPERLINK, is_external=True))
    r = OxmlElement('w:r'); pr = OxmlElement('w:rPr'); u = OxmlElement('w:u'); u.set(qn('w:val'), 'single'); pr.append(u); r.append(pr)
    t = OxmlElement('w:t'); t.text = label; r.append(t); e.append(r); para._p.append(e); return para
def cell_fmt(c, width, edges=(), sz=0, fill=None, mar=80):
    c.width = Cm(width); tc = c._tc.get_or_add_tcPr()
    b = OxmlElement('w:tcBorders')
    for e in ['top', 'left', 'bottom', 'right']:
        x = OxmlElement('w:' + e)
        if e in edges: x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), str(sz)); x.set(qn('w:color'), '000000')
        else: x.set(qn('w:val'), 'nil')
        b.append(x)
    tc.append(b)
    if fill: s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:fill'), fill); tc.append(s)
    m = OxmlElement('w:tcMar')
    for e in ['top', 'bottom', 'left', 'right']:
        x = OxmlElement('w:' + e); x.set(qn('w:w'), str(mar)); x.set(qn('w:type'), 'dxa'); m.append(x)
    tc.append(m)
def booktabs(headers, rows, widths, num_from=1, size=10.5):
    t = D.add_table(rows=1, cols=len(headers)); t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, s in enumerate(headers): t.rows[0].cells[i].text = s
    for col, wd in zip(t.columns, widths): col.width = Cm(wd)
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); t._tbl.tblPr.append(lay)
    for row in rows:
        cs = t.add_row().cells
        for i, s in enumerate(row): cs[i].text = str(s)
    n = len(t.rows)
    for ri, row in enumerate(t.rows):
        tr = row._tr.get_or_add_trPr(); tr.append(OxmlElement('w:cantSplit'))
        for ci, c in enumerate(row.cells):
            edges = (['top', 'bottom'] if ri == 0 else []) + (['bottom'] if ri == n - 1 else [])
            cell_fmt(c, widths[ci], edges, 12 if ri == n - 1 or ri == 0 else 0)
            if ri == 0:
                for x in c._tc.tcPr.find(qn('w:tcBorders')):
                    if x.tag == qn('w:bottom'): x.set(qn('w:sz'), '6')
                    if x.tag == qn('w:top'): x.set(qn('w:sz'), '12')
            for para in c.paragraphs:
                para.paragraph_format.line_spacing = 1.35; para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.keep_with_next = ri < n - 1
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci >= num_from else WD_ALIGN_PARAGRAPH.LEFT
                for r in para.runs: r.font.size = Pt(size); r.bold = ri == 0
    sp = p(); sp.paragraph_format.space_after = Pt(0)
    rpr = OxmlElement('w:rPr'); sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '8'); rpr.append(sz); sp._p.get_or_add_pPr().append(rpr)
    return t
def caption(para_or_cell, label, text):
    c = para_or_cell.add_paragraph(style='Caption') if hasattr(para_or_cell, 'add_paragraph') and not hasattr(para_or_cell, 'add_heading') else p(style='Caption')
    c.alignment = WD_ALIGN_PARAGRAPH.LEFT; c.paragraph_format.line_spacing = 1.5
    r = c.add_run(label + ' '); r.bold = True; r.italic = False; c.add_run(text); return c
def figure(name, width, label, text):
    para = p(align=WD_ALIGN_PARAGRAPH.CENTER); para.paragraph_format.keep_with_next = True; para.paragraph_format.space_after = Pt(0)
    para.add_run().add_picture(str(P / name), width=Cm(width)); caption(D, label, text)
def figure_pair(left, right):
    t = D.add_table(rows=2, cols=2); t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, (name, label, text) in zip(t.rows[0].cells, [left, right]):
        cell_fmt(c, 8.3, mar=40); para = c.paragraphs[0]; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.line_spacing = 1.5; para.paragraph_format.space_after = Pt(0)
        para.add_run().add_picture(str(P / name), width=Cm(8.0))
        va = OxmlElement('w:vAlign'); va.set(qn('w:val'), 'bottom'); c._tc.get_or_add_tcPr().append(va)
    for c, (_, label, text) in zip(t.rows[1].cells, [left, right]):
        cell_fmt(c, 8.3, mar=40)
        q = c.paragraphs[0]; q.style = D.styles['Caption']; q.alignment = WD_ALIGN_PARAGRAPH.LEFT
        q.paragraph_format.line_spacing = 1.5; q.paragraph_format.space_after = Pt(0)
        r = q.add_run(label + ' '); r.bold = True; r.italic = False; q.add_run(text)
    for row in t.rows:
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))

# ---- Dau trang ----
TC = R['target_check']; RT_ = R['raters']
top = p('NHÓM 05  ·  LỚP 61FIT4MLA  ·  NGÀY ' + RUN_DATE, align=WD_ALIGN_PARAGRAPH.LEFT)
top.runs[0].font.size = Pt(10); top.paragraph_format.space_after = Pt(0)
tt = p('Báo cáo tiến độ Tuần 11', align=WD_ALIGN_PARAGRAPH.LEFT); tt.runs[0].font.size = Pt(20); tt.runs[0].bold = True
tt.paragraph_format.space_after = Pt(0)
st = p('Nhãn, đặc trưng và lỗi nặng nhất — bám 3 điểm feedback sau phỏng vấn', align=WD_ALIGN_PARAGRAPH.LEFT)
st.runs[0].italic = True; st.runs[0].font.size = Pt(13)
border(st._p.get_or_add_pPr(), ['bottom'], 12); st.paragraph_format.space_after = Pt(8)

w = T('SVR wav2vec 2.0')
w2l = T('SVR wav2vec + độ dài'); lrw = T('LR phân loại cân bằng (wav2vec)')
cvw = CVT['SVR wav2vec 2.0']['recall20']; cvwl = CVT['SVR wav2vec + độ dài']['recall20']; cvd = CVT['SVR chỉ độ dài']['recall20']
fast, slow = H['fast'], H['slow']
# Con so recall@20% minh bach (FB2): danh sach 20% duoc chon va tong so bai under 6
N_SEL = int(round(0.20 * B6['test'][1])); N_LOW = B6['test'][0]
N_CAUGHT = int(round(w['recall20'] * N_LOW))
P_CAUGHT = int(round(w['precision20'] * N_SEL))
wv_mean, wl_mean = CZ['mean_pred_logmel'], CZ['mean_pred_w2v']

# Khung ket qua
box = D.add_table(rows=1, cols=1); box.alignment = WD_TABLE_ALIGNMENT.CENTER; bc = box.rows[0].cells[0]
cell_fmt(bc, 16.6, ['bottom'], 18, None, 120)
bp = bc.paragraphs[0]; bp.add_run('Kết quả chính tuần này').bold = True; bp.paragraph_format.line_spacing = 1.5
for s in [f"Nhãn được kiểm chứng: target = trung vị năm điểm giám khảo làm tròn xuống, khớp {num(TC['floor_median'])}/5.000 câu; định nghĩa một bản ghi và kiểm chứng trên một bản ghi cụ thể ở Mục 2, người nói tách rời train/test.",
          f"So sánh công bằng trên cùng một phép đo: bảng CV cho 10 cấu hình + test; recall@20% của SVR wav2vec 2.0 = {N_CAUGHT}/{N_LOW} bài dưới 6 {pct(w['recall20'])} (danh sách {N_SEL} bài được chọn; precision {P_CAUGHT}/{N_SEL} = {pct(w['precision20'])}).",
          f"Completeness: trên test chỉ có {CZ['n']}/{num(CZ['n_test'])} câu bị corpus chấm completeness = 0 (total 0); mô hình mức câu vẫn đoán trung bình {vn(wv_mean, 1)} điểm (log-mel) và {vn(wl_mean, 1)} điểm (wav2vec) cho nhóm này — đặc trưng mức câu không nhìn thấy phần nội dung thiếu (Mục 6).",
          f"Phần nghe 5 câu lỗi nặng nhất (FB3): " + ('đã có ghi chú của hai người nghe độc lập.' if ALL_LISTENED else 'chưa thực hiện — bảng ghi chờ hai người trong nhóm điền; hiện đã có số đo tự động và điểm corpus để đối chiếu.')]:
    q = bc.add_paragraph(); q.paragraph_format.line_spacing = 1.5; q.paragraph_format.space_after = Pt(0)
    q.paragraph_format.left_indent = Cm(0.5); q.paragraph_format.first_line_indent = Cm(-0.5); q.add_run('•\t' + s)
    q.paragraph_format.tab_stops.add_tab_stop(Cm(0.5))
sp = p(); sp.paragraph_format.space_after = Pt(0)

h('1. Ba điểm feedback sau phỏng vấn và vị trí đáp trong báo cáo này')
p('Báo cáo tuần 11 dựng lại theo ba điểm góp ý sau buổi phỏng vấn ngày 4/11. Bảng dưới đối chiếu từng điểm với mục tương ứng; mọi số lấy từ lần chạy có ảnh Terminal ở Phụ lục.')
booktabs(['Điểm feedback sau phỏng vấn', 'Báo cáo đáp thế nào', 'Ở đâu'], [
    ['1. Định nghĩa một bản ghi; giải thích năm điểm giám khảo ra total; kiểm chứng trên một bản ghi; giữ người nói tách rời train/test.',
     'Định nghĩa bản ghi + bảng kiểm nhãn trên 5.000 câu + kiểm chứng một bản ghi cụ thể', 'Mục 2'],
    ['2. Giải thích độ dài, log-mel, wav2vec là gì; so sánh trên cùng phép đánh giá; recall@20% tính từ danh sách được chọn và tổng số bài kém.',
     'Định nghĩa từng loại đặc trưng, cùng protocol CV/test, công thức recall minh bạch ' + f'{N_CAUGHT}/{N_LOW}', 'Mục 3–4'],
    ['3. Tự nghe các lỗi nặng nhất; ghi điều nghe được kèm điểm thật và dự đoán; chỉ phân biệt đọc lạc đề/im lặng khi audio hỗ trợ.',
     'Phần thống kê + completeness + số đo tự động đã làm; phần nghe chưa — bảng chờ hai người điền', 'Mục 6'],
    ['Thêm (theo yêu cầu nhóm): làm rõ thang điểm corpus, đặc biệt completeness.', 'Thang đo được trên 2.500 câu test + bảng 12 câu total ≤ 2 và 5 câu worst5 có cột completeness', 'Mục 6']],
    [7.4, 6.0, 2.6], num_from=2)

h('2. Một bản ghi là gì và năm điểm giám khảo cho ra total thế nào')
lead('Một bản ghi.', 'Một câu đọc: một mã câu (ví dụ 014040089), một người nói, một câu chữ cố định, một file WAV 16 kHz mono, và năm giám khảo độc lập của corpus chấm riêng từng từ. Điểm câu gồm 4 chỉ số mức câu: accuracy, fluency, prosodic, completeness (mỗi chỉ 0–10; completeness là tỉ lệ từ được đọc tốt từ thang 0–1 giãn lên 0–10); ngoài ra năm giám khảo còn chấm thêm một điểm tổng total cho câu.')
lead('Năm điểm giám khảo ra total thế nào.', 'Scores.json của corpus đã gộp; kiểm chứng độc lập của nhóm: total của mỗi câu = làm tròn xuống trung vị năm điểm giám khảo — khớp ' + num(TC['floor_median']) + '/5.000 câu (bảng dưới; trung vị làm tròn gần nhất chỉ khớp ' + num(TC['round_median']) + ', trung bình chỉ khớp ' + num(TC['mean_exact']) + '). Vì thế bài toán học total — không phải học trung bình.')
booktabs(['So total trong scores.json với', 'Số câu khớp / 5.000'], [
    ['Trung vị năm điểm, làm tròn xuống', num(TC['floor_median'])], ['Trung vị năm điểm, làm tròn gần nhất', num(TC['round_median'])],
    ['Trung bình năm điểm', num(TC['mean_exact'])]], [11.0, 5.6])
ex = RT_['example']
lead('Kiểm chứng trên một bản ghi.', 'Câu ' + ex['id'] + ': năm giám khảo cho ' + '; '.join(vn(v, 1) for v in ex['five']) + ' — trung bình ' + vn(ex['mean'], 2) + ' nhưng trung vị ' + vn(ex['median'], 1) + ' và total đúng là ' + vn(ex['total'], 0) + '. Một giám khảo chấm lệch (' + vn(min(ex['five']), 1) + ') không được kéo điểm của câu xuống. Đây cũng là lý do không dùng trung bình làm target.')
lead('Vì sao trung vị bền.', 'Có ' + str(RT_['n_odd3']) + ' câu mà một giám khảo lệch từ 3 điểm trở lên so với trung vị bốn người còn lại; ở nhóm đó trung bình và trung vị cách nhau trung bình ' + vn(RT_['mean_shift_odd'], 2) + ' điểm, gấp đôi mức ' + vn(RT_['mean_shift_all'], 2) + ' trên toàn bộ dữ liệu.')
lead('Người nói tách rời.', 'Chia 125 người train / 125 người test theo người nói (không phép trộn); chọn tham số bằng GroupKFold 5 phần theo người nói trên nhóm train. Kết quả test không phải cho những người mô hình đã thấy.')

h('3. Ba cách nhìn một bản ghi: độ dài, log-mel, wav2vec')
lead('Chỉ hai đặc trưng độ dài.', 'Thời gian đọc (giây) và giây/từ (thời gian chia số từ câu). Chỉ đo nhịp đọc, không nghe được âm nào.')
lead('Log-mel 81 đặc trưng.', '40 dải log-mel (khung 25 ms, bước 10 ms) trên mỗi audio; lấy trung bình và độ lệch chuẩn theo thời gian của từng dải (80) cộng độ dài câu (1) = 81. Đây là "tóm tắt âm học" mức câu: có thấy tiếng đọc to/nhỏ, đều/không đều, nhưng không biết từng âm ở đâu.')
lead('Wav2vec 2.0 768 đặc trưng.', 'Mô hình facebook/wav2vec2-base tiền huấn luyện trên tiếng nói, giữ nguyên (đóng băng); lấy trung bình theo thời gian của tầng 8 embedding (768 chiều). Đã trích sẵn từ tuần 10, lần chạy này không trích lại.')
lead('Cùng một phép so sánh.', 'Ba loại đặc trưng trên đi vào cùng một cách học (SVR) trên cùng tập train (125 người) và cùng tiêu chí chọn tham số (CV GroupKFold-5 theo người nói); test chạy một lần trên 125 người khác. Cột CV và cột test đặt cạnh nhau trong bảng Mục 4.')
lead('Recall@20% là gì (đáp điểm feedback 2).', 'Xếp 2.500 câu test theo điểm dự đoán tăng dần, lấy ' + str(N_SEL) + ' bài (20%) có điểm thấp nhất — danh sách giáo viên sẽ nghe. Recall@20% = số bài thật sự dưới 6 thu được trong danh sách đó chia tổng số bài dưới 6 của test: với SVR wav2vec 2.0 là ' + str(N_CAUGHT) + '/' + str(N_LOW) + ' = ' + pct(w['recall20']) + '. Precision@20% = ' + pct(w['precision20']) + ' (' + str(P_CAUGHT) + '/' + str(N_SEL) + ' bài trong danh sách thật sự dưới 6). Tỉ lệ nền nếu chọn ngẫu nhiên là ' + vn(R['base_rate_test'] * 100, 1) + '%, recall kỳ vọng 20%.')

h('4. So sánh trên cùng một split: bảng CV đầy đủ + test')
p('Bảng dưới là toàn bộ 10 cấu hình học, kèm dòng ngẫu nhiên / hằng số; quyết định chọn hướng đọc theo cột CV, cột test chỉ xác nhận. Độ lệch chuẩn giữa các fold ' + vn(min(CVT[k]['recall20'][1] for k in CVT) * 100, 0) + '–' + vn(max(CVT[k]['recall20'][1] for k in CVT) * 100, 0) + ' điểm %, nên chênh lệch nhỏ giữa các cấu hình không đáng tin.')
order = ['SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài', 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số', 'LR phân loại cân bằng',
         'RF phân loại cân bằng', 'SVR wav2vec 2.0', 'SVR wav2vec + độ dài', 'LR phân loại cân bằng (wav2vec)']
rows = []
for k in order:
    c, t = CVT[k], T(k)
    rows.append([k, pct(c['recall20'][0]) + ' ± ' + vn(c['recall20'][1] * 100, 0), (vn(c['MAE'][0], 3) + ' ± ' + vn(c['MAE'][1], 3)) if c['MAE'] else '—',
                 pct(t['recall20']), vn(t['MAE'], 3) if 'MAE' in t else '—'])
rows.append(['Ngẫu nhiên / hằng số', '—', '—', pct(T('Ngẫu nhiên / hằng số')['recall20']), vn(T('Ngẫu nhiên / hằng số')['MAE'], 3)])
booktabs(['Mô hình', 'R@20% CV (TB ± SD)', 'MAE CV (TB ± SD)', 'R@20% test', 'MAE test'], rows, [4.8, 3.0, 2.8, 2.4, 2.2], size=9.5)
p('Đọc bảng theo cột CV: trong nhóm hồi quy, SVR wav2vec 2.0 tốt nhất (' + pct(cvw[0]) + ' ± ' + vn(cvw[1] * 100, 0) + ' điểm %, MAE ' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + '); chỉ-độ-dài ' + pct(cvd[0]) + '. Thêm hai đặc trưng độ dài vào wav2vec gần như không đổi CV (' + pct(cvwl[0]) + ', MAE ' + vn(CVT['SVR wav2vec + độ dài']['MAE'][0], 3) + ' so với ' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + ') — nghĩa là embedding wav2vec đã chứa phần lớn thông tin độ dài; phần nó hơn chỉ-độ-dài đến từ âm học khác tốc độ đọc. LR cân bằng lớp trên wav2vec có CV ' + pct(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]) + ' nhưng test chỉ ' + pct(lrw['recall20']) + ' so với ' + pct(w['recall20']) + ' của SVR; chênh nằm trong độ lệch chuẩn giữa các fold nên không đủ căn cứ đổi mô hình chính (chi tiết Mục 7).')
figure('fig1_cv_test.png', 15.5, 'Hình 1.', 'Recall@20% trên CV (chấm rỗng, thanh mảnh là độ lệch chuẩn giữa 5 fold) và trên test (chấm đặc) cho mọi cấu hình; số % ghi dưới chấm đặc là recall trên test, giá trị CV xem bảng ở Mục 4. Khoảng cách giữa hai chấm cho biết CV lạc quan hơn test bao nhiêu.')

h('5. Kiểm tra nửa đọc nhanh / đọc chậm')
p('Chia 2.500 câu test thành hai nửa theo trung vị giây/từ (' + vn(H['threshold_sec_per_word'], 2) + ' giây/từ). Trong từng nửa, lấy 20% câu có điểm dự đoán thấp nhất và tính tỉ lệ bài dưới 6 bắt được. Phép kiểm chỉ đọc dự đoán của mô hình đã huấn luyện ở Mục 3–4, không chọn lại tham số hay ngưỡng nào.')
booktabs(['Nửa tốc độ', 'Số câu', 'Trong đó dưới 6', 'R@20% chỉ độ dài', 'R@20% wav2vec 2.0'], [
    ['Đọc nhanh (< ' + vn(H['threshold_sec_per_word'], 2) + ' s/từ)', str(fast['n']), str(fast['n_below6']), pct(fast['recall20']['length']), pct(fast['recall20']['w2v'])],
    ['Đọc chậm (≥ ' + vn(H['threshold_sec_per_word'], 2) + ' s/từ)', str(slow['n']), str(slow['n_below6']), pct(slow['recall20']['length']), pct(slow['recall20']['w2v'])]],
    [5.2, 2.2, 2.8, 3.2, 3.2])
gap_f = (fast['recall20']['w2v'] - fast['recall20']['length']) * 100
gap_s = (slow['recall20']['w2v'] - slow['recall20']['length']) * 100
if gap_f >= 0:
    concl = ('wav2vec hơn chỉ-độ-dài ở cả hai nửa (nhanh ' + vn(gap_f, 0) + ' điểm %, chậm ' + vn(gap_s, 0) + ' điểm %), nên phần vượt trội không chỉ là tốc độ đọc. Lưu ý nửa đọc nhanh chỉ có ' + str(fast['n_below6']) + ' bài dưới 6, nên chênh lệch ở nửa này có sai số lớn; nửa đọc chậm (' + str(slow['n_below6']) + ' bài dưới 6) mới là nơi hai mô hình gần nhau.')
else:
    concl = ('Ở nửa đọc nhanh wav2vec không hơn chỉ-độ-dài (' + vn(gap_f, 0) + ' điểm %), còn ở nửa đọc chậm hơn ' + vn(gap_s, 0) + ' điểm %. Kết luận vẫn có giá trị: đặc trưng mức câu chủ yếu đo tốc độ đọc, cần đặc trưng theo từng âm như GOP để bắt người đọc nhanh nhưng phát âm sai.')
p(concl)
figure_pair(('fig2_halves.png', 'Hình 2.', 'Recall@20% trong từng nửa tốc độ; n là số câu, "<6" là số bài dưới 6 của nửa đó.'),
            ('fig3_speed_dist.png', 'Hình 3.', 'Phân bố giây/từ trên 2.500 câu test; vạch đứt là trung vị dùng để chia nửa.'))

h('6. Nhóm lỗi nặng nhất: thang điểm corpus và completeness')
p('Phần này trả lời điểm feedback 3 và câu hỏi "vì sao bài total 0 mà mô hình vẫn đoán ~7". Nguồn số: điểm câu của corpus (accuracy, completeness, fluency, prosodic — đọc trực tiếp từ parquet gốc, khớp đúng 2.500 câu test), số đo âm học tự động trên file WAV, và dự đoán của lần chạy này. Phần nghe của con người chưa thực hiện; ghi tường minh ở cuối mục.')
p('Trên 2.500 câu test, thang đo được của corpus: accuracy ' + vn(C_['scale']['accuracy'][0], 1) + '–' + vn(C_['scale']['accuracy'][1], 1) + ', fluency ' + vn(C_['scale']['fluency'][0], 1) + '–' + vn(C_['scale']['fluency'][1], 1) + ', prosodic ' + vn(C_['scale']['prosodic'][0], 1) + '–' + vn(C_['scale']['prosodic'][1], 1) + ', total ' + vn(C_['scale']['total'][0], 1) + '–' + vn(C_['scale']['total'][1], 1) + '; completeness đo được ' + vn(C_['scale']['completeness'][0], 2) + '–' + vn(C_['scale']['completeness'][1], 2) + ' (tài liệu corpus ghi "0–1" như tỉ lệ từ đọc tốt; dữ liệu thực dùng thang ×10, tối đa 10 — báo cáo ghi theo số đo được).')
lead('Trước hết, nhãn total ≤ 2 khác nhau về nguyên nhân.', 'Bảng 12 câu total ≤ 2 dưới đây: chỉ ' + str(C_['n_zero_in_low12']) + ' câu có completeness = 0; ' + str(LT['n'] - C_['n_zero_in_low12']) + ' câu còn lại có completeness ' + vn(min(x['compl'] for x in L2 if x['compl'] > 0), 1) + '–' + vn(max(x['compl'] for x in L2 if x['compl'] > 0), 1) + ' — đọc được một phần hoặc gần đủ nội dung nhưng phát âm sai nặng. Nghĩa là "bài rất kém" gồm cả hai loại: thiếu nội dung và đọc sai; bảng dưới cho thấy đặc trưng mức câu không nhìn ra được sự khác nhau này.')
booktabs(['Mã câu', 'Năm điểm', 'Total', 'Acc', 'Compl', 'Flu', 'Pros', 'Log-mel', 'w2v'],
         [[x['id'], five_str(x['five']), vn(x['total'], 0), vn(x['acc'], 0), vn(x['compl'], 1), vn(x['flu'], 0), vn(x['pros'], 0), vn(x['pred_logmel'], 2), vn(x['pred_w2v'], 2)] for x in L2],
         [1.9, 2.7, 1.1, 1.0, 1.3, 1.0, 1.0, 1.35, 1.35], num_from=2, size=8.5)
n_c0 = sum(1 for x in W5C if x['compl'] == 0.0)
lead('Năm câu sai nặng nhất (cùng bộ tuần 10, đã kiểm tra trùng mã câu).', 'Định nghĩa: năm câu total dưới 6 mà SVR log-mel đoán cao hơn thật nhiều nhất. Bảng dưới thêm cột completeness: ' + str(n_c0) + '/5 câu có completeness = 0,0 — corpus coi phần đọc không còn từ nào tin cậy (đọc lạc đề, quá nhỏ, hoặc gần như không có tiếng đọc); riêng 014040122 có 1,7, tức chỉ khoảng 17% số từ được coi là đọc tốt. Nhịp đọc của năm câu dao động ' + vn(min(x['sec_per_word'] for x in W5C), 1) + '–' + vn(max(x['sec_per_word'] for x in W5C), 1) + ' giây/từ (trung vị test ' + vn(H['threshold_sec_per_word'], 2) + ' — xem Hình 3), nên tốc độ đọc một mình cũng không cho biết câu còn thiếu nội dung.')
booktabs(['Mã câu', 'Câu đọc', 'Năm điểm', 'Total', 'Acc', 'Compl', 'Log-mel', 'w2v', 'Giây'],
         [[x['id'], x['text'], five_str(x['five']), vn(x['total'], 0), vn(x['acc'], 0), vn(x['compl'], 1), vn(x['pred_logmel'], 2), vn(x['pred_w2v'], 2), vn(x['sec_per_word'], 1)] for x in W5C],
         [1.9, 3.9, 2.35, 1.0, 0.9, 1.15, 1.35, 1.2, 0.9], num_from=2, size=8.5)
lead('Số đo tự động trên file WAV (không phải nghe).', 'Bảng dưới là những gì đo được trong lần chạy này: biên độ đỉnh, RMS theo dBFS và tỉ lệ khung 25 ms có năng lượng đáng chú ý (ngưỡng = 8% mức RMS của khung có năng lượng lớn nhất). RMS của cả 5 file đều dưới −35 dBFS, dù biên độ đỉnh tới 0,58–0,60 cho thấy vẫn có đoạn phát khá to; đây là số tự động được ghi chính xác như đo, KHÔNG thay cho phần nghe của con người.')
booktabs(['Mã câu', 'Biên độ đỉnh', 'RMS (dBFS)', 'Khung có năng lượng', 'Giây'],
         [[x['id'], vn(x['acoustic']['peak'], 2), vn(x['acoustic']['rms_dbfs'], 1), vn(x['acoustic']['pct_frames'], 0) + '%', vn(x['acoustic']['duration_s'], 1)] for x in W5C],
         [2.6, 2.6, 3.4, 4.0, 2.4], num_from=1)
lead('Mô hình không nhìn thấy phần thiếu — bằng một con số.', 'Trên toàn test, chỉ ' + str(CZ['n']) + ' câu có completeness = 0 và cả ' + str(CZ['n']) + ' câu đều bị chấm total 0. Dự đoán trung bình của mô hình cho đúng nhóm này là ' + vn(wv_mean, 2) + ' (log-mel) và ' + vn(wl_mean, 2) + ' (wav2vec) — tức mô hình coi chúng là bài bình thường. Nguyên nhân: mô hình tối thiểu hoá sai số trung bình trên phần lớn 2.500 câu bình thường, nên bài rất kém bị "nén" về giữa thang (bài dưới 6 bị wav2vec đoán cao hơn thật trung bình ' + sgn(w['bias_low'], 2) + ' điểm). Completeness là điểm giám khảo corpus gán cho bài đọc; các đặc trưng mức câu không nhìn ra phần nội dung thiếu.')
lead('Phần này đóng điểm feedback 3 thế nào.', 'Dữ liệu hiện có hỗ trợ nhận diện: điểm corpus (completeness 0) và số đo tự động cho phép nghiêng về "đọc lạc đề / không đọc đủ hoặc quá nhỏ" — nhưng xác nhận cuối cùng chỉ có tai người. Audio gốc của cả 5 câu nằm trong minh chứng (worst5/*.WAV) để nhóm nghe trực tiếp và điền bảng dưới; chưa nghe thì bảng để trống đúng như vậy.')
p('Ghi chú nghe (mỗi câu hai người nghe độc lập; chỉ ghi gì thật sự nghe được: có đọc hết câu không, từ nào rõ/sai/mất, im lặng dài hay tiếng ồn):')
booktabs(['Mã câu', 'Nghe 1', 'Nghe 2'],
         [[x['id'], note(x['id'], 'nghe1'), note(x['id'], 'nghe2')] for x in R['worst5']],
         [2.4, 7.1, 7.1], num_from=1, size=9.0)
if ALL_LISTENED:
    lead('Kết quả nghe.', 'Hai người nghe độc lập đã ghi lại điều nghe được cho cả năm câu; ghi chú giữ nguyên văn, không suy diễn thêm. Phần này dùng cho buổi vấn đáp, không thay đổi điểm dự đoán hay kết luận ở các mục trên.')
else:
    lead('Trạng thái phần nghe.', 'Chưa thực hiện: mỗi câu cần ít nhất hai người nghe độc lập. Báo cáo không tự suy diễn nội dung audio; phần trên chỉ dùng điểm corpus và số đo tự động có nguồn rõ.')

h('7. Thí nghiệm phụ: LR cân bằng lớp trên wav2vec')
p('Phân loại cân bằng lớp có hơn hồi quy trên cùng đặc trưng wav2vec không? CV recall@20% = ' + pct(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]) + ' ± ' + vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][1] * 100, 0) + ' điểm %, test R@10% = ' + pct(lrw['recall10']) + ', R@20% = ' + pct(lrw['recall20']) + ' (SVR wav2vec: R@10% = ' + pct(w['recall10']) + ', R@20% = ' + pct(w['recall20']) + '). Phân loại có CV nhỉnh hơn ' + vn((CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0] - cvw[0]) * 100, 1) + ' điểm nhưng test thấp hơn ' + vn((w['recall20'] - lrw['recall20']) * 100, 0) + ' điểm; cả hai chênh đều nằm trong độ lệch chuẩn giữa các fold (' + vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][1] * 100, 0) + ' điểm). Nhóm giữ hồi quy vì cho điểm liên tục và test cao hơn. Đây là thí nghiệm phụ, không nằm trong ba điểm feedback.')

h('8. Chuẩn bị vấn đáp')
lead('Vì sao trung vị bền với một giám khảo chấm lệch?', 'Có ' + str(RT_['n_odd3']) + ' câu mà một giám khảo lệch từ 3 điểm trở lên so với trung vị bốn người còn lại; ở các câu đó trung bình và trung vị cách nhau trung bình ' + vn(RT_['mean_shift_odd'], 2) + ' điểm, gấp đôi mức ' + vn(RT_['mean_shift_all'], 2) + ' trên toàn bộ dữ liệu. Ví dụ câu ' + RT_['example']['id'] + ' ở Mục 2.')
lead('Vì sao bài total 0 vẫn bị đoán khoảng 7?', 'Hồi quy tối thiểu hoá sai số trung bình; đặc trưng mức câu không phân biệt được bài rất kém, nên dự đoán an toàn là gần trung bình. Với nhóm ' + str(CZ['n']) + ' câu completeness = 0, dự đoán trung bình là ' + vn(wv_mean, 2) + '/' + vn(wl_mean, 2) + '; điểm thật có thể đến 0. Chưa có phần nghe để xác nhận nguyên nhân từng câu — chỉ có điểm corpus và số đo tự động.')
lead('Nếu giáo viên chỉ nghe 10% số bài, con số nào cho biết công cụ đáng dùng?', 'P@10% và R@10% (tính trong lần chạy này): với SVR wav2vec 2.0, ' + pct(w['precision10']) + ' bài trong 10% được nghe thật sự dưới 6 (ngẫu nhiên ' + pct(T('Ngẫu nhiên / hằng số')['precision10']) + '), bắt được ' + pct(w['recall10']) + ' tổng số bài dưới 6.')
lead('Giới hạn.', 'Người nói có tiếng mẹ đẻ Quan Thoại, gồm cả trẻ em; bài đọc câu ngắn; công cụ chưa chẩn đoán từng âm và chưa có bằng chứng dùng tốt cho người học Việt Nam. Phân biệt đọc lạc đề / im lặng / nguyên nhân khác chỉ làm được khi audio hỗ trợ — hiện chưa có nghe của nhóm cho phần này.')

h('9. Thời gian chạy và môi trường')
p11 = p('Máy chạy: laptop Windows, chỉ dùng CPU (torch bản CPU), Python ' + R['python'] + ', scikit-learn ' + R['sklearn'] + '. Toàn bộ phân tích 10 cấu hình, CV và phép kiểm nửa tốc độ mất ' + vn(R['total_script_seconds'], 0) + ' giây; script phân tích completeness (điểm corpus từ parquet + đo âm học từ WAV) mất ' + vn(C_['seconds'], 0) + ' giây; ba hình vẽ chạy ngay sau đó — cả ba trong lần chạy có ảnh Terminal ở Phụ lục. Embedding wav2vec 2.0 dùng lại bản trích sẵn của báo cáo tuần 10.')
p11.paragraph_format.keep_together = True

h('Phụ lục. Minh chứng chạy thật')
figure('terminal_week11_run_win.png', 16.0, 'Hình 4.', 'Ảnh chụp cửa sổ PowerShell thật khi chạy week11_analysis.py, week11_completeness.py và make_figure_week11.py lúc ' + RUN + '. Mọi số trong báo cáo lấy từ lần chạy này.')
p('Gói minh chứng Group05_Week11_Attachments.zip (code tuần 11, kết quả JSON/log, dự đoán từng câu test, ba hình, ảnh Terminal, audio năm câu sai nặng nhất, README hướng dẫn chạy lại) được nhúng dưới đây vào file Group05_Week11_Report.docx. Trên Word cho Windows, nháy đúp vào biểu tượng rồi chọn Open.')
p('[[OBJECTS]]', align=WD_ALIGN_PARAGRAPH.LEFT)
link('Dữ liệu speechocean762 (OpenSLR SLR101): https://www.openslr.org/101/', 'https://www.openslr.org/101/')
link('Mô hình wav2vec 2.0 base: https://huggingface.co/facebook/wav2vec2-base', 'https://huggingface.co/facebook/wav2vec2-base')

foot = sec.footer.paragraphs[0]; foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
fr = foot.add_run('Nhóm 05 · Tuần 11 · Trang '); fr.font.size = Pt(9)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); foot._p.append(fld)
for root in (D.styles.element, D.element, sec.footer._element):
    for c in root.iter(qn('w:color')):
        c.attrib.clear(); c.set(qn('w:val'), '000000')
    for f in root.iter(qn('w:rFonts')):
        f.attrib.clear()
        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'): f.set(qn('w:' + k), 'Times New Roman')
for para in D.paragraphs: para.paragraph_format.line_spacing = 1.5
for s in D.styles:
    if s.type == 1:
        rp = s.element.get_or_add_rPr(); f = rp.find(qn('w:rFonts'))
        if f is None: f = OxmlElement('w:rFonts'); rp.insert(0, f)
        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'): f.set(qn('w:' + k), 'Times New Roman')
import sys
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'report_before_embed.docx'
D.save(out); print(out)
