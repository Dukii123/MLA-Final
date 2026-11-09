# Báo cáo tuần 11 mới theo feedback phỏng vấn — Kế hoạch thực thi

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans (thực thi tại chỗ). Các bước dùng checkbox (`- [ ]`).

**Goal:** Dựng lại báo cáo tuần 11 từ đầu trên máy Windows, cấu trúc bám 3 điểm feedback sau phỏng vấn ngày 4/11 (nhãn/bản ghi, đặc trưng & phép so sánh, tự nghe lỗi nặng nhất) và làm nổi phần **completeness**; mọi số lấy từ lần chạy mới có ảnh Terminal.

**Architecture:** Tái dùng pipeline khôi phục từ git (week11_analysis.py, build_report.py, package.py, embed…). Thêm script phân tích mới `week11_completeness.py` (score corpus từ parquet + số đo âm học từ WAV). build_report.py được viết lại theo cấu trúc 3 điểm feedback. Không đụng webapp và định nghĩa mô hình.

**Tech stack:** Python 3.14.5 hệ thống (numpy 2.5.2, sklearn 1.9.1, matplotlib 3.11.2, pyarrow 26.0.0, python-docx, PIL) · node v24 (cfb.js) · LibreOffice (render kiểm) · PowerShell (chạy thật + PrintWindow capture).

**Spec:** `docs/Interview's Feedback.txt` (3 điểm, 4/11/2026) + yêu cầu người dùng: chú trọng completeness; KHÔNG bịa ghi chú nghe.

## Global Constraints (từ AGENTS.md — bắt buộc với mọi task)

- Nộp **một file Word .docx duy nhất**; minh chứng (ZIP: code, JSON/log, dự đoán, hình, ảnh Terminal, audio worst5) nhúng OLE trong Word.
- Times New Roman, giãn 1,5, toàn bộ chữ đen; tiếng Việt ngắn gọn; có biểu đồ + **ảnh chụp Terminal thật** của lần chạy; không dựng ảnh giả, không sửa số.
- Mọi số trong report phải lấy từ `week11_results.json` / `week11_completeness.json` / `figure_stats.json` của **lần chạy có trong ảnh Terminal**.
- Không bịa ghi chú nghe: `listening_notes.json` phải là bản trống, báo cáo ghi rõ "chưa thực hiện"; chỉ điền khi nhóm nghe thật.
- worst5 phải trùng 5 ID định nghĩa cũ (`verify_week11.py` assert: 014040089, 069020059, 014040122, 014040090, 069020075).
- Số yaptı dạng Việt (dấu phẩy thập phân — hàm `vn()` có sẵn).

## Review Focus

1. **Chữ giả nghe** — `listening_notes.json` hiện chứa "Ghi chu thu mot hai ba…".expect: build dạo đầu ghi đè bản trống; `verify_docx.py` phải khẳng định cột Nghe trống và có dòng "Trạng thái phần nghe.".
2. **Thang completeness lệch tài liệu** — README corpus ghi 0–1 nhưng dữ liệu có tới 10.0. expect: script đo min/max thực, báo cáo mô tả theo số đo được, không chép dumber máy móc.
3. **worst5 lệch định nghĩa** — `over = pred_logmel − target`, 5 ID cố định. expect: assert trùng từng ID với `week11_results.json['worst5']`.
4. **Tràn trang khi bảng thêm cột** — bảng worst5 thêm cột completeness (8 cột). expectation: render LibreOffice từng trang, không cắt bảng/ảnh, không trang trắng.
5. **Số trong docx lệch JSON** — expectation: abrir anchor mới trong verify_docx: 4 câu compl 0,0 + 014040122 compl 1,7 + dòng "n câu completeness 0" khớp JSON.

---

### Task 1: Vô hiệu hoá chữ giả + script completeness mới

**Files:**
- Modify: `docs/report/week11_work/listening_notes.json` (ghi đè bằng nội dung `listening_notes.blank.json`)
- Create: `docs/report/week11_work/week11_completeness.py`

**Interfaces:**
- Consumes: parquet `test-00000-of-00001.parquet` (arg[1], mặc định `C:\Users\DucAnh\AppData\Local\Temp\opencode\sp762`); `week11_results.json`; `test_predictions_week11.csv`; `worst5/*.WAV`.
- Produces: `week11_completeness.json` (khoá: `python`, `scale`, `compl_zero`, `low_total2`, `worst5`, `acoustic5`) + `week11_completeness.log`; stdout là log đó. build_report Task 2 đọc các khoá này; package Task 5 đóng gói cả hai file.

- [ ] **1.1** Ghi đè `listening_notes.json` = nội dung bản blank (5 ID × 2 cột rỗng).
- [ ] **1.2** Đọc `make_loud_kit.py`, copy đúng thuật toán đo (khung 25 ms/bước 10 ms, ngưỡng dB thích ứng) cho `acoustic5`.
- [ ] **1.3** Viết `week11_completeness.py`:
  - test split duy nhất; uid từ stem của path audio; assert 2.500 dòng.
  - `scale`: min/max thực của accuracy/completeness/fluency/prosodic trên test.
  - `compl_zero`: n câu completeness == 0; mean total; mean pred SVR log-mel & SVR wav2vec (từ CSV); n dưới 6 của nhóm này.
  - `low_total2`: đúng 12 câu total ≤ 2 (assert `n == results['low_total']['n']`), mỗi câu: id, text, five, total, acc/compl/flu/pros, %từ dưới 5, sec_per_word, pred_logmel, pred_w2v.
  - `worst5`: cùng các trường; assert 5 ID trùng `results['worst5']` theo thứ tự.
  - `acoustic5`: mỗi WAV worst5 — peak, RMS dBFS, % khung có năng lượng (đúng thuật toán make_loud_kit).
- [ ] **1.4** Chạy: `python week11_completeness.py` → exit 0, mọi assert PASS, sinh JSON + log.
- [ ] **1.5** Commit: `week11 completeness analysis + neutral listening notes`.

### Task 2: Viết lại build_report.py theo 3 điểm feedback (completeness là mục trọng tâm)

**Files:**
- Modify: `docs/report/week11_work/build_report.py` (giữ nguyên helpers/dấu thời gian/OLE zone; viết lại phần thân mục + tiêu đề phụ; bỏ Mục 1 và Mục 8 cũ).

**Cấu trúc mới (đã chốt với người dùng):**
- Header/subtitle: "Nhãn, đặc trưng và lỗi nặng nhất — bám 3 điểm feedback sau phỏng vấn".
- Khung "Kết quả chính": 4 bullet mới (completeness là mũi nhọn: 4/5 câu worst4 compl 0…).
- **Mục 1** "Ba điểm feedback sau phỏng vấn và vị trí đáp trong báo cáo": bảng ánh xạ feedback → mục.
- **Mục 2** (FB1) "Một bản ghi là gì và năm điểm giám khảo ra total thế nào": định nghĩa bản ghi; bảng target_check; **kiểm chứng trên một bản ghi cụ thể** (raters.example: five/mean/median/total); độ bền trung vị (448 câu lệch ≥3, 0,59 vs 0,27); người nói tách rời 125/125.
- **Mục 3** (FB2) "Ba thứ đặc trưng và cùng một phép so sánh": định nghĩa độ dài 2 / log-mel / wav2vec (mô tả chính xác — đọc week09 trước khi viết); protocol GroupKFold-5 theo người nói; **định nghĩa recall@20% minh bạch: 253/330 từ danh sách 500 bài được chọn** + precision đối ứng.
- **Mục 4** Bảng CV + test đầy đủ (giữ bảng cũ) + Hình 1.
- **Mục 5** Nửa đọc nhanh/chậm + Hình 2, 3 (rút gọn).
- **Mục 6** (trọng tâm) "Thang điểm corpus và completeness ở nhóm lỗi nặng nhất":
  (a) bảng 12 câu total ≤ 2 — cột corpus acc/compl/flu/pros + pred log-mel/w2v;
  (b) bảng worst5 + cột completeness; nhận xét 4/5 = 0,0 và 014040122 = 1,7;
  (c) bảng số đo tự động âm học (peak/RMS/%khung) — nhãn rõ "số đo tự động, không phải nghe";
  (d) nhóm compl = 0: n, mean total, mean pred → giải thích mô hình đoán ~7;
  (e) bảng Nghe 1/2 trống + "Trạng thái phần nghe." (chờ nhóm nghe thật).
- **Mục 7** Thí nghiệm phụ LR (giữ, gọn).
- **Mục 8** Chuẩn bị vấn đáp: 3 câu cũ + 1 câu mới về completeness.
- **Mục 9** Thời gian chạy + môi trường (nhắc thêm script completeness).
- Phụ lục: ảnh Terminal + `[[OBJECTS]]` + 2 link.

- [ ] **2.1** Đọc week09 README/scripts để mô tả đúng 81 đặc trưng log-mel.
- [ ] **2.2** Sửa `build_report.py` theo cấu trúc trên, đọc thêm `week11_completeness.json`.
- [ ] **2.3** Chạy `python build_report.py` → `report_before_embed.docx`.
- [ ] **2.4** Chạy `python verify_docx.py` (bản mở rộng Task 3) → `verify_docx OK`.
- [ ] **2.5** Commit: `rebuild week11 report around interview feedback + completeness`.

### Task 3: Mở rộng verify_docx.py (anchor số mới)

**Files:** Modify `docs/report/week11_work/verify_docx.py`.

- [ ] **3.1** Thêm asserts: tồn tại cột "Compl." trong bảng worst5 và **mỗi ô khớp** `week11_completeness.json['worst5'][i]['completeness']`; tồn tại chữ "Trạng thái phần nghe."; bảng Nghe 1/2 toàn ô rỗng; tổng text **không chứa** "Ghi chu thu" (chống chữ giả quay lại); còn '[['OBJECTS']]', 'Group05_Week11_Report', tiêu đề Tuần 11 (giữ cũ).
- [ ] **3.2** Chạy PASS trên `report_before_embed.docx` và trên bản final sau Task 5.
- [ ] **3.3** Commit (gộp với commit Task 2).

### Task 4: Chạy thật lần chính thức + chụp ảnh Terminal

**Files:**
- Modify: `docs/report/week11_work/run_week11.ps1` (thêm bước `week11_completeness.py` giữa analysis và figures).
- Create (bởi capture): `terminal_week11_run_win.png` (ghi đè).

**Interfaces:** chạy qua `official_capture.ps1` (cửa sổ PowerShell thật → done-file → PrintWindow → đóng).

- [ ] **4.1** Sửa `run_week11.ps1`: thứ tự analysis → completeness → figures (một ảnh chụp là minh chứng cho cả ba).
- [ ] **4.2** Chạy `official_capture.ps1` đên done (analysis ~3,5 phút + completeness ~15 giây + figures).
- [ ] **4.3** Kiểm chứng: `verify_week11.py` PASS; ảnh PNG mới (mtime, kích thước); JSON/log mới có mtime đúng buổi này.
- [ ] **4.4** Commit: `official week11 run + completeness evidence`.

### Task 5: Đóng gói minh chứng + nhúng OLE + render kiểm + bàn giao

**Files:**
- Modify: `docs/report/week11_work/package.py` (thêm 3 file completeness vào ZIP; README.txt bổ sung mô tả + pyarrow trong CÁCH CHẠY LẠI).
- Create: `docs/report/Group05_Week11_Report.docx` (bản final); `C:\Users\DucAnh\Desktop\Hanu\MLA\report_week11\Group05_Week11_Report.docx` (bàn giao).

- [ ] **5.1** Sửa package.py (thêm `week11_completeness.py/.json/.log`); chạy → `Group05_Week11_Attachments.zip`.
- [ ] **5.2** `node embed_packages.cjs` → `evidence.bin`; `python build_report.py "C:\...\report_week11\báo cáo tạm"`? — KHÔNG: đúng thứ tự AGENS: `python build_report.py` → copy sang `report_before_embed.docx` → package → node embed → `python embed_report.py "C:\Users\DucAnh\Desktop\Hanu\MLA\report_week11\Group05_Week11_Report.docx"` (mkdir trước).
- [ ] **5.3** `python verify_docx.py <final>` PASS; assert OLE tồn tại (`word/embeddings/oleObject1.bin`).
- [ ] **5.4** Render: `soffice.com --headless --convert-to pdf` → đọc PDF từng trang (read tool) — không tràn bảng/ảnh, không trang trắng, chữ đen, nhãn Tuần 11.
- [ ] **5.5** Cập nhật `HUONG_DAN_AI.md` (trạng thái 9/11: bản mới, số nguồn mới, việc nghe còn thiếu) + tiến trình trong `progress.md` mới (hoặc mục "Nhật ký 9/11" trong plan này).
- [ ] **5.6** Commit cuối: `package week11 v2 evidence + handoff`.

## Nhật ký 9/11

- 10:57 khôi phục week11_work từ git; kiểm tra env (node 24, pyarrow 26, LibreOffice có); viết plan.
