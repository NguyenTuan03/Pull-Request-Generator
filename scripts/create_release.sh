#!/bin/bash
set -e

# Auto PR Generator - Local Release & GitHub Draft Release Creator
VERSION="${1:-1.0.0}"
# Loại bỏ ký tự v ở đầu nếu người dùng nhập v1.0.0
VERSION="${VERSION#v}"
TAG="v${VERSION}"
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cd "$PROJECT_DIR"

echo "=========================================================="
echo "   🚀 Chuẩn bị phát hành Auto PR Generator ${TAG}"
echo "=========================================================="

# 1. Kiểm tra GitHub CLI
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) chưa được cài đặt. Vui lòng cài đặt: brew install gh"
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Bạn chưa đăng nhập GitHub CLI. Vui lòng chạy: gh auth login"
    exit 1
fi

# 2. Đóng gói file DMG nếu chưa có
DMG_FILE="dist/Auto-PR-Generator-${TAG}.dmg"
if [ ! -f "$DMG_FILE" ]; then
    echo "🔨 Chưa tìm thấy ${DMG_FILE}, đang tiến hành đóng gói..."
    ./scripts/build_dmg.sh "$VERSION"
fi

# 3. Tạo Git Tag cục bộ
echo "🏷️ Kiểm tra Git Tag ${TAG}..."
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo "ℹ️ Tag ${TAG} đã tồn tại."
else
    echo "🔖 Đang tạo Git Tag ${TAG}..."
    git tag -a "$TAG" -m "Release ${TAG}"
    echo "📤 Đang đẩy tag ${TAG} lên GitHub..."
    git push origin "$TAG" || true
fi

# 4. Tạo Release Notes
RELEASE_NOTES="## 🚀 Auto PR Generator ${TAG}

Ứng dụng AI tóm tắt Pull Request GitHub tự động theo cấu trúc chuẩn chuyên nghiệp.

### 🌟 Tính năng nổi bật
- 🤖 **AI Engine**: Tích hợp Claude Sonnet 4.6 (Thinking) & Gemini 3.8 Flash qua Antigravity.
- 📑 **Cấu trúc PR chuẩn**: Tự động phân loại \`## What\`, \`## Why\`, \`## How to QA?\`, \`## Types of changes\`, \`## Automation tests\`.
- 🎨 **Giao diện hiện đại**: Dark Glassmorphism, tab kép xem trước Rendered Preview & Raw Editor.
- ⚡ **Tiện ích**: 1-click Copy Markdown, xem thống kê diff, lưu lịch sử tóm tắt.
- 🍏 **Hỗ trợ macOS**: Tệp cài đặt DMG tiện lợi kèm kéo-thả vào Applications.

### 💻 Hướng dẫn cài đặt trên macOS
1. Tải tệp \`${DMG_FILE##*/}\` bên dưới.
2. Mở tệp DMG và kéo biểu tượng **Auto PR Generator** vào thư mục **Applications**.
3. Khởi chạy ứng dụng từ Spotlight hoặc Launchpad."

# 5. Tạo GitHub Draft Release kèm file DMG
echo "📦 Đang tạo Draft Release trên GitHub với file ${DMG_FILE}..."
gh release create "$TAG" "$DMG_FILE" \
    --title "Auto PR Generator ${TAG}" \
    --notes "$RELEASE_NOTES" \
    --draft

echo "=========================================================="
echo "   🎉 TẠO BẢN DRAFT RELEASE THÀNH CÔNG TRÊN GITHUB!"
echo "   Bạn có thể xem và kiểm tra bản nháp tại:"
gh release view "$TAG" --web 2>/dev/null || echo "   https://github.com/$(gh repo view --json nameWithOwner -q .nameWithOwner)/releases"
echo "=========================================================="
