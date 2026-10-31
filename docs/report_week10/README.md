# Kết quả chạy dataset tuần 10 — Nhóm 05 (61FIT4MLA)

Kết quả lần chạy **Windows đêm 24 → 25/10/2026**: cả 4 bước tuần 10 chạy lại đầy đủ trong cửa sổ
Terminal thật trên máy này, được chụp minh chứng, rồi dựng **bản báo cáo Word mới**.
Code gốc và file đặc trưng trung gian nằm ở `report\week10_work\`; thư mục này cất **bản lưu + file nộp**.
Thư mục này là bản lưu và file nộp của lần chạy Windows; không đối chiếu với bản Mac.

## Môi trường lần chạy này
- Windows, Python 3.14.5, NumPy 2.5.2, scikit-learn 1.9.1, torch 2.14.1+cpu, transformers 5.20.2, matplotlib 3.11.2
- Chỉ dùng CPU (torch là wheel CPU); máy có NVIDIA RTX 2050 nhưng không dùng được vì wheel
- Model: `facebook/wav2vec2-base` (huấn luyện sẵn, không fine-tune), đã tải về cache HuggingFace 24/10/2026

## Chuẩn bị dữ liệu
- Bản dataset gốc ở `report\week09_work\data\speechocean762` chỉ còn 176/5000 file WAVE.
- Đã dựng lại **5000 file .wav** từ 2 file parquet của HuggingFace tại `MLA\speechocean762\data`
  (train 2500 + test 2500), tên file và thư mục `SPEAKER####` giữ nguyên như bản gốc.
- Kiểm tra: 5000/5000 câu trong `split_manifest.csv` đều có file wav (0 thiếu).
- `resource\scores.json`, `resource\scores-detail.json`, `train\spk2age`, `test\spk2age` (125 + 125 người) còn đủ.

## Đã chạy (lần chính thức có minh chứng)
1. `extract_w2v.py ... cpu` — 5000 câu, 5,57 giờ audio, **1485 s ≈ 25 phút** (Hình 5: `terminal_w2v_extract_win.png`)
2. `pilot_w2v.py` — 50 câu, CPU **222 ms/câu** (~11 s) (Hình 6: `terminal_pilot_win.png`)
3. `week10_analysis.py` — **146,4 s**, 9 mô hình + CV + phân tích (Hình 7)
4. `make_figure_week10.py` — 4 hình + `figure_stats.json` + `figure_run.log` (cùng cửa sổ Hình 7)

## Báo cáo Word mới của nhóm
- **`Group05_Week10_Report.docx` (~5,7 MB)**: dựng trực tiếp từ JSON/log của lần chạy trên,
  đã nhúng gói minh chứng OLE (mở Word → nháy đúp biểu tượng → Open).
- Gói minh chứng gồm 31 file: 4 script tuần 10, `split_manifest.csv`, `scores.json`, `scores-detail.json`,
  `features_logmel_stats.npz`, kết quả/log/CSV dự đoán, 4 hình + 3 ảnh Terminal, `worst5\*.WAV`,
  `README.txt`, `requirements.txt`, `SHA256.json` (mỗi file đã kiểm tra hash).
- Nội dung theo khuôn mẫu tuần 10: khung "Kết quả chính", bảng ba đường kẻ, mục 1–11, Hình 1–7,
  Phụ lục minh chứng; ngày đầu trang 25/10/2026; mô tả laptop Windows CPU-only.

## Kết quả chính (test, chạy một lần — trích `week10_run.log`)
| Mô hình | R@10 | P@10 | R@20 | P@20 | MAE | PCC |
|---|---|---|---|---|---|---|
| Ngẫu nhiên / hằng số | 10% | 13% | 20% | 13% | 1,190 | n/a |
| SVR log-mel | 48% | 64% | 67% | 44% | 0,902 | 0,598 |
| RF log-mel | 48% | 64% | 71% | 47% | 0,913 | 0,598 |
| SVR chỉ độ dài | 48% | 64% | 70% | 46% | 0,875 | 0,592 |
| SVR log-mel bỏ độ dài | 35% | 47% | 53% | 35% | 1,011 | 0,447 |
| SVR log-mel + trọng số | 47% | 62% | 68% | 45% | 0,915 | 0,587 |
| LR phân loại cân bằng | 48% | 64% | 68% | 45% | — | — |
| RF phân loại cân bằng | 40% | 53% | 68% | 45% | — | — |
| **SVR wav2vec 2.0** | **52%** | **68%** | **77%** | **51%** | **0,772** | **0,711** |

- Target check: floor(trung vị 5 điểm) == total khớp **5000/5000**; test dưới 6: 330/2500 (13%).
- Nghe lại 30% bài thấp nhất bắt được bài dưới 6: chỉ độ dài 80%, log-mel 83%, wav2vec 2.0 88%.
- Trẻ em 52 người (68 bài dưới 6, MAE 0,86 → 0,81); người lớn 73 người (262 bài, MAE 0,93 → 0,74).
- 5 câu đoán sai nặng nhất (total = 0 nhưng đoán 6,7–7,2) ở `worst5\` — nhóm cần tự nghe rồi ghi Mục 9.

## Chú ý khi đối chiếu
- Kết quả tái hiện ổn định: chạy lần 1 (22:30) và lần chính thức (0:47) cho **cùng toàn bộ bảng test**.
- `make_figure_week10.py` đã sửa dòng nạp font thành có điều kiện (Windows tự tìm font hệ thống);
  matplotlib 3.11 chỉ cảnh báo `vert` trong boxplot, không ảnh hưởng hình.
- `features_w2v_layers.npz` (~21 MB) không cất ở đây; chạy lại `extract_w2v.py` nếu cần (~25 phút trên máy này).
- Trước đặt cây Task khi nghe audio: **không nhấp chuột vào cửa sổ PowerShell đang chạy** — chế độ
  selection (chọn văn bản) của console làm đầu ra bị chặn, dễ tưởng treo máy (đã gặp lúc 23:3x đêm 24/10).
