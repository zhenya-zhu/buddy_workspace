# axiomatic-design — 公理设计辅助软件架构

- **类型**：外部 Skill（**引用，不是本地安装**）
- **仓库**：[goldengrape/skills](https://github.com/goldengrape/skills)
- **权威入口**：[axiomatic-design/SKILL.md](https://github.com/goldengrape/skills/blob/main/axiomatic-design/SKILL.md)
- **附属资料**：[axiomatic-design/resources/](https://github.com/goldengrape/skills/tree/main/axiomatic-design/resources)

## 何时考虑使用

[原文] 适用于把 PRD / 用户故事转化为低耦合的软件架构，分析已有方案的模块耦合，以及定义清晰接口与契约。

上游核心流程包括：客户需求（CN）→ 功能需求（FR）→ 设计参数（DP）的层级映射；用设计矩阵分析功能独立性与耦合；以函数式编程（FP）和契约式设计（DbC）进一步定义模块与接口。

## 给 Agent 的调用建议

1. **先打开并阅读上游 `SKILL.md` 最新版本**，不要凭这里的摘要执行完整设计。
2. 如果需要正式分析文档或模块规格，继续读取上游 `resources/templates/` 对应模板。
3. 将分析结果落在当前项目目录，并注明真实使用的来源路径与 commit / 版本。

[工程] 这里只放导航和适用性提示，不复制原 Skill；未读到上游材料时不能声称严格遵循它。
