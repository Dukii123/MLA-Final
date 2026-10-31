from pathlib import Path
import json
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT

P=Path(__file__).parent
R=json.loads((P/'verified_results.json').read_text())
RUN=R['date'][11:16]+' ngày '+str(int(R['date'][8:10]))+'/'+str(int(R['date'][5:7]))+'/'+R['date'][:4]
def vn(x,n): return f'{x:.{n}f}'.replace('.',',')
D=Document()
sec=D.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=sec.bottom_margin=Cm(1.7)
sec.left_margin=sec.right_margin=Cm(2)
for s in D.styles:
 if s.type in (1,2):
  s.font.name='Times New Roman'; s.font.color.rgb=RGBColor(0,0,0)
  s._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'),'Times New Roman')
for name in ['Normal','Body Text','Caption','Title','Subtitle','Heading 1','Heading 2']:
 s=D.styles[name];s.font.name='Times New Roman';s.font.color.rgb=RGBColor(0,0,0)
 s.paragraph_format.line_spacing=1.5
 s.paragraph_format.space_after=Pt(4)
D.styles['Normal'].font.size=Pt(12)
for name,size in [('Title',17),('Subtitle',11),('Heading 1',13),('Heading 2',12),('Caption',10)]:
 D.styles[name].font.size=Pt(size)
 D.styles[name].paragraph_format.space_before=Pt(5)
 D.styles[name].font.bold=name.startswith('Heading') or name=='Title'
D.core_properties.title='Báo cáo tiến độ tuần 9 về chấm điểm phát âm'
D.core_properties.author='Nhóm 05'

def p(t='',style=None): return D.add_paragraph(t,style)
BREAK=[False]
def h(t):
 para=D.add_heading(t,1)
 if BREAK[0]: para.paragraph_format.page_break_before=True;BREAK[0]=False
 return para
def page(): BREAK[0]=True
def link(label,url):
 para=p(); e=OxmlElement('w:hyperlink');e.set(qn('r:id'),para.part.relate_to(url,RT.HYPERLINK,is_external=True))
 r=OxmlElement('w:r');prop=OxmlElement('w:rPr');font=OxmlElement('w:rFonts');font.set(qn('w:ascii'),'Times New Roman');font.set(qn('w:hAnsi'),'Times New Roman');prop.append(font)
 col=OxmlElement('w:color');col.set(qn('w:val'),'000000');prop.append(col)
 u=OxmlElement('w:u');u.set(qn('w:val'),'single');prop.append(u);r.append(prop)
 text=OxmlElement('w:t');text.text=label;r.append(text);e.append(r);para._p.append(e)
 return para
def table(headers,rows,widths):
 t=D.add_table(rows=1,cols=len(headers));t.autofit=False
 for col,w in zip(t.columns,widths): col.width=Cm(w)
 for i,text in enumerate(headers):t.rows[0].cells[i].text=text
 for row in rows:
  cells=t.add_row().cells
  for i,text in enumerate(row):cells[i].text=str(text)
 for idx,row in enumerate(t.rows):
  pr=row._tr.get_or_add_trPr();pr.append(OxmlElement('w:cantSplit'))
  if idx==0: pr.append(OxmlElement('w:tblHeader'))
  for i,c in enumerate(row.cells):
   c.width=Cm(widths[i]);tc=c._tc.get_or_add_tcPr()
   borders=OxmlElement('w:tcBorders')
   for edge in ['top','bottom','left','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
   tc.append(borders)
   mar=OxmlElement('w:tcMar')
   for edge in ['top','bottom','left','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'65');e.set(qn('w:type'),'dxa');mar.append(e)
   tc.append(mar)
   if idx==0:
    sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'EEEEEE');tc.append(sh)
   for para in c.paragraphs:
    para.paragraph_format.line_spacing=1.5;para.paragraph_format.space_after=Pt(0)
    para.paragraph_format.keep_with_next=idx<len(t.rows)-1
    for r in para.runs:r.font.size=Pt(10.5);r.font.bold=idx==0
 sp=p();sp.paragraph_format.space_after=Pt(0)
 rpr=OxmlElement('w:rPr');sz=OxmlElement('w:sz');sz.set(qn('w:val'),'8');rpr.append(sz);sp._p.get_or_add_pPr().append(rpr)
 return t
def pic(name,caption,width=15.5):
 para=p();para.paragraph_format.space_after=Pt(0)
 para.alignment=WD_ALIGN_PARAGRAPH.CENTER
 para.add_run().add_picture(str(P/(name+'.png')),width=Cm(width))
 para.paragraph_format.keep_with_next=True
 p(caption,'Caption')

def lead(label,text):
 para=p();r=para.add_run(label+' ');r.bold=True;para.add_run(text);return para
MR=json.loads((P/'model_results.json').read_text())
A=R['agreement'];SP=R['split'];S=R['sample'];RES=MR['results']
RUN=MR_RUN=R['date'][11:16]+' ngày '+str(int(R['date'][8:10]))+'/'+str(int(R['date'][5:7]))+'/'+R['date'][:4]
pcc=lambda m:'Không xác định' if m['PCC'] is None else vn(m['PCC'],3)

p('BÁO CÁO TIẾN ĐỘ TUẦN 9','Title')
p('Nhóm 05 · Lớp 61FIT4MLA · Ngày 21 tháng 10 năm 2026','Subtitle')
h('1  Đề xuất điều chỉnh sau góp ý tuần 8')
p('Nhóm chọn một bài toán: dự đoán điểm phát âm tổng ở mức câu trên speechocean762, để giúp giáo viên ưu tiên các bài đọc cần nghe lại. Tuần 9 đã kiểm tra nhãn, chia tập theo người nói, chạy baseline hằng số và huấn luyện hai mô hình SVR, Random Forest trên đặc trưng âm thanh cố định.')
lead('Người dùng và tình huống.','Giáo viên nhận bài đọc thành tiếng của lớp 35 học viên, xem trước các bài có điểm dự đoán thấp, nghe lại và tự quyết định phản hồi. Điểm tổng không cho biết học viên sai âm nào hay cần luyện bài gì. Kịch bản này chưa được thử với lớp học thật.')
lead('Phạm vi.','Nhóm làm một benchmark nhỏ, kiểm chứng được trên dữ liệu công khai. Đã bỏ khẳng định “chưa ứng dụng nào có”, bỏ chẩn đoán âm sai, sinh bài luyện và thu giọng Việt khỏi phạm vi. Chưa có bằng chứng mô hình dùng tốt cho người học Việt Nam.')

h('2  Dữ liệu và độ đồng thuận giữa năm giám khảo')
p('speechocean762 gồm 5.000 câu tiếng Anh đọc thành tiếng của 250 người nói tiếng Quan Thoại, mỗi câu do năm giám khảo chấm (CC BY 4.0). Target là trung bình năm điểm total gốc, thang 0–10. Bảng dưới tính trên toàn bộ 5.000 câu; PCC cặp là trung bình 10 cặp giám khảo, ICC theo mô hình một chiều.')
table(['Khía cạnh','PCC cặp','ICC(1,1)','ICC(1,5)','Độ lệch chuẩn giữa 5 người'],
 [[k.capitalize()]+[vn(v,3) for v in A[k]] for k in ['accuracy','fluency','prosodic','total']],[3.0,3.0,3.0,3.0,5.0])
p('Các số mô tả độ tin cậy của nhãn; nhóm rút lại cách gọi √ICC là “trần PCC” cứng của mọi mô hình.')
link('Tải dữ liệu đầy đủ có audio (khoảng 521 MB): https://www.openslr.org/101/','https://www.openslr.org/101/')
link('Nhãn và danh sách train/test: https://github.com/jimbozhang/speechocean762','https://github.com/jimbozhang/speechocean762')

page();h('3  Đọc lại và phân biệt ba nghiên cứu')
p('Bảng dưới tách rõ ngôn ngữ được nói, đối tượng, nhiệm vụ và phần nhóm sử dụng. Số kết quả trong paper chỉ để tham khảo khi chưa tái lập cùng điều kiện.')
table(['Tiêu chí','speechocean762 [1]','GOPT [2]','LingWav2Vec2 [3]'],[
 ['Ngôn ngữ được nói','Tiếng Anh','Tiếng Anh','Tiếng Việt'],
 ['Người nói','250 người có tiếng mẹ đẻ Quan Thoại; có trẻ em','Dùng corpus speechocean762','Người lớn và trẻ em 5–7 tuổi'],
 ['Nhiệm vụ và mức nhãn','Dữ liệu chấm phát âm ở mức câu, từ và âm vị','Hồi quy nhiều khía cạnh ở mức câu, từ và âm vị','Phát hiện và chẩn đoán lỗi âm vị'],
 ['Split trong nghiên cứu','2.500 câu train và 2.500 câu test; tách người nói','Train/test của speechocean762','Train, public test, private test của VLSP VMD'],
 ['Đầu vào và đặc trưng','Audio, câu đọc, phiên âm chuẩn; nhãn gốc và tổng hợp','GOP 84 chiều và mã âm vị chuẩn; tác giả có phát hành đặc trưng','Audio qua wav2vec 2.0 và chuỗi âm vị chuẩn'],
 ['Nhóm thật sự sử dụng','Audio và nhãn của 5.000 câu; split chính thức','Tham khảo pipeline; chưa chạy GOP hoặc GOPT','Chỉ tham khảo nghiên cứu; không tái lập']
 ],[2.9,4.7,4.7,4.7])
lead('Sửa LingWav2Vec2.','Mục 3.1 nghiên cứu phát âm tiếng Việt, gồm dữ liệu người lớn và trẻ em. Paper không phải bằng chứng về người Việt học phát âm tiếng Anh; nhóm bỏ liên hệ sai này trong báo cáo tuần 8.')
lead('Lưu ý về GOP.','Paper dữ liệu cho biết chuỗi âm chuẩn dùng để căn chỉnh có thể do chuyên gia chọn bằng bỏ phiếu; thông tin này không có sẵn khi nhận bài mới. Nếu dùng GOP, nhóm phải tạo phiên âm chuẩn tự động từ câu đọc và không đưa nhãn của giám khảo vào đầu vào.')
h('Nguồn nghiên cứu')
link('[1] Zhang và cộng sự, speechocean762, Interspeech 2021, mục 2–4.','https://arxiv.org/html/2104.01378v2')
link('[2] Gong và cộng sự, GOPT, ICASSP 2022, mục 3–4.','https://arxiv.org/html/2205.03432v1')
link('[3] Nguyen và Tran, LingWav2Vec2, Interspeech 2024, mục 3.1.','https://www.isca-archive.org/interspeech_2024/nguyen24b_interspeech.pdf')

page();h('4  Mẫu dữ liệu và cách chia tập')
table(['Ví dụ một bản ghi','Giá trị'],[
 ['Audio (nhúng ở Phụ lục)',S['id']+'.WAV · 16 kHz, mono, '+vn(S['duration_seconds'],2)+' giây'],
 ['Câu đọc',S['text']],
 ['Năm điểm → target','('+' + '.join(vn(x,1) for x in S['total'])+') / 5 = '+vn(S['target'],2)]],[5.2,11.8])
p('Riêng scores.json ghi total = '+vn(S['published'],1)+' cho câu này; ở 4.948/5.000 câu, hai giá trị khác nhau. Vì vậy nhóm ghi rõ cách tạo target và chưa so trực tiếp với GOPT, vốn dùng total trong scores.json.')
lead('Cách chia tập.','Giữ '+str(SP['test'][0])+' người test chính thức ('+f"{SP['test'][1]:,}".replace(',','.')+' câu). Từ 125 người train chính thức, xáo bằng NumPy default_rng(42) và lấy '+str(SP['validation'][0])+' người làm validation ('+str(SP['validation'][1])+' câu); còn '+str(SP['train'][0])+' người train ('+f"{SP['train'][1]:,}".replace(',','.')+' câu). Không người nói nào ở hai tập.')

h('5  Mô hình và kết quả')
lead('Đặc trưng.','Mỗi audio được tính log-mel 40 dải (khung 25 ms, bước 10 ms); lấy trung bình và độ lệch chuẩn theo thời gian của từng dải, cộng độ dài câu, được vector '+str(MR['feature_dim'])+' chiều. Không dùng câu đọc, phiên âm hay điểm giám khảo làm đầu vào. Đây là đặc trưng thay thế vì chưa lấy được GOP (Mục 6).')
lead('Mô hình.','SVR nhân RBF có chuẩn hoá, thử C = 0,3; 1; 3; 10. Random Forest 300 cây, thử min_samples_leaf = 1; 5; 20. Chọn cấu hình có MAE validation thấp nhất; tập test chỉ chạy một lần với cấu hình đã chọn.')
table(['Mô hình','Cấu hình chọn','MAE val','MAE test','RMSE test','PCC test'],[
 ['Hằng số','Trung bình train = '+vn(R['constant'],2),vn(RES['constant']['validation']['MAE'],3),vn(RES['constant']['test']['MAE'],3),vn(RES['constant']['test']['RMSE'],3),pcc(RES['constant']['test'])],
 ['SVR','C = '+vn(RES['SVR']['config']['C'],0),vn(RES['SVR']['validation']['MAE'],3),vn(RES['SVR']['test']['MAE'],3),vn(RES['SVR']['test']['RMSE'],3),pcc(RES['SVR']['test'])],
 ['Random Forest','min_samples_leaf = '+str(RES['RF']['config']['min_samples_leaf']),vn(RES['RF']['validation']['MAE'],3),vn(RES['RF']['test']['MAE'],3),vn(RES['RF']['test']['RMSE'],3),pcc(RES['RF']['test'])]],[2.8,4.4,2.2,2.2,2.4,3.0])
gain=(1-RES['SVR']['test']['MAE']/RES['constant']['test']['MAE'])*100
FS=json.loads((P/'figure_stats.json').read_text())
p('Cả hai mô hình đều tốt hơn baseline: SVR giảm MAE test từ '+vn(RES['constant']['test']['MAE'],2)+' xuống '+vn(RES['SVR']['test']['MAE'],2)+' điểm (khoảng '+f'{gain:.0f}'+'%) và đạt PCC '+vn(RES['SVR']['test']['PCC'],2)+', tức đã bắt đầu xếp hạng được bài đọc. Hai mô hình gần ngang nhau trên test. PCC test thấp hơn nhiều so với validation ('+vn(RES['SVR']['validation']['PCC'],2)+'); validation chỉ có 25 người nói nên ước lượng có thể kém ổn định, vì vậy nhóm lấy số trên test 125 người làm kết quả chính.')
pic('figure_results','Hình 1. Kết quả trên tập test: (a) MAE của ba mô hình; (b) điểm SVR dự đoán so với target thật của từng câu. Vẽ bằng make_figure.py từ dự đoán của lần chạy ở Hình 2.',15.5)
lead('Hạn chế quan trọng.','Dự đoán dồn về khoảng giữa ('+vn(FS['svr_pred_min'],1)+'–'+vn(FS['svr_pred_max'],1)+' điểm). Với '+str(FS['n_low'])+' câu test có target dưới 6, SVR đoán cao hơn thật trung bình '+vn(FS['svr_bias_low'],1)+' điểm, trong khi câu từ 6 trở lên chỉ lệch '+vn(FS['svr_bias_high'],2)+'. Đây đúng là nhóm bài giáo viên cần nghe lại, nên hiện chưa dùng được ngưỡng điểm cố định để chọn bài. Kết quả dùng log-mel, split và target của nhóm nên không so trực tiếp với GOPT.')

h('6  Thời gian chạy, CPU/GPU và lựa chọn GOP')
fe=RES;s1=lambda x:vn(x,1)
table(['Bước đã chạy','Thời gian','Thiết bị'],[
 ['Kiểm tra nhãn, đồng thuận, chia tập, baseline (verify.py)',vn(R['total_script_seconds'],2)+' giây','CPU'],
 ['Đọc và trích đặc trưng cho 5.000 audio',s1(MR['feature_seconds'])+' giây','CPU'],
 ['Chọn và huấn luyện SVR (4 cấu hình)',s1(RES['SVR']['train_select_seconds'])+' giây','CPU'],
 ['Chọn và huấn luyện Random Forest (3 cấu hình)',s1(RES['RF']['train_select_seconds'])+' giây','CPU, 8 nhân'],
 ['Toàn bộ train_models.py',s1(MR['total_script_seconds'])+' giây','CPU']],[10.0,3.5,3.5])
p('Máy chạy: MacBook Air Apple M2, 8 nhân CPU, RAM 8 GB; Python '+R['python']+', NumPy '+R['numpy']+', scikit-learn '+MR['sklearn']+'; không dùng GPU. Thời gian tính từ sau khi nạp thư viện.')
lead('Lựa chọn GOP.','Nhóm chọn dùng GOP trích sẵn của tác giả GOPT, không tự chạy acoustic model và Kaldi trên 5.000 câu, vì tự chạy tốn công cài đặt và thời gian tính toán hơn nhiều. Link tải GOP của tác giả hiện bị Dropbox khoá tạm thời (kiểm tra ngày 21/10/2026), nên tuần này dùng log-mel thay thế.')
lead('Dự kiến, chưa đo.','Với GOP trích sẵn, SVR và Random Forest vẫn chạy được trên CPU của máy nhóm. GPU chỉ có thể cần nếu tự trích đặc trưng bằng mô hình lớn như wav2vec 2.0 hoặc huấn luyện GOPT.')
lead('Bước tiếp theo.','Thử lại nguồn GOP; nếu lấy được, chạy lại SVR và Random Forest trên GOP với cùng split và target để so với log-mel.')
link('Đặc trưng GOP trích sẵn của GOPT: https://github.com/YuanGongND/gopt/tree/master/data','https://github.com/YuanGongND/gopt/tree/master/data')

h('Phụ lục. Minh chứng chạy thật').paragraph_format.keep_with_next=True
pic('terminal_verify_run','Hình 2. Ảnh chụp cửa sổ Terminal thật khi chạy verify.py, train_models.py và make_figure.py lúc '+RUN+'. Mọi số trong Mục 2, 4, 5 và 6 lấy từ lần chạy này.',13)
p('Audio mẫu và gói minh chứng (code, nhãn, danh sách chia tập, kết quả, log, ảnh chụp và README hướng dẫn chạy lại) được nhúng dưới đây.')
p('[[OBJECTS]]')
p('Trên Word cho Windows, nháy đúp vào biểu tượng rồi chọn Open. Nếu không mở được, nghe audio tại link dự phòng:')
link('Nghe audio mẫu 000010011.WAV trên GitHub của speechocean762','https://raw.githubusercontent.com/jimbozhang/speechocean762/main/WAVE/SPEAKER0001/000010011.WAV')

foot=sec.footer.paragraphs[0];foot.alignment=WD_ALIGN_PARAGRAPH.CENTER
r=foot.add_run();r.font.name='Times New Roman';r.font.size=Pt(10);r.font.color.rgb=RGBColor(0,0,0)
fld=OxmlElement('w:fldSimple');fld.set(qn('w:instr'),'PAGE');r._r.addnext(fld)
for el in list(D.styles.element.iter(qn('w:pBdr'))) + list(D.element.iter(qn('w:pBdr'))):
 el.getparent().remove(el)
for para in D.paragraphs:
 para.paragraph_format.line_spacing=1.5
 for r in para.runs:
  r.font.name='Times New Roman';r.font.color.rgb=RGBColor(0,0,0)
for root in (D.styles.element, D.element):
 for color in root.iter(qn('w:color')):
  color.attrib.clear(); color.set(qn('w:val'),'000000')
 for fonts in root.iter(qn('w:rFonts')):
  fonts.attrib.clear()
  for key in ('ascii','hAnsi','eastAsia','cs'): fonts.set(qn('w:'+key),'Times New Roman')
out=P.parent/'Group05_Week09_Report.docx';D.save(out)
print(out)
