#!/usr/bin/env python3
"""超级导师 Super-Tutor — 启动入口。"""

import sys
import os

# 确保项目根目录在路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from frontend.desktop_app import main

if __name__ == "__main__":
    main()
