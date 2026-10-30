from pathlib import Path
import json, zipfile, hashlib
P=Path(__file__).parent
readme='''NHÓM 05 — MINH CHỨNG TUẦN 9
Lớp 61FIT4MLA | Ngày 21/10/2026 | Nộp cùng Group05_Week09_Report.docx

NỘI DUNG
1. 000010011.WAV: audio mẫu, 16 kHz, mono, 2,58 giây. sample_labels.json: câu đọc
   WE CALL IT BEAR, năm điểm total 7.6, 9.0, 7.9, 8.0, 9.1, target 8.32/10.
2. verify.py: kiểm tra nhãn, độ đồng thuận, chia tập theo người nói, baseline hằng số.
   Đầu vào đã kèm: scores-detail.json, scores.json, train_utt2spk, test_utt2spk.
   Đầu ra: verified_results.json, verified_run.log, split_manifest.csv (5.000 ID).
3. train_models.py: trích đặc trưng log-mel cố định cho 5.000 audio, chọn cấu hình
   SVR và Random Forest trên validation, đánh giá test một lần.
   Đầu ra: model_results.json, model_run.log, features_logmel_stats.npz,
   test_predictions.csv (dự đoán từng câu test).
   make_figure.py: vẽ figure_results.png (Hình 1) từ dự đoán test;
   đầu ra figure_run.log, figure_stats.json.
4. terminal_verify_run.png: ảnh chụp thật cửa sổ Terminal (screencapture -l) khi chạy
   ba script trên (Hình 2); output trong ảnh trùng các file log.

CÁCH CHẠY LẠI (CPU, không cần GPU/Kaldi)
  python3 -m pip install -r requirements.txt
  python3 verify.py
  Tải https://www.openslr.org/resources/101/speechocean762.tar.gz (khoảng 521 MB),
  giải nén thành data/speechocean762 cạnh các script, rồi chạy:
  python3 train_models.py            (hoặc: python3 train_models.py <thư mục dataset>)
  python3 make_figure.py
Số liệu MAE/RMSE/PCC và split tái lập được; thời gian đo thay đổi theo máy.

PHƯƠNG PHÁP
Target = trung bình năm điểm total trong scores-detail.json, không phải total trong
scores.json. Giữ 125 speaker test chính thức; từ 125 speaker train, dùng
numpy.random.default_rng(42).permutation, lấy 25 speaker làm validation.
Đặc trưng: log-mel 40 dải (khung 25 ms, bước 10 ms), trung bình và độ lệch chuẩn
theo thời gian của từng dải, cộng độ dài câu: 81 chiều. Không dùng câu đọc,
phiên âm, tuổi hay ID speaker làm đầu vào.
SVR (RBF, chuẩn hoá): C trong 0.3, 1, 3, 10. Random Forest 300 cây, max_features=sqrt,
min_samples_leaf trong 1, 5, 20. Chọn theo MAE validation thấp nhất.
Chưa dùng GOP: link đặc trưng GOP của tác giả GOPT bị Dropbox khoá tạm thời
(kiểm tra 21/10/2026). Kết quả không so trực tiếp với GOPT.

NGUỒN VÀ GIẤY PHÉP
speechocean762 (Zhang và cộng sự, Interspeech 2021), CC BY 4.0.
https://www.openslr.org/101/
https://github.com/jimbozhang/speechocean762
https://creativecommons.org/licenses/by/4.0/
GOPT: https://github.com/YuanGongND/gopt/tree/master/data
Ảnh minh chứng là ảnh chụp màn hình thật, không chỉnh sửa nội dung hay số.
'''
(P/'README.txt').write_text(readme)
(P/'requirements.txt').write_text('numpy==2.3.5\nscikit-learn==1.7.2\nmatplotlib==3.10.7\n')
names=['README.txt','requirements.txt','verify.py','train_models.py','000010011.WAV','sample_labels.json','scores-detail.json','scores.json','train_utt2spk','test_utt2spk','split_manifest.csv','verified_results.json','verified_run.log','model_results.json','model_run.log','features_logmel_stats.npz','test_predictions.csv','make_figure.py','figure_results.png','figure_run.log','figure_stats.json','terminal_verify_run.png']
checks={n:hashlib.sha256((P/n).read_bytes()).hexdigest() for n in names}
(P/'SHA256.json').write_text(json.dumps(checks,indent=2))
out=P.parent/'Group05_Week09_Attachments.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as z:
 for name in names+['SHA256.json']:z.write(P/name,name)
with zipfile.ZipFile(out) as z:
 assert z.testzip() is None
 for n,h in checks.items():assert hashlib.sha256(z.read(n)).hexdigest()==h
print(out, out.stat().st_size, 'bytes,', len(names)+1, 'files verified')
