# buddy_workspace

> 出海建站（独立站 + SEO）的工作区。方法论、架构决策、上线检查标准集中在这里，供人和 agent 共用。
> 最后更新：2026-10-26

---

## 1. 这个仓库是什么

一句话：**把「怎么做出海网站」从读书笔记变成可执行的标准。**

三条写作原则，新增文档时请遵守：

1. **每条标准必须可判定**（通过 / 不通过 / 待定），不写"要注意 SEO"这类无法执行的话。
2. **每条标准必须有出处或验证方法**，能追到原文或能跑一条命令。
3. **区分来源等级**：`[原文]` 有明确出处、`[推断]` 由多条推导、`[工程]` 通用工程常识。三者不混写。

---

## 2. 目录结构

```
buddy_workspace/
├── agent.md                              # 本文件：项目总览与导航
└── startup/
    └── website-dev/                       # 出海建站线
        ├── frontend/                      # 前端技术架构
        │   ├── tech-architecture-spec.md  # 16 条架构约束（TR-01~16），含验证命令
        │   ├── development-roadmap.md     # 首站开发 M0~M7：依赖、顺序、交付物与放行门禁
        │   └── decisions/                # 技术架构决策记录（设计，不代表已上线）
        │       ├── ADR-001-astro-多站点架构.md     # SSG/SSR、Vue、站点/内容分离、TR 评审
        │       └── ADR-002-环境隔离与发布流程.md    # local/staging/prod、域名、CI/CD、回滚
        └── seo-playbook/                  # SEO 方法论与门禁清单
            ├── SKILL.md                   # 8 阶段主清单 + 10 条铁律 + 红线条目
            └── references/
                ├── 01-opportunity-keyword.md        # 立项与选词（KDRoi / KGR / 词龄 / 搜索意图）
                ├── 02-site-architecture.md          # 站点结构与页面策略
                ├── 03-onpage-seo.md                 # 单页优化（TDH / 密度 / 原创 / 行为信号）
                ├── 04-technical-seo.md              # 技术 SEO（渲染 / 收录 / 多语言 / robots）
                ├── 05-links-authority.md            # 内外链
                ├── 06-monetization-ops.md           # 变现与止损
                ├── 07-audit-scorecard.md            # 百分制打分卡 + 诊断树
                ├── 08-sources.md                    # 全部出处 + 数据质量警告
                ├── 09-coverage-audit.md             # 覆盖率审计（读了什么、没读什么）
                ├── 10-infra-payment-compliance.md   # 域名 / 部署 / AdSense / 收款 / 备案
                └── 11-ai-tool-site.md               # AI 工具站专属打法
```

---

## 3. 任务路由：接活前先看这里

| 你要做的事 | 先读 | 关键动作 |
|---|---|---|
| **选技术架构 / 写第一行代码** | `frontend/tech-architecture-spec.md` | 先确认 TR-01/02/03 怎么满足，再选框架 |
| **规划第一个站从零到上线的开发顺序** | `frontend/development-roadmap.md` | 先完成 M0 选词；按 M1~M7 检查任务、出口和证据；i18n PoC 提前、正式翻译在上线前按需做 |
| **评估一个架构方案好不好** | 同上，第 5 节评审问卷 + `frontend/decisions/ADR-001-*` | 按"默认行为是否满足"打分，不按"理论能否实现" |
| **搭建新站或扩成多站** | `frontend/decisions/ADR-001-*` | 共享 Site/Content/Template 协议，按单站规模实现 |
| **设置环境/域名、部署、内容发布或回滚** | `frontend/decisions/ADR-002-*` | 验证环境隔离、发布审批、SEO 防护和回滚 |
| **判断一个关键词值不值得做** | `seo-playbook/references/01` | 算 KDRoi + KGR，看词龄，人工看 SERP 前 10 |
| **规划站点结构 / 页面类型** | `seo-playbook/references/02` | 一个关键词一个域名；页面深度 ≤3；别默认做博客 |
| **准备上线，做放行审核** | `seo-playbook/SKILL.md` + `references/07` | 跑 8 阶段 P0 项，任一红线命中就停 |
| **上线后没流量 / 流量掉了** | `references/07` 诊断树 + `references/04` TS-09 | 先查收录（`site:` + Past hour），再查页面 |
| **AI 工具站怎么做出差异** | `references/11` | 大词拆场景，别用一个通用页接所有需求 |
| **变现 / 收款 / 备案** | `references/10` | AdSense 账号审核与网站审核是两道门，别混为一谈 |

---

## 4. 硬约束速查（违反频率最高的 6 条）

这 6 条是**做错了后面全白费**的类型，写代码和审核时优先对照：

| # | 约束 | 错法 | 一句话判据 |
|---|---|---|---|
| TR-01 | 参与排名的正文必须在服务端 HTML 里 | 纯 CSR、`'use client'` 包整页、`client:only` 渲染正文 | `curl` 抓页面能 grep 到关键词 |
| TR-02 | 多语言必须换 URL，用子目录 | 前端 i18n 运行时切语言 | 点语言切换 URL 变不变 |
| TR-03 | 任意页面 3 次点击可达 | 多层分类目录 | Screaming Frog 的 Crawl Depth > 3 占比为 0 |
| TR-07 | 工具页必须有 ≥200 词说明正文 | 只有一个输入框和按钮 | 禁用 JS 后正文还在不在 |
| TR-11 | 新站首周可访问 URL ≤20 个 | 静态站一次构建全站上线 | 首周 `site:` 收录数 |
| AR-04 | 首页只能输出内页的标题+链接 | 首页模块把内页正文全文渲染出来 | 首页正文词数与核心词密度 |

> **AR-04（首页膨胀）是全套方法论里唯一有完整事故复盘的坑**：首页从 400 词涨到两三千词，核心词密度被稀释、语义跑偏，排名骤降，**且下掉模块后短期没恢复**。任何改动首页的发版，事前记 GSC 基线。

---

## 5. 新增内容放哪里

| 内容类型 | 位置 | 命名 |
|---|---|---|
| 新领域的建站方法论文档 | `startup/website-dev/<领域>/` | `kebab-case.md` |
| 某个站的架构决策记录（ADR） | `startup/website-dev/frontend/decisions/` | `ADR-001-选astro不用next.md` |
| 首站开发执行里程碑、门禁与延后事项 | `startup/website-dev/frontend/development-roadmap.md` | 更新 M0–M7 里程碑/验收；具体站点实施证据放其独立代码仓库 |
| 具体某个站的项目代码 | 另开仓库，不放在这里 | — |
| 上线审核记录 / 复盘 | `startup/website-dev/seo-playbook/reviews/` | `YYYY-MM-DD-域名.md` |

**不要**把这个仓库变成代码仓库。它只放「标准、决策、复盘」，代码在各自的 repo。

---

## 6. 给 agent 的注意事项

1. **不要相信"某框架也能做到"**。判据是默认行为，不是可配置上限。一个 `'use client'` 就能让整页不被收录，而浏览器里看不出来。
2. **阈值分两类**：`[原文]` 的不能动（如 KGR < 0.25），经验线可按自己的数据校准。改阈值时标明依据。
3. **知识库有污染**：`seo-playbook` 的来源是公众号 826 篇文章，其中混入了非原作者内容（已识别 2 篇，见 `references/08` 与 `09`）。引用前先核验：文中出现"我做过 XX 项目""我的社群""github.com/xxx"要反查作者。
4. **覆盖率不完整**：826 篇中约 52% 有索引、23 篇有原文精读。没有依据时**明说没有依据**，不要用通识冒充原文。
5. **时间预期分两轨**：老词一年内进首页的页面仅 5.7%，六成需 61–182 天；新词 2 周进首页、1 个月进前三。别用一套标准套所有词，会误杀或白等。

---

## 7. 变更记录

- **2026-10-26** 新增首站开发路线图 `frontend/development-roadmap.md`：M0–M7 工程里程碑、上线 Gate、多语言按需分期、MVP Sprint，区分 SEO Playbook Phase 0–7。
- **2026-10-26** 新增 ADR-001（Astro 混合渲染与多站架构选型、TR 评审）和 ADR-002（多环境、域名、代码/内容发布、回滚）。两份均为待 PoC 验证的 [工程] 设计，不改变哥飞原始规则。
- **2026-10-26** 初始化。收录前端架构约束规格（16 条 TR）与 SEO 方法论清单（8 阶段 / 23 篇原文精读）。
