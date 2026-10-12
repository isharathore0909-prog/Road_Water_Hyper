import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
dll_path = os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "qgis_gui.dll")

with open(dll_path, "rb") as f:
    data = f.read()

# Search for references to RVA 0x44df50.
# In x64:
# 1. Function pointers in vtables: 8-byte absolute address (ImageBase 0x180000000 + 0x44df50 = 0x18044df50)
target_va = 0x18044df50
va_bytes = target_va.to_bytes(8, 'little')

print(f"Searching for vtable references to {hex(target_va)}...")
pos = 0
vtable_refs = []
while True:
    idx = data.find(va_bytes, pos)
    if idx == -1:
        break
    vtable_refs.append(idx)
    pos = idx + 1

print(f"Found {len(vtable_refs)} vtable references to {hex(target_va)}:")
for r in vtable_refs:
    rva = 0x1000 + (r - 0x400) if r >= 0x400 else r
    print(f"  File offset: {hex(r)}, RVA: {hex(rva)}")

# What vtable is that?
# Let's inspect the symbols around those vtable references!
for r in vtable_refs:
    # Read the surrounding pointers in the vtable
    print(f"\nExamining table at file offset {hex(r)}:")
    for offset in range(-32, 40, 8):
        ptr = int.from_bytes(data[r + offset : r + offset + 8], 'little')
        ptr_rva = ptr - 0x180000000 if ptr >= 0x180000000 else ptr
        print(f"    [{'+' if offset >= 0 else ''}{offset}]: {hex(ptr)} (RVA: {hex(ptr_rva)})")
