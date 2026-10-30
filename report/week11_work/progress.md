# SDD ledger — plan: C:\Users\DucAnh\Desktop\Hanu\MLA\report\week11_work\2026-10-27-week11-plan.md

## Resolutions
- Việc 4: chỉ ghi đính chính trong tuần 11; nhãn link bảng đăng ký đã đổi → ghi "đã làm". (người dùng trả lời 27/10)
- Mục 11 chỉ nêu số lần chạy có ảnh Terminal tuần này; bỏ bảng pilot/extract tuần 10.
- speakers/ages/raters: chỉ để trong JSON/CSV (minh chứng), không tạo mục riêng trong báo cáo; mục vấn đáp dùng raters của lần chạy này.
- worst5: assert trùng 5 ID với week10_results.json; lệch thì dừng hỏi người dùng.
- Plan wrong handling: file `verify_week11.py` nằm ở week11_work và đọc JSON cùng thư mục (đúng như plan).

## Progress
- [x] Task 1: week11_analysis.py chạy thử 283,4 s; verify_week11.py PASS; recall/MAE 9 mô hình cũ trùng week10 (wav2vec R@20 77%, MAE 0,772, PCC 0,711). worst5 trùng 5 ID.
- [x] Task 2: make_figure_week11.py vẽ 3 hình; đã sửa 3 lần bố cục nhãn và kiểm tra bằng mắt (Hình 1 lollipop không còn chồng số; Hình 2 cột ghép; Hình 3 histogram + trung vị).
- [x] Task 3: lần chạy chính thức 17:51–17:55 ngày 27/10 (204,6 s) trong cửa sổ PowerShell thật, ảnh `terminal_week11_run_win.png` 1183×838; verify_week11 PASS; số test/CV trùng lần thử.
- [x] Task 4: build_report.py + verify_docx.py PASS; render LibreOffice 7 trang, đã sửa bảng worst5, canh caption Hình 2/3, giữ mục 11 khỏi rơi dòng, tăng ảnh Terminal lên 16 cm.
- [x] Task 5b: package.py 25 file, ZIP 3.965.542 byte; node nhúng OLE; embed_report.py xuất `report_week11\Group05_Week11_Report.docx` 4.432.621 byte; kiểm tra ZIP/OLE khớp.
- [x] Task 6: render bản cuối 7 trang (không trang trắng, không tràn bảng/cắt ảnh); kiểm tra toàn bộ chữ đen + Times New Roman; dọn file trung gian; viết README bàn giao trong `report_week11\`.

## Ghi chú nội dung đã sửa so với bản nháp
- LR cân bằng lớp trên wav2vec có CV 80,4% (cao nhất bảng) nhưng test 74% < SVR wav2vec 77%; báo cáo ghi đúng là "không đủ căn cứ đổi mô hình chính", không nói hồi quy thắng CV.
- Nửa đọc nhanh chỉ 36 bài dưới 6 → đã thêm cảnh báo sai số lớn khi so 50% và 78%.
- Hình 1 bỏ số CV trên hình; caption ghi "giá trị CV xem bảng ở Mục 3" (bảng trong báo cáo không đánh số).
- Mục 10 đổi "(Mục 3)" thành "(tính trong lần chạy này)" vì bảng Mục 3 không có P@10/R@10; "Bảng 5 câu" đổi thành "Bảng năm câu" để không đọc nhầm là Bảng số 5.
- Bảng worst5 đổi tiêu đề cột thành "w2v", "Nghe 1", "Nghe 2" và giãn cột "Năm điểm" để không bị bóp chữ.

## Bàn giao
- Bản nộp: `C:\Users\DucAnh\Desktop\Hanu\MLA\report_week11\Group05_Week11_Report.docx` (4.432.621 byte, SHA256 `31ec0008…3ebc`).
- Việc nhóm còn làm tay: nghe 5 câu bằng bộ nghe nhanh `listen_kit/worst5_nghe_nhanh.wav` (31,5 s) và phiếu `listen_kit/PHIEU_NGHE.md`, điền cột Nghe 1/2 rồi dựng lại; mở Word trên máy có Word kiểm OLE (máy này không cài Word); nhãn link bảng đăng ký đã xác nhận đổi ngày 27/10.
- Không sửa file tuần 10; các file dùng chung chỉ đọc từ `week10_work/`.
- Đã sửa lần cuối: Mục 11 nói rõ 205 giây là thời gian phân tích (hình vẽ chạy riêng) và bỏ mốc "24/10" không kiểm chứng được; chỉ ghi "bản trích sẵn của báo cáo tuần 10".
- Dựng lại lần cuối 18:06 ngày 27/10 sau khi sửa 2 tham chiếu chéo; render lại 7 trang, kiểm tra OLE 25 file và chữ đen/Times New Roman; hash mới `31ec0008…3ebc`.


