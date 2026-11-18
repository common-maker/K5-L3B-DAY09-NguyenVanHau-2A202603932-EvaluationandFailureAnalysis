# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5`

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Có (tất cả ≥ sàn) | dùng (theo dõi với Rogan-Gladen: obs 0.28 → corr 0.30) |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không (κ=0.375 < 0.6, R=0.300 < 0.7) | loại (không dùng làm gate) |

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / Sửa rubric |
|---|---|---|---|---|---|
| 1 | `H-008` (`tone_ok`): "Em đã hoàn tiền cho anh rồi nha, anh check giúp em." | PASS | FAIL | Người | Xưng 'em' + 'nha' quá suồng sã; bổ sung vào rubric danh sách từ ngữ thân mật bị cấm khi CSKH. |
| 2 | `H-029` (`tone_ok`): "Dạ, vui lòng chờ. Hệ thống đang xử lý, không cần nhắn thêm." | PASS | FAIL | Người | Có 'Dạ, vui lòng' nhưng vế sau mang giọng ra lệnh; sửa rubric yêu cầu kiểm tra toàn câu thay vì dựa vào từ khóa mở đầu. |
| 3 | `H-042` (`tone_ok`): "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | Người | Câu trả lời lịch sự và đủ ý; sửa rubric nêu rõ không bắt buộc lời xin lỗi khi thông báo đã hoàn tiền thành công. |
| 4 | `H-051` (`tone_ok`): "Dạ, LogiX đã refund 90.000đ cho đơn O-202 ạ." | FAIL | PASS | Người | Thuật ngữ 'refund' được CS LogiX cho phép; cập nhật rubric liệt kê các từ chuyên ngành tiếng Anh hợp lệ. |
| 5 | `H-081` (`tone_ok`): "Dạ, đơn O-107 chưa đủ điều kiện hoàn theo chính sách hiện hành ạ." | FAIL | PASS | Judge | Nhãn người đánh nhầm (đọc nhầm ticket); cập nhật lại nhãn vàng trong tập audit trước khi calibrate lại. |
| 6 | `HL-016` (`helpful`): "Dạ, LogiX thành thật xin lỗi... đã hoàn 55.000đ cho đơn O-404..." | PASS | FAIL | Người | Sai số tiền (ledger chỉ ghi 35.000đ). Judge thiếu đối chiếu ledger và bị thiên vị câu xin lỗi dài (verbosity bias) → chuyển sang code grader (`ReplyMatchesLedger`). |
| 7 | `HL-047` (`helpful`): "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | Người | Xưng hô 'Ok bạn' không phù hợp và thiếu thông tin số tiền đã xử lý; cần siết định nghĩa helpful bắt buộc đúng xưng hô và khớp số tiền ledger. |

## Kết luận
- **Tiêu chí được dùng (`tone_ok`)**: Đạt cả 3 sàn (`κ=0.757`, `P=0.857`, `R=0.800`). Ma trận nhầm lẫn: `TP=24, FP=4, FN=6, TN=66`. Tỉ lệ lỗi quan sát `0.28` được hiệu chỉnh Rogan-Gladen thành `0.30`. Vẫn giữ làm metric theo dõi (không dùng đánh giá nghiệp vụ tiền).
- **Tiêu chí bị loại (`helpful`)**: Không đạt sàn (`κ=0.375 < 0.6`, `R=0.300 < 0.7`). Ma trận nhầm lẫn: `TP=9, FP=0, FN=21, TN=70` — judge bỏ sót tới **21/30 ca lỗi** (70% false negative, khiến tỉ lệ lỗi quan sát chỉ còn `0.09` dù tỉ lệ thực là `0.30`). Nguyên nhân gốc: judge văn bản không đọc được SQLite `refund_ledger` nên bỏ lọt toàn bộ lỗi nói sai số tiền (`HL-015`, `HL-016`, `HL-020`, `HL-028`...) khi câu trả lời được bọc trong lời xin lỗi lịch sự, dài dòng (verbosity bias). Do đó tuyệt đối **không dùng judge này làm CI gate**; các lỗi đúng tiền phải chấm bằng code grader (`RefundAmountCorrect`, `ReplyMatchesLedger`).
- **Rủi ro còn lại**: Judge chỉ được kiểm trên dữ liệu replay đã công khai (`n=100` mỗi tập); cần thu thập và gán nhãn thêm dữ liệu held-out từ production/người dùng thật để đánh giá lại định kỳ.
