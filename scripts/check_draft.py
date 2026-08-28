#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方法类英文学术论文机械检查器。纯标准库，不联网。

接受标准输入、UTF-8 编码的 .txt/.md/.tex，以及 .docx（抽取正文散文后处理）。
脚本统一报告可疑位置，以便将注意力用于需要人工判断的内容。
未闭合的 Markdown 代码围栏会屏蔽其后全部内容，作为必改项报出。

用法
    python3 check_draft.py draft.tex
    python3 check_draft.py draft.tex --sentence-metrics
    python3 check_draft.py orig.tex --compare new.tex
    python3 check_draft.py paper.docx --extract > paper.md

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
import zipfile
import xml.etree.ElementTree as ET
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
    "literatures", "researches", "super parameter",
    "over fitting", "cold boot", "generate process", "calculate complexity",
    "comparison experiment", "robust test",
    "sensitivity analyse", "reach the best",
]
CONTEXTUAL_WORDING = {
    "listed company": "确认是否具体指上市公司；若泛指企业，改用 firm/company",
    "hidden variable": "统计模型通常用 latent variable；确指未观测变量时可保留",
    "prior to": "before 通常更简洁，但时间或程序语境中可保留",
    "subsequent to": "after 通常更简洁，但时间或程序语境中可保留",
    "in the realm of": "滥用时压缩成 in；确指某一领域时可保留",
    "target function": "优化目标通常用 objective function；确指目标映射时可保留",
    "adjust parameters": "若指超参数选择，用 tune hyperparameters；一般参数调整可保留",
    "the vast majority of": "证据支持很高比例时可保留；否则用 most 或直接报告比例",
    "serve to illustrate": "通常可压缩为 illustrate；强调作用或功能时可保留",
}
# 冗余结构。压缩后不损失正式度。
BLOAT = {
    "due to the fact that": "because",
    "in spite of the fact that": "although",
    "it should be noted that": "删除，直接说",
    "it is important to note that": "删除，直接说",
    "at this point in time": "now / currently",
    "a wide array of": "various / 给数量",
    "a myriad of": "many / 给数量",
    "has the ability to": "can",
    "make an assumption that": "assume",
    "conduct an analysis of": "analyze",
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
# .docx 只在结构预检通过后接受；.pdf、.rtf 与图片不接受。
EXTRACTABLE_EXTENSIONS = {".docx"}
WORD_NS = {
    "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "http://purl.oclc.org/ooxml/wordprocessingml/main",
}
MATH_NS = {
    "http://schemas.openxmlformats.org/officeDocument/2006/math",
    "http://purl.oclc.org/ooxml/officeDocument/math",
}
MC_NS = {"http://schemas.openxmlformats.org/markup-compatibility/2006"}
DOCX_REVISION_ELEMENTS = {
    "ins", "del", "moveFrom", "moveTo", "moveFromRangeStart", "moveFromRangeEnd",
    "moveToRangeStart", "moveToRangeEnd", "customXmlInsRangeStart",
    "customXmlInsRangeEnd", "customXmlDelRangeStart", "customXmlDelRangeEnd",
    "customXmlMoveFromRangeStart", "customXmlMoveFromRangeEnd",
    "customXmlMoveToRangeStart", "customXmlMoveToRangeEnd", "cellIns", "cellDel",
    "cellMerge", "numberingChange", "conflictIns", "conflictDel",
}
DOCX_LOSSY_ELEMENTS = {
    "tbl": "table",
    "comment": "comment",
    "commentRangeStart": "comment",
    "commentRangeEnd": "comment",
    "commentReference": "comment",
    "footnoteReference": "footnote",
    "endnoteReference": "endnote",
    "drawing": "drawing",
    "pict": "drawing",
    "object": "embedded_object",
    "txbxContent": "textbox",
    "fldSimple": "field",
    "fldChar": "field",
    "instrText": "field",
    "sdt": "content_control",
    "dataBinding": "content_control",
    "altChunk": "alt_chunk",
}
DOCX_ASSET_PREFIXES = {
    "word/media/": "media",
    "word/charts/": "chart",
    "word/diagrams/": "smartart",
    "word/embeddings/": "embedded_object",
}
MAX_DOCX_XML_BYTES = 64 * 1024 * 1024
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
# \u8fb9\u754c\u91c7\u7528 ASCII \u5b57\u7b26\u7c7b\u800c\u975e \w\u3002Python \u7684 \w \u5339\u914d\u6c49\u5b57\uff0c\u7528 \w \u4f5c\u65ad\u8a00\u4f1a\u5426\u51b3\u4e00\u5207
# \u7d27\u8d34\u6c49\u5b57\u7684\u6570\u5b57\uff08\u4e2d\u6587\u6392\u7248\u5199\u201c\u63d0\u53475%\u201d\uff0c\u4e0d\u52a0\u7a7a\u683c\uff09\uff0c\u81f4\u4f7f\u4e2d\u8bd1\u82f1 --compare \u5728\u539f\u7a3f
# \u4e00\u4fa7\u63d0\u53d6\u4e0d\u5230\u4efb\u4f55\u6570\u5b57\uff0c\u5bf9\u6570\u5b57\u6539\u52a8\u5b8c\u5168\u5931\u53bb\u9274\u522b\u529b\u3002
NUMBER_RE = re.compile(
    r"(?<![0-9A-Za-z_.])"
    r"[+\-\u2212]?(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+)"
    r"(?:[eE][+\-]?\d+)?(?:\s*(?:\\?%|\u2030))?"
    r"(?![0-9A-Za-z_])"
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


@dataclass(frozen=True)
class DocxFinding:
    level: str
    code: str
    part: str
    element: str
    count: int = 1


@dataclass(frozen=True)
class DocxPreflight:
    findings: tuple
    document_xml: bytes

    @property
    def has_blockers(self):
        return any(item.level == "block" for item in self.findings)

    @property
    def has_lossy(self):
        return any(item.level == "lossy" for item in self.findings)

    @property
    def has_info(self):
        return any(item.level == "info" for item in self.findings)

    @property
    def status(self):
        if self.has_blockers:
            return 1
        if self.has_lossy or self.has_info:
            return 2
        return 0

    def render(self):
        lines = ["=" * 62, "DOCX 预检", "=" * 62]
        if not self.findings:
            lines.append("\n未发现未决修订或已知复杂对象，可以进行纯文本处理。")
            return "\n".join(lines)
        labels = {
            "block": "阻断：文本版本不确定",
            "lossy": "有损：纯文本无法完整表示",
            "info": "提示",
        }
        for level in ("block", "lossy", "info"):
            selected = [item for item in self.findings if item.level == level]
            if not selected:
                continue
            lines.append(f"\n[{labels[level]}]")
            for item in selected:
                lines.append(
                    f"  {item.code}: {item.part} / {item.element} × {item.count}"
                )
        if self.has_blockers:
            lines.append(
                "\n请先在 Word 中接受或拒绝全部修订并另存清洁副本；"
                "硬阻断项不能通过有损抽取绕过。"
            )
        elif self.has_lossy:
            lines.append(
                "\n该文档不能安全投影为最终稿纯文本；仅可显式执行诊断性有损抽取。"
            )
        return "\n".join(lines)


@dataclass(frozen=True)
class LatexArgument:
    kind: str
    start: int
    end: int
    content_start: int
    content_end: int


@dataclass(frozen=True)
class LatexInvocation:
    name: str
    command: str
    start: int
    token_end: int
    end: int
    arguments: tuple
    issue: str = ""


@dataclass(frozen=True)
class CommandPolicy:
    editable_optional: tuple = ()
    editable_required: tuple = ()
    all_optional_text: bool = False


@dataclass(frozen=True)
class ProtectionScan:
    compare_events: tuple
    mask_spans: tuple
    parse_issues: tuple


TEXT_COMMAND_POLICIES = {
    name: CommandPolicy(editable_required=(0,))
    for name in {
        "title", "emph", "textbf", "textit", "textrm", "textsf", "textnormal",
        "textmd", "textup", "textsl", "textsc", "underline",
    }
}
TEXT_COMMAND_POLICIES.update({
    name: CommandPolicy(editable_required=(0,), all_optional_text=True)
    for name in {
        "part", "chapter", "section", "subsection", "subsubsection",
        "paragraph", "subparagraph", "caption",
    }
})
TEXT_COMMAND_POLICIES.update({
    "footnote": CommandPolicy(editable_required=(0,)),
    "href": CommandPolicy(editable_required=(1,)),
})


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


def _parse_latex_invocation(text, match):
    name = match.group(1)
    command = name + (match.group(2) or "")
    cursor = match.end()
    arguments = []
    issue = ""
    while True:
        while cursor < len(text) and text[cursor].isspace():
            cursor += 1
        if cursor >= len(text) or text[cursor] not in "[{":
            break
        opener = text[cursor]
        closer = "]" if opener == "[" else "}"
        group = _consume_group(text, cursor, opener, closer)
        if not group:
            issue = f"L{line_of(text, cursor)}: \\{command} 的参数 '{opener}' 未闭合"
            break
        end, _ = group
        arguments.append(
            LatexArgument(
                "optional" if opener == "[" else "required",
                cursor,
                end,
                cursor + 1,
                end - 1,
            )
        )
        cursor = end
    return LatexInvocation(
        name, command, match.start(), match.end(),
        arguments[-1].end if arguments else match.end(), tuple(arguments), issue,
    )


def _command_argument_is_editable(policy, argument, optional_index, required_index):
    if argument.kind == "optional":
        return policy.all_optional_text or optional_index in policy.editable_optional
    return required_index in policy.editable_required


def _scan_latex_commands(text, occupied):
    events = []
    mask_spans = []
    issues = []
    command_re = re.compile(r"\\([A-Za-z@]+)(\*)?")
    for match in command_re.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        invocation = _parse_latex_invocation(text, match)
        if invocation.issue:
            issues.append(invocation.issue)
        policy = TEXT_COMMAND_POLICIES.get(invocation.name)
        if policy is None:
            end = invocation.end
            raw = _normalize_newlines(text[invocation.start:end])
            events.append(
                _event(
                    "latex_command", invocation.command, (raw,),
                    text, invocation.start, end,
                )
            )
            mask_spans.append((invocation.start, end))
            occupied.append((invocation.start, end))
            continue
        argument_shape = tuple(argument.kind for argument in invocation.arguments)
        events.append(
            _event(
                "latex_shell", invocation.command, (argument_shape,),
                text, invocation.start, invocation.token_end,
            )
        )
        mask_spans.append((invocation.start, invocation.token_end))
        occupied.append((invocation.start, invocation.token_end))
        optional_index = required_index = 0
        for argument in invocation.arguments:
            editable = _command_argument_is_editable(
                policy, argument, optional_index, required_index
            )
            if argument.kind == "optional":
                optional_index += 1
            else:
                required_index += 1
            if editable:
                mask_spans.extend([
                    (argument.start, argument.content_start),
                    (argument.content_end, argument.end),
                ])
                occupied.extend([
                    (argument.start, argument.content_start),
                    (argument.content_end, argument.end),
                ])
                continue
            raw = _normalize_newlines(text[argument.start:argument.end])
            events.append(
                _event(
                    "latex_argument", invocation.command,
                    (argument.kind, raw), text, argument.start, argument.end,
                )
            )
            mask_spans.append((argument.start, argument.end))
            occupied.append((argument.start, argument.end))
    return events, mask_spans, issues


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


def _scan_markdown_fences(text, occupied, unclosed=None):
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
        if closing_index < len(lines):
            end = offsets[closing_index] + len(lines[closing_index])
        else:
            # 未闭合的围栏会屏蔽文件剩余部分，其后每一项检查都作用于空白。
            # 此处仍然屏蔽，否则代码会被当作散文检查；但须交由调用方报出。
            end = len(text)
            if unclosed is not None:
                unclosed.append((index + 1, fence))
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


def _scan_environments(text, names, kind, occupied, blocked=()):
    events = []
    alternatives = "|".join(re.escape(name) for name in sorted(names, key=len, reverse=True))
    pattern = re.compile(r"\\begin\s*\{(" + alternatives + r")(\*)?\}")
    for match in pattern.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        if _overlaps(match.start(), match.end(), blocked):
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


def _scan_source_lines(text, occupied, blocked=()):
    events = []
    for match in SOURCE_COMMAND_RE.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        if _overlaps(match.start(), match.end(), blocked):
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


def _scan_structural_source(text, occupied, blocked=()):
    events = []
    env_names = "|".join(
        re.escape(name) for name in sorted(STRUCTURAL_ENVS, key=len, reverse=True)
    )
    env_re = re.compile(r"\\(begin|end)\s*\{(" + env_names + r")\}")
    table_ranges = []
    for match in env_re.finditer(text):
        if _overlaps(match.start(), match.end(), occupied):
            continue
        if _overlaps(match.start(), match.end(), blocked):
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
        if _overlaps(match.start(), match.end(), blocked):
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


def _percent_is_a_sign(line, pos, body_end):
    """判定 % 为百分号而非注释起点。

    LaTeX 正文中的字面百分号须写作 \\%，但 .md/.txt 稿常直接写 15%、5 % 或 (%)。
    误判为注释将屏蔽整行正文，检查器随之输出无效的“未发现问题”，其代价高于
    漏剥一处注释，故判定向保留正文一侧倾斜。
    """
    before = line[:pos].rstrip()
    if before and before[-1].isdigit():
        return True
    after = line[pos + 1:body_end].lstrip()
    return before.endswith("(") and after.startswith(")")


def _comment_spans(text):
    """LaTeX 行注释的范围。每行只取第一个构成注释的 % 作为起点。"""
    spans = []
    offset = 0
    for line in text.splitlines(keepends=True):
        body_end = len(line.rstrip("\r\n"))
        for local_pos in range(body_end):
            if line[local_pos] != "%" or _is_escaped(line, local_pos):
                continue
            if _percent_is_a_sign(line, local_pos, body_end):
                continue
            spans.append((offset + local_pos, offset + body_end))
            break
        offset += len(line)
    return spans


def _scan_comments(text, occupied, spans):
    events = []
    for start, end in spans:
        if _overlaps(start, end, occupied):
            continue
        events.append(_event("comment", "%", (text[start:end],), text, start, end))
        occupied.append((start, end))
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


def _scan_math(text, occupied, comment_spans=()):
    events = _scan_environments(text, MATH_ENVS, "math", occupied, comment_spans)
    # 本轮新增的都是 math 事件，且扫描指针只向前走，因此进入循环前快照一次
    # 已占用位置即可；逐字符重扫 occupied 会让整体退化为 O(n^2)。
    # comment_spans 一并纳入位图：注释内的 $ 与 \[ 不构成公式。
    blocked = bytearray(len(text))
    for lo, hi in list(occupied) + list(comment_spans):
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
            r"includegraphics)\b|\\[A-Za-z@]+\*?\s*[\[{]",
            text,
            flags=re.I,
        )
    )


def scan_protection(text, is_latex=None, is_markdown=False):
    is_latex = infer_latex(text) if is_latex is None else is_latex
    occupied = []
    events = []
    mask_spans = []
    issues = []
    if is_markdown:
        events += _scan_markdown_frontmatter(text, occupied)
        events += _scan_markdown_fences(text, occupied)
        events += _scan_markdown_inline_code(text, occupied)
    # Markdown 没有 % 行注释，稿中的 % 一律是百分号。仅凭一处 \citep{} 即按
    # LaTeX 剥离注释，会屏蔽整行正文。
    comment_spans = _comment_spans(text) if is_latex and not is_markdown else []
    if is_latex:
        events += _scan_environments(text, VERBATIM_ENVS, "verbatim", occupied)
        events += _scan_inline_verbs(text, occupied)
        # 注释优先于宏定义与图表结构（`% \newcommand{...}` 归属注释）。该优先级
        # 由 comment_spans 显式表达，不依赖扫描顺序。
        events += _scan_source_lines(text, occupied, comment_spans)
        events += _scan_structural_source(text, occupied, comment_spans)
    # 公式须先于注释登记。公式内部的 % 归属公式；若先登记为注释，_overlaps 会
    # 跳过整个 \begin{equation} 或 \[...\]，公式既不被屏蔽，也不再是受保护对象，
    # --compare 随之把改动过的公式报为未变化。
    events += _scan_math(text, occupied, comment_spans)
    if is_latex:
        events += _scan_comments(text, occupied, comment_spans)
    events += _scan_protected_commands(text, occupied)
    mask_spans.extend((event.start, event.end) for event in events)
    if is_latex:
        command_events, command_masks, command_issues = _scan_latex_commands(
            text, occupied
        )
        opaque_spans = [
            (event.start, event.end)
            for event in command_events if event.kind == "latex_command"
        ]
        events = [
            event for event in events
            if not any(
                lo <= event.start and event.end <= hi
                for lo, hi in opaque_spans
            )
        ]
        events += command_events
        mask_spans += command_masks
        issues += command_issues
    return ProtectionScan(
        tuple(sorted(events, key=lambda item: item.start)),
        tuple(sorted(set(mask_spans))),
        tuple(issues),
    )


def collect_nonprose_events(text, is_latex=None, is_markdown=False):
    return list(scan_protection(text, is_latex, is_markdown).compare_events)


def unclosed_fences(text):
    """未闭合的 Markdown 代码围栏，返回 (行号, 围栏) 列表。"""
    occupied = []
    found = []
    _scan_markdown_frontmatter(text, occupied)
    _scan_markdown_fences(text, occupied, found)
    return found


def mask_preserving_layout(text, spans):
    chars = list(text)
    for start, end in spans:
        for pos in range(max(0, start), min(len(chars), end)):
            if chars[pos] not in "\r\n":
                chars[pos] = " "
    return "".join(chars)


def build_prose_view(text, is_latex=None, is_markdown=False):
    r"""屏蔽非散文源码，同时保留已登记文本命令中的正文与原始行号。"""
    scan = scan_protection(text, is_latex, is_markdown)
    return mask_preserving_layout(text, scan.mask_spans)


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def context(text, pos, span=34):
    lo, hi = max(0, pos - span), min(len(text), pos + span)
    return re.sub(r"\s+", " ", text[lo:hi]).strip()


def split_sentences_with_spans(prose):
    protected = prose
    for ab in SENT_ABBREV:
        # 左侧词边界与大小写敏感缺一不可。缺少边界时，`St.` 会命中 test.、cost.、
        # first.、most.、must.、robust.，`Fig.` 会命中 config.，相应的句子边界随之
        # 消失；整段合并为一句后必然触发无效的“超长句”，句长分布统计同时失真。
        protected = re.sub(
            r"(?<![A-Za-z])" + re.escape(ab),
            lambda match: match.group().replace(".", "\x00"),
            protected,
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


def sentence_length_metrics(prose):
    lengths = [
        len(sentence.split())
        for sentence in split_sentences(prose)
        if len(sentence.split()) > 2
    ]
    if not lengths:
        return None
    mean = statistics.mean(lengths)
    sd = statistics.pstdev(lengths)
    return {
        "count": len(lengths),
        "mean": mean,
        "sd": sd,
        "cv": sd / mean if mean else 0,
        "band": sum(1 for length in lengths if 15 <= length <= 25) / len(lengths),
    }


def render_sentence_metrics(prose):
    metrics = sentence_length_metrics(prose)
    if metrics is None:
        return "句长指标：没有足够的散文句子可供统计。"
    return (
        "句长指标："
        f"共 {metrics['count']} 句，均值 {metrics['mean']:.1f}，"
        f"标准差 {metrics['sd']:.1f}，变异系数 {metrics['cv']:.2f}，"
        f"15–25 词占 {metrics['band']:.0%}。"
        "该信息仅作描述，不产生问题等级，也不影响退出码。"
    )


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


def check_cjk_residue(text, rep, is_latex=False):
    for m in re.finditer(f"[{CJK_PUNCT}]", text):
        rep.add("hard", "全角标点残留",
                f"L{line_of(text, m.start())}: '{m.group()}' …{context(text, m.start())}…")
    for m in CJK_CHAR.finditer(text):
        rep.add("hard", "中文字符残留",
                f"L{line_of(text, m.start())}: …{context(text, m.start())}…")
    # 弯引号只有在 LaTeX 里才是问题（正文应写 `` ''）；.md/.txt 稿件里是正常写法。
    if not is_latex:
        return
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
            rep.add("soft", "写法不一致", f"{detail}  → 全文二选一")
    for us, uk in SPELLING_PAIRS:
        a = len(re.findall(rf"\b{us}\w*\b", low))
        b = len(re.findall(rf"\b{uk}\w*\b", low))
        if a and b:
            rep.add("soft", "英美拼写混用", f"{us}×{a} / {uk}×{b}  → INFORMS 系用美式")


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
    for start, _, sentence in spans:
        length = len(sentence.split())
        if length > 45:
            rep.add(
                "soft", "超长句",
                f"L{line_of(prose, start)}: {length} 词：{sentence[:80]}…",
            )
    # 规则是「连接词链条」：这些词连续出现在相邻段首。全文累计次数不构成问题。
    seps = list(re.finditer(r"\n[ \t]*\n", prose))
    para_starts = [0] + [sep.end() for sep in seps]
    para_ends = [sep.start() for sep in seps] + [len(prose)]
    lead = re.compile(
        r"\s*\b(moreover|furthermore|additionally|besides|in addition)\b", flags=re.I
    )
    heads = []
    for start, end in zip(para_starts, para_ends):
        m = lead.match(prose, start, end)
        heads.append((line_of(prose, m.start(1)), m.group(1).lower()) if m else None)
    run = []
    for head in heads + [None]:
        if head:
            run.append(head)
            continue
        if len(run) > 1:
            detail = "、".join(f"L{line} '{word}'" for line, word in run)
            rep.add("soft", "连接词堆叠", f"{len(run)} 个相邻段落以连接词开头：{detail}")
        run = []


def check_fences(text, rep):
    for line_no, fence in unclosed_fences(text):
        rep.add("hard", "未闭合代码围栏",
                f"L{line_no}: '{fence}' 缺少收尾围栏，其后内容全部未被检查")


def check_numbers(prose, rep):
    pcts = re.findall(r"(\d+)\.(\d+)\s*\\?%", prose)
    if pcts:
        places = Counter(len(d) for _, d in pcts)
        if len(places) > 1:
            rep.add(
                "soft", "数字精度需结合语境",
                f"检测到多种百分比小数位数：{dict(places)}；"
                "仅在同一表格、同一指标或直接可比数值中需要统一",
            )
    if re.search(r"(?<![\w.])\.\d", prose) and re.search(r"\b0\.\d", prose):
        rep.add("hard", "数字格式", "同时出现 .5 与 0.5 两种写法")


# ---------------------------------------------------------------- 比对模式
def _number_key(raw):
    """比对用的数字写法。中文原稿写 5%，LaTeX 稿须写 5\\%，两者是同一数值；
    不作归一化时，中译英比对中的每一个百分数都会报为受保护对象变动。"""
    return re.sub(r"\s*\\?%", "%", raw.replace("−", "-"))


def _events_with_numbers(text, scan):
    events = list(scan.compare_events)
    number_view = mask_preserving_layout(text, scan.mask_spans)
    for match in NUMBER_RE.finditer(number_view):
        events.append(
            _event("number", "", (_number_key(match.group()),),
                   text, match.start(), match.end())
        )
    return sorted(events, key=lambda item: item.start)


def extract_protected_events(text, is_latex=None, is_markdown=False):
    return _events_with_numbers(
        text, scan_protection(text, is_latex, is_markdown)
    )


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
    old_scan = scan_protection(orig_text, is_latex, is_markdown)
    new_scan = scan_protection(new_text, is_latex, is_markdown)
    old_events = _events_with_numbers(orig_text, old_scan)
    new_events = _events_with_numbers(new_text, new_scan)
    old_view = mask_preserving_layout(orig_text, old_scan.mask_spans)
    new_view = mask_preserving_layout(new_text, new_scan.mask_spans)
    lines = ["=" * 62, "润色前后比对", "=" * 62]
    old_keys = [event.key for event in old_events]
    new_keys = [event.key for event in new_events]
    matcher = SequenceMatcher(a=old_keys, b=new_keys, autojunk=False)
    hard_changes = []
    binding_changes = []
    parse_issues = [
        *(f"原稿 {issue}" for issue in old_scan.parse_issues),
        *(f"修改稿 {issue}" for issue in new_scan.parse_issues),
    ]

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

    if parse_issues:
        lines.append("\n[LaTeX 参数未闭合]")
        lines += [f"  {issue}" for issue in parse_issues]

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

    if hard_changes or parse_issues:
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


def _xml_name(tag):
    if not isinstance(tag, str):
        return "", ""
    if tag.startswith("{"):
        namespace, local = tag[1:].split("}", 1)
        return namespace, local
    return "", tag


def _docx_finding_level(namespace, local):
    if namespace in WORD_NS and (
        local in DOCX_REVISION_ELEMENTS or local.endswith("PrChange")
    ):
        return "block", "revision"
    if namespace in MC_NS and local == "AlternateContent":
        return "block", "alternate_content"
    if namespace in MATH_NS and local in {"oMath", "oMathPara"}:
        return "lossy", "equation"
    if namespace in WORD_NS and local in DOCX_LOSSY_ELEMENTS:
        return "lossy", DOCX_LOSSY_ELEMENTS[local]
    if namespace in WORD_NS and local == "trackRevisions":
        return "info", "revision_tracking_enabled"
    return None


def preflight_docx(path):
    counts = Counter()
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            if names.count("word/document.xml") != 1:
                detail = "缺少" if "word/document.xml" not in names else "包含重复的"
                raise ValueError(
                    f"'{path}' 不是有效的 .docx：{detail} word/document.xml"
                )
            xml_infos = [
                info for info in archive.infolist()
                if info.filename.startswith("word/") and info.filename.endswith(".xml")
            ]
            if sum(info.file_size for info in xml_infos) > MAX_DOCX_XML_BYTES:
                raise ValueError(
                    f"'{path}' 不是有效的 .docx：Word XML 解压后超过 64 MiB 安全上限"
                )
            document_xml = archive.read("word/document.xml")
            for part in sorted(info.filename for info in xml_infos):
                if names.count(part) > 1:
                    raise ValueError(f"'{path}' 不是有效的 .docx：包含重复成员 {part}")
                payload = document_xml if part == "word/document.xml" else archive.read(part)
                try:
                    root = ET.fromstring(payload)
                except ET.ParseError as exc:
                    raise ValueError(f"'{path}' 不是有效的 .docx：{part} XML 损坏：{exc}")
                for element in root.iter():
                    namespace, local = _xml_name(element.tag)
                    classified = _docx_finding_level(namespace, local)
                    if classified:
                        level, code = classified
                        counts[(level, code, part, local)] += 1
                    if part in {"word/footnotes.xml", "word/endnotes.xml"} and local in {
                        "footnote", "endnote"
                    }:
                        note_id = next(
                            (
                                value for key, value in element.attrib.items()
                                if _xml_name(key)[0] in WORD_NS
                                and _xml_name(key)[1] == "id"
                            ),
                            "",
                        )
                        if note_id not in {"-1", "0"}:
                            counts[("lossy", local, part, local)] += 1
                if part.startswith("word/header") or part.startswith("word/footer"):
                    namespace, local = _xml_name(root.tag)
                    if namespace in WORD_NS and any(
                        child_namespace in WORD_NS and child_local == "t"
                        for child_namespace, child_local in (
                            _xml_name(element.tag) for element in root.iter()
                        )
                    ):
                        counts[("lossy", "header_footer", part, local)] += 1
            for name in sorted(set(names)):
                for prefix, code in DOCX_ASSET_PREFIXES.items():
                    if name.startswith(prefix) and not name.endswith("/"):
                        counts[("lossy", code, name, "package_part")] += 1
                if name == "word/vbaProject.bin":
                    counts[("lossy", "macro_project", name, "package_part")] += 1
    except zipfile.BadZipFile:
        raise ValueError(f"'{path}' 不是有效的 .docx：无法作为 zip 打开")
    findings = tuple(
        DocxFinding(level, code, part, element, count)
        for (level, code, part, element), count in sorted(
            counts.items(), key=lambda item: (
                {"block": 0, "lossy": 1, "info": 2}[item[0][0]],
                item[0][1:],
            )
        )
    )
    return DocxPreflight(findings, document_xml)


def _docx_block_message(preflight):
    if preflight.has_blockers:
        return (
            "DOCX 含未决修订或不确定内容分支；请先在 Word 中接受或拒绝修订并另存清洁副本"
        )
    return "DOCX 含纯文本无法完整表示的复杂对象；最终用途处理已阻断"


def extract_docx(path, *, preflight=None, allow_lossy=False):
    preflight = preflight or preflight_docx(path)
    if preflight.has_blockers or (preflight.has_lossy and not allow_lossy):
        raise ValueError(_docx_block_message(preflight))
    try:
        root = ET.fromstring(preflight.document_xml)
    except ET.ParseError as exc:
        raise ValueError(f"'{path}' 不是有效的 .docx：word/document.xml XML 损坏：{exc}")
    body = next(
        (
            element for element in root.iter()
            if _xml_name(element.tag)[0] in WORD_NS
            and _xml_name(element.tag)[1] == "body"
        ),
        None,
    )
    if body is None:
        raise ValueError(f"'{path}' 不是有效的 .docx：word/document.xml 缺少 w:body")
    paragraphs = []
    for paragraph in body.iter():
        namespace, local = _xml_name(paragraph.tag)
        if namespace not in WORD_NS or local != "p":
            continue
        pieces = []
        for element in paragraph.iter():
            child_namespace, child_local = _xml_name(element.tag)
            if child_namespace not in WORD_NS:
                continue
            if child_local == "t" and element.text:
                pieces.append(element.text)
            elif child_local == "tab":
                pieces.append("\t")
            elif child_local in {"br", "cr"}:
                pieces.append("\n")
        value = "".join(pieces).strip()
        if value:
            paragraphs.append(value)
    return "\n\n".join(paragraphs) + ("\n" if paragraphs else "")


def read(path):
    if path == "-":
        return sys.stdin.read()
    suffix = Path(path).suffix.lower()
    if suffix in EXTRACTABLE_EXTENSIONS:
        return extract_docx(path)
    if suffix not in SUPPORTED_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_EXTENSIONS | EXTRACTABLE_EXTENSIONS))
        raise ValueError(f"不支持 '{suffix or '无扩展名'}'；仅接受 {allowed} 或标准输入")
    with open(path, encoding="utf-8-sig", errors="strict") as f:
        return f.read()


def run_checks(text, is_latex=None, is_markdown=False):
    is_latex = infer_latex(text) if is_latex is None else is_latex
    scan = scan_protection(text, is_latex, is_markdown)
    prose = mask_preserving_layout(text, scan.mask_spans)
    rep = Report()
    if is_markdown:
        check_fences(text, rep)
    for issue in scan.parse_issues:
        rep.add("hard", "LaTeX 参数未闭合", issue)
    check_dashes(prose, rep, is_markdown)
    check_cjk_residue(prose, rep, is_latex)
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
        help="UTF-8 .txt/.md/.tex 或 .docx 路径；'-' 表示从标准输入读取提示词中的文本",
    )
    ap.add_argument("--compare", metavar="EDITED",
                    help="润色后的 .txt/.md/.tex，按顺序比对受保护对象")
    ap.add_argument("--sentence-metrics", action="store_true",
                    help="附加句长描述统计；不产生问题等级，也不影响退出码")
    ap.add_argument("--extract", action="store_true",
                    help="将正文抽取为纯文本输出至标准输出，不执行检查；用于 .docx")
    ap.add_argument("--docx-preflight", action="store_true",
                    help="单独检查 DOCX 的未决修订与复杂对象")
    ap.add_argument("--allow-lossy-docx", action="store_true",
                    help="仅与 DOCX --extract 联用，允许诊断性有损纯文本投影")
    args = ap.parse_args()
    if args.path == "-" and args.compare == "-":
        ap.error("原稿和修改稿不能同时从标准输入读取")
    if args.extract and args.compare:
        ap.error("--extract 与 --compare 不能同时使用")
    if args.sentence_metrics and (args.compare or args.extract or args.docx_preflight):
        ap.error("--sentence-metrics 仅用于常规检查")
    if args.docx_preflight and (args.extract or args.compare or args.allow_lossy_docx):
        ap.error("--docx-preflight 必须单独使用")
    path_is_docx = args.path != "-" and Path(args.path).suffix.lower() == ".docx"
    if args.docx_preflight and not path_is_docx:
        ap.error("--docx-preflight 仅接受 .docx")
    if args.allow_lossy_docx and (not args.extract or not path_is_docx):
        ap.error("--allow-lossy-docx 只能与单个 DOCX 的 --extract 联用")

    try:
        preflights = {}
        for path in (args.path, args.compare):
            if path and path != "-" and Path(path).suffix.lower() == ".docx":
                preflights[path] = preflight_docx(path)
    except (OSError, UnicodeError, ValueError) as exc:
        ap.error(str(exc))

    if args.docx_preflight:
        result = preflights[args.path]
        print(result.render())
        sys.exit(result.status)

    blocked = [
        (path, result)
        for path, result in preflights.items()
        if result.has_blockers or (
            result.has_lossy and not (args.extract and args.allow_lossy_docx)
        )
    ]
    if blocked:
        for path, result in blocked:
            print(f"{path}:\n{result.render()}", file=sys.stderr)
        sys.exit(1)

    try:
        if path_is_docx:
            text = extract_docx(
                args.path,
                preflight=preflights[args.path],
                allow_lossy=args.allow_lossy_docx,
            )
        else:
            text = read(args.path)
        if args.compare:
            if args.compare in preflights:
                edited = extract_docx(
                    args.compare, preflight=preflights[args.compare]
                )
            else:
                edited = read(args.compare)
        else:
            edited = None
    except (OSError, UnicodeError, ValueError) as exc:
        ap.error(str(exc))

    for path, result in preflights.items():
        if result.findings and not (result.has_lossy and args.allow_lossy_docx):
            print(f"{path}:\n{result.render()}", file=sys.stderr)

    if args.extract:
        if args.allow_lossy_docx:
            print(preflights[args.path].render(), file=sys.stderr)
        print(text, end="" if text.endswith("\n") else "\n")
        sys.exit(2 if args.allow_lossy_docx else 0)

    is_latex, is_markdown = syntax_hints(
        (args.path, args.compare), (text, edited or "")
    )
    if args.compare:
        out, status = compare(text, edited, is_latex, is_markdown)
        print(out)
        sys.exit(status)

    rep = run_checks(text, is_latex, is_markdown)
    print(rep.render())
    if args.sentence_metrics:
        prose = build_prose_view(text, is_latex, is_markdown)
        print(f"\n{render_sentence_metrics(prose)}")
    print("\n注：脚本只覆盖机械层面。挑战是否成立、设计与评估是否对应、"
          "贡献属于 artifact、设计知识还是 design theory，这些必须人工判断。")
    sys.exit(1 if rep.hard else (2 if rep.soft else 0))


if __name__ == "__main__":
    main()
