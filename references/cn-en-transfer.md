# 中译英与中式学术英语处理

本文件处理中文思路写出的英文稿。分五部分：

1. 用词对照表
2. 句法层面的母语迁移
3. 因果与不确定性的表达强度
4. 段落与衔接
5. 常被误判为"错误"、其实应该保留的东西

---

## 一、用词对照表

左列是中文原意，中列是直译（应避免），右列是英文期刊惯用。

### 研究对象与主体

| 中文 | 避免 | 惯用 |
|---|---|---|
| 企业 | enterprise | firm（管理、战略、金融）；company；business（泛指） |
| 上市公司 | listed company | listed firms；publicly traded firms；A 股用 A-share listed firms |
| 国有企业 | state-owned enterprise（可用但注意） | state-owned enterprises (SOEs)，首次出现给全称加缩写 |
| 员工 | staff（不可数，易错） | employees；workers |
| 高管 | senior manager | executives；top management team (TMT) |
| 学者们 | scholars（滥用） | prior research；prior studies；a growing literature |
| 国内外学者 | domestic and foreign scholars | 删除该划分，改为 prior research |

### 模型与方法

| 中文 | 避免 | 惯用 |
|---|---|---|
| 本文提出的方法 | the method proposed by this paper | our proposed method；our approach |
| 框架 | frame | framework |
| 隐变量 / 潜变量 | hidden variable（口语） | latent variable |
| 隐状态 | hidden state（RNN 语境正确） | latent state（统计模型）；hidden state（神经网络） |
| 生成过程 | generate process | generative process |
| 先验 / 后验 | prior probability（冗余） | prior；posterior |
| 超参数 | super parameter | hyperparameter（一个词，不加连字符） |
| 目标函数 | target function | objective function；loss function |
| 收敛 | convergent（形容词误用） | converge（动词）；convergence（名词） |
| 拟合 | fit degree | model fit；goodness of fit |
| 过拟合 | over fitting | overfitting |
| 稀疏性 | sparse problem | sparsity；data sparsity |
| 冷启动 | cold boot | cold-start problem |
| 长尾 | long tail（正确） | long-tail items / accounts（作定语时加连字符） |
| 可解释性 | explanatory | interpretability（模型可读）；explainability（可给出解释） |
| 泛化能力 | generalization ability | generalizability；generalization performance |
| 计算复杂度 | calculate complexity | computational complexity；time complexity |
| 参数估计 | parameter estimate（名词误用） | parameter estimation（过程）；parameter estimates（结果） |
| 调参 | adjust parameters | hyperparameter tuning |
| 分群 / 细分 | classify users | segmentation；segment consumers |

### 实验术语

| 中文 | 避免 | 惯用 |
|---|---|---|
| 基线方法 | baseline method（正确） | baselines；benchmark methods |
| 对比实验 | comparison experiment | comparison with baselines |
| 消融实验 | ablation experiment（可用） | ablation study；ablation analysis |
| 敏感性分析 | sensitivity analyse | sensitivity analysis |
| 稳健性检验 | robust test | robustness checks |
| 数据集 | data set / dataset（两种都通行） | 同一篇内保持一致；INFORMS 系多用 data set |
| 训练集 / 验证集 / 测试集 | train set | training set；validation set；test set |
| 划分 | divide the data | split the data into...；partition |
| 十折交叉验证 | ten fold cross validation | 10-fold cross-validation |
| 留一法 | leave one out | leave-one-out evaluation |
| 负采样 | negative sample（名词误用） | negative sampling（方法）；negative samples（样本） |
| 命中率 | hit rate（正确） | hit ratio (HR@K)；conversion rate (CR@N) |
| 提升 / 改进幅度 | promote 15% | improve by 15%；a 15% improvement over |
| 显著优于 | significantly better（无检验时误用） | 有检验才写 significantly；否则写 consistently outperforms |
| 达到最优 | reach the best | achieves the best performance |
| 运行时间 | run time | execution time；runtime |
| 复现 | repeat | replicate；reproduce |

**注意 significant 的双重含义。**中文"显著"在方法论文里既指统计显著也指"明显、可观"。英文 significant 在实验语境下默认被读成统计显著。没做检验就写 significantly outperforms，是审稿人第一眼会抓的问题。表示幅度大用 substantial、considerable、marked。

### 论文话语

| 中文 | 避免 | 惯用 |
|---|---|---|
| 本文 / 本研究 | this paper（可用但偏弱） | this study；本领域期刊普遍接受 we |
| 得出结论 | draw the conclusion | find；show；document；provide evidence that |
| 实证结果表明 | The empirical results indicate that | We find that；Results show that |
| 数据来源于 | The data comes from | We draw on data from；Data are drawn from |
| 具有重要意义 | has important significance | has implications for；matters for |
| 具有一定的参考价值 | has certain reference value | 删除，改为具体的 implications |
| 政策建议 | policy suggestion | policy implications |
| 管理启示 | management enlightenment | managerial implications；practical implications |
| 研究展望 | research prospect | directions for future research |
| 研究不足 | research deficiency | limitations |
| 丰富了……文献 | enriches the literature | contributes to；extends；advances（后接具体是怎么扩展的） |

### 高频冗余表达（直接删）

`with the rapid development of` · `in recent years, more and more` · `as we all know` · `it is well known that` · `obviously` · `and so on` · `etc.`（列举末尾）· `to a certain extent`（无量化时）· `very` · `greatly` · `deeply` · `seriously`（作程度副词时）· `it is not difficult to find that`

---

## 二、句法层面的母语迁移

### 冠词

中文无冠词系统，这是最高频的错误来源。三条经验规则：

- 抽象概念泛指时不加 the：`Firm performance is...` 不是 `The firm performance is...`
- 特指某个已定义的对象时加 the：`the sample`、`the coefficient on R&D intensity`
- 首次引入可数单数名词用 a/an：`We adopt a two-stage approach.`

### 不可数名词

以下词不加 s，且不用 a/an：research、literature、evidence、information、knowledge、advice、feedback、equipment。

- `literatures` 是明显的中式英语标记 → `the literature` 或 `prior studies`
- `researches` → `research` 或 `studies`
- `data`：作复数（`data are`）更正式，作单数在本领域也常见；同一篇内保持一致即可
- `data set` 与 `dataset` 两种写法都通行，INFORMS 系多用 `data set`；全文统一

### 逗号粘连

中文靠逗号串联小句，英文不行。

- 原：`Firm size is controlled, it may affect performance.`
- 改：`We control for firm size, which may affect performance.` 或拆成两句。

### 话题-述题结构残留

中文常先抛话题再评论，直译后主语落空。

- 原：`For the relationship between ownership and innovation, it has been widely studied.`
- 改：`The relationship between ownership and innovation has been widely studied.`

### 名词堆叠

中文可以无限修饰，英文超过三个名词连用就难读。

- 原：`enterprise green technology innovation efficiency evaluation index system`
- 改：`an index system for evaluating firms' efficiency in green technology innovation`

### 超长主语

中文允许主语拉很长，英文里动词出现太晚会崩。把长主语拆出来，或改用 that 从句后置。

- 原：`The impact of the digital transformation strategies adopted by manufacturing firms in emerging markets on their long-term innovation performance is significant.`
- 改：`Digital transformation significantly affects long-term innovation performance among manufacturing firms in emerging markets.`

### 时态

| 位置 | 时态 |
|---|---|
| 全篇默认 | **现在时** |
| 引言中的既有研究 | 现在时（`Prior research suggests`）或现在完成时（`Prior research has shown`） |
| 理论基础 | 现在时（`Engagement theory suggests that...`） |
| 模型描述 | 现在时（`Our model assumes`、`The attention mechanism learns`） |
| 数据与实验 | 现在时（`We use five years of clickstream data`、`We conduct a five-fold cross-validation`、`We remove users with fewer than ten records`） |
| 图表描述 | 现在时（`Table 3 reports`、`Figure 5 shows`） |
| 讨论与结论 | 现在时 |

**默认一律现在时。**模型是一个持续存在的构件，实验流程是一套可复现的程序，两者都用现在时描述。中文稿常写成"我们构建了……模型""我们收集了……数据"并直译成过去时，读起来像在讲一件做完的事，而不是在描述一个方法。

只有一类内容保留过去时：**一次性的历史事实**，即那件事发生在特定时间、不可重复。例如数据覆盖的时间区间（`The data set spans August 2014 to February 2015`，本身是现在时但描述的是历史区间）、模型训练实际耗费的时长（`Estimation took about 30 hours`）、以及在特定时点做过的一次性操作（`We collected match statistics for the same period`）。这类句子在全文中通常不超过三五处。

判断方法：这句话描述的是"读者照做也会成立的程序"还是"我们当时做的一件事"？前者用现在时，后者用过去时。

### 主动与被动

中文论文习惯全篇无主语或被动，英文期刊已普遍接受第一人称。本领域期刊常见 `We argue`、`We find`、`We contribute`。不要为了"客观"把每句改成被动，那会让论证责任消失，反而显得心虚。

单作者是否用 I：本领域期刊接受；不确定时用 this study 规避。

---

## 三、声称强度

这是最重要的一节。中文论文的表述强度普遍高于英文期刊可接受的水平，直译过去就成了过度声明。方法类论文有两处特别容易越界。

### 性能声称

```
Our method is superior to X.                              ← 无条件断言，几乎不该用
Our method significantly outperforms X.                   ← 必须有统计检验支撑
Our method outperforms X.                                 ← 需限定范围
On both data sets, our method outperforms all baselines.  ← 安全
Our method achieves the best performance among the
  compared baselines on both data sets.                   ← 最安全
```

判断规则：**声称的范围不能超过实验覆盖的范围。**一个数据集就不要说 in general；没做检验就不要用 significantly。

`首次提出` 直译成 `This is the first paper to...` 而不加缓冲是常见越界。标准缓冲是 to the best of our knowledge，且写之前真的要检索过。

### 机制与因果声称

模型章节和管理启示里仍会出现因果表述，同样有强度阶梯：

```
X causes Y
X has a significant impact on Y            ← 因果声明
X drives / increases Y                      ← 因果声明
X is positively associated with Y           ← 关联，安全
Our model captures the dependence of Y on X ← 描述模型，安全
```

`影响` 这个中文词覆盖了从"相关"到"导致"的全部范围，所以直译 impact/influence 时格外容易越界。方法论文尤其要注意：模型拟合出的系数方向不等于因果效应。Dhillon & Aral 就明确写出数据中没有随机变异，因此无法评估用户对推荐的响应性。这种主动划界的写法值得学。

### 反向问题：hedging 过度

不是越弱越好。以下写法会让贡献消失：

- `may possibly suggest that there might be some potential relationship`：三层限定叠加，等于什么都没说
- 结论段还在 `it seems that`：结论段应当承担立场
- 每句都加 `to some extent`

原则：**方法部分保守，讨论部分承担立场。**限定一次就够，不要叠加。

### 不显著结果

- 写 `We do not find evidence that X is related to Y`
- 不写 `X has no effect on Y`（这是在用不显著证明零效应）
- 更不写 `X is not significantly related to Y, but the coefficient is in the expected direction`（审稿人特别反感这句）

---

## 四、段落与衔接

### 主题句要承担论证功能

中文段落常把结论放最后。英文学术段落的第一句应当直接给出这一段要确立什么，后文提供支撑。

- 弱：`Many scholars have studied absorptive capacity. Cohen and Levinthal (1990) proposed... Zahra and George (2002) extended...`（这是文献罗列）
- 强：`Although absorptive capacity is consistently linked to innovation outcomes, the literature disagrees on whether it operates through knowledge acquisition or knowledge integration.`（这是在建立张力）

方法论文的相关工作章节同理：

- 弱：`Author A (2009) proposes a time-sensitive MF method. Author B (2011) uses tensor factorization. Author C (2019) applies attention mechanisms.`（罗列）
- 强：`These approaches all treat time as an exogenous index, which requires timestamps that are unavailable in most recommendation settings.`（指出方法族的共同局限）

判断标准：把每段第一句抽出来连读，应该能看出整篇的论证线。如果连读像目录，说明主题句只在报菜名。

### 衔接词

不要靠 Moreover / Furthermore / In addition / Besides 堆叠推进。这些词只表明"还有一点"，不表明逻辑关系。用它们串起来的段落，实际上是并列的清单。

有信息量的衔接是指出关系：`This assumption is problematic because...`、`A competing explanation is that...`、`If this mechanism holds, we should also observe...`

`Besides` 在学术英语中偏口语，用 `In addition` 或改写。

### 段落长度

英文期刊正文段落一般 4–8 句。中文稿直译过来常出现只有两句的段落（读起来碎）或整页不分段（读起来堵）。合并或拆分时以"一段一个论点"为准。

---

## 五、不要过度纠正的地方

以下不是错误，改了反而失真：

- **作者自造的方法名与假设名**。PE-LDA 的 string-of-beads 假设、MS-DBN 这类命名是作者的知识产权标签，不要因为"英文里不这么说"就替换。命名可以建议（要求：好记、能提示核心机制、缩写不与既有方法冲突），但改动必须标为实质性修改。
- **中国情境的术语**：guanxi、hukou、danwei 等已进入英文文献，首次出现加简短解释即可，不必强行译成英文近义词。中国平台名（Tmall、Taobao、Douyin、Weibo）用官方英文名，首次出现加一句说明规模或性质。
- **中国制度的专有名词**：split-share structure reform（股权分置改革）、Belt and Road Initiative、A-share market 等有约定译法，按惯例走，不要自创。
- **中文期刊投稿**。如果目标是《管理世界》《经济研究》等，中文学术文体自有规范，不要用英文期刊的标准去改中文稿的结构。
