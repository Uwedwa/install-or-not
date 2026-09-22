"""
Install or Not - Tactical Package Deployment
Core: Tactical Presets & Winget Armory Kits
"""

import json
import os
from typing import Dict, List, Any

TACTICAL_PRESETS: Dict[str, Dict[str, Any]] = {
    "Gaming Vanguard": {
        "icon": "🎮",
        "description": "Essential gaming runtimes, platforms, and communication apps.",
        "packages": [
            {"id": "Valve.Steam", "name": "Steam", "desc": "Gaming Platform"},
            {"id": "Discord.Discord", "name": "Discord", "desc": "Voice & Community Chat"},
            {"id": "OBSProject.OBSStudio", "name": "OBS Studio", "desc": "Streaming & Screen Recording"},
            {"id": "7zip.7zip", "name": "7-Zip", "desc": "High-ratio Archive Utility"},
            {"id": "Microsoft.VCRedist.2015+.x64", "name": "Visual C++ 2015-2022", "desc": "Mandatory Game Runtimes"},
            {"id": "Microsoft.DirectX", "name": "DirectX End-User", "desc": "Legacy & Modern DirectX Dlls"},
        ]
    },
    "Operator DevKit": {
        "icon": "💻",
        "description": "Developer workstations: version control, IDEs, runtimes, containers.",
        "packages": [
            {"id": "Git.Git", "name": "Git", "desc": "Distributed Version Control"},
            {"id": "Microsoft.VisualStudioCode", "name": "VS Code", "desc": "Code Editor & Extensions"},
            {"id": "Microsoft.WindowsTerminal", "name": "Windows Terminal", "desc": "Fluent Tabbed Shell"},
            {"id": "Python.Python.3.12", "name": "Python 3.12", "desc": "Modern Python Runtime"},
            {"id": "OpenJS.NodeJS.LTS", "name": "Node.js LTS", "desc": "JavaScript Engine & npm"},
            {"id": "Docker.DockerDesktop", "name": "Docker Desktop", "desc": "Containerization Platform"},
        ]
    },
    "Recon & Daily Ops": {
        "icon": "🌐",
        "description": "Privacy browsers, media players, lightweight power tools.",
        "packages": [
            {"id": "Brave.Brave", "name": "Brave Browser", "desc": "Adblocking Privacy Browser"},
            {"id": "VideoLAN.VLC", "name": "VLC Media Player", "desc": "Universal Media Codecs"},
            {"id": "Spotify.Spotify", "name": "Spotify", "desc": "Digital Music Streaming"},
            {"id": "ShareX.ShareX", "name": "ShareX", "desc": "Tactical Screenshot & OCR"},
            {"id": "qBittorrent.qBittorrent", "name": "qBittorrent", "desc": "Ad-free Torrent Client"},
            {"id": "Notepad++.Notepad++", "name": "Notepad++", "desc": "Fast Text & Code Editor"},
        ]
    }
}

def export_profile(file_path: str, profile_name: str, package_ids: List[str]) -> bool:
    try:
        data = {
            "version": "2.0.0",
            "profile_name": profile_name,
            "packages": package_ids
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False

def import_profile(file_path: str) -> List[str]:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("packages", [])
    except Exception:
        return []
