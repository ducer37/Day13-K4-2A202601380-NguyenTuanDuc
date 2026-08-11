# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- **Tên nhóm**: gehihi36
- **Repository URL**: https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc
- **Commit SHA cuối**: `7a4481a` (`7a4481a963e9f601c6e855ffba0e5bc1ed73b041`)
- **Thành viên và vai trò**:
  - **Nguyễn Tuấn Đức** - `2A202601380` (Trưởng nhóm): Metrics, Dashboard UI & SLO (`app/metrics.py`, `scripts/load_test.py`, `config/dashboard.yaml`, `config/slo.yaml`)
  - **Nguyễn Việt Phong** - `2A202601975`: Logging & PII Redaction (`app/middleware.py`, `app/main.py`, `config/logging_schema.json`)
  - **Ngô Quang Anh** - `2A202601106`: Tracing & Prompt Versioning (`app/tracing.py`, `app/agent.py`, `config/alert_rules.yaml`)
  - **Lê Trọng Việt Dũng** - `2A202601746`: Incident Investigation, Evidence & Report Documentation (`submission/REPORT.md`, `submission/PRESENTATION_WORKFLOW.md`, `submission/evidence/*`)

## 2. Kết quả kỹ thuật

- **Điểm `validate_logs.py`**: Baseline Checkpoint 0 **30/100**; sau Checkpoint 1 **100/100**.
- **Tổng số traces/observations**: Langfuse list hiển thị khoảng **84 observations**, trong đó **42 root observations** (đủ mốc tối thiểu 10 traces). Xem [Trace List](evidence/listtrace.png).
- **Số PII leak còn lại**: **0** — email/phone/card được hash/redact hoàn toàn qua `app/pii.py`.
- **Link/đường dẫn dashboard**: [Langfuse Cloud Dashboard](https://cloud.langfuse.com) (project `day13-observability-lab`) & Contract tại [config/dashboard.yaml](../config/dashboard.yaml).

**Evidence Checkpoint 0:**

- [Health check](evidence/checkpoint0_health.txt)
- [Load test](evidence/checkpoint0_load_test.txt)
- [Pytest](evidence/checkpoint0_pytest.txt)
- [Baseline validate logs](evidence/checkpoint0_validate_logs_baseline.txt)
- [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt)

**Evidence Checkpoint 1:**

- [Final validate logs](evidence/checkpoint1_validate_logs_final.txt)
- [PII Redaction evidence](evidence/checkpoint1_pii_redaction.jsonl)
- [PII Redaction UI screenshot](evidence/pii.png)

**Evidence Checkpoint 2:**

- [Trace List screenshot](evidence/listtrace.png)
- [Trace Waterfall screenshot](evidence/trace.png)
- [Prompt Versioning screenshot](evidence/prompt.png)
- [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt) — validator xác nhận contract 6/6 panel.

## 3. Logging và tracing

- **Evidence correlation ID**: [checkpoint1_correlation_metadata.jsonl](evidence/checkpoint1_correlation_metadata.jsonl)
  - Mỗi request có `correlation_id` format `req-<8hex>`, ví dụ:
    - `req-f6d72b8a` → session `k4-challenge-s02`, user `cb22af258a5e`
    - `req-38240679` → session `k4-challenge-s01`, user `f00ba60b3772`
- **Evidence PII redaction**: [checkpoint1_pii_redaction.jsonl](evidence/checkpoint1_pii_redaction.jsonl)
  - `user_id_hash` trong log là hash 12-char (ví dụ: `cb22af258a5e`), không lưu `user_id` gốc.
- **Evidence trace waterfall**:
  - Mỗi trace có 2 span lồng nhau: `chat-response` (generation) chứa `rag-retrieval` (retriever) — thể hiện đúng span hierarchy.
- **Giải thích một span đáng chú ý**:
  - Span `rag-retrieval` (`as_type="retriever"`) bị kéo dài 2.5 giây do `time.sleep(2.5)` trong `mock_rag.retrieve()` khi `STATE["rag_slow"] = True`. Đây chính là span bất thường gây ra toàn bộ tail latency.

**Phản biện Checkpoint 1.** Baseline CP0 chỉ có JSON log cơ bản, thiếu trường bắt buộc/enrichment và không có correlation ID; CP1 bổ sung schema thống nhất, context request (`correlation_id`, session, feature, model, môi trường) và redact PII. `clear_contextvars()` phải chạy ngay đầu middleware để xoá context của request trước; nếu không, worker bất đồng bộ có thể tái sử dụng contextvars cũ và gán correlation ID hoặc metadata của người dùng A sang log của người dùng B.

## 4. Prompt versioning

- **Prompt name**: `day13-chat`
- **Version/label baseline**: version `#1` — `v1 baseline`, label `production`.
- **Version/label candidate**: version `#2` — `v2 candidate`, label `latest`.
- **Evidence version/label**: [Prompt Versioning screenshot](evidence/prompt.png) hiển thị đồng thời hai version và label hiện hành.
- **Liên kết trace**: metadata trace dùng `prompt_name`, `prompt_label` và `prompt_version`; việc đổi label/rollback phải được kiểm tra trên trace metadata thay vì suy đoán từ template local.

## 5. Dashboard, SLO và alerts

- **Kết quả `validate_dashboard.py`**: **HỢP LỆ: 6/6 panel**.
- **Evidence dashboard**: [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt) xác nhận đúng 6/6 panel theo [config/dashboard.yaml](../config/dashboard.yaml). Dashboard runtime phải dùng `data/logs.jsonl`, time range 60 phút, refresh 30 giây và hiển thị threshold; validator chỉ xác minh contract, không thay thế ảnh runtime.
- **SLO đã chọn và lý do**: SLO cấu hình là `latency_p95 ≤ 3000ms` trong [config/slo.yaml](../config/slo.yaml), nhằm giữ phản hồi Chat/RAG trong khoảng người dùng chấp nhận được. Challenge đặt ngưỡng điều tra nghiêm ngặt hơn là 2000ms để phát hiện sớm suy giảm.
- **Alert rules và runbook**: Xem [config/alert_rules.yaml](../config/alert_rules.yaml) và [docs/alerts.md](../docs/alerts.md): HighLatencyP95 khi `p95(latency_ms) > 3000ms` trong 5 phút; HighErrorRate khi `error_rate_pct > 2%` trong 5 phút.

**Phản biện Checkpoint 2.** Alert nên dựa trên triệu chứng/SLO (chậm, lỗi, chất lượng kém) vì chúng phản ánh trực tiếp tác động tới người dùng, vẫn đúng khi service, tên hàm hoặc kiến trúc nội bộ thay đổi, và giúp on-call ưu tiên theo mức ảnh hưởng thay vì theo chi tiết triển khai.

## 6. Điều tra challenge

- **Challenge ID**: `day13-k4-observability-v1`
- **Incident**: `rag_slow`
- **Triệu chứng từ metrics** (`GET /metrics`):

| Metric            | Giá trị         | SLO       | Status    |
| ----------------- | --------------- | --------- | --------- |
| `latency_p50`     | 3566 ms         | < 2000 ms | 🔴 VI PHẠM |
| `latency_p95`     | 3631 ms         | < 2000 ms | 🔴 VI PHẠM |
| `latency_p99`     | 3631 ms         | < 2000 ms | 🔴 VI PHẠM |
| `traffic`         | 5 requests      | —         | ✅         |
| `error_breakdown` | `{}` (0 errors) | —         | ✅         |
| `quality_avg`     | 0.84            | —         | ✅         |

*Observation*: Toàn bộ 5/5 requests đều vượt threshold 2000ms (~3.5–3.6s). Không có error, chỉ latency tăng vọt → latency-only incident.

- **Correlation ID liên quan**: [Challenge run log](evidence/challenge_run.log) ghi nhận 5 request bị ảnh hưởng:
  - `req-f6d72b8a` | session: `k4-challenge-s02` | latency: `3584 ms`
  - `req-38240679` | session: `k4-challenge-s01` | latency: `3625 ms`
  - `req-787aacd8` | session: `k4-challenge-s05` | latency: `3637 ms`
  - `req-f45bf3bb` | session: `k4-challenge-s03` | latency: `3572 ms`
  - `req-78d1df57` | session: `k4-challenge-s04` | latency: `3474 ms`
- **Log line liên quan**:
  ```json
  {"service":"api","latency_ms":3545,"event":"response_sent","correlation_id":"req-f6d72b8a","session_id":"k4-challenge-s02","feature":"monitoring","ts":"2026-08-11T07:40:23.614Z"}
  ```
  Mẫu lặp lại với tất cả 5 requests → incident xảy ra 100% requests của feature monitoring.
- **Root cause**:
  - Khi `rag_slow` được bật, span `rag-retrieval` có delay cố định 2.5 giây theo code path dưới đây; đây là giả thuyết được đối chiếu với latency 3.47–3.64 giây trong challenge run.
  - Code path: `app/mock_rag.py`, line 17-18:
    ```python
    if STATE["rag_slow"]:
        time.sleep(2.5)  # gây delay cố định 2.5s trên MỌI request
    ```
  - Incident `rag_slow` được bật qua `POST /incidents/rag_slow/enable`, inject vào `STATE` dict dùng chung.
  - Signal chain: metrics challenge → latency vượt ngưỡng → correlation IDs trong [challenge run](evidence/challenge_run.log) → log `response_sent` cùng ID → code path có delay có điều kiện. Một waterfall của đúng trace chậm là bằng chứng trực quan cần thiết để xác nhận span-level trong lần chạy đó.
- **Fix action**:
  - Tắt incident ngay lập tức: `POST /incidents/rag_slow/disable`
  - Trong production thực tế:
    1. Rollback vector store service về phiên bản trước.
    2. Giảm `fetch_timeout_seconds` trong retrieval config.
    3. Bật circuit breaker: nếu retrieval > 500ms → trả về cached/fallback docs.
- **Preventive measure**:
  1. Alert rule: Kích hoạt alert khi `latency_p95 > 3000ms` kéo dài 5 phút (đã có trong `config/alert_rules.yaml`).
  2. Timeout circuit breaker: Đặt timeout cứng cho retrieval span (ví dụ 800ms) + fallback docs.
  3. Span-level SLO: Monitor riêng `rag-retrieval` span duration trong Langfuse dashboard.
  4. Canary deployment: Test vector store mới trên 5% traffic trước khi deploy toàn bộ.

**Phản biện Checkpoint 3.** Bằng chứng kỹ thuật thuyết phục nhất là ba tín hiệu cùng khớp: metric cho thấy latency tăng, waterfall của cùng trace cho thấy `rag-retrieval` chiếm phần lớn thời gian, và log cùng correlation ID loại trừ lỗi ở các span khác. Nếu chỉ có metrics, nhóm chỉ biết *có* suy giảm ở mức tổng thể; không thể truy ra request, metadata hay điều kiện code đã gây chậm, nên không thể kết luận root cause một cách chắc chắn.

## 7. Đóng góp cá nhân

| Thành viên         | Mã Sinh Viên | Phần việc chính | Files đảm nhận | Điều đã học |
| ------------------ | ------------ | --------------- | -------------- | ----------- |
| Nguyễn Việt Phong  | 2A202601975  | Logging & PII Redaction | `app/middleware.py`<br>`app/main.py`<br>`config/logging_schema.json` | Cách triển khai Correlation ID middleware, structlog contextvars tránh rò rỉ dữ liệu giữa các request và hash PII theo chuẩn JSON schema. Commit: [`a4a060f`](https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc/commit/a4a060ffe3f340e07272572428131723133bd14d). |
| Nguyễn Tuấn Đức    | 2A202601380  | Metrics, Dashboard UI & SLO (Trưởng nhóm) | `app/metrics.py`<br>`scripts/load_test.py`<br>`config/dashboard.yaml`<br>`config/slo.yaml` | Thiết kế dashboard 6-panel, tính toán percentile latency P50/P95/P99 và đo lường SLO. Commit: [`b109042`](https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc/commit/b1090422e70c324007e19d421c9ef8abf2bb5ac0). |
| Ngô Quang Anh      | 2A202601106  | Tracing & Prompt Versioning | `app/tracing.py`<br>`app/agent.py`<br>`config/alert_rules.yaml` | Phân cấp cây vết (nested spans: `generation` & `retriever`) với Langfuse SDK, gắn metadata prompt versioning và cấu hình alert rules. Commit: [`2e15057`](https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc/commit/2e150574e76df275ba3c3a384583085abf2926c5). |
| Lê Trọng Việt Dũng | 2A202601746  | Incident Investigation, Evidence & Report | `submission/REPORT.md`<br>`submission/PRESENTATION_WORKFLOW.md`<br>`submission/evidence/*` | Phương pháp điều tra sự cố theo luồng Metrics → Traces → Logs, xây dựng kịch bản thuyết trình và tổng hợp bằng chứng kỹ thuật. Commit: [`634887e`](https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc/commit/634887ec104472338332f554464a8855344414af). |

## 8. Các tính năng Nâng cao / Bonus (+10 Điểm)

Nhóm đã hoàn thiện trọn gói **3 tính năng Bonus cao cấp**:

### 🛡️ 1. Security & Admin Audit Logger (`app/audit.py` & `/audit` API)
- **Mục đích:** Tách kênh nhật ký kiểm toán (Audit Trail) chuyên biệt cho các thao tác an toàn/quản trị.
- **Thực thi:** Ghi nhận các sự kiện bật/tắt incident, thay đổi cấu hình, PII detection vào `data/audit.jsonl`. Expose API `GET /audit` để tra cứu lịch sử kiểm toán dạng JSON.

### 💰 2. LLM Cost Optimization Engine (`app/cost_optimization.py`)
- **Mục đích:** Tối ưu chi phí gọi LLM/RAG thông qua nén ngữ cảnh (Context Pruning & Whitespace Normalization).
- **Thực thi:** Tự động cắt giảm token thừa trong tài liệu RAG, tính toán mức tiết kiệm chi phí (`cost_saved_usd`, `reduction_pct`) và ghi nhận vào Langfuse generation metadata & API `GET /metrics` (`total_cost_saved_usd`). Đã đo lường thực tế tiết kiệm ~35% input tokens ($0.0045 USD / 10 reqs).

### 🤖 3. Automated Self-Healing Watchdog (`scripts/auto_remediate.py`)
- **Mục đích:** Tự động hóa quá trình giám sát và khôi phục sự cố hệ thống.
- **Thực thi:** Script chạy độc lập kiểm tra định kỳ `/health` và `/metrics`. Khi phát hiện vi phạm SLO (`P95 > 3000ms`) hoặc có incident hoạt động, script tự động kích hoạt lệnh khôi phục `POST /incidents/{name}/disable` (Self-healing) và ghi nhận Audit log.
