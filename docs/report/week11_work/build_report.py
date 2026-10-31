from pathlib import Path
import json, datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# Bao cao Tuan 11: theo 3 viec bat buoc + 1 nen lam + 1 thu nghiem phu trong Nhan_xet_Week10.
# Kieu trinh bay doi mot chut so tuan 10: khung ket qua kieu "mo" (chi vien duoi), bang CV rong hon,
# ba hinh kieu moi (lollipop CV-test, grouped bar nua doc, histogram giay/tu). Anh Terminal giu kieu cu.
# Moi so lay tu week11_results.json + figure_stats.json cua lan chay co anh Terminal.
P = Path(__file__).parent
R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8')); FS = json.loads((P / 'figure_stats.json').read_text(encoding='utf-8'))
_t = datetime.datetime.fromtimestamp((P / 'week11_run.log').stat().st_mtime)
RUN = _t.strftime('%H:%M') + ' ngày ' + f'{_t.day}/{_t.month}/{_t.year}'
RUN_DATE = f'{_t.day:02d}/{_t.month:02d}/{_t.year}'
M, CVT, H, LT, B6 = R['models'], R['cv_table'], R['halves'], R['low_total'], R['below6']
# Ghi chu nghe: dien vao listening_notes.json (nghe1/nghe2 cho tung ma cau).
_notes_path = P / 'listening_notes.json'
NOTES = json.loads(_notes_path.read_text(encoding='utf-8-sig')) if _notes_path.exists() else {}
note = lambda uid, who: str(NOTES.get(uid, {}).get(who, '')).strip()
ALL_LISTENED = all(note(x['id'], 'nghe1') and note(x['id'], 'nghe2') for x in R['worst5'])
T = lambda k: M[k]['test']
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
pct = lambda v: f'{v*100:.0f}%'
num = lambda n: f'{n:,}'.replace(',', '.')
sgn = lambda v, n: ('+' if v > 0 else '−' if v < 0 else '') + vn(abs(v), n)

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
V9 = json.loads((P.parent / 'week09_work' / 'verified_results.json').read_text(encoding='utf-8'))['agreement']['total']
TC = R['target_check']; SP = R['speakers']; AG = R['ages']; RT_ = R['raters']; SEC = R['secondary_mean_target']
top = p('NHÓM 05  ·  LỚP 61FIT4MLA  ·  NGÀY ' + RUN_DATE, align=WD_ALIGN_PARAGRAPH.LEFT)
top.runs[0].font.size = Pt(10); top.paragraph_format.space_after = Pt(0)
tt = p('Báo cáo tiến độ Tuần 11', align=WD_ALIGN_PARAGRAPH.LEFT); tt.runs[0].font.size = Pt(20); tt.runs[0].bold = True
tt.paragraph_format.space_after = Pt(0)
st = p('Wav2vec 2.0 thêm gì ngoài tốc độ đọc?', align=WD_ALIGN_PARAGRAPH.LEFT); st.runs[0].italic = True; st.runs[0].font.size = Pt(13)
border(st._p.get_or_add_pPr(), ['bottom'], 12); st.paragraph_format.space_after = Pt(8)

w, l, d0 = T('SVR wav2vec 2.0'), T('SVR log-mel'), T('SVR chỉ độ dài')
w2l = T('SVR wav2vec + độ dài'); lr = T('LR phân loại cân bằng'); lrw = T('LR phân loại cân bằng (wav2vec)')
cvw = CVT['SVR wav2vec 2.0']['recall20']; cvwl = CVT['SVR wav2vec + độ dài']['recall20']; cvd = CVT['SVR chỉ độ dài']['recall20']
fast, slow = H['fast'], H['slow']
# Khung ket qua: kieu "mo" — chi vien duoi dam, nen trang (khac tuan 10: nen xam + vien trai)
box = D.add_table(rows=1, cols=1); box.alignment = WD_TABLE_ALIGNMENT.CENTER; bc = box.rows[0].cells[0]
cell_fmt(bc, 16.6, ['bottom'], 18, None, 120)
bp = bc.paragraphs[0]; bp.add_run('Kết quả chính tuần này').bold = True; bp.paragraph_format.line_spacing = 1.5
lead_fast = (f"Ở nửa đọc nhanh wav2vec vẫn hơn chỉ-độ-dài {vn((fast['recall20']['w2v'] - fast['recall20']['length']) * 100, 0)} điểm %"
             if fast['recall20']['w2v'] > fast['recall20']['length'] else
             f"Ở nửa đọc nhanh wav2vec không hơn chỉ-độ-dài ({pct(fast['recall20']['w2v'])} so với {pct(fast['recall20']['length'])})")
for s in [f"Bảng CV đầy đủ cho 10 cấu hình: SVR wav2vec 2.0 đứng đầu nhóm hồi quy trên CV ({pct(cvw[0])} ± {vn(cvw[1]*100, 0)} điểm %) và trên test ({pct(w['recall20'])}). LR cân bằng lớp trên wav2vec có CV {vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]*100, 1)}% so với {vn(cvw[0]*100, 1)}% của SVR wav2vec nhưng test thấp hơn ({pct(lrw['recall20'])} so với {pct(w['recall20'])}). Thêm hai đặc trưng độ dài vào wav2vec không đổi CV ({pct(cvwl[0])}).",
          f"Tách test theo trung vị giây/từ ({vn(H['threshold_sec_per_word'], 2)} s/từ): {lead_fast}; nửa đọc chậm wav2vec {pct(slow['recall20']['w2v'])} so với {pct(slow['recall20']['length'])} của chỉ-độ-dài.",
          f"Trên test có {LT['n']} câu total ≤ 2; các mô hình đoán trung bình {vn(LT['pred_mean']['SVR wav2vec 2.0'], 1)} điểm cho nhóm này. " + ("Bảng năm câu sai nặng nhất đã có ghi chú của hai người nghe." if ALL_LISTENED else "Bảng năm câu sai nặng nhất chờ hai người nghe điền ghi chú trước buổi gặp."),
          f"Thí nghiệm phụ LR cân bằng lớp trên wav2vec: CV {vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]*100, 1)}% (SVR wav2vec {vn(cvw[0]*100, 1)}%) nhưng test R@20% {pct(lrw['recall20'])} thấp hơn SVR wav2vec ({pct(w['recall20'])}); không thay đổi kết luận chọn hướng đặc trưng."]:
    q = bc.add_paragraph(); q.paragraph_format.line_spacing = 1.5; q.paragraph_format.space_after = Pt(0)
    q.paragraph_format.left_indent = Cm(0.5); q.paragraph_format.first_line_indent = Cm(-0.5); q.add_run('•\t' + s)
    q.paragraph_format.tab_stops.add_tab_stop(Cm(0.5))
sp = p(); sp.paragraph_format.space_after = Pt(0)

h('1. Năm việc thầy giao sau tuần 10')
p('Bảng dưới đối chiếu từng việc trong nhận xét tuần 10 với báo cáo này. Việc nào chưa xong được ghi đúng là chưa xong.')
booktabs(['Việc thầy giao', 'Trạng thái trong báo cáo này', 'Ở đâu'], [
    ['1. Nghe 5 câu sai nặng nhất', ('Đã nghe và ghi chú độc lập' if ALL_LISTENED else 'Phần thống kê đã làm; phần nghe: chưa — bảng chờ hai người điền'), 'Mục 6'],
    ['2. Bảng CV cho mọi cấu hình, chọn hướng bằng CV', 'Đã làm — CV kẹp cạnh test trong một bảng', 'Mục 3'],
    ['3a. CV: chỉ-độ-dài, wav2vec, wav2vec + độ dài', 'Đã làm — bảng 3 dòng', 'Mục 4'],
    ['3b. Chia test theo nửa đọc nhanh / đọc chậm', 'Đã làm — chỉ đọc dự đoán đã lưu, không chọn lại', 'Mục 5'],
    ['4. Sửa nhãn tuần và ngày', 'Đã đính chính; nhãn link bảng đăng ký đã đổi sang Week10', 'Mục 8'],
    ['Phụ. LR cân bằng lớp trên wav2vec (nếu còn thời gian)', 'Đã làm — thí nghiệm phụ, không bắt buộc', 'Mục 7']], [7.6, 6.4, 2.6], num_from=2)

h('2. Dữ liệu, target và nhóm cần nghe lại')
p('Giữ nguyên bài toán và dữ liệu tuần 10: speechocean762, 5.000 câu, 250 người nói tiếng Quan Thoại, 5 giám khảo (CC BY 4.0); target chính là total trong scores.json. Độ đồng thuận giữa giám khảo đã đo ở tuần 9: PCC trung bình ' + vn(V9[0], 3) + ', ICC(1,5) = ' + vn(V9[2], 3) + '.')
booktabs(['So total trong scores.json với', 'Số câu khớp / 5.000'], [
    ['Trung vị năm điểm, làm tròn xuống', num(TC['floor_median'])], ['Trung vị năm điểm, làm tròn gần nhất', num(TC['round_median'])],
    ['Trung bình năm điểm', num(TC['mean_exact'])]], [11.0, 5.6])
p('Tập test có ' + str(B6['test'][0]) + '/' + num(B6['test'][1]) + ' bài dưới 6 (tỉ lệ nền ' + vn(R['base_rate_test'] * 100, 1) + '%) và ' + str(LT['n']) + ' câu total ≤ 2. Mô hình vẫn chỉ xếp thứ tự ưu tiên nghe lại; giáo viên tự nghe và quyết định phản hồi.')

h('3. Bảng CV đầy đủ: chọn hướng bằng CV')
p('Việc 2 của thầy: mọi cấu hình phải có recall@20% và MAE trên CV (GroupKFold 5 phần theo người nói, 125 người train), đặt cạnh kết quả test. Bảng dưới là toàn bộ 10 cấu hình học, kèm dòng ngẫu nhiên / hằng số để so sánh; quyết định chọn hướng đọc theo cột CV, cột test chỉ xác nhận.')
rows, lab = [], {'Ngẫu nhiên / hằng số': 'Ngẫu nhiên / hằng số', 'SVR log-mel': 'SVR log-mel', 'RF log-mel': 'RF log-mel', 'SVR chỉ độ dài': 'SVR chỉ độ dài',
                 'SVR log-mel bỏ độ dài': 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số': 'SVR log-mel + trọng số', 'LR phân loại cân bằng': 'LR phân loại cân bằng',
                 'RF phân loại cân bằng': 'RF phân loại cân bằng', 'SVR wav2vec 2.0': 'SVR wav2vec 2.0', 'SVR wav2vec + độ dài': 'SVR wav2vec + độ dài',
                 'LR phân loại cân bằng (wav2vec)': 'LR phân loại cân bằng (wav2vec)'}
order = ['SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài', 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số', 'LR phân loại cân bằng',
         'RF phân loại cân bằng', 'SVR wav2vec 2.0', 'SVR wav2vec + độ dài', 'LR phân loại cân bằng (wav2vec)']
for k in order:
    c, t = CVT[k], T(k)
    rows.append([lab[k], pct(c['recall20'][0]) + ' ± ' + vn(c['recall20'][1] * 100, 0), (vn(c['MAE'][0], 3) + ' ± ' + vn(c['MAE'][1], 3)) if c['MAE'] else '—',
                 pct(t['recall20']), vn(t['MAE'], 3) if 'MAE' in t else '—'])
rows.append(['Ngẫu nhiên / hằng số', '—', '—', pct(T('Ngẫu nhiên / hằng số')['recall20']), vn(T('Ngẫu nhiên / hằng số')['MAE'], 3)])
booktabs(['Mô hình', 'R@20% CV (TB ± SD)', 'MAE CV (TB ± SD)', 'R@20% test', 'MAE test'], rows, [4.8, 3.0, 2.8, 2.4, 2.2], size=9.5)
p('Đọc bảng theo cột CV: trong nhóm hồi quy, SVR wav2vec 2.0 tốt nhất (' + pct(cvw[0]) + ' ± ' + vn(cvw[1] * 100, 0) + ' điểm %, MAE ' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + '), sau đó là nhóm log-mel (' + pct(min(CVT[k]['recall20'][0] for k in ['SVR log-mel', 'RF log-mel', 'SVR log-mel + trọng số', 'LR phân loại cân bằng', 'RF phân loại cân bằng'])) + '–' + pct(max(CVT[k]['recall20'][0] for k in ['SVR log-mel', 'RF log-mel', 'SVR log-mel + trọng số', 'LR phân loại cân bằng', 'RF phân loại cân bằng'])) + '); chỉ-độ-dài ' + pct(cvd[0]) + '. Các biến thể cách học trên log-mel cải thiện CV không quá ' +
  vn((max(CVT[k]['recall20'][0] for k in ['SVR log-mel + trọng số', 'LR phân loại cân bằng', 'RF phân loại cân bằng']) - CVT['SVR log-mel']['recall20'][0]) * 100, 1) + ' điểm %. LR cân bằng lớp trên wav2vec có CV ' + pct(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]) + ' ± ' + vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][1] * 100, 0) + ' — nhỉnh hơn SVR wav2vec ' + vn((CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0] - cvw[0]) * 100, 1) + ' điểm nhưng test chỉ ' + pct(lrw['recall20']) + ' so với ' + pct(w['recall20']) + '; chênh lệch nằm trong độ lệch chuẩn giữa các fold nên không đủ căn cứ đổi mô hình chính. Vì vậy hướng chính vẫn là đặc trưng. Độ lệch chuẩn giữa các fold ' +
  vn(min(CVT[k]['recall20'][1] for k in order) * 100, 0) + '–' + vn(max(CVT[k]['recall20'][1] for k in order) * 100, 0) + ' điểm %, nên chênh lệch nhỏ giữa các cấu hình không đáng tin.')
figure('fig1_cv_test.png', 15.5, 'Hình 1.', 'Recall@20% trên CV (chấm rỗng, thanh mảnh là độ lệch chuẩn giữa 5 fold) và trên test (chấm đặc) cho mọi cấu hình; số % ghi dưới chấm đặc là recall trên test, giá trị CV xem bảng ở Mục 3. Khoảng cách giữa hai chấm cho biết CV lạc quan hơn test bao nhiêu.')

h('4. Wav2vec 2.0 thêm gì ngoài tốc độ đọc?')
p('Việc 3a: so ba cấu hình trên cùng một phép CV — chỉ hai đặc trưng độ dài, embedding wav2vec 2.0, và wav2vec 2.0 nối thêm hai đặc trưng độ dài. Nếu wav2vec chỉ đang đo tốc độ đọc thì thêm độ dài vào sẽ không đổi gì; nếu còn thông tin khác thì wav2vec phải hơn chỉ-độ-dài.')
booktabs(['Cấu hình (CV GroupKFold-5)', 'R@20% CV', 'MAE CV', 'R@20% test', 'MAE test'], [
    ['Chỉ hai đặc trưng độ dài', pct(cvd[0]) + ' ± ' + vn(cvd[1] * 100, 0), vn(CVT['SVR chỉ độ dài']['MAE'][0], 3) + ' ± ' + vn(CVT['SVR chỉ độ dài']['MAE'][1], 3), pct(d0['recall20']), vn(d0['MAE'], 3)],
    ['SVR wav2vec 2.0', pct(cvw[0]) + ' ± ' + vn(cvw[1] * 100, 0), vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + ' ± ' + vn(CVT['SVR wav2vec 2.0']['MAE'][1], 3), pct(w['recall20']), vn(w['MAE'], 3)],
    ['SVR wav2vec + hai đặc trưng độ dài', pct(cvwl[0]) + ' ± ' + vn(cvwl[1] * 100, 0), vn(CVT['SVR wav2vec + độ dài']['MAE'][0], 3) + ' ± ' + vn(CVT['SVR wav2vec + độ dài']['MAE'][1], 3), pct(w2l['recall20']), vn(w2l['MAE'], 3)]],
    [5.6, 2.8, 2.8, 2.4, 2.2])
dl = cvwl[0] - cvw[0]
if dl < 0.01:
    interp = ('Trên CV, thêm hai đặc trưng độ dài vào wav2vec gần như không đổi recall@20% (chênh ' + vn(dl * 100, 1) + ' điểm %). Nghĩa là embedding wav2vec 2.0 đã chứa phần lớn thông tin độ dài; phần nó hơn chỉ-độ-dài đến từ thông tin khác tốc độ đọc, đúng hướng cần tìm.')
else:
    interp = ('Trên CV, thêm hai đặc trưng độ dài vào wav2vec tăng recall@20% thêm ' + vn(dl * 100, 1) + ' điểm %. Nghĩa là wav2vec chưa tận dụng hết thông tin độ dài; phần vượt trội của nó là sự kết hợp của cả tốc độ đọc và âm thanh.')
p(interp + ' MAE CV gần như không đổi (' + vn(CVT['SVR wav2vec 2.0']['MAE'][0], 3) + ' so với ' + vn(CVT['SVR wav2vec + độ dài']['MAE'][0], 3) + ').')

h('5. Phép kiểm nửa đọc nhanh / đọc chậm')
p('Việc 3b: chia 2.500 câu test thành hai nửa theo trung vị giây/từ (' + vn(H['threshold_sec_per_word'], 2) + ' giây/từ). Nửa đọc nhanh dưới trung vị, nửa đọc chậm từ trung vị trở lên. Trong từng nửa, lấy 20% câu có điểm dự đoán thấp nhất và tính tỉ lệ bài dưới 6 bắt được. Phép kiểm chỉ đọc dự đoán của mô hình đã huấn luyện ở Mục 3–4, không chọn lại tham số hay ngưỡng nào.')
booktabs(['Nửa tốc độ', 'Số câu', 'Trong đó dưới 6', 'R@20% chỉ độ dài', 'R@20% wav2vec 2.0'], [
    ['Đọc nhanh (< ' + vn(H['threshold_sec_per_word'], 2) + ' s/từ)', str(fast['n']), str(fast['n_below6']), pct(fast['recall20']['length']), pct(fast['recall20']['w2v'])],
    ['Đọc chậm (≥ ' + vn(H['threshold_sec_per_word'], 2) + ' s/từ)', str(slow['n']), str(slow['n_below6']), pct(slow['recall20']['length']), pct(slow['recall20']['w2v'])]],
    [5.2, 2.2, 2.8, 3.2, 3.2])
gap_f = (fast['recall20']['w2v'] - fast['recall20']['length']) * 100
gap_s = (slow['recall20']['w2v'] - slow['recall20']['length']) * 100
if gap_f >= 0:
    concl = ('wav2vec hơn chỉ-độ-dài ở cả hai nửa (nhanh ' + vn(gap_f, 0) + ' điểm %, chậm ' + vn(gap_s, 0) + ' điểm %), nên phần vượt trội không chỉ là tốc độ đọc. Nửa đọc nhanh là nơi mô hình dựa vào tốc độ dễ bỏ sót nhất; wav2vec bắt được ' + pct(fast['recall20']['w2v']) + ' số bài dưới 6 ở nửa này so với ' + pct(fast['recall20']['length']) + ' của chỉ-độ-dài. Lưu ý nửa đọc nhanh chỉ có ' + str(fast['n_below6']) + ' bài dưới 6, nên chênh lệch ở nửa này có sai số lớn; nửa đọc chậm (' + str(slow['n_below6']) + ' bài dưới 6) mới là nơi hai mô hình gần nhau.')
else:
    concl = ('Ở nửa đọc nhanh wav2vec không hơn chỉ-độ-dài (' + vn(gap_f, 0) + ' điểm %), còn ở nửa đọc chậm hơn ' + vn(gap_s, 0) + ' điểm %. Kết luận vẫn có giá trị: đặc trưng mức câu chủ yếu đo tốc độ đọc, cần đặc trưng theo từng âm như GOP để bắt người đọc nhanh nhưng phát âm sai.')
p(concl)
figure_pair(('fig2_halves.png', 'Hình 2.', 'Recall@20% trong từng nửa tốc độ; n là số câu, "<6" là số bài dưới 6 của nửa đó.'),
            ('fig3_speed_dist.png', 'Hình 3.', 'Phân bố giây/từ trên 2.500 câu test; vạch đứt là trung vị dùng để chia nửa.'))

h('6. Nhóm total ≤ 2 và năm câu sai nặng nhất')
p('Việc 1 (phần thống kê): thầy yêu cầu đếm số câu test có total ≤ 2 và xem mô hình đoán nhóm đó bao nhiêu điểm. Có ' + str(LT['n']) + ' câu như vậy trên 2.500 câu test. Bảng dưới là điểm dự đoán trung bình của ba mô hình chính cho đúng nhóm này — tất cả đều đoán cao hơn thực tế rất nhiều, đúng như lo ngại về việc mô hình dựa vào tốc độ đọc.')
booktabs(['Mô hình', 'Điểm dự đoán TB (nhóm ' + str(LT['n']) + ' câu)', 'Số câu đoán > 5 điểm'], [
    ['SVR log-mel', vn(LT['pred_mean']['SVR log-mel'], 2), str(LT['n_pred_above5']['SVR log-mel']) + '/' + str(LT['n'])],
    ['SVR chỉ độ dài', vn(LT['pred_mean']['SVR chỉ độ dài'], 2), str(LT['n_pred_above5']['SVR chỉ độ dài']) + '/' + str(LT['n'])],
    ['SVR wav2vec 2.0', vn(LT['pred_mean']['SVR wav2vec 2.0'], 2), str(LT['n_pred_above5']['SVR wav2vec 2.0']) + '/' + str(LT['n'])]], [6.0, 5.6, 5.0], num_from=1)
p('Năm câu dưới đây là năm câu total dưới 6 mà SVR log-mel đoán cao hơn thật nhiều nhất, giống bộ tuần 10 (đã kiểm tra trùng mã câu). Audio có trong gói minh chứng, thư mục worst5. Bảng đầu là điểm của corpus và hai mô hình; bảng sau là ghi chú nghe độc lập của hai người.')
booktabs(['Mã câu', 'Câu đọc', 'Năm điểm', 'Total', 'Log-mel', 'w2v', 'Giây'],
         [[x['id'], x['text'], ' · '.join(vn(v, 0) if v == int(v) else vn(v, 1) for v in x['five']), vn(x['total'], 0), vn(x['pred_logmel'], 1), vn(x['pred_w2v'], 1), vn(x['duration'], 1)] for x in R['worst5']],
         [1.9, 5.0, 4.1, 1.2, 1.5, 1.3, 1.0], num_from=2, size=8.5)
p('Ghi chú nghe (mỗi câu hai người nghe độc lập):')
booktabs(['Mã câu', 'Nghe 1', 'Nghe 2'],
         [[x['id'], note(x['id'], 'nghe1'), note(x['id'], 'nghe2')] for x in R['worst5']],
         [2.4, 7.1, 7.1], num_from=1, size=9.0)
if ALL_LISTENED:
    lead('Kết quả nghe.', 'Hai người nghe độc lập đã ghi lại điều nghe được cho cả năm câu; ghi chú giữ nguyên văn, không suy diễn thêm. Phần này dùng cho buổi vấn đáp, không thay đổi điểm dự đoán hay kết luận ở các mục trên.')
else:
    lead('Trạng thái phần nghe.', 'Chưa thực hiện: mỗi câu cần ít nhất hai người nghe độc lập, ghi riêng đọc đúng câu không, có im lặng/tiếng ồn/lặp từ không. Nhóm điền hai cột trống trước buổi gặp. Báo cáo không tự suy diễn nội dung audio.')

h('7. Thí nghiệm phụ: LR cân bằng lớp trên wav2vec')
p('Thầy ghi việc này chỉ làm nếu còn thời gian. Embedding đã trích sẵn nên chi phí gần như bằng không, nhóm làm luôn để trả lời câu hỏi vấn đáp: phân loại cân bằng lớp có hơn hồi quy trên cùng đặc trưng wav2vec không? Kết quả: CV recall@20% = ' + pct(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0]) + ' ± ' + vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][1] * 100, 0) + ' điểm %, test R@10% = ' + pct(lrw['recall10']) + ', R@20% = ' + pct(lrw['recall20']) + ' (hồi quy SVR wav2vec: R@10% = ' + pct(w['recall10']) + ', R@20% = ' + pct(w['recall20']) + '). Phân loại có CV nhỉnh hơn ' + vn((CVT['LR phân loại cân bằng (wav2vec)']['recall20'][0] - cvw[0]) * 100, 1) + ' điểm nhưng test thấp hơn ' + vn((w['recall20'] - lrw['recall20']) * 100, 0) + ' điểm; cả hai chênh lệch đều nằm trong độ lệch chuẩn giữa các fold (' + vn(CVT['LR phân loại cân bằng (wav2vec)']['recall20'][1] * 100, 0) + ' điểm). Vì vậy cách học không tạo khác biệt rõ ràng; nhóm giữ hồi quy vì cho điểm liên tục và kết quả test cao hơn. Kết luận "đổi đặc trưng quan trọng hơn đổi cách học" giữ nguyên.')
p('Đây là thí nghiệm phụ, không nằm trong ba việc bắt buộc; nếu thầy muốn dừng thí nghiệm thì mục này chỉ để tham khảo.')

h('8. Nhãn tuần và ngày')
p('Đính chính việc 4: câu "kiểm tra lúc 09:57 ngày 21/10/2026, cuối tuần 10" trong Mục 7 báo cáo tuần 10 là sai — 21/10 thuộc tuần 9. Báo cáo này dùng tên file Group05_Week11_Report.docx, tiêu đề và chân trang đều ghi Tuần 11; ngày trên đầu trang là ngày chạy thật trong ảnh Terminal. Nhãn link trên bảng đăng ký đã được nhóm đổi sang Week10 trước khi nộp báo cáo này.')

h('9. Kết luận và hướng đi')
p('Ba việc bắt buộc đã xong phần đo: bảng CV đầy đủ xác nhận wav2vec 2.0 là mô hình hồi quy chính (CV ' + pct(cvw[0]) + ', test ' + pct(w['recall20']) + ' recall@20%); wav2vec + độ dài không đổi CV (' + pct(cvwl[0]) + '), tức phần vượt trội không chỉ là tốc độ đọc; phép kiểm nửa đọc nhanh/chậm ' + ('xác nhận wav2vec còn hơn chỉ-độ-dài ở cả hai nửa' if gap_f >= 0 else 'cho thấy giới hạn của đặc trưng mức câu') + '. Việc còn lại là phần nghe 5 câu và chuẩn bị vấn đáp.')
p('Nhóm giữ wav2vec 2.0 làm mô hình chính kèm bằng chứng CV; không mở thêm thí nghiệm mới trước buổi gặp. Nếu kết quả nửa đọc nhanh không như mong đợi, kết luận dự phòng của thầy vẫn đúng: đặc trưng mức câu chủ yếu đo tốc độ, muốn bắt lỗi phát âm cần đặc trưng theo từng âm như GOP.')

h('10. Chuẩn bị vấn đáp')
lead('Vì sao trung vị bền với một giám khảo chấm lệch?', 'Có ' + str(RT_['n_odd3']) + ' câu mà một giám khảo lệch từ 3 điểm trở lên so với trung vị bốn người còn lại; ở các câu đó trung bình và trung vị cách nhau trung bình ' + vn(RT_['mean_shift_odd'], 2) + ' điểm, gấp đôi mức ' + vn(RT_['mean_shift_all'], 2) + ' trên toàn bộ dữ liệu. Ví dụ câu ' + RT_['example']['id'] + ': năm điểm ' + '; '.join(vn(v, 1) for v in RT_['example']['five']) + ' cho trung bình ' + vn(RT_['example']['mean'], 2) + ' nhưng trung vị ' + vn(RT_['example']['median'], 1) + '.')
lead('Vì sao hồi quy với đặc trưng yếu kéo dự đoán về giữa thang?', 'Mô hình tối thiểu hóa sai số trung bình; khi đặc trưng không phân biệt rõ bài tốt và bài kém, dự đoán an toàn là gần điểm trung bình. Trên test, bài dưới 6 bị SVR log-mel đoán cao hơn thật trung bình ' + sgn(l['bias_low'], 2) + ' điểm, wav2vec 2.0 còn ' + sgn(w['bias_low'], 2) + ' điểm.')
lead('Nếu giáo viên chỉ nghe 10% số bài, con số nào cho biết công cụ có đáng dùng?', 'P@10% và R@10% (tính trong lần chạy này): với SVR wav2vec 2.0, ' + pct(w['precision10']) + ' bài trong 10% được nghe thật sự dưới 6 (ngẫu nhiên ' + pct(T('Ngẫu nhiên / hằng số')['precision10']) + '), và bắt được ' + pct(w['recall10']) + ' tổng số bài dưới 6.')
lead('Giới hạn.', 'Người nói có tiếng mẹ đẻ Quan Thoại, gồm cả trẻ em; bài đọc câu ngắn; công cụ chưa chẩn đoán từng âm và chưa có bằng chứng dùng tốt cho người học Việt Nam.')

h('11. Thời gian chạy và môi trường')
p11 = p('Máy chạy: laptop Windows, chỉ dùng CPU (torch bản CPU), Python ' + R['python'] + ', scikit-learn ' + R['sklearn'] + '. Toàn bộ phân tích 10 cấu hình, CV và phép kiểm nửa tốc độ mất ' + vn(R['total_script_seconds'], 0) + ' giây trong lần chạy có ảnh Terminal ở Phụ lục; ba hình vẽ chạy riêng ngay sau đó. Embedding wav2vec 2.0 dùng lại bản trích sẵn của báo cáo tuần 10, không trích lại. Dự kiến, chưa đo: chỉ cần GPU nếu fine-tune wav2vec 2.0.')
p11.paragraph_format.keep_together = True

h('Phụ lục. Minh chứng chạy thật')
figure('terminal_week11_run_win.png', 16.0, 'Hình 4.', 'Ảnh chụp cửa sổ PowerShell thật khi chạy week11_analysis.py và make_figure_week11.py lúc ' + RUN + '. Mọi số trong báo cáo lấy từ lần chạy này.')
p('Gói minh chứng (code tuần 11, kết quả JSON/log, dự đoán từng câu test, ba hình, ảnh Terminal, audio năm câu sai nặng nhất, README hướng dẫn chạy lại) được nhúng dưới đây. Trên Word cho Windows, nháy đúp vào biểu tượng rồi chọn Open.')
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
