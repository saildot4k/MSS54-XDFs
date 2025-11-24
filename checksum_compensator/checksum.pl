#!/usr/bin/perl -w

#    Copyright (c) 2012, 2013 p0lar @ m3forum.net
#
#    Redistribution and use in source and binary forms, with or without
#    modification, are permitted provided that the following conditions
#    are met:
#    1. Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    2. Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    3. All advertising materials mentioning features or use of this software
#       must display the following acknowledgement:
#	This product includes software developed by p0lar @ m3forum.net and its
#       contributors
#    4. Neither the name of p0lar @ m3forum.net nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
#
#    THIS SOFTWARE IS PROVIDED BY P0LAR @ M3FORUM.NET AND CONTRIBUTORS ``AS IS''
#    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
#    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
#    ARE DISCLAIMED.  IN NO EVENT SHALL P0LAR @ M3FORUM.NET OR CONTRIBUTORS BE
#    LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
#    CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
#    SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
#    INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
#    CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
#    ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
#    POSSIBILITY OF SUCH DAMAGE.
#
#    NO WARRANTY
#
#    BECAUSE THE PROGRAM IS LICENSED FREE OF CHARGE, THERE IS NO WARRANTY
#    FOR THE PROGRAM, TO THE EXTENT PERMITTED BY APPLICABLE LAW.  EXCEPT WHEN
#    OTHERWISE STATED IN WRITING THE COPYRIGHT HOLDERS AND/OR OTHER PARTIES
#    PROVIDE THE PROGRAM "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED
#    OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
#    MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
#    TO THE QUALITY AND PERFORMANCE OF THE PROGRAM IS WITH YOU.  SHOULD THE
#    PROGRAM PROVE DEFECTIVE, YOU ASSUME THE COST OF ALL NECESSARY SERVICING,
#    REPAIR OR CORRECTION.
#
#    IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW OR AGREED TO IN WRITING
#    WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY AND/OR
#    REDISTRIBUTE THE PROGRAM AS PERMITTED ABOVE, BE LIABLE TO YOU FOR DAMAGES,
#    INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING
#    OUT OF THE USE OR INABILITY TO USE THE PROGRAM (INCLUDING BUT NOT LIMITED
#    TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY
#    YOU OR THIRD PARTIES OR A FAILURE OF THE PROGRAM TO OPERATE WITH ANY OTHER
#    PROGRAMS), EVEN IF SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE
#    POSSIBILITY OF SUCH DAMAGES.
#

use strict;
use File::Basename;
use Data::Dumper; $Data::Dumper::Indent = 1; $Data::Dumper::Sortkeys = 1;
use Getopt::Long;

# Default configuraiton options for the various DMEs, DME-specific info will be redefined on a per-DME basis in %config
my %default = (
  'offset_s' => 0x0000,
  'offset_m' => 0x4000,
  'crc_offset_s' => 0x3FFC,
  'crc_offset_m' => 0x7FFC,
  'crc_prefix'   => ''
);

# Basic cofiguration, including specific differences from %default for various DMEs included
my %config = (
  'version'   => '0.2.5',
  'debug'     => 0,
  'help'      => 0,
  'overwrite' => 0,
  'silent'    => 0,
  'MSS50'     => {%default},
  'MSS52'     => {%default, 'crc_prefix' => 'F0'},
  'MSS54'     => {%default, 'crc_prefix' => 'F0'},
  'MSS54HP'   => {%default, 'offset_s_swap' => 0x4000, 'offset_m' => 0x8000, 'offset_m_swap' => 0xC000, 'crc_offset_m' => 0xBFFC}
);

# handle command line options
&GetOptions(
  'help|?|h'    => \$config{'help'},
  'input|i=s'   => \$config{'file_in'},
  'output|o=s'  => \$config{'file_out'},
  'debug|d'     => \$config{'debug'},
  'writeover|w' => \$config{'overwrite'},
  'silent|s'    => \$config{'silent'},
  'version|v'   => \$config{'displayVersion'},
);

# Display version or usage information if requested (or implicitly)
&version if (defined($config{'displayVersion'}));
&usage unless (defined($config{'file_in'}) || $config{'help'});

# Check to see if the binary actually exists, is readable, is binary and is of the proper size
die ("No input file specified.\n")          unless (defined($config{'file_in'}));
die ("Input file does not exist.\n")        unless (-e $config{'file_in'});
die ("Input file is not readable.\n")       unless (-r $config{'file_in'});
die ("Input file is not binary.\n")         unless (-B $config{'file_in'});
die ("Wrong file size to be DME binary.\n") unless (&filesizeValidate($config{'file_in'}));

# Read binary information into %data for analysis
my %data = ('raw_bin' => &readBinFile ($config{'file_in'}));

# Extract the DME type and version from the binary code
($config{'dme_type'}, $config{'dme_version'}) = &getDMEVersion($data{'raw_bin'});

# Make sure master and slave portions are in the proper order (slave, master) based on the first byte of each section
die ("Master/Slave EPROM order invalid.\n") unless ((&bin2hex(substr($data{'raw_bin'}, $config{$config{'dme_type'}}{'offset_s'}, 1)) eq '02') && (&bin2hex(substr($data{'raw_bin'}, $config{$config{'dme_type'}}{'offset_m'}, 1)) eq '01'));
 
# Produce hashes of the original and corected binaries, also provide a means to identify if the checksums are incorrect
my ($validCheckSum, $original, $corrected) = &checksumCalc ($config{'dme_type'}, $data{'raw_bin'}, $config{$config{'dme_type'}});

# Initiate information display
print ("Checksum(s) for " . $config{'file_in'} . " (" . $config{'dme_type'} . ", " . $config{'dme_version'} . ") are ") unless ($config{'silent'});

# The heart of the software, designed to output information and/or correct the checksum and return a proper file
if ($validCheckSum) {
  print("CORRECT:
  Slave  Checksum: 0x" . &bin2hex($original->{'crc_1'}) . "
  Master Checksum: 0x" . &bin2hex($original->{'crc_2'}) . "

  File Checksum:   0x" . sprintf("%04X", &crc16($original->{'raw_bin'})) . "
  File Size:       " . length($original->{'raw_bin'}) . " bytes\n\n") unless ($config{'silent'});
} else {
  print("INCORRECT:
  Original  Slave Checksum:  0x" . &bin2hex($original->{'crc_1'}) . "
  Corrected Slave Checksum:  0x" . $corrected->{'crc_1'} . "

  Original  Master Checksum: 0x" . &bin2hex($original->{'crc_2'}) . "
  Corrected Master Checksum: 0x" . $corrected->{'crc_2'} . "

  Original  File Checksum:   0x" . sprintf("%04X", &crc16($original->{'raw_bin'})) . "
  Corrected File Checksum:   0x" . sprintf("%04X", &crc16($corrected->{'raw_bin'})) . "

  Original  File Size:       " . length($original->{'raw_bin'}) . " bytes
  Corrected File Size:       " . length($corrected->{'raw_bin'}) . " bytes\n\n") unless ($config{'silent'});

# make output file equivalent to input file if overwrite is enabled by CLI and there's no output file defined
  $config{'file_out'} = $config{'file_in'} if ($config{'overwrite'} && ! defined($config{'file_out'}));

# if output file is desired, begin write sequence
  if (defined($config{'file_out'})) {
    die ("ERROR: binary correction failed length check!\n") unless (length($original->{'raw_bin'}) == length($corrected->{'raw_bin'}));
    my $i = 1;
    my $file_out = $config{'file_out'};
# don't overwrite any files - default behaviour can be adjusted by CLI or config option
    while (-e $config{'file_out'} && ! $config{'overwrite'}) {
      print ($config{'file_out'} . " exists, trying ") unless ($config{'silent'});
      $config{'file_out'} = $file_out . "($i)";
      print ($config{'file_out'} . " instead...\n") unless ($config{'silent'});
      $i++;
    }
    print($config{'file_out'} . " is available to write corrected binary...\n") if (($i > 1) && ! $config{'silent'});
    print("Writing corrected binary to " . $config{'file_out'} . "...\n") unless ($config{'silent'});
# Write the binary file to the proper file name
    &writeBinFile($config{'file_out'}, $corrected->{'raw_bin'});
# Re-validate the checksum of the newly created/corrected file
    die ("Checksum correction failed!\n") unless (&checksumValidate($config{'file_out'}));
  } else {
    exit(1);
  }
}

#----------------------------
# SUBROUTINES               |
#----------------------------

# simple usage/syntax
sub usage {
  print("\n" .
         "Usage: " . &fileparse($0, qr/\.[%.]*/) . " --input=[filein.bin] --output=[file_out.bin] --writeover --silent --help --debug --version \n" .
         "  If an output file is not specified, checksum corrections will only be written to stdout.\n" .
         "  --writeover will cause [file_in.bin] to be overwritten if [file_out.bin] is unspecified and checksums have been corrected.\n" .
         "  --writeover will also cause [file_out.bin] to be overwritten if it already exists\n\n"
  );
  exit (1);
}

# display version, then exit.
sub version {
  print (&fileparse($0, qr/\.[%.]*/) . " v" . $config{'version'});
  exit (0);
}

# simple debug function
sub debug ($) {
  print (@_) if $config{'debug'};
}

# Converts a binary string to a hexadecimal string
sub bin2hex($) {
  my $hex_out;
  $hex_out .= sprintf("%02X", ord($_)) foreach (split //, $_[0]);
  $hex_out;
}

# Converts a hexadecimal string to a binary string
sub hex2bin($) {
  ((my $bin_out = $_[0]) =~ s/([a-f0-9][a-f0-9])/chr(hex($1))/egi);
  $bin_out;
}

# Binary file read routine
sub readBinFile ($) {
  my $file_in = shift();
  open FILE_IN, $file_in or die ($!);
  binmode FILE_IN;
  die($!) unless read (FILE_IN, my $raw_bin, -s $file_in);
  close FILE_IN;
  return ($raw_bin);
}

# Binary file write routine
sub writeBinFile ($$) {
  my ($file_out, $file_data) = (@_);
  open BIN_OUT, ">", $file_out;
  binmode BIN_OUT;
  print (BIN_OUT $file_data) or die($!);
  close BIN_OUT;
}

# extract DME Version and type from binary string
sub getDMEVersion ($) {
  my $raw_bin = $_[0];
  # gather up DME version by locating string within the raw binary
  if ($raw_bin =~ /(2113\d{8}[0-9A-Z]{4}){3}/i) {
    my $dme_version = $1;
    if    ($dme_version =~ /2113180[01](\d){4}[0-9A-Z]{4}/i) { return ('MSS50',   $dme_version) }
    elsif ($dme_version =~ /21132100(\d){4}[0-9A-Z]{4}/i)    { return ('MSS52',   $dme_version) }
    elsif ($dme_version =~ /21132200(\d){4}[0-9A-Z]{4}/i)    { return ('MSS54',   $dme_version) }
    elsif ($dme_version =~ /21132[35]00(\d){4}[0-9A-Z]{4}/i) { return ('MSS54HP', $dme_version) }
    else {
      die ("Uncertain DME type: $dme_version\n");
    }
  } else {
    die ("DME version string not located - wrong or improper file format?\n");
  }
}

# The core of the script, doing the dirty work of sifting through the file for the checksums, making comparisons and returning an analysis
sub checksumCalc ($$$) {
  my $dme_type = shift();
  my $raw_bin = shift();
  my %config = %{shift()};
  my %corrected;

  # Extract CRC information from binary
  my %original = (
    crc_1 => substr($raw_bin, $config{'crc_offset_s'}, 4),
    crc_2 => substr($raw_bin, $config{'crc_offset_m'}, 4),
    raw_bin => $raw_bin,
  );

  # Obtain CRC suffix, as it can vary between data types, but it will not change based on file content modification
  $config{'crc_1_suffix'} = &bin2hex(substr($raw_bin, $config{'crc_offset_s'} + 2, 2));
  $config{'crc_2_suffix'} = &bin2hex(substr($raw_bin, $config{'crc_offset_m'} + 2, 2));

  # Extract binary information (MSS54HP specific) and calculate CRC checksum based on DME type, also provide corrected binary (may not differ!)
  #   MSS54HP variants have two main segments with the positions of their calibrations internally swapped per EPROM
  if ($dme_type eq 'MSS54HP') {
      %original = (%original,
      raw_bin => $raw_bin,
      seg_1 => substr($raw_bin, $config{'offset_s'}, 0x4000 - 4),
      seg_2 => substr($raw_bin, $config{'offset_s_swap'}, 0x4000),
      seg_3 => substr($raw_bin, $config{'offset_m'}, 0x4000 - 4),
      seg_4 => substr($raw_bin, $config{'offset_m_swap'}, 0x4000),
    );
    $corrected{'crc_1'} = sprintf("%04X",&crc16($original{'seg_2'} . $original{'seg_1'})) . $config{'crc_1_suffix'};
    $corrected{'crc_2'} = sprintf("%04X",&crc16($original{'seg_4'} . $original{'seg_3'})) . $config{'crc_2_suffix'};
    $corrected{'raw_bin'} = $original{'seg_1'} . &hex2bin($corrected{'crc_1'}) . $original{'seg_2'} . $original{'seg_3'} . &hex2bin($corrected{'crc_2'}) . $original{'seg_4'};
  } else {
  # For MSS50/MSS52/MSS54 DME variants with only two segments
    %original = (%original,
      seg_1 => substr($raw_bin, $config{'offset_s'}, 0x4000 - 4),
      seg_2 => substr($raw_bin, $config{'offset_m'}, 0x4000 - 4),
    );
    $corrected{'crc_1'} = sprintf("%04X", &crc16(&hex2bin($config{'crc_prefix'}) . $original{'seg_1'})) . $config{'crc_1_suffix'};
    $corrected{'crc_2'} = sprintf("%04X", &crc16(&hex2bin($config{'crc_prefix'}) . $original{'seg_2'})) . $config{'crc_2_suffix'};
    $corrected{'raw_bin'} = $original{'seg_1'} . &hex2bin($corrected{'crc_1'}) . $original{'seg_2'} . &hex2bin($corrected{'crc_2'});
  }
  # If the corrected binary is the same as the original binary, the checksums are correct, return TRUE.
  return (($corrected{'raw_bin'} eq $original{'raw_bin'}) ? 1 : 0, \%original, \%corrected);
} 

# Routine to quickly verify a checksum and return true or false
sub checksumValidate ($) {
  my $raw_bin = &readBinFile(shift);
  my ($dme_type, $dme_version) = &getDMEVersion($raw_bin);
  my ($validate, $original, $corrected) = &checksumCalc ($dme_type, $raw_bin, $config{$dme_type});
  return ($validate);
}

# Routine to quickly verify the size of an allowable binary string
sub filesizeValidate ($) {
  my $file_in = shift();
  my $validate = (-s $file_in == 32768 || -s $file_in == 65536) ? 1 : 0;
  return ($validate);
}

# Purposeful routine to generate CRC routines based on a pre-generated table lookup-method
sub crc16 ($) {
  my $string = shift();
  my $crc = 0x0;
  my $pos = -length ($string);
  my @crctable;

  for (my $i = 0x0; $i <= 0xFF; $i++) {
    my $r = $i;
    for (my $j = 0x0; $j < 0x8; $j++) {
      my $t = $r & 1 && 0xA001;
      $t = ($t == 1 ? 0xA001 : $t);
      $r = ($r >> 1)^$t;
    }
    push (@crctable, ($r & 0xFFFF));
  }

  while ($pos) {
    $crc = ($crc>>8)^$crctable[($crc^ord(substr($string, $pos++, 1)))&0xFF];
  }
  $crc ^= 0;
  return ($crc & 0xFFFF);
}
