# ON.E Agent Gateway — Test Data Fix List (v2)

Nguồn: Module 3 Test Harness run lần 2 (2026-09-13, 05:21), đối chiếu với Round 1 Proposal v3 và FPT Problem Statement.

**Đã fix từ v1:** price filter, `reasoning` trong response, 3 negative cases, `token_remaining` / `token_expires_at`, low-confidence flag, category đã dịch sang tiếng Anh.

**Vấn đề mới phát sinh:** chủ yếu nằm ở tầng ranking, và có 1 test đang pass giả.

---

## P0 — Sửa trước

### 1. N3 là pass giả, không chứng minh được price floor

**Hiện tại:**
```json
{
    "eligible": false,
    "rule_id": null,
    "price_floor": null,
    "message": "No bundle discount available for this combination."
}
```
Output tự ghi: *"No matching rule, so price floor doesn't apply"* — nhưng vẫn đánh `✅ PASS`.

**Vấn đề:** test tên là "Price Floor Blocks Discount" mà kết quả thực tế là "không tìm thấy rule". Đây tệ hơn việc không có test: judge hỏi một câu là sập, và làm nghi ngờ luôn độ tin cậy của N1/N2.

**Cần làm:** dựng case có rule khớp thật, discount tính ra rơi xuống dưới floor, và bị cap lại. Output phải hiện rõ:
```
discount capped: 10% → 6.2% by price floor ($797.30)
```
Nếu không kịp: đổi tên test thành "No matching bundle rule" và bỏ nhãn price floor, đừng để tên test không khớp nội dung.

---

### 2. Phụ kiện xếp trên màn hình

**Hiện tại:** query xin monitor, nhưng thứ hạng là:
- #2 ACC-DOCK-01 (dock)
- #3 ACC-CABLE-01 (cable)
- #4 ACC-CHARGER-01 (charger)
- #5 MON-27-NANO-26 (đúng là màn 27" 4K)

**Vấn đề:** bonus tương thích đang lấn át mọi tín hiệu khác. Agent trả về cable ở top 3 cho câu hỏi về màn hình là mất điểm nặng ở tiêu chí số 1 (Intention Accuracy & Semantic Matching).

**Cần làm:** suy ra product type từ query → lọc theo type trước → chỉ xếp hạng trong nhóm đó. Phụ kiện chỉ xuất hiện ở bước bundle (Step 5), không nằm trong search result chính.

---

### 3. `"Name matches: pro"` làm lộ keyword matching

**Hiện tại:** ACC-DOCK-01 được giải thích là `"Name matches: pro"`. Chữ "Pro" này đến từ "MacBook **Pro** 14" trong query.

**Vấn đề:** cả proposal bán luận điểm semantic matching, nhưng reasoning string đang tự tố cáo engine chạy substring match. Judge đọc là thấy ngay.

**Cần làm:** bỏ token-level name match ra khỏi scoring, hoặc tối thiểu là không in ra trong `reasoning`. Chỉ giữ các tín hiệu có ý nghĩa: spec match, use case match, constraint satisfaction.

---

### 4. Xếp hạng mâu thuẫn với chính reasoning

**Hiện tại:**
- #1 MON-27-4K-01: `Specs match: screen size=27 inch` — score 0.3638
- #5 MON-27-NANO-26: `Specs match: screen size=27 inch; resolution=3840x2160 4K` — score 0.2326

**Vấn đề:** #5 khớp nhiều spec hơn #1 nhưng điểm thấp hơn. Hai dòng reasoning nằm cạnh nhau trong cùng một response, judge đối chiếu là thấy.

**Cần làm:** kiểm tra lại trọng số. Nhiều khả năng compatibility bonus đang quá lớn (xem mục 2). Có thể tự hết sau khi fix mục 8.

---

### 5. `constraints_applied` khai không đúng

**Hiện tại:**
```json
"constraints_applied": ["price ≤ $1000.0 AUD", "compatible with LAP-MBP-14"]
```
Nhưng MON-27-NANO-26 vẫn nằm trong kết quả dù reasoning của nó không có dòng "Compatible with LAP-MBP-14".

**Vấn đề:** nếu compatibility là hard constraint thì NANO-26 phải bị loại. Nếu là soft boost thì không được gọi là constraint.

**Cần làm:** chọn một trong hai:
- Hard: loại hẳn sản phẩm không tương thích khỏi kết quả.
- Soft: đổi tên field thành `signals_used` hoặc tách thành `hard_constraints` / `soft_signals`.

---

## P1 — Vấn đề dữ liệu

### 6. `use_cases` không khớp ngữ cảnh nhưng vẫn bị dùng làm bằng chứng

**Hiện tại:** query "for design work", sản phẩm 27" 4K IPS, nhưng:
```json
"use_cases": ["general_purpose", "office_work"],
"skill_level": "beginner"
```
Rồi reasoning lại trích chính hai giá trị đó ra: `"Use case: general_purpose, office_work"`.

**Vấn đề:** đang lấy thuộc tính không khớp để chứng minh là khớp. Nếu judge hỏi "design work liên quan gì tới office_work" thì không trả lời được.

**Cần làm:** sửa cho đúng sản phẩm:
```json
"use_cases": ["photo_editing", "video_editing", "cad", "design_work"],
"skill_level": "professional",
"environment": "desk_setup"
```
Và chỉ in use case vào reasoning khi nó thực sự khớp với intent đã decode.

---

### 7. Provenance vẫn rỗng

**Hiện tại:**
```json
"color_gamut": {
    "value": "~95% DCI-P3",
    "confidence": "low",
    "source_span": null,
    "inferred_from": null
}
```

**Vấn đề:** anti-hallucination layer (Section 5.1) bán bằng khả năng truy vết nguồn. Có flag `low` nhưng không có nguồn nghĩa là cơ chế truy vết chưa tồn tại, chỉ mới có cái nhãn.

**Cần làm:** điền thật, ví dụ:
```json
"inferred_from": "marketing copy: 'màu sắc sống động, chuẩn màu chuyên nghiệp'",
"source_span": "product_description:char_142-178"
```
Và thêm ít nhất 1 field `confidence: high` có `source_span` trỏ về datasheet, để thấy sự tương phản giữa traced và inferred.

---

### 8. `description` dùng để embed vẫn là tiếng Việt

**Hiện tại:**
```
"description": "ProVision UltraView 27\" 4K (ProVision) - Màn hình Thông số: Kích thước: 27 inch. Tấm nền: IPS. Độ phân giải: 3840x2160."
```

**Vấn đề:** category đã dịch sang "Monitor" nhưng chuỗi đi vào vector vẫn tiếng Việt. Query tiếng Anh + vector tiếng Việt nhiều khả năng là lý do điểm rớt từ 0.60 (v1) xuống 0.36 (v2), và là lý do hệ thống phải bù bằng keyword match ở mục 3.

**Cần làm:** dịch toàn bộ chuỗi embed sang tiếng Anh. Giữ price/stock ở ngoài (đã fix ở v1, giữ nguyên).

---

## P2 — Nhỏ, sửa nhanh

### 9. Step 5 đang dò rule trên sân khấu
```
→ No rule for ACC-ADAPTER-01, trying next...
```
Nhìn như đang mò. Làm deterministic (chọn sẵn cặp có rule), hoặc thêm rule cho ACC-ADAPTER-01 để khớp với kịch bản trong proposal Section 5.4.

### 10. Token hạn quá dài
`"token_expires_at": "2027-12-31T23:59:59Z"` — 15 tháng thì không còn là "limited authorization token" như proposal mô tả. Đổi về vài giờ hoặc 24h.

---

## Thứ tự làm

1. **N3** (mục 1) — pass giả là rủi ro lớn nhất, sửa trước tiên.
2. **Ranking + bỏ "Name matches: pro"** (mục 2, 3).
3. **Dịch description sang tiếng Anh** (mục 8) — có thể tự fix luôn mục 4.
4. **use_cases** (mục 6).
5. Mục 5, 7, 9, 10 — mỗi cái vài phút.

Cái nào không kịp thì ghi vào technical documentation dưới dạng known limitation kèm hướng xử lý. Judge đánh giá cao team tự biết điểm yếu hơn là team giấu.
