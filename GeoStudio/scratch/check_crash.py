import pefile

dll_path = r"C:\Program Files\QGIS 3.44.15\apps\qgis-ltr\bin\qgis_gui.dll"
pe = pefile.PE(dll_path)
print("Base:", hex(pe.OPTIONAL_HEADER.ImageBase))
for s in pe.sections:
    name = s.Name.decode().strip('\x00')
    va = s.VirtualAddress
    sz = s.Misc_VirtualSize
    if va <= 0x44dfbd < va + sz:
        print(f"Offset 0x44dfbd is in section {name} (VA 0x{va:x} - 0x{va+sz:x})")

# Look at exports near 0x44dfbd
closest = None
closest_dist = 99999999
for exp in pe.DIRECTORY_ENTRY_EXPORT.symbols:
    if exp.address and exp.address <= 0x44dfbd:
        dist = 0x44dfbd - exp.address
        if dist < closest_dist:
            closest_dist = dist
            closest = exp

if closest:
    name = closest.name.decode() if closest.name else "ordinal " + str(closest.ordinal)
    print(f"Closest export: {name} at 0x{closest.address:x} (offset +{closest_dist})")
