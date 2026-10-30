# Design: Báo cáo Tuần 11 — Nhóm 05 (61FIT4MLA)

Ngày: 27/10/2026. Máy: Windows (DucAnh), Python 3.14.5 system, python-docx 1.2.0, Node, LibreOffice đều có.

## Intent (vì sao làm)

Thầy Khánh trong nhận xét Tuần 10 đã nêu **3 việc bắt buộc + 1 việc nên làm + 1 thí nghiệm phụ nếu còn thời gian**. Báo cáo Tuần 11 phải là bản **nộp đầy đủ**: số lấy từ một lần chạy thật có ảnh Terminal, hình mới, nhúng gói minh chứng OLE vào Word, render LibreOffice soát từng trang — đúng yêu cầu cố định trong `report/AGENTS.md`.

Thứ tự ưu tiên theo đúng gợi ý của thầy ("Hướng đi vừa sức"):
1. Nghe 5 câu sai nặng nhất (phần thống kê làm机器 trước; phần nghe do nhóm).
2. Bảng CV đầy đủ cho mọi cấu hình, chọn hướng bằng CV.
3. Phép kiểm wav2vec theo nửa đọc nhanh/đọc chậm.
4. (Nên làm) Sửa nhãn tuần và ngày.
5. (Phụ, đã chốt làm) LR cân bằng lớp trên embedding wav2vec.

## Goals

- G1. Bảng CV đầy đủ: recall@20% và MAE CV (TB ± SD, GroupKFold 5 phần theo người nói) cho **mọi cấu hình** đã có tuần 10 + cấu hình mới, kẹp **cột CV cạnh cột test** trong cùng một bảng; ghi rõ quyết định dựa trên cột CV, test chỉ xác nhận.
- G2. Thí nghiệm 3a: bảng CV 3 dòng — chỉ-độ-dùng · wav2vec 2.0 · wav2vec + 2 đặc trưng độ dài.
- G3. Thí nghiệm 3b: chia test theo **trung vị giây/từ** thành nửa đọc nhanh / nửa đọc chậm; bảng 2×2 (mô hình × nửa) với recall@20% từng nửa cho chỉ-độ-dùng và wav2vec, kèm số bài dưới 6 của từng nửa. Chỉ đọc dự đoán có sẵn, không chọn lại gì.
- G4. Thống kê nhóm total ≤ 2 trên test (số câu, điểm dự đoán trung bình của từng mô hình chính) + bảng 5 câu sai nặng nhất với **2 cột trống cho ghi chú nghe của 2 người**.
- G5. Thí nghiệm phụ: LR `class_weight=balanced` trên embedding wav2vec 2.0, so recall@10%/20% phân loại với hồi quy (dựng bảng trong mục thí nghiệm phụ, ghi rõ đây không phải yêu cầu bắt buộc).
- G6. Báo cáo Word `.docx` **một file duy nhất**, Times New Roman, giãn 1.5, toàn chữ đen, có hình mới + ảnh Terminal thật của lần chạy, gói minh chứng ZIP nhúng OLE, render LibreOffice không tràn bảng/không cắt ảnh/không trang trắng.
- G7. Nhãn nhất quán: file `Group05_Week11_Report.docx`, tiêu đề "Tuần 11", ngày lấy từ mtime log lần chạy; có dòng đính chính rằng 21/10 thuộc tuần 9 (sửa lỗi nhãn tuần 10 thầy chỉ ra) và ghi nhãn link bảng đăng ký là việc nhóm đổi tay trước buổi gặp.

## Non-goals / Anti-goals

- **Không** chạy lại extract wav2vec (npz 20,6 MB còn nguyên), không tải lại dataset, không huấn luyện fine-tune.
- **Không** thay đổi target, cách chia train/test, bộ siêu tham số, hay phát biểu lại kết luận tuần 10 như thể mới đo.
- **Không** bịa nội dung audio 5 câu — phần nghe để trống cho nhóm điền, đánh dấu "chưa nghe, nhóm điền trước buổi gặp".
- **Không** dựng ảnh giả, không sửa số cho đẹp; mọi số trong báo cáo phải trỏ vào `week11_results.json` / `week11_run.log` của lần chạy có trong ảnh Terminal.
- Không làm slide; không mở rộng đề tài (không GOP, không mô hình mới ngoài LR-w2v).

## Constraints

- Yêu cầu cố định báo cáo: xem `report/AGENTS.md` (màu hình theo loại đặc trưng, ảnh Terminal thật, nhúng OLE, render soát trang, mỗi hình một loại).
- Tuần 10 dùng bảng ba đường kẻ ngang + khung "Kết quả chính" + tiêu đề gạch chân → **tuần 11 đổi kiểu trình bày một chút** nhưng giữ ảnh Terminal theo kiểu cũ.
- Thời gian: analysis tuần 10 ~146 s; tuần 11 thêm LR-w2v + 2 thí nghiệm mới, dự kiến tổng dưới ~6 phút CPU, chạy được trong một cửa sổ Terminal thật.

## Approaches (các cách cân nhắc)

- **A. Chạy chậm, tái sử dụng số tuần 10.** Bảng CV lấy từ `week10_results.json`, chỉ chạy phần mới. → Trái quy tắc "mỗi số lấy từ lần chạy có ảnh Terminal tuần này"; hai nguồn số khó đối chiếu. **Bỏ.**
- **B. (CHỌN) Một script `week11_analysis.py` chạy trọn gói.** Tái hiện toàn bộ pipeline tuần 10 (9 mô hình cũ, CV, worst5, log, predictions) cộng 3 thí nghiệm mới (wav2vec+độ dài, LR-w2v, nửa nhanh/chậm, nhóm total ≤ 2), ra **một** `week11_results.json` + `week11_run.log`; chạy trong cửa sổ PowerShell thật rồi chụp ảnh. Đúng quy trình tuần 10, số đồng bộ 100%, vẫn tái sử dụng npz nên không tốn extract.
- **C. Tách nhiều script nhỏ cho từng việc.** Nhiều lần chạy, nhiều ảnh Terminal, dễ lệch số giữa các lần. **Bỏ.**

## Các phần how đã chốt (theo quyết định đã nói trong hội thoại)

1. **Thư mục:** code + kết quả + hình + ảnh Terminal ở `report\week11_work\`; bản nộp `report_week11\Group05_Week11_Report.docx` (mới, không đụng `report_week10\`). Feature npz, manifest, scores đọc từ `report\week10_work\` (ghi đường dẫn tuyệt đối trong script, có fallback argv).
2. **`week11_analysis.py`** — mở rộng từ `week10_analysis.py`:
   - Giữ nguyên: target check, GroupKFold-5 theo người nói, 9 mô hình cũ, worst5, speakers/ages/raters, `test_predictions_week11.csv`.
   - Mới: `SVR wav2vec+độ dài` (nối tầng tốt nhất wav2vec với [giây, giây/từ], grid C, chọn bằng MAE CV).
   - Mới: `LR balanced wav2vec` (StandardScaler + LogisticRegression class_weight=balanced, grid C, chọn recall20 CV, xếp hạng bằng 1−P(dưới 6)).
   - Mới: 3b — split test theo trung vị giây/từ (tính trên test, ghi rõ giá trị trung vị), recall@20% trong từng nửa cho `SVR chỉ độ dài` và `SVR wav2vec 2.0`, số câu và số bài dưới 6 mỗi nửa.
   - Mới: thống kê nhóm test total ≤ 2 (n, MAE/rmse? — tối thiểu: điểm dự đoán trung bình của 3 mô hình chính log-mel, chỉ-độ-dùng, wav2vec) vào JSON/log.
   - CV đầy đủ: in ra log bảng recall20/MAE CV (TB ± SD) cho mọi mô hình.
3. **`make_figure_week11.py`** — 3 hình, kiểu khác tuần 10, màu theo loại đặc trưng:
   - Hình 1: CV vs Test recall@20% song song mọi cấu hình (dumbbell hoặc paired dot) — trực quan bảng G1.
   - Hình 2: grouped bar recall@20% theo (mô hình × nửa đọc nhanh/chậm), nhãn số bài dưới 6 mỗi nửa — trực quan G3.
   - Hình 3: phân bố giây/từ trên test với vạch trung vị + số câu/bài dưới 6 mỗi nửa (hoặc histogram có vạch) — giải thích cơ sở phép kiểm.
4. **Ảnh Terminal Windows:** cửa sổ PowerShell **thật** chạy `python week11_analysis.py && python make_figure_week11.py` (output vừa hiện vừa tee vào log), chụp cửa sổ ra `terminal_week11_run_win.png` (+1 ảnh nếu chia 2 cửa sổ). **ĐÃ SPIKE THÀNH CÔNG (27/10, temp/opencode/spike_capture)** — chuỗi chắc chắn:
   - `Start-Process powershell -PassThru` → poll `$p.Refresh()` + `$p.MainWindowHandle` tới khi ≠ 0 (cần poll; `FindWindow` theo title thì fail) → `ShowWindow(h, 9)` → `GetWindowRect` → **`PrintWindow(h, hdc, 2)`** → `Bitmap.Save(png)`.
   - **Dùng `PrintWindow` flags=2**: ảnh sạch riêng cửa sổ, chữ rõ. **Không** dùng `CopyFromScreen` (bị lẫn cửa sổ khác chồng lên).
   - Không đổi được title cửa sổ qua `-Command` (2 cách thử đều fail) → chụp theo `MainWindowHandle`, vô hại.
   - Mỗi lần chạy phải đo lại trước khi đóng cửa sổ; nếu capture lỗi thì để user chụp tay, số liệu không đổi.
5. **Dựng báo cáo:** `build_report.py` bản tuần 11 (khung Kết quả chính, tiêu đề gạch chân, bảng ba đường kẻ — nội dung mới, bố cục thay một chút), `package.py` (danh sách file ZIP mới, README.txt mới, SHA256), `embed_packages.cjs` (đổi source zip), `embed_report.py` (label "MINH CHỨNG TUẦN 11"); reuse `cfb.js`.
6. **Cấu trúc báo cáo (mục 1–11):** (1) đối chiếu 5 việc thầy yêu cầu tuần 10; (2) dữ liệu/target — tóm gọn, không lặp dài; (3) **bảng CV đầy đủ** — trái tim báo cáo; (4) wav2vec thêm gì ngoài tốc độ: bảng CV 3 dòng; (5) phép kiểm nửa nhanh/chậm — bảng 2×2; (6) nhóm total ≤ 2 + bảng 5 câu với cột trống nghe; (7) thí nghiệm phụ LR-w2v; (8) nhãn tuần/ngày đã đính chính; (9) kết luận + đề xuất giữ wav2vec; (10) chuẩn bị vấn đáp; (11) thời gian chạy; Phụ lục ảnh Terminal + OLE.
7. **Soát trang:** `soffice --headless --convert-to pdf` → `pdftoppm`/đọc PDF từng trang, sửa tới khi không lỗi; kiểm tra `document.xml/styles.xml/footer` toàn chữ đen + TNR.
8. **Xác minh cuối:** chạy lại build → hash/OLE assert có sẵn trong `embed_report.py`, mở check bằng Word nếu user có (ghi chú "mới kiểm LibreOffice" nếu chưa).

## What's left to the builder (không cần người dùng trả lời)

- Chi tiết kỹ thuật từng hình, style chart, cách tee log khi chạy cửa sổ ẩn/hiện.
- Thứ tự lệnh build/package/embed trên Windows (theo pipeline tuần 10, đã ghi trong AGENTS.md).
- Cách nhúng `worst5/*.WAV` (copy từ `week10_work\worst5` hoặc re-copy từ WAVE gốc — cả hai đều được).
