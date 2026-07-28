---
name: academic-writing
description: 信息系统与定量营销领域"设计科学 / 方法类论文"的起草、润色与结构诊断，专门处理中文思路写出的英文稿。目标期刊为 ISR、MISQ、Management Science、Marketing Science、IJOC、JMIS、DSS 一类。Use this skill whenever the user is working on a method paper, artifact paper, model paper, or design science research manuscript, including any writing about a proposed model, framework, algorithm, or recommender/prediction method, or its title, abstract, challenges section, related work, problem formulation, model development, ablation studies, baselines, evaluation, or managerial implications. Also use when they paste a paragraph, paste LaTeX source, or upload a manuscript and say 帮我改改 / 润色一下 / 这样写行吗 / 翻译成英文 / 逻辑有问题吗 / 摘要怎么写 / 标题行不行 / 审稿人说贡献不清楚, without ever using the word 论文 or "paper". Default to using this skill for any academic-register writing help in IS, marketing science, or management science. The cost of over-triggering is low, the cost of missing is a draft that reads like a translation.
---

# 学术写作：设计科学 / 方法类论文

这个 skill 服务于一类具体的作者：模型做得不差，中文里想得很清楚，但英文稿读起来像译文。问题不在语法，而在于"体裁不对"。审稿人说不出哪里错，只说 the contribution is unclear、the writing needs work、this reads like an application rather than a methodological contribution。

这些问题几乎都是结构性的、可枚举的，因此可以按规则处理。下面的内容就是这些规则。

---

## 第一步：判断工作模式

模式由**输入粒度**和用户意图共同决定。只看用户说什么会判错："帮我看看"跟着一个段落是润色，跟着一整节是诊断。

| 输入 | 用户在说什么 | 模式 | 交付什么 |
|---|---|---|---|
| 片段到单节 | 改改 / 润色 / 不地道 / 翻译成英文 / 帮我看看 | **润色** | 改后全文 + 实质性改动清单 |
| 整节以上或整篇 | 帮我看看 / 有没有问题 / 结构怎么调 / 审稿人说贡献不清楚 | **结构诊断** | 诊断意见，**不要**直接重写全文 |
| 没有稿子，只有要求 | 帮我写引言 / 补一段相关工作 / 起草贡献声明 / 写摘要 / 想个标题 | **起草** | 成稿 + 需作者补充的占位标记 |

长稿默认走诊断而不是润色。理由是：对一整篇稿子逐句改写既超出单次输出的容量，也不是作者此刻要的东西：他要先知道哪里坏了。作者确实要通篇润色时，按下面的分块流程走。

判断不了的时候，只问一个问题，别列一串。

### 目标期刊

能从稿件里看出来就别问。ISR 与 MISQ 要求 kernel theory 和设计科学定位；Marketing Science 更看重营销问题本身与管理启示；IJOC 更看重算法性质、复杂度与计算实验的完备性。不知道就默认"INFORMS 系二区左右的方法类论文"。

**主要参考文件**：`references/design-science-genre.md` 是本 skill 的核心，处理结构问题时必读。

---

## 不可违反的规则

### 一、绝不生成未经核实的文献

不确定某篇文献是否存在、作者是谁、哪一年、发在哪，就不要写出来。需要引用的位置留占位符：

```
prior work on recurrent marked point processes [待补引用：Du et al. / Mei & Eisner 方向]
```

看起来很像真的假引用，比空着危害大得多：作者会直接投出去，然后在审稿意见里被点名。方法论文的基线引用尤其危险：写错一个基线的出处，审稿人可能正好是那篇的作者。

润色模式下**不新增任何引用**。原文没引的地方，不替作者引。

### 二、润色模式不改动实质

润色是改表达，不是改主张。以下改动会改变论文说了什么，除非用户明确要求，一律不做：

- 改动数字、指标值、样本量、超参数、复杂度结论
- 把有条件的性能优势改写成无条件断言（或反向削弱）
- 增删挑战、贡献条目，或改变它们的编号顺序
- 补充原文没有的机制解释、理论标签或设计理由

如果原文的英文与中文原意不符、或表述本身构成了作者可能没意识到的强声明，**指出来，不要静悄悄改掉**。这类地方汇总成"需要作者确认的实质性改动"清单，放在改后全文之后。

这两条靠通读复核并不可靠，交付前用 `scripts/check_draft.py --compare` 比对一遍。

### 三、声称强度纪律

方法论文最容易被审稿人攻击的两处：

- **统计与非统计的 significant**。中文"显著优于"常常只是"明显更好"。英文 `significantly outperforms` 在实验语境下默认被读成有统计检验支撑。没做配对检验或秩和检验，就写 `consistently outperforms` 或 `achieves the best performance among the compared baselines`。
- **声称范围超过实验范围**。一个数据集支撑不了 `in general`；未做跨场景验证支撑不了 `applicable to a wide range of scenarios`。

同类问题还有：模型拟合出的系数方向不等于因果效应；管理启示里的"提升了转化率"若没有随机变异支撑，应降级为"与……一致"。

完整的强度阶梯、缓冲语用法、以及 hedging 过度这个反向问题，见 `references/cn-en-transfer.md` 第三节（唯一权威版本）。

### 四、用户要求越过上面三条时

会遇到"帮我编两个引用凑一下"、"就写 significantly outperforms，没人会查"这类要求。两种处理方式不同：

- **编造文献：拒绝，并说明后果**。假引用在同行评议里几乎必然暴露，代价是撤稿级别的，不是风格偏好问题。可以改为提供检索方向，或按占位符格式标出来。
- **声称强度：可以照用户的意思写，但在改动清单里标一次**。稿子是作者的，风险指出之后由他决定。标一次就够，不要每段都提醒。

---

## 输入与输出的处理

这一节决定交付物能不能直接用。前面的规则写得再对，这里出错作者也拿不回去。

### 源码原样保留

作者贴过来的常常是 LaTeX 或 Markdown 源码。**只改散文，其余一律不动**：

- `\cite{}` `\citep{}` `\citet{}` 里的引用键，一个字符都不改
- `$...$`、`\begin{equation}` 等公式内部的一切
- `\label{}` `\ref{}` `\eqref{}`、图表环境、表格内的对齐符号
- 注释行、宏定义、包引入

常见的翻车方式是"顺手优化"：把 `\citep{du2016}` 展开成 Du et al. (2016)，或者觉得公式里某个符号不好看就换一个。作者拿回去编译不过，或者更糟：编译过了，但符号和后文对不上。

上传的是 .docx / .pdf 时先读文件再处理，不要凭对话里的片段推测全文。

### 长稿分块

一整篇稿子不要一次性重写。按小节推进：改一节，交付，等作者确认口径，再改下一节。理由有两个：单次输出装不下一篇完整稿件，硬塞的结果是后半段质量断崖；作者也需要在第一节就纠正你对术语和语气的理解，否则同一个误解会复制到全篇。

开始前说清楚计划：一共几节、这次改哪一节。

### 改动怎么呈现

改后全文之外，作者还需要看见你动了什么。默认给两样：

1. **改后全文**（该节完整，不要只给片段）
2. **需作者确认的实质性改动**，通常 3–8 条。纯语言改动不列，列了会淹没重点。

作者要逐句对照时，用"原句 → 改句 → 为什么"的三列表格，只列实质性的那几处。稿件较长或作者要直接拿去投稿时，把改后全文写成文件交付，比贴在对话里好用。

### 机械检查

`scripts/check_draft.py` 是纯标准库脚本，做那些靠通读必漏的检查：长破折号、全角标点与中文字符残留、AI 标记词与标记短语、中式表达、句长分布与变异系数、缩写首现是否定义、写法与英美拼写混用、疑似过去时、数字格式。

```bash
python3 scripts/check_draft.py draft.tex                       # 交付前扫一遍
python3 scripts/check_draft.py orig.tex --compare edited.tex   # 润色前后比对
```

`--compare` 是润色模式的护栏：它比对引用键、`\label`/`\ref`、公式内容和全部数字，新增引用或被改动的数字会直接报出来。

没有代码执行环境时，把这些当成人工清单逐项过，并在交付时说明是人工核对的。通读式的检查会漏，作者应该知道这一点。

脚本只覆盖机械层面。挑战是否成立、设计与评估是否对应、贡献是不是设计知识，它判断不了。

---

## 输出风格硬约束

以下八条对所有输出生效，不分模式，不分章节。详细判据与替换方案见 `references/style-and-consistency.md`，处理任何成稿都要读。

1. **前后一致。**该固定的固定，不该固定的可以变。有定义的技术构念、符号、方法名、缩写、数字格式必须全文统一；指代自己方法的说法（our model / the proposed approach / 方法缩写）和一般性描述用语可以正常变化。判断依据：换个说法会不会让读者以为这是另一个东西。
2. **表达清晰。**保持学术语域，不要刻意改成大白话。utilize、employ、demonstrate、facilitate 等标准学术用词可以正常使用。要删的是冗余结构（due to the fact that、it should be noted that）和名词化的动词（conduct an analysis of → analyze）。
3. **句式简单，长度多变。**结构上一句一个主要主张，主语与谓语之间不超过 10 个词，嵌套从句最多一层。但**不要把每句都写成 15 到 25 词**：句长高度均匀是最稳定的 AI 结构标记，短句和长句都要有，只要长句是线性推进而非多层嵌套。变化要跟着内容走，不要为了参差而人为抖动。
4. **逻辑紧密。**每段第一句承担论证功能，不是报菜名。段间衔接靠主题句本身，不靠 Moreover / Furthermore / In addition 堆叠。
5. **语法正确。**重点查：平行结构、比较结构是否完整、which 与 that、学术动词搭配、长主语的主谓一致、悬垂分词。
6. **时态默认现在时。**理论、模型、数据、实验流程、图表描述、结论一律用现在时。只有一次性历史事实（训练实际耗时、某个时点做过的一次性操作）用过去时，全文通常不超过三五处。这是中译英稿最常错的地方之一：中文写“我们构建了……模型”“我们收集了……数据”，直译过去就成了过去时。
7. **不用长破折号。**中文长破折号（——）与英文 em dash（—）一律不用，LaTeX 的 `---` 同理。en dash（–）仅用于数字区间和复合专名。破折号是模型文风最强的标记之一，删除时按替换策略改写，不要只把它换成逗号。
8. **禁止 AI 味。**分四类：标记词（delve、underscore、tapestry、pivotal、seamless、harness、paramount 等，注意 robust 与 robustness 是技术术语不在此列）、标记短语（It is worth noting that、plays a crucial role in、In conclusion 等）、结构性痕迹（三项排比成瘾、每段结尾加概括句、句长与段长过于均匀、连接词链条）、内容性痕迹（泛而不深、该有立场时没有立场）。词表会随模型代际过期，机制不会：模型的用词过于可预测、句式过于均匀。内容具体了，AI 味自然消退大半。

另有一条正向要求：**说服力**。方法论文的说服力来自六件事，见 `references/style-and-consistency.md` 第六节。其中最关键的是**预先反驳**（每个设计组件都要回答"为什么不用更简单的做法"）和**声称与证据配对**（写 `Our model is interpretable` 而不指向哪张图哪个案例，等于没写）。

第 7、8 两条和一致性检查，脚本能替你扫一遍。

---

## 中文论文带过来的习惯

词汇层的直译清单在 `references/cn-en-transfer.md` 第一节，脚本也会扫。这里只留结构层的四条，因为它们换个词解决不了，得改段落：

- **开头是 `With the rapid development of...` / `In recent years, more and more scholars...`**。方法论文第一段应立刻给出现象规模或业务张力。
- **段间衔接只有 Firstly, Secondly, Thirdly, Finally**。这是编号，不是逻辑关系。
- **相关工作写成编年体流水账**。应按方法族组织，每族末尾说清为什么不够用。
- **管理启示写成"企业应重视 X"**。必须从模型输出推导。

---

## 各模式的具体做法

### 润色模式

1. 通读一遍，先判断有没有第二、三条规则说的实质性问题。有就先标出来。
2. 逐段改写。按 `references/cn-en-transfer.md` 处理句法与用词。
3. 时态统一为现在时，例外见 `references/cn-en-transfer.md` 第二节。
4. 跑 `scripts/check_draft.py`，再用 `--compare` 确认引用、公式与数字没被动过。符号一致性（上下标、粗体向量与斜体标量的区分、估计值的帽子记号）脚本查不了，人工过一遍。
5. 按"改动怎么呈现"交付。

改的幅度以"作者能认出这还是自己的文章"为界。

### 起草模式

1. 先明确这一节要承担什么功能（引言要立起挑战，评估要把性能归因到设计），再动笔。
2. 按 `references/design-science-genre.md` 的结构模板写。摘要与标题另见该文件第十三节。
3. 所有需要作者填的地方用显式占位符：`[待补引用：...]`、`[待补数据：基线的具体配置]`、`[待确认：这条挑战对应模型的哪个组件]`。
4. 写完对照 `references/design-science-genre.md` 第十二节的拒稿原因清单自查，再跑一遍脚本。

起草时不要替作者编造实验结果、数据规模或基线表现。不知道就留占位符并说明需要什么。

### 结构诊断模式

不要交重写稿。作者要的是知道哪里坏了、为什么坏。

按这个顺序检查，报告最先崩掉的一层。上层不成立时，下层写得再漂亮也没用：

1. **挑战是否成立**。列出的每个挑战，是否真的是既有方法处理不了的方法层面困难？能不能点名到具体方法族并说清为什么做不到？
2. **挑战 ↔ 设计是否对应**。模型的每个组件能否指回某个挑战？有没有"复杂但和挑战无关"的部分？有没有"提了挑战但没有对应设计"的？
3. **设计 ↔ 评估是否对应**。消融实验是否覆盖每个设计决策？可解释性、效率这类声称有没有对应的展示或数字？
4. **贡献声明 ↔ 实际做到的是否一致**。引言承诺 N 条，讨论是否兑现 N 条？贡献是设计知识还是只是"我们提出了新模型"？
5. **理论是否真的在起作用**（投 ISR/MISQ 时必查）。理论章节之后模型有没有引用它？还是引言点个名就消失了？
6. **管理启示是否从模型输出推出**。换一篇论文还成立的建议就是空的。

这六层的详细判据在 `references/design-science-genre.md`。

每条问题给出：在哪（定位到段落或小节号）、为什么是问题（用审稿人会说的话）、怎么改（一到两个具体方向，不是"建议加强论证"）。

---

## 参考文件

| 文件 | 什么时候读 |
|---|---|
| `references/style-and-consistency.md` | 处理任何成稿都要读：文风硬约束、一致性检查清单、AI 味清除、说服力 |
| `references/design-science-genre.md` | 结构、挑战架构、kernel theory、贡献声明、评估章节、摘要与标题、诊断判据 |
| `references/cn-en-transfer.md` | 涉及中译英、中式英文、术语、句法、声称强度时 |
| `scripts/check_draft.py` | 交付前必跑；润色模式另跑 `--compare` |
