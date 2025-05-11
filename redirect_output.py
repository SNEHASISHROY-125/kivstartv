import sys
import os

if sys.platform != "win32": 
    # For Linux/macOS: use ~/.local/share or just ~/
    log_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "KivstarTV")
else:
    log_dir = os.path.join(os.getenv("LOCALAPPDATA") or os.path.expanduser("~"), "KivstarTV")

os.makedirs(log_dir, exist_ok=True)
logfile = os.path.join(log_dir, "app.log")
# nessecery to run the fastapi server | otherwise it will not work

# logfile = os.path.join(os.path.dirname(sys.executable), "app.log")
sys.stdout = open(logfile, "a", buffering=1)
sys.stderr = open(logfile, "a", buffering=1)
