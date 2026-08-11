# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighLatencyP95
- Severity: Critical
- SLI/SLO liên quan: SLO Latency P95 <= 3000ms
- Điều kiện và thời gian duy trì: Latency P95 > 3000ms trong 5 phút liên tục
- Ảnh hưởng tới người dùng: Trải nghiệm tương tác chatbot bị chậm, phản hồi kéo dài quá 3 giây.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard chỉ số Latency P50/P95/P99 để xác định xem tăng đột biến ở phân khúc nào.
  2. Mở Langfuse Traces tìm các Trace có latency cao, kiểm tra từng span (RAG retrieval, LLM generation).
  3. Lọc `data/logs.jsonl` theo `correlation_id` của các trace chậm để xem nguyên nhân chi tiết.
- Mitigation tạm thời: Tắt incident nếu đang bị inject (`python scripts/inject_incident.py --disable`), giảm concurrency hoặc fallback prompt nhẹ hơn.
- Owner: On-Call Engineer

## Alert 2

- Tên: HighErrorRate
- Severity: High
- SLI/SLO liên quan: SLO Availability / Error Rate <= 2%
- Điều kiện và thời gian duy trì: Tỷ lệ lỗi request_failed / request_received > 2% trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận được phản hồi lỗi HTTP 500 từ hệ thống API.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard Error breakdown để biết `error_type` chính (ví dụ: Timeout, RateLimit, InvalidRequest).
  2. Tra cứu Langfuse Traces lỗi hoặc `data/logs.jsonl` có `event == "request_failed"`.
  3. Trích xuất `correlation_id` và đọc `payload.detail` cùng stack trace trong log.
- Mitigation tạm thời: Khởi động lại service API, cách ly downstream service bị lỗi hoặc fallback sang mô hình phụ.
- Owner: API Team

## Alert 3

- Tên: LowQualityScore
- Severity: Warning
- SLI/SLO liên quan: SLO Response Quality Score >= 0.75
- Điều kiện và thời gian duy trì: Điểm chất lượng trung bình (mean quality score) < 0.75 trong 10 phút
- Ảnh hưởng tới người dùng: Chất lượng câu trả lời suy giảm, thiếu thông tin RAG hoặc bị cắt ngắn.
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra Dashboard chỉ số Quality Score qua thời gian.
  2. Kiểm tra phiên bản Prompt hiện tại (`LANGFUSE_PROMPT_LABEL` / `prompt_version`).
  3. Mở Langfuse Traces kiểm tra điểm quality score từng trace và xem output của LLM.
- Mitigation tạm thời: Rollback `production` prompt label về phiên bản stable trước đó.
- Owner: AI Quality Team
