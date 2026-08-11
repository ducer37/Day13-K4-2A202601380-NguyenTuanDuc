# Báo cáo Day 13 Observability

## 1. Thông tin nhóm

- Tên nhóm:
- Repository URL:
- Commit SHA cuối:
- Thành viên và vai trò:

## 2. Kết quả kỹ thuật

- Điểm `validate_logs.py`: Checkpoint 0 baseline **30/100**; sau Checkpoint 1 **100/100**.
- Tổng số traces:
- Số PII leak còn lại: **0**.
- Link/đường dẫn dashboard: Contract tại [config/dashboard.yaml](../config/dashboard.yaml); screenshot dashboard runtime sẽ bổ sung ở Checkpoint 2.

Evidence Checkpoint 0:

- [Health check](evidence/checkpoint0_health.txt)
- [Load test](evidence/checkpoint0_load_test.txt)
- [Pytest](evidence/checkpoint0_pytest.txt)
- [Baseline validate logs](evidence/checkpoint0_validate_logs_baseline.txt)
- [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt)

Evidence Checkpoint 1:

- [Final validate logs](evidence/checkpoint1_validate_logs_final.txt)

## 3. Logging và tracing

- Evidence correlation ID: [checkpoint1_correlation_metadata.jsonl](evidence/checkpoint1_correlation_metadata.jsonl)
- Evidence PII redaction: [checkpoint1_pii_redaction.jsonl](evidence/checkpoint1_pii_redaction.jsonl)
- Evidence trace waterfall:
- Giải thích một span đáng chú ý:

## 4. Prompt versioning

- Prompt name:
- Version/label baseline:
- Version/label candidate:
- Trace ID của mỗi version:
- Bằng chứng đổi label hoặc rollback:

## 5. Dashboard, SLO và alerts

- Kết quả `validate_dashboard.py`: **HỢP LỆ: 6/6 panel**.
- Evidence dashboard: [Dashboard contract validator](evidence/checkpoint0_validate_dashboard.txt); screenshot runtime sẽ bổ sung ở Checkpoint 2.
- SLO đã chọn và lý do:
- Alert rules và runbook:

## 6. Điều tra challenge

- Challenge ID:
- Triệu chứng từ metrics:
- Trace ID liên quan:
- Log line/correlation ID liên quan:
- Root cause:
- Fix action:
- Preventive measure:

## 7. Đóng góp cá nhân

Với mỗi thành viên, ghi rõ nhiệm vụ và link commit/PR tương ứng.

| Thành viên | Phần việc | Commit/PR | Điều đã học |
|---|---|---|---|
| | | | |
