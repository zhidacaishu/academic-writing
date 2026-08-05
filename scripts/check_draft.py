#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方法类英文学术论文机械检查器。纯标准库，不联网。

仅接受标准输入或 UTF-8 编码的 .txt、.md、.tex 文件。脚本统一报告可疑位置，
以便将注意力用于需要人工判断的内容。

用法
    python check_draft.py draft.tex
    python check_draft.py orig.tex --compare new.tex

--compare 按原文顺序比对引用命令、交叉引用、公式、数字及应保持原样的
Markdown/LaTeX 源码。它能够发现这些对象的增删、改写、换序，并对局部绑定
线索变化给出人工复核提示；它不能证明其他语义完全不变。

退出码：0 未发现问题，1 发现确定性问题，2 仅发现需要人工判断的条目，
3 输入或参数错误。
"""

import argparse
import re
import statistics
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

# ---------------------------------------------------------------- 词表
# 分两级：HARD 表示按当前规则可直接判定的问题；SOFT 表示需要结合语境判断的项目。

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
    "sensitivity analyse", "reach the best",
]
CONTEXTUAL_WORDING = {
    "listed company": "确认是否具体指上市公司；若泛指企业，改用 firm/company",
    "hidden variable": "统计模型通常用 latent variable；确指未观测变量时可保留",
    "prior to": "before 通常更简洁，但时间或程序语境中可保留",
    "subsequent to": "after 通常更简洁，但时间或程序语境中可保留",
    "in the realm of": "滥用时压缩成 in；确指某一领域时可保留",
}
# 冗余结构。压缩后不损失正式度。
BLOAT = {
    "due to the fact that": "because",
    "in spite of the fact that": "although",
    "it should be noted that": "删除，直接说",
    "it is important to note that": "删除，直接说",
    "at this point in time": "now / currently",
    "the vast majority of": "most",
    "a wide array of": "various / 给数量",
    "a myriad of": "many / 给数量",
    "has the ability to": "can",
    "make an assumption that": "assume",
    "conduct an analysis of": "analyze",
    "serve to illustrate": "illustrate",
}
# 声称强度越界。
OVERCLAIM = [
    (r"\bis superior to\b", "无条件断言，改为限定范围的说法"),
    (r"\bsuperior than\b", "搭配错误，superior to"),
    (r"\bin general\b", "声称范围可能超过实验覆盖范围"),
    (r"\bthis is the first (paper|study|work)\b", "需加 to the best of our knowledge"),
    (r"\ba wide range of scenarios\b", "未做跨场景验证不能这样写"),
    (r"\bclearly (better|superior|outperforms)\b", "避免主观判断；改为报告具体数值"),
    (r"\b(greatly|obviously|undoubtedly|definitely|perfectly)\b", "程度副词无信息量"),
    (r"\bsignificantly (out)?perform", "有配对检验或秩和检验才能用 significantly"),
    (r"\bour (model|method|approach) is (efficient|interpretable|scalable|robust)\b",
     "声称必须配证据：指向图号、表号或复杂度"),
]
# 同一概念的写法变体。同篇内混用即报。
VARIANT_GROUPS = [
    ["data set", "dataset"],
    ["hyperparameter", "hyper-parameter", "hyper parameter"],
    ["overfitting", "over-fitting"],
    ["cross-validation", "cross validation"],
]
SPELLING_PAIRS = [
    ("analyze", "analyse"), ("modeling", "modelling"), ("behavior", "behaviour"),
    ("labeled", "labelled"), ("center", "centre"), ("optimize", "optimise"),
    ("characterize", "characterise"), ("generalize", "generalise"),
]
# 疑似过去时。方法类论文全篇统一使用现在时，命中处应逐项改写。
PAST_PATTERNS = [
    r"\bwe (collected|conducted|constructed|proposed|used|obtained|applied|"
    r"performed|adopted|developed|showed|found|achieved|trained|evaluated|"
    r"compared|selected|removed|computed|designed|built|implemented)\b",
    r"\b(was|were) (used|conducted|applied|adopted|performed|trained|evaluated|selected)\b",
]
ACRONYM_STOP = {
    "AI", "ML", "US", "UK", "EU", "PDF", "URL", "API", "CPU", "GPU", "RAM",
    "OK", "ID", "TV", "AND", "OR", "NOT", "THE", "A", "I", "II", "III", "IV",
}
SENT_ABBREV = {
    "et al.", "e.g.", "i.e.", "cf.", "vs.", "Fig.", "Eq.", "Sec.", "Tab.",
    "Ref.", "Dr.", "Prof.", "St.", "approx.", "resp.",
}

CJK_PUNCT = "\u3001\u3002\uff01\uff08\uff09\uff0c\uff1a\uff1b\uff1f\uff0e\u300a\u300b\u3010\u3011\u2026\u3000\uff05\uff06\uff1c\uff1e"
CJK_CHAR = re.compile(r"[\u4e00-\u9fff]+")

SUPPORTED_EXTENSIONS = {".txt", ".md", ".tex"}
VERBATIM_ENVS = {"verbatim", "Verbatim", "lstlisting", "minted"}
MATH_ENVS = {
    "math", "displaymath", "equation", "align", "alignat", "flalign",
    "gather", "multline", "eqnarray",
}
REF_COMMANDS = {
    "label", "ref", "eqref", "pageref", "autoref", "nameref",
    "vref", "cref", "Cref",
}
NON_PROSE_COMMANDS = {
    "begin", "end", "includegraphics", "input", "include", "bibliography",
    "bibliographystyle", "url", "path", "documentclass", "usepackage",
    "RequirePackage",
}
STRUCTURAL_COMMANDS = {
    "includegraphics", "input", "include", "bibliography", "bibliographystyle",
}
STRUCTURAL_ENVS = {"figure", "table", "tabular", "tabularx", "longtable"}
SOURCE_COMMANDS = {
    "documentclass", "usepackage", "RequirePackage", "newcommand",
    "renewcommand", "providecommand", "DeclareRobustCommand",
    "DeclareMathOperator", "def", "edef", "gdef", "xdef",
    "NewDocumentCommand", "RenewDocumentCommand",
    "ProvideDocumentCommand", "DeclareDocumentCommand", "newenvironment",
    "renewenvironment", "NewDocumentEnvironment", "RenewDocumentEnvironment",
    "ProvideDocumentEnvironment", "DeclareDocumentEnvironment",
}
SOURCE_COMMAND_RE = re.compile(
    r"\\(" + "|".join(
        re.escape(name) for name in sorted(SOURCE_COMMANDS, key=len, reverse=True)
    ) + r")\b(\*)?"
)
NUMBER_RE = re.compile(
    r"(?<![\w.])"
    r"[+\-\u2212]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-]?\d+)?(?:\s*(?:\\?%|\u2030))?"
    r"(?!\w)"
)


# ---------------------------------------------------------------- 基础设施
class DraftArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_usage(sys.stderr)
        self.exit(3, f"{self.prog}: error: {message}\n")


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


@dataclass(frozen=True)
class ProtectedEvent:
    kind: str
    command: str
    payload: tuple
    raw: str
    start: int
    end: int
    line: int

    @property
    def key(self):
        return self.kind, self.command, self.payload


def _normalize_newlines(value):
    return value.replace("\r\n", "\n").replace("\r", "\n")


def _is_escaped(text, pos):
    count = 0
    pos -= 1
    while pos >= 0 and text[pos] == "\\":
        count += 1
        pos -= 1
    return count % 2 == 1


def _overlaps(start, end, spans):
    return any(start < hi and end > lo for lo, hi in spans)


def _consume_group(text, pos, opener, closer):
    if pos >= len(text) or text[pos] != opener:
        return None
    depth = 0
    i = pos
    while i < len(text):
        if text[i] == opener and not _is_escaped(text, i):
            depth += 1
        elif text[i] == closer and not _is_escaped(text, i):
            depth -= 1
            if depth == 0:
                return i + 1, text[pos + 1:i]
        i += 1
    return None


def _find_unescaped(text, token, start):
    pos = text.find(token, start)
    while pos >= 0:
        if not _is_escaped(text, pos):
            return pos
        pos = text.find(token, pos + 1)
    return -1


def _event(kind, command, payload, text, start, end):
    return ProtectedEvent(
        kind, command, tuple(payload), text[start:end], start, end,
        line_of(text, start),
    )


def _scan_markdown_frontmatter(text, occupied):
    match = re.match(r"\A---[ \t]*(?:\r?\n|\r)", text)
    if not match:
        return []
    closing = re.search(r"(?m)^(?:---|\.\.\.)[ \t]*(?:\r?$)", text[match.end():])
    if not closing:
        return []
    end = match.end() + closing.end()
    event = _event(
        "frontmatter", "yaml", (_normalize_newlines(text[:end]),), text, 0, end
    )
    occupied.append((0, end))
    return [event]


def _scan_markdown_fences(text, occupied):
    events = []
    lines = text.splitlines(keepends=True)
    offsets = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)
    index = 0
    while index < len(lines):
        start = offsets[index]
        match = re.match(r" {0,3}(`{3,}|~{3,})", lines[index])
        if not match or _overlaps(start, start + len(lines[index]), occupied):
            index += 1
            continue
        fence = match.group(1)
        closing_re = re.compile(
            r" {0,3}" + re.escape(fence[0]) + r"{" + str(len(fence)) + r",}[ \t]*(?:\r?\n|\r)?$"
        )
        closing_index = index + 1
        while closing_index < len(lines) and not closing_re.fullmatch(lines[closing_index]):
            closing_index += 1
        end = (
            offsets[closing_index] + len(lines[closing_index])
            if closing_index < len(lines)
            else len(text)
        )
        raw = _normalize_newlines(text[start:end])
        events.append(_event("code_fence", fence[0], (raw,), text, start, end))
        occupied.append((start, end))
        index = closing_index + 1
    return events


def _scan_markdown_inline_code(text, occupied):
    events = []
    for opener in re.finditer(r"`+", text):
        start = opener.start()
        if _overlaps(start, opener.end(), occupied):
            continue
        size = opener.end() - start
        closing_re = re.compile(r"(?<!`)`{" + str(size) + r"}(?!`)")
        closing = closing_re.search(text, opener.end())
        if not closing or "\n\n" in text[opener.end():closing.start()]:
            continue
        end = closing.end()
        raw = _normalize_newlines(text[start:end])
        events.append(_event("inline_code", "`" * size, (raw,), text, start, end))
        occupied.append((start, end))
    return events


def _scan_environments(text, names, kind, occupied):
    events = []
    alternatives = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    pattern = re.compile(r"\\begin\s*\{(" + alternatives + r")(\*)?\}")
    for match in pattern.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        name = match.group(1) + (match.group(2) or "")
        end_pattern = re.compile(r"\\end\s*\{" + re.escape(name) + r"\}")
        end_match = end_pattern.search(text, match.end())
        if not end_match:
            continue
        start, end = match.start(), end_match.end()
        if _overlaps(start, end, occupied):
            continue
        raw = _normalize_newlines(text[start:end])
        events.append(_event(kind, name, (raw,), text, start, end))
        occupied.append((start, end))
    return events


def _scan_source_lines(text, occupied):
    events = []
    for match in SOURCE_COMMAND_RE.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        cursor = match.end()
        last_end = cursor
        if match.group(1) in {"def", "edef", "gdef", "xdef"}:
            brace = text.find("{", cursor)
            line_end = text.find("\n", cursor)
            if brace >= 0 and (line_end < 0 or brace < line_end):
                group = _consume_group(text, brace, "{", "}")
                if group:
                    last_end = group[0]
        else:
            while True:
                while cursor < len(text) and text[cursor].isspace():
                    cursor += 1
                if cursor < len(text) and text[cursor] == "[":
                    group = _consume_group(text, cursor, "[", "]")
                elif cursor < len(text) and text[cursor] == "{":
                    group = _consume_group(text, cursor, "{", "}")
                else:
                    group = None
                if not group:
                    break
                cursor, _ = group
                last_end = cursor
        if last_end == match.end():
            newline = text.find("\n", match.end())
            last_end = len(text) if newline < 0 else newline
        raw = _normalize_newlines(text[match.start():last_end])
        events.append(
            _event("source", match.group(1), (raw,), text, match.start(), last_end)
        )
        occupied.append((match.start(), last_end))
    return events


def _scan_structural_source(text, occupied):
    events = []
    env_names = "|".join(
        re.escape(name) for name in sorted(STRUCTURAL_ENVS, key=len, reverse=True)
    )
    env_re = re.compile(r"\\(begin|end)\s*\{(" + env_names + r")\}")
    table_ranges = []
    for match in env_re.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        action, name = match.group(1), match.group(2)
        pos = match.end()
        if action == "begin":
            while pos < len(text) and text[pos].isspace():
                pos += 1
            while pos < len(text) and text[pos] == "[":
                group = _consume_group(text, pos, "[", "]")
                if not group:
                    break
                pos, _ = group
                while pos < len(text) and text[pos].isspace():
                    pos += 1
            if name in {"tabular", "tabularx", "longtable"}:
                required = 2 if name == "tabularx" else 1
                for _ in range(required):
                    if pos >= len(text) or text[pos] != "{":
                        break
                    group = _consume_group(text, pos, "{", "}")
                    if not group:
                        break
                    pos, _ = group
                    while pos < len(text) and text[pos].isspace():
                        pos += 1
                end_match = re.search(
                    r"\\end\s*\{" + re.escape(name) + r"\}", text[pos:]
                )
                if end_match:
                    table_ranges.append((pos, pos + end_match.start()))
        raw = _normalize_newlines(text[match.start():pos])
        command = f"{action}:{name}"
        events.append(_event("structure", command, (raw,), text, match.start(), pos))
        occupied.append((match.start(), pos))

    command_re = re.compile(
        r"\\(" + "|".join(
            re.escape(name)
            for name in sorted(STRUCTURAL_COMMANDS, key=len, reverse=True)
        ) + r")\b"
    )
    for match in command_re.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        pos = match.end()
        while True:
            while pos < len(text) and text[pos].isspace():
                pos += 1
            opener, closer = (
                ("[", "]") if pos < len(text) and text[pos] == "[" else ("{", "}")
            )
            if pos >= len(text) or text[pos] not in "[{":
                break
            group = _consume_group(text, pos, opener, closer)
            if not group:
                break
            pos, _ = group
        raw = _normalize_newlines(text[match.start():pos])
        events.append(
            _event("structure", match.group(1), (raw,), text, match.start(), pos)
        )
        occupied.append((match.start(), pos))

    table_command_re = re.compile(
        r"\\(?:hline|toprule|midrule|bottomrule|cline|cmidrule)\b(?:\s*\{[^{}]*\})?"
    )
    for start, end in table_ranges:
        for match in re.finditer(r"(?<!\\)&|\\\\(?:\[[^\]\r\n]*\])?", text[start:end]):
            event_start, event_end = start + match.start(), start + match.end()
            if not _overlaps(event_start, event_end, occupied):
                events.append(
                    _event(
                        "table_structure", match.group(), (match.group(),),
                        text, event_start, event_end,
                    )
                )
                occupied.append((event_start, event_end))
        for match in table_command_re.finditer(text, start, end):
            if not _overlaps(match.start(), match.end(), occupied):
                raw = _normalize_newlines(match.group())
                events.append(
                    _event(
                        "table_structure", match.group().split("{")[0], (raw,),
                        text, match.start(), match.end(),
                    )
                )
                occupied.append((match.start(), match.end()))
    return events


def _scan_inline_verbs(text, occupied):
    events = []
    for match in re.finditer(r"\\verb\*?", text):
        if _overlaps(match.start(), match.end(), occupied) or match.end() >= len(text):
            continue
        delimiter = text[match.end()]
        if delimiter.isspace() or delimiter.isalnum():
            continue
        end = text.find(delimiter, match.end() + 1)
        if end < 0 or "\n" in text[match.end() + 1:end]:
            continue
        end += 1
        events.append(
            _event(
                "verbatim", "verb", (_normalize_newlines(text[match.start():end]),),
                text, match.start(), end,
            )
        )
        occupied.append((match.start(), end))
    return events


def _scan_comments(text, occupied):
    events = []
    offset = 0
    for line in text.splitlines(keepends=True):
        body_end = len(line.rstrip("\r\n"))
        for local_pos in range(body_end):
            if line[local_pos] != "%" or _is_escaped(line, local_pos):
                continue
            # 紧跟数字的 % 是百分号：LaTeX 正文里字面百分号必须写 \%，
            # 而 .md/.txt 稿常直接写 15%，误判会把整行正文当注释屏蔽。
            if local_pos and line[local_pos - 1].isdigit():
                continue
            start, end = offset + local_pos, offset + body_end
            if not _overlaps(start, end, occupied):
                raw = line[local_pos:body_end]
                events.append(_event("comment", "%", (raw,), text, start, end))
                occupied.append((start, end))
            break
        offset += len(line)
    return events


def _looks_like_inline_math(text, content_start, close):
    value = text[content_start:close].strip()
    if not value or "\n" in value:
        return False
    amount = r"\s*[+\-−]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?"
    return not (
        re.match(amount, text[content_start:])
        and re.match(amount, text[close + 1:])
    )


def _scan_math(text, occupied):
    events = _scan_environments(text, MATH_ENVS, "math", occupied)
    # 本轮新增的都是 math 事件，且扫描指针只向前走，因此进入循环前快照一次
    # 已占用位置即可；逐字符重扫 occupied 会让整体退化为 O(n^2)。
    blocked = bytearray(len(text))
    for lo, hi in occupied:
        for pos in range(max(0, lo), min(len(text), hi)):
            blocked[pos] = 1
    i = 0
    while i < len(text):
        if blocked[i]:
            i += 1
            continue
        opener = closer = command = None
        if text.startswith(r"\[", i) and not _is_escaped(text, i):
            opener, closer, command = r"\[", r"\]", r"\["
        elif text.startswith(r"\(", i) and not _is_escaped(text, i):
            opener, closer, command = r"\(", r"\)", r"\("
        elif text.startswith("$$", i) and not _is_escaped(text, i):
            opener = closer = command = "$$"
        elif text[i] == "$" and not _is_escaped(text, i):
            if i + 1 < len(text) and text[i + 1] == "$":
                i += 1
                continue
            opener = closer = command = "$"
        if opener is None:
            i += 1
            continue
        search_from = i + len(opener)
        close = _find_unescaped(text, closer, search_from)
        if command == "$":
            while close >= 0 and (
                (close + 1 < len(text) and text[close + 1] == "$")
                or (close > 0 and text[close - 1] == "$")
            ):
                close = _find_unescaped(text, closer, close + 1)
        if close < 0:
            i += len(opener)
            continue
        if command == "$" and not _looks_like_inline_math(text, search_from, close):
            i += len(opener)
            continue
        end = close + len(closer)
        if not _overlaps(i, end, occupied):
            raw = _normalize_newlines(text[i:end])
            events.append(_event("math", command, (raw,), text, i, end))
            occupied.append((i, end))
        i = end
    return events


def _is_citation_command(name):
    return bool(
        re.fullmatch(
            r"(?:cite|cites|citep|citet|citealp|citealt|citeauthor|citeyear|"
            r"citeyearpar|parencite|parencites|textcite|textcites|autocite|"
            r"autocites|footcite|footcites|smartcite|smartcites|supercite|"
            r"nocite|Cite|Cites|Parencite|Parencites|Textcite|Textcites)",
            name,
        )
    )


def _scan_protected_commands(text, occupied):
    events = []
    command_re = re.compile(r"\\([A-Za-z@]+)(\*)?")
    for match in command_re.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        name = match.group(1)
        lower = name.lower()
        is_citation = _is_citation_command(name)
        is_reference = name in REF_COMMANDS or lower in {item.lower() for item in REF_COMMANDS}
        if not is_citation and not is_reference:
            continue
        pos = match.end()
        groups = []
        mandatory = 0
        while True:
            while pos < len(text) and text[pos].isspace():
                pos += 1
            if pos < len(text) and text[pos] == "[":
                group = _consume_group(text, pos, "[", "]")
                if not group:
                    break
                pos, content = group
                groups.append(("optional", content))
                continue
            if pos < len(text) and text[pos] == "{":
                group = _consume_group(text, pos, "{", "}")
                if not group:
                    break
                pos, content = group
                groups.append(("required", content))
                mandatory += 1
                continue
            break
        if not mandatory:
            continue
        kind = "citation" if is_citation else ("label" if lower == "label" else "ref")
        command = name + (match.group(2) or "")
        events.append(_event(kind, command, groups, text, match.start(), pos))
        occupied.append((match.start(), pos))
    return events


def infer_latex(text):
    return bool(
        re.search(r"(?m)^[ \t]*%", text)
        or SOURCE_COMMAND_RE.search(text)
        or re.search(
            r"\\(?:begin\s*\{|(?:cite|cites|citep|citet|parencite|textcite)"
            r"\*?\b|label\s*\{|(?:eq|auto|page|name|v|c|C)?ref\s*\{|"
            r"includegraphics)\b",
            text,
            flags=re.I,
        )
    )


def collect_nonprose_events(text, is_latex=None, is_markdown=False):
    is_latex = infer_latex(text) if is_latex is None else is_latex
    occupied = []
    events = []
    if is_markdown:
        events += _scan_markdown_frontmatter(text, occupied)
        events += _scan_markdown_fences(text, occupied)
        events += _scan_markdown_inline_code(text, occupied)
    if is_latex:
        events += _scan_environments(text, VERBATIM_ENVS, "verbatim", occupied)
        events += _scan_inline_verbs(text, occupied)
        events += _scan_comments(text, occupied)
        events += _scan_source_lines(text, occupied)
        events += _scan_structural_source(text, occupied)
    events += _scan_math(text, occupied)
    events += _scan_protected_commands(text, occupied)
    return sorted(events, key=lambda item: item.start)


def mask_preserving_layout(text, spans):
    chars = list(text)
    for start, end in spans:
        for pos in range(max(0, start), min(len(chars), end)):
            if chars[pos] not in "\r\n":
                chars[pos] = " "
    return "".join(chars)


def build_prose_view(text, is_latex=None, is_markdown=False):
    r"""屏蔽非散文源码，同时保留 \emph{...} 等文本命令中的正文与原始行号。"""
    events = collect_nonprose_events(text, is_latex, is_markdown)
    view = mask_preserving_layout(text, [(event.start, event.end) for event in events])
    chars = list(view)
    command_re = re.compile(r"\\([A-Za-z@]+)(\*)?")
    for match in command_re.finditer(text):
        if not view[match.start():match.end()].strip():
            continue
        name = match.group(1)
        for pos in range(match.start(), match.end()):
            if chars[pos] not in "\r\n":
                chars[pos] = " "
        cursor = match.end()
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        while cursor < len(text) and text[cursor] == "[":
            group = _consume_group(text, cursor, "[", "]")
            if not group:
                break
            end, _ = group
            for pos in range(cursor, end):
                if chars[pos] not in "\r\n":
                    chars[pos] = " "
            cursor = end
            while cursor < len(text) and text[cursor].isspace():
                cursor += 1
        if name in NON_PROSE_COMMANDS:
            while cursor < len(text) and text[cursor] == "{":
                group = _consume_group(text, cursor, "{", "}")
                if not group:
                    break
                end, _ = group
                for pos in range(cursor, end):
                    if chars[pos] not in "\r\n":
                        chars[pos] = " "
                cursor = end
                while cursor < len(text) and text[cursor].isspace():
                    cursor += 1
    for pos, char in enumerate(chars):
        if char in "{}" and not _is_escaped(text, pos):
            chars[pos] = " "
    return "".join(chars)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def context(text, pos, span=34):
    lo, hi = max(0, pos - span), min(len(text), pos + span)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def split_sentences_with_spans(prose):
    protected = prose
    for ab in SENT_ABBREV:
        protected = re.sub(
            re.escape(ab),
            lambda match: match.group().replace(".", "\x00"),
            protected,
            flags=re.I,
        )
    boundaries = list(re.finditer(r"(?<=[.!?])\s+(?=[A-Z(])", protected))
    starts = [0] + [match.end() for match in boundaries]
    ends = [match.start() for match in boundaries] + [len(prose)]
    results = []
    for start, end in zip(starts, ends):
        raw = prose[start:end]
        leading = len(raw) - len(raw.lstrip())
        trailing = len(raw.rstrip())
        actual_start = start + leading
        actual_end = start + trailing
        if actual_end <= actual_start:
            continue
        sentence = re.sub(r"\s+", " ", prose[actual_start:actual_end]).strip()
        if sentence:
            results.append((actual_start, actual_end, sentence))
    return results


def split_sentences(prose):
    return [sentence for _, _, sentence in split_sentences_with_spans(prose)]


# ---------------------------------------------------------------- 各项检查
def _is_markdown_rule_line(text, pos):
    """Markdown 的分隔线、setext 下划线与表格分隔行只由 - | : 组成，不是破折号。"""
    start = text.rfind("\n", 0, pos) + 1
    end = text.find("\n", pos)
    line = text[start:] if end < 0 else text[start:end]
    return bool(re.fullmatch(r"[ \t|:-]+", line))


def check_dashes(text, rep, is_markdown=False):
    for m in re.finditer(r"\u2014{1,2}|(?<!-)---(?!-)", text):
        if is_markdown and "-" in m.group() and _is_markdown_rule_line(text, m.start()):
            continue
        rep.add("hard", "长破折号",
                f"L{line_of(text, m.start())}: …{context(text, m.start())}…")
    for m in re.finditer(r"(?<=\s)\u2013(?=\s)", text):
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
                f"L{line_of(text, m.start())}: 确认是否符合目标格式（LaTeX 用 `` ''） "
                f"…{context(text, m.start())}…")


def _scan_terms(prose, terms, rep, tier, section, note=None):
    low = prose.lower()
    for term in terms:
        for m in re.finditer(r"\b" + re.escape(term.lower()) + r"\b", low):
            tail = f"  → {note[term]}" if note else ""
            rep.add(tier, section,
                    f"L{line_of(prose, m.start())}: '{term}' …{context(prose, m.start())}…{tail}")


def check_wording(prose, rep):
    _scan_terms(prose, CN_ENGLISH, rep, "hard", "中式学术英语")
    _scan_terms(prose, list(BLOAT), rep, "hard", "冗余结构", note=BLOAT)
    _scan_terms(
        prose, list(CONTEXTUAL_WORDING), rep, "soft", "措辞需结合语境",
        note=CONTEXTUAL_WORDING,
    )
    low = prose.lower()
    for pat, why in OVERCLAIM:
        for m in re.finditer(pat, low):
            rep.add("soft", "声称强度",
                    f"L{line_of(prose, m.start())}: …{context(prose, m.start())}…  → {why}")
    if re.search(r"\betc\.", low):
        rep.add("soft", "兜底列举", "出现 etc.：列举应完整或说明选取标准")


def check_consistency(prose, rep):
    low = prose.lower()
    for group in VARIANT_GROUPS:
        found = {
            v: len(re.findall(r"\b" + re.escape(v) + r"s?\b", low)) for v in group
        }
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
    for m in re.finditer(r"\b[A-Z][A-Z0-9]+(?:-[A-Z0-9]+)*s?\b", prose):
        tok = m.group()
        base = tok[:-1] if tok.endswith("s") else tok
        if base in ACRONYM_STOP or base.isdigit():
            continue
        seen.setdefault(base, m.start())
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
                f"共 {len(hits)} 处。方法类论文全篇统一使用现在时；请逐项改写")
    for pos in sorted(hits)[:12]:
        rep.add("soft", "疑似过去时", f"L{line_of(prose, pos)}: …{context(prose, pos)}…")


def check_sentences(prose, rep):
    spans = split_sentences_with_spans(prose)
    sents = [sentence for _, _, sentence in spans]
    lengths = [len(sentence.split()) for sentence in sents if len(sentence.split()) > 2]
    for start, _, sentence in spans:
        length = len(sentence.split())
        if length > 45:
            rep.add(
                "soft", "超长句",
                f"L{line_of(prose, start)}: {length} 词：{sentence[:80]}…",
            )
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
        rep.add("soft", "句长分布", "变异系数偏低：句长分布可能过于均匀，需结合语境人工判断")
    if band > 0.55:
        rep.add("soft", "句长分布", "超过半数句子的长度集中在 15–25 词：应根据内容关系合并短句或拆分长句")
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
    if re.search(r"(?<![\w.])\.\d", prose) and re.search(r"\b0\.\d", prose):
        rep.add("hard", "数字格式", "同时出现 .5 与 0.5 两种写法")


# ---------------------------------------------------------------- 比对模式
def extract_protected_events(text, is_latex=None, is_markdown=False):
    events = collect_nonprose_events(text, is_latex, is_markdown)
    spans = [(event.start, event.end) for event in events]
    number_view = mask_preserving_layout(text, spans)
    for match in NUMBER_RE.finditer(number_view):
        raw = match.group()
        events.append(_event("number", "", (raw,), text, match.start(), match.end()))
    return sorted(events, key=lambda item: item.start)


def _binding_signature(view, event):
    if event.kind not in {
        "citation", "ref", "label", "math", "number", "comment", "verbatim",
    }:
        return None
    left_floor = max(
        view.rfind("\n\n", 0, event.start),
        view.rfind(".", 0, event.start),
        view.rfind("!", 0, event.start),
        view.rfind("?", 0, event.start),
    )
    right_candidates = [
        pos for pos in (
            view.find("\n\n", event.end),
            view.find(".", event.end),
            view.find("!", event.end),
            view.find("?", event.end),
        )
        if pos >= 0
    ]
    right_ceiling = min(right_candidates) if right_candidates else len(view)
    left_words = re.findall(
        r"[A-Za-z][A-Za-z'-]*", view[left_floor + 1:event.start].lower()
    )[-4:]
    right_words = re.findall(
        r"[A-Za-z][A-Za-z'-]*", view[event.end:right_ceiling].lower()
    )[:4]
    return tuple(left_words), tuple(right_words)


def _describe_event(event):
    raw = re.sub(r"\s+", " ", event.raw).strip()
    if len(raw) > 72:
        raw = raw[:69] + "..."
    return f"{event.kind} L{event.line}: {raw}"


def compare(orig_text, new_text, is_latex=None, is_markdown=False):
    old_events = extract_protected_events(orig_text, is_latex, is_markdown)
    new_events = extract_protected_events(new_text, is_latex, is_markdown)
    old_view = mask_preserving_layout(
        orig_text, [(event.start, event.end) for event in old_events]
    )
    new_view = mask_preserving_layout(
        new_text, [(event.start, event.end) for event in new_events]
    )
    lines = ["=" * 62, "润色前后比对", "=" * 62]
    old_keys = [event.key for event in old_events]
    new_keys = [event.key for event in new_events]
    matcher = SequenceMatcher(a=old_keys, b=new_keys, autojunk=False)
    hard_changes = []
    binding_changes = []

    for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(old_end - old_start):
                old_event = old_events[old_start + offset]
                new_event = new_events[new_start + offset]
                old_binding = _binding_signature(old_view, old_event)
                new_binding = _binding_signature(new_view, new_event)
                if old_binding is not None and old_binding != new_binding:
                    binding_changes.append((old_event, new_event, old_binding, new_binding))
            continue
        hard_changes.append((
            tag,
            old_events[old_start:old_end],
            new_events[new_start:new_end],
        ))

    if hard_changes:
        lines.append(
            "\n[受保护对象变动] 引用、交叉引用、公式、数字或受保护源码"
            "发生增删、改写或换序："
        )
        for tag, removed, added in hard_changes[:20]:
            lines.append(f"  {tag}:")
            lines += [f"    - {_describe_event(event)}" for event in removed[:6]]
            lines += [f"    + {_describe_event(event)}" for event in added[:6]]

    if binding_changes:
        lines.append(
            "\n[位置或绑定需人工复核] 对象内容与顺序未变，但所在句的局部"
            "文字锚点发生变化；确认数字、公式或引文仍支持同一项主张："
        )
        for old_event, new_event, old_binding, new_binding in binding_changes[:25]:
            lines.append(
                f"  {_describe_event(old_event)} → L{new_event.line}; "
                f"{old_binding} → {new_binding}"
            )

    if hard_changes:
        status = 1
    elif binding_changes:
        status = 2
    else:
        status = 0
        lines.append(
            "\n未检测到受保护对象的内容、相对顺序或局部绑定线索发生变化。"
        )
    lines.append(
        "\n限制：该结果只覆盖可机械观察的对象，不能证明其他语义完全不变；"
        "仍须人工复核主张强度、跨句指代和符号含义。"
    )
    return "\n".join(lines), status


# ---------------------------------------------------------------- 入口
def infer_markdown(text):
    if re.match(r"\A---[ \t]*(?:\r?\n|\r)", text) or re.search(
        r"(?m)^ {0,3}(?:`{3,}|~{3,})", text
    ):
        return True
    # 单反引号在 LaTeX 里是开引号（``quote''），不能据此判定为 Markdown。
    return bool(re.search(r"(?<!`)`[^`\r\n]+`(?!`)", text)) and not infer_latex(text)


def syntax_hints(paths, texts):
    suffixes = {
        Path(path).suffix.lower() for path in paths if path and path != "-"
    }
    is_latex = True if ".tex" in suffixes else None
    if ".md" in suffixes:
        return is_latex, True
    if ".tex" in suffixes:
        return is_latex, False
    return is_latex, any(infer_markdown(text) for text in texts)


def read(path):
    if path == "-":
        return sys.stdin.read()
    suffix = Path(path).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise ValueError(f"不支持 '{suffix or '无扩展名'}'；仅接受 {allowed} 或标准输入")
    with open(path, encoding="utf-8-sig", errors="strict") as f:
        return f.read()


def run_checks(text, is_latex=None, is_markdown=False):
    prose = build_prose_view(text, is_latex, is_markdown)
    rep = Report()
    check_dashes(prose, rep, is_markdown)
    check_cjk_residue(prose, rep)
    check_wording(prose, rep)
    check_consistency(prose, rep)
    check_acronyms(prose, rep)
    check_tense(prose, rep)
    check_sentences(prose, rep)
    check_numbers(prose, rep)
    return rep


def main():
    ap = DraftArgumentParser(description="方法类英文论文稿件机械检查")
    ap.add_argument(
        "path",
        help="UTF-8 .txt/.md/.tex 路径；'-' 表示从标准输入读取提示词中的文本",
    )
    ap.add_argument("--compare", metavar="EDITED",
                    help="润色后的 .txt/.md/.tex，按顺序比对受保护对象")
    args = ap.parse_args()
    if args.path == "-" and args.compare == "-":
        ap.error("原稿和修改稿不能同时从标准输入读取")

    try:
        text = read(args.path)
        edited = read(args.compare) if args.compare else None
    except (OSError, UnicodeError, ValueError) as exc:
        ap.error(str(exc))

    is_latex, is_markdown = syntax_hints(
        (args.path, args.compare), (text, edited or "")
    )
    if args.compare:
        out, status = compare(text, edited, is_latex, is_markdown)
        print(out)
        sys.exit(status)

    rep = run_checks(text, is_latex, is_markdown)
    print(rep.render())
    print("\n注：脚本只覆盖机械层面。挑战是否成立、设计与评估是否对应、"
          "贡献属于 artifact、设计知识还是 design theory，这些必须人工判断。")
    sys.exit(1 if rep.hard else (2 if rep.soft else 0))


if __name__ == "__main__":
    main()
