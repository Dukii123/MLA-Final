from pathlib import Path
import json, zipfile, hashlib
P=Path(__file__).parent
readme='''NHÓM 05 — MINH CHỨNG TUẦN 10
Lớp 61FIT4MLA | Nộp cùng Group05_Week10_Report.docx

NỘI DUNG
1. pilot_w2v.py: chạy thử wav2vec 2.0 base trên 50 câu, đo thời gian thật trước khi chạy cả 5.000 câu.
   Lần chạy trong báo cáo này chỉ đo CPU (máy Windows). Đầu ra: pilot_w2v.json.
2. extract_w2v.py: trích embedding wav2vec 2.0 base (facebook/wav2vec2-base, huấn luyện sẵn, không fine-tune)
   cho 5.000 câu; trung bình theo câu ở tầng 4, 8, 12. Đầu ra: w2v_run.json và features_w2v_layers.npz
   (khoảng 21 MB, không kèm trong ZIP để giữ báo cáo nhẹ; chạy lại extract_w2v.py để tạo; mất 1.499 s
   ≈ 25 phút CPU trên máy Windows chạy báo cáo này).
3. week10_analysis.py: kiểm tra target; chọn tham số bằng GroupKFold 5 phần theo người nói trên 125 người train;
   9 mô hình (SVR, RF, chỉ độ dài, bỏ độ dài, trọng số, LR/RF phân loại cân bằng, SVR wav2vec 2.0);
   recall/precision trong 10%/20% dự đoán thấp nhất; sai số theo người nói/tuổi; 5 câu sai nặng nhất;
   phân tích giám khảo lệch. Đầu ra: week10_results.json, week10_run.log, test_predictions_week10.csv,
   speaker_errors_test.csv, worst5/*.WAV (audio 5 câu sai nặng nhất).
4. make_figure_week10.py: vẽ fig1_recall.png, fig2_curve.png, fig3_bias.png, fig4_speakers.png (Hình 1–4);
   đầu ra figure_run.log, figure_stats.json.
5. split_manifest.csv và features_logmel_stats.npz lấy từ Tuần 9 (cùng người nói ở train/test).
6. terminal_w2v_extract_win.png, terminal_pilot_win.png, terminal_run_win.png: ảnh chụp thật cửa sổ
   Terminal của lần chạy trên Windows (extract / pilot / analysis + figures); output trong ảnh trùng các file log.

CÁCH CHẠY LẠI (CPU)
  python -m pip install -r requirements.txt
  Tải https://www.openslr.org/resources/101/speechocean762.tar.gz (khoảng 521 MB), giải nén.
  python pilot_w2v.py <thư mục speechocean762>
  python extract_w2v.py <thư mục speechocean762> cpu    (khoảng 25 phút trên CPU laptop Windows)
  python week10_analysis.py <thư mục speechocean762>
  python make_figure_week10.py
Kết quả recall/MAE/PCC tái lập được; thời gian đo thay đổi theo máy.

PHƯƠNG PHÁP
Target chính = total trong scores.json = floor(trung vị năm điểm), khớp 5.000/5.000 câu.
Trung bình năm điểm (scores-detail.json) là phân tích phụ. "Dưới 6" = total < 6.
Train = 125 người train chính thức (gộp train và validation của Tuần 9); test = 125 người test chính thức.
Chọn tham số bằng GroupKFold(5) theo người nói trên train; huấn luyện lại trên toàn bộ train; test chạy một lần.
Recall@k = số bài dưới 6 nằm trong k% bài có điểm dự đoán thấp nhất / tổng số bài dưới 6 của test.
Precision@k = tỉ lệ bài dưới 6 trong k% đó. Ngẫu nhiên: recall = k, precision = tỉ lệ nền.
Chưa dùng GOP: link của tác giả GOPT vẫn bị Dropbox khoá (kiểm tra 21/10/2026); nhóm quyết định bỏ GOP.

NGUỒN VÀ GIẤY PHÉP
speechocean762 (Zhang và cộng sự, Interspeech 2021), CC BY 4.0: https://www.openslr.org/101/
wav2vec 2.0 base (Baevski và cộng sự, NeurIPS 2020), Apache 2.0: https://huggingface.co/facebook/wav2vec2-base
Ảnh minh chứng là ảnh chụp màn hình thật, không chỉnh sửa nội dung hay số.
'''
(P/'README.txt').write_text(readme)
(P/'requirements.txt').write_text('numpy==2.5.2\nscikit-learn==1.9.1\nmatplotlib==3.11.2\ntorch==2.14.1+cpu\ntransformers==5.20.2\n')
names=['README.txt','requirements.txt','pilot_w2v.py','pilot_w2v.json','extract_w2v.py','week10_analysis.py','make_figure_week10.py','split_manifest.csv','scores-detail.json','scores.json',
       'features_logmel_stats.npz','w2v_run.json','week10_results.json','week10_run.log','test_predictions_week10.csv',
       'speaker_errors_test.csv','fig1_recall.png','fig2_curve.png','fig3_bias.png','fig4_speakers.png','figure_run.log','figure_stats.json','terminal_w2v_extract_win.png','terminal_pilot_win.png','terminal_run_win.png']+sorted('worst5/'+f.name for f in (P/'worst5').glob('*.WAV'))
checks={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in names}
(P/'SHA256.json').write_text(json.dumps(checks,indent=2))
out=P.parent/'Group05_Week10_Attachments.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for name in names+['SHA256.json']:z.write(P/name,name)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for n,h in checks.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
print(out, out.stat().st_size, 'bytes,', len(names)+1, 'files verified')
