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
- 通过安全预检的 `.docx` 稿件：抽取正文散文后处理，交付物为纯文本或 Markdown，不回写原文件

### 不适合处理

- 与设计科学或 artifact-centered 方法贡献无关的一般论文
- 中文论文正文润色
- 未经核实的文献、实验结果或机制解释生成
- `.pdf`、`.rtf`、图片与扫描件的抽取、OCR 或版式推断
- `.docx` 中未决修订的自动接受或拒绝，以及批注、公式、表格、图表和版式的还原

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
| [`references/style-and-consistency.md`](references/style-and-consistency.md) | 文风、一致性、语法、机械化与空泛表达复核和说服力 |
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

对长稿，可以提供 UTF-8 编码的 `.txt`、`.md` 或 `.tex` 文件，或 `.docx`（先抽取正文，见下）。完整润色不应因内部按小节处理而缩减最终交付范围。

## 机械检查器

以下示例用于在 `academic-writing/` 仓库根目录手动运行检查器；skill 自动执行时会通过 `${CLAUDE_SKILL_DIR}` 定位同一脚本。检查器需要 Python 3.7 或更高版本，仅使用标准库，不联网，也不安装第三方依赖；回归测试在 Python 3.12 上通过。

### 常规检查

```bash
python3 scripts/check_draft.py draft.tex
```

常规模式把结果分为两级：必改对应退出码 `1`，人工复核项对应退出码 `2`。

必改（可机械判定的确定性错误）：

- 中文字符与全角标点残留
- 长破折号：中文破折号、em dash 及 LaTeX `---`
- 确定性中式学术英语与冗余结构
- 数字格式不一致：`.5` 与 `0.5` 混用
- 未闭合的 Markdown 代码围栏：其后内容全部被屏蔽，须显式报出

人工复核项（依赖语境，需要人判断）：

- 声称强度越界：无检验的 `significantly`、`is superior to`、`in general` 等
- 需结合语境的措辞、英美拼写混用、百分比显示精度、句内 en dash、`etc.` 兜底列举，以及 LaTeX 稿中的弯引号
- 同一概念的表层写法变体、缩写首现（含复数形式）未定义、疑似过去时
- 超长句，以及相邻段首的连接词链条

需要句长描述统计时，另行运行：

```bash
python3 scripts/check_draft.py draft.tex --sentence-metrics
```

该选项只报告句数、均值、标准差、变异系数和 15–25 词占比，不产生问题等级，也不影响退出码。默认检查不会仅因稿件达到一定句数而产生复核项。

Markdown frontmatter、代码区域以及 LaTeX 注释、公式和结构源码不会作为普通散文检查。Markdown 的分隔线与表格分隔行不计为破折号；弯引号只在 LaTeX 稿中提示，`.md` 与 `.txt` 稿不报。

**百分号与 LaTeX 注释的区分。**`15%`、`5 %` 与 `(%)` 均判定为百分号；Markdown 稿不做 `%` 注释剥离。判定在此处向保留正文一侧倾斜：误判为注释将屏蔽整行正文，检查器随之输出无效的“未发现问题”，其代价高于漏剥一处注释。

**扫描优先级。**公式先于注释登记，因此 `\begin{equation}` 与 `\[...\]` 内部的 `%` 归属于公式，不会导致整个公式失去保护。注释仍优先于宏定义与图表结构，`% \newcommand{...}` 判定为注释。

### 润色前后比对

```bash
python3 scripts/check_draft.py original.tex --compare edited.tex
```

`--compare` 按原文顺序核对：

- 数字与公式
- 引用和交叉引用命令
- Markdown frontmatter、围栏代码和行内代码
- LaTeX 注释、宏定义、图表/表格结构及相关结构命令

`\caption{}`、`\section{}`、`\emph{}`、`\footnote{}` 等已登记命令中的文本参数仍可编辑；`\href{}{}` 只开放第二个显示文本参数。命令外壳、非文本参数以及未登记的命令调用默认冻结，避免把包专用宏的参数误当普通散文。

`--compare` 只执行受保护对象比对，不包含普通文风检查。验证润色稿时应先对修改稿运行常规检查，再运行原稿与修改稿的 `--compare`。

> 注意：机械比对不能证明语义完全不变。即使返回成功，仍需人工核对主张强度、跨句指代、符号含义及数字与结论的绑定关系。

中译英时 `--compare` 可核对数字、公式与引用的内容和顺序。数字的边界判定采用 ASCII 字符类而非 `\w`，因此紧贴汉字的 `提升5%`、`3个数据集` 均可提取；比对时 `5%` 与 LaTeX 的 `5\%` 归一为同一数值。但绑定线索只采集拉丁字母词，中文原稿一侧恒为空，因此每个对象仍会进入人工复核清单。该清单在此场景下属于结构性噪声，判断依据应取受保护对象的增删与换序。

### 退出码

| 退出码 | 常规检查 | `--compare` |
|---:|---|---|
| `0` | 未发现机械问题 | 未发现受保护对象或局部绑定变化 |
| `1` | 发现确定性问题 | 受保护对象发生增删、改写或换序 |
| `2` | 仅有人工复核项 | 对象未变，但局部文字绑定需要人工复核 |
| `3` | 输入或参数错误 | 输入或参数错误 |

`--docx-preflight` 使用同一组退出码：`0` 无发现，`1` 有不可处理的未决修订或不确定分支，`2` 只有复杂对象或信息提示，`3` 包或参数错误。显式有损抽取成功也固定返回 `2`。

也可以通过标准输入检查文本：

```bash
python3 scripts/check_draft.py - < draft.txt
```

原稿和修改稿不能同时从同一标准输入读取。

### DOCX 预检与正文抽取

处理 `.docx` 前先单独预检：

```bash
python3 scripts/check_draft.py paper.docx --docx-preflight
python3 scripts/check_draft.py paper.docx --extract > paper.md
```

脚本用标准库 `zipfile` 与 `ElementTree` 扫描 Word 包内的 XML 部件，不依赖固定 namespace 前缀。未决插入、删除、移动、属性修订或 `AlternateContent` 会永久阻断处理；请先在 Word 中接受或拒绝全部修订并另存清洁副本。仅启用“修订跟踪”但没有实际修订元素时只给提示。

公式、表格、批注、脚注/尾注、页眉页脚、图表、文本框、字段、内容控件及嵌入对象会使纯文本投影不完整，因此默认不能作为最终稿直接检查、比较或抽取。确需排障时可显式执行：

```bash
python3 scripts/check_draft.py paper.docx --extract --allow-lossy-docx > diagnostic.txt
```

该模式只允许诊断性投影，正文写 stdout，风险摘要写 stderr，退出码固定为 `2`；它不能绕过未决修订，也不能用于 `--compare`。清洁 `.docx` 可直接传入常规检查或作为 `--compare` 任一端，脚本会先分别预检再抽取。`.pdf`、`.rtf` 与图片仍不接受。

## 测试与维护

运行全部回归测试：

```bash
python3 -m unittest discover -s scripts -p "test_*.py"
```

进行语法编译检查：

```bash
python3 -m py_compile scripts/check_draft.py scripts/test_check_draft.py
```

当前测试覆盖受保护对象增删与换序、局部绑定提示、Markdown/LaTeX 边界、未知命令冻结与已登记文本参数、宏和注释优先级、公式内注释不破坏公式保护、注释内 `$` 不算公式、货币与公式区分、百分号与 LaTeX 注释的区分（含 `5 %` 与 `(%)`）、未闭合源码区域的报出、紧贴汉字的数字提取与 `5%` / `5\%` 归一、语言规则分级、DOCX 跨部件修订与复杂对象预检、有损抽取隔离、损坏包和 XML 的报错、输入编码以及 CLI 退出码。

维护时遵循以下原则：

- 保持 design-science / artifact-centered 范围，不扩展为通用学术写作规则库。
- 将详细体裁或语言知识放入 `references/`，保持 `SKILL.md` 精简。
- 只有确定性错误进入 hard checks；依赖语境的表达保留为人工复核项。
- 修改源码扫描、保护边界或退出码时，同时增加相应回归测试。
- 优先完善共享扫描机制，避免为单个命令或短语持续堆叠特例。

## 能力边界

检查器不能判断挑战是否成立、设计是否真正回应问题、评价是否支持贡献，或稿件是否达到 design theory 层级。这些内容必须结合 [`references/design-science-genre.md`](references/design-science-genre.md) 进行人工结构诊断。
