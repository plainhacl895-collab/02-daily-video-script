#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Patch script to inject compliance filter into generate_script.py"""

file_path = r'C:\Users\Huawei\.openclaw\workspace-tuantuan\skills\daily-video-script\generate_script.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加合规过滤方法（插入在 auto_fix 方法之后）
compliance_method = '''
    def apply_compliance_filter(self, script):
        """平台合规过滤 - 自动清洗限流风险内容"""
        original = script
        
        # 规则 1: 敏感词替换（投资/炒房/升值等）
        sensitive_map = {
            '投资': '资产配置',
            '炒房': '房产配置',
            '升值': '保值',
            '首付贷': '资金规划',
            '零首付': '低门槛',
            '暴涨': '市场回暖',
            '抄底': '入手时机',
            '限购': '政策调整',
        }
        for old, new in sensitive_map.items():
            script = script.replace(old, new)
        
        # 规则 2: 绝对化用语软化（千万别/绝对/100%等）
        absolute_map = {
            '千万别买': '建议谨慎考虑',
            '千万别踩': '建议避开',
            '稳赚不赔': '需综合评估',
            '100%': '大概率',
            '绝对': '相对',
            '一定': '通常',
            '必须': '建议',
        }
        for old, new in absolute_map.items():
            script = script.replace(old, new)
        
        # 规则 3: 引流话术替换（小红书/视频号严打直接引流）
        diversion_map = {
            '加我微信': '评论区留言',
            '扫码领': '后台获取',
            '私信我': '评论区交流',
            '私信聊聊': '评论区聊',
            '后台告诉我': '评论区留言',
            '送你一份': '分享一份',
            '关注我': '点赞收藏',
        }
        for old, new in diversion_map.items():
            script = script.replace(old, new)
        
        # 规则 4: 价格/政策承诺防护
        if '保证' in script or '承诺' in script:
            script = script.replace('保证', '建议').replace('承诺', '规划')
        
        # 记录修改日志
        if script != original:
            print("[COMPLIANCE] 已应用合规过滤（替换敏感词/软化绝对用语/替换引流话术）")
        
        return script

'''

# 插入位置：在 "def run(self, date_str=None):" 之前
insert_marker = '    def run(self, date_str=None):'
if insert_marker in content:
    content = content.replace(insert_marker, compliance_method + insert_marker)
    print("[PATCH] 已注入 apply_compliance_filter 方法")
else:
    print("[ERROR] 未找到插入位置")
    exit(1)

# 2. 修改 run 方法，在保存前调用合规过滤
old_save_block = '''        # 5. 保存文件
        output_path = self.save_script(script, target_date.strftime("%Y-%m-%d"))
        print(f"\\n脚本已保存：{output_path}")'''

new_save_block = '''        # 5. 合规过滤（平台限流防护）
        script = self.apply_compliance_filter(script)
        
        # 6. 保存文件
        output_path = self.save_script(script, target_date.strftime("%Y-%m-%d"))
        print(f"\\n脚本已保存：{output_path}")'''

if old_save_block in content:
    content = content.replace(old_save_block, new_save_block)
    print("[PATCH] 已集成合规过滤到主流程")
else:
    print("[WARN] 未找到保存块，尝试备用匹配")
    # 备用匹配
    content = content.replace(
        '        # 5. 保存文件\n        output_path = self.save_script(script, target_date.strftime("%Y-%m-%d"))',
        new_save_block
    )

# 写回文件
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("[PATCH] 合规过滤引擎注入完成")
