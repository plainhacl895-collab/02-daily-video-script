#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人设管理器 - 确保短视频脚本的人设一致性
负责：策略决策、人设检查、内容历史追踪
"""

import json
import re
import os
from datetime import date, datetime, timedelta
from pathlib import Path
from collections import Counter


class PersonaManager:
    """人设管理器 — 每条脚本都要经过它的审核"""

    def __init__(self):
        self.skill_dir = Path(__file__).parent
        self.profile_path = self.skill_dir / "persona_profile.json"
        self.history_path = self.skill_dir / "content_history.json"
        self.profile = self.load_profile()
        self.history = self.load_history()

    def load_profile(self):
        """加载人设档案"""
        try:
            with open(self.profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PERSONA] 加载人设档案失败：{e}，使用默认值")
            return self._default_profile()

    def load_history(self):
        """加载内容历史"""
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[PERSONA] 加载内容历史失败：{e}，使用空历史")
            return self._default_history()

    def save_history(self):
        """保存内容历史"""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[PERSONA] 保存内容历史失败：{e}")

    def get_today_strategy(self, target_date=None):
        """根据历史决定今天该用的策略、支柱和角度，防止重复"""
        if target_date is None:
            target_date = date.today()

        records = self.history.get("records", [])
        last_strategies = self.history.get("last_strategies", [])
        last_angles = self.history.get("last_angles", [])
        pillar_dist = self.history.get("pillar_distribution", {"Market": 0, "Property": 0, "Story": 0})

        # 1. 决定内容支柱 (3:4:3 目标)
        pillar = self._select_pillar(pillar_dist)

        # 2. 决定策略（优先核心，避免重复）
        strategy = self._select_strategy(last_strategies)

        # 3. 确定最近用过的角度，避免重复
        recent_angles = last_angles[:3] if last_angles else []

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "pillar": pillar,
            "strategy": strategy,
            "recent_angles": recent_angles,
            "core_lanes": self.profile.get("core_lanes", ["专业筛选", "避坑指南"]),
            "secondary_lanes": self.profile.get("secondary_lanes", ["反差拒绝"]),
        }

    def _select_pillar(self, pillar_dist):
        """选择内容支柱，向 3:4:3 目标收敛"""
        target = {"Market": 0.30, "Property": 0.40, "Story": 0.30}

        # 计算当前与目标的差距（比例差最大的优先）
        total = sum(pillar_dist.values()) or 1
        current_pct = {k: pillar_dist.get(k, 0) / total for k in target}

        gaps = {k: target[k] - current_pct.get(k, 0) for k in target}
        pillar = max(gaps, key=gaps.get)
        return pillar

    def _select_strategy(self, last_strategies):
        """确定性选择生成策略，核心策略优先，避免连续重复"""
        core = self.profile.get("core_lanes", ["专业筛选", "避坑指南"])
        secondary = self.profile.get("secondary_lanes", ["反差拒绝"])
        all_valid = core + secondary

        # 统计历史中各策略出现次数（最近14天）
        records = self.history.get("records", [])
        strategy_counts = {}
        for r in records:
            s = r.get("strategy", "")
            if s:
                strategy_counts[s] = strategy_counts.get(s, 0) + 1

        last_used = last_strategies[0] if last_strategies else None

        # 规则1：如果上次用了核心A，这次优先核心B
        if last_used in core:
            other_core = [s for s in core if s != last_used]
            if other_core:
                return other_core[0]

        # 规则2：如果两条核心均已用到，按 5:1 比例穿插副线
        # 即每 6 天中：3 天核心A、2 天核心B、1 天副线
        total_count = sum(strategy_counts.get(s, 0) for s in all_valid)
        secondary_count = sum(strategy_counts.get(s, 0) for s in secondary)

        # 副线占比目标 20%，若实际 < 15% 则本次选副线
        if total_count > 0 and secondary_count / max(total_count, 1) < 0.15:
            # 选最久未用的副线
            for s in secondary:
                return s

        # 规则3：选核心中历史次数较少的那个（负载均衡）
        core_counts = {s: strategy_counts.get(s, 0) for s in core}
        min_core = min(core, key=lambda s: core_counts.get(s, 0))
        return min_core

    def get_pillar_for_shining_type(self, shining_type):
        """将闪光点类型映射到内容支柱"""
        pillar_map = {
            "反差拒绝": "Story",
            "专业筛选": "Property",
            "家庭决策": "Story",
            "数据对比": "Property",
            "捡漏机会": "Property",
            "避坑指南": "Market",
        }
        return pillar_map.get(shining_type, "Property")

    def check_persona_alignment(self, script):
        """
        检查脚本是否符合同一个人设
        返回: {"aligned": bool, "issues": [...], "score": int}
        """
        issues = []
        score = 0
        max_score = 12

        # 1. 违禁词检测 (3分)
        forbidden = self.profile.get("forbidden_words", [])
        found_forbidden = [w for w in forbidden if w in script]
        if not found_forbidden:
            score += 3
        else:
            issues.append(f"包含违禁词：{', '.join(found_forbidden)}")
            score += max(0, 3 - len(found_forbidden))

        # 2. 偏好句式检测 (3分)
        preferred = self.profile.get("preferred_patterns", [])
        found_preferred = [p for p in preferred if p in script]
        if len(found_preferred) >= 2:
            score += 3
        elif len(found_preferred) >= 1:
            score += 2
        else:
            issues.append("缺少偏好句式（如'我建议/你可以考虑'等柔和表达）")
            score += 1

        # 3. 催促/恐吓语气检测 (3分)
        avoid_urgency = self.profile.get("avoid_expressions", {}).get("urgency", [])
        avoid_hype = self.profile.get("avoid_expressions", {}).get("hype", [])
        avoid_fear = self.profile.get("avoid_expressions", {}).get("fear_mongering", [])
        all_bad_tones = avoid_urgency + avoid_hype + avoid_fear
        found_bad_tone = [t for t in all_bad_tones if t in script]
        if not found_bad_tone:
            score += 3
        else:
            issues.append(f"含催促/夸大语气：{', '.join(found_bad_tone)}")
            score += max(0, 3 - len(found_bad_tone))

        # 4. 价值观对齐 (3分)
        values = self.profile.get("core_values", [])
        # 从 core_values 提取关键词作为检测信号
        stop_words = {"的", "是", "而", "在", "和", "与", "或", "了", "着", "过", "不", "都", "也", "就", "才"}
        value_signals = set()
        for v in values:
            # 按标点拆成短语，取 2-3 字的有意义片段
            parts = re.split(r'[，。！？、；：\s]', v)
            for part in parts:
                part = part.strip()
                if 2 <= len(part) <= 6 and part not in stop_words:
                    value_signals.add(part)
        value_signals = list(value_signals)[:10]  # 上限 10 个
        found_values = [v for v in value_signals if v in script]
        if len(found_values) >= 2:
            score += 3
        elif len(found_values) >= 1:
            score += 2
        else:
            issues.append("未体现核心价值观（筛选/真实/站在客户立场）")
            score += 1

        return {
            "aligned": len(issues) == 0,
            "issues": issues,
            "score": score,
            "max_score": max_score,
            "pass_rate": score / max_score if max_score > 0 else 0,
        }

    def record_generation(self, meta, target_date=None):
        """记录本次生成到历史"""
        if target_date is None:
            target_date = date.today()
        today = target_date.strftime("%Y-%m-%d")

        record = {
            "date": today,
            "strategy": meta.get("strategy", ""),
            "pillar": meta.get("pillar", ""),
            "shining_type": meta.get("shining_type", ""),
            "angle": meta.get("angle", ""),
            "client_context": meta.get("client_context", ""),
            "persona_score": meta.get("persona_score", 0),
            "pleasure_score": meta.get("pleasure_score", 0),
        }

        records = self.history.get("records", [])
        # 如果今天已有记录，替换
        existing_idx = None
        for i, r in enumerate(records):
            if r.get("date") == today:
                existing_idx = i
                break

        if existing_idx is not None:
            records[existing_idx] = record
        else:
            records.append(record)

        # 只保留最近 N 条
        max_window = self.history.get("max_history_window", 14)
        records = records[-max_window:]
        self.history["records"] = records

        # 更新最近策略和角度
        strategies = [r.get("strategy", "") for r in records if r.get("strategy")]
        self.history["last_strategies"] = list(reversed(strategies[-5:]))

        angles = [r.get("angle", "") for r in records if r.get("angle")]
        self.history["last_angles"] = list(reversed(angles[-5:]))

        # 更新支柱分布
        all_records = records
        pillar_counts = {"Market": 0, "Property": 0, "Story": 0}
        for r in all_records:
            p = r.get("pillar", "")
            if p in pillar_counts:
                pillar_counts[p] += 1
        self.history["pillar_distribution"] = pillar_counts

        self.save_history()
        print(f"[PERSONA] 已记录 {today} 的生成：{record.get('strategy', '')} / {record.get('pillar', '')} / {record.get('angle', '')}")

    def _default_profile(self):
        return {
            "name": "专业买手·参谋",
            "core_lanes": ["专业筛选", "避坑指南"],
            "secondary_lanes": ["反差拒绝"],
            "disabled_lanes": ["捡漏机会", "数据对比"],
            "language_style": "朋友聊天式",
            "forbidden_words": ["家人们", "绝绝子", "震惊", "重磅", "赶紧", "手慢无"],
            "preferred_patterns": ["我建议", "我觉得", "你可以考虑", "不妨看看"],
            "core_values": ["不催单", "帮客户筛选而非推销"],
            "persona_golden_sentences": [
                "我不帮你做决定，我帮你看清选项。",
                "好房子不是推销出来的，是筛选出来的。"
            ],
            "avoid_expressions": {
                "urgency": ["赶紧下手", "手慢就没了"],
                "hype": ["爆款", "神盘"],
                "bragging": ["我做了十年"],
                "fear_mongering": ["再不上车"]
            }
        }

    def _default_history(self):
        return {
            "records": [],
            "pillar_distribution": {"Market": 0, "Property": 0, "Story": 0},
            "last_strategies": [],
            "last_angles": [],
            "max_history_window": 14,
            "min_gap_same_strategy": 1,
            "min_gap_same_angle": 3,
        }
