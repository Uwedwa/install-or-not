"""
core/winget_bootstrap.py - LTSC-Ready Winget Bootstrapper & Ecosystem Utilities
Part of Install or Not 2.0
"""

import os
import sys
import subprocess
import threading
import urllib.request
import shutil

LTSC_DEPENDENCY_URLS = {
    "vclibs": {
        "name": "Microsoft.VCLibs.x64.14.00.Desktop.appx",
        "url": "https://aka.ms/Microsoft.VCLibs.x64.14.00.Desktop.appx",
        "desc": "Visual C++ UWP Runtime Dependency"
    },
    "xaml": {
        "name": "Microsoft.UI.Xaml.2.8.x64.appx",
        "url": "https://github.com/microsoft/microsoft-ui-xaml/releases/download/v2.8.6/Microsoft.UI.Xaml.2.8.x64.appx",
        "desc": "Windows UI Xaml 2.8 Framework"
    },
    "bundle": {
        "name": "Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle",
        "url": "https://github.com/microsoft/winget-cli/releases/latest/download/Microsoft.DesktopAppInstaller_8wekyb3d8bbwe.msixbundle",
        "desc": "Microsoft Desktop App Installer (Winget CLI)"
    }
}

def is_winget_ready() -> tuple:
    """
    Checks if winget is installed, reachable, and working.
    Returns (True, version_string) or (False, reason).
    """
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        proc = subprocess.run(
            ["winget", "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=creationflags
        )
        if proc.returncode == 0 and proc.stdout.strip():
            return True, proc.stdout.strip()
    except Exception:
        pass
        
    # Check WindowsApps directory if PATH doesn't have it yet
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    if local_app_data:
        winget_path = os.path.join(local_app_data, "Microsoft", "WindowsApps", "winget.exe")
        if os.path.exists(winget_path):
            try:
                proc = subprocess.run(
                    [winget_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=creationflags
                )
                if proc.returncode == 0:
                    return True, proc.stdout.strip()
            except Exception:
                pass

    return False, "Winget not found on system"


def download_file_with_progress(url: str, dest_path: str, label: str, log_callback=None):
    """
    Downloads a file streaming progress updates to log_callback.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 InstallOrNot/2.0"})
    with urllib.request.urlopen(req, timeout=30) as response, open(dest_path, "wb") as out_file:
        total_size = int(response.headers.get("Content-Length", 0))
        downloaded = 0
        block_size = 1024 * 64
        last_logged_mb = 0

        while True:
            chunk = response.read(block_size)
            if not chunk:
                break
            out_file.write(chunk)
            downloaded += len(chunk)
            
            curr_mb = downloaded / (1024 * 1024)
            if total_size > 0:
                pct = int((downloaded / total_size) * 100)
                tot_mb = total_size / (1024 * 1024)
                if curr_mb - last_logged_mb >= 5 or pct == 100:
                    if log_callback:
                        log_callback(f"[WINGET BOOTSTRAP] {label}: {curr_mb:.1f} MB / {tot_mb:.1f} MB ({pct}%)\n")
                    last_logged_mb = curr_mb
            else:
                if curr_mb - last_logged_mb >= 5:
                    if log_callback:
                        log_callback(f"[WINGET BOOTSTRAP] {label}: {curr_mb:.1f} MB downloaded...\n")
                    last_logged_mb = curr_mb


def bootstrap_winget_ltsc(log_callback=None, finished_callback=None):
    """
    Downloads and installs VCLibs, UI.Xaml, and DesktopAppInstaller bundle on LTSC / Enterprise Windows.
    Runs asynchronously in a background thread.
    """
    def _worker():
        temp_dir = os.path.join(os.environ.get("TEMP", os.getcwd()), "winget_ltsc_install")
        try:
            os.makedirs(temp_dir, exist_ok=True)
            if log_callback:
                log_callback(f"\n{'='*65}\n[WINGET BOOTSTRAP] INITIATING LTSC WINGET INSTALLATION\n{'='*65}\n")
                log_callback("[WINGET BOOTSTRAP] Staging directory: " + temp_dir + "\n")
                log_callback("[WINGET BOOTSTRAP] Fetching official Microsoft packages & dependencies...\n\n")

            vclibs_path = os.path.join(temp_dir, LTSC_DEPENDENCY_URLS["vclibs"]["name"])
            xaml_path = os.path.join(temp_dir, LTSC_DEPENDENCY_URLS["xaml"]["name"])
            bundle_path = os.path.join(temp_dir, LTSC_DEPENDENCY_URLS["bundle"]["name"])

            # 1. Download VCLibs
            if not os.path.exists(vclibs_path):
                if log_callback:
                    log_callback("--> Downloading VCLibs (UWP Desktop Runtime)...\n")
                download_file_with_progress(LTSC_DEPENDENCY_URLS["vclibs"]["url"], vclibs_path, "VCLibs", log_callback)

            # 2. Download XAML 2.8
            if not os.path.exists(xaml_path):
                if log_callback:
                    log_callback("--> Downloading Microsoft.UI.Xaml 2.8...\n")
                download_file_with_progress(LTSC_DEPENDENCY_URLS["xaml"]["url"], xaml_path, "UI.Xaml", log_callback)

            # 3. Download DesktopAppInstaller msixbundle
            if not os.path.exists(bundle_path):
                if log_callback:
                    log_callback("--> Downloading Winget DesktopAppInstaller Bundle (~217 MB)...\n")
                download_file_with_progress(LTSC_DEPENDENCY_URLS["bundle"]["url"], bundle_path, "AppInstaller Bundle", log_callback)

            if log_callback:
                log_callback("\n[WINGET BOOTSTRAP] All packages acquired. Registering with Windows AppX Subsystem...\n")

            creationflags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

            # Step A: Install VCLibs
            if log_callback:
                log_callback("--> Registering VCLibs package...\n")
            p1 = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f'Add-AppxPackage -Path "{vclibs_path}" -ForceUpdateFromAnyVersion -ErrorAction SilentlyContinue'],
                capture_output=True, text=True, creationflags=creationflags
            )

            # Step B: Install Xaml
            if log_callback:
                log_callback("--> Registering UI.Xaml package...\n")
            p2 = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", f'Add-AppxPackage -Path "{xaml_path}" -ForceUpdateFromAnyVersion -ErrorAction SilentlyContinue'],
                capture_output=True, text=True, creationflags=creationflags
            )

            # Step C: Install Main Winget Bundle
            if log_callback:
                log_callback("--> Registering Winget AppInstaller Bundle...\n")
            ps_cmd = f'Add-AppxPackage -Path "{bundle_path}" -DependencyPath "{vclibs_path}","{xaml_path}" -ForceUpdateFromAnyVersion'
            p3 = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd],
                capture_output=True, text=True, creationflags=creationflags
            )

            if p3.returncode != 0 and p3.stderr:
                if log_callback:
                    log_callback(f"[WINGET BOOTSTRAP WARNING] {p3.stderr.strip()}\n")

            # Verify Winget readiness
            ok, ver = is_winget_ready()
            if ok:
                msg = f"✔ Microsoft Winget successfully installed and verified! (Version: {ver})"
                if log_callback:
                    log_callback(f"\n[WINGET BOOTSTRAP] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg, ver)
            else:
                # Try adding WindowsApps to current user PATH
                local_app_data = os.environ.get("LOCALAPPDATA", "")
                win_apps = os.path.join(local_app_data, "Microsoft", "WindowsApps")
                if win_apps not in os.environ.get("PATH", ""):
                    os.environ["PATH"] = win_apps + os.pathsep + os.environ.get("PATH", "")
                
                ok2, ver2 = is_winget_ready()
                if ok2:
                    msg = f"✔ Microsoft Winget successfully installed and registered! (Version: {ver2})"
                    if log_callback:
                        log_callback(f"\n[WINGET BOOTSTRAP] {msg}\n")
                    if finished_callback:
                        finished_callback(True, msg, ver2)
                else:
                    msg = "⚠ Packages installed, but winget command is not yet in current session PATH. A sign-out or restart may be required."
                    if log_callback:
                        log_callback(f"\n[WINGET BOOTSTRAP] {msg}\n")
                    if finished_callback:
                        finished_callback(True, msg, "installed_reboot_recommended")

        except Exception as e:
            err = f"❌ Winget bootstrap installation failed: {str(e)}"
            if log_callback:
                log_callback(f"\n[WINGET BOOTSTRAP] {err}\n")
            if finished_callback:
                finished_callback(False, err, "")
        finally:
            # Clean up temp directory
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    t = threading.Thread(target=_worker, daemon=True)
    t.start()
    return t
