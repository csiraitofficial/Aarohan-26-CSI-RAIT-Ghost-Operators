import os
import sys
import subprocess

# 1. CRITICAL: Set hardware fix BEFORE any other imports
# This prevents 'Illegal instruction' crashes in NumPy/Torch
os.environ['OPENBLAS_CORETYPE'] = 'generic'

def bootstrap_venv():
    """Ensures this script is running using the project's virtual environment."""
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'venv', 'bin', 'python3'))
    
    # If we are not in the venv, re-execute the script using the venv's python
    if sys.executable != venv_python and os.path.exists(venv_python):
        print("� Switching to Virtual Environment context...")
        os.execv(venv_python, [venv_python] + sys.argv)

def check_root():
    """Ensures the script is running with root privileges (required for packet capture)."""
    if os.getuid() != 0:
        print("❌ Error: {O.S.I.R.I.S} NIDS requires ROOT privileges to capture network traffic.")
        print("💡 Please run as: sudo python3 pi_launcher.py")
        sys.exit(1)

def apply_hardware_tweaks():
    """Optimizes the Raspberry Pi network interface."""
    try:
        # Auto-detect first active network interface (wlan0 or eth0)
        cmd = "ip -o link show | awk '{print $2}' | grep -v 'lo' | head -n 1 | cut -d':' -f1"
        interface = subprocess.check_output(cmd, shell=True).decode().strip()
        
        if interface:
            print(f"🚀 Optimizing Hardware Interface: {interface}")
            subprocess.run(["ip", "link", "set", interface, "promisc", "on"], check=False)
            subprocess.run(["ethtool", "-K", interface, "gro", "off"], check=False)
    except Exception:
        pass # Fails silently if net-tools are missing

def launch():
    print("🛡️ Initializing Ghost Operators NIDS Appliance...")
    print("✅ Hardware Protection Active: Generic ARM Mode")

    # Add backend to path for imports
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
    sys.path.append(backend_path)

    try:
        import uvicorn
        from app.main import app
        from app.utils.config import settings
        
        print(f"⚡ LAUNCHING NIDS CORE on http://{settings.API_HOST}:{settings.API_PORT}")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except ImportError as e:
        print(f"❌ Error: Missing dependencies. Run sudo ./pi_setup_and_run.sh first. ({e})")
    except Exception as e:
        print(f"❌ Critical System Failure: {e}")

if __name__ == "__main__":
    bootstrap_venv()
    check_root()
    apply_hardware_tweaks()
    launch()
