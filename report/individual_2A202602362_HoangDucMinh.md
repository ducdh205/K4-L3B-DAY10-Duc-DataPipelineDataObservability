# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | [Hoàng Đức Minh]             |
| MSSV               | [2A202602362]                     |
| Khóa/Lớp         | [K4-L3B]              |
| Tên nhóm         | [Duc]     |
| Vai trò chính    | [Data ingestion & cleaning owner]                 |
| Repository         | [https://github.com/ducdh205/K4-L3B-DAY10-Duc-DataPipelineDataObservability] |
| Ngày hoàn thành | [2026-09-26]               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| [Crossref ingestion/raw lineage]      | [`src/ingestion/crossref.py`: `parse_crossref_payload()`, `fetch_source_records()`, `load_raw_records()`]           | [Crossref payload hoặc local response snapshot]          | [`data/raw/crossref_response.json`, `data/raw/crossref_records.json`] | [Implementation và artifacts hiện có; full pipeline chưa rerun trong lần hoàn thiện báo cáo] |
| [Cleaning/data modeling]      | [`src/ingestion/cleaning.py`: `build_clean_dataframe()`, `build_embedding_text()`]           | [`PaperRecord` list và run date]          | [`data/clean/papers_clean.csv`, `data/clean/papers_clean.json`] | [24-row artifact hiện có; focused equivalence check đã PASS] |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Kiểm tra contract dữ liệu clean và output embedding text] | [Nguyễn Văn Tứ - evaluation/observability; Đinh Hoàng Đức - integration] | [Tái tạo 24 clean records từ raw records; paper_id order và toàn bộ text_for_embedding khớp artifact baseline] |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| [Parse Crossref và lưu raw lineage] | [`src/ingestion/crossref.py`; `data/raw/crossref_response.json`, `data/raw/crossref_records.json`] | [24 raw records được lưu để cleaning/repair sử dụng] | [Đọc artifact; code hỗ trợ snapshot fallback và retry] |
| [Chuẩn hóa, deduplicate và tạo embedding text] | [`src/ingestion/cleaning.py`; `data/clean/papers_clean.json`] | [24 clean records với age_days và five-part text_for_embedding] | [Focused comparison với artifact baseline; IDs và embedding text khớp chính xác] |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

[Clean artifact có 24 rows; chạy lại cleaning từ raw records cho cùng paper_id theo thứ tự và cùng từng giá trị text_for_embedding như artifact đã lưu.]

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

[Chuyển dữ liệu Crossref có cấu trúc không đồng đều thành raw record contract ổn định và clean dataframe dùng được cho embedding, retrieval, evaluation, quality checks và repair.]

### Cách triển khai

[Parser chuẩn hóa DOI/text, bỏ record không có DOI hoặc title và loại DOI trùng, trích xuất authors/categories/date, đồng thời lưu response và parsed records. Cleaning chuẩn hóa text, deduplicate theo paper_id, loại dòng thiếu paper_id/title/summary/published, tính age_days theo run date, tạo joined fields và ghép embedding text từ Title, Authors, Categories, Published, Summary.]

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | [PaperRecord fields từ Crossref: DOI, title, abstract, authors, subjects, dates và URLs]           |
| Output                         | [Raw JSON lineage; clean CSV/JSON với paper_id, required fields, age_days, joined fields và text_for_embedding] |
| Module phụ thuộc             | [`src/core/config.py`, Crossref API hoặc local response snapshot]                    |
| Module sử dụng output        | [`src/evaluation/testset.py`, `src/retrieval/index.py`, `src/observability/quality.py`, repair flow]                    |
| Điều kiện lỗi cần xử lý | [Fetch failure, payload không có record hợp lệ, thiếu trường bắt buộc, date không parse được, duplicate paper_id]                   |

### Cách xác minh

```bash
[Set $env:PYTHONPATH='src'; chạy focused Python check dựng lại dataframe từ `data/raw/crossref_records.json` rồi so sánh 24 paper_id và text_for_embedding với `data/clean/papers_clean.json`.]
```

- **Kết quả mong đợi:** [24 clean rows; ID order và embedding text khớp artifact hiện có.]
- **Kết quả thực tế:** [PASS: 24 clean records and embedding texts exactly match the saved artifact.]
- **Artifact/log:** [`data/raw/crossref_records.json`, `data/clean/papers_clean.json`; full pipeline commands chưa chạy lại trong lần kiểm tra này.]

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** [Cần tái lập pipeline và repair khi Crossref không sẵn sàng hoặc dữ liệu đã bị synthetic corruption.] 
- **Các phương án đã cân nhắc:** [Gọi Crossref trực tiếp mỗi lần chạy; hoặc lưu raw response/records rồi dùng snapshot để tái lập.] 
- **Phương án đã chọn:** [Giữ raw response và normalized raw records; dùng local snapshot khi refresh tắt hoặc fetch thất bại; repair đọc lại raw records.] 
- **Lý do:** [Giảm phụ thuộc mạng, giữ lineage và tránh cố đảo ngược từng mutation trên corrupted dataframe.] 
- **Bằng chứng quyết định phù hợp:** [`data/raw/` artifacts tồn tại; repair flow gọi `load_raw_records()`; repaired artifacts trở về 24 rows và baseline metrics.] 

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** [Không có lỗi runtime cụ thể được ghi nhận trong artifacts đã kiểm tra; tối ưu được phát hiện là lặp xử lý text trong cleaning.] 
- **Lệnh hoặc bước tái hiện:** [Dựng lại clean dataframe từ saved raw records và so sánh với clean JSON baseline.] 
- **Nguyên nhân gốc:** [Author/category bị normalize hai lần mỗi giá trị; `DataFrame.apply(axis=1)` tạo Series cho từng dòng khi dựng embedding text.] 
- **Cách xử lý:** [Normalize mỗi giá trị một lần và dựng embedding text từ dictionaries của năm cột cần thiết.] 
- **Cách xác minh sau khi sửa:** [Focused equivalence check PASS; 24 paper_id theo cùng thứ tự và mọi text_for_embedding giống artifact.] 
- **Điều học được:** [Có thể giảm overhead xử lý theo dòng nếu bảo toàn output contract và xác minh chính xác với artifact.] 

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Quality gate hiện chưa kiểm tra source-specific expected row count/retention.]
- **Những gì đã loại trừ:** [Artifacts cho thấy quality gate vẫn fail do uniqueness, summary length và freshness; chưa có bằng chứng full pipeline được rerun trong lần này.]
- **Bước tiếp theo:** [Phối hợp observability owner bổ sung retention/count expectation và chạy lại hai pipeline.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

[Crossref response được parse và lưu thành raw records; cleaning chuẩn hóa và deduplicate thành clean dataframe, rồi MiniLM embed text_for_embedding vào ChromaDB. Evaluation set lưu câu hỏi, ground-truth answer và document IDs; retrieval hit khi retrieved paper ID trùng ID kỳ vọng, answer được đo bằng token F1 và judge. GX kiểm tra schema/completeness/uniqueness/summary length, còn freshness đo tỷ lệ age_days > 180 và fail nếu trên 25%. Dùng cùng test set để so sánh trên cùng câu hỏi/ground truth. Repair thành công khi clean artifact có 24 rows, quality/freshness PASS và metrics repaired trở lại mức baseline; judge ở artifacts là heuristic fallback và Ragas chưa chạy.]

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |      [1.0000] |       [0.8000] |      [1.0000] | [Giảm 0.2 do corruption, rồi trở về baseline sau repair.]              |
| `mean_token_f1`      |      [1.0000] |       [0.6909] |      [1.0000] | [Giảm 0.3091; phục hồi trên cùng 10 câu hỏi.]                           |
| `judge_accuracy`     |      [1.0000] |       [0.7000] |      [1.0000] | [Các con số đến từ heuristic fallback, không phải LLM judge độc lập.]              |
| `mean_judge_score`   |      [5.0000] |       [3.6000] |      [5.0000] | [Điểm giảm 1.4 rồi phục hồi; cần diễn giải trong giới hạn heuristic judge.]              |
| Quality checks         |      [PASS] |       [FAIL] |      [PASS] | [Corrupted report có duplicate-ID và summary-length violations.]              |
| Freshness status       |      [PASS: 1/24 stale] |       [FAIL: 8/21 stale] |      [PASS: 1/24 stale] | [Stale ratio 4.2% → 38.1% → 4.2%; ngưỡng 25%.]              |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Mất/sửa record và backdate → GX uniqueness/summary và freshness fail → retrieval hit rate 1.0→0.8, token F1 1.0→0.6909.]
2. [Rebuild từ raw snapshot → 24 clean rows, quality/freshness PASS → bốn metrics saved repaired trở về baseline.]

Corruption nào ảnh hưởng rõ nhất và vì sao?

[Drop latest làm mất các document được hỏi trong benchmark; đồng thời blank/truncate/noise phá nội dung, duplicate/date corruption làm quality và freshness fail. Tác động tổng hợp thể hiện ở hit rate giảm 20 điểm phần trăm và token F1 giảm 0.3091; artifacts hiện tại không cô lập riêng hiệu ứng từng mutation.]

Kết quả nào khác với kỳ vọng ban đầu?

[Drop latest 5 records khiến tổng còn 21 nhưng row_count expectation 5–5,000 vẫn PASS. Điều này xác nhận check hiện tại không đo expected count/retention; corruption gate vẫn FAIL nhờ uniqueness, summary length và freshness checks.]

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. [Raw snapshot giúp giữ lineage và tái tạo repair thay vì sửa ngược dữ liệu đã bị biến đổi.]
2. [Quality/schema checks và freshness là các tín hiệu khác nhau; cần expected-count/retention signal để bắt missing records.] 
3. [Data corruption tác động đến retrieval và answer metrics; đánh giá cùng test set giúp quan sát thay đổi có đối chiếu.] 

### Nếu có thêm thời gian

[Thêm tests cho Crossref date/missing fields/duplicate IDs và cleaning determinism; sau đó mở rộng held-out benchmark không dùng quoted exact titles và chạy semantic judge/Ragas thật.] 

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [X] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [X] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [X] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [X] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [X] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [X] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** [Hoàng Đức Minh]
**Ngày xác nhận:** [26/09/2026]
