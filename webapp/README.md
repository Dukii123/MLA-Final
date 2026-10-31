# Demo MLA Nhóm 05 — báo cáo tuần 11

Web UI chạy **local** để trình bày và dạy lại kết quả tuần 11: xếp hạng 2.500 bài test theo mức ưu tiên nghe lại, chấm thử một file audio, và phần học & vấn đáp.

Toàn bộ số liệu lấy từ lần chạy thật ngày 27/10/2026 trong `docs/report/week11_work`. Không có số nào được chỉnh cho đẹp.

## Chạy nhanh (macOS)

Bấm đúp `start.command` trong Finder, hoặc mở Terminal:

```bash
cd webapp
./start.sh
```

Trình duyệt tự mở `http://127.0.0.1:8000`. Dừng bằng `Ctrl+C`.

Lần đầu nạp wav2vec có thể mất 30–60 giây; góc phải hiện “Đang nạp wav2vec…” rồi chuyển “Sẵn sàng · dữ liệu cục bộ”. Trọng số `facebook/wav2vec2-base` (363 MB) đã nằm trong `models/wav2vec2-base/`, nên demo chạy **offline**; chỉ cần mạng khi cài lại `requirements.txt`.

Nếu chuyển sang máy khác, tạo lại môi trường (cần Python 3.12 và ffmpeg):

```bash
cd webapp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./start.sh
```

## Dữ liệu không nằm trong git

`webapp/data/speechocean762/` (audio) và `webapp/models/wav2vec2-base/` (363 MB) bị loại khỏi git để repo nhẹ. Khi clone:

- tải dataset tại https://www.openslr.org/101/, giải nén để có `webapp/data/speechocean762/WAVE/`;
- tải `facebook/wav2vec2-base` vào `webapp/models/wav2vec2-base/`, hoặc để transformers tự tải (cần mạng lần đầu).

Các JSON nhỏ, ảnh và 4 model `.joblib` vẫn có trong git.

## Bốn phần trong UI

- **Tổng quan** — con số mở bài: recall@20% 77% (253/330 bài dưới 6), so với chỉ-độ-dài 70% và ngẫu nhiên 20%; bảng 11 mô hình kèm CV; ba hình của báo cáo.
- **Giáo viên dùng** — chọn ngân sách 10/20/30%, xếp hạng theo mô hình, nghe thử, chỉ hiện điểm thật khi bấm “Lộ điểm”. Xuất CSV được danh sách ưu tiên.
- **Chấm thử** — kéo thả file, ghi âm trực tiếp, hoặc dùng câu mẫu. Trả về điểm wav2vec, xếp hạng trong 2.500 bài, mức ưu tiên, P(dưới 6) và điểm của 3 mô hình. Ngay dưới khu chấm là **phiếu chấm tay cho nhóm** (luôn hiện; bấm nút “Chấm tay cho nhóm…” ở đầu tab để nhảy tới): app đo tốc độ và tìm các khoảng lặng, nhóm nghe cả bài hoặc từng khoảng ngắt rồi chấm Nhanh/Vừa/Chậm và Đúng/Sai, lưu phiếu và xuất CSV.
- **Học & vấn đáp** — ba câu thầy đã nêu, kịch bản demo 5 phút, trung vị, độ nén dự đoán, recall, 5 câu worst5 kèm ghi chú nghe.

## Phiếu chấm tay của nhóm

- App chỉ đo **giây/từ** (khi có câu đọc) và các **khoảng lặng ≥ 0,25 giây**. App không nhận diện từ, không biết ngắt đúng hay sai về nghĩa.
- Nhóm nghe bằng nút “Nghe cả bài” hoặc ▶ ở từng khoảng ngắt, rồi tự chọn tốc độ và đánh dấu từng chỗ ngắt Đúng/Sai. “Sai” nghĩa là chỗ ngắt làm câu vỡ nghĩa hoặc ngắt giữa cụm.
- Phiếu lưu trong **localStorage của trình duyệt** trên máy đang chạy demo. Xoá dữ liệu trình duyệt là mất phiếu; nên bấm **Xuất CSV** sau mỗi buổi chấm.
- CSV dùng `;` làm dấu phân cách và có BOM để mở đúng tiếng Việt trong Excel.

## Chấm thử: giới hạn cần nói đúng

- Audio chỉ xử lý trên máy này, không gửi lên mạng.
- Tối đa **25 MB** và **30 giây** một file.
- Đây là công cụ **xếp hạng để nghe lại**, không phải điểm chấm chính thức.
- File tải lên **không có điểm thật**; chỉ câu mẫu lấy từ test mới có 5 điểm giám khảo.
- Model dồn dự đoán về giữa thang (12 bài total ≤ 2 đều được dự đoán khoảng 7), nên không đọc điểm như năng lực tuyệt đối.
- File tải lên được giữ tạm trong `data/uploads/` để nghe lại từng khoảng ngắt (tối đa 60 file hoặc 24 giờ, tự dọn khi khởi động/chấm bài). Đây vẫn là dữ liệu cục bộ.

## Cấu trúc

```
webapp/
  start.sh, start.command   # chạy demo
  requirements.txt
  app.py                    # FastAPI: API + file audio
  ml.py                     # trích đặc trưng, chấm một file
  prepare_data.py           # sinh JSON/hình từ kết quả tuần 11
  train_export.py           # huấn luyện lại model demo
  data/
    utterances.json         # 2.500 bài test
    results.json, meta.json # số liệu tuần 11
    test_predictions_week11.csv
    speechocean762/WAVE     # đủ 5.000 file WAV (667 MB)
    worst5/                 # 5 câu sai nặng
    uploads/                # audio tải lên gần nhất, để nghe lại khoảng ngắt
  models/                   # 4 model .joblib + meta
    wav2vec2-base/          # trọng số wav2vec 2.0 (363 MB), chạy offline
  static/                   # HTML/CSS/JS, Chart.js, hình báo cáo
```

Bản nén gốc `speechocean762.tar.gz` (520 MB) đã được xoá ngày 31/10/2026 để tiết kiệm dung lượng; thư mục `WAVE` vẫn giữ đủ 5.245 file WAV. Nếu cần bản nén, tải lại tại https://www.openslr.org/101/.

## Tài liệu cũ

Báo cáo, nhận xét và các thư mục tuần 08–11 nằm trong `../docs/`. Các script `prepare_data.py` / `train_export.py` trỏ tới `docs/report/...` nếu cần dựng lại dữ liệu.
