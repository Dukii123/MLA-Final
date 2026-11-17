NHÓM 05 — MINH CHỨNG BÁO CÁO CUỐI KỲ (speechocean762)
Môn MLA · Lớp 61FIT4MLA · Nộp cùng Group05_Final_Report.docx/.pdf

NỘI DUNG
1. week11_analysis.py: script chạy trọn gói sinh mọi số của báo cáo (bảng CV 10 cấu hình,
   kiểm nửa tốc độ, nhóm total <= 2, worst5). Đầu ra: week11_results.json, week11_run.log,
   test_predictions_week11.csv, worst5/*.WAV.
2. week11_completeness.py: điểm câu corpus từ parquet (khớp 2.500 câu test) + đo âm học
   tự động 5 file worst5. Đầu ra: week11_completeness.json/.log.
3. make_figure_week11.py: ba hình trong báo cáo. rebuild_wave_from_parquet.py: dựng lại
   5.000 WAV từ parquet nếu máy mất thư mục WAVE (khoảng 9 giây).
4. week11_results.json / week11_completeness.json / week11_run.log: nguồn số chính xác
   của mọi bảng trong báo cáo — lần chạy 11:16 ngày 09/11/2026 (ảnh Terminal kèm).
5. listening_notes.json: ghi chú nghe 5 câu worst5 của hai người nghe độc lập (nguyên văn).
6. final_contributions.json: đóng góp từng thành viên và khai báo sử dụng AI.
7. final_data_checks.py/.json/.log: kiểm tra chất lượng dữ liệu bổ sung (missingness,
   duplicates) — nguồn của đoạn "Phân bố và chất lượng dữ liệu" ở Mục 2 báo cáo.
8. split_manifest.csv: danh sách người nói train/test; test_predictions_week11.csv:
   dự đoán từng câu của 11 cấu hình đứng sau bảng chính.

CÁCH CHẠY LẠI (CPU)
  python -m pip install numpy scikit-learn matplotlib pyarrow
  Tải https://www.openslr.org/resources/101/speechocean762.tar.gz (khoảng 521 MB), giải nén.
  python week11_analysis.py <thư mục speechocean762>
  python week11_completeness.py <thư mục parquet HF (2 file train/test-...parquet)>
  python make_figure_week11.py
  python build_final_report.py && python verify_final.py

PHƯƠNG PHÁP (tóm tắt)
Target = total trong scores.json = floor(trung vị năm điểm), khớp 5.000/5.000 câu.
"Dưới 6" = total < 6; test 330/2.500 (13,2%). Chia theo người nói 125/125;
chọn tham số bằng GroupKFold(5) theo người nói trên train; test chạy một lần.
Recall@k = số bài dưới 6 trong k% bài dự đoán thấp nhất / tổng số bài dưới 6.

NGUỒN VÀ GIẤY PHÉP
speechocean762 (Zhang và cộng sự, Interspeech 2021), CC BY 4.0: https://www.openslr.org/101/
wav2vec 2.0 base (Baevski và cộng sự, NeurIPS 2020), Apache 2.0: https://huggingface.co/facebook/wav2vec2-base
Ảnh Terminal là ảnh chụp thật, không chỉnh sửa nội dung hay số.
