#!/usr/bin/env python3
"""
Desktop Shortcut Creator for Stock Market Monitor
Creates desktop shortcuts and launchers for all platforms
"""

import os
import sys
import platform
import shutil
from pathlib import Path
import tempfile
import subprocess

def get_platform():
    """Get the current platform."""
    return platform.system().lower()

def get_install_dir():
    """Get the installation directory."""
    return Path(__file__).parent.parent.absolute()

def create_windows_shortcuts():
    """Create Windows desktop shortcuts and start menu entries."""
    install_dir = get_install_dir()
    desktop = Path.home() / "Desktop"
    start_menu = Path.home() / "AppData" / "Roaming" / "Microsoft" / "Windows" / "Start Menu" / "Programs"
    
    # Create shortcuts directory
    shortcuts_dir = start_menu / "Stock Monitor"
    shortcuts_dir.mkdir(exist_ok=True)
    
    shortcuts = [
        {
            "name": "Stock Monitor",
            "target": str(install_dir / "scripts" / "windows" / "start_monitor.bat"),
            "description": "Start the 24/7 Stock Market Monitor",
            "icon": "",
            "desktop": True,
            "start_menu": True
        },
        {
            "name": "Stock Dashboard",
            "target": str(install_dir / "scripts" / "windows" / "open_dashboard.bat"),
            "description": "Open Stock Monitor Dashboard in Browser",
            "icon": "",
            "desktop": True,
            "start_menu": True
        },
        {
            "name": "Grafana Dashboard",
            "target": str(install_dir / "scripts" / "windows" / "open_grafana.bat"),
            "description": "Open Grafana Analytics Dashboard",
            "icon": "",
            "desktop": False,
            "start_menu": True
        },
        {
            "name": "Start with Docker",
            "target": str(install_dir / "scripts" / "windows" / "start_docker.bat"),
            "description": "Start Stock Monitor using Docker",
            "icon": "",
            "desktop": False,
            "start_menu": True
        },
        {
            "name": "Service Manager",
            "target": str(install_dir / "scripts" / "windows" / "service" / "manage_service.bat"),
            "description": "Manage Stock Monitor Windows Service",
            "icon": "",
            "desktop": False,
            "start_menu": True
        }
    ]
    
    created_shortcuts = []
    
    for shortcut in shortcuts:
        # Create PowerShell script to create shortcuts
        ps_script = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{shortcuts_dir / (shortcut['name'] + '.lnk')}")
$Shortcut.TargetPath = "{shortcut['target']}"
$Shortcut.WorkingDirectory = "{install_dir}"
$Shortcut.Description = "{shortcut['description']}"
$Shortcut.Save()
'''
        
        # Execute PowerShell script
        try:
            subprocess.run(["powershell", "-Command", ps_script], check=True, capture_output=True)
            created_shortcuts.append(f"Start Menu: {shortcut['name']}")
        except:
            print(f"⚠ Failed to create start menu shortcut: {shortcut['name']}")
        
        # Create desktop shortcut if requested
        if shortcut['desktop']:
            ps_script_desktop = f'''
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("{desktop / (shortcut['name'] + '.lnk')}")
$Shortcut.TargetPath = "{shortcut['target']}"
$Shortcut.WorkingDirectory = "{install_dir}"
$Shortcut.Description = "{shortcut['description']}"
$Shortcut.Save()
'''
            try:
                subprocess.run(["powershell", "-Command", ps_script_desktop], check=True, capture_output=True)
                created_shortcuts.append(f"Desktop: {shortcut['name']}")
            except:
                print(f"⚠ Failed to create desktop shortcut: {shortcut['name']}")
    
    return created_shortcuts

def create_macos_shortcuts():
    """Create macOS shortcuts and aliases."""
    install_dir = get_install_dir()
    applications_dir = Path.home() / "Applications"
    desktop = Path.home() / "Desktop"
    
    # Create Applications directory shortcuts
    stock_monitor_dir = applications_dir / "Stock Monitor"
    stock_monitor_dir.mkdir(exist_ok=True)
    
    shortcuts = [
        {
            "name": "Start Stock Monitor.command",
            "script": f'''#!/bin/bash
cd "{install_dir}"
source venv/bin/activate
python src/main.py
''',
            "location": "applications"
        },
        {
            "name": "Open Dashboard.command",
            "script": f'''#!/bin/bash
open http://localhost:8080
''',
            "location": "both"
        },
        {
            "name": "Open Grafana.command",
            "script": f'''#!/bin/bash
open http://localhost:3000
''',
            "location": "applications"
        },
        {
            "name": "Start with Docker.command",
            "script": f'''#!/bin/bash
cd "{install_dir}"
docker-compose -f docker-compose.desktop.yml up -d
echo "Services started. Dashboard: http://localhost:8080"
read -p "Press Enter to continue..."
''',
            "location": "applications"
        }
    ]
    
    created_shortcuts = []
    
    for shortcut in shortcuts:
        # Create in Applications
        if shortcut['location'] in ['applications', 'both']:
            app_file = stock_monitor_dir / shortcut['name']
            with open(app_file, 'w') as f:
                f.write(shortcut['script'])
            os.chmod(app_file, 0o755)
            created_shortcuts.append(f"Applications: {shortcut['name']}")
        
        # Create on Desktop
        if shortcut['location'] in ['desktop', 'both']:
            desktop_file = desktop / shortcut['name']
            with open(desktop_file, 'w') as f:
                f.write(shortcut['script'])
            os.chmod(desktop_file, 0o755)
            created_shortcuts.append(f"Desktop: {shortcut['name']}")
    
    # Add shell aliases
    shell_files = [
        Path.home() / ".zshrc",
        Path.home() / ".bash_profile",
        Path.home() / ".bashrc"
    ]
    
    aliases = f'''
# Stock Monitor Aliases
alias stock-monitor='cd "{install_dir}" && source venv/bin/activate && python src/main.py'
alias stock-dashboard='open http://localhost:8080'
alias stock-grafana='open http://localhost:3000'
alias stock-docker='cd "{install_dir}" && docker-compose -f docker-compose.desktop.yml up -d'
alias stock-logs='cd "{install_dir}" && tail -f logs/stock_monitor.log'
'''
    
    for shell_file in shell_files:
        if shell_file.exists():
            with open(shell_file, 'a') as f:
                f.write(aliases)
            created_shortcuts.append(f"Aliases added to {shell_file.name}")
            break
    
    return created_shortcuts

def create_linux_shortcuts():
    """Create Linux desktop entries and shortcuts."""
    install_dir = get_install_dir()
    desktop_dir = Path.home() / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    desktop_files = [
        {
            "filename": "stock-monitor.desktop",
            "content": f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Market Monitor
Comment=24/7 Global Stock Market Monitoring System
Exec={install_dir}/scripts/linux/start_monitor.sh
Icon=utilities-system-monitor
Terminal=true
Categories=Office;Finance;
StartupWMClass=stock-monitor
'''
        },
        {
            "filename": "stock-dashboard.desktop",
            "content": f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Monitor Dashboard
Comment=Open Stock Monitor Web Dashboard
Exec=xdg-open http://localhost:8080
Icon=web-browser
Terminal=false
Categories=Office;Finance;Network;
'''
        },
        {
            "filename": "stock-grafana.desktop",
            "content": f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Grafana Dashboard
Comment=Open Grafana Analytics Dashboard
Exec=xdg-open http://localhost:3000
Icon=web-browser
Terminal=false
Categories=Office;Finance;Network;
'''
        },
        {
            "filename": "stock-docker.desktop",
            "content": f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Stock Monitor (Docker)
Comment=Start Stock Monitor using Docker
Exec={install_dir}/scripts/linux/start_docker.sh
Icon=docker
Terminal=true
Categories=Office;Finance;System;
'''
        }
    ]
    
    created_shortcuts = []
    
    for desktop_file in desktop_files:
        file_path = desktop_dir / desktop_file['filename']
        with open(file_path, 'w') as f:
            f.write(desktop_file['content'])
        os.chmod(file_path, 0o755)
        created_shortcuts.append(f"Desktop Entry: {desktop_file['filename']}")
    
    # Update desktop database
    try:
        subprocess.run(["update-desktop-database", str(desktop_dir)], check=True, capture_output=True)
        created_shortcuts.append("Desktop database updated")
    except:
        pass
    
    # Add shell aliases
    shell_files = [
        Path.home() / ".bashrc",
        Path.home() / ".zshrc",
        Path.home() / ".profile"
    ]
    
    aliases = f'''
# Stock Monitor Aliases
alias stock-monitor='cd "{install_dir}" && source venv/bin/activate && python src/main.py'
alias stock-dashboard='xdg-open http://localhost:8080'
alias stock-grafana='xdg-open http://localhost:3000'
alias stock-docker='cd "{install_dir}" && docker-compose -f docker-compose.desktop.yml up -d'
alias stock-logs='cd "{install_dir}" && tail -f logs/stock_monitor.log'
alias stock-status='cd "{install_dir}" && systemctl --user status stock-monitor'
'''
    
    for shell_file in shell_files:
        if shell_file.exists():
            with open(shell_file, 'a') as f:
                f.write(aliases)
            created_shortcuts.append(f"Aliases added to {shell_file.name}")
            break
    
    return created_shortcuts

def create_quick_access_scripts():
    """Create quick access scripts for all platforms."""
    install_dir = get_install_dir()
    platform_name = get_platform()
    
    if platform_name == "windows":
        scripts_dir = install_dir / "scripts" / "windows"
        scripts_dir.mkdir(exist_ok=True)
        
        # Quick status script
        status_script = f'''@echo off
echo Stock Monitor System Status
echo ================================
echo.

echo Checking services...
sc query StockMonitor >nul 2>&1
if %errorLevel% equ 0 (
    echo ✓ Windows Service: Installed
    for /f "tokens=3" %%a in ('sc query StockMonitor ^| find "STATE"') do echo   Status: %%a
) else (
    echo ✗ Windows Service: Not installed
)

echo.
echo Checking processes...
tasklist /fi "imagename eq python.exe" /fo csv | find "python.exe" >nul
if %errorLevel% equ 0 (
    echo ✓ Python processes running
) else (
    echo ✗ No Python processes found
)

echo.
echo Checking ports...
netstat -an | find ":8080" >nul
if %errorLevel% equ 0 (
    echo ✓ Dashboard port 8080: Active
) else (
    echo ✗ Dashboard port 8080: Not active
)

netstat -an | find ":3000" >nul
if %errorLevel% equ 0 (
    echo ✓ Grafana port 3000: Active
) else (
    echo ✗ Grafana port 3000: Not active
)

echo.
echo Quick Actions:
echo   [1] Open Dashboard: scripts\\windows\\open_dashboard.bat
echo   [2] View Logs: type logs\\stock_monitor.log
echo   [3] Restart Service: net stop StockMonitor ^&^& net start StockMonitor
echo.
pause
'''
        with open(scripts_dir / "status.bat", 'w') as f:
            f.write(status_script)
        
        return ["Windows status script created"]
    
    else:
        scripts_dir = install_dir / "scripts" / platform_name
        scripts_dir.mkdir(exist_ok=True)
        
        # Quick status script
        status_script = f'''#!/bin/bash
echo "Stock Monitor System Status"
echo "================================"
echo

echo "Checking processes..."
if pgrep -f "src/main.py" > /dev/null; then
    echo "✓ Stock Monitor process: Running"
    echo "  PID: $(pgrep -f 'src/main.py')"
else
    echo "✗ Stock Monitor process: Not running"
fi

echo
echo "Checking ports..."
if lsof -i :8080 > /dev/null 2>&1; then
    echo "✓ Dashboard port 8080: Active"
else
    echo "✗ Dashboard port 8080: Not active"
fi

if lsof -i :3000 > /dev/null 2>&1; then
    echo "✓ Grafana port 3000: Active"
else
    echo "✗ Grafana port 3000: Not active"
fi

echo
echo "Checking services..."
if systemctl --user is-active stock-monitor > /dev/null 2>&1; then
    echo "✓ Systemd service: $(systemctl --user is-active stock-monitor)"
else
    echo "✗ Systemd service: Not configured or inactive"
fi

echo
echo "Quick Actions:"
echo "  Open Dashboard: {platform_name}/open_dashboard.sh"
echo "  View Logs: tail -f logs/stock_monitor.log"
echo "  Restart: systemctl --user restart stock-monitor"
echo
'''
        status_file = scripts_dir / "status.sh"
        with open(status_file, 'w') as f:
            f.write(status_script)
        os.chmod(status_file, 0o755)
        
        return [f"{platform_name.title()} status script created"]

def main():
    """Main function to create shortcuts for the current platform."""
    platform_name = get_platform()
    
    print(f"Creating desktop shortcuts for {platform_name.title()}...")
    print()
    
    created_shortcuts = []
    
    try:
        if platform_name == "windows":
            created_shortcuts.extend(create_windows_shortcuts())
        elif platform_name == "darwin":
            created_shortcuts.extend(create_macos_shortcuts())
        elif platform_name == "linux":
            created_shortcuts.extend(create_linux_shortcuts())
        else:
            print(f"Unsupported platform: {platform_name}")
            return
        
        # Create quick access scripts for all platforms
        created_shortcuts.extend(create_quick_access_scripts())
        
        print("✓ Shortcuts created successfully!")
        print()
        print("Created shortcuts:")
        for shortcut in created_shortcuts:
            print(f"  - {shortcut}")
        
        print()
        print("Quick access:")
        if platform_name == "windows":
            print("  - Check Start Menu > Stock Monitor")
            print("  - Look for desktop shortcuts")
            print("  - Run: scripts\\windows\\status.bat")
        elif platform_name == "darwin":
            print("  - Check Applications > Stock Monitor")
            print("  - Use terminal aliases (restart terminal first)")
            print("  - Run: ./scripts/macos/status.sh")
        else:
            print("  - Check Applications menu")
            print("  - Use terminal aliases (restart terminal first)")
            print("  - Run: ./scripts/linux/status.sh")
        
    except Exception as e:
        print(f"Error creating shortcuts: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())