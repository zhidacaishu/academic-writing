#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
稿件机械检查。纯标准库，不联网。

为什么需要它：这些检查（数破折号、数句长、找漏定义的缩写、比对引用有没有被动过）
靠通读稿件去做，在几千词的篇幅上必漏。脚本一次扫完，把注意力留给真正需要判断的地方。
脚本只负责"找出可疑位置"，判断和改写仍然是人的事——很多条目本身没有对错，要看语境。

用法
    python3 check_draft.py draft.tex              # 检查单份稿件
    cat draft.txt | python3 check_draft.py -      # 从标准输入读
    python3 check_draft.py orig.tex --compare new.tex   # 润色前后比对

--compare 是润色模式的护栏：它比对引用键、\\ref/\\label、公式内容和所有数字，
任何新增引用或被改动的数字都会报出来。skill 的前两条硬规则（不编引用、不改实质）
靠人工复核很难保证，靠这个比对可以。

退出码：0 干净，1 有硬问题，2 只有需人工判断的条目。
"""

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict

# ---------------------------------------------------------------- 词表
# 分两级：HARD 几乎一定要改；SOFT 要看语境，只提示位置。

AI_MARKERS_HARD = [
    "delve", "tapestry", "intricate", "pivotal", "multifaceted", "seamless",
    "holistic", "testament", "garner", "revolutionize", "paramount",
    "meticulous", "showcase",
]
AI_MARKERS_SOFT = [
    "underscore", "realm", "landscape", "harness", "navigate", "unlock",
    "foster", "nuanced", "comprehensive",
]
AI_PHRASES = [
    "it is worth noting that", "it is important to note that",
    "plays a crucial role in", "sheds light on", "paves the way for",
    "in today's", "at its core", "this raises an important question",
    "in conclusion", "it is worth mentioning",
]
# 中式学术英语。左边出现即报，多数是直译痕迹。
CN_ENGLISH = [
    "with the rapid development of", "in recent years, more and more",
    "as we all know", "it is well known that", "and so on",
    "domestic and foreign scholars", "domestic and overseas",
    "has certain reference", "has important significance",
    "it is not difficult to find", "to a certain extent",
    "draw the conclusion", "management enlightenment", "research prospect",
    "research deficiency", "policy suggestion", "the method proposed by this paper",
    "literatures", "researches", "super parameter", "target function",
    "over fitting", "cold boot", "generate process", "calculate complexity",
    "adjust parameters", "comparison experiment", "robust test",
    "sensitivity analyse", "listed company", "enterprise green",
    "reach the best", "hidden variable", "prior probability distribution",
]
# 冗余结构。压缩后不损失正式度。
BLOAT = {
    "due to the fact that": "because",
    "in spite of the fact that": "although",
    "it should be noted that": "删除，直接说",
    "at this point in time": "now / currently",
    "the vast majority of": "most",
    "a wide array of": "various / 给数量",
    "a myriad of": "many / 给数量",
    "has the ability to": "can",
    "make an assumption that": "assume",
    "conduct an analysis of": "analyze",
    "serve to illustrate": "illustrate",
    "prior to": "before",
    "subsequent to": "after",
    "in the realm of": "in",
}
# 声称强度越界。
OVERCLAIM = [
    (r"\bis superior to\b", "无条件断言，改为限定范围的说法"),
    (r"\bsuperior than\b", "搭配错误，superior to"),
    (r"\bin general\b", "声称范围可能超过实验覆盖范围"),
    (r"\bthis is the first (paper|study|work)\b", "需加 to the best of our knowledge"),
    (r"\ba wide range of scenarios\b", "未做跨场景验证不能这样写"),
    (r"\bclearly (better|superior|outperforms)\b", "替读者下判断，给数字"),
    (r"\b(greatly|obviously|undoubtedly|definitely|perfectly)\b", "程度副词无信息量"),
    (r"\bsignificantly (out)?perform", "有配对检验或秩和检验才能用 significantly"),
    (r"\bour (model|method|approach) is (efficient|interpretable|scalable|robust)\b",
     "声称必须配证据：指向图号、表号或复杂度"),
]
# 同一概念的写法变体。同篇内混用即报。
VARIANT_GROUPS = [
    ["data set", "dataset"],
    ["hyperparameter", "hyper-parameter", "hyper parameter"],
    ["cold-start", "cold start"],
    ["long-tail", "long tail"],
    ["state-of-the-art", "state of the art"],
    ["real-world", "real world"],
    ["high-dimensional", "high dimensional"],
    ["overfitting", "over-fitting"],
    ["cross-validation", "cross validation"],
    ["time-series", "time series"],
]
SPELLING_PAIRS = [
    ("analyze", "analyse"), ("modeling", "modelling"), ("behavior", "behaviour"),
    ("labeled", "labelled"), ("center", "centre"), ("optimize", "optimise"),
    ("characterize", "characterise"), ("generalize", "generalise"),
]
# 疑似过去时。方法类论文默认现在时，例外通常不超过三五处。
PAST_PATTERNS = [
    r"\bwe (collected|conducted|constructed|proposed|used|obtained|applied|"
    r"performed|adopted|developed|showed|found|achieved|trained|evaluated|"
    r"compared|selected|removed|computed|designed|built|implemented)\b",
    r"\b(was|were) (used|conducted|applied|adopted|performed|trained|evaluated|selected)\b",
]
ACRONYM_STOP = {
    "AI", "ML", "US", "UK", "EU", "PDF", "URL", "API", "CPU", "GPU", "RAM",
    "OK", "ID", "TV", "AND", "OR", "NOT", "THE", "A", "I", "II", "III", "IV",
    "MATHINLINE", "MATHBLOCK",  # 本脚本自己的公式占位符
}
SENT_ABBREV = {
    "et al.", "e.g.", "i.e.", "cf.", "vs.", "Fig.", "Eq.", "Sec.", "Tab.",
    "Ref.", "Dr.", "Prof.", "St.", "approx.", "resp.", "No.",
}

CJK_PUNCT = "\u3001\u3002\uff01\uff08\uff09\uff0c\uff1a\uff1b\uff1f\uff0e\u300a\u300b\u3010\u3011\u2026\u3000\uff05\uff06\uff1c\uff1e"
CJK_CHAR = re.compile(r"[\u4e00-\u9fff]+")

MATH_PATTERNS = [
    (r"\$\$.*?\$\$", "display"),
    (r"\\\[.*?\\\]", "display"),
    (r"\\begin\{(equation|align|gather|eqnarray)\*?\}.*?\\end\{\1\*?\}", "env"),
    (r"(?<!\\)\$[^$]+?\$", "inline"),
]


# ---------------------------------------------------------------- 基础设施
class Report:
    def __init__(self):
        self.hard = defaultdict(list)
        self.soft = defaultdict(list)

    def add(self, tier, section, msg):
        (self.hard if tier == "hard" else self.soft)[section].append(msg)

    def render(self):
        out = []
        for title, bucket in (("必改", self.hard), ("需人工判断", self.soft)):
            if not bucket:
                continue
            out.append(f"\n{'=' * 62}\n{title}\n{'=' * 62}")
            for section, items in bucket.items():
                out.append(f"\n[{section}]  {len(items)} 处")
                for m in items[:25]:
                    out.append(f"  {m}")
                if len(items) > 25:
                    out.append(f"  ... 另有 {len(items) - 25} 处，同类问题")
        if not out:
            return "未发现机械层面的问题。结构与论证仍需人工判断。"
        return "\n".join(out)


def strip_math(text):
    """把公式替换成等长占位符，避免公式内容污染散文层面的统计。"""
    segments = []
    for pattern, kind in MATH_PATTERNS:
        def grab(m):
            segments.append(m.group(0))
            return " MATHBLOCK " if kind != "inline" else " MATHINLINE "
        text = re.sub(pattern, grab, text, flags=re.S)
    return text, segments


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def context(text, pos, span=34):
    lo, hi = max(0, pos - span), min(len(text), pos + span)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def split_sentences(prose):
    prose = re.sub(r"\s+", " ", prose)
    for ab in SENT_ABBREV:
        prose = prose.replace(ab, ab.replace(".", "\x00"))
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", prose)
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


# ---------------------------------------------------------------- 各项检查
def check_dashes(text, rep):
    for m in re.finditer(r"\u2014{1,2}|(?<!-)---(?!-)", text):
        rep.add("hard", "长破折号",
                f"L{line_of(text, m.start())}: …{context(text, m.start())}…")
    for m in re.finditer(r"(?<=[A-Za-z])\s*\u2013\s*(?=[A-Za-z])", text):
        rep.add("soft", "en dash 用于句内",
                f"L{line_of(text, m.start())}: en dash 只用于数字区间与复合专名 …{context(text, m.start())}…")


def check_cjk_residue(text, rep):
    for m in re.finditer(f"[{CJK_PUNCT}]", text):
        rep.add("hard", "全角标点残留",
                f"L{line_of(text, m.start())}: '{m.group()}' …{context(text, m.start())}…")
    for m in CJK_CHAR.finditer(text):
        rep.add("hard", "中文字符残留",
                f"L{line_of(text, m.start())}: …{context(text, m.start())}…")
    for m in re.finditer(r"[\u201c\u201d\u2018\u2019]", text):
        rep.add("soft", "弯引号",
                f"L{line_of(text, m.start())}: LaTeX 稿应使用 `` '' …{context(text, m.start())}…")


def _scan_terms(prose, terms, rep, tier, section, note=None):
    low = prose.lower()
    for term in terms:
        for m in re.finditer(r"\b" + re.escape(term.lower()) + r"\b", low):
            tail = f"  → {note[term]}" if note else ""
            rep.add(tier, section,
                    f"L{line_of(prose, m.start())}: '{term}' …{context(prose, m.start())}…{tail}")


def check_wording(prose, rep):
    _scan_terms(prose, AI_MARKERS_HARD, rep, "hard", "AI 标记词")
    _scan_terms(prose, AI_MARKERS_SOFT, rep, "soft", "AI 标记词（看语境）")
    _scan_terms(prose, AI_PHRASES, rep, "hard", "AI 标记短语")
    _scan_terms(prose, CN_ENGLISH, rep, "hard", "中式学术英语")
    _scan_terms(prose, list(BLOAT), rep, "hard", "冗余结构", note=BLOAT)
    low = prose.lower()
    for pat, why in OVERCLAIM:
        for m in re.finditer(pat, low):
            rep.add("soft", "声称强度",
                    f"L{line_of(prose, m.start())}: …{context(prose, m.start())}…  → {why}")
    if re.search(r"\betc\.", low) or re.search(r"\band so on\b", low):
        rep.add("soft", "兜底列举", "出现 etc. / and so on：列举应完整或说明选取标准")


def check_consistency(prose, rep):
    low = prose.lower()
    for group in VARIANT_GROUPS:
        found = {v: len(re.findall(r"\b" + re.escape(v) + r"\b", low)) for v in group}
        used = {k: v for k, v in found.items() if v}
        if len(used) > 1:
            detail = "、".join(f"{k}×{v}" for k, v in used.items())
            rep.add("hard", "写法不一致", f"{detail}  → 全文二选一")
    for us, uk in SPELLING_PAIRS:
        a = len(re.findall(rf"\b{us}\w*\b", low))
        b = len(re.findall(rf"\b{uk}\w*\b", low))
        if a and b:
            rep.add("hard", "英美拼写混用", f"{us}×{a} / {uk}×{b}  → INFORMS 系用美式")


def check_acronyms(prose, rep):
    seen = {}
    for m in re.finditer(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*\b", prose):
        tok = m.group()
        if tok in ACRONYM_STOP or tok.isdigit():
            continue
        seen.setdefault(tok, m.start())
    for tok, pos in seen.items():
        window = prose[max(0, pos - 160):pos + len(tok) + 60]
        defined = re.search(r"\(\s*" + re.escape(tok) + r"s?\s*\)", window)
        if not defined:
            rep.add("soft", "缩写首现未定义",
                    f"'{tok}' 首次出现在 L{line_of(prose, pos)}: …{context(prose, pos)}…")


def check_tense(prose, rep):
    hits = []
    for pat in PAST_PATTERNS:
        hits += [m.start() for m in re.finditer(pat, prose, flags=re.I)]
    if len(hits) > 5:
        rep.add("soft", "疑似过去时",
                f"共 {len(hits)} 处。方法类论文默认现在时，真正的一次性历史事实通常不超过三五处")
    for pos in sorted(hits)[:12]:
        rep.add("soft", "疑似过去时", f"L{line_of(prose, pos)}: …{context(prose, pos)}…")


def check_sentences(prose, rep):
    sents = split_sentences(prose)
    lengths = [len(s.split()) for s in sents if len(s.split()) > 2]
    if len(lengths) < 8:
        return
    mean = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    cv = sd / mean if mean else 0
    band = sum(1 for n in lengths if 15 <= n <= 25) / len(lengths)
    rep.add("soft", "句长分布",
            f"共 {len(lengths)} 句，均值 {mean:.1f}，标准差 {sd:.1f}，"
            f"变异系数 {cv:.2f}，落在 15–25 词的占 {band:.0%}")
    if cv < 0.35:
        rep.add("soft", "句长分布", "变异系数偏低：句长过于均匀，是最稳定的 AI 结构标记")
    if band > 0.55:
        rep.add("soft", "句长分布", "过半句子挤在 15–25 词：合并短句或拆开长句，让长度跟着内容走")
    for s in sents:
        n = len(s.split())
        if n > 45:
            rep.add("soft", "超长句", f"{n} 词：{s[:80]}…")
    starts = Counter()
    for s in sents:
        w = s.split()
        if w:
            starts[w[0].strip(",").lower()] += 1
    for w in ("moreover", "furthermore", "additionally", "besides", "however"):
        if starts[w] >= 3:
            rep.add("soft", "连接词堆叠", f"{starts[w]} 句以 '{w.capitalize()}' 开头")


def check_numbers(prose, rep):
    pcts = re.findall(r"(\d+)\.(\d+)\s*\\?%", prose)
    if pcts:
        places = Counter(len(d) for _, d in pcts)
        if len(places) > 1:
            rep.add("hard", "数字格式", f"百分比小数位数不一致：{dict(places)}")
    if re.search(r"(?<![\d.])\.\d", prose) and re.search(r"\b0\.\d", prose):
        rep.add("hard", "数字格式", "同时出现 .5 与 0.5 两种写法")


# ---------------------------------------------------------------- 比对模式
def extract_invariants(text):
    cites = []
    for m in re.finditer(r"\\[a-zA-Z]*cite[a-zA-Z]*\s*(?:\[[^\]]*\])*\{([^}]*)\}", text):
        cites += [k.strip() for k in m.group(1).split(",") if k.strip()]
    labels = re.findall(r"\\label\{([^}]*)\}", text)
    refs = re.findall(r"\\(?:eq)?ref\{([^}]*)\}", text)
    _, math = strip_math(text)
    math_norm = [re.sub(r"\s+", "", s) for s in math]
    prose, _ = strip_math(text)
    numbers = re.findall(r"(?<![\w.])\d+(?:\.\d+)?%?", prose)
    return {
        "cites": Counter(cites), "labels": Counter(labels), "refs": Counter(refs),
        "math": Counter(math_norm), "numbers": Counter(numbers),
    }


def compare(orig_text, new_text):
    a, b = extract_invariants(orig_text), extract_invariants(new_text)
    lines = ["=" * 62, "润色前后比对", "=" * 62]
    clean = True

    added = b["cites"] - a["cites"]
    removed = a["cites"] - b["cites"]
    if added:
        clean = False
        lines.append("\n[新增引用]  润色模式不得替作者新增引用，逐条核实是否真实存在：")
        lines += [f"  + {k} ×{n}" for k, n in added.items()]
    if removed:
        clean = False
        lines.append("\n[丢失引用]  改写时被吃掉的引用：")
        lines += [f"  - {k} ×{n}" for k, n in removed.items()]

    for key, name in (("labels", "\\label"), ("refs", "\\ref")):
        d_add, d_del = b[key] - a[key], a[key] - b[key]
        if d_add or d_del:
            clean = False
            lines.append(f"\n[{name} 变动]")
            lines += [f"  + {k}" for k in d_add] + [f"  - {k}" for k in d_del]

    m_add, m_del = b["math"] - a["math"], a["math"] - b["math"]
    if m_add or m_del:
        clean = False
        lines.append("\n[公式内容变动]  润色不应触碰公式：")
        lines += [f"  - {s[:70]}" for s in list(m_del)[:10]]
        lines += [f"  + {s[:70]}" for s in list(m_add)[:10]]

    n_add, n_del = b["numbers"] - a["numbers"], a["numbers"] - b["numbers"]
    if n_add or n_del:
        clean = False
        lines.append("\n[数字变动]  指标值、样本量、超参数不得改动：")
        lines.append(f"  消失: {', '.join(sorted(n_del)[:20]) or '无'}")
        lines.append(f"  新增: {', '.join(sorted(n_add)[:20]) or '无'}")

    if clean:
        lines.append("\n引用、标签、公式与数字全部保持一致。语言层改动可以放心交付。")
    return "\n".join(lines), clean


# ---------------------------------------------------------------- 入口
def read(path):
    if path == "-":
        return sys.stdin.read()
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def main():
    ap = argparse.ArgumentParser(description="方法类论文稿件机械检查")
    ap.add_argument("path", help="稿件路径，'-' 表示从标准输入读")
    ap.add_argument("--compare", metavar="EDITED",
                    help="给出润色后的稿件，比对引用、公式与数字是否被动过")
    args = ap.parse_args()

    text = read(args.path)

    if args.compare:
        out, clean = compare(text, read(args.compare))
        print(out)
        sys.exit(0 if clean else 1)

    prose, _ = strip_math(text)
    prose = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", " ", prose)

    rep = Report()
    check_dashes(text, rep)
    check_cjk_residue(text, rep)
    check_wording(prose, rep)
    check_consistency(prose, rep)
    check_acronyms(prose, rep)
    check_tense(prose, rep)
    check_sentences(prose, rep)
    check_numbers(prose, rep)

    print(rep.render())
    print("\n注：脚本只覆盖机械层面。挑战是否成立、设计与评估是否对应、"
          "贡献是否是设计知识，这些必须人工判断。")
    sys.exit(1 if rep.hard else (2 if rep.soft else 0))


if __name__ == "__main__":
    main()
