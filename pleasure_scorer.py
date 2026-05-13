#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
爽点评分器 — 检测内容中的「信息结构密度」，不依赖语义理解

核心假设：爽感来自信息结构，不是话题类型。
五种可被正则检测的爽点结构：数字落差、认知反转、具体排除、可复用方法、闭环决策
"""

import re


class PleasureScorer:
    """爽点评分器 — 满分 12 分"""

    def score(self, content):
        """
        对一段内容做爽点评分
        返回: {"total": int, "details": dict, "verdict": str}
        """
        if not content:
            return self._empty_result()

        scores = {}
        evidence = {}

        # 1. 数字落差（0-3分）
        s, e = self._score_number_gap(content)
        scores["数字落差"] = s
        evidence["数字落差"] = e

        # 2. 认知反转（0-3分）
        s, e = self._score_cognitive_reversal(content)
        scores["认知反转"] = s
        evidence["认知反转"] = e

        # 3. 具体排除（0-2分）
        s, e = self._score_specific_exclusion(content)
        scores["具体排除"] = s
        evidence["具体排除"] = e

        # 4. 可复用方法（0-2分）
        s, e = self._score_reusable_method(content)
        scores["可复用方法"] = s
        evidence["可复用方法"] = e

        # 5. 闭环决策（0-2分）
        s, e = self._score_closed_loop(content)
        scores["闭环决策"] = s
        evidence["闭环决策"] = e

        total = sum(scores.values())
        verdict = self._verdict(total)

        return {
            "total": total,
            "max": 12,
            "scores": scores,
            "evidence": evidence,
            "verdict": verdict,
            "can_be_main_video": total >= 5,
            "has_any_pleasure_point": total >= 2,
        }

    # ── 结构一：数字落差 ────────────────────────────

    def _score_number_gap(self, content):
        """检测可比数字对之间的显著差距（≥15%）"""
        numbers = re.findall(r'(\d+(?:\.\d+)?)\s*(万|套|平|折|%|成|倍|个|年|月|天|层)', content)
        if len(numbers) < 2:
            return 0, []

        pairs_found = []
        for i in range(len(numbers)):
            for j in range(i + 1, len(numbers)):
                n1, u1 = float(numbers[i][0]), numbers[i][1]
                n2, u2 = float(numbers[j][0]), numbers[j][1]

                # 同单位才可比
                if u1 != u2:
                    continue
                if n1 == 0 or n2 == 0:
                    continue

                gap = abs(n1 - n2) / max(n1, n2)
                if gap >= 0.15:
                    pairs_found.append({
                        "pair": f"{numbers[i][0]}{u1} vs {numbers[j][0]}{u2}",
                        "gap": f"{gap*100:.0f}%",
                    })

        if len(pairs_found) >= 2:
            return 3, pairs_found[:3]
        elif len(pairs_found) == 1:
            return 2, pairs_found
        else:
            # 至少有一个"数字+单位"也算 1 分（有数据意识）
            single_numbers = re.findall(r'\d+\.?\d*\s*(万|套|平|折|%)', content)
            return (1, []) if single_numbers else (0, [])

    # ── 结构二：认知反转 ────────────────────────────

    def _score_cognitive_reversal(self, content):
        """检测 '以为A → 实际B' 的结构"""
        belief_words = r'(以为|觉得|本来|原本|原来以为|一直以为|看上去|听起来|表面上)'
        turn_words = r'(但|但是|结果|实际上|其实|没想到|才发现|后来|回过头看)'

        pattern = belief_words + r'.{0,40}' + turn_words
        matches = re.findall(pattern, content)

        if len(matches) >= 2:
            return 3, [m if isinstance(m, str) else "".join(m) for m in matches[:3]]
        elif len(matches) == 1:
            return 2, [matches[0] if isinstance(matches[0], str) else "".join(matches[0])]
        else:
            # 降级：转折词前后各有15个字符以上的实际内容
            turn_match = re.search(r'(.{15,})(' + turn_words + r')(.{15,})', content)
            if turn_match and len(content) > 80:
                return 1, [f"检测到转折结构：...{turn_match.group(2)}..."]
            return 0, []

    # ── 结构三：具体排除 ────────────────────────────

    def _score_specific_exclusion(self, content):
        """检测 '否定 + 具体对象 + 具体原因' 的结构"""
        negations = r'(排除|pass|跳过|不要|不建议|不能要|不合适|不推荐|放弃了)'

        # 强模式：否定词 + 具体对象 + 原因词（支持多分隔符）
        strong = re.findall(
            negations + r'.{0,30}(因为|原因是|主要是|问题在于|毛病是|——|实测)',
            content,
        )

        if strong:
            return 2, [s if isinstance(s, str) else "".join(s) for s in strong[:2]]

        # 弱模式：至少有一个否定 + 具体对象（不要求原因）
        weak = re.findall(negations + r'.{0,20}(那套|这套|房子|楼层|户型|地段|小区)', content)
        if weak:
            return 1, [w if isinstance(w, str) else "".join(w) for w in weak[:2]]

        # 再弱一点：内容同时包含否定词和具体名词（距离不限）
        if re.search(negations, content) and re.search(r'(那套|这套|房子|楼层|户型|地段|小区|临街|采光|噪音)', content):
            return 1, ["检测到否定+具体对象"]

        return 0, []

    # ── 结构四：可复用方法 ────────────────────────────

    def _score_reusable_method(self, content):
        """检测 '序号 + 动作 + 判断标准' 的结构"""
        # 有序号 + 动作
        step_action = re.findall(
            r'(第[一二三四五12345]|首先|其次|最后|[12345]\.)'
            r'.{0,40}'
            r'(看|查|对比|算|拉|问|确认|排除|筛选)',
            content,
        )

        # 有判断标准（拿什么当标尺）
        has_criterion = bool(re.search(
            r'(标准|原则|底线|红线|最重要|关键|核心|就看|盯住|记住|就看这)',
            content,
        ))

        if step_action and has_criterion:
            return 2, [s if isinstance(s, str) else "".join(s) for s in step_action[:2]]
        elif step_action:
            return 1, [s if isinstance(s, str) else "".join(s) for s in step_action[:1]]
        elif has_criterion and len(content) > 100:
            return 1, ["检测到判断标准"]
        else:
            return 0, []

    # ── 结构五：闭环决策 ────────────────────────────

    def _score_closed_loop(self, content):
        """检测 '人物 + 决定词 + 具体选项' 的结构"""
        person = r'(他|她|客户|先生|女士|太太|老公|最后|当场|看完|听完)'
        decision = r'(决定|选择|放弃|选了|定下|锁定|要了|排除|Pass|筛掉)'
        target = r'(那套|这套|房子|房源|那个|这个|户型|直接|当场|马上)'

        # 强模式：人物 + 决定词 + 目标，距离 ≤50 字
        strong = re.findall(
            person + r'.{0,30}' + decision + r'.{0,20}' + target,
            content,
        )
        if strong:
            return 2, [s if isinstance(s, str) else "".join(s) for s in strong[:2]]

        # 弱模式：人物 + 决定词（不要求目标）
        weak = re.findall(person + r'.{0,30}' + decision, content)
        if weak:
            return 1, [w if isinstance(w, str) else "".join(w) for w in weak[:1]]

        return 0, []

    # ── 判断 ────────────────────────────────────────

    def _verdict(self, total):
        if total >= 9:
            return "爆款潜力 — 5种爽点结构密集，值得重点制作"
        elif total >= 6:
            return "有爽感 — 至少2-3种爽点结构，观众会有获得感"
        elif total >= 3:
            return "及格 — 有基本的信息密度，但不够尖锐"
        elif total >= 1:
            return "平淡 — 信息密度低，建议补充具体数据或客户决策"
        else:
            return "空洞 — 无任何爽点结构，建议放弃此素材，切换模式 2/3"

    def _empty_result(self):
        return {
            "total": 0,
            "max": 12,
            "scores": {k: 0 for k in self._dimensions()},
            "evidence": {k: [] for k in self._dimensions()},
            "verdict": "空洞 — 素材为空",
            "can_be_main_video": False,
            "has_any_pleasure_point": False,
        }

    def _dimensions(self):
        return ["数字落差", "认知反转", "具体排除", "可复用方法", "闭环决策"]

    def print_report(self, result):
        """打印爽点评分报告"""
        print("\n" + "=" * 50)
        print("[PLEASURE] 爽点结构评分报告")
        print("=" * 50)
        print(f"总分：{result['total']}/{result['max']}")
        print(f"判断：{result['verdict']}")
        print(f"可作为主视频素材：{'是' if result['can_be_main_video'] else '否'}")

        print("\n各项得分：")
        for dim, score in result["scores"].items():
            bar = "#" * score + "-" * (self._max_for(dim) - score)
            evidence = result["evidence"].get(dim, [])
            ev_str = ""
            if evidence and isinstance(evidence, list) and evidence:
                first = evidence[0]
                if isinstance(first, str):
                    ev_str = f"  → {first[:60]}"
                elif isinstance(first, dict):
                    ev_str = f"  → {first.get('pair', first.get('gap', str(first)[:60]))}"
            print(f"  {dim:8s} [{bar}] {score}/{self._max_for(dim)}{ev_str}")

        print("=" * 50 + "\n")

    def _max_for(self, dimension):
        max_map = {"数字落差": 3, "认知反转": 3, "具体排除": 2, "可复用方法": 2, "闭环决策": 2}
        return max_map.get(dimension, 3)


# ── 命令行测试入口 ────────────────────────────────

if __name__ == "__main__":
    scorer = PleasureScorer()

    test_cases = [
        # 强素材：五种结构都齐
        (
            "强素材",
            "他本来以为800万在静安只能买老破小，结果我把近三个月成交数据拉出来一对比，"
            "发现同户型有一套挂了8个月没卖掉，成交价比挂牌低了12%。三套里我直接帮他排除"
            "了临街那套——因为晚上10点实测噪音65分贝，不适合睡眠浅的人。我就让他看三点："
            "第一，同小区近三个月实际成交价；第二，同户型挂牌时长；第三，房东换房动机。"
            "他看完数据，当场决定不买那套挂8个月的了，直接去谈上个月刚成交的同户型。"
        ),
        # 中等素材：只有两三种结构
        (
            "中等素材",
            "今天帮张先生看房，预算500万，在长宁。他看中了达安花园的一套房子，"
            "但我觉得价格偏高，帮他对比了周边几个小区。最后推荐了另一个性价比更高的选择。"
        ),
        # 弱素材：基本无结构
        (
            "弱素材",
            "今天带客户看了几套房子，都不太满意。继续跟进中。"
        ),
        # 纯数据无故事
        (
            "纯数据",
            "这套1500万，那套1200万，面积差了30平，单价差2万。"
        ),
    ]

    for name, content in test_cases:
        print(f"\n{'='*60}")
        print(f"测试：{name}")
        print(f"内容：{content[:80]}...")
        result = scorer.score(content)
        scorer.print_report(result)
