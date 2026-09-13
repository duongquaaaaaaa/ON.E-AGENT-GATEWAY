# ON.E Agent Gateway — Fix List: 1 GIỜ CUỐI

Nguyên tắc: **sửa data, đừng sửa thuật toán.** Không đụng vào scoring logic. Sửa xong mỗi mục chạy lại `python sample_agent.py` để chắc chắn không vỡ demo.

---

## ⏱️ 0–25 phút — MỤC 1: Enrich compatibility (quan trọng nhất)

**Vấn đề:** search chỉ trả về `"total": 1`. Một kết quả duy nhất thì engine nhìn không khác gì câu SQL filter. Mất chính phần FPT chấm nặng nhất (Intention Accuracy & Semantic Matching). Judge cũng sẽ hỏi: catalog 40+ màn hình mà chỉ 1 cái cắm được MacBook Pro 14?

**Cách sửa:** thêm `"LAP-MBP-14"` vào `compatible_with` của 6–8 monitor sẵn có trong catalog (mọi màn USB-C / Thunderbolt đều cắm được MacBook). Chỉ sửa file data, không đụng code.

**Ứng viên có sẵn:**
- `MON-27-NANO-26` — ProVision NanoEdge 27" 4K, $949
- `MON-32-QHD-09` — TechView Creator 32" QHD
- `MON-27-QHD-18` — ProVision FlexArm 27" QHD
- `MON-27-FHD-21` — TechView WebCam 27" FHD
- (thêm 2–4 SKU monitor khác nếu có)

**Mục tiêu:** top 5 có 4–5 monitor, thứ hạng phân biệt được bằng spec và use case.

**Kiểm tra:** `"total"` ≥ 4, và kết quả trả về toàn monitor, không lẫn accessory.

---

## ⏱️ 25–35 phút — MỤC 2: Map 4K ↔ 3840x2160

**Vấn đề:** reasoning của MON-27-4K-01 chỉ ghi `Specs: screen size=27 inch`. Query hỏi "4K", sản phẩm có `resolution: 3840x2160`, nhưng không được tính điểm. Đúng cái spec người dùng hỏi thì lại bỏ sót.

**Cách sửa:** thêm alias vào spec matcher:
```python
SPEC_ALIASES = {
    "4k": ["3840x2160", "3840 x 2160", "uhd"],
    "qhd": ["2560x1440", "1440p"],
    "fhd": ["1920x1080", "1080p"],
}
```

**Kiểm tra:** reasoning phải hiện `Specs: screen size=27 inch; resolution=3840x2160 (4K)`.

---

## ⏱️ 35–45 phút — MỤC 3: Thêm `final_total` vào N3

**Vấn đề:** response N3 có `"discounted_total": null`, message nói "Returning list price", nhưng không field nào mang giá đó. Agent đọc xong không biết phải trả bao nhiêu. Đây là lỗi hợp đồng API, không phải lỗi trình bày.

**Cách sửa:** thêm 1 field vào bundle offer response:
```json
"final_total": 968.0
```

**Kiểm tra:** in ra dòng `→ Final price to agent: $968.00 AUD` ở cuối N3.

---

## ⏱️ 45–50 phút — MỤC 4: Lỗi chính tả

**Vấn đề:** output in ra `"percenntage"`. Rulebook chấm mục 5 (Documentation & presentation quality) có tiêu chí "free of spelling errors".

**Cách sửa:** tìm và sửa `percenntage` → `percentage`. Tiện thể grep qua toàn bộ string in ra màn hình.

---

## ⏱️ 50–55 phút — MỤC 5: Bỏ tiếng Việt trong `source_span`

**Vấn đề:**
```json
"source_span": "product_description:char_142-178 'màu sắc sống động, chuẩn màu chuyên nghiệp'"
```
Description đã dịch sang tiếng Anh, nên đoạn trích này trỏ về text không còn tồn tại trong dữ liệu.

**Cách sửa:**
```json
"source_span": "product_description:char_142-178 'vivid colours, professional-grade accuracy'",
"inferred_from": "marketing copy — no DCI-P3 percentage found in datasheet"
```

---

## ⏱️ 55–60 phút — Chạy lại full harness + ghi known limitations

Chạy lại toàn bộ, xác nhận 6 bước + 3 negative case vẫn pass.

Thêm mục này vào README (technical documentation):

```markdown
## Known Limitations

1. **Similarity score chưa normalize.** Score hiện là raw cosine
   (khoảng 0.2–0.4), chưa scale về thang dễ đọc. Hướng xử lý:
   min-max normalize theo result set trước khi trả về agent.

2. **Provenance chưa đầy đủ ở field high-confidence.** Cơ chế
   truy vết mới implement đầy đủ cho nhánh low-confidence
   (trỏ về char span trong marketing copy). Field high-confidence
   hiện echo lại value; bản sau sẽ trỏ về datasheet row ID.

3. **Price floor hiện từ chối toàn bộ discount** thay vì cap
   xuống đúng mức floor. Hành vi mong muốn theo thiết kế là cap
   (chào $919.60 thay vì trả về list price $968.00).
```

Ba mục này nếu sửa thì phải đụng scoring và schema, rủi ro vỡ demo cao hơn giá trị thu được. Viết vào known limitations ăn điểm ở Round 2 (technical quality) và giúp chủ động khi judge hỏi ở Round 3 (Q&A, 25 điểm).

---

## Nếu chỉ còn 20 phút

Làm **mục 1** thôi. Các mục còn lại đưa hết vào known limitations.

Mục 1 là thứ duy nhất ảnh hưởng trực tiếp tới phần chấm nặng nhất, và là thứ duy nhất judge chắc chắn nhìn thấy khi xem demo.

---

## KHÔNG làm trong 1 giờ này

- ❌ Sửa scoring algorithm
- ❌ Normalize score
- ❌ Refactor schema provenance
- ❌ Đổi hành vi price floor từ reject sang cap
- ❌ Thêm SKU mới vào catalog

Tất cả đều có rủi ro vỡ demo. Ghi vào known limitations.
