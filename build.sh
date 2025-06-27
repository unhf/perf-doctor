#!/bin/bash
# -*- coding: utf-8 -*-
"""
Performance Doctor 本地构建脚本（macOS 专用）

一键构建本地可执行文件，无需考虑跨平台兼容性
"""

set -e  # 遇到错误立即退出

echo "🚀 Chrome Performance Doctor - 本地构建"
echo "=============================================="

# 检查环境
echo "📋 检查构建环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装 Python3"
    exit 1
fi

if ! command -v pipenv &> /dev/null; then
    echo "❌ pipenv 未安装，请先安装: pip install pipenv"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"
echo "✅ pipenv: $(pipenv --version)"

# 清理旧构建文件
echo ""
echo "🧹 清理旧构建文件..."
rm -rf build/ dist/ *.spec
echo "✅ 清理完成"

# 安装依赖
echo ""
echo "📦 安装/更新依赖..."
pipenv install

# 构建可执行文件
echo ""
echo "🔨 开始构建可执行文件..."
pipenv run pyinstaller \
    --clean \
    --onefile \
    --name perf-doctor \
    --add-data "config.py:." \
    --hidden-import websockets \
    --hidden-import psutil \
    --hidden-import requests \
    perf_doctor.py

# 检查构建结果
echo ""
if [ -f "dist/perf-doctor" ]; then
    echo "✅ 构建成功！"
    echo ""
    echo "📁 可执行文件: dist/perf-doctor"
    echo "📊 文件大小: $(du -h dist/perf-doctor | cut -f1)"
    echo "🔒 权限: $(ls -la dist/perf-doctor | cut -d' ' -f1)"
    
    # 测试可执行文件
    echo ""
    echo "🧪 测试可执行文件..."
    echo "测试帮助信息:"
    ./dist/perf-doctor --help
    
    # 检查可执行权限
    chmod +x dist/perf-doctor
    
    echo ""
    echo "🎉 构建完成！"
    echo ""
    echo "使用方法:"
    echo "  ./dist/perf-doctor --help                  # 查看帮助"
    echo "  ./dist/perf-doctor https://example.com     # 分析单个页面"
    echo "  ./dist/perf-doctor url1 url2 url3         # 批量分析"
    echo ""
    echo "功能特性:"
    echo "  ✅ 自动继承 Chrome 登录状态"
    echo "  ✅ 免登录分析业务页面"
    echo "  ✅ 生成详细性能报告"
    echo "  ✅ 本地一键可执行"
    
else
    echo "❌ 构建失败！"
    echo "请检查上面的错误信息"
    exit 1
fi
