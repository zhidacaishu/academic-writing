# 文风、一致性与说服力

本文件只约束本 skill 生成或润色的英文论文正文，不约束中文来源文本、面向作者的中文说明或 LaTeX 注释、公式和其他非散文源码。

---

## 一、硬性禁止：长破折号

中文长破折号（——）与英文 em dash（—）一律不用，LaTeX 源码里的 `---` 同理。en dash（–）仅用于数字区间（pp. 1–22、K = 10–30）和复合专名（Gauss–Newton），不用于句内停顿。

长破折号容易形成明显的模型化表达特征。删除时应按以下策略改写，不要只替换为逗号，否则句法关系可能仍不清晰。

| 破折号的功能 | 替换方式 | 例 |
|---|---|---|
| 插入补充说明 | 括号 | `Three baselines—LDA, DTM, and HPF—were used` → `Three baselines (LDA, DTM, and HPF) are used` |
| 引出解释或展开 | 冒号 | `The reason is simple—the data are sparse` → `The reason is simple: the data are sparse` |
| 连接两个完整小句 | 分号或拆句 | `The model converges quickly—it requires no sampling` → `The model converges quickly; it requires no sampling.` |
| 强调性停顿 | 直接删除或改用逗号 | `This is, in fact, the key trade-off` |
| 列举后的总结 | 拆成两句 | `Sparsity, dynamics, and heterogeneity all matter. Our design addresses each.` |

中文来源文本出现破折号时，不修改中文原文；翻译成英文时根据原句逻辑在英文输出中改用括号、冒号或分句。

---

## 二、用词：保持学术语域，压缩冗余表达

本节的目标不是将学术英语改为过度口语化的表达。INFORMS 体系期刊具有相应的正式语域，过度简化可能降低专业性。

**判断标准是词语是否承担具体信息，而不是词语长度。**

### 可以正常使用

utilize、employ、demonstrate、facilitate、substantial、comprise、constitute、derive、yield、exhibit、incorporate、attribute to、in line with、with respect to、be subject to、a set of。这些是标准学术用词。utilize 在"使用某种资源或方法"的语境下完全成立，不必一律改成 use。

技术术语更不受限：sparsity、endogeneity、heterogeneity、latent、generative、stochastic、robustness、identification、tractability。它们是精确概念，没有平实替代。

### 需要删或改的

问题在冗余结构，不在单词本身：

| 膨胀写法 | 改为 |
|---|---|
| due to the fact that | because |
| in order to | to（除非需要强调目的） |
| it should be noted that | 删除，该说就直接说 |
| it is important to note that | 删除 |
| in the realm of / in the context of（滥用时） | in |
| a wide array of / a myriad of | various、many、或直接给数量 |
| prior to / subsequent to（无明确时序含义时） | before / after |
| at this point in time | now、currently |
| in spite of the fact that | although |
| has the ability to | can |
| make an assumption that | assume |
| conduct an analysis of | analyze |

规律：**名词化的动词要还原成动词**（conduct an analysis → analyze），**多词介词短语要压缩**（due to the fact that → because）。这两类改动能在不损失正式度的前提下显著提高信息密度。

### 需要判断的几个

- **leverage**：在本领域论文里常见（leveraging individual-level estimates）。但如果只是"使用"的意思，改成 use 或 draw on。
- **delve into**：在正式研究写作中通常可改为 examine 或 investigate；若确需表达深入分析且语境自然，可以保留。
- **state-of-the-art**：指代真实的当前最优基线时是准确用词，保留；用来形容自己的方法就是空话。
- **novel**：可以用，但一篇里出现三次以上就贬值了。
- **the vast majority of**：只有在证据支持“绝大多数”时保留，最好给出比例；若只表达“多数”，用 most。
- **serve to illustrate**：通常可压缩为 illustrate；若 serve 用于强调作用或功能，可以保留。

---

## 三、句式：结构简单，长度多变

结构与长度应分别判断。

### 结构要简单

1. 一句表达一个主要主张。两个并列主张可分别成句，避免仅用 and 或分号强行连接。
2. 缩短主语与谓语动词之间的距离。中文允许较长主语，直译后谓语出现过晚会增加句法解析难度。
3. 避免多层嵌套从句。从句里再套从句，中文能读懂，英文读者要回读。
4. 避免长串连用的介词短语。`the effect of the number of highlights of the matches in the league on the engagement of the players` 这类链条要拆开重写。
5. 避免用过长的状语从句开头。先给主句，再补条件。

### 长度要有变化

**不要把所有句子都写成 15 到 25 词。**句长应由信息密度和句法关系决定；短句与长句都可以成立，只要长句线性推进且不过度嵌套。

需要描述文本节奏时，运行 `python3 scripts/check_draft.py draft.tex --sentence-metrics`。该选项只报告句数、均值、标准差、变异系数和 15–25 词占比，不产生问题等级，也不影响退出码。不得根据固定阈值机械合并或拆分句子。

段落长度同样应随内容变化。全文段落长度高度一致时，应检查是否存在机械化结构。

### 被动语态

不是禁忌。受事更重要、或施事不言自明时（The model is estimated on a GPU server），被动是正确选择。但整段被动会让论证责任消失，模型章节尤其应该用 we。

---

## 四、前后一致

原则：**定义明确的术语应保持一致，一般性表达可以适度变化。**过度追求“一个概念只用一个词”会造成不必要的词汇重复。

### 必须固定

- **有定义的技术构念**。论文中正式定义的概念应全文使用同一术语。若定义为 latent interest，则不应在其他位置改为 hidden preference，以免读者误认为二者是不同概念。
- **符号**。上下标、粗体（向量与矩阵）与斜体（标量）的区分、估计值的帽子记号、真值与估计值的区分。同一个量在正文、公式、图、表、算法块里用同一个符号。
- **方法名**。包括大小写与连字符位置。MS-DBN 不能在别处写成 MS DBN 或 MSDBN。
- **缩写**。首次出现给全称加缩写，之后一律用缩写。摘要和正文各定义一次，因为摘要可能被单独阅读。标题里不用未定义的缩写。
- **数字格式**。同一表格、同一指标或直接可比的一组数值应保持一致精度；不同统计对象可以采用不同但合理的精度。千分位分隔符、百分比与百分点的区分应保持一致。

### 可以变化

- **指代自己的方法**：our model、the proposed approach、方法缩写之间轮换是正常的。
- **一般性描述用语**：prior work / earlier studies / existing methods 可以换用；show / find / report / document 也可以。
- **构念的非正式复述**：正式名首次给出后，在不引起歧义的段落里用一个更短的说法回指是可以的，前提是读者不会误以为是新概念。

判断依据：**替换说法是否可能使读者误认为出现了新的概念。**如有歧义，应保持术语一致；如无歧义，可以适度变化。

### 连字符

作定语时加，作名词时不加。这是高频错误。

- long-tail items / in the long tail
- state-of-the-art methods / the state of the art
- real-world data / in the real world
- high-dimensional space / the space is high dimensional

### 其他

拼写变体二选一（INFORMS 系用美式）；引用格式全文一致；图表引用格式一致（Table 3、Figure 5，首字母大写）。

---

## 五、复核机械化与空泛表达

本节只评估文本质量，不推断文本来源，也不以规避检测为目标。合法词语或句式本身不构成问题；只有当表达缺乏具体所指、机械重复、掩盖可验证内容或削弱论证时才修改。

### 词语与过渡语

crucial、critical、significant、robust、comprehensive、nuanced 等正式词语可以使用，但必须有明确对象和证据。`It is worth noting that`、`plays a crucial role in`、`sheds light on`、`In conclusion`、段首 `Overall,` 等表达若不承担逻辑功能或信息增量，应删除或改写。不要因某个词或短语出现在固定名单中而机械替换。

### 结构性问题

- **机械重复三项排比。**如果每个列举都恰好包含三项，应检查是否由内容需要决定。
- **每段结尾都增加概括句。**例如“因此，这一设计对模型性能至关重要。”如果没有新增证据或判断，应删除此类重复总结。
- **句长与段长过于均匀。**见第三节。
- **not only X but also Y 反复出现。**
- **连接词链条。**Furthermore / Moreover / Additionally / In addition 连续出现在相邻段首。
- **否定式排比。**"这不只是一个模型问题，而是一个设计问题。"
- **过度使用平行小句。**反复使用 `X does A, Y does B, and Z does C` 等高度整齐的结构时，应根据内容关系调整句式。

### 内容性问题

这一类人工审稿人最容易察觉，也最难靠改词解决：

- **内容缺乏具体性。**只给出一般性描述，没有具体解释、取舍分析或作者判断。
- **需要明确判断的位置缺乏立场。**避免在证据已经支持特定结论时仍维持没有依据的表面对称。
- **对不确定的东西和确定的东西用同样强度的措辞。**
- **无信息增量的复述。**在回答前重复问题，但没有提供新的分析。

解决方法见第六节。提高内容具体性通常可以同时改善论证质量和阅读自然度。

---

## 六、说服力

方法类论文的说服力不来自形容词，来自四件事。

1. **用数字、对比和条件代替形容词。**“效率很高”缺乏可核查依据；“在 50 万用户的数据上训练约 30 小时，迁移到新用户只需重估一组参数”提供了具体证据。避免仅使用主观判断，`Our method achieves 0.2855 versus 0.2549 for the best baseline` 比 `Our method is clearly better` 更具可验证性。“我们的方法更好”同样缺乏可核查证据；“在稀疏度更高的全商品集上，我们的性能下降幅度为 23%，而其他方法普遍超过 40%”明确了条件和比较结果。
2. **预先回应替代解释。**模型章节的每个组件都应回答“为什么不用更简单的做法”。句式：`One might expect that a simpler X would suffice. However, X cannot handle Y because Z.`
3. **声称与证据配对。**写 `Our model is interpretable` 而不指向具体图表或案例，不能形成可核查的证据。写 `The learned latent states align with the funnel stages (Figure 4)` 则建立了证据对应关系。
4. **主动划界换取信任。**承认方法做不到的事，读者才会相信你说做得到的事。

---

## 七、高频语法问题

cn-en-transfer.md 已覆盖冠词、不可数名词、逗号粘连、话题述题残留、名词堆叠和超长主语。本节补充其他常见且容易遗漏的问题。

### 平行结构

列举项的语法形式必须一致。

- 错：`The model handles sparsity, modeling dynamics, and is interpretable.`
- 对：`The model handles sparsity, models dynamics, and remains interpretable.`

分条列举、贡献声明里的三条，都要检查形式是否平行。

### 比较结构不完整

`Our method performs better` 要说明 better than what。`higher accuracy` 要说明 higher than which baseline。中文可以省略比较对象，英文不行。

### which 与 that

限定性从句用 that，不加逗号；非限定性用 which，加逗号。中文没有这个区分，直译时经常错。

- `the model that we propose`（限定）
- `our model, which is based on LDA,`（非限定）

### 学术动词的固定搭配

consist of · result in · differ from · comparable to · superior to · contribute to · account for · in contrast to（或 with）· compared with · based on · consistent with · subject to

`superior than` 是常见错误（应为 `superior to`）。`compared to` 与 `compared with` 在本领域期刊中都通行，不必互改。

### 主谓一致

长主语后面容易配错动词，尤其是主语中心词后跟了介词短语。

- 错：`The performance of the three baseline methods are reported in Table 2.`
- 对：`The performance of the three baseline methods is reported in Table 2.`

### 悬垂分词

分词短语的逻辑主语必须是主句主语。

- 错：`Using a GPU server, the estimation takes 30 hours.`（服务器不会做估计）
- 对：`Using a GPU server, we complete the estimation in 30 hours.`
