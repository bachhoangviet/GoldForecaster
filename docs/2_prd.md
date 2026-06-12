# GoldForecaster - Product Requirements Document (PRD)

## Goal, Objective and Context
Dự án **GoldForecaster** hướng tới việc xây dựng một hệ thống phần mềm tự động hóa toàn trình (End-to-End Pipeline) nhằm thu thập, xử lý thông tin kinh tế vĩ mô và thị trường từ các nguồn chính thống quốc tế, sau đó ứng dụng mô hình ngôn ngữ lớn (Gemini API) để phân tích tâm lý, tổng hợp dữ liệu số và đưa ra các dự báo xu hướng giá vàng định kỳ theo Ngày, Tuần, Tháng, Quý. Mục tiêu cốt lõi của MVP là kiểm chứng sự hiệu quả của việc kết hợp giữa phân tích dữ liệu số (DXY, US10Y, SPDR) và phân tích định tính văn bản bằng AI để tạo ra một Dashboard hỗ trợ quyết định giao dịch trực quan, bảo mật và có khả năng kiểm thử cục bộ cao.

## Functional Requirements (MVP)
Hệ thống được bẻ nhỏ thành 5 Epic chức năng chính phục vụ cho phiên bản đầu tiên (MVP):

### Epic 1: Thiết lập nền tảng cốt lõi & Cơ sở hạ tầng hệ thống
* **Story 1.1: Khởi tạo cấu trúc dự án & Môi trường ảo Python**
  * *Mô tả:* Là một Developer, tôi muốn khởi tạo cấu trúc thư mục Monorepo chuẩn kèm cấu hình môi trường ảo Python cô lập, để mã nguồn được tổ chức khoa học và không bị xung đột thư viện thư thức.
  * *Tiêu chí nghiệm thu (AC):*
    1. Tạo đầy đủ cấu trúc thư mục cốt lõi: `src/backend/core/`, `src/backend/services/`, `src/backend/adapters/`, `tests/`, `docs/`.
    2. Thiết lập file `requirements.txt` để quản lý tập trung các dependency.
    3. Tạo file `.gitignore` loại bỏ môi trường ảo (`.venv`), file cấu hình bí mật (`.env`) và cache Python.
* **Story 1.2: Cấu hình biến môi trường bảo mật & Kết nối Gemini API cơ bản**
  * *Mô tả:* Là một Hệ thống, tôi muốn có cơ chế đọc API Key của Gemini một cách bảo mật từ file cấu hình cục bộ để thực hiện cuộc gọi kiểm tra kết nối (Ping) thông suốt.
  * *Tiêu chí nghiệm thu (AC):*
    1. Tích hợp thư viện `python-dotenv` để đọc cấu hình bí mật từ file `.env`.
    2. Tạo file mẫu `.env.example` chứa placeholder cấu hình tiêu chuẩn (`GEMINI_API_KEY=your_key_here`).
    3. Viết script `src/backend/adapters/gemini_client.py` sử dụng SDK chính thức để gửi text ngắn và nhận về phản hồi nhằm kiểm tra kết nối.
    4. Không chứa bất kỳ API Key cứng nào trong mã nguồn đưa lên Git.
* **Story 1.3: Xây dựng CLI Shell kiểm thử cục bộ cho Developer**
  * *Mô tả:* Là một Developer, tôi muốn có giao diện dòng lệnh (CLI) cơ bản để kích hoạt nhanh các hàm chức năng chính của hệ thống bằng lệnh, phục vụ việc kiểm thử độc lập mà chưa cần UI.
  * *Tiêu chí nghiệm thu (AC):*
    1. Tạo file chạy chính `main.py` ở thư mục gốc sử dụng thư viện `argparse` hoặc `click`.
    2. Hỗ trợ lệnh kiểm tra kết nối AI thông qua cú pháp: `python main.py --test-ai`.
    3. Bắt và xử lý các lỗi ngoại lệ (Mất mạng, sai khóa) một cách tường minh, in ra thông báo lỗi dễ hiểu thay vì crash ứng dụng.

### Epic 2: Module thu thập & Chuẩn hóa dữ liệu vĩ mô (Data Ingestion Pipeline)
* Thu thập văn bản tin tức hằng ngày từ Kitco, Reuters, Bloomberg, CNBC, và FED.
* Thu thập số liệu cứng thời gian thực hoặc định kỳ hằng ngày: Chỉ số DXY, Lợi suất trái phiếu US10Y, và lượng nắm giữ vàng của quỹ ETF SPDR Gold Shares.
* Làm sạch dữ liệu, lọc bỏ thẻ HTML, quảng cáo và đồng bộ thời gian (Timestamp) lưu trữ cục bộ (JSON hoặc SQLite).

### Epic 3: Hệ thống xử lý, tóm tắt tin tức & Kỹ thuật Prompt dự báo (Gemini Core Layer)
* Sử dụng Gemini Flash để rút gọn tin tức dài thành các luận điểm chính và gán nhãn trạng thái xu hướng (Bullish/Bearish/Neutral).
* Xây dựng cấu trúc prompt tích hợp dữ liệu số và văn bản để gửi lên Gemini Advanced/Ultra.
* Đầu ra của mô hình phải cung cấp dự báo xu hướng cho 4 khung thời gian kèm điểm số tự tin (Confidence Score từ 0-100%).

### Epic 4: Giao diện Dashboard trực quan (Frontend UI)
* Hiển thị biểu đồ nến/đường động cho giá vàng quốc tế thời gian thực.
* Khu vực hiển thị danh sách các tin tức tài chính kinh tế đã được AI tóm tắt gọn gàng.
* Widget hiển thị kết quả phân tích xu hướng đa mốc thời gian kèm thanh tiến trình trực quan thể hiện mức độ tự tin của AI.

### Epic 5: Kiểm thử tự động & Tối ưu hóa vận hành (Testing Shell)
* Viết kịch bản Integration Test chạy toàn trình luồng dữ liệu thô đầu vào cho tới đầu ra dự báo.
* Đảm bảo hệ thống xử lý lỗi mạng tốt khi chạy ngầm định kỳ (cron job/worker).

## Non Functional Requirements (MVP)
- **Performance (Hiệu năng):** Bộ cào dữ liệu phải hoạt động bất đồng bộ hoặc đa luồng sao cho tổng thời gian quét toàn bộ các trang nguồn không quá 5 phút mỗi phiên chạy. Thời gian phản hồi của API tóm tắt và dự báo phụ thuộc vào Gemini API nhưng cần được tối ưu hóa bằng cách lưu cache kết quả dự báo trong ngày/trong tuần.
- **Security (Bảo mật):** Toàn bộ API Key, thông tin kết nối cơ sở dữ liệu phải được mã hóa hoặc lưu trữ tách biệt trong biến môi trường hệ thống. Không để lộ thông tin nhạy cảm ở phía client (Frontend).
- **Reliability (Độ tin cậy):** Hệ thống cào dữ liệu phải có cơ chế Retry (Thử lại) tự động (tối đa 3 lần cách nhau 5 giây) khi gặp lỗi kết nối mạng hoặc lỗi timeout từ phía server nguồn.
- **Maintainability (Khả năng bảo trì):** Mã nguồn tuân thủ tiêu chuẩn PEP 8 (đối với Python), các module tách biệt rõ ràng (tách cấu trúc Scraper độc lập với Logic xử lý AI).

## User Interaction and Design Goals
- **Overall Vision & Experience:** Thiết kế giao diện theo phong cách hiện đại, tối giản, mang hơi hướng tài chính chuyên nghiệp (Sử dụng bảng màu tối Deep Blue hoặc Slate Grey, kết hợp màu Gold làm điểm nhấn phản ánh chủ đề của ứng dụng). Trải nghiệm người dùng phải nhanh chóng, cô đọng, nhìn vào là thấy ngay kết quả dự báo quan trọng nhất.
- **Key Interaction Paradigms:** - Chuyển đổi linh hoạt giữa các tab khung thời gian (Ngày / Tuần / Tháng / Quý) tại Widget Dự báo chính để xem chi tiết luận điểm tương ứng của Gemini.
  - Hỗ trợ bộ lọc nhanh tin tức theo trạng thái tâm lý (Chỉ hiển thị tin Bullish hoặc Bearish).
- **Core Screens/Views (Conceptual):**
  - *Main Dashboard:* Màn hình chính bao gồm: Góc trên bên trái là biểu đồ giá vàng thực tế; Góc trên bên phải là Widget Dự báo đa khung thời gian AI; Nửa dưới màn hình là Bảng tổng hợp các tin tức vĩ mô đã được tóm tắt kèm nhãn màu sắc (Xanh cho Bullish, Đỏ cho Bearish).

## Definitive Tech Stack Selections
- **Repository Pattern:** Monorepo.
- **Hosting / Deployment:** Chạy cục bộ (Local Desktop environment) cho giai đoạn phát triển ban đầu, có khả năng đóng gói Docker Container để triển khai lên các nền tảng đám mây nhẹ (Render, DigitalOcean).
- **Frontend Platform:** Next.js (React Framework, TypeScript) kết hợp Tailwind CSS để tối ưu hóa giao diện trực quan và responsive.
- **Backend Platform:** Python (Phiên bản >= 3.10), kết hợp thư viện `requests`, `beautifulsoup4`, `playwright` cho việc cào dữ liệu; `google-genai` hoặc `google-generativeai` làm SDK chính thức kết nối Gemini.
- **Database Requirements:** SQLite cho giai đoạn MVP gọn nhẹ, dễ di chuyển và không yêu cầu cấu hình máy chủ cơ sở dữ liệu phức tạp.

## Technical Constraints
- Bắt buộc phải sử dụng SDK chính thức của Google cho Gemini API, không sử dụng các wrapper không chính thống của bên thứ ba.
- Hệ thống cào dữ liệu văn bản từ Reuters/Bloomberg phải sử dụng cơ chế giả lập trình duyệt (Playwright với thiết lập ẩn danh chống bot) để tránh bị chặn IP ngay từ lần quét đầu tiên.
- SQLite database phải được cấu hình ghi đồng thời an toàn (WAL mode) để tránh khóa cơ sở dữ liệu khi backend vừa ghi dữ liệu cào mới, vừa có client đọc dữ liệu hiển thị.

## Deployment Considerations
- Tần suất cập nhật dữ liệu (Data Cron/Worker): Quét số liệu cứng hằng giờ; quét tin tức văn bản 4 lần/ngày (theo đầu các phiên giao dịch chính).
- Thiết lập môi trường chạy độc lập: Môi trường `local` phát triển sử dụng file `.env` cục bộ; môi trường `production` sử dụng cấu hình Config Vars của nhà cung cấp Cloud.

## Local Development & Testing Requirements
- **Local Dev Environment:** Yêu cầu cài đặt sẵn Python 3.10+ và Node.js 18+. Hướng dẫn tạo lập môi trường ảo và cài đặt dependency phải chạy mượt mà thông qua một lệnh duy nhất được tài liệu hóa trong `README.md`.
- **Command-line Testing Capabilities:** Bản phân phối mã nguồn phải bao gồm file `main.py` ở thư mục gốc đóng vai trò là một CLI Shell đa năng hỗ trợ các cờ lệnh kiểm thử độc lập như:
  - `python main.py --test-ai`: Kiểm tra kết nối Gemini API.
  - `python main.py --run-scraper`: Chạy thử độc lập module cào dữ liệu để kiểm tra cấu trúc HTML của các trang nguồn.
  - `python main.py --show-data`: In nhanh các bản ghi dữ liệu số cứng hiện có trong database cục bộ ra terminal.

## Other Technical Considerations
- **LLM Cost Mitigation:** Để tối ưu hóa chi phí token và giới hạn hạn mức gọi API, hệ thống chỉ kích hoạt cuộc gọi gửi Siêu Prompt dự báo xu hướng (Epic 3) khi và chỉ khi có dữ liệu tin tức mới được cập nhật trong phiên, không gọi API lặp đi lặp lại một cách vô nghĩa nếu dữ liệu đầu vào không thay đổi.

----- END Architect Prompt -----
