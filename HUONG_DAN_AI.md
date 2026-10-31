# Hướng dẫn cho AI đọc dự án MLA-Final

**Cập nhật:** 31/10/2026
**Chủ dự án:** Nhóm 05, lớp 61FIT4MLA, môn MLA — báo cáo cho thầy Khánh.
**Repo:** `/Users/chiseled/Documents/Github/MLA-Final`

File này để dán vào một cuộc chat khác. Nó cho AI biết dự án làm gì, số nào là số thật, file nào chứa gì, và cách đọc file nếu có quyền truy cập máy. Nếu AI không đọc được file, vẫn trả lời được từ số liệu trong đây; không được bịa thêm.

## 0. Quy tắc bắt buộc khi trả lời

1. Không bịa số, không bịa ghi chú nghe, không tự suy ra nội dung 5 câu worst5.
2. Mỗi số phải chỉ được nguồn: file nào, khóa nào. Nếu không chắc, nói "chưa kiểm chứng".
3. Phân biệt rõ: số **đo được** trong lần chạy 27/10, số **của app demo** xuất ngày 31/10, và phần **chưa làm** (nghe 5 câu).
4. Đây là công cụ **xếp hạng để nghe lại**, không phải điểm chấm chính thức. Không nói "độ chính xác 77%".
5. Audio và dữ liệu chỉ chạy local, không gửi lên mạng.
6. Trả lời bằng tiếng Việt, ngắn, thẳng vào câu hỏi.

## 1. Tóm tắt dự án

Dự án dự đoán điểm phát âm mức câu trên bộ **speechocean762** (5.000 câu, 250 người nói tiếng Quan Thoại, 5 giám khảo, CC BY 4.0), rồi dùng điểm dự đoán để **xếp thứ tự ưu tiên nghe lại** cho giáo viên. Giáo viên có ngân sách nghe hữu hạn, nên chỉ số chính là **recall@20%**: trong 20% bài bị xếp thấp nhất, bắt được bao nhiêu bài thật sự dưới 6.

- Nhãn đúng (`total`) = **trung vị năm điểm, làm tròn xuống**. Kiểm tra khớp 5.000/5.000 câu.
- Chia 2.500 train / 2.500 test theo người nói (125 + 125 speaker).
- Tập test có **330/2.500 bài dưới 6** (tỉ lệ nền 13,2%).
- Mô hình chính: **SVR trên embedding wav2vec 2.0** (wav2vec đóng băng, không fine-tune; lấy trung bình theo thời gian của tầng 8, 768 chiều).
- Kết quả chính: recall@20% test **77%** (253/330), precision@20% **51%**, MAE **0,772**, PCC **0,711**. Chỉ-độ-dài 70%; log-mel 67%; ngẫu nhiên 20%.

## 2. Trạng thái hiện tại (31/10/2026)

**Đã xong:**

- Web app local 4 tab, chấm thử bằng upload/ghi âm, phiếu chấm tay cho nhóm, xuất CSV; đã test end-to-end.
- Model và dữ liệu offline: 4 file `.joblib`, wav2vec2-base 363 MB, 5.245 file WAV.
- Phân tích tuần 11: bảng CV 10 cấu hình, phép kiểm nửa đọc nhanh/chậm, thống kê nhóm total ≤ 2, 3 hình, ảnh Terminal thật.
- Bản báo cáo Week 11 cuối (4.432.621 byte, 7 trang) nằm trên **máy Windows của bạn DucAnh**, không nằm trong repo Mac này.
- Bản dựng trong repo: `docs/report/week11_work/test_blank.docx` — cùng nội dung nhưng cột Nghe 1/2 để trống và ghi "chưa thực hiện".

**Chưa xong:**

- **Nghe 5 câu worst5**: mỗi câu cần ít nhất 2 người nghe độc lập, ghi lại thực tế nghe được. Đây là việc thầy sẽ hỏi. Hiện `listening_notes.json` vẫn là chữ giả ("Ghi chu thu mot hai ba..."), không được dùng.
- Bản cuối 4,4 MB trên Windows phải mở kiểm cột Nghe 1/2 trước khi nộp; nếu vẫn là chữ giả thì chưa dùng được.
- Đã commit ngày 31/10: docs, webapp, guide, `.gitignore` (commit `3244979`), sau đó bổ sung hướng dẫn Windows và `start.bat`. Các file nặng (`.venv`, WAVE, trọng số wav2vec, uploads) bị gitignore và vẫn nằm trên máy.

**Đã dọn ngày 31/10:** xoá file nén dataset 520 MB (đã đối chiếu đủ 5.245 WAV), xoá bản WAVE tuần 9 trùng 622 MB, xoá `test_notes.docx` chứa ghi chú giả, xoá `.DS_Store`/`__pycache__`. Repo còn khoảng: `docs` 127 MB, `webapp` 1,7 GB (venv 688 MB + data 670 MB + models 377 MB).

## 3. Bản đồ file

| Đường dẫn | Nội dung |
|---|---|
| `webapp/README.md` | Hướng dẫn chạy app, giới hạn, cấu trúc |
| `webapp/start.sh`, `start.command`, `start.bat` | Khởi động uvicorn localhost:8000 |
| `webapp/app.py` | FastAPI, API chấm và file audio |
| `webapp/ml.py` | Trích đặc trưng, chấm một file, đo tốc độ/khoảng lặng |
| `webapp/prepare_data.py` | Sinh JSON/hình từ kết quả tuần 11 |
| `webapp/train_export.py` | Huấn luyện lại model demo |
| `webapp/data/utterances.json` | 2.500 câu test: điểm, dự đoán, audio |
| `webapp/data/results.json` | Toàn bộ số liệu tuần 11 (bản sao giống hệt `week11_results.json`) |
| `webapp/data/meta.json` | Số liệu tóm tắt cho UI |
| `webapp/data/test_predictions_week11.csv` | 2.500 dòng dự đoán từng câu của 11 mô hình |
| `webapp/data/speechocean762/WAVE/` | 5.245 file WAV đầy đủ |
| `webapp/data/worst5/` | 5 câu sai nặng nhất |
| `webapp/data/uploads/` | Audio người dùng tải lên, tự dọn (60 file / 24 giờ) |
| `webapp/models/*.joblib` | SVR wav2vec, SVR log-mel, SVR độ dài, LR wav2vec |
| `webapp/models/wav2vec2-base/` | Trọng số wav2vec 2.0 local, 363 MB |
| `webapp/static/` | HTML/CSS/JS, Chart.js, 3 hình báo cáo |
| `docs/report/week11_work/` | Script phân tích, JSON/log, hình, listen kit, bản dựng báo cáo |
| `docs/report/week11_work/week11_results.json` | Nguồn số gốc tuần 11 |
| `docs/report/week11_work/week11_run.log` | Log lần chạy chính thức 27/10 |
| `docs/report/week11_work/terminal_week11_run_win.png` | Ảnh Terminal thật (1183×838) |
| `docs/report/week11_work/test_predictions_week11.csv` | Dự đoán từng câu (bản gốc) |
| `docs/report/week11_work/worst5/` | 5 WAV worst5 |
| `docs/report/week11_work/listen_kit/` | Bộ nghe worst5: WAV 31,5 giây, phiếu, ASR Windows |
| `docs/report/week11_work/test_blank.docx` | Báo cáo 7 trang, cột nghe để trống (bản trung thực) |
| `docs/report/week11_work/2026-10-27-week11-plan.md` | Kế hoạch và các việc thầy giao |
| `docs/report/week11_work/progress.md` | Nhật ký hoàn thành, nơi lưu bản nộp |
| `docs/Nhan_xet_Week10_DT_Group05.docx` | Nhận xét tuần 10 của thầy (5 việc) |
| `docs/report/Group05_Week10_Report.docx` | Báo cáo tuần 10 (không phải tuần 11) |
| `docs/report_week10/` | Bản cuối + minh chứng tuần 10 |
| `docs/report/week09_work/` | Minh chứng tuần 9 (đã xoá bản WAVE trùng) |

## 4. Số liệu gốc

### 4.1. Dữ liệu và target

- 5.000 câu, 250 người nói, 5 giám khảo, 5,57 giờ audio, CC BY 4.0.
- Train 2.500 câu / 125 speaker; test 2.500 câu / 125 speaker.
- Test: 330 câu dưới 6 (13,2%); train: 425/2.500.
- `total` = floor(trung vị 5 điểm). Khớp 5.000/5.000.
- Trong `results.json`, `target_check` là **số đếm**, không phải điểm: `floor_median: 5000`, `round_median: 2905`, `median_exact: 1370`, `mean_exact: 52`.
- Test có **12 câu total ≤ 2**.

### 4.2. Bảng CV và test (10 cấu hình + ngẫu nhiên)

| Mô hình | R@20% CV (TB ± SD) | MAE CV | R@20% test | MAE test |
|---|---|---|---|---|
| SVR log-mel | 78% ± 13 | 0,911 ± 0,051 | 67% | 0,902 |
| RF log-mel | 77% ± 10 | 0,909 ± 0,031 | 71% | 0,913 |
| SVR chỉ độ dài | 73% ± 13 | 0,885 ± 0,086 | 70% | 0,875 |
| SVR log-mel bỏ độ dài | 70% ± 11 | 1,029 ± 0,040 | 53% | 1,011 |
| SVR log-mel + trọng số | 79% ± 13 | 0,908 ± 0,047 | 68% | 0,915 |
| LR phân loại cân bằng | 76% ± 9 | — | 68% | — |
| RF phân loại cân bằng | 78% ± 9 | — | 68% | — |
| **SVR wav2vec 2.0** | **80% ± 10** | **0,797 ± 0,047** | **77%** | **0,772** |
| SVR wav2vec + độ dài | 80% ± 10 | 0,795 ± 0,047 | 77% | 0,771 |
| LR phân loại cân bằng (wav2vec) | 80% ± 8 | — | 74% | — |
| Ngẫu nhiên / hằng số | — | — | 20% | 1,190 |

Số chính xác của SVR wav2vec: CV R@20% 0,7978 ± 0,1039; test R@20% 0,7667; precision@20% 0,506; MAE 0,7719; PCC 0,7109; R@10% 0,518; P@10% 0,684; 253/330 bài dưới 6, còn **77 bài lọt**.

LR wav2vec có CV 80,4% so với 79,8% của SVR wav2vec, nhưng test 74% so với 77%. Chênh lệch nằm trong độ lệch chuẩn giữa fold (8–13 điểm %), nên nhóm giữ SVR.

### 4.3. Nửa đọc nhanh / đọc chậm

Chia theo trung vị **0,578 giây/từ**:

| Nửa | Số câu | Dưới 6 | R@20% chỉ độ dài | R@20% wav2vec |
|---|---:|---:|---:|---:|
| Đọc nhanh (< 0,58 s/từ) | 1.248 | 36 | 50% | 78% |
| Đọc chậm (≥ 0,58 s/từ) | 1.252 | 294 | 54% | 58% |

wav2vec hơn chỉ-độ-dài 28 điểm % ở nửa nhanh và 4 điểm % ở nửa chậm. Nửa nhanh chỉ có 36 bài dưới 6 nên sai số lớn; nửa chậm mới đáng tin hơn.

### 4.4. Nhóm total ≤ 2

12 câu. Điểm dự đoán trung bình: log-mel 7,00; chỉ-độ-dài 6,94; wav2vec 6,95. Cả **12/12** câu đều được đoán > 5 điểm. MAE trên nhóm này khoảng 6,36–6,42.

### 4.5. Năm câu worst5 (total 0)

| Mã | Câu đọc | Năm điểm | Total | w2v / log-mel | Giây | Số từ |
|---|---|---|---:|---|---:|---:|
| 014040089 | HERE IS TIM'S CAP | 0 · 1,2 · 0,8 · 1,2 · 0 | 0 | 7,16 / 7,15 | 3,80 | 6 |
| 069020059 | THEY DID NOT SEE THEM ANY MORE | 0 · 0 · 0 · 2,4 · 0 | 0 | 7,33 / 7,09 | 3,88 | 7 |
| 014040122 | HEY WATCH OUT FOR MY CUCUMBER | 0,41 · 0,81 · 0 · 1,07 · 1,07 | 0 | 7,12 / 7,07 | 4,04 | 6 |
| 014040090 | HERE IS MARY'S SHOES | 0,2 · 0 · 0 · 0 · 0,8 | 0 | 7,30 / 7,02 | 5,24 | 4 |
| 069020075 | SHE MUST BE MADE TO STAY | 0 · 0 · 0 · 0,79 · 0 | 0 | 7,53 / 6,65 | 3,80 | 6 |

Đây là **dự đoán**, không phải ghi chú nghe. Chưa ai nghe và xác nhận nguyên nhân (đọc sai câu, im lặng, tiếng ồn, lỗi thu âm...). Không được tự viết ghi chú nghe.

### 4.6. Số cho phần vấn đáp

- 448 câu có một giám khảo lệch ≥ 3 điểm so với trung vị bốn người còn lại.
- Ở nhóm đó, trung bình và trung vị cách nhau trung bình **0,59 điểm**, gấp đôi mức **0,27 điểm** trên toàn bộ dữ liệu.
- Ví dụ 015010033: năm điểm 8,3; 8,0; 10,0; 5,0; 2,27 → trung bình 6,71, trung vị 8,0, total 8,0.
- Bias trên bài dưới 6: log-mel đoán cao hơn thật **+2,20**; wav2vec **+1,77**.
- Nếu chỉ nghe 10%: wav2vec R@10% 52%, P@10% 68% (ngẫu nhiên 13%).

### 4.7. Thời gian và môi trường

- Lần chạy chính thức 27/10: phân tích 10 cấu hình + CV + phép kiểm nửa tốc độ mất **204,6 giây** (báo cáo ghi 205 giây), trên laptop Windows CPU, Python 3.14.5, scikit-learn 1.9.1. Ba hình vẽ chạy riêng sau đó.
- Embedding wav2vec dùng lại bản trích tuần 10: 5.000 câu, 18.153,8 giây CPU (khoảng 5,04 giờ), không trích lại.
- App demo hiện chạy Python 3.12.15, torch 2.9.1, transformers 4.57.1, scikit-learn 1.9.1, FastAPI 0.162.0.

## 5. Đọc file bằng lệnh

Nếu AI có quyền đọc máy, dùng các lệnh sau. Nếu không, bỏ qua phần này và dùng số ở mục 4.

```bash
cd /Users/chiseled/Documents/Github/MLA-Final
```

Đọc một câu test:

```bash
python3 - <<'PY'
import json
u = {r['id']: r for r in json.load(open('webapp/data/utterances.json'))}
print(json.dumps(u['014040089'], ensure_ascii=False, indent=2))
PY
```

Đọc metric của mô hình chính:

```bash
python3 - <<'PY'
import json
r = json.load(open('webapp/data/results.json'))
print(r['models']['SVR wav2vec 2.0']['test'])
print(r['halves'])
print(r['low_total'])
PY
```

Đọc một dòng dự đoán:

```bash
python3 - <<'PY'
import csv
rows = list(csv.DictReader(open('webapp/data/test_predictions_week11.csv')))
print(rows[0])
PY
```

Trích chữ từ báo cáo `.docx`:

```bash
python3 - <<'PY'
import zipfile, re
z = zipfile.ZipFile('docs/report/week11_work/test_blank.docx')
xml = z.read('word/document.xml').decode('utf-8', 'ignore')
txt = re.sub(r'</w:p>', '\n', xml)
txt = re.sub(r'<[^>]+>', '', txt)
print(txt[:4000])
PY
```

### Schema chính

`utterances.json` — mảng 2.500 object:

```text
id, speaker, age, text, words, five[5], total, below6,
sec_per_word, duration, pred{11 mô hình}, rand, audio
```

`results.json` — các khóa:

```text
python, sklearn, target, low_threshold, target_check, below6,
base_rate_test, max_recall10, models, cv_table, halves, low_total,
secondary_mean_target, speakers, ages, worst5, raters, w2v, pilot,
total_script_seconds
```

`test_predictions_week11.csv` — 17 cột, mỗi dòng một câu test:

```text
utterance_id, speaker_id, age, target_total, target_mean, sec_per_word,
SVR log-mel, RF log-mel, SVR chỉ độ dài, SVR log-mel bỏ độ dài,
SVR log-mel + trọng số, LR phân loại cân bằng, RF phân loại cân bằng,
SVR wav2vec 2.0, SVR wav2vec + độ dài, LR phân loại cân bằng (wav2vec),
Ngẫu nhiên / hằng số
```

Lưu ý: `webapp/data/results.json` và `docs/report/week11_work/week11_results.json` giống hệt nhau (cùng SHA256 `c21a7fd...`). `webapp/data/test_predictions_week11.csv` và bản trong `week11_work` cũng giống hệt (`1fe4c02...`). Đừng coi là hai bộ số khác nhau.

## 6. Web app

Chạy trên macOS:

```bash
cd /Users/chiseled/Documents/Github/MLA-Final/webapp
./start.sh
```

Trên Windows, mở PowerShell trong `webapp`:

```powershell
.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Hoặc bấm đúp `start.bat`. Mở `http://127.0.0.1:8000`. Dừng bằng `Ctrl+C`. Lần đầu nạp wav2vec mất 30–60 giây. App chạy **offline** sau khi cài đủ môi trường; audio không rời máy.

Bốn tab:

1. **Tổng quan** — 77% recall@20%, bảng 11 mô hình, 3 hình.
2. **Giáo viên dùng** — chọn ngân sách 10/20/30%, xếp hạng, nghe, "Lộ điểm thật", xuất CSV.
3. **Chấm thử** — upload hoặc ghi âm, trả điểm wav2vec, percentile, mức ưu tiên, P(dưới 6), điểm 3 mô hình; ngay dưới là phiếu chấm tay cho nhóm (luôn hiện).
4. **Học & vấn đáp** — 3 câu thầy đã nêu, kịch bản demo 5 phút, phần trung vị, độ nén dự đoán, recall, worst5.

API chính:

```text
GET  /api/meta, /api/results, /api/utterances, /api/status
GET  /audio/{utt_id}, /audio/worst5/{utt_id}, /audio/upload/{token}
GET  /api/score-sample/{utt_id}?transcript=...
POST /api/score        (multipart: file, transcript)
```

Giới hạn: file ≤ 25 MB, audio ≤ 30 giây; ffmpeg chuyển về WAV 16 kHz mono; file upload không có điểm thật, chỉ câu mẫu lấy từ test mới có 5 điểm giám khảo. Upload giữ tối đa 60 file hoặc 24 giờ. Model demo được export ngày 31/10/2026; số trong báo cáo vẫn là lần chạy 27/10. Không trộn hai nguồn khi trả lời.

## 7. Phiếu chấm tay của nhóm

- App chỉ đo **giây/từ** (nếu có câu đọc) và các **khoảng lặng ≥ 0,25 giây**; không nhận diện từ, không biết ngắt đúng/sai về nghĩa.
- Tốc độ tham chiếu 0,578 giây/từ; nhãn "nhanh" nếu < 0,85 lần, "chậm" nếu > 1,15 lần, còn lại "vừa".
- Khoảng lặng: khung 25 ms, bước 10 ms, ngưỡng dB thích ứng, gộp khoảng cách < 0,12 giây.
- Nhóm nghe cả bài hoặc từng đoạn, tự chọn tốc độ, đánh dấu từng chỗ ngắt Đúng/Sai.
- Phiếu lưu trong **localStorage** khóa `mla_group_reviews_v1` trên trình duyệt đang chạy; xoá dữ liệu trình duyệt là mất phiếu.
- Xuất CSV tên `nhom05_phieu_cham_nhom.csv`, dấu `;`, có BOM UTF-8 để mở đúng tiếng Việt trong Excel.
- Cột CSV: Thoi gian, Nguoi doc, Nguoi cham, Toc do, Giay/tu, So khoang ngat, So cho ngat sai, Thoi diem ngat sai, Ghi chu, File, Diem AI.

## 8. Báo cáo và mốc thời gian

- Báo cáo Week 08, 09, 10 nằm trong `docs/` và `docs/report/`.
- Nhận xét Week 10 của thầy: `docs/Nhan_xet_Week10_DT_Group05.docx` — 3 việc bắt buộc, 1 việc nên làm, 1 thí nghiệm phụ.
- Báo cáo Week 11:
  - Bản nộp cuối: `C:\Users\DucAnh\Desktop\Hanu\MLA\report_week11\Group05_Week11_Report.docx` (4.432.621 byte, 7 trang, SHA256 bắt đầu `31ec0008`, kết thúc `3ebc`), kèm `Group05_Week11_Attachments.zip` (3.965.542 byte, 25 file).
  - Trong repo Mac: `docs/report/week11_work/test_blank.docx` — bản dựng 7 trang, cột nghe trống. Bản `test_notes.docx` từng có chữ giả đã bị xoá ngày 31/10.
- Việc nghe worst5 vẫn chưa xong. Bộ nghe: `listen_kit/worst5_nghe_nhanh.wav` (31,5 giây), phiếu `PHIEU_NGHE.md`, `asr_windows.json`, `listen_times.json`. Cần hai người nghe độc lập, ghi riêng, rồi điền `listening_notes.json` và dựng lại báo cáo.
- Mốc: báo cáo tuần 10 ngày 21/10; phân tích tuần 11 ngày 27/10; app demo 31/10; hôm nay 31/10.
- Chưa có báo cáo/slide tuần 12.

## 9. Bộ câu hỏi — đáp án ngắn

**1. Vì sao lấy trung vị thay vì trung bình?**
Vì một giám khảo lệch mạnh không được kéo điểm của cả câu. Có 448 câu lệch ≥ 3 điểm; ở đó trung bình và trung vị cách nhau 0,59 điểm, gấp đôi mức 0,27 toàn bộ. Ví dụ 015010033: trung bình 6,71 nhưng trung vị 8,0. Target chọn trung vị làm tròn xuống, khớp 5.000/5.000 câu.

**2. 77% nghĩa là gì? Có phải độ chính xác?**
Không. Trong 20% bài bị xếp thấp nhất, bắt được 253/330 bài thật sự dưới 6 (77%). Precision 51%, còn 77 bài dưới 6 bị bỏ sót. Ngẫu nhiên 20%; chỉ độ dài 70%; log-mel 67%. Đây là chỉ số ưu tiên nghe lại, không phải accuracy.

**3. wav2vec có thêm gì ngoài tốc độ đọc?**
Trên CV, wav2vec 80% so với chỉ-độ-dài 73%; thêm hai đặc trưng độ dài vào wav2vec gần như không đổi (80%, MAE 0,795 so với 0,797). Nửa đọc nhanh: 78% so với 50%; nửa chậm: 58% so với 54%. Vậy phần vượt trội không chỉ là tốc độ, nhưng nửa nhanh chỉ có 36 bài dưới 6 nên sai số lớn.

**4. Vì sao bài total 0 vẫn bị đoán quanh 7?**
Vì hồi quy tối thiểu hoá sai số trung bình và đặc trưng mức câu không phân biệt được bài rất kém; dự đoán an toàn là gần trung bình. Có 12 câu total ≤ 2, cả 12 đều bị đoán > 5, trung bình khoảng 6,95. Bias trên bài dưới 6 là +1,77 với wav2vec. Chưa nghe thì chưa biết nguyên nhân.

**5. Vì sao không chọn LR cân bằng lớp dù CV cao hơn?**
CV 80,4% so với 79,8% chỉ hơn 0,6–0,7 điểm, nằm trong độ lệch chuẩn 8–10 điểm giữa fold; test lại 74% so với 77%. Không đủ căn cứ đổi mô hình chính. Đây là thí nghiệm phụ.

**6. Nếu thầy chỉ nghe 10% thì sao?**
wav2vec đạt R@10% 52%, P@10% 68%; ngẫu nhiên chỉ khoảng 13% vì tỉ lệ nền bài dưới 6 là 13,2%. Nghe 20% thì recall lên 77%, precision 51%.

**7. Có chẩn đoán được lỗi phát âm cụ thể không?**
Không. Mô hình chỉ cho điểm mức câu; chưa có GOP, chưa có alignment theo từ/âm. Phiếu chấm tay chỉ đo tốc độ và khoảng lặng, không biết ngắt đúng/sai về nghĩa. Muốn chỉ lỗi từng âm cần đặc trưng gắn với âm như GOP.

**8. Dữ liệu có đại diện cho người học Việt Nam không?**
Không. 250 người nói tiếng mẹ đẻ Quan Thoại, một nửa là trẻ em, bài đọc câu ngắn, không phải hội thoại. Chưa có bằng chứng dùng tốt cho người học Việt Nam.

**9. App có chấm điểm chính thức không?**
Không. App trả mức ưu tiên nghe lại, percentile và P(dưới 6), không trả điểm chính thức. File upload không có điểm thật; chỉ câu mẫu test mới có 5 điểm giám khảo. Audio xử lý local, tối đa 25 MB / 30 giây.

**10. Bản báo cáo nào dùng cho buổi tới?**
`Group05_Week11_Report.docx` — bản 4,4 MB trên máy Windows, 7 trang, ngày 27/10. Không dùng lại báo cáo Week 10. Trong repo chỉ có bản dựng `test_blank.docx`; phải kiểm cột Nghe 1/2 trước khi nộp.

**11. Vì sao target_check có 2905 và 52?**
Đó là **số câu khớp** của hai cách tính khác, không phải điểm: trung vị làm tròn gần nhất khớp 2.905 câu, trung bình khớp 52 câu. Cách chọn là trung vị làm tròn xuống, khớp 5.000/5.000.

**12. App và báo cáo có dùng cùng một model không?**
Cùng cấu hình và đặc trưng, nhưng model demo được export ngày 31/10; số trong báo cáo lấy từ lần chạy 27/10. Không trộn số của hai nguồn. App dùng phân bố dự đoán test đã lưu để tính percentile.

## 10. Những điều không được nói

- Không nói "độ chính xác 77%" hoặc "chấm đúng 77%".
- Không nói mô hình đã fine-tune wav2vec; nó đóng băng và chỉ huấn luyện SVR/LR phía sau.
- Không nói đã dùng GOP hoặc đã chẩn đoán lỗi từng âm.
- Không bịa ghi chú nghe worst5, không đoán nguyên nhân khi chưa nghe.
- Không nói kết quả đúng cho người học Việt Nam.
- Không nói app cho điểm chính thức.
- Không nói bản báo cáo cuối đã có trong repo Mac; nó ở máy Windows.
- Không nói đã nghe xong 5 câu worst5.
- Không tự thêm số mới ngoài các file nguồn.

## 11. Việc còn lại

1. Hai người nghe 5 câu worst5 bằng `listen_kit/worst5_nghe_nhanh.wav` hoặc 5 file trong `worst5/`, ghi độc lập vào `PHIEU_NGHE.md`.
2. Điền `listening_notes.json`, dựng lại báo cáo bằng `build_report.py`, nhúng gói minh chứng, kiểm tra lại 7 trang.
3. Mở bản cuối trên Windows, kiểm cột Nghe 1/2 và tên file `Group05_Week11_Report.docx`.
4. README và `start.bat` đã có hướng dẫn Windows (đã commit ngày 31/10).
5. Dựng lại môi trường: macOS dùng `python3.12 -m venv .venv` rồi `.venv/bin/pip install -r requirements.txt`; Windows dùng `py -3.12 -m venv .venv` rồi `.venv\Scripts\python -m pip install -r requirements.txt`. Cần Python 3.12 và ffmpeg.

---

Nếu AI được hỏi điều gì không có trong file này, hãy nói rõ "chưa có dữ liệu trong context" và đề nghị người dùng dán thêm file cụ thể, thay vì suy đoán.
