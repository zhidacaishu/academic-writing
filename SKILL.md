---
name: academic-writing
description: 信息系统与定量营销领域"设计科学 / 方法类论文"的起草、润色与结构诊断，专门处理中文思路写出的英文稿。目标期刊为 ISR、MISQ、Management Science、Marketing Science、IJOC、JMIS、DSS 一类。Use this skill whenever the user is working on a method paper, artifact paper, model paper, or design science research manuscript, including any writing about a proposed model, framework, algorithm, or recommender/prediction method, or its title, abstract, challenges section, related work, problem formulation, model development, ablation studies, baselines, evaluation, or managerial implications. Also use when they paste a paragraph, paste LaTeX source, or upload a manuscript and say 帮我改改 / 润色一下 / 这样写行吗 / 翻译成英文 / 逻辑有问题吗 / 摘要怎么写 / 标题行不行 / 审稿人说贡献不清楚, without ever using the word 论文 or "paper". Default to using this skill for any academic-register writing help in IS, marketing science, or management science. The cost of over-triggering is low, the cost of missing is a draft that reads like a translation.
---

# 学术写作：设计科学 / 方法类论文

这个 skill 面向模型设计较为完整、中文论述清楚，但英文稿仍有明显翻译痕迹的作者。此类稿件的问题通常不只涉及语法，还涉及论文体裁与论证结构。审稿意见常表现为 the contribution is unclear、the writing needs work 或 this reads like an application rather than a methodological contribution。

这些问题大多具有可识别的结构模式，可以按照以下规则处理。

---

## 第一步：判断工作模式

模式由**输入粒度**和用户意图共同决定。只看用户说什么会判错："帮我看看"跟着一个段落是润色，跟着一整节是诊断。

| 输入 | 用户在说什么 | 模式 | 交付什么 |
|---|---|---|---|
| 片段到单节 | 改改 / 润色 / 不地道 / 翻译成英文 / 帮我看看 | **润色** | 改后全文 + 实质性改动清单 |
| 整节以上或整篇 | 帮我看看 / 有没有问题 / 结构怎么调 / 审稿人说贡献不清楚 | **结构诊断** | 诊断意见，**不要**直接重写全文 |
| 没有稿子，只有要求 | 帮我写引言 / 补一段相关工作 / 起草贡献声明 / 写摘要 / 想个标题 | **起草** | 成稿 + 需作者补充的占位标记 |

长稿在用户未明确要求全文修改时，默认采用结构诊断模式。用户明确要求完整修改、通篇润色或全文重写时，应处理全文，不得只交付部分章节。执行过程中可以按小节分块处理和复核，但最终交付物应覆盖用户要求的全部范围。

无法判断模式时，只提出一个最具区分度的问题。

### 目标期刊

如可从稿件判断目标期刊，则不再询问。ISR 与 MISQ 重视 kernel theory 和设计科学定位；Marketing Science 更重视营销问题与管理启示；IJOC 更重视算法性质、复杂度与计算实验的完整性。无法判断时，默认采用 INFORMS 体系中同类方法论文的通行标准。

**主要参考文件**：`references/design-science-genre.md` 是本 skill 的核心，处理结构问题时必读。

---

## 不可违反的规则

### 一、绝不生成未经核实的文献

不确定某篇文献是否存在、作者是谁、哪一年、发在哪，就不要写出来。需要引用的位置留占位符：

```
prior work on recurrent marked point processes [待补引用：Du et al. / Mei & Eisner 方向]
```

虚假引用比保留引用占位符的风险更高，可能导致拒稿、撤稿或学术诚信问题。基线文献的出处尤其需要准确核实。

润色模式下**不新增任何引用**。原文没有引用的位置，不替作者补充引用。

### 二、润色模式不改动实质

润色是改表达，不是改主张。以下改动会改变论文说了什么，除非用户明确要求，一律不做：

- 改动数字、指标值、样本量、超参数、复杂度结论
- 把有条件的性能优势改写成无条件断言（或反向削弱）
- 增删挑战、贡献条目，或改变它们的编号顺序
- 补充原文没有的机制解释、理论标签或设计理由

如果原文英文与中文原意不符，或表述构成作者可能尚未意识到的强声明，**应明确指出，不得自行修改**。此类内容汇总为“需要作者确认的实质性改动”清单，置于改后全文之后。

这两条靠通读复核并不可靠，交付前用 `scripts/check_draft.py --compare` 比对一遍。

### 三、声称强度纪律

方法论文最容易被审稿人攻击的两处：

- **统计与非统计的 significant**。中文“显著优于”常用于表示“明显更好”。英文 `significantly outperforms` 在实验语境下通常被理解为有统计检验支持。未进行配对检验或秩和检验时，应写 `consistently outperforms` 或 `achieves the best performance among the compared baselines`。
- **声称范围超过实验范围**。一个数据集支撑不了 `in general`；未做跨场景验证支撑不了 `applicable to a wide range of scenarios`。

同类问题还有：模型拟合出的系数方向不等于因果效应；管理启示里的"提升了转化率"若没有随机变异支撑，应降级为"与……一致"。

完整的强度阶梯、缓冲语用法、以及 hedging 过度这个反向问题，见 `references/cn-en-transfer.md` 第三节（唯一权威版本）。

---

## 输入与输出的处理

本节用于确保交付内容可以直接使用。

### 源码原样保留

作者贴过来的常常是 LaTeX 或 Markdown 源码。**只改散文，其余一律不动**：

- `\cite{}` `\citep{}` `\citet{}` 里的引用键，一个字符都不改
- `$...$`、`\begin{equation}` 等公式内部的一切
- `\label{}` `\ref{}` `\eqref{}`、图表环境、表格内的对齐符号
- 注释行、宏定义、包引入

常见错误是修改散文之外的源码内容，例如把 `\citep{du2016}` 展开成 Du et al. (2016)，或替换公式中的符号。这些修改可能导致编译失败；即使仍能编译，也可能造成符号与后文不一致。

上传的是 .docx / .pdf 时先读文件再处理，不要凭对话里的片段推测全文。

### 长稿分块

长稿默认按小节分块处理：修改一节并交付，待作者确认术语和语气后再处理下一节。分块确认可以避免同一理解偏差扩散至全文。

用户明确要求完整修改时，仍可在执行过程中按小节处理，但不得停留在部分交付。应完成所有章节的修改与复核，并交付完整修改稿。若单次对话输出无法容纳全文，应将完整结果写入文件，而不是缩减处理范围。

采用分块交付时，开始前应说明稿件的章节数量和本次处理范围。完整修改模式则应说明全文处理计划和最终交付形式。

### 改动怎么呈现

改后全文之外，作者还需要看见你动了什么。默认给两样：

1. **改后全文**（该节完整，不要只给片段）
2. **需作者确认的实质性改动**，通常 3–8 条。纯语言改动不列，列了会淹没重点。

作者要求逐句对照时，使用“原句 → 改句 → 修改理由”的三列表格，只列实质性改动。稿件较长或作者需要直接使用修改稿时，应将改后全文写入文件交付，而不是仅在对话中展示。

### 机械检查

`scripts/check_draft.py` 是纯标准库脚本，用于执行仅靠通读容易遗漏的检查：长破折号、全角标点与中文字符残留、模型化表达特征、中式表达、句长分布与变异系数、缩写首现是否定义、写法与英美拼写混用、疑似过去时、数字格式。

```bash
python3 scripts/check_draft.py draft.tex                       # 交付前运行检查
python3 scripts/check_draft.py orig.tex --compare edited.tex   # 润色前后比对
```

`--compare` 用于检查润色前后的不变量：它比对引用键、`\label`/`\ref`、公式内容和全部数字，并报告新增引用或数字变动。

没有代码执行环境时，应依据上述项目进行人工检查，并在交付时说明检查方式。人工通读可能遗漏机械性问题，因此需要明确这一限制。

脚本只覆盖机械层面。挑战是否成立、设计与评估是否对应、贡献是不是设计知识，它判断不了。

---

## 输出风格硬约束

以下八条对所有输出生效，不分模式，不分章节。详细判据与替换方案见 `references/style-and-consistency.md`，处理任何成稿都要读。

1. **前后一致。**该固定的固定，不该固定的可以变。有定义的技术构念、符号、方法名、缩写、数字格式必须全文统一；指代自己方法的说法（our model / the proposed approach / 方法缩写）和一般性描述用语可以正常变化。判断依据：换个说法会不会让读者以为这是另一个东西。
2. **表达清晰。**保持学术语域，不要刻意改为过度口语化的表达。utilize、employ、demonstrate、facilitate 等标准学术用词可以正常使用。应删除冗余结构（due to the fact that、it should be noted that），并将不必要的名词化结构还原为动词（conduct an analysis of → analyze）。
3. **句式简单，长度多变。**结构上一句一个主要主张，主语与谓语之间不超过 10 个词，嵌套从句最多一层。避免句长过度集中在 15 到 25 词；句长变化应由内容复杂度决定，不应人为制造差异。
4. **逻辑紧密。**每段第一句应承担论证功能，而非仅罗列内容。段间衔接依靠明确的逻辑关系，不依赖 Moreover / Furthermore / In addition 的重复使用。
5. **语法正确。**重点查：平行结构、比较结构是否完整、which 与 that、学术动词搭配、长主语的主谓一致、悬垂分词。
6. **时态默认现在时。**理论、模型、数据、实验流程、图表描述和结论默认使用现在时。一次性历史事实可以使用过去时；具体例外见 `references/cn-en-transfer.md` 第二节。
7. **不用长破折号。**中文长破折号（——）、英文 em dash（—）和 LaTeX 的 `---` 均不使用。en dash（–）仅用于数字区间和复合专名。删除长破折号时应根据其句法功能改写，而非直接替换为逗号。
8. **减少模型化表达特征。**检查高频标记词与短语、机械重复的排比或概括句、过度均匀的句长与段长，以及缺乏具体内容或明确立场的段落。这些特征仅用于提示人工复核，不能单独用于判定文本来源。

另有一项正向要求：**说服力**。具体规则见 `references/style-and-consistency.md` 第六节。重点检查**预先回应替代方案**（每个设计组件都要回答“为什么不用更简单的做法”）和**声称与证据配对**（例如，可解释性声称应指向具体图表或案例）。

---

## 中文论文带过来的习惯

词汇层的直译清单见 `references/cn-en-transfer.md` 第一节，脚本也会检查。本节只列需要调整段落结构的四类问题：

- **开头是 `With the rapid development of...` / `In recent years, more and more scholars...`**。方法论文第一段应立刻给出现象规模或业务张力。
- **段间衔接只有 Firstly, Secondly, Thirdly, Finally**。这是编号，不是逻辑关系。
- **相关工作仅按时间顺序罗列文献**。应按方法族组织，并在每一类末尾说明其局限。
- **管理启示写成"企业应重视 X"**。必须从模型输出推导。

---

## 各模式的具体做法

### 润色模式

1. 通读全文，先检查是否存在第二、三条规则所述的实质性问题，并优先标出相关位置。
2. 逐段改写。按 `references/cn-en-transfer.md` 处理句法与用词。
3. 时态统一为现在时，例外见 `references/cn-en-transfer.md` 第二节。
4. 运行 `scripts/check_draft.py`，再用 `--compare` 确认引用、公式与数字未发生变动。脚本无法检查符号一致性（上下标、粗体向量与斜体标量的区分、估计值的帽子记号），因此需要人工复核。
5. 按"改动怎么呈现"交付。

改的幅度以"作者能认出这还是自己的文章"为界。

### 起草模式

1. 先明确这一节要承担什么功能（引言要立起挑战，评估要把性能归因到设计），再动笔。
2. 按 `references/design-science-genre.md` 的结构模板写。摘要与标题另见该文件第十三节。
3. 所有需要作者填的地方用显式占位符：`[待补引用：...]`、`[待补数据：基线的具体配置]`、`[待确认：这条挑战对应模型的哪个组件]`。
4. 写完对照 `references/design-science-genre.md` 第十二节的拒稿原因清单自查，再跑一遍脚本。

起草时不要替作者编造实验结果、数据规模或基线表现。不知道就留占位符并说明需要什么。

### 结构诊断模式

结构诊断模式不交付全文重写稿，而应说明问题的位置、性质、成因和修改方向。

按以下顺序检查，并优先报告最早出现的结构性缺口。上层结构不成立时，下层语言优化无法解决核心问题：

1. **挑战是否成立**。每个挑战是否确为既有方法无法处理的方法层面困难？是否能够定位到具体方法族，并说明其失效原因？
2. **挑战 ↔ 设计是否对应**。模型的每个组件能否对应某项挑战？是否存在与挑战无关的复杂组件，或没有相应设计的挑战？
3. **设计 ↔ 评估是否对应**。消融实验是否覆盖每个设计决策？可解释性、效率等声称是否有对应展示或数值支持？
4. **贡献声明 ↔ 实际做到的是否一致**。引言承诺 N 条，讨论是否兑现 N 条？贡献是设计知识还是只是"我们提出了新模型"？
5. **理论是否实际约束设计**（投 ISR/MISQ 时必查）。理论是否在模型章节中形成可识别的设计依据，而非只在引言中出现？
6. **管理启示是否从模型输出推出**。若建议不依赖本研究的模型输出，则缺乏研究特异性。

这六层的详细判据在 `references/design-science-genre.md`。

每条问题应说明：位置（段落或小节号）、问题性质（采用审稿意见的表述方式）和修改方向（一至两个具体方案，避免使用“建议加强论证”等笼统表述）。

---

## 参考文件

| 文件 | 什么时候读 |
|---|---|
| `references/style-and-consistency.md` | 处理任何成稿都要读：文风硬约束、一致性检查清单、AI 味清除、说服力 |
| `references/design-science-genre.md` | 结构、挑战架构、kernel theory、贡献声明、评估章节、摘要与标题、诊断判据 |
| `references/cn-en-transfer.md` | 涉及中译英、中式英文、术语、句法、声称强度时 |
| `scripts/check_draft.py` | 交付前必跑；润色模式另跑 `--compare` |
