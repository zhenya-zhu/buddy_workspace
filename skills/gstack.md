# gstack — 创业与工程 Agent 工作流

- **类型**：外部 Agent 工作流 / Skill 套件（**引用，不是本地安装**）
- **作者 / 仓库**：[garrytan/gstack](https://github.com/garrytan/gstack)
- **上游入口**：[README.md](https://github.com/garrytan/gstack/blob/main/README.md) · [SKILL.md](https://github.com/garrytan/gstack/blob/main/SKILL.md)
- **宿主与安装说明**：[docs/hosts.md](https://github.com/garrytan/gstack/blob/main/docs/hosts.md) · [docs/install.md](https://github.com/garrytan/gstack/blob/main/docs/install.md)

## 何时考虑使用

[原文] gstack 将产品方向思考、架构审查、设计、代码审查、QA、安全与交付等组织成面向不同职责的 AI 工作流。适合创业者、技术负责人及 AI 辅助的软件交付任务。

**触发例子**：创业想法审视、产品范围收敛、设计/工程方案评审、开发后 review、端到端 QA、发布准备。

## 给 Agent 的调用建议

1. 先读上游 README，找到当前任务对应的命令或角色；不要假定所有命令均适合当前场景。
2. 需要深入执行时，再读对应上游 `SKILL.md` / 子目录及其依赖文件。
3. 如果是 Claude Code、Codex CLI 或其他宿主，按上游最新 `docs/hosts.md` 核对兼容性与安装方式。**仅引用本卡片不会安装任何命令**。
4. 涉及执行脚本、浏览器控制、发布或代码修改时，遵循当前用户授权及环境安全限制。

[工程] 本卡片仅负责资源发现，不同步复制 gstack 的代码和 Skill 正文。
