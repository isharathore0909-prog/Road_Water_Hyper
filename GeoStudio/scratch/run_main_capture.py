import subprocess, sys, time

cmd = [r"C:\Program Files\QGIS 3.44.15\bin\python-qgis-ltr.bat", r"M:\Geo Studio\GeoStudio\app\main.py"]
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(4)
poll = proc.poll()
print("Process poll after 4s:", poll)

# Read output so far
try:
    stdout, stderr = proc.communicate(timeout=2)
except subprocess.TimeoutExpired:
    stdout, stderr = "STILL RUNNING", ""
    proc.terminate()

print("STDOUT:\n", stdout)
print("STDERR:\n", stderr)
