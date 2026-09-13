# 🧑‍⚖️ Hướng Dẫn Test Cho Ban Giám Khảo (BGK)

> ON.E Agent Gateway — UAVS Hackathon 2026

---

## Yêu cầu hệ thống

- **Python 3.10+** (kiểm tra: `python --version`)
- **Node.js 18+** (kiểm tra: `node --version`) — chỉ cần cho Module 2 Dashboard
- Không cần API key, không cần Docker, không cần database

---

## ⚡ Test nhanh nhất (2 phút) — Module 3 API Gateway

### Bước 1: Cài đặt

```bash
cd module3
python -m pip install -r requirements.txt
```

### Bước 2: Khởi động server

```bash
python -m uvicorn app.main:app --port 8000
```

> Server sẽ chạy tại http://localhost:8000
> Swagger UI tại http://localhost:8000/docs

### Bước 3: Chạy demo 6 bước (mở terminal mới)

```bash
cd module3
python sample_agent.py
```

**Kết quả mong đợi:**

```
STEP 1: Search — '27 inch 4K monitor compatible with my MacBook Pro 14, under 1000 AUD for design work'
  → Total: 7 results, top: ProVision UltraView 27" 4K ($899 AUD)
  → Constraints parsed: price ≤ $1000 AUD, compatible_with: LAP-MBP-14, product_type: monitor
  → Reasoning: Specs (screen size=27 inch, resolution=3840x2160 (4K)), use case (design_work), budget

STEP 2: Product Detail — MON-27-4K-01
  → Specs with confidence + anti-hallucination provenance (source_span, inferred_from)

STEP 3: Availability — $899 AUD, 45 units

STEP 4: Policy — Warranty (12 months), returns (14 days), shipping ($0)

STEP 5: Bundle Offer — 10% off with ACC-ADAPTER-01 ($840.60 AUD)
  → Price floor enforced ✓

STEP 6: Checkout — $840.60 AUD, order confirmed
  → Session ID & audit trail generated ✓

============================================================
NEGATIVE CASE RESULTS:
  N1 — Auth failure (401)     : ✅ PASS
  N2 — Token over-limit (402) : ✅ PASS
  N3 — Price floor block      : ✅ PASS (Final price: $968.00 AUD)
============================================================
SCENARIO COMPLETE ✓
```

---

## 🔍 Test chi tiết từng endpoint (qua Swagger UI)

Mở **http://localhost:8000/docs** trên browser khi server đang chạy.

### API Key dành cho BGK

```
X-Agent-Key: agt-key-hackathon-judge
```

> ⚠️ Mỗi request cần header `X-Agent-Key`. Trong Swagger UI, click **Authorize** (🔒) ở góc phải trên, nhập key trên.

### Test 1: Semantic Search (POST /search)

```json
{
  "query": "4K monitor for graphic design under 1000 AUD"
}
```

**Kiểm tra:**
- ✅ Trả về danh sách sản phẩm được xếp hạng theo score
- ✅ Có category tiếng Việt (Màn hình, Màn hình Đồ họa...)
- ✅ Score > 0 cho các sản phẩm liên quan

**Thử thêm:**
```json
{"query": "gaming monitor 144Hz high refresh rate"}
{"query": "ultrawide curved monitor for video editing"}
{"query": "cheap office monitor"}
```

### Test 2: Product Detail (GET /products/{sku})

Dùng SKU từ kết quả search, ví dụ: `MON-27-4K-01`

**Kiểm tra:**
- ✅ Specs có **confidence flag** (high/medium/low)
- ✅ Có `compatible_with` liệt kê SKU tương thích
- ✅ Có `warranty` với duration_months, coverage, exclusions
- ✅ Có `description` (agent_text tiếng Việt từ Module 1)

### Test 3: Availability (GET /products/{sku}/availability)

**Kiểm tra:**
- ✅ Giá bằng **AUD** (không phải USD)
- ✅ Có `stock` > 0
- ✅ Có `updated_at` timestamp

### Test 4: Policy (GET /products/{sku}/policy)

**Kiểm tra:**
- ✅ Warranty duration, coverage
- ✅ Returns window (30 hoặc 14 ngày)
- ✅ Shipping cost và ETA

### Test 5: Bundle Offer (POST /bundle-offer)

```json
{
  "skus": ["MON-27-4K-01", "ACC-DOCK-01"]
}
```

**Kiểm tra:**
- ✅ `eligible: true` — bundle được áp dụng
- ✅ `discount_percent: 10` — 10% giảm giá
- ✅ `price_floor` — giá sàn được hiển thị
- ✅ `discounted_total < original_total`
- ✅ `discounted_total >= price_floor` — **giá sàn KHÔNG bao giờ bị phá**

**Thử phá giá sàn:**
```json
{"skus": ["MON-27-4K-01", "ACC-STAND-01"]}
```

### Test 6: Checkout (POST /checkout)

```json
{
  "agent_id": "agt_judge",
  "items": [
    {"sku": "MON-27-4K-01", "qty": 1},
    {"sku": "ACC-DOCK-01", "qty": 1}
  ],
  "auth_token": "tok_judge_5000aud"
}
```

**Kiểm tra:**
- ✅ `status: "confirmed"`
- ✅ `currency: "AUD"`
- ✅ `bundle_discount_applied` > 0 (nếu mua combo)
- ✅ `audit_ref` — mã audit trail
- ✅ `session_id` — mã đơn hàng

**Thử token hết hạn/quá limit:**
```json
{
  "agent_id": "agt_demo_1",
  "items": [{"sku": "MON-27-4K-01", "qty": 1}],
  "auth_token": "tok_limited_50usd"
}
```
→ Mong đợi: **HTTP 402** (giá $899 AUD vượt limit $50)

### Test 7: Anti-abuse Detection (DP-04)

Gửi POST `/bundle-offer` liên tục > 10 lần trong 5 phút:
→ Mong đợi: **HTTP 429** — "Suspected price probing"

### Test 8: Auth & Rate Limiting

- Gửi request **không có** `X-Agent-Key` → mong đợi **HTTP 401**
- Gửi request với key sai → mong đợi **HTTP 401**
- Gửi > 120 request/phút với key BGK → mong đợi **HTTP 429**

---

## 📊 Test Module 2 — AEO Dashboard

### Khởi động backend

```bash
cd module2/backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --port 8001
```

### Khởi động frontend

```bash
cd module2/frontend
npm install
npm run dev
```

> Dashboard mở tại **http://localhost:5173**

### Kiểm tra trên Dashboard

1. **Product List** — Danh sách 63 sản phẩm với AEO score (green/yellow/red)
2. **Product Detail** — Click vào sản phẩm → xem 5-axis breakdown + đề xuất cải thiện
3. **Query Simulator** — Nhập "4K monitor for design" → xem agent chọn sản phẩm nào và tại sao
4. **Before/After** — Nhập query → so sánh keyword match (trước) vs semantic match (sau standardization)

### Test Before/After qua API (nếu frontend không chạy)

```bash
curl -X POST http://localhost:8001/compare-before-after \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo" \
  -d '{"question": "4K monitor for graphic design"}'
```

**Kiểm tra:**
- ✅ `before_matches` < `after_matches` (enriched data tìm được nhiều hơn)
- ✅ `new_matches_from_enrichment` > 0
- ✅ After results có `aeo_score` và `tier`

---

## 🔗 Test tích hợp Module 1 → Module 3

Kiểm tra data flow giữa 2 module:

```bash
# Từ thư mục gốc
python generate_module3_data.py
```

**Kiểm tra:**
- ✅ Output: "63 products", "63 availability", "20 rules"
- ✅ `module3/data/catalog.json` chứa sản phẩm từ Module 1 (monitor/display)
- ✅ SKU format: `MON-27-4K-01`, `ACC-DOCK-01`... (không phải `SKU001`)

---

## 📋 Checklist BGK (theo rubric vòng 2)

| Tiêu chí | Điểm | Cách verify |
|----------|------|-------------|
| **Demo chạy live** | ✓/✗ | `python sample_agent.py` exit code 0 |
| **README đủ** | 10 | Xem root README.md: kiến trúc ✓, tech stack ✓, one-command ✓ |
| **One-command setup** | ✓/✗ | Follow Quick Start trong README |
| **Kiến trúc rõ** | 25 | Sơ đồ ASCII trong README, data flow giữa 3 module |
| **Code sạch, tái lập được** | 25 | Clone repo → chạy 3 lệnh → demo hoạt động |
| **Bảo mật** | 25 | Không secret trong repo, `.env.example` có, auth + rate limit hoạt động |
| **Chi phí có số** | 20 | Xem phần "Infrastructure Cost Estimate" trong README |
| **Australian Privacy Act** | 20 | Xem phần "Security & Privacy" trong README |

---

## ❓ Câu hỏi Q&A gợi ý (theo §11)

1. "Vì sao không tự làm chuẩn riêng thay vì dùng schema.org?"
2. "Chi phí ở quy mô 100k SKU là bao nhiêu?"
3. "Khi LLM đọc sai spec thì xử lý thế nào?"
4. "Vì sao merchant chịu trả tiền cho hệ thống này?"

→ Team nên chuẩn bị trả lời trong vòng 2 phút mỗi câu.
