import ctypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

hProc = kernel32.OpenProcess(0x1000, False, 24016)
print("OpenProcess handle:", hProc)
if hProc:
    exit_code = ctypes.c_ulong()
    kernel32.GetExitCodeProcess(hProc, ctypes.byref(exit_code))
    print("Exit code:", exit_code.value)
    kernel32.CloseHandle(hProc)
