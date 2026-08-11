# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- **Tên nhóm**: gehihi36
- **Repository URL**: https://github.com/ducer37/Day13-K4-2A202601380-NguyenTuanDuc
- **Commit SHA cuối**: `ad19614` (`ad196142dc9cac171803a12f5163a0c8ec1a7dc7`)
- **Thành viên và vai trò**:
  - Nguyễn Tuấn Đức - 2A202601380 (Trưởng nhóm, toàn bộ implementation)
  - Nguyễn Việt Phong - 2A202601975 (Hỗ trợ phân tích log schema & kiểm thử PII redaction)
  - Lê Trọng Việt Dũng - 2A202601746 (Kiểm thử API endpoints, validate SLO & alert rules config)
  - Ngô Quang Anh - 2A202601106 (Tổng hợp evidence, kiểm tra dashboard contract & báo cáo)

## 2. Kết quả kỹ thuật

- **Điểm `validate_logs.py`**: Baseline Checkpoint 0 **30/100**; sau Checkpoint 1 **100/100**.
- **Tổng số traces**: ≥ 5 (challenge run) + traces từ Checkpoint 1/2 (Tổng số log records analyzed: 21 records).
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

## 4. Prompt versioning

- **Prompt name**: `day13-chat`
- **Version/label baseline**: `local-v1` (local fallback — prompt chưa tạo trên Langfuse cloud)
- **Version/label candidate**: `production` label trên Langfuse (sau khi tạo prompt)
- **Trace ID của mỗi version**: Xem Langfuse UI → Traces → filter by `prompt_source`
- **Bằng chứng đổi label hoặc rollback**: `prompt_source` trong trace metadata là `local-fallback` khi Langfuse không có prompt; thay bằng `langfuse` sau khi tạo prompt trên cloud.

## 5. Dashboard, SLO và alerts

- **Kết quả `validate_dashboard.py`**: **HỢP LỆ: 6/6 panel**.
- **Evidence dashboard**: [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt); filter `feature=monitoring` trên Langfuse cloud dashboard.
- **SLO đã chọn và lý do**: `latency_p95 < 2000ms` (theo `config/slo.yaml` và `latency_threshold_ms: 2000` trong challenge) nhằm bảo đảm trải nghiệm phản hồi ứng dụng Chat/RAG cho người dùng.
- **Alert rules và runbook**: Xem [config/alert_rules.yaml](../config/alert_rules.yaml) — Alert kích hoạt khi p95 vượt SLO (`> 2000ms`) kéo dài > 1 phút hoặc `error_rate > 5%`.

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

- **Trace ID liên quan**: Tất cả 5 traces từ load test đều bị ảnh hưởng:
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
  - Span `rag-retrieval` (`as_type="retriever"`) trong Langfuse trace hiển thị thời gian ~2500ms — chiếm ~70% tổng latency mỗi request.
  - Code path: `app/mock_rag.py`, line 17-18:
    ```python
    if STATE["rag_slow"]:
        time.sleep(2.5)  # gây delay cố định 2.5s trên MỌI request
    ```
  - Incident `rag_slow` được bật qua `POST /incidents/rag_slow/enable`, inject vào `STATE` dict dùng chung.
  - Signal chain: Metrics → p95 = 3631ms vượt SLO → Trace → span `rag-retrieval` dài bất thường → Log → `latency_ms` ≈ 3500ms nhất quán trên toàn bộ requests → Xác nhận root cause: vector store retrieval bị chậm.
- **Fix action**:
  - Tắt incident ngay lập tức: `POST /incidents/rag_slow/disable`
  - Trong production thực tế:
    1. Rollback vector store service về phiên bản trước.
    2. Giảm `fetch_timeout_seconds` trong retrieval config.
    3. Bật circuit breaker: nếu retrieval > 500ms → trả về cached/fallback docs.
- **Preventive measure**:
  1. Alert rule: Kích hoạt alert khi `latency_p95 > 2000ms` kéo dài > 1 phút (đã có trong `config/alert_rules.yaml`).
  2. Timeout circuit breaker: Đặt timeout cứng cho retrieval span (ví dụ 800ms) + fallback docs.
  3. Span-level SLO: Monitor riêng `rag-retrieval` span duration trong Langfuse dashboard.
  4. Canary deployment: Test vector store mới trên 5% traffic trước khi deploy toàn bộ.

## 7. Đóng góp cá nhân

| Thành viên         | Phần việc                                                                                                                                                                          | Commit/PR | Điều đã học                                                                                                                           |
| ------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Nguyễn Tuấn Đức    | Setup env (Python 3.12), tracing với Langfuse (`@observe`, nested spans, explicit input/output), hoàn thiện middleware (correlation ID, contextvars), điều tra incident `rag_slow` | `ad19614` | Span hierarchy trong Langfuse cho phép khoanh vùng span chậm chính xác; `flush_langfuse()` quan trọng để không mất event khi shutdown |
| Nguyễn Việt Phong  | Hỗ trợ phân tích log schema và kiểm thử PII redaction                                                                                                                              | `ad19614` | Cách thực hiện hashing user ID và redact thông tin nhạy cảm qua pii.py                                                                |
| Lê Trọng Việt Dũng | Kiểm thử API endpoints, validate SLO & alert rules config                                                                                                                          | `ad19614` | Thiết lập SLO latency và định nghĩa alert rule phù hợp cho hệ thống AI/RAG                                                            |
| Ngô Quang Anh      | Tổng hợp evidence, kiểm tra dashboard contract & viết báo cáo                                                                                                                      | `ad19614` | Cách xây dựng dashboard contract validator và mô hình hóa metrics observability                                                       |

