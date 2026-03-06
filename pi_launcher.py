import os
import sys
import subprocess

# 1. CRITICAL: Set hardware fix BEFORE any other imports
os.environ['OPENBLAS_CORETYPE'] = 'generic'
os.environ['OMP_NUM_THREADS'] = '1' # Reduces threading overhead on Pi

def bootstrap_venv():
    """Ensures this script is running using the project's virtual environment."""
    venv_python = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend', 'venv', 'bin', 'python3'))
    if sys.executable != venv_python and os.path.exists(venv_python):
        print("🐍 Switching to Virtual Environment context...")
        os.execv(venv_python, [venv_python] + sys.argv)

def check_root():
    if os.getuid() != 0:
        print("❌ Error: ROOT privileges required. Run as: sudo python3 pi_launcher.py")
        sys.exit(1)

def diagnose_hardware_compat():
    """Pinpoints which library is causing the 'Illegal instruction'."""
    print("🔍 Running Granular Hardware Diagnostics...")
    libs = ['numpy', 'pandas', 'scipy', 'torch']
    for lib in libs:
        try:
            print(f"  - Testing {lib}...", end=" ", flush=True)
            # We run a separate process to catch the SIGILL crash immediately
            result = subprocess.run([sys.executable, "-c", f"import {lib}"], capture_output=True, timeout=10)
            if result.returncode != 0:
                print("❌ CRASHED (Illegal Instruction)")
                return lib
            print("✅ OK")
        except Exception:
            print("❌ TIMEOUT/ERROR")
            return lib
    return None

def apply_hardware_tweaks():
    try:
        cmd = "ip -o link show | awk '{print $2}' | grep -v 'lo' | head -n 1 | cut -d':' -f1"
        interface = subprocess.check_output(cmd, shell=True).decode().strip()
        if interface:
            print(f"🚀 Optimizing Hardware Interface: {interface}")
            subprocess.run(["ip", "link", "set", interface, "promisc", "on"], check=False)
            subprocess.run(["ethtool", "-K", interface, "gro", "off"], check=False)
    except Exception: pass

def launch(safe_mode=False):
    print("🛡️  Initializing Ghost Operators NIDS Appliance...")
    
    # Add backend to path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend'))
    sys.path.append(backend_path)

    if safe_mode:
        print("⚠️  SAFE MODE ACTIVE: ML/DL Engines DISABLED due to hardware incompatibility.")
        os.environ['NIDS_SAFE_MODE'] = 'true'
    else:
        os.environ['NIDS_SAFE_MODE'] = 'false'

    try:
        from app.main import app
        import uvicorn
        from app.utils.config import settings
        
        print(f"⚡ LAUNCHING NIDS CORE on http://{settings.API_HOST}:{settings.API_PORT}")
        uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
        
    except Exception as e:
        print(f"\n❌ Critical System Failure: {e}")
        print("💡 Your hardware might be crashing inside the main app. Try running in SAFE MODE.")

if __name__ == "__main__":
    bootstrap_venv()
    check_root()
    
    print("==================================================")
    print("🤖 GHOST OPERATORS: RASPBERRY PI BOOT SEQUENCE")
    print("==================================================")
    
    failing_lib = diagnose_hardware_compat()
    
    if failing_lib:
        print(f"\n🚨 HARDWARE ALERT: Your Pi's CPU cannot run the '{failing_lib}' library.")
        print(f"💡 This is common on 32-bit OS or older ARMv7 models.")
        print("❓ Auto-enabling SAFE MODE (Signature-only defense). Proceed? [Y/n]")
        choice = input().lower()
        if choice in ['', 'y', 'yes']:
            apply_hardware_tweaks()
            launch(safe_mode=True)
        else:
            print("❌ Execution aborted.")
            sys.exit(1)
    else:
        print("\n✅ All hardware libraries verified. No 'Illegal Instruction' detected.")
        apply_hardware_tweaks()
        launch(safe_mode=False)
