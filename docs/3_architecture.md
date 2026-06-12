# GoldForecaster - Architecture Document

## Introduction / Preamble
Tài liệu này phác thảo toàn bộ kiến trúc kỹ thuật của hệ thống **GoldForecaster**, bao gồm các hệ thống backend, dịch vụ chia sẻ và các khía cạnh phi UI độc lập. Mục tiêu cốt lõi của tài liệu là đóng vai trò là một bản thiết kế kiến trúc định hướng cho việc phát triển dựa trên tác nhân AI (AI-driven development), đảm bảo tính nhất quán và tuân thủ nghiêm ngặt các khuôn mẫu phát triển và công nghệ đã chọn.

**Relationship to Frontend Architecture:**
Hệ thống sử dụng mô hình mã nguồn tập trung (Monorepo). Mã nguồn frontend ứng dụng ứng dụng Web (Next.js + Tailwind CSS) sẽ nằm chung cấu trúc kho lưu trữ này và giao tiếp trực tiếp với lớp dữ liệu/dịch vụ của Python Backend để hiển thị Dashboard trực quan cho người dùng cuối.

## Table of Contents
1. Technical Summary
2. High-Level Overview
3. Component Deep Dive
4. Definitive Tech Stack Selections
5. Technical Constraints & Security Controls
6. Deployment & Environment Considerations
7. Local Development & Testing Requirements

## Technical Summary
Hệ thống **GoldForecaster** được thiết kế theo mô hình kiến trúc **Modular Monolith** kết hợp mô hình **Monorepo** để quản lý cả Backend lẫn Frontend. Hệ thống Backend Python chịu trách nhiệm điều phối toàn bộ đường ống dữ liệu (Data Pipeline) từ việc cào/quét văn bản tin tức phi cấu trúc (Kitco, Reuters, v.v.) và tích hợp dữ liệu số cứng (DXY, US10Y, SPDR) thông qua các Worker/Cron chạy ngầm định kỳ. Lớp xử lý trí tuệ nhân tạo (AI Layer) ứng dụng dòng mô hình **Gemini API (bản Flash và Advanced)** làm hạt nhân lõi phục vụ hai mục đích chuyên biệt: Tóm tắt/gán nhãn tâm lý thị trường cho các bài báo thô và Thực thi Siêu Prompt (Meta-Prompting) để kết hợp toàn bộ bối cảnh (Context) nhằm kết xuất cấu trúc dự đoán đa khung thời gian. Dữ liệu được lưu trữ và đồng bộ cục bộ bằng **SQLite (WAL mode)** để tối ưu hóa hiệu năng đọc/ghi đồng thời trước khi đẩy ra ứng dụng **Next.js Web Dashboard**.

## High-Level Overview
- **Architectural Style:** Modular Monolith (Thiết kế đơn khối mô-đun hóa độc lập).
- **Repository Structure:** Monorepo (`goldforecaster/`).
- **Primary User Interaction Paradigm:** Giao diện dòng lệnh (CLI Shell `main.py`) phục vụ giai đoạn phát triển/kiểm thử cục bộ tại Epic 1; Hệ thống Web Dashboard tương tác trực quan thời gian thực cho người dùng cuối tại các giai đoạn sau.

## Component Deep Dive

### 1. Data Ingestion Layer (Lớp Thu thập Dữ liệu)
- **Web Scrapers Adapter (`src/backend/adapters/web_scrapers.py`):**
  - Chịu trách nhiệm trích xuất cấu trúc văn bản thô từ các trang tin (Kitco, FED, Reuters, CNBC).
  - Sử dụng `BeautifulSoup` cho các trang có cấu trúc tĩnh (Kitco) và `Playwright` ẩn danh (Headless với giả lập User-Agent xoay tua) cho các trang có tường lửa chống cào cao (Bloomberg/Reuters).
- **Market API Adapter (`src/backend/adapters/market_api.py`):**
  - Thực hiện gọi API bất đồng bộ lấy các chỉ số số cứng (DXY, US10Y, SPDR) từ các nguồn dữ liệu tài chính công cộng/miễn phí.

### 2. Storage Layer (Lớp Lưu trữ Cơ sở Dữ liệu)
- **Database Engine (`src/backend/core/database.py`):**
  - Sử dụng cơ sở dữ liệu nhúng **SQLite**.
  - Cấu hình bắt buộc: Bật chế độ **WAL (Write-Ahead Logging)** để đảm bảo tiến trình Backend Worker ghi dữ liệu cào mới vào file db không làm nghẽn hoặc khóa (Database Locked) luồng đọc dữ liệu từ phía ứng dụng Frontend/CLI.

### 3. AI Processing Layer (Lớp Xử lý Gemini Core)
- **Gemini Client Adapter (`src/backend/adapters/gemini_client.py`):**
  - Đóng gói (Encapsulate) SDK chính thức `google-genai` của Google.
  - Quản lý vòng đời kết nối, bẫy các lỗi ngoại lệ kết nối mạng hoặc lỗi định mức (Rate-limit) và trả về thông tin thô từ AI.
- **AI Services (`src/backend/services/summarizer.py` & `predictor.py`):**
  - `summarizer.py`: Nạp văn bản thô, gọi mô hình giá rẻ, tốc độ cao (Gemini Flash) để rút trích luận điểm cốt lõi và gán nhãn xu hướng (`Bullish`, `Bearish`, `Neutral`).
  - `predictor.py`: Tổng hợp chuỗi dữ liệu (Văn bản tin đã tóm tắt + Số liệu cứng DXY/US10Y/SPDR + Lịch sử giá vàng gần nhất), nhúng vào cấu trúc Siêu Prompt để yêu cầu mô hình nâng cao đưa ra dự báo xu hướng định tính 4 khung thời gian và trả về cấu trúc dữ liệu JSON chuẩn hóa chứa điểm số tự tin (`Confidence Score`).

## Definitive Tech Stack Selections
- **Core Languages:** Python (Backend >= 3.10), TypeScript (Frontend).
- **Frontend Core:** Next.js (App Router), Tailwind CSS.
- **Backend AI SDK:** `google-genai` (SDK thế hệ mới chính thức của Google).
- **Configuration Security:** `python-dotenv`.
- **Data Gathering Libraries:** `beautifulsoup4`, `playwright`.
- **Database:** `sqlite3` (WAL Mode).

## Technical Constraints & Security Controls
- **Bảo mật Khóa API:** Tuyệt đối cấm ghi cứng (Hardcode) chuỗi API Key của Gemini trong mã nguồn. Toàn bộ cấu hình phải được nạp thông qua biến môi trường hệ thống hoặc đọc từ file cục bộ `.env` thông qua thư viện `python-dotenv`. File `.env` phải được khai báo trong `.gitignore`.
- **Phòng chống Chặn IP (Anti-bot Mitigation):** Tần suất cào tin văn bản được cấu hình giãn cách (4 lần/ngày), kết hợp cơ chế thiết lập Header giả lập trình duyệt người dùng thật (Random User-Agent) và sử dụng Playwright tự động đóng phiên để giải phóng bộ nhớ hệ thống.
- **Giảm thiểu Chi phí AI (Cost Optimization):** Lưu trữ kết quả tóm tắt tin tức và kết quả dự báo trong ngày vào SQLite db. Chỉ kích hoạt luồng Siêu Prompt dự báo khi kiểm tra thấy database vừa cập nhật các bản tin tài chính hoặc chỉ số kinh tế mới trong phiên chạy, loại bỏ việc lặp lại các cuộc gọi API không cần thiết.

## Deployment & Environment Considerations
- **Môi trường phát triển (Local Dev):** Chạy trực tiếp trên máy cục bộ của Developer thông qua môi trường ảo độc lập (`.venv`), lưu trữ db dạng file vật lý cục bộ giúp kiểm thử nhanh mà không cần kết nối mạng hạ tầng phức tạp.
- **Môi trường vận hành (Production Shell):** Khả năng đóng gói toàn bộ Monorepo thành Docker Container độc lập để triển khai gọn nhẹ lên Cloud (Render/DigitalOcean), kết hợp cấu hình Cron Job hệ thống để kích hoạt Worker cào dữ liệu tự động.

## Local Development & Testing Requirements
- **CLI Shell Kiểm thử Độc lập (`main.py`):**
  - Để đảm bảo nguyên tắc kiểm thử độc lập (Local Testability) của phương pháp luận UNI, file `main.py` tại thư mục gốc đóng vai trò là bảng điều khiển CLI trung tâm cho lập trình viên.
  - Phải tích hợp thư viện `argparse`/`click` để nhận dạng các cờ lệnh thực thi độc lập:
    - `--test-ai`: Gọi script `gemini_client.py` để chạy hàm Ping kiểm tra tính thông suốt của API Key và kết nối mạng đến máy chủ Google GenAI.
    - `--run-scraper`: Chạy kiểm tra độc lập cấu trúc trích xuất dữ liệu của các Scraper mà không lưu db hoặc gọi AI.
    - `--show-data`: In trực tiếp các dữ liệu thô hiện có trong bảng SQLite ra giao diện terminal để kiểm tra tính toàn vẹn.

----- END Architect Solution Validation Checklist -----
