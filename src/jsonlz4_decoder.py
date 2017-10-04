# -*- coding: UTF-8 -*-
"""jsonlz4_decoder.py

Implementation that against the decoding of Firefox's compressed bookmarks.
Despite this pure Python implementation can deal the work.
It will be much faster if the 3rd-party "lz4" package is installed.
"""
import argparse
import os
import traceback

_JSONLZ4_MAGIC = b'mozLz40\0'
_JSONLZ4_MAGIC_LEN = len(_JSONLZ4_MAGIC)

def _raise_bad_signature():
    raise ValueError('invalid signature for jsonlz4 file.')

try:
    import lz4

    def decompress_jsonlz4(data):
        """Decompress JsonLz4 bookmarks format."""
        if data[:_JSONLZ4_MAGIC_LEN] != _JSONLZ4_MAGIC:
            _raise_bad_signature()
        return lz4.block.decompress(data[_JSONLZ4_MAGIC_LEN:])

except ImportError: # 3rd-party "lz4" package is not installed.
    import struct
    import io

    def _consume_byte(stream):
        return struct.unpack('B', stream.read(1))[0]

    def _consume_uint16_le(stream):
        return struct.unpack('<H', stream.read(2))[0]

    def _consume_uint32_le(stream):
        return struct.unpack('<I', stream.read(4))[0]

    def _decode_lsic(stream):
        """Decode linear small-integer code."""
        number = 0
        last_byte = _consume_byte(stream)
        while last_byte == 0xff:
            number += 0xff
            last_byte = _consume_byte(stream)
        number += last_byte
        return number

    def _decompress_lz4_block(stream, decompressed, data_size):
        token = _consume_byte(stream)
        # Copy un-compressed literals to output buffer.
        literals_length = token >> 4 # hi-byte of token
        if literals_length == 0x0f:
            literals_length += _decode_lsic(stream)
        decompressed += stream.read(literals_length)
        if stream.tell() == data_size:
            return # Reach the end.
        # Reproduce duplication part.
        match_offset = _consume_uint16_le(stream)
        match_length = token & 0x0f # lo-byte of token
        if match_length == 0x0f:
            match_length += _decode_lsic(stream)
        match_length += 4 # minimum match length
        if match_length >= match_offset: # RLE expansion.
            decompressed += decompressed[-match_offset:] * (match_length // match_offset)
            match_length %= match_offset
        decompressed += decompressed[-match_offset : -match_offset + match_length]

    def decompress_jsonlz4(data):
        """Decompress JsonLz4 bookmarks format."""
        data_size = len(data)
        stream = io.BytesIO(data)
        if stream.read(_JSONLZ4_MAGIC_LEN) != _JSONLZ4_MAGIC:
            _raise_bad_signature()
        decompressed_size = _consume_uint32_le(stream)
        decompressed = bytearray()
        while len(decompressed) < decompressed_size:
            _decompress_lz4_block(stream, decompressed, data_size)
        return decompressed

def _make_new_filename(filename):
    try:
        stem, ext = filename.rsplit(os.path.extsep, 1)
    except ValueError:
        stem, ext = filename, ''
    if ext.lower() == 'jsonlz4':
        return stem + os.path.extsep + 'json'
    return filename + os.path.extsep + 'json'

def _parse_arguments(args=None):
    """Setup and parse program arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filenames', nargs='+', help='jsonlz4 files to decompress.')
    return parser.parse_args(args)

def main():
    """Main function."""
    arguments = _parse_arguments()
    for filename in arguments.filenames:
        print('Decompress:', filename)
        try:
            with open(filename, 'rb') as file:
                data = file.read()
            data = decompress_jsonlz4(data)
            with open(_make_new_filename(filename), 'wb') as file:
                file.write(data)
            print('  OK!')
        except Exception:
            print('  Failed!')
            traceback.print_exc()

if __name__ == '__main__':
    main()
