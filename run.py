#!/usr/bin/env python3
"""
穿搭灵感助手启动脚本
"""
import os
import sys

# 确保app目录在路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "app"))

if __name__ == "__main__":
    os.system("streamlit run app/main.py")
