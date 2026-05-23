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
        self.format_matrix = self._load_format_matrix()

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
            "name": "佳佳 — 上海改善置换顾问",
            "role": "帮改善家庭把复杂买房决策拆成一步一步看清楚的私人顾问",
            "ip_positioning": {
                "one_liner": "帮上海改善家庭，把复杂的买房决策拆成一步一步看清楚，不催单、不推销，但每一句都有依据",
                "direction_weights": {"陪伴型": 9, "行家型": 4, "避坑型": 4, "资源型": 4},
                "direction_to_lane": {"陪伴型": "陪伴决策", "行家型": "专业分析", "避坑型": "避坑指南", "资源型": "资源推荐"},
                "core_districts": ["长宁·天山", "长宁·古北", "长宁·中山公园"],
                "extended_districts": ["普陀", "闵行", "静安"],
                "budget_range": "1000万-1500万（核心），上限约2000万",
                "target_audience": "外地父母给上海的孩子买房为主"
            },
            "core_lanes": ["陪伴决策", "专业分析", "避坑指南"],
            "secondary_lanes": ["资源推荐"],
            "language_style": "朋友聊天式",
            "forbidden_words": [
                "家人们", "绝绝子", "震惊", "重磅", "赶紧", "手慢无",
                "错过不再", "必看", "血赚", "抢疯了", "暴涨", "暴跌"
            ],
            "preferred_patterns": [
                "我建议", "我觉得", "你可以考虑", "不妨看看",
                "如果不介意", "说实话", "说白了", "其实就一点"
            ],
            "tone_markers": {
                "soft_starters": ["最近", "前两天", "今天", "刚帮一个客户"],
                "opinion_markers": ["说实话", "我觉得", "其实", "说白了"],
                "sharing_markers": ["分享一个", "说个真实的", "跟你说个事"],
                "no_pressure_markers": ["不着急", "可以先了解", "买不买无所谓", "看看也不吃亏"],
                "companion_markers": ["一步步来", "不着急", "我陪你看", "慢慢梳理", "咱们一起看看"]
            },
            "core_values": [
                "不催单，帮客户筛选而非推销",
                "用真实数据说话，不编造",
                "承认不完美，没有十全十美的房子",
                "站在客户立场想问题",
                "把复杂的决策拆成一步一步看清楚"
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
            "community_coverage": {},
            "max_window": 30,
        }

    def _save_history(self):
        path = self.data_dir / "history.json"
        path.write_text(json.dumps(self.history, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_format_matrix(self):
        path = self.config_dir / "video_format_matrix.json"
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        return {}

    # ═══ 策略决策 ═══

    def _select_video_format(self, strategy, pillar, no_venue=False):
        primary_map = self.format_matrix.get("primary_map", {})
        reason_map = self.format_matrix.get("format_rationale", {})
        format_specs = self.format_matrix.get("formats", {})

        # Layer 1: matrix lookup
        strategy_formats = primary_map.get(strategy, {})
        fmt_key = strategy_formats.get(pillar, "talking_head")

        # Layer 2: override — check recent format rotation
        records = self.history.get("records", [])
        recent_formats = [r.get("video_format", "") for r in records[-5:] if r.get("video_format")]
        if len(recent_formats) >= 3 and len(set(recent_formats[-3:])) == 1:
            same = recent_formats[-1]
            if same == "talking_head":
                fmt_key = "mixed_montage"
            elif same == "mixed_montage":
                fmt_key = "property_walk" if strategy in ("陪伴决策", "专业分析") else "talking_head"
            elif same == "property_walk":
                fmt_key = "talking_head"

        # Layer 3: no_venue fallback — 无法进入房源或天气恶劣时降级为口播
        if fmt_key == "property_walk" and no_venue:
            fmt_key = "talking_head"

        spec = format_specs.get(fmt_key, format_specs.get("talking_head", {}))
        rationale_key = f"{strategy}_{pillar}"
        rationale = reason_map.get(rationale_key, "")

        return {
            "format_key": fmt_key,
            "label": spec.get("label", "口播"),
            "rationale": rationale,
            "scene": spec.get("scene", ""),
            "shot": spec.get("shot", ""),
            "bgm": spec.get("bgm", ""),
            "equipment": spec.get("equipment", ""),
            "shoot_minutes": spec.get("shoot_minutes", 20),
            "edit_minutes": spec.get("edit_minutes", 15),
            "batch_potential": spec.get("batch_potential", ""),
            "best_platform": spec.get("best_platform", ""),
            "script_word_count": spec.get("script_word_count", "300-500字"),
            "recent_formats": recent_formats,
        }

    def get_today_strategy(self, target_date=None, no_venue=False):
        if target_date is None:
            target_date = date.today()

        records = self.history.get("records", [])
        last_strategies = self.history.get("last_strategies", [])
        last_angles = self.history.get("last_angles", [])
        pillar_dist = self.history.get("pillar_distribution", {})

        pillar = self._select_pillar(pillar_dist)
        strategy = self._select_strategy(last_strategies)
        video_format = self._select_video_format(strategy, pillar, no_venue=no_venue)
        recent_angles = last_angles[:3] if last_angles else []

        label = {"Market": "市场宏观", "Property": "房子板块", "Story": "人物故事"}

        # Strategy distribution stats
        records_all = self.history.get("records", [])
        strat_counts = Counter(r.get("strategy", "") for r in records_all[-20:] if r.get("strategy"))

        # Series progress
        series_status = self.get_series_status()

        # Suggest next community: first district with uncovered communities
        next_community = None
        for d in self.persona.get("ip_positioning", {}).get("core_districts", []):
            st = series_status.get(d, {})
            if st.get("remaining"):
                next_community = {"district": d, "community": st["remaining"][0]}
                break

        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "pillar": pillar,
            "pillar_label": label.get(pillar, pillar),
            "strategy": strategy,
            "video_format": video_format,
            "recent_angles": recent_angles,
            "recent_performance": self._recent_performance(7),
            "core_lanes": self.persona.get("core_lanes", []),
            "secondary_lanes": self.persona.get("secondary_lanes", []),
            "direction_weights": self.persona.get("ip_positioning", {}).get("direction_weights", {}),
            "direction_to_lane": self.persona.get("ip_positioning", {}).get("direction_to_lane", {}),
            "strategy_distribution": dict(strat_counts),
            "series_status": series_status,
            "next_community": next_community,
        }

    def _select_pillar(self, pillar_dist):
        target = {"Market": 0.30, "Property": 0.40, "Story": 0.30}
        total = sum(pillar_dist.values()) or 1
        current = {k: pillar_dist.get(k, 0) / total for k in target}
        gaps = {k: target[k] - current.get(k, 0) for k in target}
        return max(gaps, key=gaps.get)

    def _select_strategy(self, last_strategies):
        weights = self.persona.get("ip_positioning", {}).get("direction_weights", {})
        lane_map = self.persona.get("ip_positioning", {}).get("direction_to_lane", {})

        records = self.history.get("records", [])
        last_used = last_strategies[0] if last_strategies else None

        # Use IP direction weights if configured
        if weights and lane_map:
            recent = records[-10:]
            recent_sc = Counter(r.get("strategy", "") for r in recent if r.get("strategy"))
            recent_total = sum(recent_sc.values()) or 1
            total_weight = sum(weights.values())

            # Score each lane by how underrepresented it is vs target weight
            lane_scores = {}
            for direction, weight in weights.items():
                lane = lane_map.get(direction)
                if not lane:
                    continue
                actual_pct = recent_sc.get(lane, 0) / recent_total
                target_pct = weight / total_weight
                gap = target_pct - actual_pct
                # Penalize repeating the last strategy
                if lane == last_used:
                    gap -= 0.15
                lane_scores[lane] = gap

            if lane_scores:
                return max(lane_scores, key=lane_scores.get)

        # Fallback: simple rotation on core lanes
        core = self.persona.get("core_lanes", ["陪伴决策", "专业分析", "避坑指南"])
        secondary = self.persona.get("secondary_lanes", ["资源推荐"])
        all_valid = core + secondary
        sc = Counter(r.get("strategy", "") for r in records if r.get("strategy"))

        if last_used in core:
            other = [s for s in core if s != last_used]
            if other:
                return other[0]

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
            "video_format": meta.get("video_format", ""),
            "bgm_type": meta.get("bgm_type", ""),
            "scene": meta.get("scene", ""),
            "tags": meta.get("tags", []),
            "cover_concept": meta.get("cover_concept", ""),
            "shining_type": meta.get("shining_type", ""),
            "hook_type": meta.get("hook_type", ""),
            "topic": meta.get("topic", ""),
            "word_count": meta.get("word_count", 0),
            "duration_sec": meta.get("duration_sec", 0),
            "pleasure_score": meta.get("pleasure_score", 0),
            "persona_score": meta.get("persona_score", 0),
            "thesis": meta.get("thesis", ""),
            "community": meta.get("community", ""),
            "district": meta.get("district", ""),
            "series": meta.get("series", ""),
            "episode": meta.get("episode", 0),
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

        # Track community coverage per district
        cc = self.history.get("community_coverage", {})
        district = meta.get("district", "")
        community = meta.get("community", "")
        if district and community:
            if district not in cc:
                cc[district] = {}
            if community not in cc[district]:
                cc[district][community] = {"count": 0, "episodes": []}
            cc[district][community]["count"] += 1
            ep = meta.get("episode", 0)
            if ep:
                cc[district][community]["episodes"].append(ep)
            cc[district][community]["last_date"] = today
        self.history["community_coverage"] = cc

        self._save_history()
        return record

    def get_series_status(self, district=None):
        """查询系列拍摄进度——哪些小区已拍、哪些待拍。

        若指定 district，只返回该板块；否则返回全部。
        返回格式: {板块名: {'covered': [...], 'remaining': [...]}}
        """
        cc = self.history.get("community_coverage", {})
        persona_districts = self.persona.get("ip_positioning", {}).get("core_districts", [])
        extended = self.persona.get("ip_positioning", {}).get("extended_districts", [])

        # Load known communities from CSV
        csv_path = self.root.parent / "03-shanghai-community-analysis" / "小区对比总表.csv"
        known_by_district = {}  # keyed by persona-format name
        if csv_path.exists():
            import csv
            with open(csv_path, encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    d_short = row.get('板块', '').strip()
                    c = row.get('小区名称', '').strip()
                    if not d_short or not c:
                        continue
                    # Map CSV short name to persona long name
                    d_key = d_short
                    for pd_name in persona_districts + extended:
                        if pd_name.endswith('·' + d_short):
                            d_key = pd_name
                            break
                    if d_key not in known_by_district:
                        known_by_district[d_key] = []
                    known_by_district[d_key].append(c)

        # Build covered lookup: check both persona long name and csv short name
        covered_by_district = {}
        for cc_key, communities in cc.items():
            # Normalize to persona format
            mapped_key = cc_key
            if '·' not in cc_key:
                for pd_name in persona_districts + extended:
                    if pd_name.endswith('·' + cc_key):
                        mapped_key = pd_name
                        break
            covered_by_district[mapped_key] = list(communities.keys())

        target_districts = [district] if district else persona_districts + extended
        result = {}
        for d in target_districts:
            known = known_by_district.get(d, [])
            covered = covered_by_district.get(d, [])
            remaining = [c for c in known if c not in covered]
            result[d] = {
                "total_known": len(known),
                "covered": covered,
                "covered_count": len(covered),
                "remaining": remaining,
                "remaining_count": len(remaining),
            }

        return result

    def get_community_listings(self, community_name=None):
        """读取 daily_followup.xlsm '房源' sheet，返回指定小区的在售房源摘要。

        若 community_name 为 None，返回所有小区名列表（去重）。
        若指定 community_name，返回该小区的：
          - count: 在售套数
          - avg_unit_price: 平均单价 (万/㎡)
          - avg_total_price: 平均总价 (万)
          - score_distribution: {9: n, 8: n, 7: n, 6: n, <6: n}
          - best: 最高分房源 (面积/总价/单价/楼层/分数/硬伤/房龄)
          - listings: 所有房源列表（最多返回 20 条）
        """
        # Locate the xlsm file
        import csv as _csv
        xlsm_paths = [
            Path("D:/Unique work form/daily_followup.xlsm"),
            self.root.parent / "01-Excel-Customer-Management" / "daily_followup.xlsm",
        ]
        xlsm_path = None
        for p in xlsm_paths:
            if p.exists():
                xlsm_path = p
                break

        if xlsm_path is None:
            return None

        # Parse xlsm via zipfile + XML (same approach as 01 project)
        import zipfile, xml.etree.ElementTree as ET
        with zipfile.ZipFile(xlsm_path, 'r') as z:
            # Load shared strings
            with z.open('xl/sharedStrings.xml') as f:
                tree = ET.parse(f)
            ns = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
            strings = []
            for si in tree.findall('.//s:si', ns):
                text = ''.join(t.text or '' for t in si.findall('.//s:t', ns))
                strings.append(text)

            # Read sheet5 (房源)
            with z.open('xl/worksheets/sheet5.xml') as f:
                ws_tree = ET.parse(f)

            rows = ws_tree.findall('.//s:row', ns)
            # Data starts at row 4 (row 3 is header)
            communities = {}  # {name: [listing, ...]}
            for row in rows:
                rn = int(row.get('r', 0))
                if rn < 4:
                    continue

                cells = row.findall('s:c', ns)
                cell_vals = {}
                for c in cells:
                    col_letter = ''.join(ch for ch in c.get('r', '') if ch.isalpha())
                    v = c.find('s:v', ns)
                    t = c.get('t', '')
                    val = ''
                    if v is not None and v.text:
                        if t == 's':
                            idx = int(v.text)
                            val = strings[idx] if idx < len(strings) else ''
                        else:
                            val = v.text
                    cell_vals[col_letter] = val

                # Extract columns of interest
                name = cell_vals.get('C', '').strip()  # col C = 小区
                if not name:
                    continue

                try:
                    area = float(cell_vals.get('E', 0) or 0)
                except ValueError:
                    area = 0
                try:
                    total_price = float(cell_vals.get('F', 0) or 0)
                except ValueError:
                    total_price = 0
                try:
                    unit_price = float(cell_vals.get('G', 0) or 0)
                except ValueError:
                    unit_price = 0
                floor = cell_vals.get('H', '').strip()
                try:
                    score = float(cell_vals.get('I', 0) or 0)
                except ValueError:
                    score = 0
                listing_time = cell_vals.get('J', '').strip()
                flaw = cell_vals.get('K', '').strip()
                age = cell_vals.get('L', '').strip()

                listing = {
                    'area': area,
                    'total_price': total_price,
                    'unit_price': unit_price,
                    'floor': floor,
                    'score': score,
                    'listing_time': listing_time,
                    'flaw': flaw,
                    'age': age,
                }

                if name not in communities:
                    communities[name] = []
                communities[name].append(listing)

        # Return all names or specific community data
        if community_name is None:
            return sorted(communities.keys())

        listings = communities.get(community_name, [])
        if not listings:
            return None

        # Compute stats
        total_prices = [l['total_price'] for l in listings if l['total_price'] > 0]
        unit_prices = [l['unit_price'] for l in listings if l['unit_price'] > 0]
        scored = [l for l in listings if l['score'] > 0]
        scored.sort(key=lambda l: l['score'], reverse=True)

        score_dist = {'9+': 0, '8-9': 0, '7-8': 0, '6-7': 0, '<6': 0}
        for l in listings:
            s = l['score']
            if s >= 9:
                score_dist['9+'] += 1
            elif s >= 8:
                score_dist['8-9'] += 1
            elif s >= 7:
                score_dist['7-8'] += 1
            elif s >= 6:
                score_dist['6-7'] += 1
            elif s > 0:
                score_dist['<6'] += 1

        return {
            'count': len(listings),
            'avg_total_price': round(sum(total_prices) / len(total_prices)) if total_prices else 0,
            'avg_unit_price': round(sum(unit_prices) / len(unit_prices), 1) if unit_prices else 0,
            'min_total_price': min(total_prices) if total_prices else 0,
            'max_total_price': max(total_prices) if total_prices else 0,
            'score_distribution': score_dist,
            'best': scored[0] if scored else None,
            'listings': scored[:20],
        }

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

        # 4. 最佳格式（按完播率+互动率综合）
        by_format = defaultdict(list)
        for r in published:
            f = r.get("video_format", "")
            if not f:
                continue
            e = r["performance"].get("engagement_rate") or 0
            c = r["performance"].get("completion_rate") or 0
            by_format[f].append((e, c))

        if by_format:
            best_f = max(by_format, key=lambda f: sum(x[0] + x[1] for x in by_format[f]) / len(by_format[f]))
            avg_fe = sum(x[0] for x in by_format[best_f]) / len(by_format[best_f])
            avg_fc = sum(x[1] for x in by_format[best_f]) / len(by_format[best_f])
            insights["findings"].append({
                "type": "best_format",
                "value": best_f,
                "avg_engagement": round(avg_fe, 4),
                "avg_completion": round(avg_fc, 4),
                "count": len(by_format[best_f]),
            })

        # 5. 最佳时长区间
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
        print("  python engine.py status [--no-venue]  查看今日策略和近期状态")
        print("  python engine.py history [n]          查看最近 n 条记录")
        print("  python engine.py series [板块]        查看系列拍摄进度")
        print("  python engine.py listings [小区名]    查询优质房源表（不填则列所有小区）")
        print("  python engine.py analyze              生成表现洞察")
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd == "status":
        no_venue = "--no-venue" in args
        s = engine.get_today_strategy(no_venue=no_venue)
        print(f"\n[日期] {s['date']}")
        print(f"[策略] 今日策略: {s['strategy']}")
        print(f"[表现] 内容支柱: {s['pillar']} ({s['pillar_label']})")
        if s["recent_angles"]:
            print(f"[角度] 近3条角度: {' / '.join(s['recent_angles'][:3])}")

        # 画面形式推荐
        vf = s.get("video_format", {})
        if vf:
            print(f"\n[格式] 推荐画面形式: {vf.get('label', '?')}")
            if no_venue:
                print(f"   [!] 降级模式：no_venue=True，实拍已降级为口播")
            print(f"   理由: {vf.get('rationale', '')}")
            print(f"   场景: {vf.get('scene', '')}")
            print(f"   机位: {vf.get('shot', '')}")
            print(f"   BGM:  {vf.get('bgm', '')}")
            print(f"   设备: {vf.get('equipment', '')}")
            print(f"   耗时: 拍摄{vf.get('shoot_minutes', '?')}分钟 + 剪辑{vf.get('edit_minutes', '?')}分钟")
            print(f"   字数: {vf.get('script_word_count', '')}")
            print(f"   平台: {vf.get('best_platform', '')}")
            print(f"   批量: {vf.get('batch_potential', '')}")
            rf = vf.get("recent_formats", [])
            if rf:
                print(f"   近期: {' → '.join(rf[-5:])}")

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

        # IP方向权重分布
        dw = s.get("direction_weights", {})
        dl = s.get("direction_to_lane", {})
        sd = s.get("strategy_distribution", {})
        if dw and dl:
            print(f"\n[IP方向] 目标权重 vs 近20条实际:")
            total_w = sum(dw.values()) or 1
            total_s = sum(sd.values()) or 1
            for direction, weight in dw.items():
                lane = dl.get(direction, direction)
                actual = sd.get(lane, 0) / total_s * 100 if total_s > 0 else 0
                target = weight / total_w * 100
                bar = "#" * int(actual / 5) + "-" * (20 - int(actual / 5))
                print(f"  {direction:6s}({lane:6s}) 目标{target:.0f}% 实际{actual:.0f}% [{bar}]")

        # 系列拍摄进度
        ss = s.get("series_status", {})
        nc = s.get("next_community")
        if ss:
            print(f"\n[系列] 拍摄进度:")
            for d_name, d_info in ss.items():
                total = d_info.get("total_known", 0)
                cov = d_info.get("covered_count", 0)
                rem = d_info.get("remaining_count", 0)
                if total == 0:
                    continue
                bar_len = 20
                filled = int(cov / total * bar_len) if total > 0 else 0
                bar = "█" * filled + "░" * (bar_len - filled)
                remaining_list = d_info.get("remaining", [])
                remaining_preview = ", ".join(remaining_list[:3])
                if len(remaining_list) > 3:
                    remaining_preview += f" 等{len(remaining_list)}个"
                print(f"  {d_name:8s} [{bar}] {cov}/{total}")
                if remaining_list:
                    print(f"           待拍: {remaining_preview}")
            if nc:
                print(f"\n  → 推荐下一个: {nc['district']}·{nc['community']}")
        print()

    elif cmd == "history":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        for r in engine.history.get("records", [])[-n:]:
            pub = "[已发布]" if r.get("performance", {}).get("published") else "[待发布]"
            print(f"{r['date']} {pub} {r.get('strategy','?'):8s} {r.get('pillar','?'):8s} {str(r.get('topic',''))[:25]}")
        print()

    elif cmd == "series":
        district = sys.argv[2] if len(sys.argv) > 2 else None
        ss = engine.get_series_status(district)
        if not ss:
            print("\n暂无系列数据\n")
            return
        print(f"\n[系列] 拍摄进度\n")
        for d_name, d_info in ss.items():
            total = d_info.get("total_known", 0)
            if total == 0:
                continue
            cov = d_info.get("covered_count", 0)
            rem = d_info.get("remaining_count", 0)
            filled = int(cov / total * 20) if total > 0 else 0
            bar = "█" * filled + "░" * (20 - filled)
            print(f"  {d_name:6s} [{bar}] {cov}/{total}")
            if d_info.get("covered"):
                print(f"         已拍: {', '.join(d_info['covered'])}")
            if d_info.get("remaining"):
                print(f"         待拍: {', '.join(d_info['remaining'])}")
            print()
        print()

    elif cmd == "listings":
        community = sys.argv[2] if len(sys.argv) > 2 else None
        result = engine.get_community_listings(community)
        if result is None:
            print("\n[!] 未找到房源数据，请确认 daily_followup.xlsm 是否存在\n")
            return
        if community is None:
            print(f"\n[房源] 共 {len(result)} 个小区有优质在售房源\n")
            for name in result[:30]:
                print(f"  {name}")
            if len(result) > 30:
                print(f"  ... 共 {len(result)} 个")
            print()
        else:
            info = result
            print(f"\n[房源] {community} — 在售 {info['count']} 套")
            print(f"  均价: {info['avg_unit_price']} 万/㎡ | 总价: {info['min_total_price']}-{info['max_total_price']} 万")
            print(f"  分数分布: 9+={info['score_distribution']['9+']} | 8-9={info['score_distribution']['8-9']} | 7-8={info['score_distribution']['7-8']} | 6-7={info['score_distribution']['6-7']}")
            best = info.get('best')
            if best:
                print(f"  最佳: {best['area']}㎡ {best['total_price']}万 ({best['unit_price']}万/㎡) 分{best['score']} {best['floor']} {best['flaw']} {best['age']}")
            if info['count'] <= 15:
                print(f"\n  全部房源:")
                for i, l in enumerate(info['listings']):
                    print(f"  {i+1}. {l['area']}㎡ {l['total_price']}万 ({l['unit_price']}万/㎡) {l['floor']} 分{l['score']} {l['flaw']}")
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
            elif f["type"] == "best_format":
                label_map = {"talking_head": "口播", "property_walk": "实拍/探盘", "mixed_montage": "混剪"}
                print(f"[格式] 最佳形式: {label_map.get(f['value'], f['value'])} (互动率{f['avg_engagement']*100:.2f}% 完播率{f['avg_completion']*100:.1f}% n={f['count']})")
            elif f["type"] == "best_duration":
                print(f"[时长] 最佳时长: {f['value']} (完播率{f['avg_completion']*100:.1f}% n={f['count']})")
        print()

    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
