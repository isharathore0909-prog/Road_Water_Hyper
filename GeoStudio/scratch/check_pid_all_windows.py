import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

pid_target = 24016
found = []

def enum_all(hwnd, lparam):
    pid = wintypes.DWORD()
    tid = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == pid_target:
        found.append((hwnd, tid))
    return True

cb = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)(enum_all)
user32.EnumWindows(cb, 0)
print(f"Total windows found for PID {pid_target}: {len(found)}")
for hwnd, tid in found:
    length = user32.GetWindowTextLengthW(hwnd)
    buff = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buff, length + 1)
    vis = user32.IsWindowVisible(hwnd)
    clsname = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, clsname, 256)
    print(f"HWND {hwnd:#x} TID={tid}: class='{clsname.value}' text='{buff.value}' visible={bool(vis)}")
