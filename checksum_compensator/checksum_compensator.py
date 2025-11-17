#!/usr/bin/env python3
"""
================================================================================
                        MSS54 Checksum Compensator
                         Copyright (c) 2024
                    EDUCATIONAL AND PERSONAL USE ONLY
================================================================================

DESCRIPTION:
  This tool restores checksums in MSS54/MSS54HP ECU binary files after
  modifications by inserting compensation values in zero-byte regions,
  preserving the original CVN (Calibration Verification Number).

  SUPPORTED FORMATS:
  - MSS54:   32KB partial binaries (211322xxxxxx)
  - MSS54HP: 64KB partial binaries (211323xxxxxx, 211325xxxxxx)

  Full 512KB binaries are NOT supported.

  Based on checksum calculation methodology from checksum.pl by p0lar @ m3forum.net

CHECKSUM ALGORITHM (CRC16-MODBUS):
  - Add "F0" prefix to the beginning of each segment
  - Take first 0x3FFC bytes (16380 bytes)
  - Calculate CRC16 using polynomial 0xA001
  - Store at 0x3FFC (slave) or 0x7FFC (master) with 2-byte suffix following

================================================================================
                                DISCLAIMER
================================================================================

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
EXPRESSED OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR NON-INFRINGEMENT.

THE AUTHOR(S) ASSUME NO LIABILITY FOR DAMAGES RESULTING FROM THE USE OF THIS
SOFTWARE, INCLUDING BUT NOT LIMITED TO:
  * DAMAGE TO YOUR VEHICLE OR ENGINE CONTROL UNIT (ECU)
  * VOIDED WARRANTIES
  * FAILED EMISSIONS TESTING
  * LEGAL CONSEQUENCES OF MODIFYING EMISSIONS SYSTEMS
  * LOSS OF DATA OR CORRUPTED BINARY FILES
  * VEHICLE MALFUNCTION OR UNSAFE OPERATION
  * ANY OTHER DIRECT, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES

YOU ASSUME ALL RISK AND RESPONSIBILITY FOR THE USE OF THIS SOFTWARE.

================================================================================
                              IMPORTANT WARNINGS
================================================================================

AUTOMOTIVE SAFETY:
  * Always bench test modified ECU files before vehicle installation
  * Never modify your only backup - work on copies
  * Some modifications may be illegal in your jurisdiction
  * Modifying emissions systems may violate federal/state/local laws
  * Modifications typically void manufacturer warranties
  * Consult a professional tuner if unsure

PROPER USE:
  * This tool is for educational purposes and personal use only
  * Not for commercial use without permission
  * User is responsible for compliance with all applicable laws
  * Test thoroughly before real-world use
  * Keep detailed documentation of all modifications

================================================================================

BY USING THIS SOFTWARE, YOU ACKNOWLEDGE THAT YOU HAVE READ THIS DISCLAIMER,
UNDERSTAND IT, AND AGREE TO BE BOUND BY ITS TERMS.

USE AT YOUR OWN RISK.

================================================================================
"""

import struct
import sys
from pathlib import Path
from typing import Tuple, List, Optional
import argparse


class CRC16:
    """CRC16 calculator matching the Perl implementation"""

    @staticmethod
    def calculate(data: bytes) -> int:
        """
        Calculate CRC16 checksum using the same algorithm as the Perl script.

        Args:
            data: Bytes to calculate checksum for

        Returns:
            16-bit CRC value
        """
        crc = 0x0

        # Build CRC table
        crctable = []
        for i in range(0x100):
            r = i
            for j in range(0x8):
                t = 0xA001 if (r & 1) else 0
                r = (r >> 1) ^ t
            crctable.append(r & 0xFFFF)

        # Calculate CRC
        for byte in data:
            crc = (crc >> 8) ^ crctable[(crc ^ byte) & 0xFF]

        return crc & 0xFFFF


class MSS54Binary:
    """Represents an MSS54/MSS54HP binary file with checksum management"""

    # Configuration constants
    CRC_PREFIX = b'\xF0'
    SEGMENT_SIZE = 0x4000  # 16384 bytes

    # Will be set based on DME type
    is_mss54hp = False
    OFFSET_SLAVE = 0x0000
    OFFSET_MASTER = 0x4000
    CRC_OFFSET_SLAVE = 0x3FFC
    CRC_OFFSET_MASTER = 0x7FFC

    def __init__(self, filepath: str):
        """
        Load an MSS54 binary file.

        Args:
            filepath: Path to the binary file
        """
        self.filepath = Path(filepath)
        with open(self.filepath, 'rb') as f:
            self.data = bytearray(f.read())

        # Extract DME version first to determine type
        self.dme_type, self.dme_version = self._get_dme_version()

        # Detect MSS54HP based on part number
        self.is_mss54hp = self.dme_version.startswith('211323') or self.dme_version.startswith('211325')

        # Validate file size based on DME type
        if self.is_mss54hp:
            # MSS54HP requires 64KB
            if len(self.data) != 65536:
                raise ValueError(
                    f"ERROR: MSS54HP detected but file is {len(self.data)} bytes!\n"
                    f"MSS54HP requires 64KB (65536 bytes) partial binaries.\n"
                    f"Part number: {self.dme_version}"
                )
            # MSS54HP has additional segment offsets
            self.OFFSET_SEGMENT3 = 0x8000
            self.OFFSET_SEGMENT4 = 0xC000
            self.CRC_OFFSET_MASTER = 0xBFFC  # Second CRC at different location for MSS54HP
        else:
            # MSS54 Standard
            if len(self.data) == 32768:
                # 32KB partial - supported and tested
                pass
            elif len(self.data) == 65536:
                # 64KB file for MSS54 - warn
                print("\n⚠️  WARNING: 64KB MSS54 file detected. This is unusual.")
                print("    MSS54 typically uses 32KB partials. Proceeding with caution.\n")
            elif len(self.data) == 524288:
                # 512KB full binary - not supported
                raise ValueError(
                    f"ERROR: 512KB full binary detected!\n"
                    f"This tool is ONLY for partial binaries (32KB/64KB).\n"
                    f"Please extract the partial flash before using this tool.\n"
                    f"See ../scripts/full2partial.py for extraction."
                )
            else:
                raise ValueError(
                    f"Invalid file size: {len(self.data)} bytes.\n"
                    f"Expected: 32768 bytes (MSS54) or 65536 bytes (MSS54HP)\n"
                    f"This tool does NOT work with full 512KB binaries."
                )

        # Validate master/slave order
        # MSS54: slave at 0x0000, master at 0x4000
        # MSS54HP: slave at 0x0000, master at 0x8000
        master_offset = 0x8000 if self.is_mss54hp else self.OFFSET_MASTER
        if self.data[self.OFFSET_SLAVE] != 0x02 or self.data[master_offset] != 0x01:
            raise ValueError("Master/Slave EPROM order invalid")

        # Extract original checksums
        self.original_crc_slave = struct.unpack('>H', self.data[self.CRC_OFFSET_SLAVE:self.CRC_OFFSET_SLAVE + 2])[0]
        self.original_crc_master = struct.unpack('>H', self.data[self.CRC_OFFSET_MASTER:self.CRC_OFFSET_MASTER + 2])[0]
        self.crc_suffix_slave = self.data[self.CRC_OFFSET_SLAVE + 2:self.CRC_OFFSET_SLAVE + 4]
        self.crc_suffix_master = self.data[self.CRC_OFFSET_MASTER + 2:self.CRC_OFFSET_MASTER + 4]

    def _get_dme_version(self) -> Tuple[str, str]:
        """Extract DME type and version from binary"""
        import re

        # Convert binary to ASCII string for pattern matching
        try:
            data_str = self.data.decode('latin-1')
        except:
            data_str = ''.join(chr(b) if 32 <= b < 127 else '.' for b in self.data)

        # Look for version pattern: 2113XXXXXXXX[0-9A-Z]{4}
        # This pattern appears 3 times in the binary
        pattern = r'(2113\d{8}[0-9A-Z]{4})'
        matches = re.findall(pattern, data_str)

        if not matches:
            raise ValueError("DME version string not found")

        # Take the first match
        version = matches[0]

        # Determine DME type based on version pattern
        if version.startswith('211318'):
            return 'MSS50', version
        elif version.startswith('211321'):
            return 'MSS52', version
        elif version.startswith('211322'):
            return 'MSS54', version
        elif version.startswith('211323') or version.startswith('211325'):
            return 'MSS54HP', version
        else:
            raise ValueError(f"Unknown DME type for version: {version}")

    def calculate_segment_crc(self, segment: str) -> int:
        """
        Calculate CRC for a segment (slave or master).

        For MSS54: Standard calculation
        For MSS54HP: Segments are swapped before CRC calculation

        Args:
            segment: 'slave' or 'master'

        Returns:
            Calculated CRC16 value
        """
        if self.is_mss54hp:
            # MSS54HP uses swapped segments for CRC calculation
            if segment == 'slave':
                # Slave CRC = CRC16(Segment1 + Segment2)
                # Segment1: 0x4000-0x7FFF, Segment2: 0x0000-0x3FFC
                seg1 = self.data[0x4000:0x8000]
                seg2 = self.data[0x0000:0x3FFC]
                data = seg1 + seg2
            elif segment == 'master':
                # Master CRC = CRC16(Segment3 + Segment4)
                # Segment3: 0xC000-0xFFFF, Segment4: 0x8000-0xBFFC
                seg3 = self.data[0xC000:0x10000]
                seg4 = self.data[0x8000:0xBFFC]
                data = seg3 + seg4
            else:
                raise ValueError("Segment must be 'slave' or 'master'")

            # Calculate CRC without prefix for MSS54HP
            return CRC16.calculate(data)
        else:
            # MSS54 Standard - original logic
            if segment == 'slave':
                offset = self.OFFSET_SLAVE
            elif segment == 'master':
                offset = self.OFFSET_MASTER
            else:
                raise ValueError("Segment must be 'slave' or 'master'")

        # Extract segment data (excluding the 4-byte checksum area)
        segment_data = self.data[offset:offset + self.SEGMENT_SIZE - 4]

        # Add prefix and calculate CRC
        data_with_prefix = self.CRC_PREFIX + segment_data
        return CRC16.calculate(data_with_prefix)

    def verify_checksums(self) -> Tuple[bool, bool]:
        """
        Verify if checksums are correct.

        Returns:
            Tuple of (slave_valid, master_valid)
        """
        calc_slave = self.calculate_segment_crc('slave')
        calc_master = self.calculate_segment_crc('master')

        return (calc_slave == self.original_crc_slave,
                calc_master == self.original_crc_master)

    def update_checksums(self):
        """Update checksums in the binary data"""
        crc_slave = self.calculate_segment_crc('slave')
        crc_master = self.calculate_segment_crc('master')

        # Update slave checksum
        struct.pack_into('>H', self.data, self.CRC_OFFSET_SLAVE, crc_slave)
        # Update master checksum
        struct.pack_into('>H', self.data, self.CRC_OFFSET_MASTER, crc_master)

    def find_zero_sequences(self, min_length: int = 8, segment: str = 'both') -> List[Tuple[int, int]]:
        """
        Find sequences of 0x00 bytes in the binary.

        Args:
            min_length: Minimum length of zero sequence to find
            segment: 'slave', 'master', or 'both'

        Returns:
            List of (offset, length) tuples
        """
        sequences = []

        # Determine search range
        if segment == 'slave':
            start, end = self.OFFSET_SLAVE, self.CRC_OFFSET_SLAVE
        elif segment == 'master':
            start, end = self.OFFSET_MASTER, self.CRC_OFFSET_MASTER
        else:  # both
            start, end = 0, len(self.data)

        current_start = None
        current_length = 0

        for i in range(start, end):
            # Skip checksum areas
            if i in range(self.CRC_OFFSET_SLAVE, self.CRC_OFFSET_SLAVE + 4):
                if current_start is not None and current_length >= min_length:
                    sequences.append((current_start, current_length))
                current_start = None
                current_length = 0
                continue
            if i in range(self.CRC_OFFSET_MASTER, self.CRC_OFFSET_MASTER + 4):
                if current_start is not None and current_length >= min_length:
                    sequences.append((current_start, current_length))
                current_start = None
                current_length = 0
                continue

            if self.data[i] == 0x00:
                if current_start is None:
                    current_start = i
                    current_length = 1
                else:
                    current_length += 1
            else:
                if current_start is not None and current_length >= min_length:
                    sequences.append((current_start, current_length))
                current_start = None
                current_length = 0

        # Check last sequence
        if current_start is not None and current_length >= min_length:
            sequences.append((current_start, current_length))

        return sequences

    def brute_force_compensation(self, target_offset: int, target_value: int,
                                 original_value: int, compensation_offset: int,
                                 max_attempts: int = 65536) -> Optional[Tuple[int, int]]:
        """
        Brute force a value to place at compensation_offset to maintain checksum
        when changing target_offset from original_value to target_value.

        Args:
            target_offset: Offset of the byte to change
            target_value: New value for the target byte
            original_value: Original value at target offset
            compensation_offset: Offset where compensation value will be placed
            max_attempts: Maximum values to try (for 2-byte compensation)

        Returns:
            Tuple of (compensation_value, compensation_size) or None if not found
            compensation_size is 1 or 2 bytes
        """
        # Determine which segment we're working in
        if target_offset < self.OFFSET_MASTER:
            segment = 'slave'
        else:
            segment = 'master'

        # Get original checksum
        original_crc = self.calculate_segment_crc(segment)

        # Make the target change
        self.data[target_offset] = target_value

        # Try single-byte compensation first
        print(f"Attempting single-byte compensation at 0x{compensation_offset:04X}...")
        original_comp_value = self.data[compensation_offset]

        for comp_value in range(256):
            self.data[compensation_offset] = comp_value
            new_crc = self.calculate_segment_crc(segment)

            if new_crc == original_crc:
                print(f"✓ Found single-byte solution: 0x{comp_value:02X}")
                return (comp_value, 1)

        # Restore original compensation value
        self.data[compensation_offset] = original_comp_value

        # Try two-byte compensation
        print(f"Single-byte failed. Attempting two-byte compensation at 0x{compensation_offset:04X}...")
        original_comp_value2 = self.data[compensation_offset + 1]

        attempts = 0
        for comp_value in range(min(max_attempts, 65536)):
            if attempts % 10000 == 0:
                print(f"  Tried {attempts} combinations...")

            byte1 = (comp_value >> 8) & 0xFF
            byte2 = comp_value & 0xFF

            self.data[compensation_offset] = byte1
            self.data[compensation_offset + 1] = byte2
            new_crc = self.calculate_segment_crc(segment)

            if new_crc == original_crc:
                print(f"✓ Found two-byte solution: 0x{comp_value:04X}")
                return (comp_value, 2)

            attempts += 1

        # Restore original values
        self.data[target_offset] = original_value
        self.data[compensation_offset] = original_comp_value
        self.data[compensation_offset + 1] = original_comp_value2

        print("✗ No solution found")
        return None

    def save(self, output_path: Optional[str] = None):
        """
        Save the binary to a file.

        Args:
            output_path: Path to save to. If None, overwrites original.
        """
        if output_path is None:
            output_path = self.filepath

        with open(output_path, 'wb') as f:
            f.write(self.data)

        print(f"Saved to: {output_path}")

    def print_info(self, show_zeros=False, min_zero_length=32):
        """Print information about the binary"""
        slave_valid, master_valid = self.verify_checksums()

        print(f"\n{'='*60}")
        print(f"MSS54{' HP' if self.is_mss54hp else ''} Binary Information")
        print(f"{'='*60}")
        print(f"File:            {self.filepath.name}")
        print(f"DME Type:        {self.dme_type}")
        print(f"DME Version:     {self.dme_version}")
        print(f"File Size:       {len(self.data)} bytes")

        if self.is_mss54hp:
            print(f"\nFirst CRC (Segment1+2):")
            print(f"  Stored CRC:    0x{self.original_crc_slave:04X} (at 0x3FFC)")
            print(f"  Calculated:    0x{self.calculate_segment_crc('slave'):04X}")
            print(f"  Status:        {'✓ VALID' if slave_valid else '✗ INVALID'}")
            print(f"  Note:          Covers 0x4000-0x7FFF + 0x0000-0x3FFC (swapped)")
            print(f"\nSecond CRC (Segment3+4):")
            print(f"  Stored CRC:    0x{self.original_crc_master:04X} (at 0xBFFC)")
            print(f"  Calculated:    0x{self.calculate_segment_crc('master'):04X}")
            print(f"  Status:        {'✓ VALID' if master_valid else '✗ INVALID'}")
            print(f"  Note:          Covers 0xC000-0xFFFF + 0x8000-0xBFFC (swapped)")
        else:
            print(f"\nSlave Segment:")
            print(f"  Stored CRC:    0x{self.original_crc_slave:04X}")
            print(f"  Calculated:    0x{self.calculate_segment_crc('slave'):04X}")
            print(f"  Status:        {'✓ VALID' if slave_valid else '✗ INVALID'}")
            print(f"\nMaster Segment:")
            print(f"  Stored CRC:    0x{self.original_crc_master:04X}")
            print(f"  Calculated:    0x{self.calculate_segment_crc('master'):04X}")
            print(f"  Status:        {'✓ VALID' if master_valid else '✗ INVALID'}")

        if show_zeros:
            print(f"\nZero Sequences (>= {min_zero_length} bytes):")
            print(f"{'='*60}")
            sequences = self.find_zero_sequences(min_zero_length, 'both')

            if sequences:
                if self.is_mss54hp:
                    # MSS54HP: Split into 4 segments
                    seg1_2_seqs = [(o, l) for o, l in sequences if o < 0x8000]  # First half (Seg1+2)
                    seg3_4_seqs = [(o, l) for o, l in sequences if o >= 0x8000]  # Second half (Seg3+4)

                    print(f"\nFirst Half - Segments 1+2 ({len(seg1_2_seqs)} found):")
                    print(f"  Covers: 0x0000-0x3FFF, 0x4000-0x7FFF")
                    if seg1_2_seqs:
                        print(f"  {'Offset':>10}  {'Length':>8}  Notes")
                        print(f"  {'-'*40}")
                        for offset, length in seg1_2_seqs[:5]:
                            note = "← Good for compensation" if length >= 32 else ""
                            print(f"  0x{offset:08X}  {length:8} bytes  {note}")
                        if len(seg1_2_seqs) > 5:
                            print(f"  ... and {len(seg1_2_seqs)-5} more")
                    else:
                        print(f"  None found")

                    print(f"\nSecond Half - Segments 3+4 ({len(seg3_4_seqs)} found):")
                    print(f"  Covers: 0x8000-0xBFFF, 0xC000-0xFFFF")
                    if seg3_4_seqs:
                        print(f"  {'Offset':>10}  {'Length':>8}  Notes")
                        print(f"  {'-'*40}")
                        for offset, length in seg3_4_seqs[:5]:
                            note = "← Good for compensation" if length >= 32 else ""
                            print(f"  0x{offset:08X}  {length:8} bytes  {note}")
                        if len(seg3_4_seqs) > 5:
                            print(f"  ... and {len(seg3_4_seqs)-5} more")
                    else:
                        print(f"  None found")

                    slave_seqs = seg1_2_seqs
                    master_seqs = seg3_4_seqs
                else:
                    # MSS54: Standard 2 segments
                    slave_seqs = [(o, l) for o, l in sequences if o < self.OFFSET_MASTER]
                    master_seqs = [(o, l) for o, l in sequences if o >= self.OFFSET_MASTER]

                    print(f"\nSlave Segment ({len(slave_seqs)} found):")
                    if slave_seqs:
                        print(f"  {'Offset':>10}  {'Length':>8}  Notes")
                        print(f"  {'-'*40}")
                        for offset, length in slave_seqs[:5]:  # Show first 5
                            note = "← Good for compensation" if length >= 32 else ""
                            print(f"  0x{offset:08X}  {length:8} bytes  {note}")
                        if len(slave_seqs) > 5:
                            print(f"  ... and {len(slave_seqs)-5} more")
                    else:
                        print(f"  None found")

                    print(f"\nMaster Segment ({len(master_seqs)} found):")
                    if master_seqs:
                        print(f"  {'Offset':>10}  {'Length':>8}  Notes")
                        print(f"  {'-'*40}")
                        for offset, length in master_seqs[:5]:  # Show first 5
                            note = "← Good for compensation" if length >= 32 else ""
                            print(f"  0x{offset:08X}  {length:8} bytes  {note}")
                        if len(master_seqs) > 5:
                            print(f"  ... and {len(master_seqs)-5} more")
                    else:
                        print(f"  None found")

                # Suggest best compensation offsets
                print(f"\nRecommended Compensation Offsets:")
                if slave_seqs:
                    best_slave = max(slave_seqs, key=lambda x: x[1])
                    print(f"  --slave-comp 0x{best_slave[0]:04X}  (largest: {best_slave[1]} bytes)")
                else:
                    print(f"  --slave-comp: No suitable area found")

                if master_seqs:
                    best_master = max(master_seqs, key=lambda x: x[1])
                    print(f"  --master-comp 0x{best_master[0]:04X}  (largest: {best_master[1]} bytes)")
                else:
                    print(f"  --master-comp: No suitable area found")
            else:
                print(f"  No zero sequences found (>= {min_zero_length} bytes)")

        print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(
        description='MSS54 Binary Checksum Compensator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show file info with recommended compensation offsets
  %(prog)s input.bin --info --show-zeros

  # Detailed zero sequence listing
  %(prog)s input.bin --find-zeros --min-zero-length 16

  # Make a single modification with checksum preservation
  %(prog)s input.bin --target-offset 0x1000 --target-value 0xFF \\
                     --original-value 0x00 --comp-offset 0x2000 \\
                     --output modified.bin

  # Restore checksums to match a reference file (after editing)
  %(prog)s edited.bin --restore-checksums --match-file original.bin \\
                      --slave-comp 0x06D0 --master-comp 0x7300 \\
                      --output compensated.bin

  # Restore checksums to specific values
  %(prog)s edited.bin --restore-checksums \\
                      --target-slave-crc 0x7EF8 --target-master-crc 0x484B \\
                      --slave-comp 0x06D0 --master-comp 0x7300 \\
                      --output compensated.bin

  # Just fix checksums (updates stored values)
  %(prog)s input.bin --fix-checksums --output fixed.bin
        """
    )

    parser.add_argument('input', help='Input MSS54 binary file')
    parser.add_argument('--output', '-o', help='Output file path')
    parser.add_argument('--info', '-i', action='store_true',
                       help='Display binary information')
    parser.add_argument('--show-zeros', action='store_true',
                       help='Show zero sequences with --info (recommended for compensation planning)')
    parser.add_argument('--find-zeros', '-z', action='store_true',
                       help='Find sequences of 0x00 bytes (detailed output)')
    parser.add_argument('--min-zero-length', type=int, default=32,
                       help='Minimum length of zero sequences to find (default: 32)')
    parser.add_argument('--segment', choices=['slave', 'master', 'both'], default='both',
                       help='Which segment to search (default: both)')

    # Brute force options
    parser.add_argument('--target-offset', type=lambda x: int(x, 0),
                       help='Offset of byte to modify (hex or decimal)')
    parser.add_argument('--target-value', type=lambda x: int(x, 0),
                       help='New value for target byte (hex or decimal)')
    parser.add_argument('--original-value', type=lambda x: int(x, 0),
                       help='Original value at target offset (hex or decimal)')
    parser.add_argument('--comp-offset', type=lambda x: int(x, 0),
                       help='Offset for compensation bytes (hex or decimal)')
    parser.add_argument('--max-attempts', type=int, default=65536,
                       help='Maximum attempts for two-byte compensation (default: 65536)')

    parser.add_argument('--fix-checksums', action='store_true',
                       help='Recalculate and update checksums')

    # Checksum restoration options
    parser.add_argument('--restore-checksums', action='store_true',
                       help='Restore checksums to original values via compensation')
    parser.add_argument('--match-file', type=str,
                       help='Reference file to match checksums from')
    parser.add_argument('--target-slave-crc', type=lambda x: int(x, 0),
                       help='Target slave CRC value (hex or decimal)')
    parser.add_argument('--target-master-crc', type=lambda x: int(x, 0),
                       help='Target master CRC value (hex or decimal)')
    parser.add_argument('--slave-comp', type=lambda x: int(x, 0),
                       help='Offset for slave segment compensation (hex or decimal)')
    parser.add_argument('--master-comp', type=lambda x: int(x, 0),
                       help='Offset for master segment compensation (hex or decimal)')

    args = parser.parse_args()

    try:
        # Load binary
        binary = MSS54Binary(args.input)

        # Display info if requested
        if args.info or not any([args.find_zeros, args.target_offset, args.fix_checksums, args.restore_checksums]):
            binary.print_info(show_zeros=args.show_zeros, min_zero_length=args.min_zero_length)

        # Find zero sequences
        if args.find_zeros:
            sequences = binary.find_zero_sequences(args.min_zero_length, args.segment)
            print(f"\nFound {len(sequences)} zero sequences (>= {args.min_zero_length} bytes):")
            print(f"{'Offset':>10}  {'Length':>10}  {'Segment'}")
            print("-" * 40)

            for offset, length in sequences:
                if offset < binary.OFFSET_MASTER:
                    seg = 'Slave'
                else:
                    seg = 'Master'
                print(f"0x{offset:08X}  {length:10}  {seg}")

            if sequences:
                print(f"\nLargest sequence: {max(sequences, key=lambda x: x[1])[1]} bytes at 0x{max(sequences, key=lambda x: x[1])[0]:08X}")

        # Brute force compensation
        if args.target_offset is not None:
            if args.target_value is None or args.original_value is None or args.comp_offset is None:
                print("Error: --target-offset requires --target-value, --original-value, and --comp-offset")
                sys.exit(1)

            print(f"\nBrute forcing compensation...")
            print(f"Target change: 0x{args.target_offset:04X}: 0x{args.original_value:02X} -> 0x{args.target_value:02X}")
            print(f"Compensation offset: 0x{args.comp_offset:04X}")

            result = binary.brute_force_compensation(
                args.target_offset,
                args.target_value,
                args.original_value,
                args.comp_offset,
                args.max_attempts
            )

            if result:
                comp_value, comp_size = result
                print(f"\n✓ Success! Compensation value: 0x{comp_value:0{comp_size*2}X} ({comp_size} byte{'s' if comp_size > 1 else ''})")

                if args.output:
                    binary.save(args.output)
            else:
                print("\n✗ Failed to find compensation value")
                sys.exit(1)

        # Fix checksums
        if args.fix_checksums:
            print("\nRecalculating checksums...")
            old_slave = binary.calculate_segment_crc('slave')
            old_master = binary.calculate_segment_crc('master')

            binary.update_checksums()

            new_slave = binary.calculate_segment_crc('slave')
            new_master = binary.calculate_segment_crc('master')

            print(f"Slave:  0x{old_slave:04X} -> 0x{new_slave:04X}")
            print(f"Master: 0x{old_master:04X} -> 0x{new_master:04X}")

            if args.output:
                binary.save(args.output)

        # Restore checksums via compensation
        if args.restore_checksums:
            # Determine target checksums
            target_slave = None
            target_master = None

            if args.match_file:
                print(f"\nReading target checksums from: {args.match_file}")
                ref_binary = MSS54Binary(args.match_file)
                target_slave = ref_binary.original_crc_slave
                target_master = ref_binary.original_crc_master
                print(f"  Target Slave CRC:  0x{target_slave:04X}")
                print(f"  Target Master CRC: 0x{target_master:04X}")
            elif args.target_slave_crc is not None or args.target_master_crc is not None:
                target_slave = args.target_slave_crc
                target_master = args.target_master_crc
                if target_slave:
                    print(f"\nTarget Slave CRC:  0x{target_slave:04X}")
                if target_master:
                    print(f"Target Master CRC: 0x{target_master:04X}")
            else:
                print("Error: --restore-checksums requires either --match-file or --target-*-crc")
                sys.exit(1)

            # Find zero areas if not specified
            slave_comp = args.slave_comp
            master_comp = args.master_comp

            if (target_slave and not slave_comp) or (target_master and not master_comp):
                print("\nFinding zero sequences for compensation...")
                sequences = binary.find_zero_sequences(32, 'both')

                if not slave_comp and target_slave:
                    # Find first suitable slave area
                    for offset, length in sequences:
                        if offset < binary.CRC_OFFSET_SLAVE and length >= 2:
                            slave_comp = offset
                            print(f"  Auto-selected slave comp: 0x{slave_comp:04X}")
                            break

                if not master_comp and target_master:
                    # Find first suitable master area
                    for offset, length in sequences:
                        if offset >= binary.OFFSET_MASTER and offset < binary.CRC_OFFSET_MASTER and length >= 2:
                            master_comp = offset
                            print(f"  Auto-selected master comp: 0x{master_comp:04X}")
                            break

            # Apply compensation
            success = True

            if target_slave:
                print(f"\nCompensating slave segment (target: 0x{target_slave:04X})...")
                current = binary.calculate_segment_crc('slave')
                print(f"  Current: 0x{current:04X}")

                if current != target_slave:
                    if not slave_comp:
                        print("  Error: No slave compensation offset available")
                        success = False
                    else:
                        print(f"  Searching at 0x{slave_comp:04X}...")
                        found = False
                        orig_bytes = (binary.data[slave_comp], binary.data[slave_comp + 1])

                        for val in range(65536):
                            if val % 10000 == 0 and val > 0:
                                print(f"    Tried {val:,}...")

                            binary.data[slave_comp] = (val >> 8) & 0xFF
                            binary.data[slave_comp + 1] = val & 0xFF

                            if binary.calculate_segment_crc('slave') == target_slave:
                                print(f"  ✓ Found compensation: 0x{val:04X}")
                                found = True
                                break

                        if not found:
                            binary.data[slave_comp], binary.data[slave_comp + 1] = orig_bytes
                            print("  ✗ No compensation found")
                            success = False
                else:
                    print("  Already matches target")

            if target_master:
                print(f"\nCompensating master segment (target: 0x{target_master:04X})...")
                current = binary.calculate_segment_crc('master')
                print(f"  Current: 0x{current:04X}")

                if current != target_master:
                    if not master_comp:
                        print("  Error: No master compensation offset available")
                        success = False
                    else:
                        print(f"  Searching at 0x{master_comp:04X}...")
                        found = False
                        orig_bytes = (binary.data[master_comp], binary.data[master_comp + 1])

                        for val in range(65536):
                            if val % 10000 == 0 and val > 0:
                                print(f"    Tried {val:,}...")

                            binary.data[master_comp] = (val >> 8) & 0xFF
                            binary.data[master_comp + 1] = val & 0xFF

                            if binary.calculate_segment_crc('master') == target_master:
                                print(f"  ✓ Found compensation: 0x{val:04X}")
                                found = True
                                break

                        if not found:
                            binary.data[master_comp], binary.data[master_comp + 1] = orig_bytes
                            print("  ✗ No compensation found")
                            success = False
                else:
                    print("  Already matches target")

            if success and args.output:
                binary.save(args.output)
                print("\n✓ Checksums restored successfully!")
            elif not success:
                print("\n✗ Failed to restore checksums")
                sys.exit(1)

        # Save if output specified but no other operations
        if args.output and not any([args.target_offset, args.fix_checksums, args.restore_checksums]):
            binary.save(args.output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

