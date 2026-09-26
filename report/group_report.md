# Group Report — Day 10: Data Pipeline & Data Observability

> Dùng mẫu này cho báo cáo chung của nhóm 3–5 thành viên. Thay toàn bộ nội dung trong dấu `[ ]` bằng thông tin và kết quả thực tế. Xóa các dòng hướng dẫn không còn cần thiết trước khi nộp.

## 1. Thông tin bài nộp

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Khóa/Lớp         | [K4-L3B]              |
| Tên nhóm         | [Duc]     |
| Repository         | [https://github.com/ducdh205/K4-L3B-DAY10-Duc-DataPipelineDataObservability] |
| Ngày hoàn thành | [2026-09-26]               |

### Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò chính | Module/deliverable sở hữu |
| --: | --- | --- | --- | --- |
| 1 | [Hoàng Đức Minh] | [2A202602362] | [Data ingestion & cleaning owner] | [`src/ingestion/crossref.py`, `src/ingestion/cleaning.py`; raw/clean artifacts] |
| 2 | [Nguyễn Văn Tứ] | [2A202602586] | [Evaluation & observability owner] | [`src/evaluation/testset.py`, `src/evaluation/metrics.py`, `src/observability/quality.py`, `src/observability/reporting.py`] |
| 3 | [Đinh Hoàng Đức] | [2A202602795] | [Corruption & integration owner] | [`src/ingestion/corruption.py`, `src/pipelines/phase1.py`, `src/pipelines/corruption_flow.py`] |


## 2. Tóm tắt kết quả

Viết từ 150–250 từ, trả lời ngắn gọn:

- Nhóm đã hoàn thành những phần nào?
- Baseline pipeline đã tạo ra các artifact nào?
- Corruption nào ảnh hưởng rõ nhất đến data quality hoặc agent?
- Repair đã phục hồi được chỉ số nào?
- Blocker hoặc giới hạn quan trọng nhất còn lại là gì?

**Tóm tắt của nhóm:**

[Artifacts hiện có thể hiện pipeline Crossref-to-RAG với 24 clean records, evaluation set 10 câu, MiniLM/ChromaDB, quality/freshness reports và metrics cho ba trạng thái. Baseline đạt retrieval hit rate, mean token F1 và judge accuracy lần lượt 1.0000; corrupted giảm còn 0.8000, 0.6909 và 0.7000; repaired trở lại các giá trị baseline. Freshness chuyển từ PASS (1/24 stale, 4.2%) sang FAIL (8/21, 38.1%) rồi PASS sau repair; corruption log ghi đủ sáu kịch bản. Judge thực tế dùng heuristic fallback vì LLM evaluator không khả dụng, còn Ragas bị bỏ qua. Đã xác minh cleaning tạo lại đúng 24 ID và embedding text so với artifact đã lưu, nhưng chưa chạy lại toàn bộ hai pipeline trong lần hoàn thiện báo cáo này. Giới hạn cần xử lý là row-count expectation 5–5,000 không phát hiện trực tiếp việc mất năm record mới nhất; cần bổ sung retention/count contract và xác nhận MSSV của hai thành viên còn lại.]

## 3. Kiến trúc và luồng dữ liệu

### Luồng end-to-end

Điều chỉnh sơ đồ dưới đây nếu cách triển khai thực tế của nhóm khác starter:

```text
Crossref API
    -> raw response/raw records
    -> cleaning và data modeling
    -> embedding + ChromaDB index
    -> evaluation baseline
    -> quality/freshness reports
    -> corruption
    -> re-index và re-evaluate
    -> repair từ dữ liệu nguồn
    -> comparison report
```

### Trách nhiệm của từng khối

| Khối             | Input          | Xử lý chính             | Output/artifact          | Owner          |
| ----------------- | -------------- | -------------------------- | ------------------------ | -------------- |
| Ingestion         | [Crossref payload hoặc local response snapshot] | [Fetch, retry, parse DOI/title/authors/dates, fallback snapshot]   | [`data/raw/crossref_response.json`, `data/raw/crossref_records.json`] | [Hoàng Đức Minh] |
| Cleaning          | [`PaperRecord` từ raw records]        | [Normalize text, loại record thiếu trường bắt buộc, deduplicate `paper_id`, tính `age_days`]     | [`data/clean/papers_clean.csv`, `data/clean/papers_clean.json`] | [Hoàng Đức Minh] |
| Embedding/index   | [Clean dataframe]        | [MiniLM embeddings, persistent ChromaDB, collection riêng theo trạng thái]       | [`data/embeddings/`, `data/chroma/`] | [Đinh Hoàng Đức (tích hợp)] |
| Evaluation        | [Index và test set dùng chung]        | [10 câu hỏi; retrieval hit rate, token F1, judge]     | [`data/eval/test_set.json`, `data/results/*_metrics.json`] | [Nguyễn Văn Tứ] |
| Observability     | [Clean/corrupted/repaired dataframe]        | [Great Expectations 1.x và freshness SLA 180 ngày/25%] | [`data/quality/*_quality_report.json`] | [Nguyễn Văn Tứ] |
| Corruption/repair | [Baseline clean data và raw records]        | [Sáu corruption xác định; rebuild repair từ raw snapshot]    | [`data/results/corruption_log.json`, corrupted/repaired artifacts] | [Đinh Hoàng Đức] |
| Orchestration     | [Raw records, clean data, evaluation set]        | [Baseline → corruption → re-index/evaluate → repair → compare]           | [`data/reports/phase1_report.md`, `data/reports/corruption_report.md`]        | [Đinh Hoàng Đức] |

## 4. Cách tái hiện kết quả

### Cấu hình không chứa secret

| Biến/cấu hình             | Giá trị sử dụng |
| ---------------------------- | ------------------- |
| `LLM_PROVIDER`             | [gemini; artifact cho thấy judge dùng heuristic fallback]         |
| `LLM_MODEL`                | [gemini-2.5-flash]         |
| Embedding model              | [sentence-transformers/all-MiniLM-L6-v2]         |
| Số lượng Crossref records | [24]         |
| Retrieval`top_k`           | [4]                   |
| Freshness threshold          | [180 ngày; stale ratio tối đa 25%]         |
| Random seed, nếu có        | [Không cấu hình/không áp dụng]         |

Không dán nội dung API key hoặc file `.env` vào báo cáo.

### Lệnh cài đặt

Chỉ giữ lại cách nhóm đã dùng.

```bash
uv sync
```

Hoặc:

```bash
python -m pip install -e .
```

### Lệnh chạy

Baseline:

```bash
uv run python script/run_phase1.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_phase1.py
```

Corruption flow:

```bash
uv run python script/run_corruption_flow.py
```

Hoặc với môi trường `pip` đã kích hoạt:

```bash
python script/run_corruption_flow.py
```

### Kết quả tái hiện

| Lệnh             | Trạng thái                                    | Thời điểm chạy gần nhất | Bằng chứng                         |
| ----------------- | ----------------------------------------------- | ----------------------------- | ------------------------------------ |
| Baseline pipeline | [Artifacts baseline có sẵn; chưa rerun trong lần hoàn thiện báo cáo] | [Chưa xác minh lần chạy gần nhất]                  | [`data/results/baseline_metrics.json`, `data/quality/baseline_quality_report.json`; focused cleaning equivalence check PASS] |
| Corruption flow   | [Artifacts corruption/repair có sẵn; chưa rerun trong lần hoàn thiện báo cáo] | [Chưa xác minh lần chạy gần nhất]                  | [`data/results/corruption_log.json`, corrupted/repaired metrics và quality reports] |

## 5. Ingestion, cleaning và data contract

### Nguồn dữ liệu

| Thuộc tính                | Giá trị                             |
| --------------------------- | ------------------------------------- |
| Source                      | [Crossref Works REST API; local snapshot `data/raw/crossref_response.json`] |
| Query/filter                | [`agentic retrieval augmented generation large language model`; `has-abstract:true`; publication filter từ cấu hình]                  |
| Thời điểm lấy dữ liệu | [Không có timestamp lấy nguồn được xác nhận trong artifact]                           |
| Số record nhận được    | [24 raw records; 24 clean records]                         |
| Cơ chế retry/backoff      | [Tối đa 3 lần, timeout 20 giây, exponential wait; fallback sang snapshot local]                       |

### Raw và clean schema

| Trường        | Kiểu dữ liệu | Bắt buộc?  | Ý nghĩa   | Xử lý khi thiếu/sai |
| --------------- | --------------- | ------------ | ----------- | ---------------------- |
| [paper_id] | [string/DOI]         | [Có] | [Định danh ổn định của paper] | [Chuẩn hóa chữ thường; loại record nếu rỗng; deduplicate]        |
| [title, summary, published] | [string/date string]         | [Có] | [Tiêu đề, abstract và ngày xuất bản dùng cho clean model] | [Loại record nếu thiếu sau parse; date parse lỗi thành NaT rồi loại]        |

### Quy tắc cleaning

| Quy tắc                                 | Quality dimension liên quan | Số record bị tác động | Cách xác minh      |
| ---------------------------------------- | ---------------------------- | -------------------------: | -------------------- |
| [Loại HTML/JATS, chuẩn hóa whitespace; bỏ record thiếu trường bắt buộc] | [Validity/completeness]  |              [Raw records 24 → clean records 24; không có record bị loại trong artifact hiện tại] | [`data/raw/crossref_records.json` và `data/clean/papers_clean.json`] |
| [Deduplicate theo `paper_id`; tính `age_days` và text embedding năm phần]                     | [Uniqueness/freshness/consistency]                  |              [24 clean records; quality báo cáo không unexpected ID baseline] | [`data/clean/papers_clean.json`, baseline quality report] |

Giải thích cách nhóm tạo `text_for_embedding`, document ID và `age_days`:

[Embedding text ghép Title, Authors, Categories, Published và Summary; document ID gắn `paper_id` với vị trí record khi index; `age_days` là số ngày từ published đến ngày chạy pipeline, chặn giá trị âm về 0.]

## 6. Evaluation setup

| Thành phần                             | Cấu hình thực tế          |
| ---------------------------------------- | ----------------------------- |
| Số câu hỏi                            | [10]                 |
| Các`question_type`                    | [summary (3), authors (3), date (2), categories (2)]                  |
| Ground-truth document ID                 | [`ground_truth_doc_ids` trong `data/eval/test_set.json`, đối chiếu retrieved paper IDs]     |
| Embedding model                          | [sentence-transformers/all-MiniLM-L6-v2]                  |
| Vector store/collection                  | [ChromaDB persistent; `papers-baseline`, `papers-corrupted`, `papers-repaired`]                 |
| Retrieval`top_k`                       | [4]                   |
| LLM provider/model                       | [Cấu hình gemini / gemini-2.5-flash; saved answers xác nhận heuristic judge fallback]                   |
| Test set dùng chung cho ba trạng thái | [`data/eval/test_set.json`] |

Giải thích vì sao test set được giữ nguyên khi đánh giá baseline, corrupted và repaired:

[Dùng cùng câu hỏi và ground-truth IDs để giữ cố định mục tiêu đo; do đó chênh lệch metrics có thể đối chiếu giữa các trạng thái, dù bộ 10 câu còn nhỏ và QA có exact-title lookup.]

## 7. Kết quả baseline

### Artifact checklist

| Artifact                 | Đường dẫn thực tế                | Trạng thái | Ghi chú   |
| ------------------------ | -------------------------------------- | ------------ | ---------- |
| Raw response/records     | `data/raw/`                          | [Có] | [Crossref response và 24 parsed records] |
| Cleaned dataset          | `data/clean/`                        | [Có] | [24 records; CSV/JSON] |
| Embedding manifest/index | `data/embeddings/`                   | [Có] | [Manifest và persistent ChromaDB collections] |
| Evaluation set           | `data/eval/`                         | [Có] | [10 câu hỏi, bốn loại] |
| Baseline metrics         | `data/results/baseline_metrics.json` | [Có] | [Metrics đã đối chiếu với comparison report] |
| Quality/freshness        | `data/quality/`                      | [Có] | [Baseline/corrupted/repaired JSON reports] |
| Baseline report          | `data/reports/phase1_report.md`      | [Có] | [24 records; baseline metrics và freshness] |

### Baseline metrics

| Metric                 |       Giá trị | Diễn giải                             |
| ---------------------- | --------------: | --------------------------------------- |
| `retrieval_hit_rate` |     [1.0000] | [10/10 câu có ground-truth document trong kết quả retrieval]  |
| `mean_token_f1`      |     [1.0000] | [Trùng hoàn toàn theo token F1 trên benchmark này]                           |
| `judge_accuracy`     |     [1.0000] | [Heuristic fallback cho kết quả đúng; không phải LLM judge độc lập]                           |
| `mean_judge_score`   |     [5.0000] | [Điểm trung bình heuristic judge trên thang 1–5]                           |
| Ragas, nếu có        | [N/A] | [Không chạy; metrics artifact ghi RUN_RAGAS=1 để bật] |

## 8. Data quality và freshness

### Quality checks

| Check        | Quality dimension | Ngưỡng/kỳ vọng | Kết quả baseline      | Bằng chứng |
| ------------ | ----------------- | ------------------ | ----------------------- | ------------ |
| [Row count, non-null, unique paper_id] | [Completeness/uniqueness]       | [5–5,000 rows; required fields non-null; paper_id unique]         | [PASS; row count 24, unexpected unique IDs 0] | [`data/quality/baseline_quality_report.json`]   |
| [Summary length] | [Validity/completeness]       | [30–10,000 ký tự]         | [PASS; unexpected count 0] | [`data/quality/baseline_quality_report.json`]   |

### Freshness

| Thuộc tính               | Giá trị                           |
| -------------------------- | ----------------------------------- |
| Freshness được đo tại | [Clean dataframe `age_days`/`published`]            |
| Timestamp mới nhất       | [2026-07-22]                         |
| Ngưỡng freshness         | [180 ngày; tối đa 25% records stale]                         |
| Trạng thái baseline      | [Fresh/PASS]               |
| Lý do                     | [1/24 record stale, tỷ lệ 4.2%, thấp hơn ngưỡng 25%] |

## 9. Corruption scenarios và repair

| Corruption         | Cách tạo | Record bị tác động | Quality signal kỳ vọng | Tác động thực tế | Cách repair   |
| ------------------ | ---------- | ---------------------: | ------------------------ | --------------------- | -------------- |
| [Drop latest; blank summary; inject noise] | [Loại 5 record mới nhất, xóa summary 3 record, thêm noise vào 3 summary]  |          [5; 3; 3] | [Mất record/summary contract hoặc nhiễu text]              | [Corpus 24→21; summary length có 5 unexpected; retrieval hit rate 1.0→0.8]     | [Rebuild clean data từ raw-record snapshot] |
| [Truncate title; stale date; duplicate rows] | [Cắt 3 title còn 7 ký tự; lùi ngày 7 record 365 ngày; thêm 2 duplicate rows]  |          [3; 7; 2] | [Title ngắn, freshness fail, uniqueness fail]              | [8/21 stale (38.1%); unique check báo 4 unexpected values; F1 1.0→0.6909]     | [Re-clean raw records rồi tạo repaired index riêng] |

Corruption log:

- Đường dẫn: `data/results/corruption_log.json`
- Trạng thái: [Có]
- Nhận xét: [Ghi đủ 6 scenario, affected paper IDs và count; input 24 rows, output 21 rows.]

Giải thích cách repair đảm bảo dữ liệu được phục hồi từ nguồn đáng tin cậy thay vì chỉ che kết quả lỗi:

[Repair đọc lại `data/raw/crossref_records.json`, chạy cùng cleaning transformation rồi ghi repaired clean artifacts và collection riêng; không đảo ngược từng mutation trong corrupted dataframe.]

## 10. So sánh baseline, corrupted và repaired

| Metric/signal            | Baseline | Corrupted | Repaired | Thay đổi do corruption | Mức phục hồi | Nhận xét   |
| ------------------------ | -------: | --------: | -------: | -----------------------: | --------------: | ------------ |
| `retrieval_hit_rate`   |      [1.0000] |       [0.8000] |      [1.0000] |                      [-0.2000] |             [Trở về baseline] | [Retrieval hit giảm 20 điểm phần trăm trên cùng 10 câu.] |
| `mean_token_f1`        |      [1.0000] |       [0.6909] |      [1.0000] |                      [-0.3091] |             [Trở về baseline] | [Corruption làm giảm answer overlap; repair phục hồi.] |
| `judge_accuracy`       |      [1.0000] |       [0.7000] |      [1.0000] |                      [-0.3000] |             [Trở về baseline] | [Judge dùng heuristic fallback, không phải đánh giá LLM độc lập.] |
| `mean_judge_score`     |      [5.0000] |       [3.6000] |      [5.0000] |                      [-1.4000] |             [Trở về baseline] | [Điểm heuristic trung bình giảm sau corruption.] |
| Quality checks pass/fail |      [PASS] |       [FAIL] |      [PASS] |                      [PASS→FAIL] |             [PASS được phục hồi] | [Corrupted có duplicate ID và summary length violations.] |
| Freshness status         |      [PASS: 1/24 stale] |       [FAIL: 8/21 stale] |      [PASS: 1/24 stale] |                      [4.2%→38.1% stale] |             [Về 4.2% stale] | [Corrupted vượt SLA 25%; repaired quay lại dưới ngưỡng.] |

Nêu ít nhất hai kết luận có quan hệ nhân quả được hỗ trợ bởi artifacts:

1. [Drop/corrupt records và sửa text/date → unique/summary checks fail, stale ratio 38.1% → retrieval hit rate giảm 1.0 xuống 0.8 và token F1 xuống 0.6909.]
2. [Rebuild từ raw snapshot → 24 clean rows, GX/freshness PASS → cả bốn saved evaluation metrics trở về baseline.]

Không kết luận corruption “có tác động” nếu số liệu không cho thấy thay đổi. Nếu kết quả khác kỳ vọng, mô tả giả thuyết và cách nhóm đã kiểm tra.

## 11. Vấn đề tích hợp quan trọng

Mô tả một vấn đề phát sinh khi ghép các module trong pipeline và cách nhóm xử lý:

- **Triệu chứng:** [Corruption log cho thấy mất 5 record (24→21) nhưng row_count expectation vẫn PASS.]
- **Nguyên nhân:** [Expectation dùng khoảng rộng 5–5,000 thay vì expected-count hoặc retention threshold.]
- **Cách xử lý:** [Chưa có source-specific count/retention gate; ghi nhận là cải thiện cần phối hợp observability owner.]
- **Cách xác minh:** [`data/results/corruption_log.json` và `data/quality/corrupted_quality_report.json`; corrupted gate fail do các check khác và freshness.]

## 12. Giới hạn và hướng cải thiện

| Giới hạn hiện tại | Ảnh hưởng   | Hướng cải thiện có thể kiểm chứng |
| --------------------- | -------------- | ----------------------------------------- |
| [Benchmark chỉ có 10 câu và QA có exact-title lookup]          | [Khó khái quát chất lượng truy vấn tự nhiên rộng] | [Thêm held-out questions không trích title; báo cáo metric theo loại câu]                              |
| [Judge fallback heuristic; Ragas chưa chạy; full flow chưa rerun khi hoàn thiện báo cáo]          | [Không có independent semantic judge và chưa xác nhận fresh end-to-end run] | [Chạy judge/Ragas có cấu hình; rerun hai script và lưu exit status/artifact mới]                              |

## 13. Checklist trước khi nộp

- [x] Thông tin nhóm và repository chính xác.
- [x] Phân công khớp với module, artifact và kết quả thực tế.
- [ ] Lệnh tái hiện đã được chạy lại trên phiên bản dùng để nộp.
- [x] Baseline, corrupted và repaired dùng cùng evaluation set.
- [x] Bảng metrics khớp với các file trong `data/results/`.
- [x] Quality/freshness conclusions khớp với `data/quality/`.
- [x] Các đường dẫn báo cáo và artifact truy cập được.
- [ ] Mỗi thành viên đã hoàn thành báo cáo vai trò riêng.
- [ ] Không có `.env`, API key, token hoặc secret trong source, report, log hay ảnh.
