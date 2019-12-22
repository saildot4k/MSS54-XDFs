#!/usr/bin/env python
import os
import sys
import argparse

size_to_type = { 1048576: 'MSS54HP',
                 524288: 'MSS54' }

parameter_offsets = { 'MSS54': (0x48000, 0x08000, 16384),
                      'MSS54HP': (0x88000, 0x08000, 32768) }

def main( ):
    parser = argparse.ArgumentParser()
    parser.add_argument("infile")
    parser.add_argument("outfile")
    args = parser.parse_args()
    
    file_size = os.path.getsize(args.infile)

    if file_size not in size_to_type:
        print "Appears the input file is not a valid MSS54(HP) full bin"

    dme_type = size_to_type[file_size]

    print "Detected %s full binary" % dme_type

    (slave_offset, master_offset, size) = parameter_offsets[dme_type]

    f = open(args.infile, 'rb')
    f.seek(slave_offset)
    slave_data = f.read(size)
    
    f.seek(master_offset)
    master_data = f.read(size)

    f = open(args.outfile, 'wb')
    f.write(slave_data)
    f.write(master_data)

    print "Wrote partial binary to %s" % args.outfile


if __name__ == '__main__':
    main( )