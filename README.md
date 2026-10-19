# 🚀 Auto PR Generator (AI-Powered)

Ứng dụng Python sử dụng trí tuệ nhân tạo (Claude Sonnet 4.6 & Gemini 3.8 Flash qua Antigravity AI Engine) để tự động đọc và tóm tắt Pull Request từ GitHub, phân tích toàn bộ commit và file diffs để tạo ra bản mô tả PR chuyên nghiệp theo chuẩn cấu trúc markdown của team.

---

## 🌟 Tính Năng Nổi Bật

1. **Tự Động Phân Tích Dữ Liệu PR**:
   - Tự động lấy tiêu đề, tác giả, nhánh nguồn (`head`), nhánh đích (`base`), danh sách commits và số lượng thay đổi (+/-).
   - Tự động đọc code diff, lọc bỏ các file lock/bundle sinh tự động (`package-lock.json`, minified files) để tập trung vào logic cốt lõi.
2. **AI Tóm Tắt Chuẩn Xác**:
   - Sử dụng mô hình **Claude Sonnet 4.6 (Thinking)** hoặc **Gemini 3.8 Flash** thông qua Antigravity CLI.
   - Nội dung mô tả được viết chuẩn mực bằng **tiếng Anh**, phân loại chính xác các mục thay đổi (Bugfix, Feature, Performance...).
3. **Tuân Thủ Cấu Trúc Markdown Bắt Buộc**:
   - `## What`: Chi tiết các thay đổi logic.
   - `## Why`: Lý do thực hiện thay đổi và bài toán giải quyết.
   - `## How to QA?`: Checklist các bước kiểm thử cụ thể kèm cam kết sau khi merge lên master.
   - `## Any screenshots or loom video?`: Gợi ý kiểm thử trực quan.
   - `## Types of changes`: Đánh dấu checkbox tự động (`[x]`).
   - `## Automation tests:`: Gợi ý các trường hợp kiểm thử tự động hóa giá trị cao.
4. **Giao Diện Người Dùng Hiện Đại (Dark Glassmorphism)**:
   - Tông màu tối neon sang trọng, icon ứng dụng 3D độc quyền.
   - Chế độ xem kép: **Rendered Preview** (hiển thị trực quan như trên GitHub) và **Raw Editor** (chỉnh sửa trực tiếp).
   - Sao chép 1-chạm (Copy to Clipboard) kèm thông báo toast.
   - Lưu trữ và tra cứu lại lịch sử các PR đã tóm tắt.
   - Hướng dẫn sử dụng chi tiết bằng tiếng Việt ngay trong ứng dụng.

---

## 🛠 Hướng Dẫn Cài Đặt & Sử Dụng (Vietnamese Instructions)

### 1. Yêu cầu hệ thống
- macOS, Linux hoặc Windows với **Python 3.9+** (khuyên dùng Python 3.14).
- GitHub CLI (`gh`) đã đăng nhập tài khoản của bạn (để đọc cả repository private và tránh bị giới hạn API rate limit).
- Antigravity CLI (`agy`) đã cài đặt trên máy.

### 2. Khởi chạy ứng dụng

Chạy file bash script:
```bash
./run.sh
```

Hoặc kích hoạt virtualenv thủ công:
```bash
source .venv/bin/activate
python main.py
```

Ứng dụng sẽ tự động mở trình duyệt tại địa chỉ: `http://127.0.0.1:8000`.

### 3. Các bước tóm tắt Pull Request
1. Dán URL của GitHub PR vào ô nhập (ví dụ: `https://github.com/owner/repo/pull/123`).
2. Chọn mô hình AI:
   - **Claude Sonnet 4.6 (Thinking)**: Khuyên dùng cho các PR phức tạp, nhiều diff logic.
   - **Gemini 3.8 Flash**: Khuyên dùng khi cần tốc độ sinh nhanh tức thì.
3. (Tùy chọn) Điền thêm ghi chú như link Figma hoặc lưu ý nghiệp vụ trong ô "Ghi chú thêm".
4. Nhấn **"Tạo PR Description"**.
5. Xem trước bản kết quả, chỉnh sửa nếu cần và nhấn **"Sao Chép Markdown"** để dán vào PR trên GitHub.

---

## 📁 Cấu Trúc Dự Án
```
Auto PR Generator/
├── backend/
│   ├── controllers/
│   │   └── pr_controller.py       # API endpoints cho Parse, Summarize, History
│   ├── models/
│   │   ├── enums.py               # Enums cho Models, Providers, ChangeTypes
│   │   └── pr_model.py            # Pydantic schemas cho PR & Response
│   └── services/
│       ├── ai_service.py          # Service gọi Antigravity AI (Claude/Gemini)
│       ├── github_service.py      # Service trích xuất PR và diff từ GitHub
│       ├── history_service.py     # Service lưu trữ lịch sử tóm tắt (JSON)
│       └── prompt_builder.py      # Xây dựng prompt chuẩn cấu trúc bắt buộc
├── frontend/
│   ├── static/
│   │   ├── assets/
│   │   │   └── icon.jpg           # App icon neon glassmorphism
│   │   ├── css/
│   │   │   └── style.css          # Giao diện Dark Glassmorphism cao cấp
│   │   └── js/
│   │       └── app.js             # Logic xử lý giao diện và gọi API
│   └── templates/
│       └── index.html             # Template HTML chính
├── main.py                        # Entry point FastAPI server
├── requirements.txt               # Danh sách thư viện Python
├── run.sh                         # Script khởi chạy nhanh 1 chạm
└── README.md                      # Tài liệu hướng dẫn sử dụng
```
