import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
dll_path = os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "qgis_gui.dll")

with open(dll_path, "rb") as f:
    data = f.read()

# Target RVA is 0x44dfbd. In .text section (VA 0x1000, RawPtr 0x400):
file_offset = 0x400 + (0x44dfbd - 0x1000)

# Let's search backward for function prologue
# Common MSVC prologues:
# 48 89 5c 24 (mov [rsp+...], rbx)
# 48 83 ec (sub rsp, ...)
# 40 53 (push rbx)
# 40 55 (push rbp)
# 41 56 (push r14)
# 55 48 8b ec (push rbp; mov rbp, rsp)
# cc cc cc (int 3 padding before function)

for off in range(file_offset, file_offset - 1000, -1):
    if data[off:off+3] == b'\xcc\xcc\xcc':
        func_start = off + 3
        while data[func_start] == 0xcc:
            func_start += 1
        func_rva = 0x1000 + (func_start - 0x400)
        print(f"Function start detected at file offset {hex(func_start)}, RVA: {hex(func_rva)}")
        print(f"Prologue bytes: {data[func_start:func_start+16].hex()}")
        break
