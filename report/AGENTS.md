# Dự án MLA — Nhóm 05 (lớp 61FIT4MLA)

Ghi chú bàn giao cho các phiên AI sau. Đọc hết file này trước khi làm. Trả lời người dùng bằng tiếng Việt.

## Đề tài
- Dự đoán điểm phát âm tổng mức câu trên **speechocean762** để **giáo viên ưu tiên nghe lại** bài đọc điểm thấp. Không chẩn đoán từng âm, không sinh bài luyện, không thu giọng Việt (đã bỏ theo góp ý thầy).
- Thầy hướng dẫn: thầy Khánh. Buổi kiểm tra là **mở report cho thầy vấn đáp, không làm slide**.
- Dữ liệu: 5.000 câu tiếng Anh đọc thành tiếng, 250 người nói tiếng Quan Thoại (có trẻ em), 5 giám khảo, CC BY 4.0.

## File trong thư mục MLA
| File | Nội dung |
|---|---|
| `Group05_Week08_Report.docx`, `Group05_Midterm.pdf` | Bản cũ, chỉ để tham khảo |
| `Group05_Week09_Report.docx` | Báo cáo tuần 9 (đã nộp) |
| `Group05_Week10_Report.docx` | Báo cáo tuần 10, bản mới nhất, 8 trang |
| `Group05_WeekXX_Attachments.zip` | Không còn để sẵn: `package.py` tạo lại ở thư mục gốc mỗi lần dựng report, rồi được nhúng vào Word; không nộp riêng |
| `Nhan_xet_*.docx` | Nhận xét của thầy: giữa kỳ, tuần 8, tuần 9 (bản ngắn) |
| `feedback/Nhan_xet_Week9_chinh_thuc.md` | Nhận xét tuần 9 bản chính thức, chi tiết (6 mục sửa); bản này người dùng dán vào chat |
| `week09_work/` | Code, dữ liệu, kết quả tuần 9; có `data/speechocean762/` (dataset đã giải nén, khoảng 700 MB; file .tar.gz đã xoá, cần thì tải lại) và `.venv/` |
| `week10_work/` | Code, kết quả, hình, ảnh Terminal tuần 10 |

## Môi trường (macOS, MacBook Air Apple M2, 8 nhân, RAM 8 GB)
- Python chạy phân tích: `week09_work/.venv/bin/python` (Python 3.12.14, NumPy 2.3.5, scikit-learn 1.7.2, matplotlib 3.10.7, torch 2.9.1, transformers 4.57.1, pyobjc-framework-Quartz).
- Python dựng Word (có python-docx, PIL): `/Users/chiseled/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`.
- Node (để tạo gói OLE): `/Users/chiseled/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node`.
- LibreOffice để render kiểm tra: `/Users/chiseled/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/libreoffice-headless/libreoffice/LibreOfficeDev.app/Contents/MacOS/soffice` (thêm `-env:UserInstallation=file://<thư mục tạm>`). `/opt/homebrew/bin/soffice` là symlink hỏng. Có `pdftoppm`. Không có `pandoc`.
- Model wav2vec 2.0: `facebook/wav2vec2-base` (đã có trong cache HuggingFace).
- Dataset: `week09_work/data/speechocean762/` (WAVE/, resource/, train/, test/ có spk2age).

## Yêu cầu cố định cho mọi báo cáo
- Nộp **một file Word .docx duy nhất**; minh chứng (ZIP gồm code, kết quả, log, ảnh) **nhúng trong Word** dưới dạng OLE Package.
- Times New Roman, giãn dòng 1,5, **toàn bộ chữ màu đen**. Tiếng Việt dễ hiểu, ngắn vừa phải.
- Phải có **biểu đồ**, và **ảnh chụp Terminal thật** của lần chạy. **Không dựng ảnh giả**, không sửa số cho đẹp.
- Mỗi số trong report phải lấy từ file kết quả (JSON/log) của lần chạy có trong ảnh Terminal. Chạy lại thì đồng bộ report, log, JSON, ZIP và ảnh.
- Phân biệt rõ việc **đã chạy** với **kế hoạch**; thứ gì "dự kiến, chưa đo" phải ghi như vậy.
- Biểu đồ mỗi hình một loại; màu theo loại đặc trưng: log-mel xanh `#2a78d6`, wav2vec 2.0 cam `#eb6834`, chỉ độ dài xanh lục `#1baf7a`, ngẫu nhiên xám `#8a8a86`.
- Tuần 10 dùng bảng ba đường kẻ ngang, khung "Kết quả chính" đầu trang, tiêu đề mục có gạch chân. Tuần sau nên đổi kiểu trình bày một chút, ảnh Terminal giữ như cũ.
- Render bằng LibreOffice và xem từng trang trước khi giao: không tràn bảng, không cắt ảnh, không trang trắng.
- Người dùng muốn làm tới nơi, hạn chế hỏi lại những gì đã rõ.

## Quy trình dựng report (tuần 10, chạy trong `week10_work/`)
```
PY=../week09_work/.venv/bin/python
$PY pilot_w2v.py && $PY week10_analysis.py && $PY make_figure_week10.py   # chạy trong Terminal thật rồi chụp
DOCPY=/Users/chiseled/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
NODE=/Users/chiseled/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
$DOCPY build_report.py && cp ../Group05_Week10_Report.docx report_before_embed.docx \
  && $DOCPY package.py && $NODE embed_packages.cjs && $DOCPY embed_report.py
```
- `build_report.py` đặt đoạn `[[OBJECTS]]` ở Phụ lục; `embed_report.py` đọc `report_before_embed.docx` và chèn ZIP vào đoạn đó. Dựng lại thì luôn copy sang `report_before_embed.docx` trước khi nhúng.
- `extract_w2v.py` (khoảng 13 phút CPU) tạo `features_w2v_layers.npz` (23 MB, không đưa vào ZIP). Không cần chạy lại trừ khi đổi tầng hoặc model.
- Tuần 9 dùng cùng quy trình trong `week09_work/` (`verify.py`, `train_models.py`, `make_figure.py`, rồi `build_report.py`, `package.py`, `embed_packages.cjs`, `embed_report.py`).

## Chụp ảnh Terminal thật (dễ sai, đọc kỹ)
- Terminal.app đã được cấp quyền Screen Recording. `screencapture` phải chạy **bên trong Terminal**: `osascript -e 'tell application "Terminal" to do script "screencapture -o -x -l<ID> <file>; exit"'`. Gọi trực tiếp từ tiến trình AI sẽ báo "could not create image from display".
- Mở cửa sổ riêng bằng `do script`, đặt `number of columns/rows` **trước** `clear`, rồi mới chạy lệnh. Đặt biến `PY=...` trước `clear` để dòng lệnh ngắn, không bị xuống dòng.
- **Không dùng `close every window`**: người dùng có phiên **opencode** đang mở trong Terminal. Chỉ đóng các cửa sổ do mình tạo, theo id.
- Lấy CGWindowID thật bằng Quartz (`week09_work/.venv/bin/python`, `Quartz.CGWindowListCopyWindowInfo`), lọc theo tên cửa sổ có `week10_work`. Sau khi chụp, **kiểm tra thời gian sửa file ảnh và mở ảnh ra xem**: đã từng xảy ra trường hợp chụp không ghi đè file nên vẫn thấy ảnh cũ.
- Lệnh `screencapture ... ; exit` có thể để lại cửa sổ thừa; dọn đi theo id.

## Kết quả hiện tại (tuần 10, chạy lúc 10:09 ngày 21/10/2026)
- Total trong scores.json = floor(trung vị năm điểm), khớp 5.000/5.000. Từ tuần 10, target chính là total này; trung bình năm điểm là phân tích phụ. "Dưới 6" = total < 6; test có 330/2.500 bài (13,2%).
- Train = 125 người train chính thức; chọn tham số bằng GroupKFold 5 phần theo người nói; test chạy một lần.
- Recall@20% trên test: ngẫu nhiên 20%, SVR log-mel 67%, RF 71%, SVR chỉ độ dài 70%, log-mel bỏ độ dài 53%, có trọng số 68%, LR phân loại cân bằng 71%, RF phân loại 68%, **SVR wav2vec 2.0 77%** (MAE 0,772, PCC 0,711).
- Kết luận: đổi đặc trưng giúp nhiều hơn đổi cách học. Phần lớn tín hiệu của log-mel đến từ độ dài câu (tốc độ đọc). Mô hình vẫn dồn điểm về giữa thang.
- Chạy thử 50 câu wav2vec 2.0: CPU khoảng 83 ms/câu, GPU Apple (MPS) khoảng 88 ms/câu; dao động giữa các lần chạy. Trích thật 5.000 câu trên CPU mất 796 giây.
- GOP: link Dropbox của tác giả GOPT bị khóa ("Link Temporarily Disabled"). Đã quyết định bỏ GOP ngày 21/10/2026.

## Việc còn mở
1. **Nhóm phải tự nghe 5 câu bị đoán sai nặng nhất** (`week10_work/worst5/*.WAV`, cũng có trong ZIP) và ghi lại điều nghe được vào Mục 9 của report tuần 10. Không được tự bịa nội dung audio. Cả 5 câu có total = 0 nhưng mô hình đoán khoảng 7.
2. Tuần 11: thí nghiệm chính theo hướng đặc trưng (wav2vec 2.0). Có thể thử LR cân bằng lớp trên embedding wav2vec 2.0, so recall@10% của phân loại với hồi quy.
3. Mở report bằng Microsoft Word để kiểm tra; mới chỉ kiểm tra bằng LibreOffice. Audio/ZIP nhúng chỉ chắc mở được trên Word cho Windows.

## Lưu ý kỹ thuật khác
- File trung gian (`report_before_embed.docx`, `evidence.bin`, `audio.bin`, `*_object.png`, file ZIP ở gốc) đã được dọn; quy trình dựng report tự tạo lại. Dọn xong thì xoá lại cho gọn.
- Lệnh `rm` với biến shell bị công cụ an toàn chặn; dùng `"${S:?}"` hoặc đường dẫn tuyệt đối, hoặc tạo thư mục render mới.
- Muốn ghi đè một file bằng công cụ Write thì phải đọc file đó trước.
- Hostname máy đã đổi thành `MacBook-Air-cua-Nguyen-5` nên dấu nhắc lệnh dài; cần đặt cửa sổ Terminal đủ rộng.
- Kiểm tra màu và font chỉ trong `word/document.xml`, `word/styles.xml`, `word/footer1.xml`; các phần theme hay numbering mặc định của Word có màu và font khác nhưng không hiển thị.

## Máy Windows (24/10/2026) — đã chạy lại đủ tuần 10
- Python hệ thống `C:\Users\DucAnh\AppData\Local\Programs\Python\Python314\python.exe` (3.14.5): NumPy 2.5.2, scikit-learn 1.9.1, torch 2.14.1+cpu, transformers 5.20.2, matplotlib 3.11.2, datasets 5.1.0. Không có `.venv` trên máy này; torch là wheel CPU nên pilot chỉ đo CPU.
- Bản dataset gốc ở `week09_work\data\speechocean762` từng thiếu WAVE (176/5000); đã dựng lại đủ 5000 file .wav từ 2 parquet tại `MLA\speechocean762\data` (kiểm tra 5000/5000 khớp `split_manifest.csv`). `resource\`, `train\`, `test\` còn đủ.
- Kết quả tuần 10 của lần chạy này lưu ở `MLA\report_week10\` (README.md liệt kê đủ); số chỉ chính trên test: SVR wav2vec 2.0 R@20 77%, MAE 0,772, PCC 0,711 (trùng Mac); LR phân loại 68% thay vì 71% do sklearn khác phiên bản. Extract 1499 s (300 ms/câu), analysis 96,5 s, pilot 222 ms/câu.
- Kết quả Mac cũ (21/10/2026) lưu ở `report\week10_work\lac_mac_20261021\`; các file JSON/CSV/fig trong `week10_work` giờ là của lần chạy Windows.
- `make_figure_week10.py` đã sửa nạp font để chạy được cả macOS và Windows; matplotlib 3.11 chỉ cảnh báo `vert` của boxplot, vô hại.
- Chưa chụp ảnh Terminal trên Windows và **chưa dựng report** — người dùng dặn chỉ chạy và lưu kết quả.
- **Cập nhật đêm 24 → 25/10/2026**: đã chụp 3 ảnh Terminal thật trên Windows khi chạy đủ 4 bước lần cuối
  (extract 1485 s, pilot 222 ms/câu, analysis 146,4 s) và **dựng xong `report_week10\Group05_Week10_Report.docx`**
  (5,7 MB, nhúng OLE 31 file). Thư mục `report_week10\` là bản nộp của máy này; bản Mac 21/10 ở
  `report\Group05_Week10_Report.docx` không đụng tới. build_report.py / embed_report.py giờ nhận đường
  dẫn output qua argv[1] (mặc định như cũ); package.py dùng ảnh `terminal_*_win.png` và requirements phiên
  bản máy Windows; make_figure + embed đã vẽ/nạp font hai nền macOS–Windows. Việc còn mở: nhóm tự nghe
  5 câu `worst5\` ghi Mục 9; mở báo cáo mới bằng Microsoft Word kiểm tra nhúng OLE/LibreOffice render.
