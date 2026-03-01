# Image → 3D Pro - UI Design Specification

## Overview

This document provides complete specifications for recreating the "Image → 3D Pro" desktop application UI. Follow these specifications exactly to match the provided design.

---

## Color Palette

### Background Colors
| Name | HEX | Usage |
|------|-----|-------|
| Deepest BG | `#0a0e1a` | Main window background |
| Sidebar BG | `#0d1320` | Left sidebar background |
| Card BG | `#111827` | Content cards/panels |
| Input BG | `#1a2332` | Input fields, dropdowns |
| Border | `#1e3a5f` | Card borders, dividers |
| Border Light | `#2d4a6f` | Hover states |

### Accent Colors
| Name | HEX | Usage |
|------|-----|-------|
| Primary Blue | `#3b82f6` | Active tabs, primary buttons, links |
| Primary Blue Hover | `#2563eb` | Button hover states |
| Success Green | `#22c55e` | Generate button, success states |
| Success Green Hover | `#16a34a` | Generate button hover |
| Danger Red | `#ef4444` | Quit button, errors |
| Danger Red Hover | `#dc2626` | Danger hover |
| Warning/Accent | `#f59e0b` | Secondary accents |

### Text Colors
| Name | HEX | Usage |
|------|-----|-------|
| Text Primary | `#e2e8f0` | Headings, primary text |
| Text Secondary | `#94a3b8` | Labels, secondary info |
| Text Muted | `#64748b` | Placeholder text, hints |
| Text Accent | `#60a5fa` | Links, highlighted text |
| Status Green | `#4ade80` | Online/secured status |

---

## Layout Structure

### Window Dimensions
- **Minimum Size**: 1200x800 pixels
- **Default Size**: 1400x900 pixels
- **Resizable**: Yes

### Layout Grid
```
+----------------------------------------------------------+
|  SIDEBAR (280px)  |  MAIN CONTENT AREA (flexible)        |
|                   |                                      |
|  +-------------+  |  +----------------------------------+  |
|  | Logo/Title  |  |  | SOURCE        | PROCESSING      |  |
|  +-------------+  |  +---------------+------------------+  |
|  | DEVICE      |  |                                      |
|  |  - ID       |  |  +--------------------------------+  |
|  |  - Host     |  |  | PREVIEW        | PROGRESS       |  |
|  |  - Status   |  |  |                |                |  |
|  +-------------+  |  +--------------------------------+  |
|  | SYSTEM      |  |                                      |
|  |  - RAM      |  |  +--------------------------------+  |
|  |  - CPU      |  |  |         ACTION BUTTONS         |  |
|  |  - Platform |  |  +--------------------------------+  |
|  |  - Mode     |  |                                      |
|  +-------------+  |  +--------------------------------+  |
|  |             |  |  | OUTPUTS (OBJ | STL | GLB)       |  |
|  +-------------+  |  +--------------------------------+  |
|  | Log Out     |  |                                      |
|  +-------------+  |  +--------------------------------+  |
|  | Quit        |  |  | ACTIVITY LOG                   |  |
|  +-------------+  |  +--------------------------------+  |
+-------------------+--------------------------------------+
```

---

## Component Specifications

### 1. Left Sidebar (Width: 280px)

#### Header Section
- **Logo**: Brain/AI icon (🧠) + "Image → 3D Pro" text
- **Version**: "v2.1.0" below title, muted color
- **Padding**: 20px top, 16px sides

#### DEVICE Card
```
┌─────────────────────────┐
│ 🔒 DEVICE               │  ← Header with lock icon
├─────────────────────────┤
│ ID:      719FB37F       │  ← Right-aligned value
│ Host:    DESKTOP-XXX    │
│ Status:  ✓ Secured      │  ← Green checkmark + text
└─────────────────────────┘
```
- Background: `#0d1320` with border `#1e3a5f`
- Border radius: 8px
- Padding: 16px
- Label color: `#94a3b8`
- Value color: `#60a5fa` (blue) for ID, `#4ade80` (green) for Status

#### SYSTEM Card
```
┌─────────────────────────┐
│ ⚙️ SYSTEM               │
├─────────────────────────┤
│ RAM:      3.41 / 15.88 GB
│ CPU:      8             │
│ Platform: Windows 10    │
│ Mode:     Local         │  ← Green text
└─────────────────────────┘
```
- Same styling as DEVICE card
- "Local" in green (`#4ade80`)

#### Action Buttons (Bottom)
```
┌─────────────────────────┐
│ 🔒 Log Out              │  ← Secondary button
├─────────────────────────┤
│ ✕ Quit                  │  ← Danger button (red bg)
└─────────────────────────┘
```
- **Log Out**: Bordered button, transparent bg, white text
- **Quit**: Solid red (`#ef4444`) background, white text
- Height: 44px
- Border radius: 6px

---

### 2. SOURCE Section (Top Left)

#### Tab Switcher
```
┌─────────────────────────────────────┐
│  📁 SOURCE                          │
├─────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐        │
│  │ 🖼️ Image │  │ 🔤 Text  │        │
│  │  ACTIVE  │  │          │        │
│  └──────────┘  └──────────┘        │
│       Blue bg      Dark bg          │
└─────────────────────────────────────┘
```
- Active tab: Blue (`#3b82f6`) background, white text
- Inactive tab: Dark (`#1a2332`) background, gray text
- Tab border radius: 6px
- Gap between tabs: 8px

#### File Selection Area
```
┌─────────────────────────────────────┐
│                                     │
│  ┌───────────────────────────────┐  │
│  │ Select image file...          │  │  ← Input field
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────┐                      │
│  │ Browse... │                      │  ← Button
│  └───────────┘                      │
│                                     │
└─────────────────────────────────────┘
```
- Input: Dark bg (`#1a2332`), border `#1e3a5f`, placeholder text
- Browse button: Blue (`#3b82f6`), white text, rounded

---

### 3. PROCESSING Section (Top Right)

#### Method Selection
```
┌─────────────────────────────────────────────────────────┐
│ ⚙️ PROCESSING                                           │
├─────────────────────────────────────────────────────────┤
│ Method                                                  │
│ ┌─────────────────────────────┐ ┌─────────────────────┐ │
│ │ ◉ Local Processing          │ │ ○ Cloud API         │ │
│ │   Geometry only             │ │   Geometry + Texture│ │
│ └─────────────────────────────┘ └─────────────────────┘ │
│      Selected (blue border)        Unselected          │
└─────────────────────────────────────────────────────────┘
```
- Radio button style cards
- Selected: Blue border (`#3b82f6`), subtle blue bg tint
- Unselected: Border `#1e3a5f`, dark bg
- Icon: Computer for Local, Cloud for Cloud API

#### Quality Dropdown
```
│ Quality                                                 │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Standard                              ▼             │ │
│ └─────────────────────────────────────────────────────┘ │
```
- Full width dropdown
- Dark bg, border, rounded corners

---

### 4. PREVIEW Section (Middle Left)

```
┌─────────────────────────────────────────────────────────┐
│ 🖼️ PREVIEW                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│    ┌───────────────────────────────────────────────┐    │
│    │                                               │    │
│    │                                               │    │
│    │         No image selected                     │    │
│    │                                               │    │
│    │                                               │    │
│    └───────────────────────────────────────────────┘    │
│         Dashed border (#1e3a5f)                         │
│         Rounded corners (12px)                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
- Dashed border: 2px dashed `#1e3a5f`
- Background: Slightly lighter than card (`#151d2a`)
- Border radius: 12px
- Min height: 250px
- Centered placeholder text

---

### 5. PROGRESS Section (Middle Right)

```
┌─────────────────────────────────────────────────────────┐
│ 📊 PROGRESS                                             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │  ████████████████████████████████████░░░░░░░░░ │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│              Progress bar (blue fill)                 │
│                                                         │
│  ⏳ Ready                                               │
│                                                         │
│  Elapsed: --:--                           ETA: --:--   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
- Progress bar: Blue (`#3b82f6`) fill, dark track
- Status: Hourglass icon + text
- Time labels: Small, muted color, space-between layout

---

### 6. Action Buttons (Center)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│   ┌──────────┐  ┌──────────┐  ┌──────────────────────┐ │
│   │ 🔄 Reset │  │ 📂 Open  │  │ 🚀 Generate 3D Model │ │
│   │          │  │ Folder   │  │                    │ │
│   └──────────┘  └──────────┘  └──────────────────────┘ │
│      Gray bg      Gray bg         Green bg (#22c55e)   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
- **Reset**: Gray (`#475569`), white text
- **Open Folder**: Gray (`#475569`), white text, folder icon
- **Generate 3D Model**: Green (`#22c55e`), white text, rocket icon
- All buttons: 44px height, 8px border radius
- Generate button: Wider, bold text

---

### 7. OUTPUTS Section (Bottom)

```
┌─────────────────────────────────────────────────────────┐
│ 📦 OUTPUTS                                              │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │ OBJ          │ │ STL          │ │ GLB          │   │
│  │              │ │              │ │              │   │
│  │ ┌───┐ ┌───┐ │ │ ┌───┐ ┌───┐ │ │ ┌───┐ ┌───┐ │   │
│  │ │Open│ │Save│ │ │Open│ │Save│ │ │Open│ │Save│ │   │
│  │ └───┘ └───┘ │ │ └───┘ └───┘ │ │ └───┘ └───┘ │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│                                                         │
│     Dark cards with title and two buttons each         │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Output Card Structure
- Title: Format name (OBJ, STL, GLB) in blue (`#60a5fa`)
- Background: `#1a2332`
- Border: `#1e3a5f`
- Border radius: 8px
- Two buttons per card:
  - **Open**: Blue (`#3b82f6`), white text
  - **Save**: Dark (`#374151`), white text

---

### 8. ACTIVITY LOG Section (Bottom)

```
┌─────────────────────────────────────────────────────────┐
│ 📋 ACTIVITY LOG                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │  [10:30:15] Application started                 │   │
│  │  [10:30:22] User logged in                      │   │
│  │  [10:31:05] Image loaded: example.jpg           │   │
│  │                                                 │   │
│  │                                                 │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│              Dark text area, monospace font            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```
- Background: `#0d1320`
- Text: Monospace font, `#94a3b8` color
- Border: `#1e3a5f`
- Scrollable
- Timestamps in brackets

---

## Typography

### Font Family
- **Primary**: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif`
- **Monospace**: `'Consolas', 'Monaco', 'Courier New', monospace` (for logs)

### Font Sizes
| Element | Size | Weight |
|---------|------|--------|
| App Title | 20px | Bold (700) |
| Section Headers | 13px | Bold (600) |
| Card Titles | 14px | Bold (600) |
| Body Text | 13px | Normal (400) |
| Labels | 12px | Normal (400) |
| Buttons | 13px | Semi-bold (600) |
| Small/Status | 11px | Normal (400) |

---

## Spacing & Dimensions

### Margins & Padding
- Window padding: 20px
- Card padding: 16px
- Card margin-bottom: 16px
- Section gap: 20px
- Button padding: 10px 20px
- Input padding: 10px 14px

### Border Radius
- Cards/Groups: 10px
- Buttons: 8px
- Inputs: 6px
- Small elements: 4px

### Sidebar
- Width: 280px fixed
- Internal padding: 16px

---

## Icons

Use emoji icons as shown:
- 🧠 Logo/Brain
- 🔒 Device/Security
- ⚙️ System/Settings
- 📁 Source
- 🖼️ Image
- 🔤 Text
- 💻 Local Processing
- ☁️ Cloud API
- 📊 Progress
- ⏳ Status/Hourglass
- 🔄 Reset
- 📂 Open Folder
- 🚀 Generate
- 📦 Outputs
- 📋 Activity Log
- ✕ Close/Quit

---

## File Structure

```
project/
├── main.py                    # Application entry point
├── requirements.txt           # Dependencies
├── ui/
│   ├── __init__.py
│   ├── main_window.py         # Main window implementation
│   ├── auth_dialog.py         # Authentication dialog
│   └── styles/
│       └── styles.qss         # Qt stylesheet (optional)
├── core/
│   ├── __init__.py
│   ├── session_manager.py     # User session management
│   └── [other modules]
└── assets/
    └── logo/
        └── logo.png           # App logo
```

---

## Implementation Notes

### Framework
- **Recommended**: PySide6 or PyQt6
- Alternative: PyQt5, PySide2

### Key Widgets
- `QMainWindow` - Main window
- `QWidget` with `QHBoxLayout` - Sidebar + Content split
- `QGroupBox` - Section containers
- `QTabWidget` or custom buttons - Image/Text tabs
- `QRadioButton` with custom styling - Method selection
- `QComboBox` - Quality dropdown
- `QProgressBar` - Progress indicator
- `QPlainTextEdit` - Activity log
- `QFrame` - Output cards

### Styling Approach
1. Use `setStyleSheet()` on widgets for specific styling
2. OR create a `styles.qss` file and load it:
   ```python
   app.setStyleSheet(open("ui/styles/styles.qss").read())
   ```

### Critical Implementation Details

1. **Sidebar Fixed Width**: Set maximum and minimum width to 280px
2. **Tab Switcher**: Custom implementation with `QPushButton` or `QTabBar`
3. **Method Cards**: Use `QRadioButton` with custom styling or clickable `QFrame`
4. **Preview Area**: `QFrame` with dashed border, accept drag-drop
5. **Progress Bar**: Custom styling for chunk color
6. **Output Cards**: Three identical cards in horizontal layout

### Color Application Priority
1. Apply background colors to containers first
2. Use border colors for definition
3. Apply accent colors sparingly for emphasis
4. Ensure text contrast meets accessibility standards

---

## Example Code Structure

```python
# Main window setup
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image → 3D Pro")
        self.setMinimumSize(1200, 800)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout: Sidebar + Content
        main_layout = QHBoxLayout(central)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Sidebar (fixed width)
        self.sidebar = self._create_sidebar()
        self.sidebar.setFixedWidth(280)
        main_layout.addWidget(self.sidebar)
        
        # Content area
        self.content = self._create_content_area()
        main_layout.addWidget(self.content, 1)
        
        # Apply global stylesheet
        self.setStyleSheet(self._get_stylesheet())
    
    def _create_sidebar(self):
        # Implementation per specifications above
        pass
    
    def _create_content_area(self):
        # Implementation per specifications above
        pass
```

---

## Verification Checklist

- [ ] Window has dark background (`#0a0e1a`)
- [ ] Sidebar is 280px wide with correct background
- [ ] Logo shows "Image → 3D Pro" with brain icon
- [ ] DEVICE card shows ID, Host, Status (green checkmark)
- [ ] SYSTEM card shows RAM, CPU, Platform, Mode (green)
- [ ] Log Out and Quit buttons at bottom of sidebar
- [ ] SOURCE section has Image/Text tabs (blue active)
- [ ] File selection input with Browse button
- [ ] PROCESSING section has Local/Cloud radio cards
- [ ] Quality dropdown present
- [ ] PREVIEW has dashed border area
- [ ] PROGRESS has blue progress bar and time labels
- [ ] Three action buttons: Reset, Open Folder, Generate (green)
- [ ] OUTPUTS has three cards: OBJ, STL, GLB
- [ ] Each output card has Open (blue) and Save (gray) buttons
- [ ] ACTIVITY LOG at bottom with monospace text
- [ ] All spacing and padding matches specifications
- [ ] All colors match the palette exactly

---

## End of Specification
