# UAVS HACKATHON 2026 — ROUND 2 SUBMISSION
## Product: ON.E Agent Gateway
**FPT Australasia Challenge — Business-to-Agent (B2A) Readiness Layer**

- **Repository:** [https://github.com/duongquaaaaaaa/ON.E-AGENT-GATEWAY](https://github.com/duongquaaaaaaa/ON.E-AGENT-GATEWAY) (Branch: `main`)
- **Product Name:** ON.E Agent Gateway
- **Submission Date:** 13/09/2026

---

## 📦 4 BẢNG SẢN PHẨM BÀN GIAO (DELIVERABLES)

### 1. Demo Sản Phẩm / Giải Pháp AI (Runnable MVP)
- **Module 1 (Semantic Transformation Engine):** Chuẩn hóa 63 SKU thô ("bẩn") với trích xuất thông số kỹ thuật qua Gemini, kiểm tra chống ảo giác (traced provenance), và đánh chỉ mục vector đa ngữ (BGE-M3).
- **Module 2 (AEO Scoring & Merchant Dashboard):** Web app React + Vite hiển thị điểm AEO 5 trục (Completeness, Machine-Readability, Retrievability, Answerability, Transactability) kèm Agent Query Simulator và màn hình Before/After.
- **Module 3 (B2A API Gateway & Dynamic Policy Engine):** REST API FastAPI + MCP Server (Model Context Protocol) cho AI Shopping Agent, hỗ trợ tìm kiếm ngữ nghĩa đa ràng buộc, xác thực API key, kiểm soát hạn mức chi tiêu (token spend limit), bundle pricing 100% tất định với chặn trần giá sàn (hard price floor protection), và audit trail log.
- **Test Harness tự động:** `python module3/sample_agent.py` chạy toàn bộ kịch bản mua hàng 6 bước tự động + 3 negative test cases (401 Auth, 402 Token Limit, N3 Price Floor Block).

### 2. Technical Documentation
- **Tài liệu chính:** [`README.md`](./README.md) đầy đủ thông tin kiến trúc hệ thống, sơ đồ data flow, tech stack, quick-start một câu lệnh, bảng giá vận hành hạ tầng (Infrastructure Cost Estimate).
- **Hướng dẫn chấm thi độc quyền:** [`TESTING_GUIDE_BGK.md`](./TESTING_GUIDE_BGK.md) dành riêng cho Ban Giám Khảo test nhanh trong 2 phút qua console hoặc Swagger UI (`http://localhost:8000/docs`).

### 3. Source Code & GitHub Repository
- **URL:** `https://github.com/duongquaaaaaaa/ON.E-AGENT-GATEWAY`
- **Branch:** `main`
- **Trạng thái:** Public, code sạch, có tài liệu và file cấu hình môi trường `.env.example`.

### 4. Pitch Deck (Round 3 Gala Night)
- Cấu trúc 10 slides bám sát Rubric chấm điểm:
  1. **Executive Summary:** Vấn đề bán hàng cho AI Agent (B2A) thay vì người tiêu dùng truyền thống (B2C).
  2. **Market Problem:** 90% website TMĐT hiện tại chặn hoặc gây ảo giác cho AI Shopping Agent do dữ liệu phi cấu trúc và thiếu cơ chế bảo vệ biên lợi nhuận.
  3. **Solution — ON.E Agent Gateway:** Lớp sẵn sàng B2A gồm 3 module: Chuẩn hóa Catalog -> Đo lường AEO -> Gateway giao dịch có bảo mật.
  4. **Proprietary Technology:** Dual-layer anti-hallucination verification (`source_span`, confidence flags), Closed taxonomy anti-greenwashing.
  5. **Deterministic Policy Engine:** Cơ chế chiết khấu bundle dựa trên luật tất định, bảo vệ giá sàn tuyệt đối, 0% rủi ro prompt injection giá.
  6. **Architecture & Standards:** Chuẩn MCP (Anthropic Model Context Protocol), REST OpenAPI 3.1, JSON-LD Schema.org.
  7. **Market Strategy & GTM:** Target các merchant điện máy & công nghệ trên sàn ON.E tại thị trường Úc/APAC.
  8. **Unit Economics & Cost:** Chi phí trích xuất ~$0.04/63 SKU, mở rộng 100K SKU chỉ ~$6.35, biên lợi nhuận SaaS > 80%.
  9. **Security, Governance & Compliance:** Token spend limit (HTTP 402), X-Agent-Key (HTTP 401), Audit logging, tuân thủ Australian Privacy Act 1988.
  10. **Roadmap & Team:** Lộ trình từ PoC đến tích hợp trực tiếp vào ON.E Core Platform.

---

## 🏆 ĐỐI CHIẾU THANG ĐIỂM CHẤM THI ROUND 2 (100 ĐIỂM)

### 1. Technical Quality (25 Điểm)
- **Sản phẩm chạy được 100%:** Server REST API (`localhost:8000`), Dashboard React (`localhost:5173`), và MCP tool server (`stdio`).
- **Reproducible & One-Command Setup:**
  ```bash
  cd module3 && pip install -r requirements.txt && python -m uvicorn app.main:app --port 8000
  python sample_agent.py
  ```
- **Kiến trúc rõ ràng, Code sạch:** Tách biệt rõ ràng 3 module: Ingestion/Vector Indexing (Module 1), Dashboard/AEO Engine (Module 2), Gateway/Policy/Security (Module 3).
- **Tích hợp AI/ML đúng chỗ:** Dùng LLM cho trích xuất thuộc tính khó từ văn bản marketing; dùng Embeddings BGE-M3 cho vector semantic search; **tuyệt đối không dùng LLM để tính tiền hay chốt giá** (100% deterministic rules).
- **Bảo mật & Privacy:** Header `X-Agent-Key`, token spend limit kiểm tra trước khi xác nhận đơn, log audit trail không lưu trữ thông tin nhạy cảm của khách hàng cá nhân (tuân thủ Privacy Act).

### 2. Market Strategy (25 Điểm)
- **Mô hình giá trị B2A (Business-to-Agent):** Chuyển dịch từ tối ưu cho con người (SEO) sang tối ưu cho AI Agent (AEO - Agent Engine Optimization). Giúp nhà bán hàng không bị "tàng hình" trước thế hệ AI Shopping Assistant (ChatGPT Search, Gemini, Claude Computer Use).
- **Lợi thế cạnh tranh:**
  - So với API TMĐT truyền thống: Có semantic enrichment, anti-hallucination provenance, và agent governance.
  - So với Custom LLM Chatbot: Không có rủi ro ảo giác giá, bảo vệ margin bằng code cứng (hard price floor), độ trễ thấp (< 50ms).
- **Go-To-Market (GTM):**
  - Giai đoạn 1: Triển khai như một plugin/app trên nền tảng ON.E cho nhóm merchant ngành Điện máy / IT hardware.
  - Giai đoạn 2: Mở rộng sang thời trang, gia dụng; cung cấp SDK cho các nền tảng AI Agent (OpenAI GPT Actions, Claude MCP).

### 3. User Experience (20 Điểm)
- **Hai đối tượng người dùng (Dual Persona):**
  - **Nhà bán hàng (Merchant):** Được phục vụ bởi Dashboard trực quan (Module 2), xem điểm AEO theo 5 trục, phát hiện sản phẩm thiếu dữ liệu và dùng Query Simulator để thấy trước AI Agent sẽ tìm thấy gì.
  - **AI Shopping Agent (Buyer Agent):** Được phục vụ bởi REST API chuẩn xác (Module 3) có schema tường minh, response giải thích lý do (`reasoning`), báo rõ nguồn dữ liệu (`source_span`, `confidence`), mã lỗi chuẩn HTTP (401, 402, 429).
- **Trải nghiệm nhất quán & mượt mà:** Giao diện tối ưu, phản hồi tức thì, Swagger docs đầy đủ ví dụ request/response.

### 4. Deployability & Scalability (20 Điểm)
- **Hạ tầng tinh gọn, chi phí tối thiểu:**
  - Chạy trên 1 vCPU Linux container ($10/tháng).
  - Không cần GPU cho inference thời gian thực (BGE-M3 pre-embedded hoặc vector engine nhẹ).
  - Trích xuất 63 SKU thô tốn chưa tới $0.04 tiền API Gemini 2.5 Flash.
- **Khả năng mở rộng (Scale to 100K+ SKUs):**
  - Kiến trúc microservices không trạng thái (stateless API).
  - Dữ liệu tách bạch giữa catalog tĩnh (vector index) và availability động (giá, tồn kho thời gian thực).
- **Pháp lý & An toàn dữ liệu:** Giảm thiểu thu thập PII (Data Minimization), bảo vệ quyền lợi người tiêu dùng theo quy định TMĐT của Úc.

### 5. Adaptation & Upgrade (10 Điểm)
- **Tiếp thu trọn vẹn đề bài từ FPT Australasia:** Giải quyết toàn diện từ chuẩn hóa dữ liệu, chấm điểm sẵn sàng, đến cổng API cho Agent giao dịch.
- **Tính năng nâng cấp độc đáo:**
  - **Anti-Hallucination Traceability:** Trỏ ngược giá trị thông số về đoạn trích xuất gốc (`source_span`).
  - **Deterministic Price Floor Protection:** Ngăn chặn Agent "ép giá" hay khai thác lỗ hổng bundle.
  - **MCP Integration:** Đi đầu đón đầu chuẩn giao tiếp AI mới nhất của ngành.
