# ON.E Agent Gateway — Test Data Fix List

Nguồn: Module 3 Test Harness run (2026-09-13), đối chiếu với Round 1 Proposal v3 và FPT Problem Statement.

---

## P0 — Sửa trước, ăn trực tiếp vào tiêu chí chấm

### 1. Ràng buộc giá không được áp dụng
**Hiện tại:** query `'27 inch 4K IPS monitor for design work under 1000 AUD'` trả 63 kết quả, response không có field `price`, không thấy dấu hiệu filter theo ngân sách.

**Vấn đề:** tiêu chí số 1 của FPT là Intention Accuracy & Semantic Matching. Query multi-constraint mà chỉ xử lý được "monitor" là hụt đúng phần chấm nặng nhất.

**Cần làm:** parse constraint giá từ query, áp filter, và trả `price` trong mỗi search result để chứng minh filter đã chạy.

---

### 2. `use_cases`, `skill_level`, `environment` đều rỗng
**Hiện tại:**
```json
"use_cases": [],
"skill_level": "",
"environment": ""
```

**Vấn đề:** đây chính là phần "map product features to human outcomes" mà proposal dùng để khác biệt với schema.org thuần. Để rỗng là tự phá luận điểm ngay trong demo.

**Cần làm:** fill đầy đủ cho toàn bộ SKU nằm trên demo path (khoảng 5–10 SKU). Ví dụ: `use_cases: ["photo editing", "video editing", "CAD"]`, `skill_level: "professional"`, `environment: "desk setup"`.

---

### 3. Confidence toàn bộ là `high`
**Hiện tại:** cả 3 spec của MON-27-4K-01 đều `confidence: high`.

**Vấn đề:** anti-hallucination verification layer là selling point trong Section 5.1, nhưng không field nào bị flag thì không chứng minh được cơ chế có tồn tại.

**Cần làm:** cố ý tạo ít nhất 1 SKU có spec suy luận từ marketing text (ví dụ "màu sắc sống động" → `color_gamut: "~95% DCI-P3"`) và flag `confidence: low`, kèm field `source` chỉ ra không trace được về dữ liệu gốc.

---

### 4. Điểm similarity bị trùng chính xác
**Hiện tại:** 0.6045 (2 SKU), 0.5136 (3 SKU).

**Vấn đề:** trùng tới 4 chữ số thập phân không phải ngẫu nhiên. Nhiều khả năng embedding đang bắt chủ yếu vào `category` chứ không vào spec. Đây là bug, không phải đặc điểm.

**Cần làm:** kiểm tra lại text đầu vào của embedding. Nếu không kịp fix, ghi rõ vào technical documentation như known limitation kèm hướng xử lý.

---

### 5. Lẫn lộn ngôn ngữ
**Hiện tại:** query tiếng Anh, catalog tiếng Việt (`"Màn hình Viền mỏng"`, `"Còn hàng"`, tên rule bundle).

**Vấn đề:** hai mặt. (a) làm mờ embedding cross-lingual, có thể là nguyên nhân của mục 4. (b) thiếu chỉn chu với FPT Australasia, là đơn vị nói tiếng Anh.

**Cần làm:** chuẩn hóa toàn bộ demo path sang tiếng Anh: category, description, tên rule, trạng thái tồn kho.

---

## P1 — Vấn đề logic

### 6. Giá nằm trong text được embed
**Hiện tại:** `"description": "... Giá: 899 AUD. Còn hàng."`

**Vấn đề:** giá đi vào vector là dữ liệu chết, mâu thuẫn với chính proposal (giá phải qua real-time endpoint). Giá đổi thì vector sai.

**Cần làm:** bỏ price và stock khỏi chuỗi dùng để embed. Giữ nguyên ở `/availability`.

---

### 7. Price floor không bao giờ chạm
**Hiện tại:** floor 100 AUD trên đơn 934 AUD.

**Vấn đề:** cơ chế bảo vệ margin mà không bao giờ kích hoạt thì chưa chứng minh được gì.

**Cần làm:** thêm 1 test case mà floor thực sự chặn discount, in ra log kiểu "discount capped by price floor".

---

### 8. Token không được validate
**Hiện tại:** khai báo `tok_limited_2000aud` ở đầu, checkout response không có remaining limit hay expiry.

**Vấn đề:** agent security & governance là phần được nhấn mạnh trong Section 5.3, và Round 2 chấm 25 điểm technical quality có mục bảo mật và quyền riêng tư dữ liệu.

**Cần làm:** thêm vào checkout response `token_remaining`, `token_expires_at`; validate limit trước khi confirm order.

---

### 9. Không có negative case nào
**Hiện tại:** 6/6 bước đều happy path.

**Cần làm:** thêm ít nhất 3 case bị từ chối:
- API key sai → 401
- Đơn vượt hạn mức token → từ chối kèm lý do
- Rate limit vượt ngưỡng → 429
- (nếu kịp) SKU hết hàng

Cho judge thấy request bị chặn có giá trị hơn 10 happy path.

---

### 10. Thiếu justification
**Hiện tại:** search result chỉ có `score`, không có lý do chọn.

**Vấn đề:** brief FPT nói rõ mong muốn "not just a list of SKUs, but a logical justification of why these products match the buyer's specific intention".

**Cần làm:** thêm field `reasoning` vào mỗi search result và product detail, sinh từ constraint đã decode. Ví dụ: "Matches 4K + IPS + 27 inch; 899 AUD nằm trong ngân sách 1000 AUD; hỗ trợ 6 phụ kiện tương thích."

---

### 11. Kịch bản demo lệch với proposal
**Hiện tại:** proposal Section 5.4 bước 1 là "tìm màn hình tương thích với laptop hiện tại", nhưng query test không nhắc laptop nào, nên `compatible_with` chỉ là list chết.

**Cần làm:** đổi query thành dạng có thiết bị cụ thể, ví dụ `"27 inch 4K monitor compatible with my MacBook Pro 14, under 1000 AUD"`, và dùng `compatible_with` làm điều kiện lọc thật.

---

## Thứ tự làm nếu chỉ còn vài tiếng

1. Price filter (mục 1)
2. Fill `use_cases` cho demo SKU (mục 2)
3. Thêm 1 low-confidence field (mục 3)
4. Thêm `reasoning` vào response (mục 10)
5. Thêm 1 negative case (mục 9)

Năm mục này ăn trực tiếp vào Intention Accuracy, Technical Architecture và Business Value. Các mục còn lại đưa vào technical documentation dưới dạng known limitations nếu không kịp.
