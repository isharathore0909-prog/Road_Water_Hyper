import subprocess

cmd = [r"C:\Program Files\QGIS 3.44.15\bin\python-qgis-ltr.bat", r"M:\Geo Studio\GeoStudio\app\main.py", "--test-autoclose"]
proc = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", proc.stdout)
print("STDERR:\n", proc.stderr)
print("RETURNCODE:", proc.returncode)
