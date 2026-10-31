# Đại trà Nhóm 5 · Nhận xét Tuần 9 (bản chính thức, chi tiết)

> Người dùng dán bản này vào chat ngày 21/10/2026. Bản ngắn hơn nằm trong `Nhan_xet_Week9_DT_Group05.docx`.

Speechocean762: dự đoán điểm phát âm để giáo viên ưu tiên nghe lại

## Nhận xét chung
Nhóm đã làm đúng hướng thầy đề nghị ở Tuần 8: một bài toán, chia theo người nói, baseline hằng số, hai mô hình, ảnh chụp lần chạy thật và thời gian chạy; sửa lại liên hệ sai với LingWav2Vec2; tính ICC cho năm giám khảo. SVR giảm MAE test từ 1,123 xuống 0,835, PCC 0,592. Nhưng chính nhóm đã chỉ ra điểm yếu quyết định: với 324 câu test điểm dưới 6, SVR đoán cao hơn thật trung bình 2,1 điểm. Công cụ được thiết kế để tìm bài cần nghe lại, mà lại kém đúng ở những bài đó. Hai tuần tới phải tập trung vào chỗ này.

## Dữ liệu đang nói gì
Dự đoán dồn vào khoảng 4,3–9,3, tức mô hình kéo mọi bài về gần giữa thang. Đây là biểu hiện quen thuộc khi đặc trưng yếu: đoán gần trung bình là cách an toàn nhất để giảm MAE. Đặc trưng log-mel lấy trung bình theo thời gian mô tả âm sắc giọng và điều kiện thu âm nhiều hơn là việc phát âm đúng hay sai từng âm. Độ dài câu cũng nằm trong vector, và người đọc chậm, ngập ngừng thường bị chấm thấp, nên một phần điểm có thể đến từ tốc độ đọc. Có một chi tiết đáng chú ý trong chính ví dụ của các em: năm điểm 7,6; 7,9; 8,0; 9,0; 9,1 có trung vị là 8,0, đúng bằng total trong scores.json.

## Những chỗ phải sửa trước buổi thuyết trình
1. **[Bắt buộc] Kiểm tra giả thuyết target là trung vị.** Ở đâu: Mục 4, ví dụ 000010011. Vấn đề: Target của nhóm là trung bình năm điểm, khác total trong scores.json ở 4.948/5.000 câu. Ví dụ của nhóm gợi ý total có thể là trung vị. Cần làm: Tính trung vị năm điểm cho cả 5.000 câu, đếm bao nhiêu câu khớp scores.json (cho phép sai lệch do làm tròn). Nếu khớp gần hết, chuyển target sang total trong scores.json để so được với các nghiên cứu khác; giữ bản trung bình như phân tích phụ. Pipeline chỉ chạy 13 giây nên chạy lại không tốn công. Xong khi: Một câu "trung vị khớp … /5.000 câu" và quyết định target ghi rõ trong mục 4.
2. **[Bắt buộc] Đổi chỉ số chính sang đúng việc của giáo viên.** Ở đâu: Mục 5, bảng kết quả. Vấn đề: MAE trung bình trông ổn, nhưng không cho biết giáo viên có tìm được bài cần nghe lại không. Cần làm: Xếp câu test theo điểm dự đoán tăng dần. Trong 10% và 20% thấp nhất, đếm số câu có điểm thật dưới 6, tính recall (trên 324 câu) và precision. Báo cho SVR, RF và thứ tự ngẫu nhiên (kỳ vọng bằng tỷ lệ nền 324/2.500, khoảng 13%). MAE và PCC giữ làm chỉ số phụ. Xong khi: Bảng 3 dòng × 2 ngân sách, kèm tỷ lệ nền.
3. **[Bắt buộc] Chọn tham số bằng CV theo người nói.** Ở đâu: Mục 4–5, tập validation 25 người. Vấn đề: PCC validation 0,87 nhưng test chỉ 0,59; MAE 0,726 so với 0,835. Với 25 người nói, vài người dễ đoán đủ làm số đẹp lên. Cần làm: Chọn C của SVR và min_samples_leaf của RF bằng GroupKFold 5 phần theo người nói trên 125 người train chính thức, báo trung bình ± độ lệch chuẩn giữa các fold. Test vẫn chỉ chạy một lần sau khi chọn. Xong khi: Bảng chọn tham số có cột MAE CV (TB ± SD).
4. **[Bắt buộc] Tách phần đóng góp của độ dài câu.** Ở đâu: Mục 5, đặc trưng 81 chiều. Vấn đề: Chưa biết mô hình dựa vào phát âm hay vào tốc độ đọc. Cần làm: Chạy SVR với hai cấu hình: (a) chỉ độ dài và độ dài chia số từ của câu đọc (câu đọc là đề bài giáo viên giao, nên biết trước); (b) log-mel bỏ độ dài. So với cấu hình đầy đủ. Xong khi: Hai dòng mới trong bảng kết quả và một câu diễn giải phần nào của điểm đến từ tốc độ.
5. **[Nên làm] Đặt hạn cho GOP.** Ở đâu: Mục 6. Vấn đề: Link GOP của tác giả đang bị khóa; chờ mãi sẽ mất thời gian của cả nhóm. Cần làm: Nếu đến cuối Tuần 10 vẫn chưa tải được, bỏ GOP khỏi kế hoạch trước thuyết trình và chuyển sang embedding huấn luyện sẵn ở phần dưới. Xong khi: Báo cáo ghi rõ ngày quyết định và lựa chọn.
6. **[Nên làm] Sửa định dạng báo cáo.** Ở đâu: Tiêu đề mục 1 và 2. Vấn đề: Còn ký hiệu định dạng lỗi ("\# \*\*") trong tiêu đề. Cần làm: Sửa trước khi nộp bản cuối. Xong khi: Tiêu đề hiển thị sạch.

## Hướng đi khả thi trong hai tuần
Câu hỏi đáng làm: vì sao mô hình không nhận ra bài đọc kém, và cái gì sửa được điều đó, đặc trưng hay cách học? Kết quả cho biết vấn đề nằm ở đâu, và câu trả lời đó có ích cho mọi công cụ chấm phát âm.
- Bước 1. Hướng đặc trưng: embedding trung bình theo câu từ một mô hình tiếng nói huấn luyện sẵn như wav2vec 2.0 base, đưa vào SVR với cùng split. Chạy thử 50 câu trên máy để đo thời gian thật trước khi chạy cả 5.000 câu.
- Bước 2. Hướng cách học: giữ log-mel, đặt trọng số mẫu lớn hơn cho câu điểm thấp, hoặc huấn luyện thẳng bài phân loại "dưới 6 hay không" (LR, RF có cân bằng lớp).
- Bước 3. So hai hướng bằng chỉ số ngân sách ở mục sửa 2.
- Bước 4. Nghe lại 5 câu điểm thật thấp nhất mà mô hình đoán cao nhất; ghi tai các em nghe thấy gì.

Nếu kết quả không như mong đợi: Nếu cả hai hướng đều không kéo được recall lên rõ, kết luận vẫn có giá trị: đặc trưng mức câu không đủ để nhận ra bài đọc kém, cần đặc trưng gắn với từng âm như GOP. Trình bày con số và lý do.

## Kế hoạch hai tuần
- Tuần 10: Bốn mục bắt buộc (đều nhanh vì pipeline chạy 13 giây). Nghe 5 câu bị đoán sai nặng nhất.
- Tuần 11 (trước buổi thuyết trình): Một trong hai hướng: embedding hoặc trọng số/phân loại. Làm slide và tập trình bày. *(Người dùng cho biết: không làm slide, mở report cho thầy vấn đáp.)*

## Chuẩn bị cho buổi gặp thầy
Các em phải tự giải thích được, bằng lời của mình:
- Vì sao một mô hình hồi quy có đặc trưng yếu lại kéo dự đoán về gần trung bình?
- Nếu giáo viên chỉ nghe lại được 10% số bài, con số nào trong báo cáo cho họ biết công cụ có đáng dùng không?
- Khi một giám khảo chấm lệch hẳn bốn người còn lại, trung bình và trung vị phản ứng khác nhau thế nào?

Mang theo: Kết quả kiểm tra trung vị. Bảng ngân sách nghe lại. Ghi chú 5 câu đã nghe. Đề xuất hướng đi: Đề xuất chọn hướng đặc trưng hay hướng cách học làm thí nghiệm chính, kèm thời gian chạy thử 50 câu.

## Mạch thuyết trình gợi ý
1. Giáo viên có 35 bài đọc thành tiếng: nghe bài nào trước?
2. Dữ liệu speechocean762, năm giám khảo, ICC, cách tạo target.
3. Chia theo người nói; baseline hằng số.
4. Kết quả MAE và PCC, và vì sao chưa đủ.
5. Chỉ số theo ngân sách nghe lại; hiện tượng dồn về giữa thang.
6. Thí nghiệm sửa: đặc trưng hoặc cách học.
7. Giới hạn: người nói tiếng mẹ đẻ Quan Thoại, bài đọc thành tiếng, chưa chẩn đoán từng âm.

Các em đã có pipeline chạy thật và tự tìm ra điểm yếu quan trọng nhất. Hai tuần tới hãy dành trọn cho đúng những bài giáo viên cần nghe lại.

Thầy Khánh
