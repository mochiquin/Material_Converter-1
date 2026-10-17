# Material Converter for Blender

<div align="center">

**A Blender addon that converts Cycles materials to Octane, V-Ray, and LuxCore**

[![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange.svg)](https://www.blender.org/)
[![Version](https://img.shields.io/badge/version-1.0.8-blue.svg)](https://github.com/mochiquin/Material_Converter-1)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)

</div>

---

## 📖 Overview

Material Converter walks a Cycles material's node tree and rebuilds it as a native
material for another render engine. It ungroups node groups, labels nodes based on
what they feed into, converts each recognized node type to its engine-specific
equivalent, and reconnects everything using that labeling.

This fork focuses on the **Octane** conversion path - that's the part getting active
development and testing. V-Ray and LuxCore support exists in the codebase but hasn't
been touched or re-verified here.

### ✨ Key Features

- 🔄 **Cycles → Octane / V-Ray / LuxCore**: one-directional conversion from a Cycles
  material to a native material in the target engine (not an any-to-any matrix - see
  [Supported Conversions](#-supported-conversions) below)
- 🎯 **Node Group Handling**: recursively ungroups and flattens node trees before
  converting, so nodes inside groups get converted too
- 🖼️ **Image Texture Conversion**: converts `ShaderNodeTexImage` to the target
  engine's image node, including colorspace/gamma handling
- 🔗 **Label-Based Connection Rebuilding**: reconnects converted nodes by matching
  auto-assigned labels between the Cycles side and the engine side
- ⚡ **Three conversion scopes**: active material, active object's material slots, or
  every material in the file

---

## 🎮 Supported Conversions

Conversion is **one-directional, always starting from a Cycles material**:

| Cycles material converted to → | Octane | V-Ray | LuxCore |
| --- | --- | --- | --- |
| Supported | ✅ | ✅ | ✅ |

There is no Octane→V-Ray, V-Ray→LuxCore, etc. path - convert everything back to
Cycles-equivalent nodes first if you need to hop between two non-Cycles engines.

---

## 📥 Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/mochiquin/Material_Converter-1.git
   ```
2. Copy the `Material_Converter 1` folder into your Blender addons directory:
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\{version}\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender/{version}/scripts/addons/`
   - **Linux**: `~/.config/blender/{version}/scripts/addons/`
3. Restart Blender and enable **Material: Material Converter** in
   `Edit → Preferences → Add-ons`

---

## 🚀 Usage

### Basic Material Conversion

1. Select an object with the Cycles material you want to convert
2. Open the **Shader Editor** or **Material Properties** panel and find the
   **Material Converter** panel in the sidebar
3. Pick the target engine (Octane / V-Ray / LuxCore) and click one of:
   - **Convert active material to `<engine>`** - always reconverts the active
     material, even if it was already converted before
   - **Convert all non-`<engine>` materials in selected object** - loops over the
     active object's material slots, skipping materials that already have
     engine-native nodes
   - **Convert all non-`<engine>` materials** - same, but over every material in
     the file

### Auto-Convert Images (Octane)

Toggle **Auto-Convert Images** in the panel to have newly added image texture nodes
automatically convert to `OctaneRGBImage` and auto-connect based on filename
keywords (Diffuse, Normal, Roughness, Metallic, Bump, Opacity, Specular, ...).

---

## 🔧 Technical Details

### Conversion Pipeline

```
Cycles Material
    ↓
1. Remove reroute nodes
    ↓
2. Ungroup all node groups (flatten node tree, recursively)
    ↓
3. Label nodes based on what they feed into
    ↓
4. Convert each recognized node type (image, math, mix, mapping, ...)
    ↓
5. Convert the Principled BSDF → engine material (Universal/Standard/BRDFVRayMtl/...)
    ↓
6. Rebuild connections between converted nodes using label matching
    ↓
Target Engine Material
```

### Octane node coverage

| Cycles node | Converts to | Notes |
| --- | --- | --- |
| Principled BSDF | `OctaneUniversalMaterial` or `OctaneStandardSurfaceMaterial` | user-configurable in preferences |
| Image Texture | `OctaneRGBImage` | |
| Mix (Color/Float/Vector) | `OctaneCyclesMixColorNodeWrapper` / `...MixFloatNodeWrapper` / `...MixFloat3NodeWrapper` | |
| Mapping | `Octane3DTransformation` | |
| Hue/Saturation/Value | `OctaneColorCorrection` | |
| Color Ramp | `OctaneGradientMap` | |
| Invert | `OctaneInvertTexture` | |
| Bump/Normal Map | tagged onto the source image, no dedicated node | |
| Displacement | `OctaneTextureDisplacement` / `OctaneVertexDisplacement` | mode set in preferences |
| Separate Color / Separate RGB | one `OctaneChannelPicker` **per used output channel** | see note below |
| Math: Add/Subtract/Multiply | `OctaneAddTexture` / `OctaneSubtractTexture` / `OctaneMultiplyTexture` | only these three - see limitations |
| RGB (constant color) | `OctaneRGBColor` | |
| Value (constant float) | `OctaneFloatValue` | |
| Glass/Translucent BSDF | `OctaneUniversalMaterial` (Specular/Diffuse model) | |
| Mix Shader | `OctaneMixMaterial` | |

**Separate Color note**: `OctaneChannelPicker` only has one output, but a Cycles
Separate Color/RGB node can drive up to three independent downstream connections
(R/G/B). The converter builds one Channel Picker per output that's actually used,
each configured with the right channel index and RGB/HSV/HSL conversion mode, then
wires them up in a dedicated pass (`rebuild_octane_separate_color_connections`)
since the generic one-node-per-label rebuild logic can't express a 1-to-3 mapping.

**Alpha-clip note**: Blender's glTF importer builds `Less Than → Subtract → Alpha`
style chains for `KHR_materials_alphaMode = MASK`. None of that comparison logic has
a working Octane texture-domain equivalent (see limitations), so the converter
doesn't try to reproduce it - instead it traces back through any node chain from the
Principled BSDF's Alpha input to find the original image texture, and connects that
image's Octane counterpart directly to the material's Opacity input. Octane reads
the image's alpha channel automatically, so the cutoff logic isn't needed.

### Node group handling

Node groups are ungrouped recursively (up to 50 levels deep) by copying internal
nodes into the main material tree and reconnecting Group Input/Output boundaries -
this is scripted directly rather than using Blender's built-in ungroup operator, for
more reliable behavior when run headlessly from these conversion scripts.

### Shared conversion core

`octane/convert_active_octane.py`, `convert_selected_octane.py` and
`convert_all_octane.py` are thin wrappers - they only differ in which materials
they gather (the active material; the active object's material slots; every
material in the file). All of them call the same
`octane/convert_core.py::convert_material_to_octane(mat)` to do the actual work.
Fix bugs or add node support there, once - don't re-duplicate it into the three
entry scripts.

---

## ⚠️ Known Limitations (Octane)

These were found by testing real conversions against actual Octane renders, not by
inference from the API alone - some Octane node types have plausible-looking
sockets that simply don't evaluate:

- **Math node operations other than Add/Subtract/Multiply are not converted**
  (Divide, Less Than, Greater Than, Power, Sqrt, trig functions, ...). Octane has no
  confirmed-working native texture-domain node for these - `OctaneCyclesNodeMathNodeWrapper`,
  `OctaneBinaryMathOperation`, and `OctaneComparison` all exist and have matching
  sockets, but real-render testing showed none of them actually evaluate for
  texture/RGB inputs. Unconverted Math nodes are left in place, unconnected on the
  Octane side.
- **Vector Math is not converted at all**, for the same reason
  (`OctaneCyclesNodeVectorMathNodeWrapper` doesn't render).
- **Procedural textures are not converted**: Noise, Voronoi, Wave, Checker, Brick,
  Gradient, Magic, White Noise. Octane has its own native procedural nodes
  (`OctaneNoiseTexture`, `OctaneSmoothVoronoiContours`, etc.) but they don't map
  1:1 onto Cycles' parameters or algorithm, so this needs dedicated work per node
  type rather than a generic mapping.
- Some complex/uncommon Principled BSDF configurations may need manual adjustment
  after conversion.
- This addon cannot be tested headlessly (`blender --background`) end-to-end: the
  Octane render engine itself fails to initialize without a GPU/window context
  (`gpu.platform.backend_type_get()` raises in background mode), which also breaks
  Octane's node type registration. Conversions have to be verified inside a normal
  Blender session.

---

## 📁 Project Structure

```text
Material_Converter 1/
├── __init__.py                    # Addon registration, operators, UI panels
├── README.md                      # This file
├── CONVERSION_LOGIC.md            # Deeper technical notes on the conversion logic
├── converter/                     # Shared per-node-type conversion helpers
│   ├── Shader_node_group.py       # Recursive node group ungrouping
│   ├── convert_images.py          # Image node conversion
│   ├── convert_curve.py           # RGB Curve conversion
│   └── ...
├── octane/                        # Octane conversion
│   ├── convert_core.py            # Shared conversion logic (see above)
│   ├── convert_active_octane.py   # Thin wrapper: active material
│   ├── convert_selected_octane.py # Thin wrapper: active object's material slots
│   ├── convert_all_octane.py      # Thin wrapper: every material in the file
│   ├── basic_octane.py / glass_octane.py / metal_octane.py / trans_octane.py / ...
│   └── textures_octane.py         # Bulk image import tool (separate from conversion)
├── vray/                          # V-Ray conversion (not actively maintained here)
├── luxcore/                       # LuxCore conversion (not actively maintained here)
├── cycles/                        # Cycles-side helper material tools
├── scripts/                       # Renderer-agnostic shared utilities
│   ├── rebuild.py                 # Label-matched connection rebuilding, per engine
│   ├── connect_nodes.py           # Fallback proximity/label connectors, Alpha-clip bypass
│   ├── premade.py                 # Node labeling (label_nodes_from_base_color, ...)
│   └── auto_convert_image.py      # "Auto-Convert Images" background handler
├── operators/                     # Misc Blender operators (image import, mapping)
└── preferences/                   # Per-engine addon preferences
    ├── octane_preferences.py
    ├── vray_preferences.py
    └── luxcore_preferences.py
```

---

## 🤝 Contributing

Contributions are welcome, particularly around the Octane math/procedural-texture
limitations listed above - if you find a real Octane node that actually evaluates
for a currently-unsupported operation, please open an issue or PR with the node's
`bl_idname` and how you verified it renders.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the GNU General Public License v3.0, the same
license as the original add-on. See [LICENSE](LICENSE) for the full text.

- Copyright (C) 2025-2026 Adam Zorian Radziszewski (original add-on)
- Copyright (C) 2026 mochiquin (modifications in this fork)

---

## 👤 Credits

- Original author: **Adam Zorian Radziszewski**
- Fork maintained by: **[mochiquin](https://github.com/mochiquin)**

### Changes in this fork

- Octane conversion for Math, RGB and Value nodes
- Fix for alpha-clip handling in Octane materials
- An option to ignore alpha in Octane conversion
- Refactor of the conversion core
- Rewritten README documenting Octane node coverage and known limitations

---

## 📚 Documentation

For deeper technical documentation on the conversion logic, see
[CONVERSION_LOGIC.md](CONVERSION_LOGIC.md).
