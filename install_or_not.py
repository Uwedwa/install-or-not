# install_or_not.py
# Copyright (C) 2025-2026 uwedwa
# This program is licensed under the terms of the GNU General Public License v3.0.
# See https://www.gnu.org/licenses/gpl-3.0.html for details.
#
# INSTALL OR NOT 2.0 — Tactical Package Deployment Suite (PyWebView Edition)

import os
import sys
import webview
from app_api import TacticalBridge

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath(os.path.dirname(__file__)), relative_path)

def create_main_window():
    ui_dir = get_resource_path("ui")
    index_html = os.path.join(ui_dir, "index.html")

    if not os.path.exists(index_html):
        raise FileNotFoundError(f"CRITICAL: UI entry point not found at: {index_html}")

    # Ensure installers folder exists in the working directory
    installers_dir = os.path.join(os.getcwd(), "installers")
    os.makedirs(installers_dir, exist_ok=True)

    bridge = TacticalBridge(installers_dir=installers_dir)

    window = webview.create_window(
        title="INSTALL OR NOT 2.0 — Tactical Deployment Suite",
        url=index_html,
        js_api=bridge,
        width=1160,
        height=780,
        min_size=(960, 680),
        background_color="#080b10",
        easy_drag=False
    )
    bridge._set_window(window)

    # Start PyWebView loop (native Windows Edge Chromium WebView2 engine)
    webview.start(debug=False)

if __name__ == "__main__":
    create_main_window()
