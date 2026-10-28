# 出海 SEO 首站开发路线图：从 MVP 到多站平台（M0–M7）

> **状态**：推荐实施顺序，未开始执行；每阶段的“通过”必须附实际证据。  
> **日期**：2026-10-26  
> **来源等级**：本文的开发排序、部署策略、分期范围均为 **[工程]** 判断；既有 SEO 检查项引用原规格（其来源等级沿用原文件），不改写为 Google 官方要求。  
> **范围**：先做一个出海 SEO 站点验证需求、流量和商业模式，后续有真实需求再扩成多站平台。  
> **依赖**：[技术架构约束 TR-01～16](./tech-architecture-spec.md) · [ADR-001 Astro 多站架构](./decisions/ADR-001-astro-多站点架构.md) · [ADR-002 环境/发布](./decisions/ADR-002-环境隔离与发布流程.md) · [SEO Playbook（Phase 0～7）](../seo-playbook/SKILL.md)

> **具体项目落地**：康复创业首站 Desk Mobility 已按本路线图拆解为产品定位、[MVP PRD](../products/desk-mobility/mvp-prd.md)、[两周用户验证](../products/desk-mobility/validation-experiment.md)与 [DM-001～016 执行任务](../products/desk-mobility/delivery-plan.md)。通用路线图适用于各站；具体项目的医学审核与隐私门禁优先于开发进度。

## 一句话原则

**早确定不可逆的边界，晚开发昂贵的能力；先有一个可用、可抓取、可部署的核心页面，再增加内容与语言，最后经过发布门禁上线。**

本路线图的 `M0–M7` 是**工程交付里程碑**，**不是** SEO Playbook 的 `Phase 0–7`（后者按选词、站点策略、页面优化、技术 SEO、链接与变现组织）。两套阶段相互配合，不可替代。**M0 的市场判断未通过，不能因为工程准备好了就进入建设。**

## 1. 八阶段总览与门禁

| 阶段 | 目标 | 本阶段最小范围 | 可判定出口 / 证据 | 与 SEO Playbook 关系 |
|---|---|---|---|---|
| **M0 需求与关键词验证** | 确认第一个站做什么 | 主关键词、搜索意图、SERP、竞争差异、首批页面清单 | 一页 Brief；人工 SERP 检查；有清楚的目标用户与差异化价值 | Phase 0–2 |
| **M1 工程骨架和 Staging** | 建立“提交→预发布”的最小闭环 | Astro/TS、按需 Vue、Site Config、SEO Layout、GitHub CI、Cloudflare Staging | PR 能 build；main 合并部署 staging；原始 HTML 有正文；staging 不可公开索引 | TR-01/04/14 基线、ADR-001/002 |
| **M2 单页面端到端 MVP** | 核心工具/内容真的可用 | 首页 + 一个核心页 + 必要 API/错误处理；用两个 locale 的**少量测试页**验证路由 | 主流程可用；curl/无 JS 有正文；不同 locale 各自 HTML/URL；密钥不泄露 | TR-01/02/07/14 |
| **M3 页面模板和首批内容** | 能低成本新增高质量场景页 | 模板/数据化、稳定 slug、published 状态、首页最新列表、索引和内链 | 新增同类场景主要改数据；draft 返回 404；抓取深度/元数据检测 | Phase 2–3，TR-03/05/06/09/11/13 |
| **M4 首发多语言内容完善** | 只有确定首发要多语时补齐翻译 | 独立翻译、slug、TDH、canonical/hreflang、语言 sitemap、语言切换 | 每个已发布语言 URL 返回对应语言 HTML；无空壳和假翻译 | Phase 3–4，TR-02/04/15 |
| **M5 上线门禁与生产发布能力** | 安全、可控地发布正式域名 | Production Worker/Secrets、正式域名、SEO 审核、性能、回滚演练、GSC 准备 | QA 报告全部 P0 通过；能部署指定 SHA 并回滚；正式环境无 noindex | Phase 3–4、Phase 7 基建 |
| **M6 首批正式上线及观测** | 用真实搜索/用户反馈验证 | 首批已审核页面发布、GSC/Analytics、错误/成本监控 | 真实 URL 正常；可抓取；已提交 sitemap；记录初始指标与发布记录 | Phase 4–6 |
| **M7 迭代与平台化** | 用数据判断要扩哪一层 | 按触发条件上 D1、SSR 扩容、CMS、多站、队列 | 每项扩容有容量/效率/成本指标和前后对比 | Phase 5–7、TR-10/12/16 |

**阶段推进**：每个 M 阶段交付物必须标注 `通过/不通过/待定`、验证时间、证据（URL、CI run、报告或截图），缺证据一律待定。研发可以并行做小项，但**不能跳过 M5 的 Production 发布门禁**。

## 2. 哪些决策必须提前、哪些延后

| 时间点 | 现在固定/预留接口 | 不要提前实现 |
|---|---|---|
| **M0–M1** | SEO 主关键词、主要页面类型、稳定 slug 规则、`SiteConfig`、环境配置、Astro SSG/SSR 边界、`SEO Layout` | CMS、多租户后台、付费系统、复杂推荐/分析 |
| **M1–M2** | `Page`/`PageLocalization` 数据结构、独立语言 URL、正文服务端输出、Git 测试发布 | 全语种翻译、数据库驱动发布、数万页压测 |
| **M2–M3** | 场景模型、模板复用、draft/published、URL 301、首页/索引内链结构 | 内容生成流水线、全自动翻译、批量建站后台 |
| **M4–M5** | 首发需要的语言和翻译、hreflang、sitemap、正式站域名、独立生产凭据、回滚预案 | 所有潜在语言、复杂 A/B 实验 |
| **M6 之后** | 基于真实抓取、搜索与转化数据迭代 | 仅因为“未来可能有 100 个站”而预建基础设施 |

**特别区分：多语言的设计要早做，完整内容的翻译可以晚做。** 首站若只运营英语，则 M4 只做 i18n 就绪检查，不强制发布日语/西语页；未来有真实需求再开放这些语言。未翻译的语言不要生成可索引的空页面或英文拷贝。

## 3. 各阶段执行清单

### M0 — 需求/关键词验证（尚未写代码）

- [ ] 选定一个核心需求及主要目标市场、首发语言；记录核心词与 3–5 个有差异化价值的场景候选。
- [ ] 用 SEO Playbook `01-opportunity-keyword` 完成关键词评估与人工 SERP 前 10 检查；阅读 `02-site-architecture` 确定首页定位、场景页分工、首批内容。
- [ ] 确认用户实际操作流程和差异化价值，写出可测试的“最小可用功能”。
- [ ] 明确潜在成本/依赖（如模型 API、付费额度、版权、用户文件保留）。
- [ ] 输出 `site-brief.md`：目标用户、关键词、页面地图、主要场景、首发语言、核心成功指标、暂不做什么。

**Gate M0**：可以一句话说明“用户为什么来，而不是去已有网站”；首批页面不是只换关键词/标题的同质模板。若不成立，回到选词与定位，不进入 M1。

### M1 — Astro 工程骨架 + Staging

- [ ] 在**独立的网站代码仓库**建立 Astro + TypeScript；Vue 只在交互组件需要时引入。本 `buddy_workspace` 仍只放标准/决策/复盘。
- [ ] 建立 `SiteConfig`（站点 ID、生产/预发布域名、默认语言、启用语言列表）和 `EnvironmentConfig`；**避免组件硬编码域名**。
- [ ] 建立公共 `SEO Layout`，接收 title、description、canonical、H1；先放一个服务器输出的示例正文页。
- [ ] 先使用 Git 中 Markdown/JSON/TS 内容；数据对象至少保留 `id`、`slug`、`locale`、`status` 和 `templateKey`。初期不需要 D1。
- [ ] GitHub PR 跑 lint/typecheck/build；main 合并后自动部署到 Cloudflare Staging。
- [ ] Staging 与 Preview 受 Cloudflare Access 保护（或等效认证），并加 `X-Robots-Tag: noindex`；用测试域名，不向 GSC 提交 Staging。
- [ ] 建立一条真实的 `curl` HTML smoke test，确保不会交付空的 CSR 壳。

**Gate M1**：一次 PR 合并成功触发 Staging 更新；能拿到带完整 HTML 的测试页；Staging 不被匿名访客直接当正式站使用。证据：CI 链接、Staging 地址、HTTP 结果。

### M2 — 一个可用的核心页面 + 最小 i18n PoC

- [ ] 交付真正可用的核心功能或内容（包含至少一种真实用户输入→结果的路径）；失败/空输入也有响应。
- [ ] 首页和核心工具/内容页 SEO 正文由 Astro 生成；Vue Island 只处理交互区；禁用 JS 后仍能看到正文。
- [ ] 若使用 AI/外部 API：只从 Worker 服务端调用，凭据放 Secrets；加最基本的限流、额度/成本上限和错误处理。
- [ ] 验证路径约定：默认语言（如 `/`、`/tool`）和第二语言 PoC（如 `/ja/`、`/ja/tool`）。PoC 可用少量真实测试翻译，**不对外索引**。
- [ ] 确认 locale 与 page ID 分开，语言切换改变 URL，服务端直出对应语言 HTML；为未来 hreflang/sitemap 留出共享接口。

**Gate M2**：核心场景可用；`curl -sL "$STAGING_URL/tool"` 能在 HTML 找到工具说明与 H1；另一 locale 页面不是 JS 动态替换英语；API Key 不在前端产物。

### M3 — 首批页面、模板、内链、发布状态

- [ ] 通过数据驱动的 `HomePage`、`ToolPage`、`ScenePage`、`IndexPage` 模板渲染；同类型场景只增加配置/内容，不复制一份页面文件。
- [ ] 首页最新内容只输出**标题 + 真正的链接**，不把详情正文、FAQ 整块输出到首页。
- [ ] 页面具有稳定 ID 和 slug；改标题不自动改 URL；需要变更 URL 时使用 301。
- [ ] 实现 `draft`/`published`：draft 不在公开路由、首页、索引、sitemap 暴露；需要预览时走受认证的单独入口。
- [ ] 首批每个场景有具体功能差异、默认参数、案例和有用正文，避免只改 TDH 的“换皮页”。
- [ ] 从首页、分类/索引、相关页面建设真实 `<a href>` 内链；按原规格爬取检测点击深度。
- [ ] 检查 Title、Description、H1 唯一性，首页内容污染以及工具说明区。遵循 TR 的原方法论阈值；遇到与搜索引擎官方标准不一致时单独记录评审。

**Gate M3**：至少一个新场景通过数据配置创建；draft 公开访问 404；全站爬取报告、TDH 去重报告、首页 HTML 快照符合约束。不要用 `site:` 收录量代替“已公开 URL 数量”的测试。

### M4 — 上线前补齐首发多语言（有条件阶段）

**必须区分**：技术 i18n 已在 M1/M2 设计并用 PoC 验证；这里只补齐**确定首发上线**的语言，而非一次性把所有语言做全。

- [ ] 为每种首发语言提供独立、经检查的标题/描述/H1/正文/FAQ；链接到对应语言页面。
- [ ] 固定每种语言的实际可访问 URL/slug，优先使用子目录（`/ja/`、`/es/`）而非无 URL 的前端切换。
- [ ] 对**真实存在且已公开的译文**生成互指 hreflang 与自引用 canonical；`x-default` 仅在适当的默认/语言选择页上使用。
- [ ] 语言版本加入生产 sitemap，严格过滤 draft、测试版和不存在的翻译。
- [ ] 实测直接请求 `/ja/tool` 返回日文 HTML，而不是英文空壳加 JS 翻译；切换语言保留用户意图对应的页面。

**Gate M4**：没有可索引的假翻译、空 locale 或错误互指；每种首发语言的核心页在禁 JS 状态下可阅读。如果首发仅英语，明确记录 `其它 locale 暂不发布`，然后进入 M5。

### M5 — Release Gate：正式上线准备

- [ ] 按 ADR-002 新建 Production Worker、生产域名、Secrets、独立数据绑定（若已采用 D1/R2）；Staging 与 Production 不共享测试数据和 AI 配额。
- [ ] Staging 验收后用**指定 Git SHA**执行 Production 部署；GitHub Environment 审批，记录 release ID。生产变更后运行 smoke tests。
- [ ] SEO 技术检查：原始 HTML、TDH、canonical、hreflang（若有多语言）、状态码、robots、sitemap、301、无孤岛/草稿泄露。
- [ ] **负向环境测试**：Staging/Preview 受访问控制且 noindex；Production 不得意外 noindex、不得把 canonical 指向 staging。
- [ ] 核心功能、边界错误、安全与依赖检查；关键交互可在手机浏览器中正常完成。
- [ ] 测试移动端体验、响应时间、缓存行为；制定可检验的项目阈值，不伪造性能数据。
- [ ] 演练 Worker **代码回滚**。如果有数据库与动态发布，还要分别演练**内容修订回滚**和兼容性 schema migration；三者不能混为一谈。
- [ ] 准备 Google Search Console、正式 sitemap、基础 Analytics、错误监控、必要的隐私/条款页面；若拟做 AdSense/收款，再走 SEO Playbook Phase 7 的对应检查。

**Gate M5**：技术规格中所有适用 L0 和上线 P0 均通过；有 CI/HTTP/检查报告证明；重大未通过项不放行。纯设计上的“可以做到”不算通过。

### M6 — 小批量生产发布与观测

- [ ] 按经审核的清单公开首批页面（可遵循原 Playbook 的**新站首周 ≤20 个 URL**运营策略；这是**该方法论的阈值，不是 Google 官方通用门槛**）。
- [ ] 使用站点自身发布清单、公开路由和 sitemap 核对可访问 URL 数；`site:` 结果反映收录估计，不等于实际上线数量。
- [ ] 正式域名 HTTPS、canonical、robots、sitemap、主要语言页面和首页互链运行正常；向 GSC 提交正式 sitemap。
- [ ] 按 URL/语言/场景记录曝光、点击、索引状态、错误、页面体验、转化和 API 成本；留好上线基线与版本记录。
- [ ] 内容质量、需求满足度优先于“冲页面数”；按真实数据增补场景和内容，勿因短期没收录就盲目批量发布。

**Gate M6**：发布版本可追溯；核心站可访问、可抓取且可监测；发布页面清单与实际可访问页面一致。**不把获得 Google 收录/排名当作部署成功的即时保证。**

### M7 — 由真实需求驱动扩容/平台化

| 观察到的触发条件（示例，不是固定阈值） | 允许增加的能力 | 决策前必须量化 |
|---|---|---|
| 内容发布越来越频繁，Git 部署拖慢迭代 | D1 + 内容独立发布 + ContentRevision | 发布耗时、编辑频率、迁移成本 |
| 页面量、构建时间/产物大小明显增加 | 把数据化内容迁向 SSR + CDN 缓存 + 分片 sitemap | 1k/10k/50k build、P95 TTFB、缓存命中率、成本 |
| 准备第二、第三个独立域名 | 共享 packages、Site Config、每站独立 Worker/域名/Secrets | 新站初始化步骤、共享代码比例、隔离测试 |
| 需要多人编辑/审批翻译 | CMS + RBAC + 工作流 | 手工审核耗时、误发布率 |
| AI 生成耗时长或 UGC 规模增长 | 后台队列、R2、任务状态/限额、专用数据存储 | 任务分布、并发、成本、滥用风险 |
| 需要统一管理许多站点 | 发布控制平面/跨站指标平台 | 站点数、运维工时、单站故障影响范围 |

**Gate M7**：每项扩容先建立基线和明确目标；升级后用真实数据证明性能/效率/风险收益，否则维持简单架构。

## 4. 发布工作流与里程碑关系

```text
M0 Brief approved
      |
M1 create code repo -> PR -> CI -> staging auto-deploy
      |
M2 real core page + 2-locale route PoC
      |
M3 data-driven pages + stable slug + draft/published
      |
M4 launch-locale translations (optional for English-only launch)
      |
M5 SEO/quality/security tests -> approval -> production deploy
      |
M6 limited release -> GSC/Analytics feedback
      |
M7 measured improvements, possible platform expansion
```

**在 M1–M4，原则上只部署 Staging，不需要公开 Production 站。** 正式域名和正式发布机制可在 M5 完成；如需提前购买域名或验证 DNS/TLS，可以先完成配置但不要让半成品被索引。

**代码与内容发布**：
- **初期**：内容在 Git，PR 审核通过以后随 Astro 构建部署；`draft/published` 过滤实际公开页面。此时“内容发布”仍依赖部署，简单可控。
- **后期**：当内容更新频率需要脱离代码时，再引入数据库、审核后的 `ContentRevision`、单独的 Publish 操作与缓存失效。不可宣称已有独立发布功能。

## 5. 关键验收自动化（建议，不是仓库当前已有脚本）

这些只是**拟实现的测试行为**；仓库尚无可执行的网站代码，不应写成已经启用的 CI 检查。

| Gate | 自动化/人工核验 | 对应 TR / ADR |
|---|---|---|
| 原始 HTML | 对每类模板 GET 原始响应并检查 title、H1、关键正文；禁用 JS 复验 | TR-01/04/07 |
| 多语言 | 请求默认语言和非默认语言，核对实际语言、URL、canonical、hreflang | TR-02 |
| 内链 | 全站 crawler 检查深度和孤岛；按原 TR-03 严格门槛报告 | TR-03 |
| 首页 | 最新列表只输出标题和链接；不包含详情正文或长 FAQ | TR-05/06/08 |
| 发布状态 | 公开 URL/draft、索引、sitemap、最新列表一致；未发布返回 404 | TR-05/11/15 |
| 场景/slug | 新场景通过配置生成；改标题不改 URL；旧 slug 301 | TR-09/13 |
| API | 客户端构建物不包含密钥；无未授权调用和显著滥用风险 | TR-14 |
| 环境 | Staging Access+noindex；Production 无 noindex；URL/Secrets/data 不串 | ADR-002 DEP-02～05 |
| 发布 | 指定 SHA 才可发布生产；smoke tests；Worker rollback 演练 | ADR-002 DEP-06～09 |
| 可观测性 | GSC 记录按语言/页面归因；性能/错误/成本有基线 | TR-16 |

## 6. 推荐的第一轮 Sprint：只做最小闭环

**目标**：一个域名方向 + 一套 Astro 工程 + 一个可用核心页面 + 一条 Staging 发布流水线。无需数据库、CMS、多站平台、所有译文和生产正式上线。

- [ ] `S1-01` 完成 `site-brief.md`（M0；SEO 选词与首批页面）。
- [ ] `S1-02` 新建独立代码 repo，初始化 Astro/TS，按需集成 Vue（M1）。
- [ ] `S1-03` 定义 `SiteConfig`、`Page`、`PageLocalization`、`SEO Layout`（M1）。
- [ ] `S1-04` GitHub PR CI + Cloudflare Staging + Access/noindex（M1）。
- [ ] `S1-05` 一个真正可用的核心页面，服务器输出 SEO 正文（M2）。
- [ ] `S1-06` 仅两种语言的少量测试数据，验证语言路径及服务端 HTML（M2）。
- [ ] `S1-07` 写出 5 个真实 smoke tests 与截图/CI 证据（M2）。

Sprint 验收：**在 staging 实测“修改代码→PR/CI→合并→部署→访问页面”，并证明核心页可用且非 CSR 空壳**。如无法通过，先修基础，不跳到批量生成页面。

## 7. 对后续 Agent 的交接约定

每次新任务先说明：当前里程碑（M0–M7）、本次最小变更、依赖的 TR/ADR、验收方式、实际证据。不要因为路线图列出未来功能，就在 M1 把所有模块实现。

建议用独立进度记录：`Milestone | 状态（未开始/进行中/通过/阻塞） | 证据链接 | 日期 | 下一个阻塞项`；没有 CI 或 HTTP 证据不得写“通过”。

**附注**：原 SEO 文档的关键词密度、说明词数、首周页面限制是**内部方法论规则**，不应与 Google 官方技术要求混为一谈。本路线图不擅自调整原文来源等级或门禁，遇到争议请建立单独评审记录。
