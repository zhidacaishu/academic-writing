#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for check_draft.py."""

import io
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from scripts import check_draft


DOCX_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/></Types>'
)


def write_docx(path, paragraphs=(), *, document=None, parts=None):
    if document is None:
        body = "".join(
            f"<w:p><w:r><w:t xml:space=\"preserve\">{text}</w:t></w:r></w:p>"
            for text in paragraphs
        )
        document = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/'
            f'2006/main"><w:body>{body}</w:body></w:document>'
        )
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
        archive.writestr("word/document.xml", document)
        for name, payload in (parts or {}).items():
            archive.writestr(name, payload)


class CompareTests(unittest.TestCase):
    def assert_hard_change(self, original, edited):
        report, status = check_draft.compare(original, edited)
        self.assertEqual(status, 1, report)

    def test_detects_protected_content_and_order_changes(self):
        cases = [
            ("Accuracy is 0.9; loss is 0.2.", "Accuracy is 0.2; loss is 0.9."),
            ("Estimate: -1.5.", "Estimate: +1.5."),
            ("Estimate: .5.", "Estimate: .6."),
            ("Tolerance: 1e-5.", "Tolerance: 1e-4."),
            (r"Value \(x=y\).", r"Value \(x=z\)."),
            (
                r"\begin{multline}x=y\end{multline}",
                r"\begin{multline}x=z\end{multline}",
            ),
            (
                r"\begin{alignat}{2}x&=y\end{alignat}",
                r"\begin{alignat}{2}x&=z\end{alignat}",
            ),
            (r"Value $\text{a b}$.", r"Value $\text{ab}$."),
            (r"First $x=1$, then $y=2$.", r"First $y=2$, then $x=1$."),
            (r"Claim \citep*{old}.", r"Claim \citep*{new}."),
            (r"Claim \cites{same}{old}.", r"Claim \cites{same}{new}."),
            (r"See \ref {old}.", r"See \ref {new}."),
            (r"Claim \citep{x}.", r"Claim \citet{x}."),
            (r"See \ref{x}.", r"See \eqref{x}."),
            (r"Claim \citep[p. 3]{x}.", r"Claim \citep[p. 4]{x}."),
            (
                r"A \cite{alpha}; B \cite{beta}.",
                r"A \cite{beta}; B \cite{alpha}.",
            ),
        ]
        for original, edited in cases:
            with self.subTest(original=original, edited=edited):
                self.assert_hard_change(original, edited)

    def test_detects_comment_and_macro_changes(self):
        self.assert_hard_change("% keep this", "% changed")
        self.assert_hard_change(
            r"\newcommand{\vect}[1]{\mathbf{#1}}",
            r"\newcommand{\vect}[1]{\boldsymbol{#1}}",
        )
        self.assert_hard_change(
            "\\newcommand{\\longmacro}[1]{\n  First #1\n}",
            "\\newcommand{\\longmacro}[1]{\n  Second #1\n}",
        )

    def test_comment_inside_formula_does_not_disable_protection(self):
        cases = [
            (
                "\\begin{equation}\n\\label{eq:d}\nq = a + b p % TODO\n\\end{equation}",
                "\\begin{equation}\n\\label{eq:d}\nq = a + c p % TODO\n\\end{equation}",
            ),
            (
                "\\begin{align}\nx &= y % note\n\\end{align}",
                "\\begin{align}\nx &= z % note\n\\end{align}",
            ),
            (r"Value \[ x = y % note" "\n" r"\] here.",
             r"Value \[ x = z % note" "\n" r"\] here."),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                report, status = check_draft.compare(original, edited, is_latex=True)
                self.assertEqual(status, 1, report)
        kinds = [
            event.kind
            for event in check_draft.collect_nonprose_events(cases[0][0], is_latex=True)
        ]
        self.assertIn("math", kinds)

    def test_dollar_inside_a_comment_stays_a_comment(self):
        events = check_draft.collect_nonprose_events(
            "Text.\n% cost is $5$ here\nMore.", is_latex=True
        )
        self.assertEqual([event.kind for event in events], ["comment"])

    def test_numbers_adjacent_to_chinese_are_extracted(self):
        source = "我们在3个数据集上评估，召回率提升5%，样本量为12000。"
        self.assertEqual(
            [match.group() for match in check_draft.NUMBER_RE.finditer(source)],
            ["3", "5%", "12000"],
        )
        edited = r"We use 4 data sets; recall improves by 9\%, with 21000 users."
        _, status = check_draft.compare(source, edited)
        self.assertEqual(status, 1)

    def test_percent_escaping_alone_is_not_a_change(self):
        _, status = check_draft.compare(r"Rate: 5\%.", "Rate: 5 %.")
        self.assertEqual(status, 0)
        _, status = check_draft.compare("Rate: 5%.", "Rate: 50%.")
        self.assertEqual(status, 1)

    def test_binding_change_requires_review(self):
        report, status = check_draft.compare(
            "Accuracy is 0.9; loss is 0.2.",
            "Loss is 0.9; accuracy is 0.2.",
        )
        self.assertEqual(status, 2, report)
        self.assertIn("绑定需人工复核", report)

    def test_moved_comment_requires_review(self):
        report, status = check_draft.compare(
            "Claim A. % keep\nClaim B.",
            "Claim A.\nClaim B. % keep",
            is_latex=True,
        )
        self.assertEqual(status, 2, report)

    def test_line_shift_alone_is_not_a_change(self):
        report, status = check_draft.compare(
            r"Claim is supported \citep{x}.",
            "Background sentence.\n" + r"Claim is supported \citep{x}.",
        )
        self.assertEqual(status, 0, report)

    def test_identical_text_is_clean_but_report_states_limit(self):
        report, status = check_draft.compare(
            r"At 5%, \(x=1\) \citep{x}.",
            r"At 5%, \(x=1\) \citep{x}.",
        )
        self.assertEqual(status, 0, report)
        self.assertIn("不能证明其他语义完全不变", report)

    def test_markdown_source_regions_are_protected(self):
        cases = [
            ("---\ntitle: Old\n---\nText.", "---\ntitle: New\n---\nText."),
            ("Use `old_name`.", "Use `new_name`."),
            ("```text\nold\n```\nText.", "```text\nnew\n```\nText."),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                report, status = check_draft.compare(
                    original, edited, is_markdown=True
                )
                self.assertEqual(status, 1, report)

    def test_latex_structural_source_is_protected(self):
        cases = [
            (
                r"\includegraphics[width=\textwidth]{old.pdf}",
                r"\includegraphics[width=\textwidth]{new.pdf}",
            ),
            (
                "\\begin{figure}[ht]\n\\caption{Text}\n\\end{figure}",
                "\\begin{figure}[p]\n\\caption{Text}\n\\end{figure}",
            ),
            (
                "\\begin{tabular}{lc}\nA & B \\\\\n\\end{tabular}",
                "\\begin{tabular}{ll}\nA & B \\\\\n\\end{tabular}",
            ),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                self.assert_hard_change(original, edited)

    def test_common_macro_definition_forms_are_protected(self):
        cases = [
            (
                r"\DeclareRobustCommand{\vect}[1]{\mathbf{#1}}",
                r"\DeclareRobustCommand{\vect}[1]{\boldsymbol{#1}}",
            ),
            (
                r"\NewDocumentCommand{\vect}{m}{\mathbf{#1}}",
                r"\NewDocumentCommand{\vect}{m}{\boldsymbol{#1}}",
            ),
            (
                "\\newcommand*{\\longmacro}[1]{\n  First #1\n}",
                "\\newcommand*{\\longmacro}[1]{\n  Second #1\n}",
            ),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                self.assert_hard_change(original, edited)

    def test_uncommenting_macro_definition_is_detected(self):
        self.assert_hard_change(
            r"% \newcommand{\vect}[1]{\mathbf{#1}}",
            r"\newcommand{\vect}[1]{\mathbf{#1}}",
        )

    def test_unknown_command_is_frozen_but_registered_text_is_editable(self):
        self.assert_hard_change(r"A \excite{old}.", r"A \excite{new}.")
        for original, edited in [
            (r"\caption{Old caption}", r"\caption{New caption}"),
            (r"\section{Old heading}", r"\section{New heading}"),
            (r"\emph{Old text}", r"\emph{New text}"),
        ]:
            with self.subTest(original=original):
                report, status = check_draft.compare(
                    original, edited, is_latex=True
                )
                self.assertEqual(status, 0, report)

    def test_unknown_command_arguments_and_shell_are_frozen(self):
        cases = [
            (r"\custom[old]{same}", r"\custom[new]{same}"),
            (r"\custom[mode]{old}", r"\custom[mode]{new}"),
            (r"\custom{same}", r"\changed{same}"),
            (r"\url{https://old.example}", r"\url{https://new.example}"),
            (r"\path{old/file}", r"\path{new/file}"),
            (r"\begin{itemize}", r"\begin{enumerate}"),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                self.assert_hard_change(original, edited)

    def test_known_text_command_argument_policies(self):
        hard_cases = [
            (
                r"\href{https://old.example}{same anchor}",
                r"\href{https://new.example}{same anchor}",
            ),
            (r"\footnote[1]{same text}", r"\footnote[2]{same text}"),
            (r"\caption[Short]{Long}", r"\caption[Short]{Long}".replace("caption", "caption*")),
            (r"\emph{See \citep{old}.}", r"\emph{See \citep{new}.}"),
        ]
        for original, edited in hard_cases:
            with self.subTest(original=original):
                self.assert_hard_change(original, edited)
        for original, edited in [
            (
                r"\href{https://same.example}{old anchor}",
                r"\href{https://same.example}{new anchor}",
            ),
            (r"\footnote{Old note}", r"\footnote{New note}"),
            (r"\caption[Old short]{Old long}", r"\caption[New short]{New long}"),
        ]:
            with self.subTest(original=original):
                report, status = check_draft.compare(original, edited, is_latex=True)
                self.assertEqual(status, 0, report)

    def test_unknown_outer_command_does_not_duplicate_nested_events(self):
        events = check_draft.collect_nonprose_events(
            r"\unknown{See \citep{x} and $y=1$.}", is_latex=True
        )
        self.assertEqual([event.kind for event in events], ["latex_command"])

    def test_unclosed_latex_argument_is_a_hard_failure(self):
        text = r"\unknown{broken argument. Following prose remains visible."
        report = check_draft.run_checks(text, is_latex=True)
        self.assertIn("LaTeX 参数未闭合", report.hard)
        output, status = check_draft.compare(text, text, is_latex=True)
        self.assertEqual(status, 1, output)
        self.assertIn("参数未闭合", output)


class ProseViewTests(unittest.TestCase):
    def test_tex_comments_are_not_checked_as_prose(self):
        report = check_draft.run_checks(
            "% 中文注释：不要修改 —\nEnglish prose.", is_latex=True
        )
        self.assertNotIn("中文字符残留", report.hard)
        self.assertNotIn("全角标点残留", report.hard)
        self.assertNotIn("长破折号", report.hard)

    def test_verbatim_content_is_not_checked_as_prose(self):
        text = (
            "\\begin{verbatim}\n中文 — with the rapid development of\n"
            "\\end{verbatim}\nEnglish prose.\n"
            "\\verb|中文 — with the rapid development of|"
        )
        report = check_draft.run_checks(text, is_latex=True)
        self.assertNotIn("中文字符残留", report.hard)
        self.assertNotIn("长破折号", report.hard)
        self.assertNotIn("中式学术英语", report.hard)

    def test_escaped_percent_is_not_a_comment(self):
        view = check_draft.build_prose_view(r"Coverage is 10\%.", is_latex=True)
        self.assertIn("Coverage is 10", view)

    def test_text_inside_formatting_command_is_checked(self):
        report = check_draft.run_checks(
            r"\emph{with the rapid development of markets}", is_latex=True
        )
        self.assertIn("中式学术英语", report.hard)

    def test_unknown_no_argument_command_only_masks_token(self):
        report = check_draft.run_checks(
            r"\unknown with the rapid development of markets", is_latex=True
        )
        self.assertIn("中式学术英语", report.hard)

    def test_unknown_arguments_are_not_checked_as_prose(self):
        report = check_draft.run_checks(
            r"\unknown[中文]{with the rapid development of markets}", is_latex=True
        )
        self.assertNotIn("中文字符残留", report.hard)
        self.assertNotIn("中式学术英语", report.hard)

    def test_registered_text_arguments_remain_prose(self):
        for text in [
            r"\caption[with the rapid development of markets]{Clean title}",
            r"\footnote{with the rapid development of markets}",
            r"\href{https://example.test}{with the rapid development of markets}",
        ]:
            with self.subTest(text=text):
                report = check_draft.run_checks(text, is_latex=True)
                self.assertIn("中式学术英语", report.hard)

    def test_legal_ai_associated_words_are_not_checked(self):
        text = (
            "We delve into an intricate and pivotal problem and showcase a "
            "multifaceted, nuanced, and comprehensive analysis."
        )
        report = check_draft.run_checks(text, is_latex=False)
        sections = set(report.hard) | set(report.soft)
        self.assertFalse(any("AI" in section for section in sections))

    def test_grammar_sensitive_hyphenation_is_not_reported(self):
        text = (
            "State-of-the-art methods represent the state of the art. "
            "Long-tail items occur in the long tail. "
            "A real-world study reflects the real world. "
            "Gauss–Newton optimization is used."
        )
        report = check_draft.run_checks(text, is_latex=False)
        self.assertNotIn("写法不一致", report.soft)
        self.assertNotIn("en dash 用于句内", report.soft)

    def test_formula_mask_preserves_real_line_number(self):
        text = (
            "Line one.\n"
            "$$\n"
            "x=y\n"
            "$$\n"
            "Line five.\n"
            "With the rapid development of markets, firms adapt."
        )
        report = check_draft.run_checks(text, is_latex=True)
        item = report.hard["中式学术英语"][0]
        self.assertIn("L6:", item)

    def test_short_text_still_reports_long_sentence(self):
        text = " ".join(["word"] * 60) + "."
        report = check_draft.run_checks(text, is_latex=False)
        self.assertIn("超长句", report.soft)

    def test_connective_chain_needs_adjacent_paragraph_starts(self):
        chained = (
            "We estimate the model on public data.\n\n"
            "Moreover, the effect persists in the holdout sample.\n\n"
            "In addition, the ranking of the baselines is stable.\n"
        )
        report = check_draft.run_checks(chained, is_latex=False)
        self.assertIn("连接词堆叠", report.soft)
        item = report.soft["连接词堆叠"][0]
        self.assertIn("L3 'moreover'", item)
        self.assertIn("L5 'in addition'", item)
        apart = (
            "Moreover, the effect persists in the holdout sample.\n\n"
            "The ranking of the baselines is stable.\n\n"
            "Furthermore, the remaining gain is small.\n"
        )
        report = check_draft.run_checks(apart, is_latex=False)
        self.assertNotIn("连接词堆叠", report.soft)
        however = (
            "However, the effect is small.\n\n"
            "Estimates remain stable. However, standard errors grow.\n\n"
            "However, the ranking is unchanged.\n"
        )
        report = check_draft.run_checks(however, is_latex=False)
        self.assertNotIn("连接词堆叠", report.soft)

    def test_markdown_source_regions_are_not_checked_as_prose(self):
        cases = [
            "---\ntitle: 中文 —\n---\nEnglish prose.",
            "```text\n中文 — with the rapid development of\n```\nEnglish prose.",
            "Use `中文 — with the rapid development of` as a literal.",
        ]
        for text in cases:
            with self.subTest(text=text):
                report = check_draft.run_checks(text, is_markdown=True)
                self.assertNotIn("中文字符残留", report.hard)
                self.assertNotIn("长破折号", report.hard)
                self.assertNotIn("中式学术英语", report.hard)

    def test_horizontal_rule_is_not_frontmatter(self):
        text = "English prose.\n---\nWith the rapid development of markets, firms adapt."
        report = check_draft.run_checks(text, is_markdown=True)
        self.assertIn("中式学术英语", report.hard)

    def test_currency_does_not_create_false_inline_math(self):
        cases = [
            "Revenue rose from $5 million in 2020 to $7 million in 2021.",
            "The price range is $5-$7.",
        ]
        for prose in cases:
            with self.subTest(prose=prose):
                view = check_draft.build_prose_view(prose, is_latex=False)
                self.assertIn("5", view)
        for math in ("Value $x=1$ remains.", "Value $5$ remains."):
            with self.subTest(math=math):
                math_view = check_draft.build_prose_view(math, is_latex=False)
                self.assertNotIn(math.split("$")[1], math_view)

    def test_percent_sign_is_not_a_latex_comment(self):
        draft = "Recall improves by 15% over the baseline \\citep{du2016}."
        view = check_draft.build_prose_view(draft, *check_draft.syntax_hints(
            ("draft.md",), (draft,)
        ))
        self.assertIn("over the baseline", view)
        self.assertNotIn("keep", check_draft.build_prose_view(
            "Text. % keep this", is_latex=True
        ))

    def test_markdown_rule_lines_are_not_em_dashes(self):
        clean = "| M | HR |\n|---|---|\n| A | 0.2 |\n\n---\n\nHeading\n---\n\nText."
        report = check_draft.run_checks(clean, is_markdown=True)
        self.assertNotIn("长破折号", report.hard)
        report = check_draft.run_checks("A model---the best---wins.", is_markdown=True)
        self.assertIn("长破折号", report.hard)

    def test_abbreviated_reference_is_not_a_missing_leading_zero(self):
        report = check_draft.run_checks(
            "See Fig.5 for details. The threshold is 0.5.", is_latex=False
        )
        self.assertNotIn("数字格式", report.hard)
        report = check_draft.run_checks("Values are .5 and 0.5.", is_latex=False)
        self.assertIn("数字格式", report.hard)

    def test_plural_variants_and_acronyms_are_checked(self):
        report = check_draft.run_checks(
            "We tune two hyperparameters. Each hyper-parameter matters.",
            is_latex=False,
        )
        self.assertIn("写法不一致", report.soft)
        report = check_draft.run_checks("We study SOEs and TMTs.", is_latex=False)
        self.assertEqual(len(report.soft["缩写首现未定义"]), 2)
        report = check_draft.run_checks(
            "We study state-owned enterprises (SOEs). SOEs differ.", is_latex=False
        )
        self.assertNotIn("缩写首现未定义", report.soft)

    def test_variant_spelling_is_softer_than_british_american_mix(self):
        report = check_draft.run_checks(
            "We tune the hyperparameter and report every hyper-parameter.",
            is_latex=False,
        )
        self.assertIn("写法不一致", report.soft)
        self.assertNotIn("写法不一致", report.hard)
        report = check_draft.run_checks(
            "We analyze the sample and then analyse the residuals.", is_latex=False
        )
        self.assertIn("英美拼写混用", report.hard)

    def test_curly_quotes_are_reported_only_for_latex(self):
        draft = "We call this a “regime” of behavior."
        report = check_draft.run_checks(draft, is_latex=True)
        self.assertIn("弯引号", report.soft)
        report = check_draft.run_checks(draft, is_latex=False, is_markdown=True)
        self.assertNotIn("弯引号", report.soft)
        report = check_draft.run_checks(draft)
        self.assertNotIn("弯引号", report.soft)
        report = check_draft.run_checks(
            r"We follow \citep{du2016} and call this a “regime”."
        )
        self.assertIn("弯引号", report.soft)

    def test_latex_quotes_do_not_trigger_markdown_inline_code(self):
        draft = "We call a `mode' of behavior a `regime' in this study."
        is_latex, is_markdown = check_draft.syntax_hints(("draft.tex",), (draft,))
        self.assertFalse(is_markdown)
        self.assertIn(
            "of behavior",
            check_draft.build_prose_view(draft, is_latex, is_markdown),
        )

    def test_spaced_percent_does_not_mask_the_rest_of_the_line(self):
        draft = (
            "Recall improves by 5 % over the baseline \\citep{du2016}, "
            "with the rapid development of the market.\n\n"
            "The share of censored orders (%) is reported, and so on.\n"
        )
        for is_markdown in (True, False):
            with self.subTest(is_markdown=is_markdown):
                report = check_draft.run_checks(draft, is_markdown=is_markdown)
                self.assertEqual(len(report.hard["中式学术英语"]), 2)
        self.assertNotIn(
            "keep",
            check_draft.build_prose_view("Text. % keep this", is_latex=True),
        )

    def test_unclosed_code_fence_is_reported(self):
        draft = (
            "Intro sentence.\n\n```\nfor i in 1..n\n\n"
            "With the rapid development of markets, firms adapt.\n"
        )
        report = check_draft.run_checks(draft, is_markdown=True)
        self.assertIn("未闭合代码围栏", report.hard)
        closed = draft.replace("for i in 1..n\n", "for i in 1..n\n```\n")
        report = check_draft.run_checks(closed, is_markdown=True)
        self.assertNotIn("未闭合代码围栏", report.hard)
        self.assertIn("中式学术英语", report.hard)

    def test_sentence_final_st_is_not_an_abbreviation(self):
        prose = (
            "We evaluate the model on the held-out test. "
            "The proposed design attains the lowest cost. "
            "This is the first result."
        )
        self.assertEqual(len(check_draft.split_sentences(prose)), 3)
        self.assertNotIn("超长句", check_draft.run_checks(prose, is_latex=False).soft)
        kept = "Zhang et al. (2021) report gains. St. Louis is the site."
        self.assertEqual(len(check_draft.split_sentences(kept)), 2)

    def test_contextual_wording_is_not_a_hard_failure(self):
        report = check_draft.run_checks(
            "Prior to estimation, the listed company model includes a hidden variable.",
            is_latex=False,
        )
        self.assertNotIn("中式学术英语", report.hard)
        self.assertNotIn("冗余结构", report.hard)
        self.assertTrue(report.soft)


class InputTests(unittest.TestCase):
    def test_supported_extensions_and_utf8_bom(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "draft.TXT"
            path.write_text("\ufeffEnglish text.", encoding="utf-8")
            self.assertEqual(check_draft.read(str(path)), "English text.")

    def test_rejects_unsupported_extensions(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            for suffix in (".pdf", ".rtf", ".png"):
                path = Path(temp_dir) / f"draft{suffix}"
                path.write_bytes(b"not a supported text input")
                with self.subTest(suffix=suffix):
                    with self.assertRaises(ValueError):
                        check_draft.read(str(path))

    def test_docx_prose_is_extracted(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "paper.docx"
            write_docx(path, [
                "With the rapid development of e-commerce, firms adapt.",
                "Recall improves by 12.5% &amp; precision by 3%.",
            ])
            text = check_draft.read(str(path))
        self.assertEqual(
            text,
            "With the rapid development of e-commerce, firms adapt.\n\n"
            "Recall improves by 12.5% & precision by 3%.\n",
        )
        report = check_draft.run_checks(text)
        self.assertIn("中式学术英语", report.hard)

    def test_docx_preflight_is_namespace_prefix_independent(self):
        document = (
            '<x:document xmlns:x="http://schemas.openxmlformats.org/'
            'wordprocessingml/2006/main"><x:body><x:p><x:r><x:t>'
            'Prefix independent.</x:t></x:r></x:p></x:body></x:document>'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "paper.docx"
            write_docx(path, document=document)
            result = check_draft.preflight_docx(path)
            self.assertEqual(result.status, 0)
            self.assertEqual(check_draft.read(str(path)), "Prefix independent.\n")

    def test_unresolved_docx_revision_families_block_extraction(self):
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        for element in [
            "ins", "del", "moveFrom", "moveTo", "moveFromRangeStart",
            "moveToRangeEnd", "cellIns", "numberingChange", "rPrChange",
            "pPrChange", "tblPrChange", "sectPrChange",
        ]:
            document = (
                f'<w:document xmlns:w="{w_ns}"><w:body><w:p>'
                f'<w:{element}><w:r><w:t>Unresolved.</w:t></w:r></w:{element}>'
                '</w:p></w:body></w:document>'
            )
            with self.subTest(element=element), tempfile.TemporaryDirectory() as temp_dir:
                path = Path(temp_dir) / "revision.docx"
                write_docx(path, document=document)
                result = check_draft.preflight_docx(path)
                self.assertTrue(result.has_blockers)
                with self.assertRaises(ValueError):
                    check_draft.read(str(path))

    def test_revision_in_secondary_story_blocks_extraction(self):
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        header = (
            f'<w:hdr xmlns:w="{w_ns}"><w:p><w:ins><w:r>'
            '<w:t>Header insertion.</w:t></w:r></w:ins></w:p></w:hdr>'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "revision.docx"
            write_docx(path, ["Clean body."], parts={"word/header1.xml": header})
            result = check_draft.preflight_docx(path)
        self.assertTrue(result.has_blockers)
        self.assertTrue(any(item.part == "word/header1.xml" for item in result.findings))

    def test_alternate_content_blocks_but_tracking_setting_only_informs(self):
        mc_ns = "http://schemas.openxmlformats.org/markup-compatibility/2006"
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        alternate = (
            f'<w:document xmlns:w="{w_ns}" xmlns:mc="{mc_ns}"><w:body>'
            '<mc:AlternateContent><mc:Choice Requires="w"><w:p><w:r><w:t>A</w:t>'
            '</w:r></w:p></mc:Choice></mc:AlternateContent></w:body></w:document>'
        )
        settings = f'<w:settings xmlns:w="{w_ns}"><w:trackRevisions/></w:settings>'
        with tempfile.TemporaryDirectory() as temp_dir:
            blocked = Path(temp_dir) / "alternate.docx"
            write_docx(blocked, document=alternate)
            self.assertTrue(check_draft.preflight_docx(blocked).has_blockers)
            tracked = Path(temp_dir) / "tracked.docx"
            write_docx(tracked, ["Clean body."], parts={"word/settings.xml": settings})
            result = check_draft.preflight_docx(tracked)
            self.assertEqual(result.status, 2)
            self.assertFalse(result.has_blockers)
            self.assertEqual(check_draft.read(str(tracked)), "Clean body.\n")

    def test_complex_docx_objects_are_structured_lossy_findings(self):
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        m_ns = "http://schemas.openxmlformats.org/officeDocument/2006/math"
        document = (
            f'<w:document xmlns:w="{w_ns}" xmlns:m="{m_ns}"><w:body>'
            '<w:p><w:r><w:t>Visible prose.</w:t></w:r><m:oMath/></w:p>'
            '<w:tbl/><w:p><w:fldSimple/><w:sdt/><w:drawing/><w:txbxContent/>'
            '</w:p></w:body></w:document>'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "complex.docx"
            write_docx(
                path,
                document=document,
                parts={
                    "word/comments.xml": (
                        f'<w:comments xmlns:w="{w_ns}"><w:comment><w:p><w:r>'
                        '<w:t>Comment.</w:t></w:r></w:p></w:comment></w:comments>'
                    ),
                    "word/media/image1.png": b"image",
                    "word/charts/chart1.xml": "<chart/>",
                    "word/embeddings/object1.bin": b"object",
                },
            )
            result = check_draft.preflight_docx(path)
            codes = {item.code for item in result.findings}
            self.assertTrue(result.has_lossy)
            self.assertTrue(
                {"equation", "table", "field", "content_control", "drawing",
                 "textbox", "comment", "media", "chart", "embedded_object"}
                <= codes
            )
            with self.assertRaises(ValueError):
                check_draft.read(str(path))
            self.assertEqual(
                check_draft.extract_docx(path, preflight=result, allow_lossy=True),
                "Visible prose.\n",
            )

    def test_malformed_docx_is_an_input_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "draft.docx"
            path.write_bytes(b"not a zip archive")
            with self.assertRaises(ValueError):
                check_draft.read(str(path))
            empty = Path(temp_dir) / "empty.docx"
            with zipfile.ZipFile(empty, "w") as archive:
                archive.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
            with self.assertRaises(ValueError):
                check_draft.read(str(empty))

    def test_docx_rejects_malformed_related_xml_and_duplicate_main_part(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            malformed = Path(temp_dir) / "malformed.docx"
            write_docx(
                malformed, ["Clean body."],
                parts={"word/header1.xml": "<w:hdr>"},
            )
            with self.assertRaisesRegex(ValueError, "header1.xml XML 损坏"):
                check_draft.preflight_docx(malformed)
            duplicate = Path(temp_dir) / "duplicate.docx"
            document = (
                '<w:document xmlns:w="http://schemas.openxmlformats.org/'
                'wordprocessingml/2006/main"><w:body/></w:document>'
            )
            with zipfile.ZipFile(duplicate, "w") as archive:
                archive.writestr("[Content_Types].xml", DOCX_CONTENT_TYPES)
                archive.writestr("word/document.xml", document)
                with self.assertWarns(UserWarning):
                    archive.writestr("word/document.xml", document)
            with self.assertRaisesRegex(ValueError, "重复的 word/document.xml"):
                check_draft.preflight_docx(duplicate)

    def test_rejects_invalid_utf8(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "draft.txt"
            path.write_bytes(b"\xff\xfe\x00")
            with self.assertRaises(UnicodeError):
                check_draft.read(str(path))

    def run_main(self, argv, stdin=""):
        stdout = io.StringIO()
        stderr = io.StringIO()
        with patch.object(sys, "argv", ["check_draft.py", *argv]), patch.object(
            sys, "stdin", io.StringIO(stdin)
        ), patch.object(sys, "stdout", stdout), patch.object(sys, "stderr", stderr):
            with self.assertRaises(SystemExit) as raised:
                check_draft.main()
        return raised.exception.code, stdout.getvalue(), stderr.getvalue()

    def test_double_stdin_is_rejected_with_input_error_status(self):
        status, _, error = self.run_main(["-", "--compare", "-"], "Text.")
        self.assertEqual(status, 3)
        self.assertIn("标准输入", error)

    def test_input_error_does_not_use_review_status(self):
        status, _, error = self.run_main(["missing.pdf"])
        self.assertEqual(status, 3)
        self.assertIn("不支持", error)

    def test_extract_prints_prose_and_rejects_compare(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "paper.docx"
            write_docx(path, ["First paragraph.", "Second paragraph."])
            status, output, _ = self.run_main([str(path), "--extract"])
            self.assertEqual(status, 0)
            self.assertEqual(output, "First paragraph.\n\nSecond paragraph.\n")
            status, _, error = self.run_main(
                [str(path), "--extract", "--compare", str(path)]
            )
        self.assertEqual(status, 3)
        self.assertIn("--extract", error)

    def test_docx_preflight_cli_and_lossy_extraction_contract(self):
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        document = (
            f'<w:document xmlns:w="{w_ns}"><w:body><w:p><w:r>'
            '<w:t>Visible prose.</w:t></w:r></w:p><w:tbl/></w:body></w:document>'
        )
        revision = document.replace("<w:tbl/>", "<w:ins><w:r><w:t>Pending.</w:t></w:r></w:ins>")
        with tempfile.TemporaryDirectory() as temp_dir:
            complex_path = Path(temp_dir) / "complex.docx"
            write_docx(complex_path, document=document)
            status, output, error = self.run_main([str(complex_path), "--docx-preflight"])
            self.assertEqual(status, 2)
            self.assertIn("table", output)
            self.assertEqual(error, "")
            status, output, error = self.run_main([str(complex_path), "--extract"])
            self.assertEqual(status, 1)
            self.assertEqual(output, "")
            self.assertIn("有损", error)
            status, output, error = self.run_main(
                [str(complex_path), "--extract", "--allow-lossy-docx"]
            )
            self.assertEqual(status, 2)
            self.assertEqual(output, "Visible prose.\n")
            self.assertIn("诊断性有损抽取", error)
            revision_path = Path(temp_dir) / "revision.docx"
            write_docx(revision_path, document=revision)
            status, output, error = self.run_main(
                [str(revision_path), "--extract", "--allow-lossy-docx"]
            )
        self.assertEqual(status, 1)
        self.assertEqual(output, "")
        self.assertIn("接受或拒绝全部修订", error)

    def test_compare_preflights_either_docx_side(self):
        w_ns = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        revision = (
            f'<w:document xmlns:w="{w_ns}"><w:body><w:p><w:ins><w:r>'
            '<w:t>Pending.</w:t></w:r></w:ins></w:p></w:body></w:document>'
        )
        with tempfile.TemporaryDirectory() as temp_dir:
            blocked = Path(temp_dir) / "blocked.docx"
            clean = Path(temp_dir) / "clean.docx"
            write_docx(blocked, document=revision)
            write_docx(clean, ["Clean body."])
            for original, edited in [(blocked, clean), (clean, blocked)]:
                with self.subTest(original=original):
                    status, output, error = self.run_main(
                        [str(original), "--compare", str(edited)]
                    )
                    self.assertEqual(status, 1)
                    self.assertEqual(output, "")
                    self.assertIn("revision", error)

    def test_docx_cli_rejects_invalid_option_combinations(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "clean.docx"
            write_docx(path, ["Clean."])
            cases = [
                [str(path), "--docx-preflight", "--extract"],
                [str(path), "--allow-lossy-docx"],
                ["-", "--allow-lossy-docx", "--extract"],
            ]
            for argv in cases:
                with self.subTest(argv=argv):
                    status, _, error = self.run_main(argv)
                    self.assertEqual(status, 3)
                    self.assertIn("error", error)

    def test_mixed_stdin_and_tex_preserves_latex_hint(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            edited = Path(temp_dir) / "edited.tex"
            edited.write_text(r"\newcommand{\x}{new}", encoding="utf-8")
            status, output, _ = self.run_main(
                ["-", "--compare", str(edited)], r"\newcommand{\x}{old}"
            )
        self.assertEqual(status, 1, output)

    def test_stdin_infers_markdown_source_regions(self):
        status, output, _ = self.run_main(
            ["-"], "---\ntitle: 中文 —\n---\nEnglish prose."
        )
        self.assertEqual(status, 0, output)
        self.assertNotIn("中文字符残留", output)


if __name__ == "__main__":
    unittest.main()
