# Harness trong dự án BurgerPrintsAgent

Tài liệu này giải thích Harness theo cách dễ hiểu cho người không chuyên kỹ thuật.

## Harness là gì?

Harness là một nền tảng giúp đội phát triển điều khiển và triển khai phần mềm an toàn hơn.

Trong dự án này, phần Harness quan trọng nhất là **Feature Flags**.

Có thể hiểu Feature Flag giống như một **công tắc bật/tắt tính năng từ xa**.

Ví dụ ngoài đời:

- Công tắc đèn bật/tắt bóng đèn mà không cần thay dây điện.
- Remote bật/tắt TV mà không cần mở máy ra sửa.
- Admin bật/tắt một chức năng trong app mà không cần lập trình lại.

Với Harness Feature Flags, team có thể bật hoặc tắt một tính năng ngay trên dashboard Harness, còn ứng dụng sẽ tự đọc trạng thái đó và quyết định có cho người dùng sử dụng tính năng hay không.

## Harness dùng để làm gì trong dự án này?

Trong BurgerPrintsAgent, Harness đang được dùng để kiểm soát tính năng **tạo đơn hàng thật**.

Tên công tắc hiện tại là:

```text
enable_order_creation
```

Ý nghĩa:

- Nếu công tắc `enable_order_creation` được bật: chatbot được phép tạo đơn hàng fulfillment.
- Nếu công tắc này bị tắt: chatbot không tạo đơn, và sẽ báo rằng tính năng tạo đơn đang bị admin tắt.

Điều này rất quan trọng vì tạo đơn hàng là hành động có rủi ro cao hơn việc chỉ tìm kiếm hay tư vấn sản phẩm.

## Vì sao cần Harness cho tính năng tạo đơn?

Tạo đơn hàng có thể ảnh hưởng đến tiền, khách hàng, địa chỉ giao hàng, tồn kho và quy trình fulfillment.

Vì vậy team không nên để tính năng này luôn bật trong mọi tình huống.

Harness giúp team:

- Bật tính năng tạo đơn khi demo hoặc test.
- Tắt ngay lập tức nếu có lỗi.
- Không cần sửa code khi muốn bật/tắt.
- Không cần build lại app.
- Không cần restart toàn bộ hệ thống trong nhiều trường hợp.
- Giảm rủi ro tạo đơn nhầm.

## Cách nó vận hành trong app

Luồng đơn giản như sau:

1. Người dùng chat với BurgerPrintsAgent.
2. Nếu người dùng yêu cầu tạo đơn hàng, AI sẽ gọi chức năng `create_order`.
3. Trước khi tạo đơn thật, backend hỏi Harness:

```text
Công tắc enable_order_creation đang bật hay tắt?
```

4. Harness trả lời:

```text
Bật
```

hoặc:

```text
Tắt
```

5. Backend quyết định:

- Nếu bật: tiếp tục gọi BurgerPrints API để tạo đơn.
- Nếu tắt: không tạo đơn, chỉ trả thông báo cho người dùng.

## Ví dụ dễ hiểu

Giả sử người dùng nói:

```text
Tạo cho tôi đơn 2 áo ship đến New York
```

Backend sẽ không tạo đơn ngay lập tức.

Trước tiên backend kiểm tra Harness.

Nếu Harness đang tắt `enable_order_creation`, chatbot sẽ trả lời kiểu:

```text
Tính năng tạo đơn hiện đang bị tắt bởi Admin.
```

Nếu Harness đang bật `enable_order_creation`, chatbot mới được phép đi tiếp tới bước tạo đơn.

## Trạng thái hiện tại

Backend đã có tích hợp Harness Feature Flags.

Ứng dụng đọc SDK key từ biến môi trường:

```text
HARNESS_FF_SDK_KEY
```

Ứng dụng đang kiểm tra flag:

```text
enable_order_creation
```

Lưu ý: flag này cần được tạo đúng tên trong Harness dashboard. Nếu chưa tạo, backend sẽ hiểu là flag đang tắt và không cho tạo đơn.

## Harness khác gì so với sửa code?

Nếu không dùng Harness:

- Muốn tắt tạo đơn phải sửa code.
- Sau đó phải build lại.
- Sau đó phải deploy lại.
- Có thể mất thời gian và dễ ảnh hưởng demo.

Nếu dùng Harness:

- Admin chỉ cần bật/tắt flag trên Harness.
- App tự đọc trạng thái mới.
- Kiểm soát nhanh và an toàn hơn.

## Vai trò của Harness trong demo hackathon

Harness giúp demo trông thực tế hơn vì hệ thống có cơ chế kiểm soát tính năng giống sản phẩm thật.

Trong demo, team có thể nói:

```text
Chúng tôi không hard-code việc tạo đơn. Tính năng này được kiểm soát bằng Harness Feature Flags, nên admin có thể bật/tắt live để đảm bảo an toàn.
```

Đây là điểm cộng vì nó cho thấy dự án không chỉ là chatbot trả lời, mà còn nghĩ đến vận hành, kiểm soát rủi ro và triển khai thực tế.

## Nên thêm những flag nào?

Ngoài `enable_order_creation`, dự án có thể thêm một số công tắc khác:

```text
enable_demo_mode
```

Bật chế độ demo. Nếu Gemini hoặc API thật bị lỗi, app có thể trả phản hồi demo thân thiện thay vì hiện lỗi kỹ thuật.

```text
use_mock_catalog
```

Cho phép dùng dữ liệu mẫu khi BurgerPrints API chưa sẵn sàng hoặc trả lỗi.

```text
enable_realtime_pricing
```

Bật/tắt việc gọi giá realtime. Nếu API chậm, có thể tắt để demo mượt hơn.

```text
require_order_confirmation
```

Bắt người dùng xác nhận lần cuối trước khi tạo đơn thật.

## Tóm tắt một câu

Trong dự án này, Harness đóng vai trò như một bảng điều khiển từ xa, giúp admin bật/tắt các tính năng quan trọng như tạo đơn hàng mà không cần sửa code hoặc deploy lại ứng dụng.
