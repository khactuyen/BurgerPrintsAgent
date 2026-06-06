# Harness Engineering Implementation Plan

Tài liệu này là lộ trình triển khai thực tế cho Agent Engineering Harness trong
BurgerPrintsAgent. Mục tiêu là tăng chất lượng hành vi agent mà không làm chậm
runtime đáng kể.

## Nguyên tắc triển khai

- Ưu tiên rule-based control trước, không thêm LLM call mới.
- Không làm chậm startup hoặc chat path quá vài chục ms.
- Mỗi phase phải có giá trị demo rõ ràng.
- Model chỉ đề xuất; harness kiểm tra và quyết định tool nào được chạy.

## Phase 1: Policy Engine tối thiểu

**Mục tiêu**

Chặn các hành vi rủi ro nhất bằng code thay vì chỉ dựa vào prompt.

**Làm ngay**

- Tạo `backend/harness/policy_engine.py`.
- Chuẩn hóa `PolicyDecision`.
- Kiểm tra tool access cơ bản.
- Chặn `create_order` nếu thiếu:
  - SKU
  - SKU có thật trong DuckDB
  - xác nhận SKU trong tin nhắn hiện tại
  - Harness order flag đang bật
- Trả mã lỗi có cấu trúc.

**Độ trễ ước tính**

`5-30 ms/request`, chủ yếu do check SKU trong DuckDB.

**Kết quả mong đợi**

- Model không thể tạo đơn bằng SKU bịa.
- Model không thể dùng xác nhận cũ.
- Lý do bị chặn được log rõ.

**Trạng thái triển khai**

Đã triển khai trong:

- `backend/harness/policy_engine.py`
- `backend/harness/__init__.py`
- `backend/agent/gemini_agent.py`

Policy hiện chạy trước khi tool được thực thi trong `execute_tool()`.

Các rule đã có:

- Read-only tools được allow:
  - `search_products`
  - `get_sku_info`
  - `get_base_cost`
  - `get_shipping_cost`
  - `get_production_time`
  - `get_shipping_time`
  - `check_sku_availability`
  - `check_provider_status`
  - `check_region_support`
  - `get_order_creation_status`
- Unknown tool bị chặn bằng `TOOL_NOT_ALLOWED`.
- `create_order` bị coi là critical tool và phải qua policy.
- `create_order` bị chặn nếu:
  - Harness order flag đang tắt: `ORDER_CREATION_DISABLED`
  - thiếu SKU: `SKU_REQUIRED`
  - SKU không tồn tại trong DuckDB: `SKU_NOT_FOUND`
  - user chưa xác nhận đúng SKU trong tin nhắn hiện tại: `ORDER_CONFIRMATION_REQUIRED`
  - thiếu địa chỉ: `ADDRESS_REQUIRED`
  - quantity không hợp lệ: `INVALID_QUANTITY`
  - quantity lớn hơn 10: `QUANTITY_REQUIRES_REVIEW`

Tool denial trả về dạng chuẩn:

```json
{
  "ok": false,
  "code": "ORDER_CONFIRMATION_REQUIRED",
  "error": "..."
}
```

**Kết quả test**

Test trực tiếp bằng container tạm sau khi dừng backend để tránh DuckDB lock:

```text
missing_confirm False ORDER_CONFIRMATION_REQUIRED
confirmed       True  POLICY_ALLOWED
fake_sku        False SKU_NOT_FOUND
large_qty       False QUANTITY_REQUIRES_REVIEW
safe_tool       True  POLICY_ALLOWED
unknown_tool    False TOOL_NOT_ALLOWED
```

Test qua HTTP chat cũng xác nhận policy chạy cho read-only tool:

```text
Policy decision for tool search_products:
allowed=True code=POLICY_ALLOWED reason=Safe read-only tool.
```

Giới hạn test hiện tại:

- Gemini API đang hết free-tier quota, nên chưa test được full chat flow cho
  case model gọi `create_order`.
- Policy đã được test trực tiếp ở code path riêng và được gắn vào
  `execute_tool()`, nên khi Gemini gọi `create_order`, policy sẽ chạy trước API
  thật.

## Phase 2: Tool Registry + Executor

**Mục tiêu**

Thay chuỗi `if/elif` lớn trong `gemini_agent.py` bằng registry có metadata.

**Làm**

- Tạo `ToolDefinition`.
- Gắn metadata:
  - risk level
  - timeout
  - retry
  - required permissions
  - idempotent
- Executor chịu trách nhiệm:
  - timeout
  - policy check
  - structured result
  - log latency

**Độ trễ ước tính**

`5-30 ms/request`, trừ khi tool timeout.

**Trạng thái triển khai**

Đã triển khai:

- `backend/harness/tool_registry.py`
  - `ToolDefinition`
  - `RiskLevel`
  - metadata timeout, retry, permission và idempotency
  - chặn cấu hình retry cho tool không idempotent
- `backend/harness/tool_executor.py`
  - mọi tool chạy qua policy trước khi thực thi
  - áp dụng timeout bằng `asyncio.wait_for`
  - chỉ retry theo metadata của tool
  - trả lỗi có cấu trúc: `TOOL_NOT_REGISTERED`, `TOOL_TIMEOUT`, `TOOL_EXECUTION_ERROR`
  - log risk, attempt và duration
- `backend/harness/default_tools.py`
  - đăng ký toàn bộ tool hiện có
  - `create_order` là critical, timeout 15 giây, retry 0, không idempotent
- `backend/agent/tool_handlers.py`
  - tách handler khỏi chuỗi `if/elif` trong agent
- `backend/agent/gemini_agent.py`
  - `execute_tool()` hiện chuyển mọi tool call qua `ToolExecutor`

Order production:

- `backend/api/burgerprints.py` hiện gửi `sandbox=false`.
- Policy xác nhận SKU, kiểm tra địa chỉ, kiểm tra `design_url_front` và giới hạn quantity vẫn bắt buộc trước khi tạo đơn.
- `create_order` hiện bắt buộc có `design_url_front` là public `http/https` URL. Nếu thiếu hoặc sai định dạng, policy trả `DESIGN_URL_REQUIRED` hoặc `INVALID_DESIGN_URL` trước khi gọi BurgerPrints API.
- Payload gửi BurgerPrints có `design_url_front`; nếu không có `mockup_url_front` riêng thì dùng lại `design_url_front`.
- Không chạy test tạo đơn thật trong automated test suite.

Test Phase 2:

- `backend/tests/test_tool_executor.py`
  - unknown tool trả structured error
  - timeout được áp dụng
  - registry chặn retry cho non-idempotent tool
- `backend/tests/test_order_creation.py`
  - create order API luôn được mock, không tạo đơn production trong test tự động

## Phase 3: Structured Context & Memory

**Mục tiêu**

Hỗ trợ hội thoại nhiều lượt mà không để model tự hiểu nhầm lịch sử.

**Làm**

- Lưu structured session state:
  - marketplace
  - destination
  - target margin
  - priority
  - selected product/SKU
- Confirmation là object riêng có TTL và consume state.
- Không dùng chat history làm nguồn xác nhận.

**Độ trễ ước tính**

`5-30 ms/request` nếu lưu RAM.

## Phase 4: Observability cơ bản

**Mục tiêu**

Debug nhanh vì sao agent trả lời sai.

**Làm**

- Sinh `trace_id`.
- Log:
  - model call
  - tool call
  - policy decision
  - error code
  - duration
- Mask dữ liệu nhạy cảm trong log.

**Độ trễ ước tính**

`1-20 ms/request`.

## Phase 5: Evaluation Harness

**Mục tiêu**

Bắt regression khi sửa prompt/model/tool.

**Làm**

- Tạo dataset 10-20 case từ lỗi thật:
  - Etsy US margin >40 không hỏi form
  - Premium hoodie giá rẻ phải nêu trade-off
  - Không bịa SKU
  - Không tạo đơn khi chưa xác nhận
  - Harness bật không được nói tắt
- Deterministic grader kiểm tra:
  - forbidden tool calls
  - required policy codes
  - forbidden claims

**Độ trễ runtime**

`0 ms`, vì chỉ chạy trong dev/CI.

## Thứ tự triển khai khuyến nghị

1. Policy Engine tối thiểu
2. Tool Registry + Executor
3. Structured Context & Memory
4. Observability
5. Evaluation Harness

## Definition of Done cho MVP Harness

- Critical tool `create_order` luôn đi qua policy.
- Policy denial có `ok=false`, `code`, `error`.
- Mọi SKU dùng để order phải tồn tại trong DuckDB.
- Xác nhận order chỉ tính trên tin nhắn hiện tại.
- Logs có đủ tool name, policy code và reason.
- Không thêm LLM call mới cho harness.

## Policy Extension Status

Implemented after Phase 2:

- SKU Presentation Policy
  - `get_sku_info` records that a SKU was presented for the current session.
  - `create_order` is blocked with `SKU_PRESENTATION_REQUIRED` if a session tries to order before SKU details were presented.
- Destination Policy
  - Address country/state/postal-code mismatch is blocked.
  - Provider `countries_served` is enforced only when cache has verified country data.
  - Unsupported region API responses are not treated as verified support.
- Design Validation Policy
  - `prepare_order_review` and `create_order` validate `design_url_front`.
  - Blocks non-http URLs, localhost/private network URLs, SVG, non-image responses, oversized files, and unsupported image resolutions.
- Order Confirmation Policy
  - Added `prepare_order_review` tool.
  - Agent must call `prepare_order_review` before asking for final confirmation.
  - `create_order` requires `order_review_token`.
  - Duplicate order fingerprints are blocked for a short TTL.
  - Quantity-large auto-block was removed by product decision.
- External API Response Policy
  - BurgerPrints order errors are normalized into structured codes such as `SHIPPING_SERVICE_UNAVAILABLE`, `DESIGN_URL_REQUIRED_BY_API`, and `DESIGN_RESOLUTION_INVALID`.

Implementation files:

- `backend/harness/order_state.py`
- `backend/harness/design_validator.py`
- `backend/harness/api_response_policy.py`
- `backend/agent/tool_handlers.py`
- `backend/agent/tools.py`
- `backend/harness/policy_engine.py`
- `backend/harness/tool_executor.py`

Latest test:

```text
13 passed
```
