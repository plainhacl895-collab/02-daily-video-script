#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
短视频引擎 — 策略决策 + 记录 + 反馈分析
取代旧 persona_manager.py + generate_script.py 中的记录逻辑
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path
from collections import Counter, defaultdict


class VideoEngine:
    """短视频系统引擎"""

    def __init__(self):
        self.root = Path(__file__).parent
        self.config_dir = self.root / "config"
        self.data_dir = self.root / "data"
        self.config_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)

        self.persona = self._load_persona()
        self.history = self._load_history()

    # ═══ 加载 ═══

    def _load_persona(self):
        path = self.config_dir / "persona.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        old = self.root / "persona_profile.json"
        if old.exists():
            data = json.loads(old.read_text(encoding="utf-8"))
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            return data
        return self._default_persona()

    def _load_history(self):
        path = self.data_dir / "history.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return self._default_history()

    def _default_persona(self):
        return {
            "name": "专业买手·参谋",
            "core_lanes": ["专业筛选", "避坑指南"],
            "secondary_lanes": ["反差拒绝"],
            "disabled_lanes": ["捡漏机会", "数据对比"],
            "language_style": "朋友聊天式",
            "forbidden_words": [
                "家人们", "绝绝子", "震惊", "重磅", "赶紧", "手慢无",
                "错过不再", "必看", "血赚", "抢疯了", "暴涨", "暴跌"
            ],
            "preferred_patterns": [
                "我建议", "我觉得", "你可以考虑", "不妨看看",
                "如果不介意", "说实话", "说白了", "其实就一点"
            ],
            "core_values": [
                "不催单，帮客户筛选而非推销",
                "用真实数据说话，不编造",
                "承认不完美，没有十全十美的房子",
                "站在客户立场想问题"
            ],
            "persona_golden_sentences": [
                "我不帮你做决定，我帮你看清选项。",
                "好房子不是推销出来的，是筛选出来的。",
                "买不买无所谓，先让你知道真实情况。",
                "说到底，房子是给人住的，合适比便宜重要。"
            ],
            "avoid_expressions": {
                "urgency": ["赶紧下手", "手慢就没了", "再不下手就晚了"],
                "hype": ["爆款", "神盘", "顶级", "天花板"],
                "bragging": ["我做了十年", "专业团队", "独家资源"],
                "fear_mongering": ["再不上车", "以后就买不起了", "房价要暴涨了"]
            }
        }

    def _default_history(self):
        return {
            "records": [],
            "pillar_distribution": {"Market": 0, "Property": 0, "Story": 0},
            "last_strategies": [],
            "last_angles": [],
            "max_window": 30,
        }

    def _save_history(self):
        path = self.data_dir / "history.json"
        path.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")

    # ═══ 策略决策 ═══

    def get_today_strategy(self, target_date=None):
        if target_date is None:
            target_date = date.today()

        records = self.history.get("records", [])
        last_strategies = self.history.get("last_strategies", [])
        last_angles = self.history.get("last_angles", [])
        pillar_dist = self.history.get("pillar_distribution", {})

        pillar = self._select_pillar(pillar_dist)
        strategy = self._select_strategy(last_strategies)
        recent_angles = last_angles[:3] if last_angles else []

        label = {"Market": "市场宏观", "Property": "房子板块", "Story": "人物故事"}

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "pillar": pillar,
            "pillar_label": label.get(pillar, pillar),
            "strategy": strategy,
            "recent_angles": recent_angles,
            "recent_performance": self._recent_performance(7),
            "core_lanes": self.persona.get("core_lanes", []),
            "secondary_lanes": self.persona.get("secondary_lanes", []),
        }

    def _select_pillar(self, pillar_dist):
        target = {"Market": 0.30, "Property": 0.40, "Story": 0.30}
        total = sum(pillar_dist.values()) or 1
        current = {k: pillar_dist.get(k, 0) / total for k in target}
        gaps = {k: target[k] - current.get(k, 0) for k in target}
        return max(gaps, key=gaps.get)

    def _select_strategy(self, last_strategies):
        core = self.persona.get("core_lanes", ["专业筛选", "避坑指南"])
        secondary = self.persona.get("secondary_lanes", ["反差拒绝"])
        all_valid = core + secondary

        records = self.history.get("records", [])
        sc = Counter(r.get("strategy", "") for r in records if r.get("strategy"))
        last_used = last_strategies[0] if last_strategies else None

        if last_used in core:
            other = [s for s in core if s != last_used]
            if other:
                return other[0]

        total = sum(sc.get(s, 0) for s in all_valid)
        sec_total = sum(sc.get(s, 0) for s in secondary)
        if total > 0 and sec_total / max(total, 1) < 0.15:
            for s in secondary:
                return s

        return min(core, key=lambda s: sc.get(s, 0))

    def _recent_performance(self, days=7):
        recent = [
            r for r in self.history.get("records", [])
            if r.get("performance", {}).get("published")
        ][-days:]

        if not recent:
            return {"has_data": False, "message": f"最近{days}天暂无发布数据"}

        views = [r["performance"].get("views", 0) or 0 for r in recent]
        completions = [r["performance"].get("completion_rate", 0) or 0 for r in recent]
        engagements = [r["performance"].get("engagement_rate", 0) or 0 for r in recent]

        return {
            "has_data": True,
            "count": len(recent),
            "avg_views": sum(views) / len(views),
            "avg_completion": sum(completions) / len(completions),
            "avg_engagement": sum(engagements) / len(engagements),
            "best_day": recent[max(range(len(recent)), key=lambda i: views[i])]["date"],
        }

    # ═══ 记录 ═══

    def record_generation(self, meta, target_date=None):
        if target_date is None:
            target_date = date.today()
        today = target_date.strftime("%Y-%m-%d")

        record = {
            "date": today,
            "strategy": meta.get("strategy", ""),
            "pillar": meta.get("pillar", ""),
            "shining_type": meta.get("shining_type", ""),
            "hook_type": meta.get("hook_type", ""),
            "topic": meta.get("topic", ""),
            "word_count": meta.get("word_count", 0),
            "duration_sec": meta.get("duration_sec", 0),
            "pleasure_score": meta.get("pleasure_score", 0),
            "persona_score": meta.get("persona_score", 0),
            "thesis": meta.get("thesis", ""),
            "performance": {"published": False},
        }

        records = self.history.get("records", [])

        for i, r in enumerate(records):
            if r.get("date") == today:
                records[i] = record
                break
        else:
            records.append(record)

        max_win = self.history.get("max_window", 30)
        records = records[-max_win:]
        self.history["records"] = records

        strategies = [r.get("strategy", "") for r in records if r.get("strategy")]
        self.history["last_strategies"] = list(reversed(strategies[-5:]))

        angles = [r.get("angle", "") for r in records if r.get("angle")]
        self.history["last_angles"] = list(reversed(angles[-5:]))

        pillar_counts = {"Market": 0, "Property": 0, "Story": 0}
        for r in records:
            p = r.get("pillar", "")
            if p in pillar_counts:
                pillar_counts[p] += 1
        self.history["pillar_distribution"] = pillar_counts

        self._save_history()
        return record

    def record_feedback(self, date_str, metrics):
        records = self.history.get("records", [])
        for r in records:
            if r.get("date") == date_str:
                r["performance"] = {
                    "published": True,
                    **{k: v for k, v in metrics.items()},
                    "recorded_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                }
                self._save_history()
                return r
        return None

    # ═══ 分析 ═══

    def analyze(self):
        records = self.history.get("records", [])
        published = [r for r in records if r.get("performance", {}).get("published")]

        if len(published) < 3:
            return {"ready": False, "message": f"需要至少3条已发布数据，当前{len(published)}条"}

        insights = {"generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"), "ready": True, "findings": []}

        # 1. 最佳策略（按互动率）
        by_strategy = defaultdict(list)
        for r in published:
            s = r.get("strategy", "未知")
            e = r["performance"].get("engagement_rate") or 0
            c = r["performance"].get("completion_rate") or 0
            by_strategy[s].append((e, c))

        best_s = max(by_strategy, key=lambda s: sum(x[0] for x in by_strategy[s]) / len(by_strategy[s]))
        avg_e = sum(x[0] for x in by_strategy[best_s]) / len(by_strategy[best_s])
        avg_c = sum(x[1] for x in by_strategy[best_s]) / len(by_strategy[best_s])
        insights["findings"].append({
            "type": "best_strategy",
            "value": best_s,
            "avg_engagement": round(avg_e, 4),
            "avg_completion": round(avg_c, 4),
            "count": len(by_strategy[best_s]),
        })

        # 2. 最佳支柱
        by_pillar = defaultdict(list)
        for r in published:
            p = r.get("pillar", "未知")
            e = r["performance"].get("engagement_rate") or 0
            by_pillar[p].append(e)

        best_p = max(by_pillar, key=lambda p: sum(by_pillar[p]) / len(by_pillar[p]))
        insights["findings"].append({
            "type": "best_pillar",
            "value": best_p,
            "avg_engagement": round(sum(by_pillar[best_p]) / len(by_pillar[best_p]), 4),
            "count": len(by_pillar[best_p]),
        })

        # 3. 趋势（前后半对比）
        if len(published) >= 6:
            mid = len(published) // 2
            first = [r["performance"].get("engagement_rate", 0) or 0 for r in published[:mid]]
            second = [r["performance"].get("engagement_rate", 0) or 0 for r in published[mid:]]
            avg1, avg2 = sum(first) / len(first), sum(second) / len(second)
            change = (avg2 - avg1) / avg1 * 100 if avg1 > 0 else 0
            insights["findings"].append({
                "type": "trend",
                "direction": "上升 ↑" if change > 0 else "下降 ↓",
                "change_pct": round(change, 1),
            })

        # 4. 最佳时长区间
        by_dur = defaultdict(list)
        for r in published:
            d = r.get("duration_sec", 0) or 60
            bucket = f"{(d // 15) * 15}-{(d // 15 + 1) * 15}秒"
            c = r["performance"].get("completion_rate") or 0
            by_dur[bucket].append(c)

        best_dur = max(by_dur, key=lambda d: sum(by_dur[d]) / len(by_dur[d]))
        insights["findings"].append({
            "type": "best_duration",
            "value": best_dur,
            "avg_completion": round(sum(by_dur[best_dur]) / len(by_dur[best_dur]), 4),
            "count": len(by_dur[best_dur]),
        })

        # 保存
        ipath = self.data_dir / "insights.json"
        ipath.write_text(json.dumps(insights, ensure_ascii=False, indent=2), encoding="utf-8")
        return insights


# ═══ CLI ═══

def main():
    engine = VideoEngine()

    if len(sys.argv) < 2:
        print("用法:")
        print("  python engine.py status          查看今日策略和近期状态")
        print("  python engine.py history [n]     查看最近 n 条记录")
        print("  python engine.py analyze         生成表现洞察")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        s = engine.get_today_strategy()
        print(f"\n[日期] {s['date']}")
        print(f"[策略] 今日策略: {s['strategy']}")
        print(f"[表现] 内容支柱: {s['pillar']} ({s['pillar_label']})")
        if s["recent_angles"]:
            print(f"[角度] 近3条角度: {' / '.join(s['recent_angles'][:3])}")

        perf = s["recent_performance"]
        if perf.get("has_data"):
            print(f"\n[趋势] 近7天表现 ({perf['count']}条):")
            print(f"   平均完播率: {perf['avg_completion']*100:.1f}%")
            print(f"   平均互动率: {perf['avg_engagement']*100:.2f}%")
            print(f"   最佳播放日: {perf['best_day']}")
        else:
            print(f"\n[趋势] {perf.get('message', '暂无数据')}")

        dist = engine.history.get("pillar_distribution", {})
        print(f"\n[表现] 支柱分布: Market={dist.get('Market',0)} Property={dist.get('Property',0)} Story={dist.get('Story',0)}")
        print()

    elif cmd == "history":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for r in engine.history.get("records", [])[-n:]:
            pub = "[已发布]" if r.get("performance", {}).get("published") else "[待发布]"
            print(f"{r['date']} {pub} {r.get('strategy','?'):8s} {r.get('pillar','?'):8s} {str(r.get('topic',''))[:25]}")
        print()

    elif cmd == "analyze":
        r = engine.analyze()
        if not r.get("ready"):
            print(f"\n[!] {r.get('message')}\n")
            return
        print("\n[表现] 表现洞察\n")
        for f in r["findings"]:
            if f["type"] == "best_strategy":
                print(f"* 最佳策略: {f['value']} (互动率{f['avg_engagement']*100:.2f}% 完播率{f['avg_completion']*100:.1f}% n={f['count']})")
            elif f["type"] == "best_pillar":
                print(f"[表现] 最佳支柱: {f['value']} (互动率{f['avg_engagement']*100:.2f}% n={f['count']})")
            elif f["type"] == "trend":
                print(f"[趋势] 互动率趋势: {f['direction']} ({f['change_pct']:+.1f}%)")
            elif f["type"] == "best_duration":
                print(f"[时长] 最佳时长: {f['value']} (完播率{f['avg_completion']*100:.1f}% n={f['count']})")
        print()

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
