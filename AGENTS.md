# AGENTS.md — 标准化开发与自动化验证契约


## 1. 核心架构红线（Hard Boundaries）
本项目必须严格保持 **纯逻辑决策层** 与 **宿主执行层（Blender API）** 的单向解耦：
- `core/`（纯 Python 逻辑层）：存放贴图正则匹配、节点类型/Socket 映射规则、图转换规划算法。**严禁**在 `core/` 下的任何文件中导入 `bpy`、`mathutils`、`bmesh` 或 `executor/`。
- `executor/` & `ui_panel.py` & `__init__.py`（宿主执行层）：仅负责读取 Blender 场景数据序列化为字典，以及按 `core/` 生成的指令创建节点与连线。严禁在此层堆砌复杂的业务判断。
- 路径操作统一使用标准库 `pathlib.Path`，确保跨平台（macOS / Windows）兼容。


## 2. 领域避坑红线（Octane Render 限制）
- **禁止无头端到端 Octane 测试**：Octane for Blender 在 `blender --background` 模式下无法初始化 GPU 上下文，严禁编写启动无头 Blender 实例化 `OctaneUniversalMaterial` 的测试。
- **已知节点限制拦截**：`OctaneCyclesNodeMathNodeWrapper` 等不支持纹理域评估的节点必须在 `core/` 的映射规则中显式处理或警告，禁止静默失败。


## 3. 工作流标准（SOP）
1. **先规划后动手**：接到任何新需求或重构任务时，必须先输出修改计划（涉及文件、接口变更、测试点），获得用户确认后再修改代码。
2. **测试先行与闭环验证**：
   - 修改 `core/` 下任何逻辑时，**必须**同步在 `tests/` 中新增或更新对应的 `pytest` 单元测试。
   - 每次修改 `.py` 文件后，必须主动执行 `python -m pytest -v` 和 `ruff check .`。
   - 若测试或 Lint 报错，必须立刻自行修复直至全部通过（退出码为 0），严禁跳过测试直接交付。
3. **代码风格**：遵循 PEP 8，类型注解清晰，包内统一使用显式相对导入。
