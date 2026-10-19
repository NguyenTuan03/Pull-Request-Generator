import os
import sys
import webbrowser
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.controllers import pr_router

app = FastAPI(
    title="Auto PR Generator",
    description="Ứng dụng AI tóm tắt Pull Request chuyên nghiệp theo cấu trúc chuẩn",
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

# Đường dẫn tệp hỗ trợ cả môi trường phát triển và môi trường đóng gói PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    IS_FROZEN = True
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    IS_FROZEN = False

STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def read_index():
    index_path = os.path.join(TEMPLATES_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Auto PR Generator backend is running. Frontend template not found."}


@app.get("/health")
async def health_check():
    return {"status": "ok", "app": "Auto PR Generator"}


def start_server(port: int = 8000, host: str = "127.0.0.1", open_browser: bool = True):
    url = f"http://{host}:{port}"
    print(f"🚀 Auto PR Generator đang khởi chạy tại: {url}")
    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    if IS_FROZEN:
        # Trong bản build đóng gói PyInstaller, chạy trực tiếp instance app và tắt reload
        uvicorn.run(app, host=host, port=port, reload=False)
        return

    uvicorn.run("main:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    port = 8000
    host = "127.0.0.1"
    no_browser = "--no-browser" in sys.argv
    start_server(port=port, host=host, open_browser=not no_browser)
