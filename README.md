# Material Converter for Blender

<div align="center">

**A powerful Blender addon for converting materials between different render engines**

[![Blender](https://img.shields.io/badge/Blender-4.2%2B-orange.svg)](https://www.blender.org/)
[![Version](https://img.shields.io/badge/version-1.0.8-blue.svg)](https://github.com/yourusername/material-converter)
[![License](https://img.shields.io/badge/license-GPL--3.0-green.svg)](LICENSE)

</div>

---

## 📖 Overview

Material Converter is a comprehensive Blender addon that seamlessly converts materials between different render engines. It intelligently handles node groups, texture connections, and material properties to ensure accurate conversions with minimal manual adjustment.

### ✨ Key Features

- 🔄 **Multi-Engine Support**: Convert materials between Cycles, Octane, V-Ray, and LuxCore
- 🎯 **Smart Node Group Handling**: Automatically ungroups and flattens node trees for reliable conversion
- 🖼️ **Auto Image Conversion**: Automatically converts image texture nodes to engine-specific formats
- 🔗 **Intelligent Connection Rebuilding**: Preserves material connections using label-based matching
- ⚡ **Batch Processing**: Convert multiple materials at once
- 🎨 **KISS Principle**: Simple, reliable conversion logic (Keep It Simple, Stupid)

---

## 🎮 Supported Render Engines

| From/To | Cycles | Octane | V-Ray | LuxCore |
|---------|--------|--------|-------|---------|
| **Cycles** | ✅ | ✅ | ✅ | ✅ |
| **Octane** | ✅ | ✅ | ✅ | ✅ |
| **V-Ray** | ✅ | ✅ | ✅ | ✅ |
| **LuxCore** | ✅ | ✅ | ✅ | ✅ |

---

## 📥 Installation

### Method 1: Download and Install

1. Download the latest release from the [Releases page](https://github.com/yourusername/material-converter/releases)
2. Open Blender
3. Go to `Edit` → `Preferences` → `Add-ons`
4. Click `Install...` and select the downloaded `.zip` file
5. Enable the addon by checking the checkbox next to "Material: Material Converter"

### Method 2: Manual Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/material-converter.git
   ```
2. Copy the entire folder to your Blender addons directory:
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\{version}\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender/{version}/scripts/addons/`
   - **Linux**: `~/.config/blender/{version}/scripts/addons/`
3. Restart Blender and enable the addon in Preferences

---

## 🚀 Usage

### Basic Material Conversion

1. Select an object with the material you want to convert
2. Open the **Shader Editor** or **Material Properties** panel
3. In the sidebar, find the **Material Converter** panel
4. Choose your target render engine
5. Click **Convert Material**

### Auto-Convert Images (Octane)

When working with Octane render engine, you can enable automatic image conversion:

1. Enable **Auto-Convert Images** in the Material Converter panel
2. When you drag and drop image texture nodes into the shader editor, they will automatically:
   - Convert to `OctaneRGBImage` nodes
   - Auto-connect to the appropriate material input based on filename keywords
   - Set correct gamma values based on texture type

**Supported Keywords for Auto-Connection**:
- **Diffuse**: `diffuse`, `albedo`, `basecolor`, `base`, `color`
- **Normal**: `normal`, `nrm`, `norm`
- **Roughness**: `rough`, `roughness`
- **Metallic**: `metal`, `metallic`, `metalness`
- **Bump**: `bump`, `height`
- **Opacity**: `opacity`, `alpha`
- **Specular**: `spec`, `specular`

### Batch Conversion

1. Select multiple objects
2. Open the **Material Converter** panel
3. Choose your target render engine
4. Click **Convert All Materials** to convert all materials at once

---

## 🔧 Technical Details

### Conversion Pipeline

```
Cycles Material
    ↓
1. Remove reroute nodes
    ↓
2. Ungroup all node groups (flatten node tree)
    ↓
3. Label nodes based on connections
    ↓
4. Convert image texture nodes
    ↓
5. Convert material nodes (Principled BSDF → Engine Material)
    ↓
6. Rebuild connections using label matching
    ↓
Target Engine Material
```

### Node Group Handling

Material Converter uses a **manual node ungrouping approach** that:
- Copies all nodes from node groups to the main material tree
- Reconstructs internal connections
- Reconnects Group Input/Output to the appropriate nodes
- Handles nested node groups iteratively (up to 50 levels deep)
- Does NOT rely on Blender operators (more reliable in scripts)

### Connection Strategy

Connections are rebuilt using a three-tier matching system:
1. **Label matching** (highest priority)
2. **Image name matching** (for texture nodes)
3. **Node name matching** (fallback)

---

## ⚙️ System Requirements

- **Blender**: 4.2.0 or higher
- **Python**: 3.10+ (included with Blender)
- **Render Engines** (at least one required):
  - Cycles (built-in)
  - Octane Render
  - V-Ray for Blender
  - LuxCore Render

---

## 📁 Project Structure

```
Material_Converter/
├── __init__.py              # Main addon file
├── README.md                # This file
├── CONVERSION_LOGIC.md      # Detailed conversion logic documentation
├── converter/               # Core conversion modules
│   ├── Shader_node_group.py # Node group ungrouping
│   ├── convert_images.py    # Image node conversion
│   └── ...
├── octane/                  # Octane-specific conversion
│   └── convert_active_octane.py
├── vray/                    # V-Ray-specific conversion
├── luxcore/                 # LuxCore-specific conversion
├── cycles/                  # Cycles-specific conversion
├── scripts/                 # Utility scripts
│   ├── rebuild.py           # Connection rebuilding
│   ├── auto_convert_image.py # Auto-convert feature
│   └── premade.py           # Node labeling
├── operators/               # Blender operators
└── preferences/             # Addon preferences
    ├── octane_preferences.py
    ├── vray_preferences.py
    └── luxcore_preferences.py
```

---

## 🐛 Known Issues & Limitations

- Some complex procedural textures may not convert perfectly
- Custom shader nodes may require manual adjustment
- Material output nodes for multiple render engines may need cleanup after conversion
- Alpha/transparency settings might need manual tweaking depending on engine differences

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

---

## 👤 Author

**Adam Zorian Radziszewski**



---

## 🙏 Acknowledgments

- Thanks to the Blender community for their invaluable feedback and support
- Special thanks to all render engine developers for their documentation

---

## 📚 Documentation

For detailed technical documentation on the conversion logic, see [CONVERSION_LOGIC.md](CONVERSION_LOGIC.md).

---

<div align="center">

**If you find this addon helpful, please give it a ⭐ on GitHub!**

</div>
