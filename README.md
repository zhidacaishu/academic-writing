# Academic Writing Skill

面向信息系统与定量营销领域的设计科学、artifact-centered 方法论文，提供英文起草、润色、翻译与结构诊断支持。

该 skill 特别适合中文研究思路已经较清楚，但英文稿仍存在直译痕迹、贡献定位模糊，或问题—设计—评价链条不完整的稿件。中文材料可以作为英文写作的语义来源，但不生成或润色中文论文正文。

## 适用范围

### 适合处理

- Design-science、artifact、model-development 和方法贡献型论文
- 标题、摘要、引言、相关工作、问题形式化、模型设计、评价与管理启示
- 中译英和已有英文稿润色
- 贡献、结构、逻辑及审稿意见诊断
- UTF-8 编码的 `.txt`、`.md` 和 `.tex` 稿件

### 不适合处理

- 与设计科学或 artifact-centered 方法贡献无关的一般论文
- 中文论文正文润色
- 未经核实的文献、实验结果或机制解释生成
- `.docx`、`.pdf`、图片等附件的抽取、OCR 或格式推断

## 工作模式

| 模式 | 典型请求 | 默认交付 |
|---|---|---|
| 润色 | “润色一下”“翻译成英文”“全文修改” | 改后全文及需要作者确认的实质性问题 |
| 结构诊断 | “逻辑有问题吗”“贡献不清楚怎么办” | 问题位置、性质、成因和修改方向 |
| 组合执行 | 同时要求诊断和改写 | 先诊断，再按诊断结果改写 |
| 起草 | 只有写作目标，没有现成稿件 | 英文草稿及待作者补充的显式占位符 |

具体模式判定、交付要求和边界规则以 [`SKILL.md`](SKILL.md) 为准。

## 核心原则

1. **不编造文献。** 无法核实的引用使用明确占位符。
2. **润色不改变实质。** 不擅自修改数字、贡献条目、结论强度或设计理由。
3. **声称与证据匹配。** 区分统计显著性、一般性能优势和因果机制声称。
4. **只改散文。** 保持公式、引用键、交叉引用、宏定义、注释及结构命令不变；正常文本参数仍可编辑。
5. **保持设计闭环。** 检查问题、挑战、设计、贡献和评价之间的可追溯关系。

## 目录结构

```text
academic-writing/
├── SKILL.md
├── README.md
├── references/
│   ├── design-science-genre.md
│   ├── cn-en-transfer.md
│   └── style-and-consistency.md
└── scripts/
    ├── check_draft.py
    └── test_check_draft.py
```

### 资源导航

| 文件 | 用途 |
|---|---|
| [`SKILL.md`](SKILL.md) | 触发范围、工作模式、硬性边界和执行流程 |
| [`references/design-science-genre.md`](references/design-science-genre.md) | 设计科学体裁、贡献层级、理论适配、评价、摘要和标题 |
| [`references/cn-en-transfer.md`](references/cn-en-transfer.md) | 中译英、句法迁移、时态和声称强度 |
| [`references/style-and-consistency.md`](references/style-and-consistency.md) | 文风、一致性、语法、模型化表达复核和说服力 |
| [`scripts/check_draft.py`](scripts/check_draft.py) | 英文稿机械检查及润色前后受保护对象比对 |
| [`scripts/test_check_draft.py`](scripts/test_check_draft.py) | 检查器回归测试 |

`SKILL.md` 只保留执行所需的核心规则，详细知识按任务需要从 `references/` 加载；检查器可直接运行，无需将脚本全文载入上下文。

## 安装与调用

将本仓库完整复制或链接为一个具名 skill 目录，确保 `SKILL.md` 位于该目录顶层：

- **个人范围**：`~/.claude/skills/academic-writing/`
- **项目范围**：`<project>/.claude/skills/academic-writing/`

Claude Code 可以根据 `SKILL.md` 的 description 自动加载该 skill，也可以显式输入：

```text
/academic-writing
```

skill 内部通过 `${CLAUDE_SKILL_DIR}` 定位随附脚本，因此无论从哪个项目调用，都不依赖当前工作目录中的 `scripts/`。

加载后直接提出自然语言请求，例如：

```text
帮我润色这段方法章节，只改英文表达，不改变公式和引用。
```

```text
检查这篇 design-science 论文的问题、设计、贡献和评价是否对应。
```

```text
根据这些中文要点起草英文摘要，不要编造实验结果或文献。
```

对长稿，可以提供 UTF-8 编码的 `.txt`、`.md` 或 `.tex` 文件。完整润色不应因内部按小节处理而缩减最终交付范围。

## 机械检查器

以下示例用于在 `academic-writing/` 仓库根目录手动运行检查器；skill 自动执行时会通过 `${CLAUDE_SKILL_DIR}` 定位同一脚本。检查器需要 Python 3.7 或更高版本，仅使用标准库，不联网，也不安装第三方依赖；回归测试在 Python 3.12 上通过。

### 常规检查

```bash
python scripts/check_draft.py draft.tex
```

常规模式检查可机械识别的问题和人工复核线索，包括：

- 中文字符、全角标点和长破折号残留
- 确定性中式表达与上下文相关措辞
- 英美拼写混用与数字格式一致性；同一概念的表层写法变体只作人工复核项
- 缩写首现（含复数形式）、疑似过去时、句长分布与相邻段首的连接词链条

Markdown frontmatter、代码区域以及 LaTeX 注释、公式和结构源码不会作为普通散文检查。Markdown 的分隔线与表格分隔行不计为破折号；紧跟数字的 `%` 视为百分号而非 LaTeX 注释；弯引号只在 LaTeX 稿中提示，`.md` 与 `.txt` 稿不报。

### 润色前后比对

```bash
python scripts/check_draft.py original.tex --compare edited.tex
```

`--compare` 按原文顺序核对：

- 数字与公式
- 引用和交叉引用命令
- Markdown frontmatter、围栏代码和行内代码
- LaTeX 注释、宏定义、图表/表格结构及相关结构命令

`\caption{}`、`\section{}`、`\emph{}` 等命令中的散文仍可编辑；检查器保护的是命令结构，而不是冻结其中的正常文本。

`--compare` 只执行受保护对象比对，不包含普通文风检查。验证润色稿时应先对修改稿运行常规检查，再运行原稿与修改稿的 `--compare`。

> 注意：机械比对不能证明语义完全不变。即使返回成功，仍需人工核对主张强度、跨句指代、符号含义及数字与结论的绑定关系。

中译英时 `--compare` 仍可核对数字、公式与引用的内容和顺序，但绑定线索只采集拉丁字母词，中文原稿一侧恒为空，因此每个对象都会进入人工复核清单。

### 退出码

| 退出码 | 常规检查 | `--compare` |
|---:|---|---|
| `0` | 未发现机械问题 | 未发现受保护对象或局部绑定变化 |
| `1` | 发现确定性问题 | 受保护对象发生增删、改写或换序 |
| `2` | 仅有人工复核项 | 对象未变，但局部文字绑定需要人工复核 |
| `3` | 输入或参数错误 | 输入或参数错误 |

也可以通过标准输入检查文本：

```bash
python scripts/check_draft.py - < draft.txt
```

原稿和修改稿不能同时从同一标准输入读取。

## 测试与维护

运行全部回归测试：

```bash
python -m unittest discover -s scripts -p "test_*.py"
```

进行语法编译检查：

```bash
python -m py_compile scripts/check_draft.py scripts/test_check_draft.py
```

当前测试覆盖受保护对象增删与换序、局部绑定提示、Markdown/LaTeX 边界、宏和注释优先级、货币与公式区分、百分号与 LaTeX 注释的区分、Markdown 分隔行与破折号的区分、复数写法与复数缩写、连接词链条的相邻段首判定、弯引号的 LaTeX 限定、表层写法变体与英美拼写混用的分级、输入编码以及 CLI 退出码。

维护时遵循以下原则：

- 保持 design-science / artifact-centered 范围，不扩展为通用学术写作规则库。
- 将详细体裁或语言知识放入 `references/`，保持 `SKILL.md` 精简。
- 只有确定性错误进入 hard checks；依赖语境的表达保留为人工复核项。
- 修改源码扫描、保护边界或退出码时，同时增加相应回归测试。
- 优先完善共享扫描机制，避免为单个命令或短语持续堆叠特例。

## 能力边界

检查器不能判断挑战是否成立、设计是否真正回应问题、评价是否支持贡献，或稿件是否达到 design theory 层级。这些内容必须结合 [`references/design-science-genre.md`](references/design-science-genre.md) 进行人工结构诊断。
