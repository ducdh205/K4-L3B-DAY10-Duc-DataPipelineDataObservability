
# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đức (định danh Git: `dinhhduc`) |
| MSSV | 2A202602795 |
| Khóa/Lớp | K4-L3B |
| Tên nhóm | Duc — Data Pipeline & Data Observability |
| Vai trò chính | Tích hợp pipeline, data observability và evaluation |
| Repository | `ducdh205/K4-L3B-DAY10-Duc-DataPipelineDataObservability` |
| Ngày hoàn thành | 2026-09-26 |

> Thay “Đức” bằng họ tên đầy đủ đúng theo danh sách lớp trước khi nộp nếu cần; repository chỉ cung cấp định danh `dinhhduc`.

## 2. Vai trò và phạm vi công việc

| Module/deliverable | File/hàm phụ trách | Input | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Orchestration baseline | `src/pipelines/phase1.py`, `run_phase1_pipeline` | Raw/clean config, test set | Baseline artifacts và report | Hoàn thành |
| Corruption & repair flow | `src/pipelines/corruption_flow.py`, `repair_from_raw_snapshot` | Clean data, immutable raw snapshot | Corrupted/repaired datasets, indexes, metrics | Hoàn thành |
| Quality observability | `src/observability/quality.py` | Normalized dataframe | GX quality/freshness results | Hoàn thành |
| Evaluation integration | `data/results/*metrics.json`, reports | Index và common test set | Baseline/corruption comparison | Hoàn thành |

### Hỗ trợ ngoài phạm vi chính

| Hoạt động | Module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Đồng bộ data contract | Cleaning, embedding và quality | `text_for_embedding`, summary length và unique ID được kiểm tra nhất quán |
| Tái chạy end-to-end | Toàn bộ pipeline | Tạo lại artifacts ngày 2026-09-26 để report có số liệu thực |

## 3. Kết quả theo vai trò

| Nhiệm vụ | File/artifact | Kết quả | Cách xác minh |
| --- | --- | --- | --- |
| Chạy baseline | `data/reports/phase1_report.md` | 24 records; quality PASS; hit rate 1.0 | `./.venv/bin/python script/run_phase1.py` |
| Chạy corruption/repair | `data/reports/corruption_report.md` | Metrics giảm rồi hồi phục đúng baseline | `./.venv/bin/python script/run_corruption_flow.py` |
| Bắt contract violation | `data/quality/`, GX result | Corrupted FAIL, repaired PASS | Đối chiếu report/artifacts |

Output cụ thể tôi dùng để xác minh tích hợp là `data/reports/corruption_report.md`: nó ghi cùng một test set có `retrieval_hit_rate` `1.0000 → 0.8000 → 1.0000` và quality/freshness `PASS → FAIL → PASS`.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Một RAG pipeline chỉ có metric retrieval tốt ở dữ liệu sạch vẫn chưa đủ: cần phát hiện data contract/freshness bị phá vỡ và chứng minh repair phục hồi chất lượng agent, thay vì chỉ sửa file lỗi thủ công.

### Cách triển khai

Baseline orchestration lấy raw snapshot, làm sạch thành schema chuẩn, tạo `text_for_embedding`, embed bằng MiniLM và index vào Chroma. Evaluation đọc 10 test cases có ground-truth `paper_id`, lấy top-4 documents và tổng hợp hit rate, token F1, judge accuracy và judge score. Corruption flow tạo sáu lỗi deterministic, đánh giá lại trên cùng test set, sau đó `repair_from_raw_snapshot` đọc raw artifact bất biến, chạy cleaning và index lại vào collection riêng. Quality layer dùng Great Expectations 1.x kiểm tra row count, non-null fields, unique ID, summary length và freshness SLA.

| Thành phần | Mô tả |
| --- | --- |
| Input | Crossref raw snapshot, clean dataframe, `data/eval/test_set.json` |
| Output | Clean/corrupted/repaired data, Chroma indexes, GX results, JSON metrics và Markdown reports |
| Module phụ thuộc | Ingestion, cleaning, embeddings/index, evaluation |
| Module dùng output | Reports và submission evidence |
| Lỗi cần xử lý | Schema thiếu, duplicate ID, summary ngắn/rỗng, stale records, index không khớp dataset |

```bash
./.venv/bin/python script/run_phase1.py
./.venv/bin/python script/run_corruption_flow.py
```

Kết quả thực tế: cả hai lệnh thành công ngày 2026-09-26; artifact có baseline 24 rows và corrupted 21 rows với 8 stale records.

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Repair có thể vá trực tiếp corrupted dataframe hoặc dựng lại từ nguồn.
- **Phương án cân nhắc:** (1) sửa các field lỗi tại chỗ; (2) reload raw snapshot, cleaning và re-index.
- **Phương án chọn:** (2), rebuild từ `data/raw/crossref_records.json` và collection repaired riêng.
- **Lý do:** Cách này truy nguyên được, idempotent, đồng thời loại bỏ cả lỗi ẩn như duplicate/record bị drop thay vì đoán cách vá từng scenario.
- **Bằng chứng:** Quality/freshness chuyển `FAIL → PASS`; hit rate `0.8000 → 1.0000`, F1 `0.6909 → 1.0000`, judge score `3.6 → 5.0`.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng:** Quality checks không phản ánh đầy đủ contract khi ghép corruption flow; cần để corrupted data bị bắt lỗi một cách đáng tin cậy.
- **Tái hiện:** Chạy `./.venv/bin/python script/run_corruption_flow.py` rồi xem quality result.
- **Nguyên nhân gốc:** Expectations chưa bao phủ thống nhất các điều kiện mà pipeline tạo/dùng: row range, `text_for_embedding`, summary length, unique `paper_id` và freshness.
- **Cách xử lý:** Đồng bộ `src/observability/quality.py` với data contract: 5–5,000 rows; required non-null fields; unique ID; summary ≥30; freshness check.
- **Xác minh:** Baseline PASS, corrupted FAIL, repaired PASS; các metric evaluation biến động theo corruption rồi phục hồi.
- **Điều học được:** Observability phải kiểm tra contract thực sự quan trọng với consumer (embedding/retrieval), không chỉ kiểm tra dataframe có tồn tại.

## 7. Hiểu biết về luồng end-to-end

1. Crossref trả raw metadata; cleaning chuẩn hóa `paper_id`, title, summary, published và tạo `text_for_embedding`; MiniLM biến text thành vectors, Chroma lưu vectors cùng metadata.
2. Mỗi test case giữ ground-truth `paper_id`. Retrieval hit rate kiểm tra document đích có trong top-k; F1/judge đánh giá answer sinh từ retrieved context.
3. Quality kiểm tra tính hợp lệ/completeness/uniqueness của contract; freshness đo độ mới theo publication age và SLA. Một record có thể schema-valid nhưng stale.
4. Cùng test set loại bỏ nhiễu do thay đổi câu hỏi/ground truth, nên có thể quy thay đổi metric cho dataset/index của từng trạng thái.
5. Repair thành công khi artifact rebuilt từ raw, GX và freshness PASS, đồng thời các metric trên common test set phục hồi tới baseline.

## 8. Phân tích kết quả

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 1.0000 | 0.8000 | 1.0000 | Mất coverage làm giảm 2/10 case |
| `mean_token_f1` | 1.0000 | 0.6909 | 1.0000 | Context/text hỏng ảnh hưởng answer |
| `judge_accuracy` | 1.0000 | 0.7000 | 1.0000 | 3 case không đạt judge sau corruption |
| `mean_judge_score` | 5.0000 | 3.6000 | 5.0000 | Chất lượng answer giảm rõ |
| Quality checks | PASS | FAIL | PASS | GX bắt duplicate/summary/contract issue |
| Freshness | PASS | FAIL (8/21) | PASS (1/24) | Backdate vượt SLA |

1. Drop-latest, blank/noisy summary, truncated title, stale date và duplicate → quality/freshness FAIL → hit rate giảm `0.20`, score giảm `1.4`.
2. Rebuild từ raw snapshot → quality/freshness PASS → mọi metric quay về baseline.

Tác động rõ nhất là tổ hợp drop-latest với làm hỏng semantic fields: cùng lúc giảm coverage document và giảm tín hiệu embedding, nên F1 giảm `0.3091`. Kết quả không ngược kỳ vọng: quality signal và retrieval/answer metrics thay đổi theo hướng nhất quán.

## 9. Điều học được và hướng cải thiện

1. Data lineage từ raw snapshot là điều kiện quan trọng để repair có thể audit và lặp lại.
2. Quality contract và freshness SLA cần được kiểm tra độc lập vì chúng trả lời hai rủi ro khác nhau.
3. RAG agent có thể suy giảm mạnh do lỗi dữ liệu trước khi lỗi này biểu hiện thành lỗi code.

Nếu có thêm thời gian, tôi sẽ mở rộng nhiều query và snapshot Crossref, thêm Ragas khi môi trường sẵn sàng, rồi báo cáo confidence interval của metric thay vì chỉ một test set 10 câu.

## 10. Cam kết của thành viên

- [x] Nội dung phản ánh phạm vi tích hợp/observability/evaluation tôi thực hiện và có artifact đối chiếu.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module phụ trách.
- [x] Mọi kết luận metric đều tham chiếu artifact đã chạy.
- [x] Không ghi thành công cho phần chưa kiểm chứng.
- [x] Không chứa `.env`, API key, token hoặc secret.
- [x] Không sao chép nguyên văn báo cáo nhóm.

**Họ và tên:** Đức (cần thay bằng họ tên đầy đủ nếu biểu mẫu yêu cầu)
**Ngày xác nhận:** 2026-09-26
