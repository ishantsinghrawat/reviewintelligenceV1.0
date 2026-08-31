import subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for s in ['scripts/analyze.py','scripts/generate_report.py']: subprocess.run([sys.executable,s],cwd=R,check=True)
