from google.generativeai.types import FunctionDeclaration, Tool
import json

# =======================================================
# 1. search_products
# =======================================================
search_products_func = FunctionDeclaration(
    name="search_products",
    description="Tìm kiếm sản phẩm trong catalog dựa trên text query, danh mục, hoặc chất liệu. Tool này sử dụng BM25 và Vector Search kết hợp DuckDB để tìm kiếm nhanh.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Câu query tìm kiếm tự do (ví dụ: 'áo thun cotton mùa hè', 'premium mug')"
            },
            "category": {
                "type": "string",
                "description": "Danh mục sản phẩm (ví dụ: 't-shirt', 'polo', 'hoodie', 'mug', 'poster', 'tote')"
            },
            "material": {
                "type": "string",
                "description": "Chất liệu (ví dụ: 'cotton', 'polyester', 'ceramic')"
            }
        }
    }
)

# =======================================================
# 2. get_sku_info
# =======================================================
get_sku_info_func = FunctionDeclaration(
    name="get_sku_info",
    description="Lấy danh sách các SKUs (bao gồm màu sắc, kích thước, xưởng, mã sku_code) của một product_id cụ thể.",
    parameters={
        "type": "object",
        "properties": {
            "sku_code": {
                "type": "string",
                "description": "Ma SKU cu the user dua, vi du USBG5000DTF-Black-S. Uu tien dung field nay khi user muon xem hoac dat mot SKU."
            },
            "product_id": {
                "type": "string",
                "description": "ID của sản phẩm (ví dụ: P1, P2)"
            }
        },
    }
)

# =======================================================
# 3. get_base_cost
# =======================================================
get_base_cost_func = FunctionDeclaration(
    name="get_base_cost",
    description="[REALTIME] Lấy giá sản xuất (base cost) cập nhật nhất của một hoặc nhiều SKU codes. Luôn gọi hàm này để báo giá chính xác, không được đoán.",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách các mã SKU cần lấy giá."
            }
        },
        "required": ["sku_codes"]
    }
)

# =======================================================
# 4. get_shipping_cost
# =======================================================
get_shipping_cost_func = FunctionDeclaration(
    name="get_shipping_cost",
    description="[REALTIME] Lấy phí vận chuyển cập nhật nhất của SKU đến một quốc gia cụ thể.",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách mã SKU."
            },
            "destination": {
                "type": "string",
                "description": "Quốc gia đích đến (ví dụ: US, EU, AU, CA, VN)."
            }
        },
        "required": ["sku_codes", "destination"]
    }
)

# =======================================================
# 5. get_production_time
# =======================================================
get_production_time_func = FunctionDeclaration(
    name="get_production_time",
    description="[REALTIME] Lấy thời gian sản xuất ước tính hiện tại của SKU.",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách mã SKU."
            }
        },
        "required": ["sku_codes"]
    }
)

# =======================================================
# 6. get_shipping_time
# =======================================================
get_shipping_time_func = FunctionDeclaration(
    name="get_shipping_time",
    description="[REALTIME] Lấy thời gian vận chuyển ước tính của SKU đến quốc gia đích.",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách mã SKU."
            },
            "destination": {
                "type": "string",
                "description": "Quốc gia đích đến."
            }
        },
        "required": ["sku_codes", "destination"]
    }
)

# =======================================================
# 7. check_sku_availability
# =======================================================
check_sku_availability_func = FunctionDeclaration(
    name="check_sku_availability",
    description="[REALTIME] Kiểm tra trạng thái tồn kho và hoạt động của SKU (active, inactive, discontinued). Không được recommend SKU inactive.",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách mã SKU cần check."
            }
        },
        "required": ["sku_codes"]
    }
)

# =======================================================
# 8. check_provider_status
# =======================================================
check_provider_status_func = FunctionDeclaration(
    name="check_provider_status",
    description="[REALTIME] Kiểm tra trạng thái của xưởng (active, overload, maintenance). Không được recommend xưởng overload/maintenance.",
    parameters={
        "type": "object",
        "properties": {
            "provider_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách ID xưởng cần check."
            }
        },
        "required": ["provider_ids"]
    }
)

# =======================================================
# 9. check_region_support
# =======================================================
check_region_support_func = FunctionDeclaration(
    name="check_region_support",
    description="[REALTIME] Kiểm tra xem SKU có hỗ trợ vận chuyển đến quốc gia đích hay không (True/False).",
    parameters={
        "type": "object",
        "properties": {
            "sku_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Danh sách mã SKU."
            },
            "region": {
                "type": "string",
                "description": "Khu vực/Quốc gia đích đến (US, EU, AU...)."
            }
        },
        "required": ["sku_codes", "region"]
    }
)

# =======================================================
# 10. create_order
# =======================================================
create_order_func = FunctionDeclaration(
    name="create_order",
    description="Tạo đơn hàng fulfillment mới. BẮT BUỘC: Không bao giờ thu thập địa chỉ người nhận nếu chưa gọi tool check_sku_availability để đảm bảo SKU tồn tại. CHỈ GỌI khi người dùng gõ câu lệnh có chứa chữ 'xác nhận'. BẮT BUỘC phải có design_url_front là link ảnh public http/https mở được trên internet, ví dụ https://domain.com/design.png hoặc .jpg. Không dùng file local, localhost, private Google Drive link, hoặc placeholder. Tuyệt đối không tự chọn ngẫu nhiên.",
    parameters={
        "type": "object",
        "properties": {
            "sku": {"type": "string", "description": "Mã SKU để order"},
            "quantity": {"type": "integer", "description": "Số lượng (mặc định 1)"},
            "address": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "street": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "zip": {"type": "string"},
                    "country": {"type": "string"}
                },
                "required": ["name", "street", "city", "state", "zip", "country"]
            },
            "design_url_front": {
                "type": "string",
                "description": "Bat buoc. Public http/https URL cua file design mat truoc, vi du https://domain.com/design-front.png hoac .jpg. Link phai mo duoc cong khai tren internet; khong dung file local, localhost, private link, hoac placeholder."
            },
            "mockup_url_front": {
                "type": "string",
                "description": "Public http/https URL cua mockup mat truoc neu co. Neu khong co se dung design_url_front."
            },
            "shipping_method": {"type": "string", "description": "Ví dụ: 'standard', 'express'"}
        },
        "required": ["sku", "quantity", "address", "design_url_front"]
    }
)

get_order_creation_status_func = FunctionDeclaration(
    name="get_order_creation_status",
    description="Kiểm tra trạng thái bật/tắt hiện tại của tính năng tạo đơn từ Harness. Phải gọi tool này thay vì tự suy đoán trạng thái.",
    parameters={"type": "object", "properties": {}}
)

# Group all tools into a single Tool object
agent_tools = Tool(
    function_declarations=[
        search_products_func,
        get_sku_info_func,
        get_base_cost_func,
        get_shipping_cost_func,
        get_production_time_func,
        get_shipping_time_func,
        check_sku_availability_func,
        check_provider_status_func,
        check_region_support_func,
        get_order_creation_status_func,
        create_order_func
    ]
)
