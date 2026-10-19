#!/bin/bash
set -e

# Auto PR Generator - macOS Desktop App & DMG Builder Script
VERSION="${1:-1.0.0}"
APP_NAME="Auto PR Generator"
DMG_NAME="Auto-PR-Generator-v${VERSION}.dmg"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

echo "=========================================================="
echo "   🔨 Bắt đầu đóng gói Desktop App ${APP_NAME} v${VERSION} (.dmg) "
echo "=========================================================="

# 1. Kích hoạt môi trường ảo Python
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 2. Tạo AppIcon.icns nếu chưa có
ICNS_PATH="frontend/static/assets/AppIcon.icns"
ICON_JPG="frontend/static/assets/icon.jpg"

if [ ! -f "$ICNS_PATH" ] && [ -f "$ICON_JPG" ]; then
    echo "🎨 Đang tạo biểu tượng macOS AppIcon.icns..."
    mkdir -p build/icon.iconset
    sips -s format png "$ICON_JPG" --out build/base.png > /dev/null
    sips -z 16 16     build/base.png --out build/icon.iconset/icon_16x16.png > /dev/null
    sips -z 32 32     build/base.png --out build/icon.iconset/icon_16x16@2x.png > /dev/null
    sips -z 32 32     build/base.png --out build/icon.iconset/icon_32x32.png > /dev/null
    sips -z 64 64     build/base.png --out build/icon.iconset/icon_32x32@2x.png > /dev/null
    sips -z 128 128   build/base.png --out build/icon.iconset/icon_128x128.png > /dev/null
    sips -z 256 256   build/base.png --out build/icon.iconset/icon_128x128@2x.png > /dev/null
    sips -z 256 256   build/base.png --out build/icon.iconset/icon_256x256.png > /dev/null
    sips -z 512 512   build/base.png --out build/icon.iconset/icon_256x256@2x.png > /dev/null
    sips -z 512 512   build/base.png --out build/icon.iconset/icon_512x512.png > /dev/null
    sips -z 1024 1024 build/base.png --out build/icon.iconset/icon_512x512@2x.png > /dev/null
    iconutil -c icns build/icon.iconset -o "$ICNS_PATH"
    rm -rf build/icon.iconset build/base.png
    echo "✓ Đã tạo $ICNS_PATH"
fi

# 3. Biên dịch Desktop App bằng PyInstaller
echo "⚙️ Đang đóng gói Desktop App với PyInstaller..."
rm -rf "dist/${APP_NAME}.app" "dist/${APP_NAME}"

pyinstaller \
    --name "${APP_NAME}" \
    --windowed \
    --noconfirm \
    --clean \
    --icon "${ICNS_PATH}" \
    --add-data "frontend:frontend" \
    --add-data "backend:backend" \
    --collect-all "webview" \
    --hidden-import "webview" \
    --hidden-import "webview.platforms.cocoa" \
    --hidden-import "objc" \
    --hidden-import "WebKit" \
    --hidden-import "AppKit" \
    --hidden-import "Foundation" \
    --hidden-import "uvicorn.logging" \
    --hidden-import "uvicorn.loops" \
    --hidden-import "uvicorn.loops.auto" \
    --hidden-import "uvicorn.protocols.http.auto" \
    --hidden-import "uvicorn.protocols.websockets.auto" \
    --hidden-import "jinja2" \
    --hidden-import "httpx" \
    main.py

echo "✓ Đã tạo ứng dụng Desktop: dist/${APP_NAME}.app"

# 4. Đóng gói file DMG bằng hdiutil
echo "📀 Đang tạo tệp disk image (.dmg)..."
STAGING_DIR="dist/dmg_staging"
rm -rf "$STAGING_DIR" "dist/${DMG_NAME}"
mkdir -p "$STAGING_DIR"

# Copy file .app vào thư mục staging
cp -R "dist/${APP_NAME}.app" "$STAGING_DIR/"

# Tạo shortcut liên kết thư mục /Applications
ln -s /Applications "$STAGING_DIR/Applications"

# Tạo tệp DMG nén UDZO
hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "$STAGING_DIR" \
    -ov \
    -format UDZO \
    "dist/${DMG_NAME}"

# Dọn dẹp staging
rm -rf "$STAGING_DIR"

echo "=========================================================="
echo "   🎉 ĐÓNG GÓI THÀNH CÔNG!"
echo "   Tệp DMG Desktop App: dist/${DMG_NAME}"
ls -lh "dist/${DMG_NAME}"
echo "=========================================================="
