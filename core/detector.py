"""
Install or Not - Tactical Package Deployment
Core: Smart Installer Engine Fingerprinting (Zero-Dependency)
Detects installer types (Inno, NSIS, InstallShield, WiX, MSI, etc.)
and generates targeted silent installation parameters.
"""

import os
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class InstallerProfile:
    name: str
    engine: str
    silent_args: List[str]
    confidence: str
    description: str

def analyze_installer(file_path: str) -> InstallerProfile:
    """
    Analyzes an executable or MSI file by inspecting its header,
    embedded strings, and binary markers to detect the packaging engine.
    """
    base_name = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".msi":
        return InstallerProfile(
            name=base_name,
            engine="Microsoft Installer (MSI)",
            silent_args=["/qn", "/norestart", "/passive"],
            confidence="High",
            description="Standard Windows Installer package"
        )

    if ext != ".exe":
        return InstallerProfile(
            name=base_name,
            engine="Unknown / Unsupported",
            silent_args=[],
            confidence="Low",
            description="Non-executable package format"
        )

    # Read binary chunks (first 512KB and last 64KB for embedded signatures)
    header_chunk = b""
    footer_chunk = b""
    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as f:
            header_chunk = f.read(min(524288, file_size))
            if file_size > 65536:
                f.seek(max(0, file_size - 65536))
                footer_chunk = f.read(65536)
    except Exception:
        pass

    combined_samples = header_chunk + footer_chunk

    # 1. Inno Setup Detection
    # Look for "Inno Setup", "Inno Setup Setup Data", "InnoSetup"
    if b"Inno Setup" in combined_samples or b"jr.inno.setup" in combined_samples or b"InnoSetup" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="Inno Setup",
            silent_args=["/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES", "/SP-"],
            confidence="High",
            description="Jordan Russell Inno Setup Installer"
        )

    # 2. NSIS (Nullsoft Scriptable Install System)
    # Look for "NullsoftInst", "Nullsoft.NSIS", "NSIS Error"
    if b"NullsoftInst" in combined_samples or b"Nullsoft.NSIS" in combined_samples or b"NSIS.Library" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="NSIS (Nullsoft)",
            silent_args=["/S"],
            confidence="High",
            description="Nullsoft Scriptable Install System (Case-sensitive /S)"
        )

    # 3. WiX / Burn (Windows Installer XML Bootstrapper)
    # Look for "WixBurn", "WixAttachedContainer", "BurnEngine"
    if b"WixBurn" in combined_samples or b"WixAttachedContainer" in combined_samples or b"wix.ca.dll" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="WiX Toolset Bootstrapper",
            silent_args=["/quiet", "/norestart"],
            confidence="High",
            description="WiX / Burn Bundle Installer"
        )

    # 4. InstallShield
    # Look for "InstallShield", "ISSetup.dll", "InstallShield Wizard"
    if b"InstallShield" in combined_samples or b"ISSetup" in combined_samples or b"InstallShield.Setup" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="InstallShield",
            silent_args=["/s", "/v/qn /norestart"],
            confidence="Medium",
            description="InstallShield Professional Setup"
        )

    # 5. Advanced Installer
    if b"Advanced Installer" in combined_samples or b"Caphyon" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="Advanced Installer",
            silent_args=["/exenoui", "/qn", "/norestart"],
            confidence="High",
            description="Caphyon Advanced Installer"
        )

    # 6. 7-Zip SFX
    if b"7-Zip" in combined_samples or header_chunk.startswith(b"7z\xbc\xaf\x27\x1c") or b"7zS.sfx" in combined_samples:
        return InstallerProfile(
            name=base_name,
            engine="7-Zip Self-Extracting",
            silent_args=["-y"],
            confidence="High",
            description="7-Zip Self-Extracting Archive"
        )

    # 7. Generic Fallback
    # Try conservative silent parameters that don't trigger syntax errors on common installers
    return InstallerProfile(
        name=base_name,
        engine="Generic Windows Executable",
        silent_args=["/quiet", "/norestart", "/S", "/silent"],
        confidence="Generic",
        description="Standard PE executable, using standard multi-flag probe"
    )
