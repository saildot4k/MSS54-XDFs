# MSS54 Checksum Compensator

A Python tool for restoring checksums in MSS54/MSS54HP ECU binary files after modifications, preserving the original CVN through intelligent compensation.

> **⚠️ IMPORTANT:** This tool is designed and tested for **32KB partial flash binaries only**. Use on full 512KB binaries is **UNTESTED** and **NOT RECOMMENDED**.

## Table of Contents

- [Quick Start](#quick-start)
- [What This Tool Does](#what-this-tool-does)
- [Installation](#installation)
- [Usage](#usage)
- [Real-World Examples](#real-world-examples)
- [Understanding Checksums](#understanding-checksums)
- [File Structure](#file-structure)
- [Tips & Best Practices](#tips--best-practices)
- [Troubleshooting](#troubleshooting)
- [Technical Details](#technical-details)

---

## Quick Start

```bash
# 1. Check your binary file
./checksum_compensator.py original.bin --info --show-zeros

# 2. Make your edits (hex editor, TunerPro, etc.)

# 3. Restore checksums to match original
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --output fixed.bin

# Done! CVN preserved, ECU happy 🎉
```

---

## What This Tool Does

### The Problem

When you modify MSS54 binary files (for tuning, engine swaps, or DTC deletion), you face two issues:

1. **EPROM Checksums** - Change any byte → checksums become invalid → ECU rejects the file
2. **CVN (Calibration Verification Number)** - Changes are visible to diagnostic scanners

### The Solution

This tool solves **BOTH** problems through **checksum compensation**:

```
┌─────────────────────────────────────────────────┐
│ Your Edit: 0x1234: 0x00 → 0xFF                 │
│ Problem: Checksum changes from 0x7EF8 → 0xABCD │
├─────────────────────────────────────────────────┤
│ Tool finds: Zero area at 0x06D2                │
│ Inserts: Compensation value 0x42A5             │
│ Result: Checksum restored to 0x7EF8            │
└─────────────────────────────────────────────────┘
```

**✅ EPROM checksums preserved** → ECU accepts file  
**✅ CVN preserved** → Scanner shows original value (invisible modification!)

---

## Installation

**Requirements:** 
- Python 3.6 or later (no external dependencies)
- **32KB partial flash binary** (full 512KB binaries are not supported)

That's it! No installation needed.

---

## Usage

### 1. Check Binary Information

```bash
./checksum_compensator.py input.bin --info
```

**Output:**
```
============================================================
MSS54 Binary Information
============================================================
File:            input.bin
DME Type:        MSS54
DME Version:     211322002801J469
File Size:       32768 bytes

Slave Segment:
  Stored CRC:    0x7EF8
  Calculated:    0x7EF8
  Status:        ✓ VALID

Master Segment:
  Stored CRC:    0x484B
  Calculated:    0x484B
  Status:        ✓ VALID
============================================================
```

### 2. Show Available Zero Areas (for compensation)

```bash
./checksum_compensator.py input.bin --info --show-zeros
```

**Output:**
```
Zero Sequences (>= 32 bytes):
============================================================

Slave Segment (8 found):
      Offset    Length  Notes
  ----------------------------------------
  0x000006D2       126 bytes  ← Good for compensation
  0x00000772       128 bytes  ← Good for compensation
  ...

Master Segment (5 found):
      Offset    Length  Notes
  ----------------------------------------
  0x0000732E       201 bytes  ← Good for compensation
  ...

Recommended Compensation Offsets:
  --slave-comp 0x0772  (largest: 128 bytes)
  --master-comp 0x732E  (largest: 201 bytes)
```

### 3. Restore Checksums (Main Use Case)

**After editing your binary with a hex editor or TunerPro:**

```bash
# Auto-detect compensation areas
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --output fixed.bin

# Or specify exact compensation offsets
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --slave-comp 0x0772 \
  --master-comp 0x732E \
  --output fixed.bin
```

**Output:**
```
Reading target checksums from: original.bin
  Target Slave CRC:  0x7EF8
  Target Master CRC: 0x484B

Compensating slave segment (target: 0x7EF8)...
  Current: 0xC4C3
  Searching at 0x0772...
    Tried 10,000...
    Tried 20,000...
  ✓ Found compensation: 0x42A5

Compensating master segment (target: 0x484B)...
  Current: 0xE4C2
  Searching at 0x732E...
    Tried 10,000...
  ✓ Found compensation: 0x8F21

✓ Checksums restored successfully!
```

### 4. Fix Checksums (Update Stored Values)

**If you want to update the stored checksums instead of preserving originals:**

```bash
./checksum_compensator.py edited.bin --fix-checksums --output fixed.bin
```

⚠️ **Warning:** This changes the stored checksum values (and CVN), making modifications detectable.

### 5. Find Zero Sequences (Detailed)

```bash
# Find all sequences >= 32 bytes
./checksum_compensator.py input.bin --find-zeros

# Find larger sequences only
./checksum_compensator.py input.bin --find-zeros --min-zero-length 64

# Search specific segment
./checksum_compensator.py input.bin --find-zeros --segment slave
```

---

## Real-World Examples

### Example 1: After TunerPro Editing

You've made your tuning changes in TunerPro using XDFs:

```bash
# After saving from TunerPro:
./checksum_compensator.py my-tuned-file.bin \
  --restore-checksums \
  --match-file original-stock.bin \
  --output my-tuned-file-fixed.bin

# Flash to ECU - scanner shows ORIGINAL CVN (invisible!)
```

### Example 2: After Hex Editor Changes

You manually edited the binary (e.g., EWS delete at 0x2DB2: 09 → 00):

```bash
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --output fixed.bin
```

### Example 3: Verify a Binary File

Check if a binary has valid checksums:

```bash
./checksum_compensator.py suspect-file.bin --info

# Shows:
#   ✓ VALID   - checksums are good
#   ✗ INVALID - checksums are broken
```

---

## Understanding Checksums

### Two Types of Checksums

| Aspect | EPROM Checksum | CVN |
|--------|---------------|-----|
| **Purpose** | File integrity validation | Calibration identification |
| **Standard** | Manufacturer-specific (Siemens) | SAE J1979 (OBD-II) |
| **Algorithm** | CRC16-MODBUS with 0xF0 prefix | Proprietary (BMW/Siemens) |
| **Storage** | Stored at 0x3FFC, 0x7FFC | Calculated by ECU at runtime |
| **Used by** | ECU bootloader (file validation) | Scanners, diagnostics, emissions |
| **Can preserve?** | ✅ YES (this tool does it!) | ✅ YES (via same compensation!) |

### How CVN Preservation Works

**Discovery:** We tested this empirically and it works!

1. Make your calibration edit (e.g., EWS delete)
2. Use compensation to restore EPROM checksums
3. **Result:** Both EPROM checksums AND CVN are preserved!

**Example:**
```
v0-partial.bin (stock):
  EPROM Checksums: 0x7EF8 / 0x484B
  CVN: 0x7DCC4B79

v0-partial-EWS-DELETE.bin (with compensation):
  EPROM Checksums: 0x7EF8 / 0x484B  ← Preserved
  CVN: 0x7DCC4B79                   ← ALSO preserved!
```

**Why this works:** The CVN algorithm likely operates on the same data regions as EPROM checksums. Compensation creates a "checksum collision" that preserves both values simultaneously.

### What Gets Preserved vs Changed

```
┌──────────────────────────────────────────┐
│ MODIFICATIONS WITH COMPENSATION          │
├──────────────────────────────────────────┤
│ ✅ Your edits applied                    │
│ ✅ EPROM checksums: Original values      │
│ ✅ CVN: Original value                   │
│ ✅ ECU accepts file                      │
│ ✅ Scanner shows stock CVN               │
│ ✅ Invisible to diagnostics              │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│ MODIFICATIONS WITH --fix-checksums       │
├──────────────────────────────────────────┤
│ ✅ Your edits applied                    │
│ ✗ EPROM checksums: NEW values            │
│ ✗ CVN: NEW value                         │
│ ✅ ECU accepts file                      │
│ ✗ Scanner shows modified CVN             │
│ ✗ Visible to diagnostics                 │
└──────────────────────────────────────────┘
```

**Recommendation:** Always use `--restore-checksums` to preserve CVN!

---

## File Structure

### MSS54 Binary Layout (32KB Partial)

```
Offset      | Content              | Size     | Checksum Range
------------|----------------------|----------|----------------
0x0000      | Slave segment start  | 16380 B  | ← CRC includes
...         | Calibration data     |          | ← CRC includes
0x3FFB      | Slave segment end    |          | ← CRC includes
0x3FFC      | Slave CRC (stored)   | 2 bytes  | ✗ Not included
0x3FFE      | Slave suffix         | 2 bytes  | ✗ Not included
------------|----------------------|----------|----------------
0x4000      | Master segment start | 16380 B  | ← CRC includes
...         | Program code         |          | ← CRC includes
0x7FFB      | Master segment end   |          | ← CRC includes
0x7FFC      | Master CRC (stored)  | 2 bytes  | ✗ Not included
0x7FFE      | Master suffix        | 2 bytes  | ✗ Not included
```

**Important:**
- First byte of slave: `0x02`
- First byte of master: `0x01`
- Total file size: 32,768 bytes (partial) or 65,536 bytes (full)

### Checksum Calculation

For each segment:
1. Add `0xF0` prefix byte
2. Take first `0x3FFC` bytes (16,380 bytes of data)
3. Calculate CRC16-MODBUS (polynomial 0xA001)
4. Result is 2-byte checksum (big-endian)

**Zero sequences MUST be within the checksummed range** to affect the CRC!

---

## Tips & Best Practices

### ✅ DO:

1. **Always work on copies** - Never modify your only backup
2. **Check zero areas first** - Use `--info --show-zeros` before editing
3. **Verify after changes** - Always run `--info` on the output
4. **Document modifications** - Keep notes of what you changed
5. **Test on bench** - Verify functionality before installing in car
6. **Use version control** - Git is great for tracking binary changes
7. **Keep multiple backups** - In multiple locations

### ❌ DON'T:

1. **Don't skip verification** - Always check the output file
2. **Don't mix segments** - Slave edits need slave compensation
3. **Don't guess offsets** - Use `--show-zeros` to find valid areas
4. **Don't modify checksum storage** - Areas 0x3FFC-0x3FFF, 0x7FFC-0x7FFF
5. **Don't flash untested** - Bench test first!
6. **Don't lose your original** - Keep stock binary safe

### 🎯 Pro Tips:

```bash
# Tip 1: Save recommended offsets for reuse
./checksum_compensator.py original.bin --info --show-zeros > zero_areas.txt

# Tip 2: Quick validation of multiple files
for f in *.bin; do 
  echo "$f:"; 
  ./checksum_compensator.py "$f" --info | grep Status; 
done

# Tip 3: Compare original vs modified
diff <(xxd original.bin) <(xxd modified.bin) | head -20

# Tip 4: Track CVN changes (if curious)
# Flash modified file, read CVN with scanner, document it
```

---

## Troubleshooting

### Problem: "No compensation found"

**Causes:**
- Zero area too small (only 1 byte available, need 2)
- No mathematical solution exists at that offset
- Wrong segment (slave/master mismatch)

**Solutions:**
```bash
# Try a different zero area
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --slave-comp 0x06D2  # Try different offset
  --output fixed.bin

# Let tool auto-select (finds best areas)
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --output fixed.bin
```

### Problem: "DME version string not found"

**Causes:**
- Not a valid MSS54 binary
- File corrupted
- Wrong file type

**Solutions:**
- Verify file came from MSS54/MSS54HP ECU
- Re-extract from ECU
- Check file size is exactly 32,768 or 65,536 bytes

### Problem: "Master/Slave EPROM order invalid"

**Causes:**
- Corrupted binary
- First byte of slave not 0x02
- First byte of master not 0x01

**Solutions:**
- Use a different extraction tool
- Verify with hex editor: byte at 0x0000 should be 0x02, byte at 0x4000 should be 0x01

### Problem: Checksums valid but ECU rejects file

**Possible causes:**
- Wrong ECU hardware version
- File flashing issue (not tool-related)
- ECU in locked state

**Solutions:**
- Verify hardware compatibility (211322xxxxxx = MSS54, 211323xxxxxx = MSS54HP)
- Try different flashing tool
- Check ECU isn't write-protected

### Problem: Scanner shows different CVN after compensation

**This should NOT happen if tool worked correctly!**

If CVN changed:
1. Verify you used `--restore-checksums` (not `--fix-checksums`)
2. Verify EPROM checksums match original
3. Run `--info` on both files to compare

```bash
# Check both files
./checksum_compensator.py original.bin --info
./checksum_compensator.py compensated.bin --info

# EPROM checksums should be identical
```

---

## Technical Details

### Command-Line Arguments

```
Usage: checksum_compensator.py INPUT [OPTIONS]

Display:
  --info, -i              Show file information
  --show-zeros            Show zero sequences (use with --info)
  --find-zeros, -z        Detailed zero sequence listing
  --min-zero-length N     Minimum zero sequence size (default: 32)
  --segment {slave,master,both}  Which segment to search

Restore Checksums:
  --restore-checksums     Restore original checksums via compensation
  --match-file FILE       Reference file to match checksums from
  --target-slave-crc HEX  Target slave CRC (alternative to --match-file)
  --target-master-crc HEX Target master CRC (alternative to --match-file)
  --slave-comp OFFSET     Slave compensation offset (auto if omitted)
  --master-comp OFFSET    Master compensation offset (auto if omitted)

Update Checksums:
  --fix-checksums         Recalculate and update stored checksums
  
Output:
  --output, -o FILE       Output file path
```

### Input Format

All numeric arguments accept hex or decimal:
```bash
--slave-comp 0x06D2     # Hexadecimal
--slave-comp 1746       # Decimal (same value)
```

### CRC16 Algorithm

**Implementation:** CRC-16-MODBUS
- **Polynomial:** 0xA001 (reflected 0x8005)
- **Initial value:** 0x0000
- **Final XOR:** 0x0000
- **Byte order:** LSB first (reflected)
- **MSS54 prefix:** 0xF0 prepended before calculation

```python
def crc16(data: bytes) -> int:
    crc = 0x0000
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1
    return crc
```

### Compensation Algorithm

**How it works:**

1. **Detect change:**
   ```
   Original CRC: 0x7EF8
   After edit:   0xC4C3
   Delta needed: Find value that restores 0x7EF8
   ```

2. **Brute force search:**
   - Try 1-byte values: 0x00 to 0xFF (256 attempts, ~5ms)
   - Try 2-byte values: 0x0000 to 0xFFFF (65,536 attempts, ~30-60s)

3. **Insert compensation:**
   ```
   Found: 0x42A5 at offset 0x0772
   Result: CRC restored to 0x7EF8
   ```

**Success rate:** Very high if:
- Compensation area is 2+ bytes
- Area is in same segment as edit
- Area is within CRC calculation range

### Segment Rules

**Critical:** Target edit and compensation MUST be in same segment!

| Your Edit Location | Must Use Compensation In |
|-------------------|-------------------------|
| 0x0000 - 0x3FFB   | Slave segment (0x0000 - 0x3FFB) |
| 0x4000 - 0x7FFB   | Master segment (0x4000 - 0x7FFB) |

**Invalid ranges for compensation:**
- 0x3FFC - 0x3FFF (slave checksum storage)
- 0x7FFC - 0x7FFF (master checksum storage)

### Supported File Types

**MSS54 Standard (32KB Partial - SUPPORTED):**
- Part numbers: 211322xxxxxx
- File size: 32,768 bytes
- Slave calibration: 0x0000-0x3FFF
- Master program: 0x4000-0x7FFF

**MSS54HP High Pressure (32KB Partial - SUPPORTED):**
- Part numbers: 211323xxxxxx, 211325xxxxxx
- File size: 32,768 bytes
- Same structure as MSS54, different internal calibration layout

**⚠️ Full Binaries (512KB - NOT SUPPORTED):**
- File size: 524,288 bytes (512KB)
- Contains additional bootloader and redundant data
- This tool is UNTESTED on full binaries - use at own risk
- Extract 32KB partial from full binary if needed

---

## Common Modifications

**Note:** Offsets vary by software version. Always verify with your XDF file!

| Modification | Typical Range | Segment | Notes |
|--------------|--------------|---------|-------|
| **EWS Delete** | 0x2DB2 | Slave | Single byte: 0x09 → 0x00 |
| **Rev limiter** | 0x1200-0x1400 | Slave | 2-byte value (RPM/10) |
| **Speed limiter** | 0x3000-0x3500 | Slave | 1-byte value (km/h) |
| **DTC codes** | 0x2000-0x2800 | Slave | Set to 0x00 to disable |
| **Fuel maps** | 0x5000-0x6000 | Master | Use TunerPro with XDF |
| **Ignition timing** | 0x6000-0x7000 | Master | Use TunerPro with XDF |

---

## Workflow Summary

### Standard Workflow (Works for ANY edits)

```bash
# 1. Make your edits (TunerPro, hex editor, whatever)

# 2. Restore checksums
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --output fixed.bin

# 3. Verify (optional but recommended)
./checksum_compensator.py fixed.bin --info

# 4. Flash and test

# Done! Works for 1 byte or 1000 bytes of edits.
```

### If Compensation Fails

If auto-detection doesn't find suitable zero areas:

```bash
# Find zero areas manually
./checksum_compensator.py original.bin --info --show-zeros

# Use specific offsets
./checksum_compensator.py edited.bin \
  --restore-checksums \
  --match-file original.bin \
  --slave-comp 0x0772 \
  --master-comp 0x732E \
  --output fixed.bin
```

---

## Resources

### Related Files in Repository

- `checksum.pl` - Original Perl script by p0lar @ m3forum.net
- `../Complete XDFs/` - XDF definitions for TunerPro
- `../Engine Swap XDFs/` - Engine swap specific XDFs (includes EWS delete info)
- `../Unmodified BIN Dumps - Partials/` - Stock binaries for reference
- `../DTC Codes w ODBII and Error Values.xlsx` - DTC code reference

### Community Resources

- [M3Forum MSS54 Thread](https://nam3forum.com/forums/forum/special-interests/coding-tuning/2052-comprehensive-mss54-mss54hp-dme-information)
- [M3Forum General](https://www.m3forum.net)

### Tools Ecosystem

- **TunerPro**: XDF-based tuning software
- **HxD**: Hex editor (Windows)
- **Hex Fiend**: Hex editor (macOS)
- **This tool**: Checksum compensation

---

## Safety & Legal

### ⚠️ Important Safety Information

1. **Always work on copies** - Never modify your only backup
2. **Bench test first** - Verify functionality before car installation
3. **Professional help** - Consult a professional tuner if unsure
4. **Multiple backups** - Keep backups in multiple locations
5. **Document everything** - Log all modifications
6. **Know your skill level** - Some mods require experience
7. **Test incrementally** - Don't make 50 changes at once

### Legal Considerations

- **Emissions:** Modifying emissions systems may be illegal in your jurisdiction
- **Warranty:** Modifications typically void manufacturer warranty
- **Insurance:** Notify your insurance of modifications
- **Track use:** Some modifications are for track/race use only
- **Responsibility:** You assume all risk for modifications

### Disclaimer

This tool is provided **as-is** for **educational and personal use only**. The authors are not responsible for:
- Damage to your vehicle
- Damage to your ECU
- Failed emissions testing
- Warranty issues
- Legal consequences
- Any other issues arising from use

**Use at your own risk!**

---

## Credits & License

### Credits

- **Original checksum.pl:** p0lar @ m3forum.net
- **Python implementation:** Based on Perl script methodology  
- **CRC16 algorithm:** Standard CRC-16-MODBUS
- **Testing & validation:** MSS54 community

### License

- **checksum_compensator.py:** Provided as-is for educational and personal use
- **checksum.pl:** Retains original BSD-style license by p0lar @ m3forum.net
- **Documentation:** Free to use and modify

---

## Version History

**v1.0** (November 2024)
- Initial Python implementation
- EPROM checksum preservation
- CVN preservation (empirically verified!)
- Single comprehensive tool
- Complete documentation

---

## Support

**For issues or questions:**

1. Read this README thoroughly
2. Check the troubleshooting section
3. Verify your binary file is valid (32KB or 64KB, proper format)
4. Post on M3Forum with detailed error messages
5. Include: file size, DME version, exact command used, error output

**No guarantees of support, but the community is helpful!**

---

**Happy tuning! Remember: Safety first, test on bench, keep backups!** 🔧🏁
