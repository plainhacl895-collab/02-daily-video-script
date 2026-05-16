#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爆款脚本验证器 - 基于 8 大爆款特点
"""

import json
import re


class ViralScriptValidator:
    """爆款脚本验证器"""
    
    def validate(self, script, persona_profile=None):
        """验证脚本质量 - 基于 9 大爆款特点

        Args:
            script: 要验证的脚本文本
            persona_profile: 可选的人设档案dict，用于读取违禁词/偏好句式/语气词
        """
        if persona_profile is None:
            persona_profile = {}
        issues = []
        scores = {}
        
        # 提取正文（去掉标题和标记）
        text = re.sub(r'#.*\n', '', script)
        text = re.sub(r'##.*\n', '', text)
        word_count = len(text.replace(' ', '').replace('\n', ''))
        
        # 1. 黄金 3 秒钩子检查
        hook_section = self._extract_section(script, '开场')
        hook_score = 0
        if hook_section:
            hook_keywords = ['劝退', '别买', '为什么', '怎么办', '今天', '刚',
                           '最近', '发现', '跟你说', '老实说', '有个情况',
                           '有意思', '值得说', '说真的']
            hook_has_keyword = any(kw in hook_section for kw in hook_keywords)
            hook_has_question = '?' in hook_section or '？' in hook_section
            hook_has_number = bool(re.search(r'\d+', hook_section))
            
            if hook_has_keyword:
                hook_score += 3
            if hook_has_question:
                hook_score += 2
            if hook_has_number:
                hook_score += 1
            
            if hook_score < 3:
                issues.append("钩子不够尖锐（缺少反常识/痛点/数据）")
        else:
            issues.append("缺少开场钩子")
        scores['黄金3秒钩子'] = hook_score
        
        # 2. 反差感检查
        contrast_score = 0
        contrast_keywords = ['但', '却', '结果', '没想到', '出乎意料', '相反',
                           '不是...而是', '以为', '其实', '然而', '不过']
        contrast_count = sum(1 for kw in contrast_keywords if kw in text)
        if contrast_count >= 2:
            contrast_score = 3
        elif contrast_count >= 1:
            contrast_score = 2
        else:
            issues.append("缺少反差感（预期vs现实的对比）")
        scores['反差感'] = contrast_score
        
        # 3. 情感共鸣检查
        emotion_score = 0
        emotion_keywords = ['太太', '老公', '夫妻', '家人', '纠结', '犹豫',
                          '痛苦', '焦虑', '担心', '后悔', '庆幸', '终于']
        emotion_count = sum(1 for kw in emotion_keywords if kw in text)
        if emotion_count >= 2:
            emotion_score = 3
        elif emotion_count >= 1:
            emotion_score = 2
        else:
            issues.append("缺少情感共鸣（缺少人物情绪/家庭元素）")
        scores['情感共鸣'] = emotion_score
        
        # 4. 价值输出检查
        value_score = 0
        value_keywords = ['建议', '方法', '技巧', '经验', '教训', '三点',
                        '第一', '第二', '第三', '清单', '对比', '分析']
        value_count = sum(1 for kw in value_keywords if kw in text)
        if value_count >= 3:
            value_score = 3
        elif value_count >= 2:
            value_score = 2
        elif value_count >= 1:
            value_score = 1
        else:
            issues.append("缺少价值输出（缺少具体建议/方法）")
        scores['价值输出'] = value_score
        
        # 5. 真实感检查
        authenticity_score = 0
        has_client_name = bool(re.search(r'[张王李赵刘陈杨黄周吴].*微信', text))
        has_budget = bool(re.search(r'\d+万', text))
        has_community = bool(re.search(r'花园|新城|苑|小区|府|湾', text))
        has_data = bool(re.search(r'\d+套|\d+平|\d+%', text))
        
        if has_client_name:
            authenticity_score += 2
        if has_budget:
            authenticity_score += 1
        if has_community:
            authenticity_score += 1
        if has_data:
            authenticity_score += 1
        
        if authenticity_score < 3:
            issues.append("缺少真实感（缺少具体客户名/数据/小区）")
        scores['真实感'] = authenticity_score
        
        # 6. 节奏感检查
        pacing_score = 0
        has_hook = '## 开场' in script
        has_conflict = '## 冲突' in script or '## 反差' in script or '## 痛点' in script
        has_solution = '## 解决' in script or '## 专业' in script or '## 分析' in script
        has_golden = '## 金句' in script
        has_cta = '## 结尾' in script
        
        section_count = sum([has_hook, has_conflict, has_solution, has_golden, has_cta])
        if section_count >= 4:
            pacing_score = 3
        elif section_count >= 3:
            pacing_score = 2
        elif section_count >= 2:
            pacing_score = 1
        else:
            issues.append("节奏感不足（缺少明确的结构分段）")
        scores['节奏感'] = pacing_score
        
        # 7. 互动钩子检查
        interaction_score = 0
        has_cta_text = '私信' in text or '关注' in text or '点赞' in text or '评论' in text
        has_question = '?' in text or '？' in text
        
        if has_cta_text:
            interaction_score += 2
        if has_question:
            interaction_score += 1
        
        if interaction_score < 2:
            issues.append("缺少互动钩子（缺少引导关注/评论/私信）")
        scores['互动钩子'] = interaction_score
        
        # 8. 人设一致性检查（升级为多维评估）
        persona_score = 0

        # 8a. 违禁词检测（0-1分） — 出现一个即扣分
        forbidden = persona_profile.get("forbidden_words", [
            '家人们', '绝绝子', '震惊', '重磅', '赶紧', '手慢无', '错过不再',
            '必看', '血赚', '抢疯了', '暴涨', '暴跌', '千万别买', '不要错过'
        ])
        found_forbidden = [w for w in forbidden if w in script]
        if not found_forbidden:
            persona_score += 1
        else:
            issues.append(f"人设违禁词：{', '.join(found_forbidden[:3])}")

        # 8b. 偏好句式检测（0-1分） — 匹配朋友聊天式表达
        preferred = persona_profile.get("preferred_patterns", [
            '我建议', '我觉得', '你可以考虑', '不妨看看', '说实话', '说白了',
            '帮你分析', '帮你看清', '搞清楚', '说真的'
        ])
        found_preferred = [p for p in preferred if p in text]
        if len(found_preferred) >= 2:
            persona_score += 1
        elif len(found_preferred) >= 1:
            persona_score += 0  # 有但不加分也不扣分
        else:
            issues.append("人设语言缺失：缺少'我建议/说实话/帮你分析'等柔和表达")

        # 8c. 催促/恐吓/夸大语气检测（0-1分）
        avoid_expr = persona_profile.get("avoid_expressions", {})
        aggressive_tones = (
            avoid_expr.get("urgency", [])
            + avoid_expr.get("hype", [])
            + avoid_expr.get("fear_mongering", [])
        )
        if not aggressive_tones:
            aggressive_tones = ['赶紧下手', '手慢就没了', '再不下手', '再不上车',
                               '以后就买不起了', '爆款', '神盘', '天花板', '顶级']
        found_aggressive = [t for t in aggressive_tones if t in text]
        if not found_aggressive:
            persona_score += 1
        else:
            issues.append(f"语气不当：{', '.join(found_aggressive[:3])}")

        scores['人设一致性'] = persona_score
        
        # 9. 中心思想明确性（新增）
        thesis_score = 0
        # 检查是否有核心观点信号词
        thesis_signals = ['其实就', '说白了', '关键不在于', '真正的问题是', '说到底',
                         '很多人以为', '实际上', '真正原因', '核心逻辑']
        found_thesis = [s for s in thesis_signals if s in text]
        if len(found_thesis) >= 2:
            thesis_score = 3
        elif len(found_thesis) >= 1:
            thesis_score = 2
        else:
            issues.append("中心思想不够明确（缺少'其实/说白了/说到底'等核心观点表达）")
            thesis_score = 1
        scores['中心思想明确性'] = thesis_score

        # 长度验证
        if word_count < 250:
            issues.append(f"脚本太短（{word_count}字，建议300-500字）")
        elif word_count > 600:
            issues.append(f"脚本太长（{word_count}字，建议300-500字）")
        
        # 内部术语验证
        if "【" in script or "】" in script:
            issues.append("包含内部术语（【】）")
        
        # 计算总分
        total_score = sum(scores.values())
        max_score = 27  # 9 项 * 3 分
        
        return {
            "valid": len(issues) == 0,
            "word_count": word_count,
            "issues": issues,
            "scores": scores,
            "total_score": total_score,
            "max_score": max_score,
            "pass_rate": total_score / max_score if max_score > 0 else 0
        }
    
    def _extract_section(self, script, section_name):
        """提取脚本中的某个段落"""
        pattern = rf'## {section_name}[^\n]*\n([^#]*?)(?=## |---|$)'
        match = re.search(pattern, script, re.DOTALL)
        return match.group(1).strip() if match else None
    
    def print_report(self, validation):
        """打印验证报告"""
        print("\n" + "="*50)
        print("[SCRIPT] 爆款脚本验证报告")
        print("="*50)
        
        # 总分
        total = validation['total_score']
        max_score = validation['max_score']
        rate = validation['pass_rate']
        
        print(f"\n总分：{total}/{max_score} ({rate*100:.0f}%)")
        
        if rate >= 0.8:
            print("[PASS] 优质脚本（80% 以上）")
        elif rate >= 0.6:
            print("[WARN] 合格脚本（60-80%）")
        else:
            print("[FAIL] 不合格脚本（60% 以下）")
        
        # 各项得分
        print("\n[SCORES] 各项得分：")
        for name, score in validation['scores'].items():
            bar = '#' * score + '-' * (3 - score)
            print(f"  {name:10s} [{bar}] {score}/3")
        
        # 问题列表
        if validation['issues']:
            print(f"\n[WARN] 发现问题（{len(validation['issues'])}项）：")
            for i, issue in enumerate(validation['issues'], 1):
                print(f"  {i}. {issue}")
        else:
            print("\n[PASS] 无问题")
        
        print("="*50 + "\n")


if __name__ == "__main__":
    import sys
    from pathlib import Path

    validator = ViralScriptValidator()

    if len(sys.argv) > 1:
        # CLI mode: python viral_validator.py <script_file>
        script = Path(sys.argv[1]).read_text(encoding="utf-8")
        persona_path = Path("config/persona.json")
        persona = json.loads(persona_path.read_text(encoding="utf-8")) if persona_path.exists() else {}
        result = validator.validate(script, persona)
        validator.print_report(result)
    else:
        # Test mode
        validator = ViralScriptValidator()

        test_script = """# 1500.0买房，太太和老公意见不统一怎么办？

## 开场（3秒钩子）
今天遇到一对夫妻，为了一套房子吵得不可开交。为什么？

## 冲突描述（15秒）
张越微信和太太来看房，预算1500.0，想在长宁买。
本来以为是一件高兴的事，结果两个人意见完全不一致。
太太觉得某个方面不太满意，但老公觉得价格合适。
两个人看了好几套房子，就是定不下来。

## 解决方案（20秒）
我帮他们做了三件事：
第一，列出了'必须满足'的清单。
第二，列出了'可以妥协'的清单。
第三，让他们各自选出最看重的3个点。

## 金句（15秒）
买房不是一个人的事，家庭意见统一比什么都重要。
记住，房子是给人住的，不是用来吵架的。

## 结尾（7秒）
如果你也在长宁买房遇到家庭分歧，私信我，帮你分析。关注走起来"""

        result = validator.validate(test_script)
        validator.print_report(result)
