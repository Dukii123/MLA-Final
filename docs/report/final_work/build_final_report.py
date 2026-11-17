# -*- coding: utf-8 -*-
# Báo cáo cuối kỳ MLA — Nhóm 05. Cấu trúc research-paper theo
# MLA_FinalProject_Requirements_and_Rubric: Tóm tắt & Giới thiệu; Dữ liệu và Phương pháp;
# Thiết lập thí nghiệm; Kết quả và Phân tích lỗi; Thảo luận và Kết luận; Tài liệu tham khảo + Phụ lục
# (run table, experiment matrix, đóng góp cá nhân, AI disclosure, hướng dẫn chạy lại).
# Mọi số lấy từ week11_results.json + week11_completeness.json (lần chạy 11:16 ngày 9/11/2026, có ảnh Terminal).
import json, sys, datetime
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

P = Path(__file__).parent
W = P.parent / 'week11_work'
for req in ['week11_results.json', 'week11_completeness.json', 'final_contributions.json', 'final_data_checks.json']:
    if not (P / req).exists() and not (W / req).exists():
        sys.exit(f'THIEU FILE BAT BUOC: {req} — dung file nay truoc khi build (xem plan final report).')
R = json.loads((W / 'week11_results.json').read_text(encoding='utf-8'))
C_ = json.loads((W / 'week11_completeness.json').read_text(encoding='utf-8'))
Q = json.loads((P / 'final_data_checks.json').read_text(encoding='utf-8'))
NOTES = json.loads((W / 'listening_notes.json').read_text(encoding='utf-8-sig'))
FC = json.loads((P / 'final_contributions.json').read_text(encoding='utf-8-sig'))
CZ, L2, W5C = C_['compl_zero'], C_['low_total2'], C_['worst5']
_t = datetime.datetime.fromtimestamp((W / 'week11_run.log').stat().st_mtime)
RUN = _t.strftime('%H:%M') + ' ngày ' + f'{_t.day}/{_t.month}/{_t.year}'
_today = datetime.date.today()
RUN_DATE = f'{_today.day:02d}/{_today.month:02d}/{_today.year}'
M, CVT, H, LT, B6 = R['models'], R['cv_table'], R['halves'], R['low_total'], R['below6']
TC, RT_ = R['target_check'], R['raters']
note = lambda uid, who: str(NOTES.get(uid, {}).get(who, '')).strip()
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
D.core_properties.title = 'Báo cáo cuối kỳ — chấm điểm phát âm và xếp hạng nghe lại'; D.core_properties.author = 'Nhóm 05'

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
    para.add_run().add_picture(str(W / name), width=Cm(width)); caption(D, label, text)

# ---------- Số dùng nhiều ----------
w = T('SVR wav2vec 2.0'); lrw = T('LR phân loại cân bằng (wav2vec)')
cvw = CVT['SVR wav2vec 2.0']['recall20']; cvd = CVT['SVR chỉ độ dài']['recall20']
N_SEL = int(round(0.20 * B6['test'][1])); N_LOW = B6['test'][0]
N_CAUGHT = int(round(w['recall20'] * N_LOW)); P_CAUGHT = int(round(w['precision20'] * N_SEL))
wv_mean, wl_mean = CZ['mean_pred_logmel'], CZ['mean_pred_w2v']
fast, slow = H['fast'], H['slow']
ex = RT_['example']

# ---------- Đầu trang ----------
top = p('NHÓM 05  ·  LỚP 61FIT4MLA  ·  BÁO CÁO CUỐI KỲ  ·  NGÀY ' + RUN_DATE, align=WD_ALIGN_PARAGRAPH.LEFT)
top.runs[0].font.size = Pt(10); top.paragraph_format.space_after = Pt(0)
tt = p('Dự đoán điểm phát âm mức câu để xếp thứ tự ưu tiên nghe lại', align=WD_ALIGN_PARAGRAPH.LEFT)
tt.runs[0].font.size = Pt(19); tt.runs[0].bold = True; tt.paragraph_format.space_after = Pt(0)
st = p('speechocean762 · SVR trên embedding wav2vec 2.0 · so sánh công bằng theo ngân sách nghe', align=WD_ALIGN_PARAGRAPH.LEFT)
st.runs[0].italic = True; st.runs[0].font.size = Pt(13)
border(st._p.get_or_add_pPr(), ['bottom'], 12); st.paragraph_format.space_after = Pt(8)

# ---------- 1. Tóm tắt và Giới thiệu ----------
h('1. Tóm tắt và giới thiệu')
lead('Câu hỏi.', 'Cho một bài đọc thành tiếng mới, hệ thống có thể xếp thứ tự các bài theo mức cần nghe lại để giáo viên, với ngân sách nghe hữu hạn (ví dụ 20% số bài), bắt được nhiều nhất các bài thật sự kém (total dưới 6)? Đây là bài toán xếp thứ tự để ưu tiên nghe lại, không phải chấm điểm chính thức.')
lead('Người dùng và thời điểm dự đoán.', 'Người dùng là giáo viên tiếng Anh phụ trách lớp luyện đọc thành tiếng. Sau khi người học nộp bài đọc (file audio), hệ thống trích đặc trưng từ chính file audio đó và trả về một điểm dự đoán kèm thứ hạng ưu tiên. Mọi đặc trưng đều chỉ dùng thông tin có trong audio tại thời điểm dự đoán (độ dài, thống kê log-mel, embedding wav2vec 2.0); không dùng điểm giám khảo.')
lead('Dữ liệu và phạm vi.', 'speechocean762 (OpenSLR SLR101, CC BY 4.0): 5.000 câu tiếng Anh đọc thành tiếng của 250 người nói tiếng Quan Thoại (có trẻ em), mỗi câu được 5 giám khảo chấm. Mọi kết luận chỉ áp dụng cho kiểu dữ liệu này; bài báo không khẳng định hiệu quả cho người học Việt Nam.')
lead('Kết quả chính.', 'SVR trên embedding wav2vec 2.0 (đóng băng, tầng 8, 768 chiều) đạt recall@20% trên test ' + pct(w['recall20']) + ' (' + str(N_CAUGHT) + '/' + str(N_LOW) + ' bài dưới 6), so với ' + pct(T('SVR chỉ độ dài')['recall20']) + ' của mô hình chỉ dùng tốc độ đọc và ' + pct(T('Ngẫu nhiên / hằng số')['recall20']) + ' của chọn ngẫu nhiên; MAE ' + vn(w['MAE'], 3) + '. Với ngân sách nghe 20% (500 bài), precision ' + pct(w['precision20']) + ' — còn ' + str(N_LOW - N_CAUGHT) + ' bài dưới 6 bị bỏ sót, nên công cụ chỉ xếp thứ tự việc nghe, không thay giáo viên.')
lead('Hạn chế chính.', 'Mô hình dồn dự đoán về giữa thang: nhóm 12 câu total ≤ 2 bị đoán trung bình khoảng 7 (Mục 4), đặc trưng mức câu không nhìn thấy phần nội dung thiếu (completeness = 0); hệ thống không chẩn đoán được lỗi từng âm (chưa có GOP).')

# ---------- 2. Dữ liệu và Phương pháp ----------
h('2. Dữ liệu và phương pháp')
lead('Nguồn và điều kiện sử dụng.', 'speechocean762 (Zhang và cộng sự, Interspeech 2021), CC BY 4.0, tải từ https://www.openslr.org/101/. Không thu giọng Việt Nam (đã bỏ theo góp ý giữa kỳ).')
lead('Một bản ghi và nhãn.', 'Một bản ghi là một câu đọc: một mã câu, một người nói, một câu chữ cố định, một file WAV 16 kHz mono, và năm giám khảo độc lập chấm riêng từng từ. Điểm câu gồm accuracy, fluency, prosodic (0–10) và completeness (tỉ lệ từ đọc tốt, thang 0–1 giãn ×10 — dữ liệu thực đo được 0,00–10,00). Nhãn total của corpus bằng làm tròn xuống trung vị năm điểm giám khảo: khớp ' + num(TC['floor_median']) + '/5.000 câu (trung vị làm tròn gần nhất chỉ khớp ' + num(TC['round_median']) + ', trung bình ' + num(TC['mean_exact']) + '). Ví dụ câu ' + ex['id'] + ': năm điểm ' + '; '.join(vn(v, 1) for v in ex['five']) + ' — trung bình ' + vn(ex['mean'], 2) + ' nhưng total đúng là ' + vn(ex['total'], 0) + ' bằng trung vị ' + vn(ex['median'], 1) + ': một giám khảo chấm lệch không được kéo điểm câu xuống. Có ' + str(RT_['n_odd3']) + ' câu lệch kiểu này (một giám khảo chênh ≥ 3 điểm); ở đó trung bình và trung vị cách nhau ' + vn(RT_['mean_shift_odd'], 2) + ' điểm, gấp đôi mức ' + vn(RT_['mean_shift_all'], 2) + ' toàn dữ liệu.')
lead('Phép chia.', 'Chia theo người nói: 125 người train / 125 người test (2.500 + 2.500 câu, không trộn người); chọn tham số bằng GroupKFold 5 phần theo người nói trên train. Test có ' + str(N_LOW) + '/2.500 bài dưới 6 (tỉ lệ nền ' + vn(R['base_rate_test'] * 100, 1) + '%).')
AG = R['ages']
lead('Phân bố và chất lượng dữ liệu.', 'Tuổi: ' + str(AG['child']['speakers']) + ' trẻ em (' + num(AG['child']['utterances']) + ' câu, ' + str(AG['child']['below6']) + ' dưới 6) và ' + str(AG['adult']['speakers']) + ' người lớn (' + num(AG['adult']['utterances']) + ' câu, ' + str(AG['adult']['below6']) + ' dưới 6) — trẻ em chiếm khoảng ' + vn(AG['child']['utterances'] / (AG['child']['utterances'] + AG['adult']['utterances']) * 100, 0) + '% số câu. Kiểm tra chất lượng bổ sung (script + log trong zip minh chứng, chạy ngày 11/11): không có giá trị thiếu trong các trường điểm mức câu của cả ' + num(Q['n_utterances']) + ' câu, và mỗi câu đều đủ 5 lượt chấm của 5 giám khảo cho cả 4 chỉ số; ' + num(Q['duplicates']['n_distinct_ids']) + ' mã câu duy nhất, ' + num(Q['duplicates']['n_distinct_texts']) + ' câu chữ khác nhau — ' + str(Q['duplicates']['n_texts_repeated']) + ' câu chữ xuất hiện 2 lần do người nói khác đọc, không có cặp (người nói, câu chữ) nào trùng nên mỗi người chỉ đọc mỗi câu một lần.')
lead('Ba bộ đặc trưng.', 'Chỉ độ dài: thời gian đọc và giây/từ (2). Log-mel: 40 dải log-mel (khung 25 ms, bước 10 ms), lấy trung bình và độ lệch chuẩn theo thời gian của từng dải cộng độ dài câu (81). Wav2vec 2.0: facebook/wav2vec2-base tiền huấn luyện, đóng băng, trung bình theo thời gian của tầng 8 embedding (768).')
lead('Họ mô hình và mô hình tham chiếu.', 'Ba họ: máy vector hỗ trợ (SVR, kernel RBF, loss epsilon-insensitive ε = 0,1), rừng ngẫu nhiên (RF, 300 cây, seed 42), và hồi quy logistic phân loại cân bằng lớp (linear, loss cross-entropy). Mô hình tham chiếu dễ hiểu là SVR chỉ độ dài — chỉ đo nhịp đọc; baseline bổ sung là chọn ngẫu nhiên/hằng số (recall kỳ vọng 20%). Huấn luyện SVR có trọng số mẫu cho bài dưới 6 trong một biến thể; LR dùng class_weight = balanced.')
lead('Tiền xử lý.', 'StandardScaler nằm trong Pipeline nên chỉ fit trên dữ liệu của từng fold huấn luyện, không rò rỉ sang fold kiểm hay test.')

# ---------- 3. Thiết lập thí nghiệm ----------
h('3. Thiết lập thí nghiệm')
lead('Tham số và chọn mô hình.', 'SVR: C ∈ {0,3; 1; 3; 10} (biến thể wav2vec: 3 tầng embedding × C ∈ {1; 3; 10}); RF: min_samples_leaf ∈ {1; 5; 20}, 300 cây; LR: C ∈ {0,01; 0,1; 1}. Biến thể trọng số chọn C bằng với SVR log-mel tốt nhất rồi quét alpha ∈ {2; 4; 8} theo recall@20%. Tiêu chí chọn là recall@20% trung bình qua 5 fold GroupKFold theo người nói (MAE cho nhóm hồi quy, recall@20% cho phân loại). RF dùng seed 42; SVR và LR tất định; GroupKFold không trộn nên phép chia tái lập được từ split_manifest.csv.')
lead('Độ đo.', 'Recall@20%: số bài dưới 6 nằm trong 20% bài có điểm dự đoán thấp nhất chia tổng số bài dưới 6 của test; precision@20% đối ứng; MAE để đo mức độ dồn điểm. Cùng mẫu số, cùng ngân sách nghe giữa các mô hình.')
lead('Lịch sử dùng test.', 'Test chỉ chạy một lần cho mỗi cấu hình sau khi chốt tham số bằng CV; mọi quyết định (chọn đặc trưng, chọn giữa hồi quy và phân loại) đều đọc cột CV. Không có bước nào chọn mô hình theo điểm test.')

# ---------- 4. Kết quả và phân tích lỗi ----------
h('4. Kết quả và phân tích lỗi')
lead('So sánh công bằng.', 'Bảng 1 đặt cột CV và test cạnh nhau cho mọi cấu hình; khoảng cách CV–test cho biết CV lạc quan bao nhiêu. Độ lệch chuẩn giữa các fold 9–13 điểm %, nên chênh lệch nhỏ không đáng tin.')
order = ['SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài', 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số', 'LR phân loại cân bằng',
         'RF phân loại cân bằng', 'SVR wav2vec 2.0', 'SVR wav2vec + độ dài', 'LR phân loại cân bằng (wav2vec)']
rows = []
for k in order:
    c, t = CVT[k], T(k)
    rows.append([k, pct(c['recall20'][0]) + ' ± ' + vn(c['recall20'][1] * 100, 0), (vn(c['MAE'][0], 3) + ' ± ' + vn(c['MAE'][1], 3)) if c['MAE'] else '—',
                 pct(t['recall20']), vn(t['MAE'], 3) if 'MAE' in t else '—'])
rows.append(['Ngẫu nhiên / hằng số', '—', '—', pct(T('Ngẫu nhiên / hằng số')['recall20']), vn(T('Ngẫu nhiên / hằng số')['MAE'], 3)])
booktabs(['Mô hình', 'R@20% CV (TB ± SD)', 'MAE CV (TB ± SD)', 'R@20% test', 'MAE test'], rows, [4.8, 3.0, 2.8, 2.4, 2.2], size=9.5)
caption(D, 'Bảng 1.', 'Bảng so sánh công bằng trên cùng split và ngân sách nghe; quyết định chọn mô hình đọc theo cột CV.')
p('Theo cột CV, SVR wav2vec 2.0 tốt nhất nhóm hồi quy (' + pct(cvw[0]) + ' ± ' + vn(cvw[1] * 100, 0) + ', MAE ' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + '); trên test đạt ' + pct(w['recall20']) + ' (' + str(N_CAUGHT) + '/' + str(N_LOW) + ', precision ' + str(P_CAUGHT) + '/' + str(N_SEL) + ' = ' + pct(w['precision20']) + '). Thêm hai đặc trưng độ dài vào wav2vec gần như không đổi (CV ' + pct(CVT['SVR wav2vec + độ dài']['recall20'][0]) + ', MAE ' + vn(CVT['SVR wav2vec + độ dài']['MAE'][0], 3) + ' so với ' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + ') — embedding đã chứa thông tin độ dài. LR cân bằng lớp có CV ' + pct(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]) + ' nhưng test ' + pct(lrw['recall20']) + ' so với ' + pct(w['recall20']) + '; chênh nằm trong sai số giữa các fold nên nhóm giữ SVR (cho điểm liên tục và test cao hơn).')
figure('fig1_cv_test.png', 15.5, 'Hình 1.', 'Recall@20% trên CV (chấm rỗng, thanh độ lệch chuẩn 5 fold) và trên test (chấm đặc) cho mọi cấu hình.')
lead('Kiểm tra có kiểm soát 1 — log-mel còn gì ngoài tốc độ đọc?', 'Bỏ hai đặc trưng độ dài khỏi log-mel: CV giảm từ ' + pct(CVT['SVR log-mel']['recall20'][0]) + ' xuống ' + pct(CVT['SVR log-mel bỏ độ dài']['recall20'][0]) + ' (test 67% → 53%) — gần hết khả năng của log-mel là tốc độ đọc.')
lead('Kiểm tra có kiểm soát 2 — wav2vec hơn nhờ tốc độ?', 'Chia test thành hai nửa theo trung vị giây/từ (' + vn(H['threshold_sec_per_word'], 2) + '). wav2vec hơn chỉ-độ-dài ở cả hai nửa (nhanh ' + pct(fast['recall20']['w2v']) + ' so với ' + pct(fast['recall20']['length']) + '; chậm ' + pct(slow['recall20']['w2v']) + ' so với ' + pct(slow['recall20']['length']) + ') nên phần vượt trội không chỉ là tốc độ; nửa nhanh chỉ có ' + str(fast['n_below6']) + ' bài dưới 6 nên sai số lớn, nửa chậm (' + str(slow['n_below6']) + ' bài) mới đáng tin.')
figure('fig2_halves.png', 11.0, 'Hình 2.', 'Recall@20% trong nửa đọc nhanh và nửa đọc chậm.')
lead('Phân tích lỗi — nhóm bài rất kém.', 'Quy tắc chọn: toàn bộ ' + str(LT['n']) + ' câu test có total ≤ 2. Chỉ ' + str(C_['n_zero_in_low12']) + '/' + str(LT['n']) + ' câu có completeness = 0 (thiếu nội dung); phần còn lại completeness 1,7–10,0 (đọc đủ/sai nặng). Cả nhóm đều bị các mô hình đoán 6,3–7,5 — mô hình tối thiểu hoá sai số trung bình nên bài rất kém bị nén về giữa thang (bài dưới 6 bị wav2vec đoán cao hơn thật trung bình ' + sgn(w['bias_low'], 2) + ' điểm).')
booktabs(['Mã câu', 'Năm điểm', 'Total', 'Acc', 'Compl', 'Log-mel', 'w2v'],
         [[x['id'], five_str(x['five']), vn(x['total'], 0), vn(x['acc'], 0), vn(x['compl'], 1), vn(x['pred_logmel'], 2), vn(x['pred_w2v'], 2)] for x in L2],
         [2.1, 3.0, 1.1, 1.0, 1.3, 1.5, 1.5], num_from=2, size=8.5)
caption(D, 'Bảng 2.', 'Nhóm total ≤ 2: nhãn, completeness và dự đoán; nhóm compl = 0 chỉ có ' + str(CZ['n']) + '/' + num(CZ['n_test']) + ' câu trên toàn test, bị đoán trung bình ' + vn(wv_mean, 2) + ' (log-mel) và ' + vn(wl_mean, 2) + ' (wav2vec).')
lead('Năm câu sai nặng nhất — đã nghe thật.', 'Quy tắc chọn: năm câu total < 6 mà SVR log-mel đoán cao hơn thật nhiều nhất. Hai người nghe độc lập đã nghe cả năm file WAV gốc; ghi chú giữ nguyên văn, không suy diễn:')
booktabs(['Mã câu', 'Nghe 1', 'Nghe 2'],
         [[x['id'], note(x['id'], 'nghe1'), note(x['id'], 'nghe2')] for x in W5C],
         [2.4, 7.1, 7.1], num_from=1, size=9.0)
caption(D, 'Bảng 3.', 'Ghi chú nghe 5 câu worst5 (hai người độc lập) đối chiếu với số đo tự động (Bảng 4): 3 câu đầu đọc lạc đề (completeness 0,0–1,7); 2 câu cuối không có tiếng đọc — chỉ tiếng gõ, khớp RMS thấp và tỉ lệ khung có năng lượng rất nhỏ.')
lead('Số đo âm học tự động trên file WAV.', 'Biên độ đỉnh, RMS theo dBFS và tỉ lệ khung 25 ms có năng lượng đáng chú ý (ngưỡng = 8% mức RMS của khung có năng lượng lớn nhất). Đây là số tự động, không thay cho phần nghe của con người:')
booktabs(['Mã câu', 'Biên độ đỉnh', 'RMS (dBFS)', 'Khung có năng lượng', 'Giây'],
         [[x['id'], vn(x['acoustic']['peak'], 2), vn(x['acoustic']['rms_dbfs'], 1), vn(x['acoustic']['pct_frames'], 0) + '%', vn(x['acoustic']['duration_s'], 1)] for x in W5C],
         [2.4, 2.5, 2.3, 3.4, 1.6], num_from=1, size=9.0)
caption(D, 'Bảng 4.', 'Số đo âm học tự động của 5 câu worst5 (script week11_completeness.py, lần chạy ' + RUN + ').')
p('Kết luận từ bằng chứng: lỗi nặng nhất gồm hai loại — đọc lạc đề và không có tiếng đọc — mà đặc trưng mức câu không phân biệt được; đây là lý do recall@20% không thể đạt 100% và vì sao công cụ chỉ nên xếp thứ tự nghe lại. Để bắt các lỗi này tự động cần đặc trưng theo nội dung (ASR/alignment, GOP).')

# ---------- 5. Thảo luận và kết luận ----------
h('5. Thảo luận và kết luận')
lead('Trả lời được.', 'Với ngân sách nghe 20%, xếp theo điểm dự đoán bắt được ' + str(N_CAUGHT) + '/' + str(N_LOW) + ' bài dưới 6 (' + pct(w['recall20']) + ') so với 20% ngẫu nhiên và ' + pct(T('SVR chỉ độ dài')['recall20']) + ' chỉ nhờ tốc độ; phần vượt trội ' + vn((w['recall20'] - T('SVR chỉ độ dài')['recall20']) * 100, 0) + ' điểm % của wav2vec có kiểm chứng không phải là tốc độ đọc (Hình 2). Chọn đặc trưng quan trọng hơn chọn cách học: đổi SVR → RF/LR không đổi thứ hạng.')
lead('Chưa trả lời được.', 'Không chẩn đoán lỗi từng âm (cần GOP/alignment); chưa chứng minh cho người học ngoài tiếng Quan Thoại (dữ liệu 250 người Quan Thoại, có trẻ em, đọc câu ngắn); ' + str(N_LOW - N_CAUGHT) + ' bài dưới 6 vẫn lọt khỏi danh sách 20%; bài rất kém bị nén về giữa thang nên điểm dự đoán không dùng làm điểm thật.')
lead('So với nguồn đọc.', 'speechocean762 (Zhang và cộng sự, 2021) công bố corpus và chuẩn chấm; báo cáo dùng đúng target corpus (total = floor median, kiểm 5.000/5.000) và kiểm tra lại độc lập. wav2vec 2.0 (Baevski và cộng sự, 2020) được dùng đúng tinh thần "tiền huấn luyện trên tiếng nói, đóng băng, chỉ huấn luyện đầu đọc điểm".')
lead('Khuyến nghị trong phạm vi.', 'Dùng công cụ như bộ xếp hạng ưu tiên nghe lại cho giáo viên (precision 51% ở ngân sách 20%); đi kèm audio để giáo viên tự xác nhận; bước tiếp theo hợp lý là GOP hoặc ASR để phân biệt đọc lạc đề và thiếu nội dung — hai loại lỗi đã nghe thấy ở Mục 4.')

# ---------- 6. Tài liệu tham khảo + Phụ lục ----------
h('6. Tài liệu tham khảo')
link('Zhang và cộng sự (2021), speechocean762 (OpenSLR SLR101), CC BY 4.0: https://www.openslr.org/101/', 'https://www.openslr.org/101/')
link('Baevski và cộng sự (2020), wav2vec 2.0 base, Apache 2.0: https://huggingface.co/facebook/wav2vec2-base', 'https://huggingface.co/facebook/wav2vec2-base')
h('Phụ lục A. Lịch sử lần chạy và ma trận thí nghiệm')
booktabs(['Lần chạy', 'Máy / thời điểm', 'Nội dung', 'Ghi chú'],
         [['Mac', '21/10/2026 10:09', 'Tuần 10: extract w2v, analysis, báo cáo tuần 10', 'Kết quả cũ, chỉ tham chiếu'],
          ['Windows', '24–25/10/2026', 'Chạy lại tuần 10 trên máy Windows', 'Số trùng Mac'],
          ['Windows', '09/11/2026 11:16', 'Tuần 11: analysis 253 s + completeness 1 s + 3 hình', 'Mọi số mô hình và completeness lấy từ lần chạy này (Hình 3)'],
          ['Windows', '11/11/2026 ' + Q['checked_at'][:5], 'Kiểm tra chất lượng dữ liệu bổ sung: missingness, duplicates (final_data_checks.py)', 'Script + JSON + log trong zip minh chứng']],
         [1.8, 3.6, 6.6, 4.4], num_from=2, size=9.0)
booktabs(['Câu hỏi', 'Thay đổi / cấu hình', 'Metric — output', 'Quyết định'],
         [['Nhãn nào là target?', 'So 3 cách tính trên 5.000 câu', 'Số câu khớp: floor median 5.000', 'Dùng floor median; không học trung bình'],
          ['Log-mel hơn độ dài nhờ gì?', 'SVR log-mel bỏ 2 đặc trưng độ dài', 'R@20% CV 70% ± 11 (test 53%)', 'Gần hết log-mel là tốc độ đọc'],
          ['wav2vec thêm gì ngoài tốc độ?', 'SVR w2v + độ dài; kiểm nửa nhanh/chậm', 'CV 80% ± 10, MAE 0,795; nửa nhanh 78% vs 50%', 'Có phần âm học khác tốc độ; giữ w2v'],
          ['Phân loại có hơn hồi quy?', 'LR cân bằng lớp trên w2v', 'CV 80% ± 8; test 74% vs 77%', 'Không đủ căn cứ đổi; giữ SVR'],
          ['Mô hình xử lý bài rất kém thế nào?', 'Nhóm compl = 0 + 12 câu total ≤ 2', 'Đoán trung bình ~7 cho cả nhóm', 'Điểm chỉ để xếp thứ tự; đã nghe 5 câu worst5']],
         [3.6, 4.6, 4.4, 3.8], num_from=0, size=9.0)
caption(D, 'Bảng 5.', 'Ma trận thí nghiệm: mỗi hàng một câu hỏi, thay đổi có kiểm soát, số đo và quyết định sau khi đọc kết quả (đúng yêu cầu "experiment matrix" của rubric).')
p('Môi trường lần chạy chính thức: laptop Windows, CPU only (torch bản CPU), Python ' + R['python'] + ', scikit-learn ' + R['sklearn'] + ', matplotlib 3.11.2, pyarrow 26.0.0. Embedding wav2vec trích sẵn tuần 10 (5.000 câu, khoảng 5 giờ CPU), dùng lại không trích lại.')

h('Phụ lục B. Đóng góp cá nhân và sử dụng AI')
for mem in FC['members']:
    lead(str(mem.get('name', '')) + (' (' + str(mem['student_id']) + ')' if mem.get('student_id') else '') + ':', '; '.join(mem['contributions']))
lead('Sử dụng AI.', FC.get('ai_summary', ''))
for ai in FC.get('ai_use', []):
    p('• ' + ai.get('tool', '') + ' — ' + ai.get('purpose', '') + ' Kiểm chứng: ' + ai.get('checked', ''))

h('Phụ lục C. Tái lập kết quả')
p('Gói minh chứng Group05_Final_Evidence.zip (code, JSON/log, dự đoán từng câu test, split_manifest.csv, ba hình, ảnh Terminal, audio 5 câu worst5, ghi chú nghe, đóng góp nhóm, README hướng dẫn chạy lại) được nhúng dưới đây vào file Group05_Final_Report.docx. Trên Word cho Windows, nháy đúp vào biểu tượng rồi chọn Open. Cách chạy lại tóm tắt: python week11_analysis.py <speechocean762> → python week11_completeness.py <parquet> → python make_figure_week11.py; chi tiết trong README của zip.')
p('[[OBJECTS]]', align=WD_ALIGN_PARAGRAPH.LEFT)
figure('terminal_week11_run_win.png', 16.0, 'Hình 3.', 'Ảnh chụp cửa sổ PowerShell thật khi chạy week11_analysis.py, week11_completeness.py và make_figure_week11.py lúc ' + RUN + '. Mọi số trong báo cáo lấy từ lần chạy này.')

foot = sec.footer.paragraphs[0]; foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
fr = foot.add_run('Nhóm 05 · Báo cáo cuối kỳ · Trang '); fr.font.size = Pt(9)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); foot._p.append(fld)
for root in (D.styles.element, D.element, sec.footer._element):
    for c in root.iter(qn('w:color')):
        c.attrib.clear(); c.set(qn('w:val'), '000000')
    for f in root.iter(qn('w:rFonts')):
        f.attrib.clear()
        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'): f.set(qn('w:' + k), 'Times New Roman')
for para in D.paragraphs: para.paragraph_format.line_spacing = 1.5
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P / 'report_before_embed.docx'
D.save(out); print(out)
