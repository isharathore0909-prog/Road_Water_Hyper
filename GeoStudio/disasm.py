import os

qgis_root = r"C:\Program Files\QGIS 3.44.15"
dll_path = os.path.join(qgis_root, "apps", "qgis-ltr", "bin", "qgis_gui.dll")

with open(dll_path, "rb") as f:
    data = f.read()

# Target RVA is 0x44dfbd. In .text section (VA 0x1000, RawPtr 0x400):
file_offset = 0x400 + (0x44dfbd - 0x1000)
print(f"File offset for RVA 0x44dfbd: {hex(file_offset)}")

chunk = data[file_offset - 32 : file_offset + 32]
print(f"Bytes around offset:\n{chunk.hex()}")

# Try importing capstone or disassembler
try:
    import capstone
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    print("\nDisassembly:")
    for ins in md.disasm(data[file_offset - 32 : file_offset + 32], 0x18044dfbd - 32):
        marker = "===> " if ins.address == 0x18044dfbd else "     "
        print(f"{marker}0x{ins.address:x}: {ins.mnemonic} {ins.op_str}")
except ImportError:
    print("capstone not installed in python")
