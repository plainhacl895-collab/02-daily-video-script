#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix regex in viral_validator.py"""

file_path = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\daily-video-script\viral_validator.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix regex
content = content.replace(
    r"[张王李赵刘陈杨黄周吴]..微信",
    r"[张王李赵刘陈杨黄周吴].*微信"
)
content = content.replace(
    r"花园|新城|苑|小区|府|湾|湾|湾",
    r"花园|新城|苑|小区|府|湾"
)

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed regex patterns")
