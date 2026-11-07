# crash-course-learning-okf-factory — 课程学习 OKF 工厂

- **类型**：外部 OKF bundle / 方法论工厂（**引用，不是已安装的单文件 Skill**）
- **仓库**：[goldengrape/skills](https://github.com/goldengrape/skills)
- **权威入口**：[crash-course-learning-okf-factory/index.md](https://github.com/goldengrape/skills/blob/main/crash-course-learning-okf-factory/index.md)
- **关键步骤**：[课程实例生成 playbook](https://github.com/goldengrape/skills/blob/main/crash-course-learning-okf-factory/playbooks/generate-new-course-okf.md)
- **其他资料**：[docs](https://github.com/goldengrape/skills/tree/main/crash-course-learning-okf-factory/docs) · [schemas](https://github.com/goldengrape/skills/tree/main/crash-course-learning-okf-factory/schemas) · [templates](https://github.com/goldengrape/skills/tree/main/crash-course-learning-okf-factory/templates)

## 何时考虑使用

[原文] 根据课程名称、学习者基础、考试限制、可用材料与时间预算，创建一套**有状态**的课程学习文件：日计划、测验、错题与误解、复习卡片、学习记录、后续调整，以及可恢复的下一次学习会话。

上游主要面向短期备考（例如一周、每天约一小时）；扩展到长期学习需明确重新设计节奏与评估目标，不宜直接照搬。

## 给 Agent 的调用建议

1. **先读上游 `index.md`**，再根据任务进入对应的 `docs/`、`playbooks/`、`schemas/`、`templates/`。
2. 要生成课程，阅读生成契约和主 playbook；要续学，阅读恢复会话与状态更新 playbook。
3. 不要把索引当成已经持久化的学习状态。真正生成的课程实例及其学习状态，应保存在约定的成果目录，并在下次会话重新读取。
4. 若要运行上游本地工具，先检查依赖与安全边界；本索引不自动安装或执行任何脚本。

[工程] 本卡片为导航，不复制 OKF factory 的内容文件。
