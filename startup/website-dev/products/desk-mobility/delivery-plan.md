# Desk Mobility 首站交付计划：从验证到英文上线（M0–M7）

> **状态**：候选执行计划；目前不存在已完成的产品代码、临床审核、流量或收款记录。  
> **更新**：2026-10-28 · 来源：康复 Project 创业切入讨论的既有方向 + 本次新增工程拆解。  
> 关联：[产品策略](./product-strategy.md) · [MVP PRD](./mvp-prd.md) · [实验方案](./validation-experiment.md) · [通用开发路线图](../../frontend/development-roadmap.md) · [ADR-001](../../frontend/decisions/ADR-001-astro-多站点架构.md) · [ADR-002](../../frontend/decisions/ADR-002-环境隔离与发布流程.md)。

## 1. 执行顺序（两条轨道并行，少做无效开发）

**轨道 A — 产品/证据**：选择细分用户和首发地区 → 对照替代工具访谈 → 3 版 landing 文案 → 小样本可用性 → 临床审核后的 7 天 Concierge → 真实付费验证 → 决定 Go/Iterate/Stop。

**轨道 B — 工程/SEO**：建立 Astro 项目和 Staging → SSR/SSG 基础与一个体验流程 → 医学安全门禁 → 路由/索引页/SEO 元数据 → 英语可索引内容的专业审阅 → Production release gate → GSC 观测。

**同步原则**：不等 SEO 自然流量出现才测需求，也不等全部功能上线才访谈；但是**无临床审核绝不发布可能造成伤害的动作/诊疗建议**。可以先发布不含个体化指导的产品介绍、非医疗调查、waitlist 与教育内容（同样需要事实核验）。

## 2. M0 → M7 产品专用里程碑

| 通用阶段 | Desk Mobility 必交付 | 不在本阶段做 | 专属 Exit Gate |
|---|---|---|---|
| M0 机会验证 | 细分用户访谈 + 替代产品/SERP 检查 + 3 落地页 + 伦理/安全审查计划 | 3D/AI 诊断/产品平台 | 至少记录实际访谈和招募渠道；安全试验可执行 |
| M1 工程骨架 | 独立代码仓库，Astro/TS/Vue，SEO Layout，staging CI，Access/noindex | D1 CMS、复杂登录 | curl 返回正文、Staging 自动部署 |
| M2 3 分钟 MVP | 目标→安全→基线→审核活动（或纯观察）→即时反馈；两语言少量 PoC 验证路由但仅英文首发 | 相机、肌肉模型、自动处方 | 5–8 人无指导完成；风险退出测试全通过 |
| M3 7 天 MVP + 页面 | 次日入口、D1/D3/D7 记录、最小持久化、报告、首页+2–3 个差异化场景页 | 大规模内容生成 | 真正能恢复 session 并完成 7 天；草稿不索引 |
| M4 首发语言 | 英文核心文案审核，未来语言的路由准备 | 全语种翻译 | 英文内容可读；i18n test route 不公开索引 |
| M5 上线门禁 | 安全/医学专家审阅、数据处理与删除机制、生产域名/密钥、SEO/性能/回滚测试 | 成千页面、自动运营系统 | 安全+隐私+部署 P0 全部有证据 |
| M6 英文小规模上线 | 有帮助的公开页面 + 非索引个人试验区 + GSC/Analytics；受控推广 | 宣称医疗功效 | 真实访问/试用/错误/留存可追踪 |
| M7 按需升级 | 根据留存/费用/需求引入 CMS、更多动作场景、可视化/多语言/多站 | 未验证前的自诊断引擎 | 每次升级都要收益/风险复盘 |

**特例**：实验 7 天记录不必等到正式 M3 开发完成：M0 可通过受控人工实验工具完成，但不要承诺复杂功能已自动化。只有当持续记录对用户明显有价值时，才建设持久化产品功能。

## 3. 首发网站结构与索引策略

### 英文、候选路径（SEO 关键词均待 SERP 研究）

| URL | 主要用户价值 | 是否可索引 | 内容/安全要求 |
|---|---|---|---|
| `/` | 核心定位、限制、体验入口 | 是 | 真实价值主张，不称“治愈颈痛” |
| `/desk-neck-stiffness` | 电脑工作情境下颈部不适的一般解释/照护常识 | 是（专业审核后） | 来源 + 何时停用/求助 |
| `/movement-breaks-at-desk` | 简单工作间歇活动的用途与适用边界 | 是（审核后） | 独立示例与限制 |
| `/seven-day-desk-mobility` | 实验模式、报告样例、明确不是诊断 | 是 | 与其他页面内容真实不同 |
| `/start` | 3 分钟 Web 体验入口 | 入口可公开；私人环节不索引 | 不要暴露个人数据 |
| `/safety` | 安全边界、需要专业帮助的情况 | 是 | 医学审阅和更新 |
| `/evidence` | 文献、制作方法、审阅者和内容更新记录 | 是 | 不使用不存在的资质 |
| `/about`、`/privacy`、`/terms` | 运营者、隐私、服务范围与责任 | 是 | 真实主体/联系与删除流程 |
| `/session/*`、`/report/*` | 私人记录与七天报告 | **不索引 + 访问控制** | 不缓存/不向分析平台泄露 |

仅 1 个正式站和英语一组有效页面。**页面数量不是成功指标**；禁止为了 TR-13 的场景数要求人为复制 YMYL 内容。三种文案的 A/B 实验变体先不索引；成熟后依据各自有价值的内容决定是否做独立 SEO 页面。

**术语/关键词待验证**：desk neck stiffness、movement breaks at desk、neck stiffness after computer work、desk mobility routine。它们只是待调研候选词，未查询搜索量、KD、KGR、SERP 竞争，不应写成已选定的排名目标。

## 4. 工程结构（独立代码仓库，不放 buddy_workspace）

```text
desk-mobility-web/
  src/
    pages/                # index, scenario pages, evidence, safety, start
    layouts/              # SEO Layout
    components/
      marketing/          # SEO-friendly Astro components
      experiment/         # Vue Islands: goal/safety/baseline/activity/feedback
    domain/
      content/            # Page + PageLocalization interfaces
      activities/         # versioned, clinically reviewed whitelist
      experiment/         # feedback/check-in model and eligibility states
      safety/             # deterministic gate, reviewed rules
    repositories/
      content/            # Markdown/JSON first
      sessions/           # only if needed: secure DB adapter
    lib/
      analytics/          # non-sensitive event schema
  content/                # English public copy, metadata, references
  tests/
    e2e/                 # no JS SEO test / safety branching / privacy
    unit/
  public/
  .github/workflows/
  astro.config.mjs
  wrangler.jsonc
```

**技术决定**：[既有 ADR] Astro + TypeScript + Vue Islands + Cloudflare Workers；前期 Markdown/JSON 维护可索引内容；若产品真的要跨天恢复私有 check-in，可对该**小功能**使用 D1（或一个受控研究工具），**这不意味着要建 CMS/多租户后台**。临床活动审核清单应版本化保存，但可公开的只有内容/规则版本摘要，实际用户隐私数据必须严格隔离。

### 推荐的系统边界

```text
Astro public HTML (SEO)
    ├── Landing / content / FAQ / source / safety pages
    └── Vue Experiment Island
           ├── Goal
           ├── Deterministic Safety Gate  ← reviewed rules, no AI bypass
           ├── Baseline
           ├── Approved Activity Registry
           ├── Feedback / Next-day
           └── Private Session Repository ← optional managed persistence
                 └── 7-day report (private, noindex, no public cache)
```

**LLM 在首版没有必要**。未来如果加入，只能用于语言表达或受约束的内容辅助，不能给出疾病诊断、私自修改安全规则、无限生成活动指令。

## 5. 首轮 Backlog：按依赖顺序，可直接开 Issues

| ID | Priority | 实施任务 | 依赖 | Done / 可验证 |
|---|---|---|---|---|
| DM-001 | P0 | 写目标用户 + 关键词/SERP 研究 Brief | 无 | 有渠道、竞品、候选搜索意图与真实数据 |
| DM-002 | P0 | 3 套文案 + 统一 landing flow 原型 | DM-001 | 有可测试的 CTA 与非索引实验变体 |
| DM-003 | P0 | 临床审核人/安全规则/动作名单与内容审阅流程 | 无 | 审核意见、禁忌、退出文案具备签名/日期 |
| DM-004 | P0 | 研究同意、隐私/删除、适用地区审查 | DM-001 | 用户可理解且能撤回，数据访问受控 |
| DM-005 | P0 | 可用性测试 5–8 人、修核心卡点 | DM-002, DM-004 | 完成时间/问题清单与更改记录 |
| DM-006 | P0 | 搭 Astro + Vue / staging CI / noindex | DM-001 | PR build、staging、curl 正文通过 |
| DM-007 | P0 | 实现 Goal / Safety / Baseline / Feedback | DM-003, DM-006 | Yes/Unsure/Worse 退出测试通过 |
| DM-008 | P0 | 审核活动 Registry + 2 分钟展示，或纯观察替代 | DM-003, DM-007 | 未审查活动不可调用 |
| DM-009 | P0 | 7 天 Concierge 招募与人工反馈记录 | DM-003, DM-004, DM-005 | 20–30 人目标，逐人去标识数据 |
| DM-010 | P1 | 7 天 Check-in 会话恢复/报告 | DM-007, DM-009 | 真实逐日记录/报告，用户信息不外泄 |
| DM-011 | P1 | 英文 SEO 内容：3 个差异化页面 + evidence/safety | DM-001, DM-003 | 作者/审阅/参考/原始 HTML 合格 |
| DM-012 | P1 | i18n 测试 PoC（第二 locale 非索引） | DM-006 | locale URL 输出对应语言测试 HTML |
| DM-013 | P0 | 两周实验漏斗与真实付费试验 | DM-009 | 数量/分母/付款/负面反馈/决策 |
| DM-014 | P0 | Prod gate：安全、隐私、SEO、测试、rollback | DM-010, DM-011 | Release checklist 全通过 |
| DM-015 | P1 | 生产小批量发布和 GSC/Analytics | DM-014 | 页面公开正确，可抓取、可跟踪 |
| DM-016 | P2 | 后续迭代：活动适配、3D、更多部位、多语言 | DM-013, DM-015 | 必须另立可测 ROI 和风险假设 |

**并行执行建议**：DM-001/002/003/004/005 的产品验证线可先于 DM-006 启动。DM-003 是所有实际运动指导的阻断依赖，DM-004 是真实用户数据采集的阻断依赖。不要为了快速跑实验跳过安全和隐私。

## 6. 发布与环境

| 环境 | 做什么 | 数据 | SEO |
|---|---|---|---|
| Local | 功能开发、假数据、测试 | 假数据 | 不索引 |
| Staging | 安全退出和端到端流程审核、专家审阅 | 测试/受控试验数据 | Access 保护 + noindex |
| Production | 经审核的英文页面与真实体验 | 单独 secrets/数据库 | 公共页面可索引，私有记录一律不索引 |

GitHub Actions：PR CI → 合并 main 自动 Staging → Staging 检查 → 指定 Git SHA 审批 Production。**敏感数据绝不可在开发与生产之间自动拷贝**，也不应因分析方便把健康数据发往普通 analytics。

## 7. 产品专用上线 Gate（没有证据即待定）

- [ ] **医学**：动作/适应人群/停止条件已由真实合格专业人员审核；风险触发必退出；无诊断或治疗承诺。
- [ ] **隐私**：收集范围、明确同意、数据保留与删除、第三方处理者、访问控制、首发地区合规审查。
- [ ] **真实功能**：3 分钟首访可完成；次日反馈和 7 天报告可复现；所有边界路径有自动化/人工测试。
- [ ] **SEO**：所有公开 HTML 有独特有用内容；sitemap、canonical、robots、正确状态码；所有健康声称可追溯、标作者/审阅；营销文案不夸张。
- [ ] **环境/安全**：Production 无 noindex，Staging 有访问保护；Secrets 不泄露；私人结果不可抓取/缓存/分享。
- [ ] **商业**：如果收款，服务范围、退款、账单/支付处理和用户支持可交付；不要提前销售尚未具备的个体化治疗。

## 8. 明确的后续研究（暂不实现）

1. **身体图/痛点标注**：先研究其是否比文字描述提高了记录质量；不许直接从痛点推断疾病。
2. **活动个体化**：在有足够真实、合规且已审阅的记录与专业依据之后，验证规则化调整是否提高留存和自评功能；不得等同诊断。
3. **3D 肌肉可视化**：作为教育、解释/探索层独立验证用户价值；不绑定 MVP。
4. **动作摄像头检查**：额外的隐私、偏差、可靠性、监管与设备兼容性研究，不能替代临床评估。
5. **更多身体区域**：肩/上背之外的腰、髋等，每增加一个部位需要单独风险和证据审核。
6. **更成熟商业模式**：面向企业福利、B2B/专业转诊、多语言扩张在完成首站验证后再议。

## 9. 如何记录推进状态

建议每次任务报告一行：`ID | Status(todo/doing/blocked/done) | Evidence URL | Verified by | Date | Next action`。**不能因“文档已写”将 M0 或 MVP 写成已通过**。PoC 代码写在另一个仓库，buddy_workspace 只存可公开的设计与去标识复盘。

**下一步默认行动**：先完成 **DM-001（用户问题/关键词与竞品研究）+ DM-002（三套 landing 文案）+ DM-003（临床内容审核安排）**；并行可以启动 DM-006 的 Staging 空骨架，但不开放未经审核的健康指导。
