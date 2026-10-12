import sys
import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
dll_path = os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "qgis_gui.dll")
print(f"DLL Path: {dll_path}")
print(f"Exists: {os.path.exists(dll_path)}")
print(f"Size: {os.path.getsize(dll_path)}")

import ctypes
from ctypes import wintypes

# Read PE export table using ctypes / pure python
with open(dll_path, "rb") as f:
    data = f.read()

# Parse DOS header
e_lfanew = int.from_bytes(data[0x3C:0x40], "little")
print(f"PE Header offset: hex({hex(e_lfanew)})")

# Optional header (PE32+ 64-bit)
magic = int.from_bytes(data[e_lfanew+24:e_lfanew+26], "little")
print(f"Magic: {hex(magic)} (0x20b is PE32+)")

entry_point = int.from_bytes(data[e_lfanew+40:e_lfanew+44], "little")
image_base = int.from_bytes(data[e_lfanew+48:e_lfanew+56], "little")
print(f"Image Base: {hex(image_base)}, Entry Point: {hex(entry_point)}")

# Number of RvaAndSizes
num_rva = int.from_bytes(data[e_lfanew+132:e_lfanew+136], "little")
export_rva = int.from_bytes(data[e_lfanew+136:e_lfanew+140], "little")
export_size = int.from_bytes(data[e_lfanew+140:e_lfanew+144], "little")
print(f"Export table RVA: {hex(export_rva)}, size: {hex(export_size)}")

# Read section headers
num_sections = int.from_bytes(data[e_lfanew+6:e_lfanew+8], "little")
opt_header_size = int.from_bytes(data[e_lfanew+20:e_lfanew+22], "little")
sec_start = e_lfanew + 24 + opt_header_size

sections = []
for i in range(num_sections):
    sec_data = data[sec_start + i*40 : sec_start + (i+1)*40]
    name = sec_data[:8].rstrip(b'\x00').decode('latin1', errors='ignore')
    vsize = int.from_bytes(sec_data[8:12], 'little')
    va = int.from_bytes(sec_data[12:16], 'little')
    raw_size = int.from_bytes(sec_data[16:20], 'little')
    raw_ptr = int.from_bytes(sec_data[20:24], 'little')
    sections.append((name, va, vsize, raw_ptr, raw_size))
    print(f"Section {name}: VA={hex(va)}, VSize={hex(vsize)}, RawPtr={hex(raw_ptr)}")

def rva_to_offset(rva):
    for name, va, vsize, raw_ptr, raw_size in sections:
        if va <= rva < va + vsize:
            return raw_ptr + (rva - va)
    return None

target_rva = 0x0044dfbd
print(f"\nTarget Crash Offset: {hex(target_rva)}")
for name, va, vsize, raw_ptr, raw_size in sections:
    if va <= target_rva < va + vsize:
        print(f"Target is in section: {name} (base {hex(va)}, offset in section: {hex(target_rva - va)})")

# Find closest exported function before target_rva
exp_off = rva_to_offset(export_rva)
if exp_off:
    num_funcs = int.from_bytes(data[exp_off+20:exp_off+24], 'little')
    num_names = int.from_bytes(data[exp_off+24:exp_off+28], 'little')
    funcs_rva = int.from_bytes(data[exp_off+28:exp_off+32], 'little')
    names_rva = int.from_bytes(data[exp_off+32:exp_off+36], 'little')
    ord_rva = int.from_bytes(data[exp_off+36:exp_off+40], 'little')

    names_off = rva_to_offset(names_rva)
    ord_off = rva_to_offset(ord_rva)
    funcs_off = rva_to_offset(funcs_rva)

    exports = []
    for i in range(num_names):
        name_ptr_rva = int.from_bytes(data[names_off + i*4 : names_off + (i+1)*4], 'little')
        name_file_off = rva_to_offset(name_ptr_rva)
        name_str = data[name_file_off:data.find(b'\x00', name_file_off)].decode('latin1', errors='ignore')
        
        ord_val = int.from_bytes(data[ord_off + i*2 : ord_off + (i+1)*2], 'little')
        func_rva = int.from_bytes(data[funcs_off + ord_val*4 : funcs_off + (ord_val+1)*4], 'little')
        exports.append((func_rva, name_str))

    exports.sort()
    
    # Find functions closest to target_rva
    closest = [(rva, name) for rva, name in exports if rva <= target_rva]
    if closest:
        print("\nExported functions immediately preceding target:")
        for rva, name in closest[-5:]:
            print(f"  {hex(rva)} (+{hex(target_rva - rva)}): {name}")
    
    following = [(rva, name) for rva, name in exports if rva > target_rva]
    if following:
        print("\nExported functions immediately following target:")
        for rva, name in following[:5]:
            print(f"  {hex(rva)} (-{hex(rva - target_rva)}): {name}")
