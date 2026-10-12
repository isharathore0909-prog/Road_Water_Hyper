import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
dll_path = os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "qgis_gui.dll")

with open(dll_path, "rb") as f:
    data = f.read()

# Vtable is at file offset 0xacae08
# In MSVC 64-bit, vtable[-1] is at offset 0xacae08 - 8 = 0xacae00.
# It holds the 64-bit pointer or 32-bit RVA to RTTICompleteObjectLocator.
# Let's inspect the 8 bytes right before the vtable:
col_ptr = int.from_bytes(data[0xacae08 - 8 : 0xacae08], 'little')
print(f"RTTI Complete Object Locator VA: {hex(col_ptr)}")

col_off = 0x400 + ((col_ptr - 0x180000000) - 0x1000)
print(f"COL file offset: {hex(col_off)}")

# In RTTICompleteObjectLocator (64-bit):
# offset 0: signature (int32)
# offset 4: offset (int32)
# offset 8: cdOffset (int32)
# offset 12: typeDescriptor RVA (int32)
# offset 16: classDescriptor RVA (int32)
# offset 20: self RVA (int32)
type_desc_rva = int.from_bytes(data[col_off + 12 : col_off + 16], 'little')
type_desc_off = 0x400 + (type_desc_rva - 0x1000)
print(f"TypeDescriptor RVA: {hex(type_desc_rva)}, offset: {hex(type_desc_off)}")

# TypeDescriptor:
# offset 0: pVFTable (int64)
# offset 8: spare (int64)
# offset 16: name (mangled string, null terminated)
name = data[type_desc_off + 16 : data.find(b'\x00', type_desc_off + 16)].decode('latin1', errors='ignore')
print(f"\nExact C++ Class Name from RTTI: {name}")

# Demangle MSVC name
import ctypes
from ctypes import wintypes
dbghelp = ctypes.windll.dbghelp
buf = ctypes.create_string_buffer(256)
res = dbghelp.UnDecorateSymbolName(name.encode('ascii'), buf, 256, 0)
if res:
    print(f"Demangled Class Name: {buf.value.decode('latin1')}")
