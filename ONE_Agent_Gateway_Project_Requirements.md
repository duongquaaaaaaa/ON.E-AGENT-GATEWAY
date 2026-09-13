# ON.E Agent Gateway — Yêu cầu chi tiết dự án cần đạt được

> Tài liệu nội bộ. Tổng hợp từ: Hackathon Rulebook 2026, FPT Problem Statement (The B2A Shift), FPT Round 1 Challenge Brief, và bản proposal v3 EN.
> Mục đích: biến những gì proposal đã hứa thành tiêu chí nghiệm thu đo được (pass/fail), để biết chính xác lúc nào coi là "xong".

---

## 0. Cách đọc tài liệu

- **MUST** = không có thì coi như thất bại ở vòng tương ứng.
- **SHOULD** = ảnh hưởng trực tiếp tới điểm, nhưng có thể cắt nếu trễ tiến độ.
- **COULD** = điểm cộng, chỉ làm khi ba khối chính đã chạy.
- Mỗi yêu cầu có ID (SE / AEO / GW / DP / DATA / NFR) để tick trong checklist mục 11.
- Mọi tiêu chí nghiệm thu phải kiểm được bằng một lệnh chạy hoặc một thao tác quan sát. Nếu không kiểm được thì viết lại tiêu chí.

---

## 1. Mục tiêu tổng thể

**Luận điểm của dự án:** catalog của retailer hiện đang vô hình hoặc bị đọc sai bởi AI agent. Vấn đề nằm ở tầng dữ liệu và tầng giao tiếp, không nằm ở giao diện. Vì vậy giải pháp là một lớp add-on backend cắm vào ON.E, không phải dự án redesign website.

**North star:** một AI agent của người mua gửi truy vấn nhiều ràng buộc, hệ thống merchant trả về đúng sản phẩm kèm lý do có căn cứ, và chốt được đơn qua API. Song song đó, merchant nhìn thấy trên dashboard tại sao sản phẩm của mình được chọn hoặc bị loại.

Dự án chỉ được coi là đạt khi chứng minh được **cả ba mệnh đề** dưới đây bằng số liệu chạy thật, không phải bằng slide:

| # | Mệnh đề phải chứng minh | Bằng chứng bắt buộc |
|---|---|---|
| P1 | Catalog thô không đọc được bởi agent, sau khi qua pipeline thì đọc được | So sánh before/after trên cùng một bộ SKU, có số |
| P2 | Hệ thống hiểu đúng ý định phức tạp, không phải keyword match | Kết quả trên bộ query có đáp án chuẩn, có recall@k |
| P3 | Agent tự chốt được đơn end-to-end, không cần người can thiệp | Log audit của một transaction hoàn chỉnh |

---

## 2. Ràng buộc cứng (vi phạm là bị loại, không phải trừ điểm)

### 2.1 Vòng 1
- File PDF, **tối đa 07 trang**, font 11–12pt, lề tối thiểu 2cm. Phần Sources không tính vào giới hạn trang.
- **Viết bằng tiếng Anh.**
- Hạn 23:59 ngày 05/09/2026 AEST. Nộp muộn hoặc sai format là loại ngay.
- Đúng 01 proposal cho 01 case study. Nộp nhiều lần thì chỉ tính bản cuối trước deadline.
- Đủ thông tin team: họ tên đầy đủ, trường, email liên hệ, SĐT team leader. Thiếu là loại.
- Đủ 7 đầu mục nội dung bắt buộc: tên sản phẩm, thông tin team, đề đã chọn và lý do, problem framing, assumptions & open questions, giải pháp AI/ML, **sơ đồ kiến trúc hoặc wireframe**, roadmap, sources.

### 2.2 Vòng 2
- **Toàn bộ code phải viết trong giờ thi** (từ 09:00 ngày 12/09/2026). Dùng code viết trước là cấm tuyệt đối. Chuẩn bị trước chỉ được phép ở mức: thiết kế, wireframe, làm quen tool.
- Nộp trước 17:00 ngày 13/09/2026 AEST. Muộn là không nhận.
- Bắt buộc có: demo chạy được, README.md (kiến trúc + tech stack + hướng dẫn cài đặt/chạy), link repo public hoặc share cho BTC, pitch deck.
- Khai báo đầy đủ mọi dataset, API, thư viện bên ngoài trong tài liệu kỹ thuật.
- Có mặt trực tiếp tại venue. Dưới 03 thành viên có mặt lúc 10:00 là bị loại. Tham gia online không thay thế được thành viên vắng.
- Không được sửa nội dung sản phẩm sau 17:00 ngày 13/09.

### 2.3 Vòng 3
- Pitch deck chốt nộp trước 23:59 ngày 19/09/2026.
- Demo **phải là bản nộp ở vòng 2**. Đổi tính năng cốt lõi sau deadline vòng 2 là cấm.
- Pitch tối đa 10 phút, Q&A 5 phút. Toàn bộ thành viên phải có mặt.

### 2.4 Ranh giới phạm vi (rủi ro dễ chết nhất)
Đề bài ghi rõ **OUT OF SCOPE: xây dựng AI shopping assistant hướng người tiêu dùng**. Góc nhìn phải luôn là merchant-side.

- Con agent phía người mua trong demo **bắt buộc** phải được gọi và trình bày là *test harness / mock buyer agent* dùng để kiểm thử Gateway, không được trình bày như một sản phẩm của team.
- Trong deck, README và lời pitch: không có câu nào mô tả agent người mua như một feature.
- Dashboard dành cho merchant, không dành cho shopper. Nếu có màn hình nào giống trang mua sắm thì bỏ.

---

## 3. Phạm vi

**Trong phạm vi:** chuẩn hoá dữ liệu machine-readable, semantic search và intent decoding, dynamic bundling, giao thức thương lượng AI-to-AI, API checkout, chiến lược marketing B2A.

**Ngoài phạm vi:** consumer-facing shopping assistant, tối ưu UI/UX cho người, logistics chuỗi cung ứng vật lý, train model mới từ đầu, thanh toán thật (chỉ mô phỏng authorization token).

**Non-goal có chủ đích:** không tự định nghĩa chuẩn riêng. Kiến trúc phải standard-neutral, sẵn sàng gắn adapter cho ACP / UCP / x402.

---

## 4. Yêu cầu chức năng theo module

### 4.1 Semantic Catalog Transformation Engine (SE)

| ID | Yêu cầu | Mức | Tiêu chí nghiệm thu |
|---|---|---|---|
| SE-01 | Ingest và normalize catalog thô từ OrderCloud/PIM hoặc file mẫu, map tên field không đồng nhất về một field set chuẩn | MUST | Chạy được trên toàn bộ dataset mà không crash; log rõ SKU nào lỗi và lý do |
| SE-02 | Trích xuất spec kỹ thuật đang nằm trong văn bản marketing thành field có kiểu dữ liệu rõ ràng | MUST | Độ chính xác ≥ 90% trên bộ gold set 30 SKU gán nhãn tay (xem DATA-02) |
| SE-03 | Xuất mỗi sản phẩm thành object Product chuẩn schema.org / JSON-LD, spec đặt trong `additionalProperty` | MUST | 100% output pass validator schema.org; có script validate chạy một lệnh |
| SE-04 | Cấu trúc hoá bảo hành, đổi trả, vận chuyển, và quan hệ tương thích chéo giữa sản phẩm | SHOULD | Truy vấn được "phụ kiện nào tương thích với SKU X" và trả về danh sách đúng |
| SE-05 | Embedding mô tả đã chuẩn hoá vào vector DB để truy vấn theo ngữ nghĩa | MUST | Index đầy đủ số SKU; thời gian index có ghi lại để tính chi phí |
| SE-06 | Lớp chống hallucination: chỉ ghi nhận field truy vết được về nguồn; field do model suy ra phải gắn cờ confidence thấp | MUST | Mọi field trong output có `source` hoặc `confidence`; không có field nào thiếu cả hai |
| SE-07 | Pipeline idempotent, chạy lại chỉ xử lý SKU đã thay đổi | SHOULD | Chạy lần 2 trên dataset không đổi thì số token tiêu thụ ≈ 0 |

**Điểm chết cần tránh:** SE-06 chính là thứ phân biệt dự án này với "gọi LLM tag JSON-LD". Nếu cắt SE-06 thì mất luôn lập luận cốt lõi ở pain point (2).

### 4.2 AEO Scoring và Merchant Dashboard (AEO)

Mỗi trục điểm phải có **công thức xác định**, không được là số do LLM chấm cảm tính.

| ID | Trục | Công thức bắt buộc định nghĩa | Mức |
|---|---|---|---|
| AEO-01 | Completeness | Số field bắt buộc đã điền / tổng field bắt buộc | MUST |
| AEO-02 | Machine-readability | Tập check nhị phân có trọng số: có JSON-LD, spec dạng field thay vì prose, giá và tồn kho không phụ thuộc JS render | MUST |
| AEO-03 | Retrievability | recall@5 trên bộ query chuẩn (DATA-03) | MUST |
| AEO-04 | Answerability | Tỷ lệ câu hỏi trong bộ template trả lời được chỉ bằng dữ liệu của SKU đó | SHOULD |
| AEO-05 | Transactability | Đủ giá, tồn kho, SKU, phí ship để agent tạo đơn hay chưa | MUST |

| ID | Yêu cầu dashboard | Mức | Tiêu chí nghiệm thu |
|---|---|---|---|
| AEO-06 | Danh sách sản phẩm kèm điểm tổng phân tầng màu | MUST | Sắp xếp và lọc được theo điểm |
| AEO-07 | Trang chi tiết từng sản phẩm với điểm 5 trục và **gợi ý cải thiện cụ thể** | MUST | Gợi ý phải gọi tên field còn thiếu, ví dụ "thiếu refresh_rate", không được viết chung chung |
| AEO-08 | Agent Query Simulator: merchant gõ câu hỏi kiểu khách hàng, thấy ngay agent lấy về gì, sản phẩm của mình có được chọn không, và vì sao | MUST | Chạy live trên sân khấu không lỗi; có hiển thị lý do bị loại |
| AEO-09 | So sánh before/after: cùng một query, kết quả trước và sau khi chuẩn hoá | SHOULD | Đây là slide ăn điểm nhất, nên ưu tiên |

> Lưu ý từ đề bài: *độ bóng bẩy của dashboard hướng người là ưu tiên thấp hơn logic tương tác máy với máy*. Đừng dành Day 2 cho CSS.

### 4.3 B2A API Gateway (GW)

| ID | Yêu cầu | Mức | Tiêu chí nghiệm thu |
|---|---|---|---|
| GW-01 | Endpoint semantic catalog search | MUST | Nhận mô tả nhu cầu ngôn ngữ tự nhiên, trả candidate set |
| GW-02 | Endpoint product detail có cấu trúc | MUST | Trả kèm confidence flag từng field |
| GW-03 | Endpoint kiểm tra giá và tồn kho real-time | MUST | Giá trả về khớp nguồn tại thời điểm gọi |
| GW-04 | Endpoint tra cứu chính sách bảo hành / đổi trả / vận chuyển | MUST | Trả dữ liệu có cấu trúc, không trả đoạn văn |
| GW-05 | Endpoint tạo checkout session | MUST | Tạo được order và trả order id |
| GW-06 | Công bố OpenAPI spec | MUST | Spec pass linter; import được vào Swagger UI |
| GW-07 | Bọc thêm MCP server | SHOULD | Gọi được từ một MCP client thật, quay video làm bằng chứng |
| GW-08 | Định danh agent qua API key hoặc OAuth, phân biệt agent hợp lệ với scraping bot | MUST | Request không có credential bị từ chối với mã lỗi rõ ràng |
| GW-09 | Rate limit theo từng agent | SHOULD | Vượt ngưỡng trả 429 |
| GW-10 | Audit log mọi giao dịch | MUST | Mỗi call thay đổi trạng thái sinh một dòng log truy vết được |
| GW-11 | Thanh toán qua authorization token có giới hạn hạn mức và thời gian; agent không bao giờ chạm dữ liệu thẻ | MUST | Token vượt hạn mức hoặc hết hạn bị từ chối; test case chứng minh |

**Ngưỡng hiệu năng đề xuất (nêu trong README, đo thật khi demo):** p95 semantic search < 1.5s, p95 product detail < 300ms. Nếu chậm hơn thì demo sân khấu sẽ chết.

### 4.4 Dynamic Policy Engine (DP)

| ID | Yêu cầu | Mức | Tiêu chí nghiệm thu |
|---|---|---|---|
| DP-01 | Bảng rule dựa trên biên lợi nhuận, tự đề xuất giảm giá hoặc bundle khi agent hỏi nhiều sản phẩm liên quan | MUST | Trigger đúng khi có ≥ 2 sản phẩm liên quan trong phiên |
| DP-02 | **Giá sàn cứng, logic giá là rule tất định, không để LLM tự quyết** | MUST | Chạy thử 1000 trường hợp ngẫu nhiên, không có trường hợp nào xuống dưới sàn |
| DP-03 | Mỗi đề xuất giá trả kèm mã lý do giải thích được | SHOULD | Merchant đọc log hiểu vì sao hệ thống giảm giá |
| DP-04 | Chống lạm dụng: agent hỏi lặp để dò giá sàn phải bị chặn | COULD | Rate limit + không leo thang discount trong cùng phiên |

---

## 5. Yêu cầu dữ liệu (DATA) — phần dễ bị xem nhẹ nhất

Không có bộ dữ liệu tử tế thì cả 5 trục AEO đều sụp, và mọi con số trong pitch thành bịa. Đây là việc cần làm xong **trước** hackathon (được phép, vì không phải viết code).

| ID | Yêu cầu | Mức | Chi tiết |
|---|---|---|---|
| DATA-01 | Catalog mẫu 300–1000 SKU ngành điện tử, có chủ đích "bẩn" | MUST | Spec giấu trong văn xuôi marketing, bảo hành nằm trang riêng, giá render bằng JS. Phải bẩn thì before/after mới thấy được |
| DATA-02 | Gold set 30 SKU gán nhãn tay | MUST | Dùng đo độ chính xác của SE-02. Gán nhãn thủ công, không dùng LLM gán |
| DATA-03 | Bộ 25–40 query ngôn ngữ tự nhiên có đáp án chuẩn | MUST | Phủ 4 nhóm: ràng buộc tương thích, ràng buộc ngân sách, ràng buộc giá trị (ví dụ thương hiệu bền vững), đa ràng buộc kết hợp |
| DATA-04 | Nguồn dữ liệu hợp pháp và khai báo được | MUST | Rulebook chấm tiêu chí "legitimate and reliable data sources". Nếu tự sinh thì ghi rõ là synthetic và nêu cách sinh |
| DATA-05 | Script seed chạy một lệnh | MUST | Giám khảo phải dựng lại được môi trường |

---

## 6. Yêu cầu phi chức năng (NFR)

| ID | Yêu cầu | Mức |
|---|---|---|
| NFR-01 | README.md có: sơ đồ kiến trúc, danh sách công nghệ và API, hướng dẫn cài đặt chạy bằng **một lệnh** | MUST |
| NFR-02 | Repo public hoặc đã share cho BTC; không commit secret; có `.env.example` | MUST |
| NFR-03 | Không lưu dữ liệu thẻ, PII tối thiểu; nêu rõ cách xử lý dữ liệu merchant | MUST |
| NFR-04 | Tuân thủ pháp lý: nêu được Australian Privacy Act và nguyên tắc định danh agent minh bạch | SHOULD |
| NFR-05 | Ước tính chi phí hạ tầng có **con số thật đo từ lần chạy demo**, không phải mô tả định tính | MUST |
| NFR-06 | Kế hoạch scale khi số SKU và lượng truy vấn tăng, kèm điểm nghẽn dự kiến | SHOULD |
| NFR-07 | Khai báo toàn bộ dataset, API, thư viện, pre-trained model đã dùng | MUST |
| NFR-08 | Mọi code viết trong giờ thi; chuẩn bị trước chỉ gồm thiết kế, wireframe, dữ liệu, làm quen tool | MUST |

---

## 7. Kịch bản demo bắt buộc chạy được

Đây chính là kịch bản 6 bước trong proposal. Mỗi bước phải có tiêu chí pass riêng, và toàn bộ phải chạy trong ngân sách thời gian pitch.

| Bước | Hành động của agent | Gateway phải làm | Pass khi |
|---|---|---|---|
| 1 | Người dùng nhờ agent tìm màn hình tương thích laptop hiện có, trong khoảng ngân sách | — | Prompt đọc lên nghe tự nhiên, có ≥ 3 ràng buộc |
| 2 | Gọi semantic search bằng mô tả nhu cầu | Vector DB trả candidate theo ngữ nghĩa | Kết quả khác rõ rệt so với keyword search, chiếu song song 2 cột |
| 3 | Hỏi chi tiết từng candidate để kiểm cổng kết nối và độ phân giải | Trả spec có cấu trúc kèm confidence flag | Nhìn thấy được confidence flag trên màn hình |
| 4 | Kiểm tồn kho, giá, chính sách bảo hành real-time | Truy vấn ON.E/OrderCloud, trả kết quả chuẩn hoá | Số liệu khớp nguồn |
| 5 | Hỏi có ưu đãi khi mua kèm phụ kiện không | Policy engine đề xuất bundle trong biên, tôn trọng giá sàn | Hiện rõ giá sàn không bị phá |
| 6 | Tạo checkout session và hoàn tất đơn | Xác thực token giới hạn, ghi audit trail, đẩy đơn về ON.E | Có order id và dòng audit log chiếu lên màn hình |

**Ngân sách 10 phút pitch:** 1 phút bối cảnh, 1 phút vấn đề, 5 phút demo 6 bước, 1,5 phút dashboard + số liệu, 1,5 phút giá trị kinh doanh và roadmap. Tập bấm giờ ít nhất 3 lần.

**Phương án dự phòng:** quay sẵn video demo full 6 bước phòng khi mạng ở venue hỏng. Cho phép, vì không phải sửa sản phẩm.

---

## 8. Ánh xạ sang thang điểm

### Vòng 1 (100 điểm)

| Tiêu chí | Điểm | Artifact trong dự án ăn điểm này |
|---|---|---|
| Problem framing & depth of research | 30 | Mục 3 (3 pain point + bảng before/after), mục 4 (assumptions + câu hỏi cho FPT), references có nguồn kiểm chứng được |
| Feasibility | 25 | Mục 5.5 tech stack, mục 8.1, và **ước tính chi phí có số** |
| Creativity & innovation | 15 | AEO Scoring 5 trục + Agent Query Simulator. Đây là thứ không giải pháp nào khác có |
| Practical impact | 20 | Bảng metric before/after, giá trị cho FPT (đóng gói bán lại), roadmap |
| Documentation & presentation | 10 | Đúng format, không lỗi chính tả, **có sơ đồ kiến trúc thật** |

### Vòng 2 (100 điểm)

| Tiêu chí | Điểm | Cần có |
|---|---|---|
| User experience | 20 | Merchant là user chính, không phải shopper. Dashboard trực trực quan, nhất quán |
| Technical quality | 25 | Demo chạy, repo + one-command setup, kiến trúc rõ, code sạch, tái lập được, bảo mật dữ liệu |
| Deployability & scalability | 20 | NFR-05, NFR-06, NFR-04 |
| Market strategy | 25 | Phân khúc khách, lợi thế cạnh tranh, kênh phân phối qua ON.E, go-to-market |
| Adaptation & upgrade | 10 | Tiếp thu full case study và input từ Problem Setter ở talkshow |

**Lưu ý:** Market strategy chiếm 25 điểm ở vòng 2, ngang Technical quality. Đây là chỗ team kỹ thuật hay bỏ quên. Phải có người chịu trách nhiệm riêng phần này.

### Ưu tiên riêng của FPT (chấm ở Gala, theo thứ tự trọng số)
1. Intention Accuracy & Semantic Matching
2. Technical Architecture
3. Business Value & Conversion

Ba việc trên map thẳng vào SE-02/SE-05/AEO-03, GW-06/GW-07, và DP-01/AEO-09.

---

## 9. Khoảng trống trong bản v3 cần lấp trước khi nộp

Đọc kỹ bản v3 so với rubric, có 6 chỗ đang mất điểm:

1. **Mục 6 kiến trúc hiện chỉ có chữ.** Rulebook yêu cầu sơ đồ kiến trúc hoặc wireframe, và tiêu chí 5 chấm riêng "illustrative architecture diagram". Phải vẽ hình thật.
2. **Mục 8.2 chi phí không có một con số nào.** Tiêu chí Feasibility ghi rõ "estimated infrastructure and operating costs". Cần ít nhất: chi phí embedding một lần cho N SKU, chi phí vector DB theo tháng, chi phí mỗi 1000 truy vấn agent.
3. **Bảng 8.3 cột "Expected After" đang định tính.** Tiêu chí Practical impact yêu cầu "estimated concrete value". Cần con số dự kiến, kèm giả định dẫn tới con số đó.
4. **References thiếu URL, và có nguồn ghi mơ hồ** kiểu "compiled from industry analyses". Giám khảo có kiểm nguồn. Một nguồn không truy được làm hỏng cả tiêu chí 1.
5. **"Sample AI agent script" dễ bị đọc thành consumer-facing assistant.** Đổi cách gọi thành test harness và nói rõ trong 1 câu.
6. **Chưa nêu số SKU cụ thể của dataset.** Con số này là thứ làm cho toàn bộ ước tính chi phí và metric trở nên đáng tin.

---

## 10. Definition of Done và thang cắt phạm vi

### Bộ ba tối thiểu (dưới mức này thì không chứng minh được luận điểm)
`Semantic Engine + Merchant Dashboard + 1 agent chạy end-to-end`

### Thứ tự cắt khi trễ
1. Knowledge Graph tương thích chéo (SE-04)
2. Dynamic pricing policy (DP-01 tới DP-04)
3. Checkout (GW-05, GW-11)
4. MCP wrapper (GW-07)

Không bao giờ cắt: SE-02, SE-03, SE-06, AEO-03, AEO-08.

### Mốc thời gian trong 16 giờ

| Thời điểm | Phải xong |
|---|---|
| Day 1, hết giờ 3 | Pipeline ingest + JSON-LD chạy trên toàn dataset |
| Day 1, hết giờ 6 | Vector index xong, semantic search endpoint trả kết quả |
| Day 1, hết giờ 8 | **Tích hợp 3 nhánh, một luồng end-to-end thô đã chạy** |
| Day 2, hết giờ 4 | AEO scoring + Query Simulator hoạt động |
| Day 2, hết giờ 6 | README + repo + đóng băng tính năng |
| Day 2, hết giờ 7 | Chạy thử demo 2 lượt, quay video dự phòng |
| Day 2, 17:00 | Nộp |

Nguyên tắc: ba khối phát triển song song, chỉ tích hợp cuối Day 1, để không ai ngồi chờ ai. Nếu đến hết giờ 8 Day 1 chưa có luồng end-to-end thô thì kích hoạt thang cắt ngay, đừng chờ Day 2.

---

## 11. Checklist nộp bài

### Vòng 1
- [ ] PDF ≤ 7 trang, 11–12pt, lề ≥ 2cm, tiếng Anh
- [ ] Đủ 5 thành viên, ≥ 2 quốc tịch Việt Nam, đủ tên trường email SĐT leader
- [ ] Có sơ đồ kiến trúc thật
- [ ] Chi phí có số
- [ ] Impact có số
- [ ] References có URL, không có nguồn mơ hồ
- [ ] Không câu nào mô tả sản phẩm là consumer-facing assistant
- [ ] Nộp trước 23:59 05/09/2026 AEST

### Vòng 2
- [ ] Demo chạy được live
- [ ] README.md đủ kiến trúc + tech stack + one-command setup
- [ ] Repo public hoặc đã share BTC, không có secret
- [ ] Khai báo đủ dataset / API / thư viện
- [ ] Pitch deck
- [ ] Video demo dự phòng
- [ ] 100% code viết trong giờ thi
- [ ] Nộp trước 17:00 13/09/2026 AEST

### Vòng 3
- [ ] Deck chốt nộp trước 23:59 19/09/2026
- [ ] Demo đúng bản vòng 2, không sửa tính năng cốt lõi
- [ ] Đã bấm giờ pitch ≤ 10 phút, ít nhất 3 lượt
- [ ] Chuẩn bị trả lời Q&A: vì sao không tự làm chuẩn riêng, chi phí ở quy mô 100k SKU, xử lý khi LLM đọc sai spec, vì sao merchant chịu trả tiền

---

## 12. Rủi ro và phòng ngừa

| Rủi ro | Mức | Phòng ngừa |
|---|---|---|
| Bị đánh giá là lệch phạm vi vì mock buyer agent | Cao | Đổi tên thành test harness, nói rõ trong deck và README |
| Chuẩn agentic commerce thay đổi giữa chừng | Trung bình | Tách tầng giao tiếp khỏi lõi ngữ nghĩa, đổi chuẩn chỉ cần thay adapter |
| LLM trích sai spec kỹ thuật | Cao | SE-06 truy vết nguồn, field không truy được thì gắn cờ chứ không công bố |
| Demo chết trên sân khấu do mạng hoặc rate limit API | Cao | Cache kết quả demo, video dự phòng, tăng quota trước |
| Không kịp tích hợp 3 nhánh | Cao | Chốt interface giữa 3 nhánh **trước** hackathon (thiết kế, được phép), tích hợp cuối Day 1 |
| Số liệu trong pitch không có chỗ dựa | Trung bình | DATA-02 và DATA-03 phải xong trước hackathon |
| Bỏ quên Market strategy 25 điểm ở vòng 2 | Trung bình | Giao riêng một người phụ trách, không để dev kiêm |
