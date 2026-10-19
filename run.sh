#!/bin/bash
# Auto PR Generator - Start Script
cd "$(dirname "$0")"

echo "=============================================="
echo "   🚀 Auto PR Generator (AI-Powered)          "
echo "=============================================="

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "📦 Đang tạo virtual environment (.venv)..."
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
else
    source .venv/bin/activate
fi

echo "🌐 Khởi động Web App tại http://127.0.0.1:8000 ..."
python main.py
