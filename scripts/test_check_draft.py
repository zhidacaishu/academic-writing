#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression tests for check_draft.py."""

import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_draft


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

    def test_non_citation_macro_and_editable_latex_text_are_not_protected(self):
        cases = [
            (r"A \excite{old}.", r"A \excite{new}."),
            (r"\caption{Old caption}", r"\caption{New caption}"),
            (r"\section{Old heading}", r"\section{New heading}"),
        ]
        for original, edited in cases:
            with self.subTest(original=original):
                report, status = check_draft.compare(
                    original, edited, is_latex=True
                )
                self.assertEqual(status, 0, report)


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
        self.assertNotIn("写法不一致", report.hard)
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
            for suffix in (".docx", ".pdf", ".rtf"):
                path = Path(temp_dir) / f"draft{suffix}"
                path.write_bytes(b"not a supported text input")
                with self.subTest(suffix=suffix):
                    with self.assertRaises(ValueError):
                        check_draft.read(str(path))

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
        status, _, error = self.run_main(["missing.docx"])
        self.assertEqual(status, 3)
        self.assertIn("不支持", error)

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
