import sys
import os

# nessecery to run the fastapi server | otherwise it will not work

logfile = os.path.join(os.path.dirname(sys.executable), "app.log")
sys.stdout = open(logfile, "a", buffering=1)
sys.stderr = open(logfile, "a", buffering=1)
