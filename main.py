import os
import sys
import time
import socket
import threading
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Đảm bảo CWD an toàn khi macOS LaunchServices mở từ Finder (tránh lỗi root / read-only)
if os.getcwd() == "/":
    try:
        os.chdir(os.path.expanduser("~"))
    except Exception:
        pass

from backend.controllers import pr_router

app = FastAPI(
    title="Auto PR Generator",
    description="Ứng dụng Desktop AI tóm tắt Pull Request chuyên nghiệp",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký Controller Router
app.include_router(pr_router)

# Hỗ trợ đường dẫn cả khi chạy mã nguồn và khi đóng gói PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def read_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Auto PR Generator running."}


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "Auto PR Generator"}


def find_available_port(start_port: int = 8000) -> int:
    """Tìm cổng mạng khả dụng để chạy server nền cho Desktop app"""
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port


def wait_for_server(port: int, max_wait: float = 5.0) -> bool:
    start = time.time()
    while time.time() - start < max_wait:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.1)
    return False


def start_desktop_app():
    """Khởi chạy ứng dụng Desktop độc lập (Native Window, không phải trình duyệt web)"""
    port = find_available_port(8000)

    # Chạy FastAPI ở thread ngầm
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="127.0.0.1", port=port, log_level="error"),
        daemon=True,
    )
    server_thread.start()

    wait_for_server(port)

    # Khởi tạo cửa sổ Desktop chuẩn macOS
    try:
        import webview

        window = webview.create_window(
            title="Auto PR Generator",
            url=f"http://127.0.0.1:{port}",
            width=1240,
            height=860,
            min_size=(900, 650),
            background_color="#070a12",
        )
        webview.start()
    except Exception as e:
        print(f"Lỗi khởi chạy cửa sổ Desktop: {e}")
        import webbrowser

        webbrowser.open(f"http://127.0.0.1:{port}")
        server_thread.join()


if __name__ == "__main__":
    if "--server" in sys.argv:
        # Chế độ chạy máy chủ nếu cần
        port = find_available_port(8000)
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        # Chế độ mặc định: Cửa sổ Desktop App độc lập
        start_desktop_app()
