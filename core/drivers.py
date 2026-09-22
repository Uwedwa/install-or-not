"""
core/drivers.py - Driver Vault: Native Windows Driver Backup & Restore Engine
Part of Install or Not 2.0
"""

import os
import subprocess
import threading
import glob

def get_backup_stats(directory: str) -> dict:
    """
    Inspects a directory to find backed up driver packages (.inf files).
    Returns count and total size in MB.
    """
    if not os.path.exists(directory):
        return {"exists": False, "count": 0, "size_mb": 0.0, "inf_files": []}
    
    inf_files = []
    total_bytes = 0
    for root, _, files in os.walk(directory):
        for f in files:
            full_path = os.path.join(root, f)
            try:
                total_bytes += os.path.getsize(full_path)
            except OSError:
                pass
            if f.lower().endswith(".inf"):
                inf_files.append(full_path)
                
    return {
        "exists": True,
        "count": len(inf_files),
        "size_mb": round(total_bytes / (1024 * 1024), 2),
        "inf_files": inf_files
    }

def backup_drivers(dest_dir: str, log_callback=None, finished_callback=None):
    """
    Exports all third-party Windows drivers to dest_dir using dism.exe /export-driver.
    Runs asynchronously in a background thread.
    """
    def _worker():
        try:
            os.makedirs(dest_dir, exist_ok=True)
            if log_callback:
                log_callback(f"[DRIVER VAULT] Starting driver export to: {dest_dir}\n")
                log_callback("[DRIVER VAULT] Invoking Windows DISM OEM Driver Export Engine...\n")
                
            cmd = ["dism.exe", "/online", "/export-driver", f"/destination:{dest_dir}"]
            
            # Use CREATE_NO_WINDOW if on Windows
            startupinfo = None
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
            
            exported_count = 0
            for line in process.stdout:
                if line.strip():
                    if log_callback:
                        log_callback(line)
                    if "Exporting" in line or ".inf" in line.lower():
                        exported_count += 1
                        
            process.wait()
            
            stats = get_backup_stats(dest_dir)
            total_infs = stats["count"]
            total_mb = stats["size_mb"]
            
            if process.returncode == 0:
                msg = f"✔ Driver export successful! {total_infs} driver packages saved ({total_mb} MB)."
                if log_callback:
                    log_callback(f"\n[DRIVER VAULT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg, stats)
            else:
                msg = f"❌ Driver export exited with code {process.returncode}."
                if log_callback:
                    log_callback(f"\n[DRIVER VAULT] {msg}\n")
                if finished_callback:
                    finished_callback(False, msg, stats)
                    
        except Exception as e:
            err_msg = f"❌ Driver export failed: {str(e)}"
            if log_callback:
                log_callback(f"\n[DRIVER VAULT] {err_msg}\n")
            if finished_callback:
                finished_callback(False, err_msg, None)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread

def restore_drivers(source_dir: str, log_callback=None, finished_callback=None):
    """
    Restores and installs all .inf drivers from source_dir using pnputil.exe.
    Runs asynchronously in a background thread.
    """
    def _worker():
        try:
            if not os.path.exists(source_dir):
                err_msg = f"❌ Source directory does not exist: {source_dir}"
                if log_callback:
                    log_callback(f"[DRIVER VAULT] {err_msg}\n")
                if finished_callback:
                    finished_callback(False, err_msg, 0)
                return
                
            stats = get_backup_stats(source_dir)
            if stats["count"] == 0:
                err_msg = f"❌ No .inf driver packages found in: {source_dir}"
                if log_callback:
                    log_callback(f"[DRIVER VAULT] {err_msg}\n")
                if finished_callback:
                    finished_callback(False, err_msg, 0)
                return
                
            if log_callback:
                log_callback(f"[DRIVER VAULT] Found {stats['count']} driver packages ({stats['size_mb']} MB).\n")
                log_callback("[DRIVER VAULT] Launching Windows PnP Driver Installer (pnputil.exe)...\n")
                log_callback("[DRIVER VAULT] Please wait, this process may take 1-3 minutes depending on driver sizes.\n\n")

            pattern = os.path.join(source_dir, "*.inf")
            cmd = ["pnputil.exe", "/add-driver", pattern, "/subdirs", "/install"]
            
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NO_WINDOW
                
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags
            )
            
            installed_count = 0
            for line in process.stdout:
                if line.strip():
                    if log_callback:
                        log_callback(line)
                    if "Driver package added successfully" in line or "başarıyla eklendi" in line.lower() or "installed" in line.lower():
                        installed_count += 1
                        
            process.wait()
            
            # pnputil returns 0 or 3010 (3010 = ERROR_SUCCESS_REBOOT_REQUIRED)
            if process.returncode in (0, 3010):
                reboot_note = " (A system restart is recommended to finalize installation)" if process.returncode == 3010 else ""
                msg = f"✔ Driver installation completed!{reboot_note}"
                if log_callback:
                    log_callback(f"\n[DRIVER VAULT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg, stats["count"])
            else:
                msg = f"⚠ Driver restoration finished with code {process.returncode}."
                if log_callback:
                    log_callback(f"\n[DRIVER VAULT] {msg}\n")
                if finished_callback:
                    finished_callback(True, msg, stats["count"])
                    
        except Exception as e:
            err_msg = f"❌ Driver installation failed: {str(e)}"
            if log_callback:
                log_callback(f"\n[DRIVER VAULT] {err_msg}\n")
            if finished_callback:
                finished_callback(False, err_msg, 0)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    return thread
