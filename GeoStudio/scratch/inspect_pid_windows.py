import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

pid_target = 24016

def enum_windows_callback(hwnd, extra):
    lpdw_process_id = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lpdw_process_id))
    if lpdw_process_id.value == pid_target:
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        is_vis = user32.IsWindowVisible(hwnd)
        rect = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        print(f"HWND {hwnd:#x}: title='{buff.value}', visible={bool(is_vis)}, rect=({rect.left}, {rect.top}, {rect.right}, {rect.bottom})")
    return True

WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
cb = WNDENUMPROC(enum_windows_callback)
user32.EnumWindows(cb, 0)
