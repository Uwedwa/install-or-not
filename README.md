<div align="left" style="position: relative;">
<img src="https://cdn-icons-png.flaticon.com/512/6295/6295417.png" align="right" width="25%" style="margin: -20px 0 0 20px;">
<h1>INSTALL OR NOT 2.0</h1>
<p align="left">
	<em><code>Tactical Package Deployment Suite — Smart Silent Installer & Armory System</code></em>
</p>
<p align="left">
	<img src="https://img.shields.io/github/license/Uwedwa/install-or-not?style=flat-square&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/badge/version-2.0.0--tactical-3fb950?style=flat-square" alt="version">
	<img src="https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-58a6ff?style=flat-square&logo=windows" alt="platform">
	<img src="https://img.shields.io/github/last-commit/Uwedwa/install-or-not?style=flat-square&logo=git&logoColor=white&color=0080ff" alt="last-commit">
</p>
</div>
<br clear="right">

---

## 📍 Overview

**INSTALL OR NOT 2.0** is an elite, semi-automated tactical software deployment suite inspired by the atmosphere of *Ready or Not* (SWAT / TOC Communications).

Instead of blindly throwing generic silent flags at executables, **Install or Not 2.0 inspects binary PE headers in real-time** to fingerprint the packaging engine (Inno Setup, NSIS, WiX, InstallShield, 7-Zip, MSI) and deploys each package with its exact tailored silent flags. If an installer refuses silent execution, it gracefully falls back to interactive GUI mode without stalling the deployment queue.

Additionally, it integrates **Winget Tactical Armory Kits** to deploy curated post-format setups (Gaming, Development, Media) in a single click.

---

## 👾 Features (v2.0 Tactical)

* 🧠 **Smart Engine Fingerprinting:** Inspects binary headers to accurately detect Inno Setup, NSIS, WiX Bootstrapper, InstallShield, 7-Zip SFX, and MSI packages.
* 🛡️ **Zero-Conflict Silent Flags:** Delivers engine-specific silent arguments (e.g. `/VERYSILENT` for Inno, `/S` for NSIS, `/qn` for MSI) to avoid syntax rejections.
* 🪄 **Graceful GUI Fallback:** When silent execution returns non-zero, it automatically launches the interactive installer for the operator without breaking the queue.
* 🎯 **Winget Armory Presets:** Curated 1-click loadouts:
  * 🎮 **Gaming Vanguard:** Steam, Discord, OBS Studio, 7-Zip, Visual C++ Runtimes All-in-One, DirectX
  * 💻 **Operator DevKit:** Git, VS Code, Windows Terminal, Python 3.12, Node.js LTS, Docker Desktop
  * 🌐 **Recon & Daily Ops:** Brave, VLC, Spotify, ShareX, qBittorrent, Notepad++
* 🗂️ **Tactical Zone Management:** Inspect, filter, select, import, and delete packages directly inside the deployment zone.
* 📻 **TOC Comms HUD:** Color-coded tactical logging terminal with Ready or Not Entry Team / TOC voice line reporting and audio feedback.

---

## 📁 Project Structure

```bash
install-or-not/
├── install_or_not.py          # Tactical HUD Application & GUI
├── core/
│   ├── detector.py            # Zero-dependency binary PE installer fingerprinting
│   ├── executor.py            # Multi-threaded execution & GUI fallback engine
│   └── presets.py             # Winget armory kits & profile export/import
├── installers/                # Place your .exe and .msi packages here
├── requirements.txt           # Minimal dependencies (Pillow)
├── LICENSE                    # GNU GPL v3
└── README.md
```

---

## 🚀 Getting Started

### ☑️ Prerequisites
- Windows 10 / 11
- Python 3.10+ (if running from source)
- `Pillow` (for icon rendering)

### ⚙️ Installation

```bash
git clone https://github.com/Uwedwa/install-or-not.git
cd install-or-not
pip install -r requirements.txt
python install_or_not.py
```

### 📦 Building Standalone Executable (.exe)

You can compile **Install or Not** into a single standalone `.exe` using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "Install_or_Not" install_or_not.py
```

---

## 🎗 License

This project is licensed under the terms of the **GNU GPL v3**. See the [LICENSE](./LICENSE) file for full details.

---

> Made with Python, caffeine, and tactical operational discipline.
