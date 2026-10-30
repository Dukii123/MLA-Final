from pathlib import Path
import json, zipfile, hashlib, sys, shutil

P = Path(__file__).parent
out = Path(sys.argv[1]) if len(sys.argv) > 1 else P.parent / 'Group05_Week11_Attachments.zip'
# Các file dùng chung với tuần 10: copy sang để ZIP tự đủ (trừ embedding 21 MB).
W10 = P.parent / 'week10_work'
for name in ['split_manifest.csv', 'scores.json', 'scores-detail.json', 'features_logmel_stats.npz', 'w2v_run.json']:
    if not (P / name).exists():
        shutil.copy2(W10 / name, P / name)
readme = '''NHÓM 05 — MINH CHỨNG TUẦN 11
Lớp 61FIT4MLA | Nộp cùng Group05_Week11_Report.docx

NỘI DUNG
1. week11_analysis.py: một script chạy trọn gói cho tuần 11, tái hiện 9 mô hình tuần 10 và thêm
   4 thí nghiệm mới theo nhận xét của thầy:
   - kiểm tra target trên 5.000 câu; thống kê nhóm test có total <= 2 và 5 câu sai nặng nhất;
   - bảng CV đầy đủ (recall@20%, MAE, trung bình ± độ lệch chuẩn qua 5 fold theo người nói)
     cho mọi cấu hình, đặt cạnh kết quả test;
   - SVR wav2vec 2.0 nối thêm hai đặc trưng độ dài (CV 3 tầng × 3 giá trị C);
   - phép kiểm nửa đọc nhanh / đọc chậm: chia test theo trung vị giây/từ, chỉ đọc dự đoán đã lưu;
   - thí nghiệm phụ: LR cân bằng lớp trên embedding wav2vec 2.0.
   Đầu ra: week11_results.json, week11_run.log, test_predictions_week11.csv,
   speaker_errors_test.csv, worst5/*.WAV (audio 5 câu sai nặng nhất).
2. make_figure_week11.py: vẽ fig1_cv_test.png (lollipop CV so với test), fig2_halves.png
   (cột ghép theo nửa tốc độ), fig3_speed_dist.png (phân bố giây/từ); đầu ra figure_run.log,
   figure_stats.json.
3. terminal_week11_run_win.png: ảnh chụp thật cửa sổ PowerShell khi chạy week11_analysis.py
   và make_figure_week11.py trên Windows (CPU only). Số trong ảnh trùng week11_run.log và JSON.
4. split_manifest.csv, scores.json, scores-detail.json, features_logmel_stats.npz: lấy từ tuần 9/10,
   giữ nguyên để tái lập đúng phép chia người nói và target.
5. w2v_run.json: thông tin lần trích wav2vec 2.0 ngày 24/10/2026 (tuần 10), dùng lại, không trích lại.
   Embedding features_w2v_layers.npz (21 MB) không kèm trong ZIP; xem cách tạo ở mục CÁCH CHẠY LẠI.

CÁCH CHẠY LẠI (CPU)
  python -m pip install -r requirements.txt
  Tải https://www.openslr.org/resources/101/speechocean762.tar.gz (khoảng 521 MB), giải nén.
  Đặt thư mục report/week10_work cạnh week11_work, trong đó có features_w2v_layers.npz và
  split_manifest.csv (hoặc chạy extract_w2v.py của tuần 10 để tạo lại embedding, khoảng 25 phút CPU).
  python week11_analysis.py <thư mục speechocean762>
  python make_figure_week11.py
Kết quả recall/MAE/PCC tái lập được; thời gian đo thay đổi theo máy.

PHƯƠNG PHÁP
Target chính = total trong scores.json = floor(trung vị năm điểm), khớp 5.000/5.000 câu.
Trung bình năm điểm (scores-detail.json) là phân tích phụ. "Dưới 6" = total < 6; test có 330/2.500.
Train = 125 người train chính thức; test = 125 người test chính thức (không trùng người nói).
Chọn tham số bằng GroupKFold(5) theo người nói trên train; huấn luyện lại trên toàn bộ train;
test chạy một lần. Mọi bảng trong báo cáo lấy đúng lần chạy có ảnh Terminal.
Recall@k = số bài dưới 6 nằm trong k% bài có điểm dự đoán thấp nhất / tổng số bài dưới 6 của test.
Precision@k = tỉ lệ bài dưới 6 trong k% đó. Ngẫu nhiên: recall = k, precision = tỉ lệ nền.
Phép kiểm nửa tốc độ không chọn lại tham số: chỉ đọc dự đoán của mô hình đã huấn luyện.
Chưa dùng GOP: link của tác giả GOPT vẫn bị Dropbox khoá (kiểm tra 21/10/2026); nhóm quyết định bỏ GOP.

NGUỒN VÀ GIẤY PHÉP
speechocean762 (Zhang và cộng sự, Interspeech 2021), CC BY 4.0: https://www.openslr.org/101/
wav2vec 2.0 base (Baevski và cộng sự, NeurIPS 2020), Apache 2.0: https://huggingface.co/facebook/wav2vec2-base
Ảnh minh chứng là ảnh chụp màn hình thật, không chỉnh sửa nội dung hay số.
'''
(P / 'README.txt').write_text(readme, encoding='utf-8')
(P / 'requirements.txt').write_text('numpy==2.5.2\nscikit-learn==1.9.1\nmatplotlib==3.11.2\n')

names = ['README.txt', 'requirements.txt', 'week11_analysis.py', 'make_figure_week11.py',
         'split_manifest.csv', 'scores.json', 'scores-detail.json', 'features_logmel_stats.npz', 'w2v_run.json',
         'week11_results.json', 'week11_run.log', 'test_predictions_week11.csv', 'speaker_errors_test.csv',
         'fig1_cv_test.png', 'fig2_halves.png', 'fig3_speed_dist.png', 'figure_run.log', 'figure_stats.json',
         'terminal_week11_run_win.png'] + sorted('worst5/' + f.name for f in (P / 'worst5').glob('*.WAV'))
missing = [n for n in names if not (P / n).exists()]
assert not missing, f'thiếu file để đóng gói: {missing}'
checks = {n: hashlib.sha256((P / n).read_bytes()).hexdigest() for n in names}
(P / 'SHA256.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
out.parent.mkdir(parents=True, exist_ok=True)
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in names + ['SHA256.json']:
        z.write(P / name, name)
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None
    for n, h in checks.items():
        assert hashlib.sha256(z.read(n)).hexdigest() == h
print(out, out.stat().st_size, 'bytes,', len(names) + 1, 'files verified')
