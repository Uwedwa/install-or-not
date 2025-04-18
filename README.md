<div align="left" style="position: relative;">
<img src="https://cdn-icons-png.flaticon.com/512/6295/6295417.png" align="right" width="30%" style="margin: -20px 0 0 20px;">
<h1>INSTALL-OR-NOT</h1>
<p align="left">
	<em><code>A GUI tool that attempts silent installs, then gracefully falls back to manual if needed.</code></em>
</p>
<p align="left">
	<img src="https://img.shields.io/github/license/Uwedwa/install-or-not?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/Uwedwa/install-or-not?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/Uwedwa/install-or-not?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/Uwedwa/install-or-not?style=default&color=0080ff" alt="repo-language-count">
</p>
</div>
<br clear="right">

---

## 🔗 Table of Contents

- [📍 Overview](#-overview)
- [👾 Features](#-features)
- [📁 Project Structure](#-project-structure)
- [🚀 Getting Started](#-getting-started)
  - [☑️ Prerequisites](#-prerequisites)
  - [⚙️ Installation](#-installation)
  - [🤖 Usage](#🤖-usage)
- [📌 Project Roadmap](#-project-roadmap)
- [🎗 License](#-license)

---

## 📍 Overview

Install-or-not is a lightweight desktop tool that lets users install multiple programs in a semi-automated way. It attempts to run each executable in the `installers/` folder with silent flags (e.g., `/S`, `/quiet`).  
If the silent installation fails, it falls back to manual mode by prompting the user to continue the install interactively.

---

## 👾 Features

- Automatically detects `.exe` or `.msi` installers
- Attempts silent installation with smart flags
- If silent mode fails, switches to manual installer execution
- Logs each step and displays real-time messages
- Includes animated feedback and multi-threaded install process
- GUI built with `tkinter`

---

## 📁 Project Structure

```bash
install-or-not/
├── install_or_not.py       # Main logic and GUI
├── installers/             # Put your .exe or .msi files here
├── LICENSE                 # GPL v3 license
└── README.md               # You're reading it!
```

---

## 🚀 Getting Started

### ☑️ Prerequisites

You do **not** need Python if you are using the precompiled `.exe` version.

If you'd rather run it from source:

- Python 3.10+
- `Pillow` (used for image/icon support)
- `tkinter` (usually bundled with Python on Windows)

### ⚙️ Installation

#### Precompiled `.exe` (Recommended)

1. Download the latest `.exe` from [Releases](https://github.com/Uwedwa/install-or-not/releases)
2. Place your `.exe` or `.msi` files into the `installers/` folder.
3. Run the tool as Administrator:
   ```bash
   Install_or_Not.exe
   ```

#### From Source (For Developers)

```bash
git clone https://github.com/Uwedwa/install-or-not
cd install-or-not
pip install pillow
python install_or_not.py
```

---

### 🤖 Usage

1. Add setup files to the `installers/` folder.
2. Run the app.
3. Silent installation will be attempted.
4. If it fails, you'll be prompted for manual install.
5. Progress and logs will appear in the GUI.

---

## 📌 Project Roadmap

- [X] Automatic silent install fallback
- [X] GUI threading and real-time status
- [ ] Per-app silent flag customization
- [ ] Language support (i18n)
- [ ] Dark mode / Theme selection

---

## 🎗 License

This project is licensed under the terms of the **GNU GPL v3**. See the [LICENSE](./LICENSE) file for full details.

---

> Made with Python, caffeine, and a hatred for repetitive installs.
