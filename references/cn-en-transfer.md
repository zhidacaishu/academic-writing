# 中译英与中式学术英语处理

本文件只处理中文思路或中文来源文本向**英文论文正文**的迁移，不起草或润色中文论文正文。分五部分：

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

**注意 significant 的双重含义。**中文“显著”在方法论文里既可指统计显著，也可表示“明显、可观”。英文 significant 在实验语境下通常被理解为具有统计检验依据。没有相应检验时，不应写 significantly outperforms。表示幅度较大可用 substantial、considerable 或 marked。

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

### 高频冗余表达（删除或改为具体表述）

`with the rapid development of` · `in recent years, more and more` · `as we all know` · `it is well known that` · `obviously` · `and so on` · `etc.`（列举末尾）· `to a certain extent`（无量化时）· `very` · `greatly` · `deeply` · `seriously`（作程度副词时）· `it is not difficult to find that`

---

## 二、句法层面的母语迁移

### 冠词

中文没有冠词系统，因此冠词是中译英稿中的常见错误来源。先判断名词是否可数、是单数还是复数，再判断是泛指还是特指。可采用以下规则：

- 抽象概念泛指时不加 the：`Firm performance is...` 不是 `The firm performance is...`
- 可数名词单数通常不能单独出现，前面需要冠词、指示词、所有格或其他限定词：`a model`、`the model`、`this model`、`our model`，不能写 `We propose model.`
- 首次引入一个非特定的可数单数对象时用 a/an：`We adopt a two-stage approach.`；后续再次指代该对象时通常用 the：`The approach consists of two stages.`
- 特指已定义、已提及或由后置修饰语明确限定的对象时用 the：`the sample`、`the coefficient on R&D intensity`、`the model described in Section 3`
- 可数名词复数或不可数名词用于类别泛指时通常不加冠词：`Firms differ in their capabilities.`、`Information affects decision quality.`
- a/an 取决于后续词语开头的**读音**，而不是字母：`an MCMC method`、`a university-based study`

高频检查方法：逐项查找裸露的可数单数名词，并确认其前面是否已有适当限定词；再检查 the 是否确实指向读者能够识别的特定对象。不要仅因为名词在论文中重要就加 the。

### 不可数名词

以下词不加 s，且不用 a/an：research、literature、evidence、information、knowledge、advice、feedback、equipment。

- `literatures` 是常见的中式英语用法 → `the literature` 或 `prior studies`
- `researches` → `research` 或 `studies`
- `data`：作复数（`data are`）更正式，作单数在本领域也常见；同一篇内保持一致即可
- `data set` 与 `dataset` 两种写法都通行，INFORMS 系多用 `data set`；全文统一

### 逗号粘连

中文可以用逗号串联多个小句，英文通常需要使用连词、从句或分句。

- 原：`Firm size is controlled, it may affect performance.`
- 改：`We control for firm size, which may affect performance.` 或拆成两句。

### 话题-述题结构残留

中文常先提出话题再进行评论，直译后可能缺少明确的语法主语。

- 原：`For the relationship between ownership and innovation, it has been widely studied.`
- 改：`The relationship between ownership and innovation has been widely studied.`

### 名词堆叠

中文允许较长的前置修饰结构；英文连续使用多个名词作前置修饰时会增加理解负担。

- 原：`enterprise green technology innovation efficiency evaluation index system`
- 改：`an index system for evaluating firms' efficiency in green technology innovation`

### 超长主语

中文允许较长的主语结构；英文中谓语出现过晚会增加句法解析难度。可以拆分长主语，或使用 that 从句后置相关内容。

- 原：`The comparison of model performance across the five experimental settings under the sparse-data condition is reported in Table 4.`
- 改：`Table 4 reports model performance across the five experimental settings under the sparse-data condition.`

改写长主语时只调整句法焦点，不改变统计、因果或证据范围。除非原稿已有相应检验与识别设计，不得因缩句引入 `significantly`、`affects`、`drives` 等更强声称。

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

**除下述例外外，默认使用现在时。**模型是持续存在的构件，实验流程是可复现的程序，因此两者均用现在时描述。中文稿常把“我们构建了……模型”“我们收集了……数据”直译为过去时，从而将方法描述误写为一次性历史叙述。

过去时用于**一次性的历史事实**，即发生在特定时间且不作为可复现程序描述的事件。例如数据覆盖的时间区间（`The data set spans August 2014 to February 2015`，句子本身仍用现在时）、模型训练实际耗费的时长（`Estimation took about 30 hours`），以及特定时点完成的一次性操作（`We collected match statistics for the same period`）。如果全文出现多处过去时，应逐项确认其是否属于此类事实。

判断方法：若句子描述可复现的程序，则使用现在时；若描述特定时点发生的一次性事实，则使用过去时。

### 主动与被动

中文论文常使用无主语句或被动语态，英文期刊则普遍接受第一人称。本领域期刊常见 `We argue`、`We find` 和 `We contribute`。不要仅为追求“客观”而将每句改为被动语态，否则可能弱化论证主体和责任归属。

---

## 三、声称强度

本节用于确保论断强度与证据范围一致。中文论文中的强度表达直接译入英文时，可能形成证据不足的强声明。方法类论文尤其需要检查性能声称与因果声称。

### 性能声称

```
Our method is superior to X.                              ← 无条件断言，通常不使用
Our method significantly outperforms X.                   ← 必须有统计检验支撑
Our method outperforms X.                                 ← 需限定范围
On both data sets, our method outperforms all baselines.  ← 安全
Our method achieves the best performance among the
  compared baselines on both data sets.                   ← 最安全
```

判断规则：**声称的范围不能超过实验覆盖范围。**仅使用一个数据集时，不应使用 in general；未进行统计检验时，不应使用 significantly。

将“首次提出”直译为 `This is the first paper to...` 而不加限定，容易形成证据范围过大的声明。常用限定语是 to the best of our knowledge，且仅应在完成充分文献检索后使用。

### 机制与因果声称

模型章节和管理启示中可能同时出现三类不同声明：现实世界中的因果关系、数据中的统计关联，以及模型内部表示的依赖关系。三者需要严格区分：

```
X causes Y
X has a significant impact on Y            ← 因果声明
X drives / increases Y                      ← 因果声明
X is positively associated with Y           ← 关联，安全
Our model captures the dependence of Y on X ← 描述模型，安全
```

中文“影响”可能表示相关关系，也可能表示因果作用。翻译为 impact、influence、drive、increase 或 reduce 时，英文读者通常会将其理解为因果声明。只有研究设计能够识别干预效应时，例如采用随机实验、可信的准实验设计或明确的因果识别策略，才应使用这类表达。

如果证据来自观察数据、预测模型或一般回归分析，通常只能写 `is associated with`、`is related to` 或 `predicts`。如果句子只描述模型结构或估计结果，应写 `the model captures the dependence of Y on X` 或 `the estimated coefficient is positive`。正系数说明模型估计的条件关联方向为正，不表示改变 X 会导致 Y 改变，也不能直接支持“采取某项措施将提高转化率”等管理建议。

判断时应先问：这句话是在描述数据中的共变关系、模型中的参数关系，还是对现实干预结果作出推断？前两类不得改写为第三类。若数据缺乏支持因果识别的变异，应明确限定研究只能评估关联或预测能力。

### 反向问题：hedging 过度

不是越弱越好。以下写法会让贡献消失：

- `may possibly suggest that there might be some potential relationship`：叠加三层限定语，导致主张不明确
- 结论段还在 `it seems that`：结论段应当承担立场
- 每句都加 `to some extent`

原则：**方法部分应严格限定推断范围，讨论部分应明确陈述有证据支持的立场。**通常只需使用一层限定语，避免重复叠加。

---

## 四、段落与衔接

### 主题句要承担论证功能

中文段落常把结论放最后。英文学术段落的第一句应当直接给出这一段要确立什么，后文提供支撑。

- 弱：`Many scholars have studied absorptive capacity. Cohen and Levinthal (1990) proposed... Zahra and George (2002) extended...`（这是文献罗列）
- 强：`Although absorptive capacity is consistently linked to innovation outcomes, the literature disagrees on whether it operates through knowledge acquisition or knowledge integration.`（这是在建立张力）

方法论文的相关工作章节同理：

- 弱：`Author A (2009) proposes a time-sensitive MF method. Author B (2011) uses tensor factorization. Author C (2019) applies attention mechanisms.`（罗列）
- 强：`These approaches all treat time as an exogenous index, which requires timestamps that are unavailable in most recommendation settings.`（指出方法族的共同局限）

判断标准：将各段第一句连读后，应能识别全文的论证链条。如果这些句子仅构成章节目录式的内容罗列，则主题句没有承担论证功能。

### 衔接词

不要依赖 Moreover / Furthermore / In addition / Besides 的重复使用来推进段落。这些词只表示信息追加，不能说明因果、转折、条件或竞争解释等具体逻辑关系。连续使用时，段落通常仍是并列清单。

有信息量的衔接是指出关系：`This assumption is problematic because...`、`A competing explanation is that...`、`If this mechanism holds, we should also observe...`

`Besides` 在学术英语中偏口语，用 `In addition` 或改写。

### 段落长度

英文期刊正文段落通常包含 4–8 句。中译英稿常出现只有两句的短段，导致论证过度分散；也可能出现整页不分段的长段，增加阅读负担。合并或拆分时以“一段一个论点”为准。

---

## 五、不要过度纠正的地方

以下写法并非错误，不应在缺乏依据时改动：

- **作者自定义的方法名与假设名**。作者定义的研究标识，不应仅因“不符合一般英语表达”而替换。可以提出命名建议（要求：易于记忆、能够提示核心机制、缩写不与既有方法冲突），但相关改动必须标为实质性修改。
- **中国情境的术语**：guanxi、hukou、danwei 等已进入英文文献，首次出现加简短解释即可，不必强行译成英文近义词。中国平台名（Tmall、Taobao、Douyin、Weibo）用官方英文名，首次出现加一句说明规模或性质。
- **中国制度的专有名词**：split-share structure reform（股权分置改革）、Belt and Road Initiative、A-share market 等有约定译法，应采用通行译法，不要自行创造新译名。
- **中文论文正文**。本 skill 不起草或润色中文论文正文，也不声称符合中文期刊文体。中文文本只作为英文写作的语义来源；用户明确要求时可以给高层结构诊断，但输出不得伪装成中文期刊润色稿。
