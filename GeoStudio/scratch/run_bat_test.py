import subprocess

cmd = [r"M:\Geo Studio\GeoStudio\GeoStudio.bat", "--test-autoclose"]
proc = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:\n", proc.stdout)
print("STDERR:\n", proc.stderr)
print("RETURNCODE:", proc.returncode)
