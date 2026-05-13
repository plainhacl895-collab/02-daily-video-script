#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch script to update _validate_script method"""

import re

file_path = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\daily-video-script\generate_script.py'

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the _validate_script method
start_line = None
end_line = None

for i, line in enumerate(lines):
    if 'def _validate_script(self, script):' in line:
        start_line = i
    elif start_line is not None and line.strip().startswith('def ') and i > start_line + 5:
        end_line = i
        break

if start_line is None:
    print("ERROR: _validate_script method not found")
    exit(1)

print(f"Found _validate_script at lines {start_line+1}-{end_line}")

# New method
new_method = '''    def _validate_script(self, script):
        """验证脚本质量 - 基于 8 大爆款特点"""
        from viral_validator import ViralScriptValidator
        validator = ViralScriptValidator()
        return validator.validate(script)
    
'''

# Replace
new_lines = lines[:start_line] + [new_method] + lines[end_line:]

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("Patch applied successfully")
