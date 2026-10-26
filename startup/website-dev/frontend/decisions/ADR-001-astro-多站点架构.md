# ADR-001：Astro 混合渲染与多站点 SEO 架构

> **状态**：建议采纳，待首站 PoC 验证（不是已上线的事实）  
> **日期**：2026-10-26  
> **决策类型**：技术架构 [工程]；需求约束来自现有 [原文]/[推断]/[工程] 规格  
> **范围**：先上线一个出海 SEO 网站，将来扩展成复用代码的多网站平台  
> **相关文档**：[TR-01～TR-16 规格](../tech-architecture-spec.md)、[站点架构](../../seo-playbook/references/02-site-architecture.md)、[技术 SEO](../../seo-playbook/references/04-technical-seo.md)、[ADR-002 环境与发布](./ADR-002-环境隔离与发布流程.md)

## 1. 背景与目标

[工程] 先做一个可验证 SEO 流量与商业模式的网站，以后可能复制不同主题、语言、域名和工具站；不在第一个站就建设复杂的通用 SaaS 管理后台。

**核心原则：按平台设计接口，按单站规模实现。**

必须区分：
- **网站运行时**：面向浏览器/Googlebot 输出已发布内容、工具组件与 API。
- **内容/发布控制面**：内容生产、翻译、审核、分批放量、版本管理和数据推送；初期可由脚本与 Git 完成，不需要后台服务。
- **站点配置**：域名、语言、品牌、模板选择与功能开关。
- **环境配置**：local / preview / staging / production 的域名、凭据、数据库和部署目标，详见 ADR-002。

来源追溯：TR-01/02/03/10/14 是规格列出的 L0；TR-04～09/11～13/15/16 影响模板、数据与运营能力。这里的「平台化」和环境隔离是新增 [工程] 决策，不冒充哥飞原文。

## 2. 候选方案及取舍

| 候选 | SEO 正文默认产出 | 动态大规模页面 | 交互区 | 引入成本 / 错误面 | 结论 |
|---|---|---|---|---|---|
| Astro SSG | 构建时生成 HTML | 需要重建/分片 | Islands | 初期低；扩量构建风险 | 小型纯内容站合适，不作为唯一模式 |
| **Astro SSG + 按需 SSR** | 默认预渲染 HTML，动态路由 SSR | 通过数据驱动按需输出 | **Vue Islands** | 低～中，容易保持正文非 CSR | **首选** |
| Nuxt SSR/Hybrid | SSR 可输出完整 HTML | 可扩展 | Vue 原生一体化 | 中；复杂交互应用更合适 | 备选 |
| Next.js App Router | Server Components 可 SSR；Client Components 也可预渲染首屏 | 可扩展 | React | 中；更依赖开发约定避免正文客户端后取 | 备选 |
| Vite + Vue/React 纯 CSR | 默认 HTML 常只有挂载壳 | 服务端渲染需另造 | 强 | 违反 TR-01 默认行为取向 | 不选 |

[工程] **决策**：Astro + TypeScript 作为 HTML/路由层；Vue 3 仅用于需要 hydration 的交互功能；Cloudflare Workers 提供按需 SSR 与 API；Cloudflare CDN 提供分发与缓存。数据存储在 PoC 阶段可用 Git 管理内容；需要无构建发布和海量页面时引入 D1（可替换为 PostgreSQL），上传文件/生成资源按需使用 R2。

不选「所有页面都 SSR」作为硬规则：对稳定内容用 SSG；对动态内容、页面数不可控、首页最新列表用 SSR。可按路由显式选择 `prerender` 或项目 `output` 默认值；**必须在 PoC 中实际验证**。Astro 官方：<https://docs.astro.build/en/guides/on-demand-rendering/>。

## 3. 逻辑架构与模块边界

```text
Users / Googlebot
       |
  CDN + domain
       |
  Site Runtime (Astro on Workers)
       |---- SEO Engine (metadata, canonical, hreflang, sitemap)
       |---- Page Router (host + locale + path)
       |---- Templates (home / tool / scene / article / index)
       |---- Vue Islands (client interaction only)
       |---- Server API (AI proxy, auth, quotas as needed)
       |
  ContentRepository interface
       |---- Git/Markdown adapter (early MVP, optional)
       |---- D1 adapter (dynamic publishing)
       |---- PostgreSQL adapter (future, if justified)

Separate control plane (scripts first, admin services later)
       |---- content generation / QA / translation
       |---- draft -> review -> approved -> published
       |---- cache invalidation / audit log
       |---- deploy and content promotion
```

**依赖方向**：Template -> Page Model -> ContentRepository；模板不直接写数据库 SQL，不读 Cloudflare 特有 binding；SEO Engine 不依赖某个 AI 工具。ContentRepository 的设计降低耦合，但换数据库仍然需要 schema/数据迁移，不能宣称零成本。

### 核心数据模型 [工程]

| 对象 | 最小字段 | 不变量 |
|---|---|---|
| Site | id, domains, default_locale, enabled_locales, config | 站点以稳定 ID 标识，不依赖域名当主键 |
| Page | id, site_id, template_key, status, published_at | 页面 ID 不随标题变化；只允许发布态公开 |
| PageLocalization | page_id, locale, slug, title, description, h1, body | 每个语言版本独立 URL 和元数据 |
| SceneConfiguration | page_id, tool_type, defaults, examples, template_options | 新场景尽量新增数据而非复制模板 |
| Redirect | site_id, old_path, new_path, status_code | slug 变更必须有可追溯的 301 |
| ContentRevision（后续引入） | page_id, revision_id, author, approved_at, content | 内容回滚独立于 Worker 代码回滚 |

**路由解析键**：`Host + Locale + Path -> Site + Published Page + Template`。查询、缓存、sitemap、搜索索引必须使用 site_id 作隔离边界。未发布与未授权预览：公开路由返回 404，不允许仅靠前端隐藏。

SEO 正文、FAQ、案例和内链由 Astro 服务端 HTML 输出；Vue 只接管表单、编辑器、生成器等需要交互的区域。禁止 `client:only` 承载参与排名的正文。

## 4. TR-01～TR-16 逐条评审

判据按原规格第 5/7 节：**默认满足 / 需配置 / 需自研**，不是「理论上能做」。本表的判定对象是**选定的技术栈在实施前的默认状态**，不代表项目已通过验收。

| TR | 方案如何满足 | 默认性 | 成本 | 残留风险 / 验证 |
|---|---|---|---|---|
| **01 正文在 HTML** | Astro SSG/SSR 输出正文 | 默认满足（正确用 .astro 模板） | 低 | 每类页用 curl + 禁用 JS 验证，禁止正文 client:only |
| **02 多语言 URL** | /es/ 等目录 + 独立翻译、canonical、互指 hreflang | 需配置 | 中 | 添加语种后逐语言 curl、元数据和链接校验 |
| **03 ≤3 次点击** | 分类/索引/相关页生成真实 a 链接 | 需自研 | 中 | 5 万页可能链接膨胀，爬全站测深度 |
| 04 TDH 独立 | SEO Engine 按 PageLocalization 生成 | 需自研 | 低 | 唯一性/空值检查 |
| 05 首页最新 + 索引 | 已发布内容查询；SSR 或触发重建 | 需自研 | 低 | 首页/索引缓存过期 |
| 06 首页不输出内页全文 | SummaryLink 与 DetailContent 分离 | 需自研 | 低 | HTML 快照检查列表只含标题/链接 |
| 07 工具页说明 | Astro 工具模板中的正文/FAQ/案例区 | 需自研 | 低 | 验证原始 HTML；按原规格检查 ≥200 词 |
| 08 交互文案不污染 | 功能区与正文语义分区 | 需自研 | 低 | 按规格跑词频报告 |
| 09 URL 稳定 | 稳定 ID + 不随标题变动的 slug + 301 | 需自研 | 中 | 改名后旧链接 301 |
| **10 匹配页面规模** | 低量 SSG，动态数据路由 SSR + 缓存 | 需配置/自研 | 中 | 量级及构建耗时必须实测 |
| 11 分批发布 | status/发布快照过滤 | 需自研 | 低 | sitemap、首页不能泄露草稿 |
| 12 一代码多站 | Site Config + 共享模板 + 每站独立 Worker | 需自研 | 中 | 配置漂移/跨站污染 |
| 13 场景数据化 | SceneConfiguration + 少量可复用交互组件 | 需自研 | 中 | 真正不同 UI 仍需开发组件 |
| **14 服务端密钥** | Workers Secrets + 服务端模型代理 | 需配置/自研 | 中 | 滥用/费用；需认证/限流/配额 |
| 15 根目录静态文件 | 公开资源 + sitemap/robots 动态路由 | 需配置 | 低 | 检查四路径状态码、内容类型 |
| 16 URL 归因指标 | GSC/Analytics 按域名/语言/场景维度 | 需集成 | 中 | GSC 数据延迟且非实时 |

**门禁**：[工程] L0 的「方案可满足」不等于「实现已通过」。进入开发前锁定渲染模式、路由、密钥设计；上线前跑全套自动化验收。TR-03 被原规格列为 L0，但主要属于链接/信息架构，无法靠选框架默认保证；保留其验收要求，不擅自下调原等级。

## 5. 规格第 5 节的六个必答问题

1. **加 1 个语种**：注册 locale，补 PageLocalization 翻译；通用路由、TDH、canonical/hreflang、sitemap 从数据生成。首次需实现 SEO Engine/i18n；之后不应逐页改模板。检测缺译、互指关系和首页 x-default。
2. **100 -> 50,000 页**：不复制 50,000 个模板文件；用 SSR 数据路由 + 分片 sitemap + CDN 缓存。无需重写框架，但容量、吞吐、数据库索引与账单须重新验证。**构建耗时无实测，不能写具体分钟数**；建立 1k/10k/50k 样本 CI 基准（构建时长、产物大小、P50/P95 TTFB、缓存命中率）。
3. **首周仅上线 15/515 页**：公开查询、首页、索引、sitemap 全部只读取 published；其余 500 保持 draft，公开 URL 返回 404。Git-MVP 用发布清单过滤构建；DB 模式按状态发布，不需重建。
4. **最新内容生效**：SSG 触发首页/索引重建；SSR 直接查询已发布数据，更新由 TTL/缓存失效决定。目标可设置如 60s，但必须在 Cloudflare 配置实测，不能保证写库即刻全网可见。
5. **加 1 个 AI 场景**：相同工具类型新增 1 条配置及对应独立内容/示例；不同交互能力则新增/扩展通用 Vue 组件。不能承诺所有场景都零代码。
6. **第 2 个站**：复用基础设施、SEO Engine、模板、发布工作流和工具组件；新增 site config、域名、数据集、独立 Worker/Secrets/DB binding。先一代码库多部署，而不是第一天就实现共享 Worker 动态多租户。

## 6. 部署组织与分阶段实现

[工程] **本仓库只存标准/ADR，不存网站代码**（遵循 `agent.md`）。实际网站代码建议独立仓库（或未来平台 Monorepo），统一模块化管理；第一个站无需多 app 复制。

**MVP / Site A**：Astro + Vue + TypeScript，Cloudflare Workers（静态内容可 SSG），可选 Git Markdown 内容，统一站点配置/SEO 模板/CI 验证/预发布环境；如需动态内容和在线发布，则一开始引入 D1 与 SSR。

**Growth / Site B,C**：共享模板、ContentRepository、SEO Engine；按 site_id 与 environment 生成不同部署，内容和 Secrets 隔离；补翻译、场景配置、内容审核；若复杂 UGC/高并发写入再评估 PostgreSQL。

**Platform**：经实测后增加统一内容后台、任务队列、批量翻译/生成、版本化审核、租户权限；不要预先上微服务。

## 7. 本次工程判断与原方法论的边界

- [原文] 原规格主张正文在 HTML、多语种独立 URL、点击深度、工具说明、关键词词频/密度、首周发布限制；本 ADR **不修改原始规范**。
- [工程] Google **可以渲染 JavaScript**，但让重要正文进入原始 HTML 仍能降低抓取/渲染失败风险。不能把「Next.js 出现 use client」等同于绝对无法收录。官方：<https://developers.google.com/search/docs/fundamentals/how-search-works>。
- [工程] 「至少 200 词」「关键词密度 ≥1%」「新站首周 ≤20 页」是方法论上的运营/内容阈值，**并非已证实的 Google 算法硬性阈值**。在原规格未修订前用于内部审查，遇到冲突应单独记录评审而非偷偷改变标准。
- [工程] 批量页面必须有独立功能价值/场景价值，不能以复制模板 + 换标题进行无价值规模化；Google 的 scaled content abuse 政策：<https://developers.google.com/search/docs/essentials/spam-policies>。
- [工程] Astro 也不是免配置：服务端域名、动态 SSR、hreflang、缓存、安全、内容审核都需要明确实现及自动化验收。

## 8. 放行检查与待验证事项

| ID | 可判定验收项 | 当前状态 |
|---|---|---|
| A01 | 每类页 curl 原始 HTML 包含正文与 H1；禁 JS 内容保留 | 待验证 |
| A02 | /es/ 等有真实语言 HTML，互指 hreflang/canonical 正确 | 待验证 |
| A03 | 全站爬取，Crawl Depth >3 占比 = 0（按当前规格） | 待验证 |
| A04 | 修改标题不改 slug；改 slug 有 301 | 待验证 |
| A05 | draft 不出现在页面、最新列表、索引与 sitemap | 待验证 |
| A06 | 首页列表只有标题+链接，工具页说明内容不依赖 JS | 待验证 |
| A07 | AI Key 不在客户端 bundle，API 有限流/配额 | 待验证 |
| A08 | 1k/10k/50k 页测量 build、P95 TTFB、缓存命中率、部署成本 | 待验证 |
| A09 | 新站/新语种/新场景记录变更文件数与上线步骤 | 待验证 |
| A10 | staging/production SEO、数据库、密钥、回滚门禁通过 ADR-002 | 待验证 |

**结论**：推荐以 Astro 混合渲染构建首站、共享数据与模板协议支撑未来多站。最终「通过」必须基于 PoC 和验收结果，而不是架构口头承诺。
