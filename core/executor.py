"""
Install or Not - Tactical Package Deployment
Core: Multi-Threaded Execution & Fallback Engine
"""

import os
import subprocess
import time
from typing import Callable, Optional, Dict, Any
from .detector import analyze_installer, InstallerProfile

class DeploymentTask:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.file_name = os.path.basename(file_path)
        self.profile: InstallerProfile = analyze_installer(file_path)
        self.status = "PENDING"
        self.detail = ""
        self.is_silent_success = False
        self.duration = 0.0

def execute_installer_task(
    task: DeploymentTask,
    log_callback: Callable[[str, str], None],
    timeout: int = 300
) -> bool:
    """
    Executes a single installer task:
    1. Tries targeted silent execution based on detected engine.
    2. If silent execution fails, smoothly falls back to interactive GUI execution.
    """
    start_time = time.time()
    file_path = task.file_path
    file_name = task.file_name
    profile = task.profile

    log_callback(f"Analyzing {file_name}: Detected engine '{profile.engine}' ({profile.confidence} confidence)", "INFO")

    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

    # 1. Prepare Command Line
    if file_path.lower().endswith(".msi"):
        command = ["msiexec", "/i", file_path] + profile.silent_args
    else:
        command = [file_path] + profile.silent_args

    log_callback(f"Engaging silent deployment: {' '.join(command[:4])}...", "INFO")
    task.status = "INSTALLING_SILENT"

    silent_ok = False
    try:
        proc = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creation_flags,
            timeout=timeout
        )
        # Windows Installer return codes: 0 = success, 3010 = success, reboot required
        if proc.returncode in (0, 3010):
            silent_ok = True
            reboot_tag = " (Reboot recommended)" if proc.returncode == 3010 else ""
            log_callback(f"Package {file_name} successfully deployed silent!{reboot_tag}", "SUCCESS")
            task.status = "SUCCESS_SILENT"
            task.detail = f"Silent OK{reboot_tag}"
            task.is_silent_success = True
        else:
            log_callback(f"Silent deployment exited with code {proc.returncode}. Initiating GUI fallback...", "WARNING")
    except subprocess.TimeoutExpired:
        log_callback(f"Silent deployment timed out ({timeout}s). Falling back to GUI...", "WARNING")
    except Exception as e:
        log_callback(f"Silent deployment exception ({e}). Falling back to GUI...", "WARNING")

    # 2. GUI Fallback if Silent Failed
    if not silent_ok:
        task.status = "FALLBACK_GUI"
        log_callback(f"TOC to Entry Team: Opening interactive window for {file_name}...", "INFO")
        try:
            gui_flags = getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
            p = subprocess.Popen([file_path], creationflags=gui_flags)
            task.detail = "Manual GUI Launched"
            task.status = "MANUAL_LAUNCHED"
            log_callback(f"Manual installer for {file_name} launched in foreground.", "INFO")
            # We don't block the queue indefinitely on manual GUI; mark as manual active
            silent_ok = True
        except Exception as e:
            log_callback(f"Critical error launching GUI for {file_name}: {e}", "CRITICAL")
            task.status = "FAILED"
            task.detail = str(e)
            silent_ok = False

    task.duration = round(time.time() - start_time, 1)
    return silent_ok

def execute_winget_install(
    package_id: str,
    log_callback: Callable[[str, str], None],
    timeout: int = 600
) -> bool:
    """
    Installs a package via Winget silently with automated agreement acceptance.
    """
    log_callback(f"Deploying Winget package '{package_id}'...", "INFO")
    creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    cmd = [
        "winget", "install",
        "--id", package_id,
        "--source", "winget",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements"
    ]
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            creationflags=creation_flags,
            timeout=timeout
        )
        if proc.returncode == 0:
            log_callback(f"Winget package '{package_id}' deployed successfully!", "SUCCESS")
            return True
        else:
            err = proc.stderr.strip() or proc.stdout.strip()
            log_callback(f"Winget install failed for '{package_id}': {err[:150]}", "ERROR")
            return False
    except subprocess.TimeoutExpired:
        log_callback(f"Winget install timed out for '{package_id}'", "ERROR")
        return False
    except Exception as e:
        log_callback(f"Winget install error: {e}", "CRITICAL")
        return False
