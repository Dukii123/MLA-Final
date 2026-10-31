# MLA-Final

Demo và tài liệu môn MLA — Nhóm 05, 61FIT4MLA.

- `webapp/` — web UI chạy local để trình bày kết quả tuần 11. Xem [webapp/README.md](webapp/README.md).
- `docs/` — báo cáo, nhận xét và dữ liệu làm việc các tuần.
- [HUONG_DAN_AI.md](HUONG_DAN_AI.md) — context pack để dán sang chat khác: bản đồ file, số liệu gốc, cách đọc dữ liệu và bộ câu hỏi vấn đáp.

## Chạy demo

macOS: mở Terminal trong `webapp` rồi chạy `./start.sh`, hoặc bấm đúp `start.command`.

Windows: bấm đúp `webapp\start.bat`, hoặc mở PowerShell trong `webapp`:

```powershell
.venv\Scripts\python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Mở `http://127.0.0.1:8000`, dừng bằng `Ctrl+C`. Lần đầu cài môi trường, xem [webapp/README.md](webapp/README.md).
