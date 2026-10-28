# MVP PRD：3 分钟 Web Check-in + 7 天 Desk Mobility Experiment

> **状态**：实现规格草案；待访谈与临床审核，不代表产品功能已实现。  
> **2026-10-28** · 基于 [产品定位](./product-strategy.md)、[开发路线图](../../frontend/development-roadmap.md) · 来源标注：[既有讨论] = 康复 Project 2026-09-02/09-24 的可恢复摘要；[新设计] = 当前落地规划。

## 1. MVP 用户旅程

### 首次约 3 分钟核心体验

1. **Choose goal / 选择日常功能目标**：例如“我希望今天在电脑前休息后转头更自如”或“减少工作间不适感”，避免“自测诊断”用语。用户可跳过主观不适量化。
2. **Safety screen / 最小安全检查**：[新设计] 可选择“否/是/不确定”与帮助链接；风险信号/不确定情况**不进入自动动作流程**，转为专业评估/安全信息。严重/突然症状的提示需由临床审核人员定义，用户能直接退出。
3. **Baseline / 功能基线**：0–10 自评舒适度或动作容易程度（精确定义一个量表，不能与医学疼痛量表混用），可选描述“今天最希望改善的一个简单动作/工作情境”。不得要求用户做高风险诱发测试。
4. **Movement / 2 分钟温和活动**：只从**5–8 个经临床审核**的活动库中呈现一个；显示简洁步骤、常见错误、停止条件、时长、无器械替代。若未完成审核，则整个流程替换为非运动的记录体验。
5. **Immediate feedback / 即时反馈**：**Easier / Same / Worse / Unsure**；再问用户是否愿意次日再试一次、是否需要提醒（默认关闭）。
6. **Next-day feedback / 次日反馈**：询问第二天的体验和功能状态，非因果判定；用户可以不做，允许退出。
7. **7-day report / 七天趋势**：显示每天记录、活动完成次数、自评体验、缺失天数、用户自身观察，不写“病因”“疗效”“治愈率”。

整个流程用户可以不输入姓名、出生日期或照片；不应以注册为开始条件。

### 页面与 UI 状态（可用于 Vue component）

```text
landing
  → goal
  → safety_check
     ├── flagged_or_unsure → safety_exit (no movement suggestion)
     └── proceed
           → baseline
           → reviewed_activity
           → immediate_feedback
                ├── Worse → stop_and_safety_guidance
                └── Else → next_day_opt_in
                             → daily_check_in (D1...D7)
                             → seven_day_summary
```

页面 URL 由 Astro 渲染 SEO 文本，只有问答/反馈小组件使用 Vue Island；个人记录在私人/受控的路径里，**不要允许搜索引擎索引个人记录页面**。

## 2. 功能范围与明确排除

| ID | MVP 功能（P0） | 不做（P2+/探索） | 验收 |
|---|---|---|---|
| F01 | 三文案 landing 共用一个体验入口 | 三套互不相干的产品 | 每个入口有 source attribution |
| F02 | 目标 + 最小安全筛查（规则驱动） | AI 疾病分类/症状归因 | 触发信号时不出现活动指令 |
| F03 | 一个自评基线（可跳过） | 视频拍摄、姿态识别 | 记录字段含 timestamp 和量表定义 |
| F04 | 5–8 个专业审核活动库，单次只推荐一个 | 自动动作生成、大规模视频库 | 每条动作有 reviewer、reviewed_at、stop_rule |
| F05 | Easier/Same/Worse/Unsure 即时反馈 | 用即时改善判断肌肉病因 | Worse 进入停止/提示流程 |
| F06 | 可选次日和连续 7 天 check-in | 打卡游戏化强制刺激 | 不反馈也不会自动发送新动作 |
| F07 | 免费第 7 天基础观察报告 | 诊断报告、风险预测、疗效百分比 | 报告仅包含用户记录的事实与自我观察 |
| F08 | 手动 Concierge 后台操作步骤 | CMS、自动处方引擎 | 每次人工调整有审计记录 |
| F09 | 同意/撤回/删除数据说明 | 分享健康信息到公开 SEO 页面 | 用户可无须披露身份退出；支持删除请求 |

**F04 为有条件的 P0**：临床审查未完成时不得运行推荐活动的实验。可以先做 F01、F02（通用警示）、F03、F05（单纯体验记录）、F09 的静态/交互原型验证需求。

## 3. 安全规则（待医学专业人员最终审核）

### 基础原则

- **不自动进行医学诊断、鉴别或处方**；风险信号筛查只决定能否继续通用活动体验，不等于“排除疾病”。
- 对持续、明显加重、突然严重或伴麻木/无力/感觉缺失、显著肿胀/颜色变化、外伤等不确定情况，直接退出活动建议；向用户展示就医建议，紧急情形需清楚提示当地紧急医疗资源。**风险类别、措辞和阈值由执业临床人员审核**。
- 对任何新出现或明显加剧的症状提示停止活动，禁止用“越痛越有效”劝说继续。
- AI/LLM 若未来加入，只可辅助润色或对结构化答案生成易读解释；**不能绕过确定性的 safety gate，也不能自行创建活动**。

### 规则状态示意（不得作为实际医疗审核结果）

| 事件 | 系统行为 | 记录 |
|---|---|---|
| 安全筛查任一风险项 Yes/Unsure | 不展示动作；显示合适的帮助/转诊提示 | safety_exit 及规则版本（尽可能不记录具体敏感症状） |
| 可继续且用户主动选择体验 | 展示一个已审核的活动，明确可随时停止 | activity_id, activity_version |
| 即时反馈 Worse | 终止当前活动并显示安全提示；不继续推荐 | feedback, interrupted |
| 连续失访/未响应 | 不推断效果，不强制提醒 | missing_date |
| 未完成同意/撤回 | 不保留或继续处理识别信息 | consent_version, deletion event |

发布前要求医学审阅者签署：每项活动适用人群、禁忌/停止条件、文字与示范视频、风险提示、基本审计字段。**产品经理和 LLM 不能替代这个审阅**。

## 4. 最小数据模型（先手动/轻量存储，后续再上 D1）

```ts
type Feedback = "easier" | "same" | "worse" | "unsure";

interface ExperimentSession {
  sessionId: string;             // 随机标识，非姓名/邮件
  consentVersion: string;
  campaign: "A" | "B" | "C" | "direct";
  preferredGoal: string;         // 预定义分类，避免不必要的医疗自由文本
  createdAt: string;
  safetyState: "not_checked" | "eligible_for_general_flow" | "exited";
  safetyRuleVersion: string;
}

interface CheckIn {
  sessionId: string;
  dayIndex: number;              // 0..7
  recordedAt: string;
  baselineScore?: number;        // 0..10，自定义问题/方向固定
  activityId?: string;           // 经审核、版本化
  activityVersion?: string;
  feedback?: Feedback;
  nextDayScore?: number;
  completed: boolean;
}

interface ApprovedActivity {
  id: string;
  version: string;
  title: string;
  durationSeconds: number;       // 通常约 120 秒
  steps: string[];
  stopRules: string[];
  reviewerId: string;
  reviewedAt: string;
  isPublished: boolean;
}
```

**数据实施选项**：
- Phase 0 Concierge：可仅在用户知情同意前提下收集最少的表单记录，使用受控私有存储 + 人工回访；禁止把敏感记录提交到公开 Git 仓库。
- 可用性测试：非持久化 demo/本地状态即可，但不可假装已具备跨设备七天追踪功能。
- 进入真实 7 天线上体验：需要能恢复 session 的受控数据存储（例如 D1），或由明确管理的安全实验工具承载；必须有隐私/保留/删除和访问控制。避免把健康问卷放在 Analytics 事件、URL query、共享表格公开链接。

## 5. 状态管理与报告

首次活动必须可单独完成，不能依赖次日返回。用户愿意继续时，使用无需公开账户的安全恢复方式；多设备/邮件提醒是可选功能而非承诺。**唯一访问 token 必须足够随机且避免泄露；私有页面需要防索引、谨慎缓存、禁止将 token 打进 URL Analytics/日志**。

第七天报告（仅非诊断性的描述）：
- 共记录几天，实际进行了几次活动。
- 每天反馈为 Easier/Same/Worse/Unsure 的分布，不出现伪精确“医学改善率”。
- 用户选择的主观功能目标与基线/之后的自评变化，清楚标注未填数据。
- 用户可以下载/删除自己的记录（根据实际能力提供，不做虚假入口）。
- 如出现 Worse/风险提示，报告不能自动把其改写成“已改善”。

## 6. 流量与产品指标 Event Taxonomy

**不向分析平台发送症状详情、自由文本、个人身份或诊断信息**。仅收集非敏感流程转化事件，需获得必要同意并遵守当地适用规则。

| Event | 重要属性 | 用途 |
|---|---|---|
| landing_view | variant, page_slug, locale | 不同文案流量 |
| start_clicked | variant | 点击体验意愿 |
| safety_exited | 无具体风险症状 | 安全流程退出率 |
| baseline_completed | 是否完成（不包含分数） | 体验摩擦 |
| activity_started / activity_finished | approved_activity_id | 完成率 |
| feedback_submitted | 是否已提交（不建议发送具体医疗反馈到第三方 Analytics） | 反馈完成率 |
| next_day_opt_in | yes/no | 次日意愿 |
| checkin_day_completed | day_index | D1/D3/D7 活跃 |
| report_viewed | yes | 7 日闭环 |
| checkout_success | price_variant | 真实付费意愿（需支付集成合法合规） |

**核心漏斗**：Landing → Start → Safety result → Baseline → 2min Activity → Immediate feedback → Next day → ≥5/7 days → Report → Paid upgrade。

## 7. SEO 与路由边界

建议正式公开索引的内容聚焦**有帮助的肩颈日常自我照护信息**，不做疾病诊断结果页：
- `/`：主要价值主张与进入体验的按钮。
- `/desk-neck-stiffness`：电脑工作者颈部僵硬场景解释、停用/就医提示、来源。
- `/movement-breaks-at-desk`：工作间歇活动的用途与限制。
- `/seven-day-desk-mobility`：7 天实验如何运作、记录与报告示例。
- `/about`、`/safety`、`/privacy`、`/terms`：透明度和信任基础；商业展示也不得伪造医学资质。

体验起点 `/start` 可公开访问但对问卷/私人结果部分禁止索引；私有会话/个人报告应认证控制、标记 noindex，并避免 HTML/SSR 缓存暴露身份。三套“仅文案不同”的落地页 **先做非索引实验变体**，不制造相似重复 SEO 页。

内容的医学事实要有来源、作者/临床审阅、发布日期和更新记录。参见：<https://developers.google.com/search/docs/fundamentals/creating-helpful-content>、<https://www.nhs.uk/symptoms/neck-pain-and-stiff-neck/>。

## 8. MVP 交付验收

- [ ] 首次体验在移动与桌面浏览器可独立完成；基于 5–8 位目标用户记录完成时间/卡点，**约 3 分钟是目标不是已达到的事实**。
- [ ] 所有安全终止路径（Yes、Unsure、Worse、未完成筛查）经过测试；未审查活动不可被访问。
- [ ] SSR/SSG 原始 HTML 可读；私人记录在静态抓取、缓存、sitemap、Analytics 中均不泄露。
- [ ] 英文文案清楚、不夸大、可访问；不要发布无资质的临床声称。
- [ ] 次日反馈与七天记录真实能恢复，人工调整有日志。
- [ ] 7 天报告不写病因/疗效；付费实验有真实支付与退款/服务条款准备。
- [ ] 安全内容与活动审阅证据实际存在；在没有合格审核之前不开放活动指导。

**当前状态：全部待验证。**
