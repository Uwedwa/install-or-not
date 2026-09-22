"""
Install or Not - Tactical Package Deployment
Core: Tactical Presets & Winget Armory Kits + App Backup/Restore
"""

import json
import os
import subprocess
import threading
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
            {"id": "Ablaze.Floorp", "name": "Floorp Browser", "desc": "Customizable Privacy Browser (Firefox Engine)"},
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

def export_winget_apps(output_file: str, log_callback=None, finished_callback=None):
    """
    Exports all installed system applications via Winget to a JSON manifest.
    Runs asynchronously.
    """
    def _worker():
        try:
            if log_callback:
                log_callback(f"[WINGET EXPORT] Exporting installed applications to: {output_file}\n")
                log_callback("[WINGET EXPORT] Querying system packages via Windows Package Manager...\n")
                
            cmd = ["winget", "export", "-o", output_file, "--include-versions", "--accept-source-agreements", "--disable-interactivity"]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
            
            for line in proc.stdout:
                if line.strip() and log_callback:
                    log_callback(line)
                    
            proc.wait()
            
            if proc.returncode == 0 and os.path.exists(output_file):
                msg = f"✔ Application export completed successfully: {os.path.basename(output_file)}"
                if log_callback:
                    log_callback(f"\n[WINGET EXPORT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg, output_file)
            else:
                msg = f"❌ Application export exited with code {proc.returncode}."
                if log_callback:
                    log_callback(f"\n[WINGET EXPORT] {msg}\n")
                if finished_callback:
                    finished_callback(False, msg, None)
        except Exception as e:
            err = f"❌ Winget export failed: {str(e)}"
            if log_callback:
                log_callback(f"\n[WINGET EXPORT] {err}\n")
            if finished_callback:
                finished_callback(False, err, None)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t

def import_winget_apps(input_file: str, log_callback=None, finished_callback=None):
    """
    Restores and installs all applications listed in a Winget JSON manifest.
    Runs asynchronously.
    """
    def _worker():
        try:
            if not os.path.exists(input_file):
                err = f"❌ Manifest file not found: {input_file}"
                if log_callback:
                    log_callback(f"[WINGET IMPORT] {err}\n")
                if finished_callback:
                    finished_callback(False, err)
                return

            if log_callback:
                log_callback(f"[WINGET IMPORT] Starting restoration from manifest: {os.path.basename(input_file)}\n")
                log_callback("[WINGET IMPORT] Invoking unattended batch installation...\n\n")

            cmd = [
                "winget", "import", "-i", input_file,
                "--ignore-unavailable",
                "--accept-package-agreements",
                "--accept-source-agreements",
                "--disable-interactivity"
            ]
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )

            for line in proc.stdout:
                if line.strip() and log_callback:
                    log_callback(line)

            proc.wait()

            if proc.returncode == 0:
                msg = "✔ All applications restored successfully!"
                if log_callback:
                    log_callback(f"\n[WINGET IMPORT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg)
            else:
                msg = f"⚠ Application import finished with exit code {proc.returncode}."
                if log_callback:
                    log_callback(f"\n[WINGET IMPORT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg)
        except Exception as e:
            err = f"❌ Winget import failed: {str(e)}"
            if log_callback:
                log_callback(f"\n[WINGET IMPORT] {err}\n")
            if finished_callback:
                finished_callback(False, err)

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
