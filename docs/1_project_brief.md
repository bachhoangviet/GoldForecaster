# Project Brief: GoldForecaster - Hệ Thống Dự Báo Giá Vàng AI

## Introduction / Problem Statement
Vàng là một trong những tài sản tài chính có tính thanh khoản cao và nhạy cảm bậc nhất thế giới. Giá vàng biến động liên tục dưới tác động phức tạp của các yếu tố kinh tế vĩ mô (lãi suất, lạm phát, sức mạnh đồng tiền), các sự kiện địa chính trị (chiến tranh, khủng hoảng) và tâm lý thị trường toàn cầu. 

Đối với các nhà đầu tư và nhà giao dịch, việc theo dõi và xử lý một khối lượng khổng lồ thông tin từ các nguồn tin chính thống hằng ngày là một thách thức lớn, dễ dẫn đến hiện tượng "quá tải thông tin" (information overload) hoặc bỏ lỡ các tín hiệu đảo chiều quan trọng. Dự án **GoldForecaster** được phát triển nhằm giải quyết bài toán này bằng cách tự động hóa toàn bộ quy trình: thu thập dữ liệu vĩ mô cứng và mềm từ các nguồn chính thống, tóm tắt tinh gọn tin tức và sử dụng mô hình ngôn ngữ lớn nâng cao (Gemini API) để đưa ra dự báo đa khung thời gian một cách trực quan.

## Vision & Goals
- **Vision:** Trở thành nền tảng trợ lý AI hàng đầu hỗ trợ ra quyết định đầu tư và giao dịch vàng dựa trên việc tích hợp dữ liệu vĩ mô thời gian thực và phân tích ngôn ngữ tự nhiên tiên tiến.
- **Primary Goals (MVP):**
  - **Goal 1:** Xây dựng đường ống tự động (Data Pipeline) thu thập tin tức và chỉ số tài chính từ ít nhất 4 nguồn chính thống quốc tế hằng ngày mà không bị chặn (rate-limiting).
  - **Goal 2:** Ứng dụng Gemini API (dòng Flash) để tự động hóa việc tóm tắt văn bản tin tức, phân loại tác động thị trường (Bullish/Bearish/Neutral) với độ chính xác và tính cô đọng cao.
  - **Goal 3:** Thiết kế Siêu Prompt (Meta-Prompting) để Gemini đưa ra dự báo giá vàng định kỳ cho 4 khung thời gian (Ngày, Tuần, Tháng, Quý) đính kèm Mức độ tự tin (Confidence Score).
  - **Goal 4:** Triển khai một Web Dashboard trực quan (Next.js + Tailwind CSS) hiển thị biểu đồ, tin tóm tắt và widget dự báo trong vòng 1-2 tháng phát triển.

## Target Audience / Users
- **Nhà giao dịch nhỏ lẻ (Retail Traders / Day Traders):** Những người cần cập nhật nhanh tin tức hằng ngày, biến động chỉ số vĩ mô trong các phiên Á-Âu-Mỹ để lướt sóng ngắn hạn.
- **Nhà đầu tư cá nhân trung và dài hạn:** Những người quan tâm đến xu hướng tuần, tháng, quý để đưa ra chiến lược tích sản hoặc phân bổ danh mục đầu tư vàng vật chất/tài khoản.
- **Chuyên viên phân tích tài chính sơ cấp:** Sử dụng công cụ như một trợ lý tóm tắt và cung cấp góc nhìn tham khảo nhanh về tâm lý thị trường.

## Key Features / Scope (High-Level Ideas for MVP)
- **Feature 1: Động cơ Thu thập Dữ liệu Đa nguồn (Multi-source Scraper & Ingestion Engine)**
  - Tự động cào/quét văn bản tin tức từ Kitco News, Reuters, Bloomberg, CNBC và trang chủ FED.
  - Tích hợp API thu thập các điểm số liệu cứng: Chỉ số sức mạnh đồng USD (DXY), Lợi suất trái phiếu chính phủ Mỹ 10 năm (US10Y), Khối lượng giao dịch/nắm giữ của quỹ ETF SPDR Gold Shares.
- **Feature 2: Khối Xử lý & Tóm tắt Thông minh (AI News Summarizer)**
  - Chuyển hóa các bài báo dài thành các gạch đầu dòng luận điểm cốt lõi.
  - Gán nhãn tác động tâm lý thị trường (Bullish - Tăng giá, Bearish - Giảm giá, Neutral - Trung lập).
- **Feature 3: Khối Dự báo Đa khung Thời gian (Gemini Forecasting Core)**
  - Kết hợp "Tin tóm tắt + Số liệu cứng + Lịch sử giá ngắn hạn" vào cấu trúc Prompt chuyên sâu.
  - Gọi Gemini API sinh kết quả phân tích xu hướng cho 4 mốc: Ngày, Tuần, Tháng, Quý kèm điểm số tự tin (Confidence Score 0-100%).
- **Feature 4: Giao diện Web Trực quan (Modern Web Dashboard)**
  - Biểu đồ nến/line biến động giá vàng thời gian thực.
  - Bảng tin vĩ mô tóm tắt bởi AI.
  - Widget hiển thị dự báo xu hướng (Mũi tên xanh/đỏ/ngang) kèm thanh tiến trình mức độ tin cậy.

## Post MVP Features / Scope and Ideas
- **Feature 1:** Tích hợp thêm các mô hình học máy truyền thống (LSTM, ARIMA) hoặc mô hình định lượng để chấm điểm kỹ thuật độc lập song song với phân tích định tính của Gemini.
- **Feature 2:** Hệ thống cảnh báo tự động qua Telegram/Email/Push Notification khi có tin tức tác động cực mạnh (ví dụ: Thay đổi lãi suất bất ngờ từ FED, xung đột địa chính trị leo thang).
- **Feature 3:** Hỗ trợ phân tích chuyên sâu các tài liệu báo cáo PDF định kỳ dài hàng trăm trang của các tổ chức tài chính lớn (Goldman Sachs, JPMorgan, World Gold Council).

## Known Technical Constraints or Preferences
- **Constraints:** - Tránh hardcode mã khóa API; bắt buộc quản lý bảo mật qua biến môi trường.
  - Các trang tin như Bloomberg/Reuters có cơ chế chống cào (Anti-bot) nghiêm ngặt, backend cần triển khai cơ chế rotate user-agent hoặc sử dụng headless browser phù hợp (Playwright).
  - Giới hạn hạn mức (Rate-limit) và chi phí token của Gemini API khi xử lý khối lượng lớn bài báo hằng ngày.
- **Preferences (if any):**
  - Cấu trúc kho lưu trữ: **Monorepo** để quản lý cả backend và frontend trong một dự án duy nhất.
  - Ngôn ngữ & Framework Backend: **Python** để tận dụng tối đa hệ sinh thái thư viện xử lý dữ liệu (Pandas, BeautifulSoup) và AI SDK.
  - Ngôn ngữ & Framework Frontend: **Next.js (React/TypeScript) + Tailwind CSS** để dựng ứng dụng web hiện đại, chuẩn SEO và mượt mà.
- **Risks:** - Hiện tượng "ảo tưởng" (Hallucination) của LLM khiến Gemini đưa ra các con số dự báo giá cụ thể thiếu căn cứ logic. Biện pháp giảm thiểu: Ép cấu trúc đầu ra (Structured Outputs) chỉ dự báo xu hướng định tính và mức độ tự tin, không đoán giá trị tuyệt đối cụ thể nếu không có mô hình toán học hỗ trợ.
  - Thay đổi cấu trúc DOM của các trang tin tức làm gãy bộ cào dữ liệu (Web Scraper).

## Relevant Research (Optional)
*(Sẽ bổ sung các báo cáo Deep Research về độ tương quan tuyến tính/phi tuyến giữa DXY, US10Y và Giá Vàng quốc tế theo dữ liệu lịch sử 10 năm qua ở các giai đoạn sau).*

## PM Prompt
This Project Brief provides the full context for GoldForecaster. Please start in 'PRD Generation Mode', review the brief thoroughly to work with the user to create the PRD section by section 1 at a time, asking for any necessary clarification or suggesting improvements as your mode 1 programming allows.
