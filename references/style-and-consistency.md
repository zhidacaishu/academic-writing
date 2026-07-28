# 文风、一致性与说服力

本文件是全局约束，不分模式，不分章节，所有输出都要过一遍。

---

## 一、硬性禁止：长破折号

中文长破折号（——）与英文 em dash（—）一律不用，LaTeX 源码里的 `---` 同理。en dash（–）仅用于数字区间（pp. 1–22、K = 10–30）和复合专名（Gauss–Newton），不用于句内停顿。

破折号是模型文风最强的标记之一。删除时按下面的策略改写，不要只把破折号换成逗号，那样往往留下一个结构松垮的句子。

| 破折号的功能 | 替换方式 | 例 |
|---|---|---|
| 插入补充说明 | 括号 | `Three baselines—LDA, DTM, and HPF—were used` → `Three baselines (LDA, DTM, and HPF) are used` |
| 引出解释或展开 | 冒号 | `The reason is simple—the data are sparse` → `The reason is simple: the data are sparse` |
| 连接两个完整小句 | 分号或拆句 | `The model converges quickly—it requires no sampling` → `The model converges quickly because it requires no sampling.` |
| 强调性停顿 | 直接删除或改用逗号 | `This is, in fact, the key trade-off` |
| 列举后的总结 | 拆成两句 | `Sparsity, dynamics, and heterogeneity all matter. Our design addresses each.` |

中文稿里的破折号同理，改用括号、冒号或分句。

---

## 二、用词：保持学术register，只删膨胀

这一节的目标不是把学术英语改成大白话。INFORMS 系期刊有它的正式语域，刻意平实反而不专业。

**判断标准是这个词有没有承担信息，不是它有几个音节。**

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
| the vast majority of | most |
| prior to / subsequent to | before / after |
| at this point in time | now、currently |
| in spite of the fact that | although |
| has the ability to | can |
| make an assumption that | assume |
| conduct an analysis of | analyze |
| serve to illustrate | illustrate |

规律：**名词化的动词要还原成动词**（conduct an analysis → analyze），**多词介词短语要压缩**（due to the fact that → because）。这两类改动能在不损失正式度的前提下显著提高信息密度。

### 需要判断的几个

- **leverage**：在本领域论文里常见（leveraging individual-level estimates）。但如果只是"使用"的意思，改成 use 或 draw on。
- **delve into**：改成 examine、investigate。这个词是当前最强的 AI 标记之一，即使含义正确也建议避开。
- **state-of-the-art**：指代真实的当前最优基线时是准确用词，保留；用来形容自己的方法就是空话。
- **novel**：可以用，但一篇里出现三次以上就贬值了。

---

## 三、句式：结构简单，长度多变

这两件事要分开，混在一起会写出最像 AI 的文本。

### 结构要简单

1. 一句一个主要主张。两个并列的主张用两句话说，不要用 and 或分号硬粘。
2. 主语和它的谓语动词之间不超过 10 个词。中文允许极长主语，直译后动词出现太晚，句子就崩了。
3. 嵌套从句最多一层。从句里再套从句，中文能读懂，英文读者要回读。
4. 连用的介词短语不超过三个。`the effect of the number of highlights of the matches in the league on the engagement of the players` 这类链条要拆开重写。
5. 不用超过 15 词的状语从句开头。先给主句，再补条件。

### 长度要有变化

**不要把所有句子都写成 15 到 25 词。**语言学研究反复发现，LLM 生成的文本句长高度集中在 10 到 30 词区间，而人类写作的句长分布明显更分散、更常出现长句。句长的变异系数（标准差除以均值）低，是 AI 检测最稳定的结构指标之一。

所以正确的目标是：**结构简单，但长度参差。**8 词的短句和 35 词的长句都可以有，只要后者是线性推进的，不是嵌套三层的。

自检方法：`scripts/check_draft.py` 会算出全文的句长均值、标准差、变异系数和落在 15–25 词区间的比例。靠肉眼数几千词稿件的句长不可靠，这类统计交给脚本。

变异系数偏低时，改法是合并两个短句、拆开一个长句，或者在该下判断的地方写一句短的。注意**变化要跟着内容走**：为了参差而随机插入短句，会写出一种更假的节奏，读者能感觉到句子和它承担的内容不匹配。真实的长短变化来自"这句话要说的事情本身有多复杂"。

段落长度同理。真实写作里段落长短随内容变化，全篇整齐的 5 句段是痕迹。

### 被动语态

不是禁忌。受事更重要、或施事不言自明时（The model is estimated on a GPU server），被动是正确选择。但整段被动会让论证责任消失，模型章节尤其应该用 we。

---

## 四、前后一致

原则：**该固定的固定，不该固定的可以变。**过度追求"一个概念一个词"会让全文词汇重复率异常高，这本身也是 AI 文本的特征之一。

### 必须固定

- **有定义的技术构念**。论文里正式定义过的概念，全文用同一个词。定义为 latent interest 的东西，不要在别处写成 hidden preference，因为读者会以为是两个东西。
- **符号**。上下标、粗体（向量与矩阵）与斜体（标量）的区分、估计值的帽子记号、真值与估计值的区分。同一个量在正文、公式、图、表、算法块里用同一个符号。
- **方法名**。包括大小写与连字符位置。MS-DBN 不能在别处写成 MS DBN 或 MSDBN。
- **缩写**。首次出现给全称加缩写，之后一律用缩写。摘要和正文各定义一次，因为摘要可能被单独阅读。标题里不用未定义的缩写。
- **数字格式**。小数位数、千分位分隔符、百分比与百分点的区分。

### 可以变化

- **指代自己的方法**：our model、the proposed approach、方法缩写之间轮换是正常的。
- **一般性描述用语**：prior work / earlier studies / existing methods 可以换用；show / find / report / document 也可以。
- **构念的非正式复述**：正式名首次给出后，在不引起歧义的段落里用一个更短的说法回指是可以的，前提是读者不会误以为是新概念。

判断依据：**换词会不会让读者以为这是另一个东西。**会就固定，不会就可以变。

### 连字符

作定语时加，作名词时不加。这是高频错误。

- long-tail items / in the long tail
- state-of-the-art methods / the state of the art
- real-world data / in the real world
- high-dimensional space / the space is high dimensional

### 其他

拼写变体二选一（INFORMS 系用美式）；引用格式全文一致；图表引用格式一致（Table 3、Figure 5，首字母大写）。

---

## 五、禁止 AI 味

### 先理解机制

检测和人工识别都建立在两个量上：

- **困惑度（perplexity）**：文本对语言模型的可预测程度。模型倾向于选高概率词，所以生成文本的用词比人类更"意料之中"。
- **突发度（burstiness）**：句长与句式在全文中的变化幅度。人类在长短句之间来回切换，模型倾向于保持均匀。

理解这两点比背黑名单重要，因为**词表会随模型代际变化**：早期的标记词是 delve、tapestry、meticulous、pivotal，之后转向 fostering、showcasing、align with，再之后是 emphasizing、enhancing、highlighting 这类框架动词。固定名单会过期，机制不会。

一个重要的反面提醒：**不要以通过检测器为目标。**学术写作本身就是格式化的，人类写的正式学术文本困惑度和突发度天然偏低，检测器误报率很高（有报道称《圣经》和美国宪法片段都被判为 AI 生成）。而且所谓的 humanizer 工具已经被 Turnitin 等系统专门识别，反而增加风险。正确的目标是**让人类读者读起来自然**，不是让某个分数好看。

### 标记词

delve、underscore（作动词）、tapestry、intricate、pivotal、multifaceted、realm（比喻义）、landscape（比喻义）、seamless、holistic、testament、garner、harness（比喻义）、navigate（比喻义）、unlock（比喻义）、revolutionize、paramount、meticulous、showcase（作动词）、foster（滥用时）、nuanced（滥用时）、comprehensive（滥用时）。

注意：robust 和 robustness 在方法论文里是技术术语（robustness checks），不在此列。crucial、critical、significant 在有具体所指时可用，泛泛地说 plays a crucial role 才是问题。

### 标记短语

`It is worth noting that` · `It is important to note that` · `plays a crucial role in` · `sheds light on` · `paves the way for` · `In today's rapidly evolving landscape` · `At its core` · `This raises an important question` · `In conclusion`（结论段直接讲结论）· `Overall,`（作段首万能开头时）

### 结构性痕迹

- **三项排比成瘾。**每个列举都恰好三项。真实的列举经常是两项或四项。
- **每段结尾加一句概括。**"因此，这一设计对模型性能至关重要。"学术段落靠证据推进，不靠打气。
- **句长与段长过于均匀。**见第三节。
- **not only X but also Y 反复出现。**
- **连接词链条。**Furthermore / Moreover / Additionally / In addition 连续出现在相邻段首。
- **否定式排比。**"这不只是一个模型问题，而是一个设计问题。"
- **平行小句成瘾。**模型偏好 `X does A, Y does B, and Z does C` 这种整齐结构，人类写作里这三件事常常长度不等、结构不同。

### 内容性痕迹

这一类人工审稿人最容易察觉，也最难靠改词解决：

- **泛而不深。**给出正确但空洞的描述，没有具体解释、没有取舍分析、没有作者自己的判断。审稿人会读成"作者其实没想清楚"。
- **该有立场的地方没有立场。**万事皆有两面的假平衡。
- **对不确定的东西和确定的东西用同样强度的措辞。**
- **绕圈子。**回答前先把问题复述一遍。

解决办法是补具体内容：给数字、给条件、给反例、说明为什么不选另一条路。**内容具体了，AI 味自然消退大半。**

---

## 六、说服力

方法类论文的说服力不来自形容词，来自六件事。

1. **用数字代替形容词。**"效率很高"没有说服力；"在 50 万用户的数据上训练约 30 小时，迁移到新用户只需重估一组参数"有。
2. **预先反驳。**在审稿人想到之前先提出反对意见并回答。模型章节每个组件都要回答"为什么不用更简单的做法"。句式：`One might expect that a simpler X would suffice. However, X cannot handle Y because Z.`
3. **声称与证据配对。**写 `Our model is interpretable` 而不指向哪张图哪个案例，等于没写。写 `The learned latent states align with the funnel stages (Figure 4)` 才成立。
4. **主动划界换取信任。**承认方法做不到的事，读者才会相信你说做得到的事。
5. **让读者自己得出结论。**给出对比和证据，不要替读者下判断。`Our method achieves 0.2855 versus 0.2549 for the best baseline` 比 `Our method is clearly better` 有力。
6. **具体到组件和条件。**"我们的方法更好"是空的；"在稀疏度更高的全商品集上，我们的性能下降幅度为 23%，而其他方法普遍超过 40%"是实的，还顺带说明了为什么好。

---

## 七、高频语法问题

cn-en-transfer.md 覆盖了冠词、不可数名词、逗号粘连、话题述题残留、名词堆叠、超长主语。这里补几条同样高频、但容易漏掉的。

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

`superior than` 和严格比较语境下的 `compared to` 都是常见错误。

### 主谓一致

长主语后面容易配错动词，尤其是主语中心词后跟了介词短语。

- 错：`The performance of the three baseline methods are reported in Table 2.`
- 对：`The performance of the three baseline methods is reported in Table 2.`

### 悬垂分词

分词短语的逻辑主语必须是主句主语。

- 错：`Using a GPU server, the estimation took 30 hours.`（服务器不会做估计）
- 对：`Using a GPU server, we complete the estimation in 30 hours.`
