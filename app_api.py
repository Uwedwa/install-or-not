# app_api.py
# Tactical Backend Bridge for PyWebView

import os
import sys
import json
import time
import shutil
import threading
import subprocess
import webview

from core.detector import analyze_installer
from core.executor import DeploymentTask, execute_installer_task, execute_winget_install
from core.presets import (
    TACTICAL_PRESETS,
    export_winget_apps,
    import_winget_apps
)
from core.winget_bootstrap import is_winget_ready, bootstrap_winget_ltsc
from core.drivers import backup_drivers, restore_drivers, get_backup_stats

try:
    import winsound
    def play_tactical_beep(freq=1200, duration=80):
        try:
            winsound.Beep(freq, duration)
        except Exception:
            pass
except Exception:
    def play_tactical_beep(freq=1200, duration=80):
        pass


class TacticalBridge:
    def __init__(self, installers_dir=None):
        self._window = None
        self._installers_dir = installers_dir or os.path.join(os.getcwd(), "installers")
        os.makedirs(self._installers_dir, exist_ok=True)
        self._is_deploying = False

    def _set_window(self, window):
        self._window = window

    def _eval(self, js_code):
        if self._window:
            try:
                self._window.evaluate_js(js_code)
            except Exception as e:
                print(f"[JS EVAL ERR] {e}")

    def log(self, message: str, level: str = "INFO"):
        print(f"[{level}] {message}")
        safe_msg = json.dumps(message)
        self._eval(f"window.appendLog('{level}', {safe_msg})")

    def driver_log(self, text: str):
        safe_txt = json.dumps(text)
        self._eval(f"window.appendDriverLog({safe_txt})")

    # -------------------------------------------------------------
    # INSTALLERS & DEPLOY ZONE
    # -------------------------------------------------------------
    def get_installers(self):
        result = []
        if not os.path.exists(self._installers_dir):
            return result

        files = [f for f in os.listdir(self._installers_dir) if f.lower().endswith((".exe", ".msi"))]
        for fname in sorted(files):
            fpath = os.path.join(self._installers_dir, fname)
            profile = analyze_installer(fpath)
            size_mb = round(os.path.getsize(fpath) / (1024 * 1024), 1)
            result.append({
                "name": fname,
                "size_mb": size_mb,
                "engine": profile.engine,
                "confidence": profile.confidence,
                "silent_args": profile.silent_args
            })
        return result

    def open_installers_folder(self):
        try:
            os.startfile(self._installers_dir)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def start_deployment(self):
        if self._is_deploying:
            return {"success": False, "message": "Deployment already running"}

        files = [f for f in os.listdir(self._installers_dir) if f.lower().endswith((".exe", ".msi"))]
        if not files:
            return {"success": False, "message": "No installers found"}

        self._is_deploying = True
        total = len(files)
        success_count = 0
        self.log(f"Initiating deployment sequence for {total} packages...", "INFO")
        play_tactical_beep(1100, 100)

        for idx, fname in enumerate(files):
            fpath = os.path.join(self._installers_dir, fname)
            pct = (idx / total) * 100
            self._eval(f"window.updateDeployProgress({pct}, 'Deploying: {fname}...')")
            self._eval(f"window.updateTaskBadge('{fname}', 'DEPLOYING...', 'status-running')")

            task = DeploymentTask(fpath)
            ok = execute_installer_task(task, self.log)

            if task.status == "SUCCESS_SILENT":
                self._eval(f"window.updateTaskBadge('{fname}', '✔ SILENT OK', 'status-success')")
                success_count += 1
            elif task.status == "MANUAL_LAUNCHED":
                self._eval(f"window.updateTaskBadge('{fname}', '🟡 MANUAL GUI', 'status-manual')")
                success_count += 1
            else:
                self._eval(f"window.updateTaskBadge('{fname}', '❌ FAILED', 'status-failed')")

            time.sleep(0.3)

        self._eval(f"window.updateDeployProgress(100, 'Deployment sequence completed.')")
        self._is_deploying = False

        if success_count == total:
            self.log(f"All {total} packages deployed successfully. Operation a complete success.", "SUCCESS")
            return {"success": True, "count": total}
        else:
            self.log(f"Partial deployment: {success_count}/{total} succeeded.", "WARNING")
            return {"success": False, "count": success_count, "total": total}

    # -------------------------------------------------------------
    # WINGET ARMORY
    # -------------------------------------------------------------
    def get_winget_status(self):
        ok, ver = is_winget_ready()
        return {"ready": ok, "version": ver}

    def get_presets(self):
        return TACTICAL_PRESETS

    def search_winget(self, query):
        if not query or not query.strip():
            return "Empty search term."
        cmd = ["winget", "search", query.strip(), "--source", "winget"]
        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creation_flags)
            return proc.stdout if proc.returncode == 0 else (proc.stderr or proc.stdout)
        except Exception as e:
            return f"Error executing winget: {e}"

    def deploy_single_winget(self, package_id):
        if not package_id:
            return {"success": False, "message": "No package ID"}
        self.log(f"Deploying Winget package: {package_id}...", "INFO")
        ok = execute_winget_install(package_id, self.log)
        return {"success": ok}

    def deploy_preset(self, preset_key):
        preset = TACTICAL_PRESETS.get(preset_key)
        if not preset:
            return {"success": False, "message": "Preset not found"}

        packages = preset.get("packages", [])
        self.log(f"Engaging armory kit '{preset_key}' with {len(packages)} packages...", "INFO")
        success_count = 0
        for p in packages:
            ok = execute_winget_install(p["id"], self.log)
            if ok:
                success_count += 1
            time.sleep(1)

        ok = (success_count == len(packages))
        return {"success": ok, "count": success_count, "total": len(packages)}

    def bootstrap_winget_ltsc(self):
        self.log("Starting native LTSC Winget bootstrapper...", "INFO")
        event = threading.Event()
        result = {"success": False, "message": ""}

        def _finish(success, msg, ver):
            result["success"] = success
            result["message"] = msg
            result["version"] = ver
            event.set()

        bootstrap_winget_ltsc(log_callback=lambda l: self.log(l.strip(), "INFO"), finished_callback=_finish)
        event.wait(timeout=300)
        return result

    def export_winget_apps(self, save_path):
        event = threading.Event()
        result = {"success": False, "message": ""}

        def _finish(success, msg, out):
            result["success"] = success
            result["message"] = msg
            result["output"] = out
            event.set()

        export_winget_apps(save_path, log_callback=lambda l: self.log(l.strip(), "INFO"), finished_callback=_finish)
        event.wait(timeout=180)
        return result

    def import_winget_apps(self, manifest_path):
        event = threading.Event()
        result = {"success": False, "message": ""}

        def _finish(success, msg):
            result["success"] = success
            result["message"] = msg
            event.set()

        import_winget_apps(manifest_path, log_callback=lambda l: self.log(l.strip(), "INFO"), finished_callback=_finish)
        event.wait(timeout=600)
        return result

    # -------------------------------------------------------------
    # DRIVER VAULT
    # -------------------------------------------------------------
    def get_default_driver_dir(self):
        return os.path.abspath("drivers_backup")

    def get_driver_stats(self, path):
        return get_backup_stats(path)

    def backup_drivers(self, dest_dir):
        event = threading.Event()
        result = {"success": False, "message": ""}

        def _finish(success, msg, stats):
            result["success"] = success
            result["message"] = msg
            result["stats"] = stats
            event.set()

        self.driver_log(f"\n{'='*60}\n[DRIVER VAULT] INITIATING DRIVER BACKUP OPERATION\n{'='*60}\n")
        backup_drivers(dest_dir, log_callback=self.driver_log, finished_callback=_finish)
        event.wait(timeout=600)
        return result

    def restore_drivers(self, source_dir):
        event = threading.Event()
        result = {"success": False, "message": ""}

        def _finish(success, msg, count):
            result["success"] = success
            result["message"] = msg
            result["count"] = count
            event.set()

        self.driver_log(f"\n{'='*60}\n[DRIVER VAULT] INITIATING DRIVER RESTORE OPERATION\n{'='*60}\n")
        restore_drivers(source_dir, log_callback=self.driver_log, finished_callback=_finish)
        event.wait(timeout=600)
        return result

    # -------------------------------------------------------------
    # FILE DIALOGS & PACKAGE MANAGEMENT
    # -------------------------------------------------------------
    def select_folder(self, title="Select Directory", default_path=""):
        if not self._window:
            return default_path
        res = self._window.create_file_dialog(webview.FOLDER_DIALOG, directory=default_path)
        if res and len(res) > 0:
            return res[0]
        return None

    def select_save_file(self, title="Save File", default_name=""):
        if not self._window:
            return None
        res = self._window.create_file_dialog(
            webview.SAVE_DIALOG,
            save_filename=default_name,
            file_types=('JSON Files (*.json)', 'All Files (*.*)')
        )
        if isinstance(res, (list, tuple)) and len(res) > 0:
            return res[0]
        elif isinstance(res, str):
            return res
        return None

    def select_open_file(self, title="Select File"):
        if not self._window:
            return None
        res = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            file_types=('JSON Files (*.json)', 'All Files (*.*)')
        )
        if isinstance(res, (list, tuple)) and len(res) > 0:
            return res[0]
        elif isinstance(res, str):
            return res
        return None

    def import_packages_dialog(self):
        if not self._window:
            return {"count": 0}
        files = self._window.create_file_dialog(
            webview.OPEN_DIALOG,
            allow_multiple=True,
            file_types=('Installers (*.exe;*.msi)', 'All Files (*.*)')
        )
        if not files:
            return {"count": 0}

        count = 0
        for src in files:
            fname = os.path.basename(src)
            dst = os.path.join(self._installers_dir, fname)
            try:
                shutil.copy2(src, dst)
                self.log(f"Imported: {fname}", "SUCCESS")
                count += 1
            except Exception as e:
                self.log(f"Failed to import {fname}: {e}", "ERROR")

        return {"count": count}

    def delete_packages(self, file_names):
        for fname in file_names:
            fpath = os.path.join(self._installers_dir, fname)
            try:
                if os.path.exists(fpath):
                    os.remove(fpath)
                    self.log(f"Deleted package: {fname}", "INFO")
            except Exception as e:
                self.log(f"Error deleting {fname}: {e}", "ERROR")
        return {"success": True}

    # -------------------------------------------------------------
    # MISSION BRIEFING NOTES
    # -------------------------------------------------------------
    def load_briefing_notes(self):
        notes_path = os.path.join(os.getcwd(), "toc_notes.txt")
        if os.path.exists(notes_path):
            try:
                with open(notes_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception:
                pass

        default_notes = (
            "TACTICAL FIELD DIRECTIVES:\n\n"
            "1. SMART ENGINE DETECTION:\n"
            "   All .exe & .msi packages in 'installers/' are inspected.\n"
            "   Inno, NSIS, InstallShield, WiX & 7z receive exact silent flags.\n\n"
            "2. AUTOMATIC FALLBACK:\n"
            "   If silent install exits with non-zero, GUI automatically\n"
            "   spawns in foreground without failing the entire queue.\n\n"
            "3. NVIDIA DRIVERS:\n"
            "   Always build clean bloatware-free packages using NVCLEANINSTALL.\n\n"
            "4. RUN AS ADMINISTRATOR:\n"
            "   Always execute this suite with elevated privileges\n"
            "   to prevent privilege escalation blocks."
        )
        return default_notes

    def save_briefing_notes(self, content):
        notes_path = os.path.join(os.getcwd(), "toc_notes.txt")
        try:
            with open(notes_path, "w", encoding="utf-8") as f:
                f.write(content)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}
