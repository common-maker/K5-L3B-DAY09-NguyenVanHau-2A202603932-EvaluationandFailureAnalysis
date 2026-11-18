# Trace case: từ trace tới quyết định sai đầu tiên

Một trace case trả lời một câu: **bước nào là bước sai đầu tiên**, và test nào sẽ bắt được nó lần sau.

```bash
cd src
python -m lab9.trace_case --shape seeded_regression --claim C-002 --seed 11
python -m lab9.trace_case --shape fixed --claim C-002 --seed 11   # đối chứng
```

Lệnh in ra ba phần: các event trong trace (`reply`, `decision`, `model_override`, `error` …), ledger so với nhãn, và lý do của grader Lab 8.

## Mẫu điền (mỗi bạn 1 case, lấy từ trial đang fail trong report)

| Trường | Nội dung |
|---|---|
| Trial | `seeded_regression C-002@11`, run ID `E-seeded_regression-20261118-4aa6` (`reports/eval_seeded_regression.json`) |
| Triệu chứng | `lab8 grader` (`trial_pass`) FAIL (`status resolved != denied`), `refund_amount_correct` FAIL (`ledger=20000 != label=0`), `db_fact_kept` FAIL (`1 override event(s)`); reply gửi khách báo `"Dạ, LogiX đã hoàn 20.000đ cho đơn O-202."` trong khi nhãn đúng yêu cầu `denied` (`0đ`). |
| Bước sai đầu tiên | Event `3` (`model_override`): `{"delay_days": 5}` — agent ghi đè giá trị `delay_days=5` trích từ ticket lên dữ kiện `delay_days=2` của DB. |
| Vì sao là bước *đầu tiên* | Event `1` (`handoff`) giao đúng phạm vi `owner_order_only` và `allowed_tools`; Event `2` (`investigator`) truy vấn DB ra chính xác đơn `O-202` có `delay_days=2`, `shipping_fee_vnd=20000`. Mọi dữ kiện trước bước `3` đều chính xác; bước `3` làm sai đầu vào cho bước `4` (`quote`) khiến hệ thống tính nhầm mức bồi thường 20.000đ. |
| Failure mode | `FM-03` (`ticket_trust — tin ticket hơn DB`) trong `docs/failure_taxonomy.md` |
| Đối chứng | Trên `fixed C-002@11`: sau Event `2` (`investigator`), KHÔNG có Event `model_override`; Event `3` là `quote` (`amount_vnd=0, reason="no_entitlement"`), ledger ghi `refund_vnd=0`, reply từ chối đúng chính sách (`PASS`). |
| Regression test | `src/tests/test_lab9_trace_case.py::test_c002_seed11_trace_case_catches_regression_and_passes_fixed` (dùng `DbFactKept` + `RefundAmountCorrect` + `lab8_pass`): đã xác nhận fail trên `seeded_regression` và pass trên `fixed`. |
| Chưa chắc chắn | Trace chạy trên MockLLM nên chỉ tái hiện lỗi theo công tắc `ticket_trust`; chưa chứng minh được trên LLM thật cơ chế nào (prompt injection hay lỗi parse số ngày) gây ra `model_override`. |

## Quy tắc

- Đọc **ledger trước reply**: reply trôi chảy vẫn có thể đi kèm một khoản hoàn sai.
- "Bước sai đầu tiên" phải dẫn số event cụ thể, không phải "agent bị nhầm".
- Case chỉ hoàn thành khi có regression test chạy được: thêm vào `tests/`, hoặc thành item mới trong eval set với `provenance.from_trace`.
