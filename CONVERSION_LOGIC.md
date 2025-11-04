# Material Converter - 转换逻辑文档

## 核心原则：KISS (Keep It Simple, Stupid)

在转换 Cycles 材质到 Octane 之前，**先解散所有节点组，将节点树扁平化**。

---

## 转换流程

```
Cycles 材质
    ↓
1. 解散所有节点组（扁平化节点树）
    ↓
2. 转换节点（Image Texture → Octane RGB Image）
    ↓
3. 转换材质（Principled BSDF → Octane Universal/Standard）
    ↓
4. 重建连接
    ↓
Octane 材质
```

---

## 1. 解散节点组（核心步骤）

**文件**: `converter/Shader_node_group.py`

**函数**: `ungroup_all_recursively(mat)`

### 为什么要解散节点组？

- Principled BSDF 和贴图可能藏在节点组里
- 直接处理扁平化的节点树更简单可靠
- 避免复杂的递归追踪和连接映射

### 如何解散？

**手动复制节点**，不依赖 Blender 操作符：

1. **复制节点组内的所有节点**到主材质树
2. **重建内部连接**（节点组内部的连接）
3. **重新连接 Group Input**（外部输入 → 内部节点）
4. **重新连接 Group Output**（内部节点 → 外部输出）
5. **删除节点组节点**

### 迭代处理

- 循环查找并解散节点组，直到没有节点组为止
- 处理嵌套节点组（最多 50 次迭代）

---

## 2. 转换图像节点

**文件**: `converter/convert_images.py`

**函数**: `Convert_image_node(Cycles_Images, mat)`

### 转换映射

```
ShaderNodeTexImage  →  OctaneRGBImage
```

### 属性复制

- 图像文件引用
- 颜色空间（sRGB vs Linear）
- Gamma 值
- 位置和标签

---

## 3. 转换材质节点

**文件**: `octane/convert_active_octane.py`

**函数**:
- `Convert_Universal_Material(cycles_principled, node_tree)`
- `Convert_Standard_Material(cycles_principled, node_tree)`

### 转换映射

```
ShaderNodeBsdfPrincipled  →  OctaneUniversalMaterial / OctaneStandardSurface
```

### 输入映射（Cycles → Octane Universal）

| Cycles Input | Octane Input Index | Octane Input Name |
|--------------|-------------------|-------------------|
| Base Color | 5 | Diffuse |
| Metallic | 7 | Metallic |
| Roughness | 13 | Roughness |
| Specular IOR Level | 10 | Specular |
| IOR | 18 | IOR |
| Alpha | 43 | Opacity |
| Anisotropic | 14 | Anisotropy |
| Anisotropic Rotation | 15 | Anisotropy Rotation |

---

## 4. 重建连接

**文件**: `scripts/rebuild.py`

**函数**: `rebuild_octane_connections(mat)`

### 连接策略

1. **按标签匹配**：如果节点有标签，优先使用标签匹配
2. **按图像名匹配**：对于图像节点，使用图像文件名匹配
3. **按节点名匹配**：最后尝试节点名称匹配

---

## 关键文件结构

```
Material_Converter 1/
├── converter/
│   ├── Shader_node_group.py       # 解散节点组
│   ├── convert_images.py          # 转换图像节点
│   └── ...
├── octane/
│   └── convert_active_octane.py   # 主转换逻辑
└── scripts/
    └── rebuild.py                  # 重建连接
```

---

## 主转换函数入口

**文件**: `octane/convert_active_octane.py` (第 201-211 行)

```python
mat = bpy.context.object.active_material
remove_reroutes_from_material(mat)
label_nodes_from_base_color(mat)

# 关键步骤：先解散所有节点组
from Shader_node_group import ungroup_all_recursively
ungroup_all_recursively(mat)

# 然后进行正常转换
# ... 转换图像节点
# ... 转换材质节点
# ... 重建连接
```

---

## 已废弃的复杂方案

### ❌ 不再使用：递归追踪连接

之前的方案尝试：
- 递归进入节点组查找 Principled BSDF
- 追踪 Group Input/Output 连接
- 跨节点组边界映射连接

**问题**：
- 代码复杂，难以维护
- 容易出现连接错误
- 调试困难

### ✅ 当前方案：先解散再转换

**优势**：
- 简单直接
- 可靠稳定
- 易于理解和维护

---

## 调试技巧

### 查看解散过程

```python
print(f"Iteration {iteration}: Found {len(node_groups)} node groups")
```

### 查看转换结果

```python
print(f"Converted {len(Cycles_principled_nodes)} Principled BSDF nodes")
print(f"Converted {len(Cycles_Images_nodes)} Image Texture nodes")
```

### 检查节点组是否完全解散

```python
node_groups = [node for node in mat.node_tree.nodes if node.bl_idname == "ShaderNodeGroup"]
print(f"Remaining node groups: {len(node_groups)}")  # 应该为 0
```

---

## 常见问题

### Q: 为什么 `bpy.ops.node.group_ungroup()` 不能用？

A: 该操作符需要节点编辑器的 UI 上下文。脚本运行时没有正确的上下文，会报错 "context is incorrect"。

### Q: 手动解散节点组会丢失属性吗？

A: 不会。`copy_node_properties()` 函数会复制所有重要属性：
- 图像引用
- 输入默认值
- 节点特定属性（操作类型、混合模式等）

### Q: 嵌套节点组如何处理？

A: 迭代处理。每次迭代解散一层，重复直到没有节点组为止。

---

## 版本历史

- **Version 6.0 MANUAL**: 手动节点复制，不依赖操作符
- **Version 5.0 SIMPLE**: 尝试使用 `bpy.ops.node.group_ungroup()`（已废弃）
- **Version 4.x**: 复杂的递归追踪方案（已废弃）

---

## 总结

**转换的核心思想**：先简化（解散节点组），再转换（节点和连接）。

这样做的好处：
1. ✅ 代码简单
2. ✅ 逻辑清晰
3. ✅ 易于维护
4. ✅ 不易出错

**记住**：复杂不等于更好，简单才是王道！
