from pathlib import Path
import json, datetime
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

# Bao cao Tuan 10: kieu trinh bay rieng (khung ket qua chinh, tieu de co gach chan, bang ba duong ke, hai hinh canh nhau).
# Moi so lay tu week10_results.json, w2v_run.json va figure_stats.json.
P = Path(__file__).parent
R = json.loads((P/'week10_results.json').read_text()); FS = json.loads((P/'figure_stats.json').read_text())
_t = datetime.datetime.fromtimestamp((P/'week10_run.log').stat().st_mtime)
RUN = _t.strftime('%H:%M')+' ngày '+str(_t.day)+'/'+str(_t.month)+'/'+str(_t.year)
M, W2, B6 = R['models'], R['w2v'], R['below6']
T = lambda k: M[k]['test']
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
pct = lambda v: f'{v*100:.0f}%'
num = lambda n: f'{n:,}'.replace(',', '.')
sgn = lambda v, n: ('+' if v > 0 else '−' if v < 0 else '')+vn(abs(v), n)

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
D.core_properties.title = 'Báo cáo tuần 10 về chấm điểm phát âm'; D.core_properties.author = 'Nhóm 05'

def border(el, edges, sz, color='000000'):
    b = OxmlElement('w:pBdr' if el.tag == qn('w:pPr') else 'w:tcBorders')
    for e in edges:
        x = OxmlElement('w:'+e); x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), str(sz)); x.set(qn('w:space'), '1'); x.set(qn('w:color'), color); b.append(x)
    el.append(b)
def p(text='', style=None, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
    para = D.add_paragraph(text, style); para.alignment = align; return para
def lead(label, text):
    para = p(); para.add_run(label+' ').bold = True; para.add_run(text); return para
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
        x = OxmlElement('w:'+e)
        if e in edges: x.set(qn('w:val'), 'single'); x.set(qn('w:sz'), str(sz)); x.set(qn('w:color'), '000000')
        else: x.set(qn('w:val'), 'nil')
        b.append(x)
    tc.append(b)
    if fill: s = OxmlElement('w:shd'); s.set(qn('w:val'), 'clear'); s.set(qn('w:fill'), fill); tc.append(s)
    m = OxmlElement('w:tcMar')
    for e in ['top', 'bottom', 'left', 'right']:
        x = OxmlElement('w:'+e); x.set(qn('w:w'), str(mar)); x.set(qn('w:type'), 'dxa'); m.append(x)
    tc.append(m)
def booktabs(headers, rows, widths, num_from=1):
    # Bang ba duong ke: ke day tren, ke mong duoi tieu de, ke day cuoi bang; khong ke doc.
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
            edges = (['top', 'bottom'] if ri == 0 else []) + (['bottom'] if ri == n-1 else [])
            cell_fmt(c, widths[ci], edges, 12 if ri == n-1 or ri == 0 else 0)
            if ri == 0:  # duong duoi tieu de mong hon
                for x in c._tc.tcPr.find(qn('w:tcBorders')):
                    if x.tag == qn('w:bottom'): x.set(qn('w:sz'), '6')
                    if x.tag == qn('w:top'): x.set(qn('w:sz'), '12')
            for para in c.paragraphs:
                para.paragraph_format.line_spacing = 1.5; para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.keep_with_next = ri < n-1
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER if ci >= num_from else WD_ALIGN_PARAGRAPH.LEFT
                for r in para.runs: r.font.size = Pt(10.5); r.bold = ri == 0
    sp = p(); sp.paragraph_format.space_after = Pt(0)
    rpr = OxmlElement('w:rPr'); sz = OxmlElement('w:sz'); sz.set(qn('w:val'), '8'); rpr.append(sz); sp._p.get_or_add_pPr().append(rpr)
    return t
def caption(para_or_cell, label, text):
    c = para_or_cell.add_paragraph(style='Caption') if hasattr(para_or_cell, 'add_paragraph') and not hasattr(para_or_cell, 'add_heading') else p(style='Caption')
    c.alignment = WD_ALIGN_PARAGRAPH.LEFT; c.paragraph_format.line_spacing = 1.5
    r = c.add_run(label+' '); r.bold = True; r.italic = False; c.add_run(text); return c
def figure(name, width, label, text):
    para = p(align=WD_ALIGN_PARAGRAPH.CENTER); para.paragraph_format.keep_with_next = True; para.paragraph_format.space_after = Pt(0)
    para.add_run().add_picture(str(P/name), width=Cm(width)); caption(D, label, text)
def figure_pair(left, right):
    t = D.add_table(rows=1, cols=2); t.autofit = False; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for c, (name, label, text) in zip(t.rows[0].cells, [left, right]):
        cell_fmt(c, 8.3, mar=40); para = c.paragraphs[0]; para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        para.paragraph_format.line_spacing = 1.5; para.paragraph_format.space_after = Pt(0)
        para.add_run().add_picture(str(P/name), width=Cm(8.0)); caption(c, label, text)
    t.rows[0]._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))

# ---- Dau trang ----
V9 = json.loads((P.parent/'week09_work'/'verified_results.json').read_text())['agreement']['total']
PI = R['pilot']; SEC = R['secondary_mean_target']; SP = R['speakers']; AG = R['ages']; RT_ = R['raters']; TC = R['target_check']
_today = datetime.date.today()
top = p('NHÓM 05  ·  LỚP 61FIT4MLA  ·  NGÀY '+f'{_today.day:02d}/{_today.month:02d}/{_today.year}', align=WD_ALIGN_PARAGRAPH.LEFT)
top.runs[0].font.size = Pt(10); top.paragraph_format.space_after = Pt(0)
tt = p('Báo cáo tiến độ Tuần 10', align=WD_ALIGN_PARAGRAPH.LEFT); tt.runs[0].font.size = Pt(20); tt.runs[0].bold = True
tt.paragraph_format.space_after = Pt(0)
st = p('Tìm đúng những bài đọc giáo viên cần nghe lại', align=WD_ALIGN_PARAGRAPH.LEFT); st.runs[0].italic = True; st.runs[0].font.size = Pt(13)
border(st._p.get_or_add_pPr(), ['bottom'], 12); st.paragraph_format.space_after = Pt(8)

w, l, d0, c0 = T('SVR wav2vec 2.0'), T('SVR log-mel'), T('SVR chỉ độ dài'), T('Ngẫu nhiên / hằng số')
nl, lr = T('SVR log-mel bỏ độ dài'), T('LR phân loại cân bằng')
box = D.add_table(rows=1, cols=1); box.alignment = WD_TABLE_ALIGNMENT.CENTER; bc = box.rows[0].cells[0]
cell_fmt(bc, 16.6, ['left'], 36, 'F2F2F2', 140)
bp = bc.paragraphs[0]; bp.add_run('Kết quả chính tuần này').bold = True; bp.paragraph_format.line_spacing = 1.5
for k, s in [('1.', 'Total trong scores.json đúng bằng trung vị năm điểm làm tròn xuống ('+num(TC['floor_median'])+'/'+num(TC['n'])+' câu). Target chính chuyển sang total này.'),
             ('2.', 'Nghe lại 20% bài có điểm dự đoán thấp nhất: SVR log-mel bắt được '+pct(l['recall20'])+' bài dưới 6, wav2vec 2.0 được '+pct(w['recall20'])+', chọn ngẫu nhiên chỉ '+pct(c0['recall20'])+'.'),
             ('3.', 'Chỉ hai đặc trưng độ dài câu đã đạt '+pct(d0['recall20'])+'; bỏ độ dài thì log-mel tụt còn '+pct(nl['recall20'])+'. Phần lớn tín hiệu của log-mel đến từ tốc độ đọc.'),
             ('4.', 'Đổi cách học (trọng số, phân loại cân bằng) chỉ thêm tối đa '+f"{(max(T(k)['recall20'] for k in ['SVR log-mel + trọng số','LR phân loại cân bằng','RF phân loại cân bằng'])-l['recall20'])*100:.0f}"+' điểm %; đổi đặc trưng thêm '+f"{(w['recall20']-l['recall20'])*100:.0f}"+' điểm %. Nhóm đề xuất hướng đặc trưng làm thí nghiệm chính.')]:
    q = bc.add_paragraph(); q.paragraph_format.line_spacing = 1.5; q.paragraph_format.space_after = Pt(0)
    q.paragraph_format.left_indent = Cm(0.6); q.paragraph_format.first_line_indent = Cm(-0.6); q.add_run(k+'\t'+s)
    q.paragraph_format.tab_stops.add_tab_stop(Cm(0.6))
sp = p(); sp.paragraph_format.space_after = Pt(0)

h('1. Giáo viên có 35 bài đọc: nghe bài nào trước?')
p('Bài toán giữ nguyên: dự đoán điểm phát âm tổng mức câu trên speechocean762 để giáo viên ưu tiên nghe lại những bài điểm thấp. Công cụ chỉ sắp thứ tự ưu tiên; giáo viên vẫn tự nghe và quyết định phản hồi. Điểm tổng không cho biết học viên sai âm nào. Bảng dưới đối chiếu các mục thầy yêu cầu sửa sau tuần 9.')
booktabs(['Mục thầy yêu cầu', 'Trạng thái', 'Ở đâu'], [
    ['1. Kiểm tra target là trung vị', 'Đã làm; đổi target chính', 'Mục 2'],
    ['2. Chỉ số theo ngân sách nghe lại', 'Đã làm', 'Mục 4'],
    ['3. Chọn tham số bằng CV theo người nói', 'Đã làm (GroupKFold 5 phần)', 'Mục 3'],
    ['4. Tách phần đóng góp của độ dài câu', 'Đã làm', 'Mục 5'],
    ['5. Đặt hạn cho GOP', 'Đã quyết định bỏ GOP', 'Mục 7'],
    ['6. Sửa định dạng tiêu đề', 'Đã sửa; tiêu đề không còn ký hiệu thừa', 'Toàn bài']], [6.6, 6.6, 3.4], num_from=2)

h('2. Dữ liệu, giám khảo và cách tạo target')
p('speechocean762 có 5.000 câu tiếng Anh đọc thành tiếng của 250 người nói tiếng Quan Thoại, mỗi câu do năm giám khảo chấm (CC BY 4.0). Tuần 9 đã tính độ đồng thuận cho điểm total: PCC cặp trung bình '+vn(V9[0], 3)+', ICC(1,1) = '+vn(V9[1], 3)+', ICC(1,5) = '+vn(V9[2], 3)+'.')
booktabs(['So total trong scores.json với', 'Số câu khớp / 5.000'], [
    ['Trung vị năm điểm, làm tròn xuống', num(TC['floor_median'])], ['Trung vị năm điểm, làm tròn gần nhất', num(TC['round_median'])],
    ['Trung vị năm điểm, giữ nguyên', num(TC['median_exact'])], ['Trung bình năm điểm', num(TC['mean_exact'])]], [11.0, 5.6])
lead('Quyết định target.', 'Trung vị làm tròn xuống khớp cả '+num(TC['floor_median'])+'/'+num(TC['n'])+' câu, nên từ tuần 10 target chính là total trong scores.json, giống các nghiên cứu khác dùng bộ dữ liệu này. Trung bình năm điểm giữ làm phân tích phụ: với target đó, recall@20% của SVR log-mel là '+pct(SEC['SVR log-mel']['recall20'])+' và của SVR wav2vec 2.0 là '+pct(SEC['SVR wav2vec 2.0']['recall20'])+', cùng xu hướng với target chính.')
p('“Bài dưới 6” là bài có total nhỏ hơn 6. Tập train (125 người) có '+str(B6['train125'][0])+'/'+num(B6['train125'][1])+' bài dưới 6; tập test có '+str(B6['test'][0])+'/'+num(B6['test'][1])+' bài, tỉ lệ nền '+vn(R['base_rate_test']*100, 1)+'%. Top 10% của test là 250 bài, ít hơn '+str(B6['test'][0])+', nên recall@10% tối đa là '+pct(R['max_recall10'])+'.')

h('3. Chia theo người nói và chọn tham số bằng CV')
p('Giữ 125 người test chính thức, chỉ chạy test một lần. Tuần 9 chọn tham số trên 25 người validation và được PCC 0,87 nhưng test chỉ 0,59. Tuần này bỏ tập validation riêng: chọn tham số bằng GroupKFold 5 phần theo người nói trên cả 125 người train, rồi huấn luyện lại trên toàn bộ train.')
gs, gr = M['SVR log-mel']['grid'], M['RF log-mel']['grid']
booktabs(['Tham số', 'MAE CV (TB ± SD)', 'Recall@20% CV (TB ± SD)'],
         [['SVR, C = '+vn(c['C'], 1 if c['C'] < 1 else 0)+(' (chọn)' if c == M['SVR log-mel']['config'] else ''), vn(r['MAE'][0], 3)+' ± '+vn(r['MAE'][1], 3), pct(r['recall20'][0])+' ± '+pct(r['recall20'][1])] for c, r in gs] +
         [['RF, min_samples_leaf = '+str(c['min_samples_leaf'])+(' (chọn)' if c == M['RF log-mel']['config'] else ''), vn(r['MAE'][0], 3)+' ± '+vn(r['MAE'][1], 3), pct(r['recall20'][0])+' ± '+pct(r['recall20'][1])] for c, r in gr],
         [7.0, 4.8, 4.8])
p('SVR và RF chọn theo MAE CV thấp nhất. Các biến thể nhằm vào bài điểm thấp (trọng số, phân loại) chọn theo recall@20% CV; wav2vec 2.0 chọn tầng và C theo MAE CV (tầng '+str(M['SVR wav2vec 2.0']['config']['layer'])+', C = '+str(M['SVR wav2vec 2.0']['config']['C'])+'). Độ lệch chuẩn giữa các fold khoảng 0,08–0,10 điểm MAE, lớn hơn chênh lệch giữa các giá trị C, nên khác biệt giữa các tham số này là nhỏ.')

h('4. Kết quả theo ngân sách nghe lại')
lab = {'Ngẫu nhiên / hằng số': 'Ngẫu nhiên (hằng số)', 'SVR log-mel': 'SVR log-mel', 'RF log-mel': 'RF log-mel', 'SVR chỉ độ dài': 'SVR chỉ độ dài',
       'SVR log-mel bỏ độ dài': 'SVR log-mel bỏ độ dài', 'SVR log-mel + trọng số': 'SVR log-mel + trọng số', 'LR phân loại cân bằng': 'LR phân loại cân bằng',
       'RF phân loại cân bằng': 'RF phân loại cân bằng', 'SVR wav2vec 2.0': 'SVR wav2vec 2.0'}
booktabs(['Mô hình (test, 2.500 câu)', 'R@10%', 'P@10%', 'R@20%', 'P@20%', 'MAE', 'PCC'],
         [[lab[k], pct(T(k)['recall10']), pct(T(k)['precision10']), pct(T(k)['recall20']), pct(T(k)['precision20']),
           vn(T(k)['MAE'], 3) if 'MAE' in T(k) else '—', '—' if T(k).get('PCC') is None else vn(T(k)['PCC'], 3)] for k in lab], [5.2, 1.9, 1.9, 1.9, 1.9, 1.9, 1.9])
p('R@k: tỉ lệ trong '+str(B6['test'][0])+' bài dưới 6 nằm trong k% bài có điểm dự đoán thấp nhất. P@k: tỉ lệ bài thật sự dưới 6 trong k% đó; chọn ngẫu nhiên thì P@k bằng tỉ lệ nền '+vn(R['base_rate_test']*100, 1)+'%. Mô hình phân loại xếp theo xác suất “dưới 6” nên không có MAE.')
figure('fig1_recall.png', 15.5, 'Hình 1.', 'Recall bài dưới 6 trên test: chấm rỗng khi nghe lại 10% bài thấp nhất, chấm đặc khi nghe lại 20%. Xanh dương: log-mel; xanh lục: chỉ độ dài; cam: wav2vec 2.0; xám: ngẫu nhiên.')
cv = FS['curve_listen30']; bb = FS['bias_by_bin']
figure_pair(('fig2_curve.png', 'Hình 2.', 'Nghe lại x% bài có điểm dự đoán thấp nhất thì bắt được bao nhiêu % bài dưới 6 (test).'),
            ('fig3_bias.png', 'Hình 3.', 'Độ lệch trung bình (dự đoán − thật) theo điểm thật trên test; n là số câu.'))
p('Nếu giáo viên chỉ nghe được 10% số bài, con số cần xem là P@10% và R@10%: với SVR wav2vec 2.0, '+pct(w['precision10'])+' bài được nghe thật sự dưới 6 (ngẫu nhiên '+pct(c0['precision10'])+') và bắt được '+pct(w['recall10'])+' tổng số bài dưới 6. Công cụ tìm bài kém nhanh hơn chọn ngẫu nhiên khoảng '+f"{w['precision10']/c0['precision10']:.0f}"+' lần nhưng vẫn bỏ sót gần một nửa. Ở mức 10% các mô hình gần như ngang nhau; khác biệt rõ từ 15–30%: nghe 30% thì wav2vec 2.0 bắt được '+f"{cv['w2v']:.0f}"+'%, log-mel '+f"{cv['logmel']:.0f}"+'%, chỉ độ dài '+f"{cv['length']:.0f}"+'% (Hình 2).')
lead('Dồn về giữa thang điểm.', 'Hình 3 cho thấy bài điểm thấp bị đoán cao hơn thật, bài điểm cao bị đoán thấp hơn thật. Với '+str(bb['counts'][0])+' câu test có total từ 4 trở xuống, log-mel đoán cao hơn '+vn(bb['SVR log-mel'][0], 2)+' điểm, wav2vec 2.0 còn '+vn(bb['SVR wav2vec 2.0'][0], 2)+' điểm.')

h('5. Độ dài câu đóng góp bao nhiêu?')
p('Câu đọc là đề bài giáo viên giao nên số từ biết trước. SVR chỉ dùng hai đặc trưng, độ dài audio và độ dài chia số từ (giây/từ), đạt recall@20% = '+pct(d0['recall20'])+' và MAE = '+vn(d0['MAE'], 3)+', ngang hoặc hơn log-mel đầy đủ ('+pct(l['recall20'])+', MAE '+vn(l['MAE'], 3)+'). Bỏ độ dài khỏi log-mel thì recall@20% tụt còn '+pct(nl['recall20'])+' và MAE tăng lên '+vn(nl['MAE'], 3)+'. Vậy phần lớn khả năng của log-mel đến từ tốc độ đọc: người đọc chậm, ngập ngừng thường bị chấm thấp. Phần còn lại của log-mel, chủ yếu mô tả âm sắc và điều kiện thu âm, chỉ thêm được ít. Đây là giới hạn quan trọng: một mô hình dựa vào tốc độ sẽ bỏ sót người đọc nhanh nhưng phát âm sai.')

h('6. Thí nghiệm sửa: đặc trưng hay cách học?')
lead('Hướng cách học (giữ log-mel).', 'SVR có trọng số α = '+str(M['SVR log-mel + trọng số']['config']['alpha'])+' cho bài dưới 6 đạt recall@20% = '+pct(T('SVR log-mel + trọng số')['recall20'])+'; LR phân loại cân bằng lớp đạt '+pct(lr['recall20'])+' (tốt nhất ở mức 10%: R@10% = '+pct(lr['recall10'])+'); RF phân loại cân bằng đạt '+pct(T('RF phân loại cân bằng')['recall20'])+'. So với SVR log-mel ('+pct(l['recall20'])+'), cách học chỉ thêm vài điểm %.')
lead('Hướng đặc trưng.', 'Embedding wav2vec 2.0 base huấn luyện sẵn, không fine-tune, lấy trung bình theo câu ở tầng 4, 8 hoặc 12, đưa vào SVR. Kết quả: recall@20% = '+pct(w['recall20'])+', MAE = '+vn(w['MAE'], 3)+', PCC = '+vn(w['PCC'], 2)+' — tốt nhất trên mọi chỉ số. Vẫn còn dồn về giữa, nhưng ít hơn log-mel.')
booktabs(['Đo thời gian wav2vec 2.0 (máy chạy lần này)', 'CPU'], [
    ['Chạy thử '+str(PI['n'])+' câu ('+f"{PI['audio_seconds']:.0f}"+' giây audio)', vn(PI['cpu']['seconds'], 1)+' giây · '+f"{PI['cpu']['ms_per_utt']:.0f}"+' ms/câu'],
    ['Ước tính cho 5.000 câu', vn(PI['cpu']['estimate_5000_minutes'], 1)+' phút'],
    ['Chạy thật 5.000 câu ('+vn(W2['audio_hours'], 2)+' giờ audio)', f"{W2['extract_seconds']:.0f} giây ≈ {W2['extract_seconds']/60:.0f} phút"]], [7.4, 9.2])
base = 'Chạy thử 50 câu trước khi chạy cả 5.000 câu. Lần chạy này chỉ đo CPU (máy Windows, không dùng GPU). '
base += 'Lần chạy thật 5.000 câu mất lâu hơn ước tính từ 50 câu, vì máy còn chạy các việc khác và độ dài câu khác nhau. Phân tích và huấn luyện 9 mô hình với CV mất '+vn(R['total_script_seconds'], 0)+' giây.'
p(base)
lead('Đề xuất.', 'Chọn hướng đặc trưng làm thí nghiệm chính cho tuần 11: thêm '+f"{(w['recall20']-l['recall20'])*100:.0f}"+' điểm % recall@20% với chi phí khoảng '+f"{W2['extract_seconds']/60:.0f}"+' phút CPU một lần. Hướng cách học giữ làm so sánh phụ, có thể kết hợp LR cân bằng lớp với embedding wav2vec 2.0.')

h('7. GOP: quyết định ngày 21/10/2026')
p('Link đặc trưng GOP trích sẵn của tác giả GOPT vẫn bị Dropbox khoá (“Link Temporarily Disabled”, kiểm tra lúc 09:57 ngày 21/10/2026, cuối tuần 10). Theo hạn thầy đặt, nhóm bỏ GOP khỏi kế hoạch trước buổi thuyết trình và dùng embedding wav2vec 2.0. Nếu cả hai hướng đều không kéo recall lên đủ, kết luận vẫn có giá trị: đặc trưng mức câu chưa đủ để nhận ra bài đọc kém, cần đặc trưng gắn với từng âm như GOP.')

h('8. Sai số theo người nói và nhóm tuổi')
a, b = SP['SVR log-mel'], SP['SVR wav2vec 2.0']
p('Trên 125 người nói test, MAE theo người nói của SVR log-mel có trung vị '+vn(a['median_MAE'], 2)+', cao nhất '+vn(a['max_MAE'], 2)+'; '+str(a['top_n'])+' người kém nhất (10%) chiếm '+pct(a['top_share'])+' tổng sai số. MAE theo người nói tương quan mạnh với điểm trung bình của người đó (r = '+vn(SP['corr_mae_meantarget'], 2)+'): lỗi dồn vào người đọc kém. wav2vec 2.0 giảm trung vị còn '+vn(b['median_MAE'], 2)+'.')
figure('fig4_speakers.png', 15.5, 'Hình 4.', 'MAE theo từng người nói test, tách theo nhóm tuổi. Vạch đen là trung vị, chấm xám là người nói có sai số bất thường.')
p('Người lớn có '+str(AG['adult']['below6'])+' bài dưới 6, trẻ em có '+str(AG['child']['below6'])+'. wav2vec 2.0 giảm sai số rõ ở người lớn ('+vn(AG['adult']['MAE_logmel'], 2)+' → '+vn(AG['adult']['MAE_w2v'], 2)+') hơn ở trẻ em ('+vn(AG['child']['MAE_logmel'], 2)+' → '+vn(AG['child']['MAE_w2v'], 2)+'), có thể vì wav2vec 2.0 base được huấn luyện trên giọng đọc của người lớn; nhóm chưa kiểm chứng.')

h('9. Năm câu bị đoán sai nặng nhất')
p('Đây là năm câu có total dưới 6 mà SVR log-mel đoán cao hơn thật nhiều nhất. Audio của cả năm câu có trong gói minh chứng (thư mục worst5).')
booktabs(['Mã câu', 'Câu đọc', 'Năm điểm', 'Total', 'Log-mel', 'wav2vec', 'Giây'],
         [[x['id'], x['text'], ' · '.join(vn(v, 0) if v == int(v) else vn(v, 1) for v in x['five']), vn(x['total'], 0), vn(x['pred_logmel'], 1), vn(x['pred_w2v'], 1), vn(x['duration'], 1)] for x in R['worst5']],
         [2.2, 5.6, 3.2, 1.3, 1.5, 1.6, 1.2], num_from=2)
lead('Ghi chú khi nghe.', 'Nhóm sẽ nghe trực tiếp năm câu này và ghi lại trước buổi gặp thầy; báo cáo không tự suy diễn nội dung audio. Các con số đã cho thấy: cả năm câu đều bị cả năm giám khảo chấm rất thấp nhưng mô hình vẫn đoán khoảng 7 điểm.')

h('10. Chuẩn bị vấn đáp')
lead('Vì sao hồi quy với đặc trưng yếu kéo dự đoán về gần trung bình?', 'Mô hình học cách giảm sai số trung bình. Khi đặc trưng không phân biệt rõ bài tốt và bài kém, dự đoán an toàn nhất là gần điểm trung bình; bài dưới 6 chỉ chiếm '+vn(B6['train125'][0]/B6['train125'][1]*100, 0)+'% tập train nên bị kéo về giữa mà sai số chung tăng không nhiều (Hình 3).')
lead('Nếu chỉ nghe được 10% số bài, con số nào cho biết công cụ có đáng dùng?', 'P@10% và R@10% (Mục 4): '+pct(w['precision10'])+' bài được nghe thật sự kém, so với '+pct(c0['precision10'])+' khi chọn ngẫu nhiên; bắt được '+pct(w['recall10'])+' số bài kém.')
ex = RT_['example']
lead('Khi một giám khảo chấm lệch hẳn bốn người còn lại, trung bình và trung vị phản ứng thế nào?', 'Trung bình bị kéo theo người chấm lệch, trung vị gần như không đổi. Có '+str(RT_['n_odd3'])+' câu có một giám khảo lệch từ 3 điểm trở lên so với trung vị bốn người còn lại; ở các câu đó, trung bình và trung vị cách nhau trung bình '+vn(RT_['mean_shift_odd'], 2)+' điểm, gấp đôi mức '+vn(RT_['mean_shift_all'], 2)+' trên toàn bộ dữ liệu. Ví dụ câu '+ex['id']+': năm điểm '+'; '.join(vn(v, 1) for v in ex['five'])+' cho trung bình '+vn(ex['mean'], 2)+' nhưng trung vị '+vn(ex['median'], 1)+'. Đây là một lý do total dùng trung vị.')
lead('Giới hạn.', 'Người nói có tiếng mẹ đẻ Quan Thoại, gồm cả trẻ em; bài đọc thành tiếng câu ngắn; công cụ chưa chẩn đoán từng âm và chưa có bằng chứng dùng tốt cho người học Việt Nam.')

h('11. Thời gian chạy và CPU/GPU')
p('Máy chạy: laptop Windows với GPU NVIDIA RTX 2050 (không dùng trong lần chạy này — torch bản CPU); Python '+R['python']+', PyTorch '+W2['torch'].replace('+cpu', ' (bản CPU)')+', transformers '+W2['transformers']+', scikit-learn '+R['sklearn']+'. Trích wav2vec 2.0 cho 5.000 câu khoảng '+f"{W2['extract_seconds']/60:.0f}"+' phút, phân tích và CV '+vn(R['total_script_seconds'], 0)+' giây. Dự kiến, chưa đo: chỉ cần GPU nếu fine-tune wav2vec 2.0 hoặc dùng mô hình lớn hơn.')

h('Phụ lục. Minh chứng chạy thật')
figure('terminal_w2v_extract_win.png', 12, 'Hình 5.', 'Ảnh chụp cửa sổ Terminal thật khi trích embedding wav2vec 2.0 cho 5.000 câu trên CPU.')
figure('terminal_pilot_win.png', 13, 'Hình 6.', 'Ảnh chụp cửa sổ Terminal thật khi chạy pilot_w2v.py trên 50 câu ở máy chạy lần này.')
figure('terminal_run_win.png', 13.5, 'Hình 7.', 'Ảnh chụp cửa sổ Terminal thật khi chạy week10_analysis.py và make_figure_week10.py lúc '+RUN+'. Mọi số trong báo cáo lấy từ lần chạy này.')
p('Gói minh chứng (code, đặc trưng log-mel, dự đoán từng câu test, kết quả CV, sai số theo người nói, audio năm câu sai nặng nhất, log, ảnh chụp và README hướng dẫn chạy lại) được nhúng dưới đây. Trên Word cho Windows, nháy đúp vào biểu tượng rồi chọn Open.')
p('[[OBJECTS]]', align=WD_ALIGN_PARAGRAPH.LEFT)
link('Dữ liệu speechocean762 (OpenSLR SLR101): https://www.openslr.org/101/', 'https://www.openslr.org/101/')
link('Mô hình wav2vec 2.0 base: https://huggingface.co/facebook/wav2vec2-base', 'https://huggingface.co/facebook/wav2vec2-base')

foot = sec.footer.paragraphs[0]; foot.alignment = WD_ALIGN_PARAGRAPH.RIGHT
fr = foot.add_run('Nhóm 05 · Tuần 10 · Trang '); fr.font.size = Pt(9)
fld = OxmlElement('w:fldSimple'); fld.set(qn('w:instr'), 'PAGE'); foot._p.append(fld)
for root in (D.styles.element, D.element, sec.footer._element):
    for c in root.iter(qn('w:color')):
        c.attrib.clear(); c.set(qn('w:val'), '000000')
    for f in root.iter(qn('w:rFonts')):
        f.attrib.clear()
        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'): f.set(qn('w:'+k), 'Times New Roman')
for para in D.paragraphs: para.paragraph_format.line_spacing = 1.5
for s in D.styles:
    if s.type == 1:
        rp = s.element.get_or_add_rPr(); f = rp.find(qn('w:rFonts'))
        if f is None: f = OxmlElement('w:rFonts'); rp.insert(0, f)
        for k in ('ascii', 'hAnsi', 'eastAsia', 'cs'): f.set(qn('w:'+k), 'Times New Roman')
import sys
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent/'Group05_Week10_Report.docx'
D.save(out); print(out)
