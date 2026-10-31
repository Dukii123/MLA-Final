# Phiếu nghe 5 câu sai nặng nhất — Tuần 11

Mở `worst5_nghe_nhanh.wav` (31,5 giây, đã tăng âm lượng đều, có 2 giây im lặng giữa các câu)
hoặc từng file trong thư mục này. File gốc không bị sửa; bản tăng âm chỉ để nghe rõ hơn.

Thời gian trong file gộp:

| # | Thời gian | Mã câu | Câu đọc | Total | Log-mel | w2v | Giây |
|---|---|---|---|---|---|---|---|
| 1 | 0,75–4,55 | 014040089 | HERE IS TIM'S CAP | 0 | 7,2 | 7,2 | 3,8 |
| 2 | 6,55–10,43 | 069020059 | THEY DID NOT SEE THEM ANY MORE | 0 | 7,1 | 7,3 | 3,9 |
| 3 | 12,43–16,47 | 014040122 | HEY WATCH OUT FOR MY CUCUMBER | 0 | 7,1 | 7,1 | 4,0 |
| 4 | 18,47–23,71 | 014040090 | HERE IS MARY'S SHOES | 0 | 7,0 | 7,3 | 5,2 |
| 5 | 25,71–29,51 | 069020075 | SHE MUST BE MADE TO STAY | 0 | 6,7 | 7,5 | 3,8 |

## Cách ghi

Mỗi câu cần **hai người nghe độc lập**, không trao đổi trước khi ghi. Chỉ ghi điều thật sự nghe được:
có đọc hết câu không, từ nào rõ / từ nào sai hoặc mất, có im lặng dài hay tiếng ồn, giọng to/nhỏ.
Không suy đoán theo câu mẫu. Nếu không nghe ra từ nào, ghi đúng như vậy.

| # | Mã câu | Nghe 1 ghi | Nghe 2 ghi |
|---|---|---|---|
| 1 | 014040089 | | |
| 2 | 069020059 | | |
| 3 | 014040122 | | |
| 4 | 014040090 | | |
| 5 | 069020075 | | |

## Chấm của giám khảo corpus (để đối chiếu, không phải nhóm nghe)

Năm giám khảo của speechocean762 đã chấm từng từ. Cả 5 câu đều có **completeness 0–1**
(tức bị coi là không hoàn thành câu) và gần như mọi từ chỉ 1,0–3,4 điểm. Riêng 014040122
có hai giám khảo cho HEY / OUT / MY / CUCUMBER 9–10 điểm nhưng WATCH / FOR vẫn 1–2 điểm.
Khi nghe, đối chiếu xem bé bỏ từ, nuốt âm hay đọc quá nhỏ; đây là chỗ giám khảo corpus
và tai người có thể khác nhau.

## Số đo tự động trên file gốc (không phải nội dung nghe)

| Mã câu | Biên độ đỉnh | RMS (dBFS) | % khung 25 ms có năng lượng | Hệ số tăng âm |
|---|---|---|---|---|
| 014040089 | 0,14 | −42,7 | 14% | ×6,6 |
| 069020059 | 0,58 | −35,6 | 8% | ×1,6 |
| 014040122 | 0,19 | −40,5 | 20% | ×4,7 |
| 014040090 | 0,31 | −39,1 | 10% | ×2,9 |
| 069020075 | 0,60 | −37,3 | 5% | ×1,5 |

Cả 5 file đều rất nhỏ và phần lớn thời lượng gần như im lặng; đây là lý do nên nghe bản tăng âm.
Bộ nhận dạng tiếng Anh có sẵn của Windows không chép được câu nào rõ ràng (tin cậy 0–30%),
nên bảng này **không** thay cho việc nghe của nhóm.

## Sau khi nghe

Gửi lại 5 dòng ghi chú (hoặc điền trực tiếp vào bảng trên); báo cáo sẽ được điền vào hai cột
“Nghe 1” / “Nghe 2”, dựng lại Word, nhúng lại gói minh chứng và render kiểm tra.
