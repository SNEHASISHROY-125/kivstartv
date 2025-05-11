import sys
import os

# nessecery to run the fastapi server | otherwise it will not work

# Determine a user-writable directory for the log file
log_dir = os.getenv('LOCALAPPDATA', os.path.expanduser('~'))
log_file = os.path.join(log_dir, 'KivstarTV', 'app.log')

# Ensure the directory exists
os.makedirs(os.path.dirname(log_file), exist_ok=True)

# Redirect output to the log file
sys.stdout = open(log_file, "a", buffering=1)
sys.stderr = open(log_file, "a", buffering=1)
