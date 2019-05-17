#!/usr/bin/env python
"""
# guppi.py

A python file handler for guppi RAW files from the GBT.

The guppi raw format consists of a FITS-like header, followed by a block of data,
and repeated over and over until the end of the file.
"""

import numpy as np
import os
import time
from pprint import pprint
from utils import unpack, rebin
import sys

PYTHON3 = sys.version_info >= (3, 0)

# Check if $DISPLAY is set (for handling plotting on remote machines with no X-forwarding)
# if 'DISPLAY' in os.environ.keys():

#     try:
#         import matplotlib
#         # matplotlib.use('Qt5Agg')
#     except ImportError:
#         pass
#     import pylab as plt
# else:
#     import matplotlib

#     matplotlib.use('Agg')
#     import pylab as plt

###
# Config values
###

MAX_PLT_POINTS = 65536 * 4  # Max number of points in matplotlib plot
MAX_IMSHOW_POINTS = (8192, 4096)  # Max number of points in imshow plot
MAX_DATA_ARRAY_SIZE = 1024 * 1024 * 1024  # Max size of data array to load into memory


class EndOfFileError(Exception):
    pass


class GuppiRaw(object):
    """ Python class for reading Guppi raw files

    Args:
        filename (str): name of the .raw file to open

    Optional args:
        n_blocks (int): if number of blocks to read is known, set it here.
                        This saves seeking through the file to check how many
                        integrations there are in the file.
    """

    def __init__(self, filename, n_blocks=None):
        self.filename = filename
        if PYTHON3:
            self.file_obj = open(filename, 'rb')
        else:
            self.file_obj = open(filename, 'r')
        self.filesize = os.path.getsize(filename)

        if not n_blocks:
            self.n_blocks = self.find_n_data_blocks()

        else:
            self.n_blocks = n_blocks

        self._d = np.zeros(1, dtype='complex64')
        self._d_x = np.zeros(1, dtype='int8')
        self._d_y = np.zeros(1, dtype='int8')
        self.data_gen = None

    def __enter__(self):
        """
        reopen the file each time a `with` block is entered
        :return:
        """
        if PYTHON3:
            self.file_obj = open(self.filename, 'rb')
        else:
            self.file_obj = open(self.filename, 'r')
        self.filesize = os.path.getsize(self.filename)
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """
        closes the file after `with` block has exited
        :param exception_type:
        :param exception_value:
        :param traceback:
        :return:
        """
        self.file_obj.close()

    def __repr__(self):
        return "<GuppiRaw file handler for %s>" % self.filename

    def read_header(self):
        """ Read next header (multiple headers in file)

        Returns:
            (header, data_idx) - a dictionary of keyword:value header data and
            also the byte index of where the corresponding data block resides.
        """
        start_idx = self.file_obj.tell()
        key, val = '', ''

        header_dict = {}
        keep_reading = True

        first_line = self.file_obj

        try:
            while keep_reading:
                if start_idx + 80 > self.filesize:
                    keep_reading = False
                    raise EndOfFileError("End Of Data File")
                line = self.file_obj.read(80)
                if PYTHON3:
                    line = line.decode("utf-8")
                # print line
                if line.startswith('END'):
                    keep_reading = False
                    break
                else:
                    key, val = line.split('=')
                    key, val = key.strip(), val.strip()

                    if "'" in val:
                        # Items in quotes are strings
                        val = str(val.strip("'").strip())
                    elif "." in val:
                        # Items with periods are floats (if not a string)
                        val = float(val)
                    else:
                        # Otherwise it's an integer
                        val = int(val)

                header_dict[key] = val
        except ValueError:
            print("CURRENT LINE: ", line)
            print("BLOCK START IDX: ", start_idx)
            print("FILE SIZE: ", self.filesize)
            print("NEXT 512 BYTES: \n")
            print(self.file_obj.read(512))
            raise

        data_idx = self.file_obj.tell()

        # Seek past padding if DIRECTIO is being used
        if "DIRECTIO" in header_dict.keys():
            if int(header_dict["DIRECTIO"]) == 1:
                if data_idx % 512:
                    data_idx += (512 - data_idx % 512)

        self.file_obj.seek(start_idx)
        return header_dict, data_idx

    def read_first_header(self):
        """ Read first header in file

        Returns:
            header (dict): keyword:value pairs of header metadata
        """
        self.file_obj.seek(0)
        header_dict, pos = self.read_header()
        self.file_obj.seek(0)
        return header_dict

    def read_next_data_block_shape(self):
        header, data_idx = self.read_header()
        n_chan = int(header['OBSNCHAN'])
        n_pol = int(header['NPOL'])
        n_bit = int(header['NBITS'])
        n_samples = int(int(header['BLOCSIZE']) / (n_chan * n_pol * (n_bit / 8)))
        print("NP",n_pol, n_bit)
        is_chanmaj = False
        if 'CHANMAJ' in header.keys():
            if int(header['CHANMAJ']) == 1:
                is_chanmaj = True
        if is_chanmaj:
            dshape = (int(n_samples), n_chan, n_pol)
        else:
            dshape = (n_chan, int(n_samples), n_pol)
        return dshape

    def get_data(self, chan=-1, nchan=1):
        """
        returns a generator object that reads data a block at a time;
        the generator prints "File depleted" and returns nothing when all data in the file has been read.
        :return:
        """
        with self as gen:
            while True:
                try:
                    yield gen.generator_read_next_data_block_int8(chan, nchan)
                except EndOfFileError as e:
                    print("\nFile depleted")
                    raise StopIteration

    def read_next_data_block_int8(self, chan=-1, nchan=1):
        """
        Instantiates a new generator as self.data_gen if there wasn't one already
        Calls next() on the generator once and returns the value
        Handles generator depletion
        :return: header, data_x, data_y
        """
        if not self.data_gen:
            self.data_gen = self.get_data(chan, nchan)
        try:
            header, data_x, data_y = next(self.data_gen)
        except StopIteration:
            self.data_gen = None
            return None, None, None
        self._d_x, self._d_y = data_x, data_y
        return header, self._d_x, self._d_y

    def generator_read_next_data_block_int8(self,chan=-1, nchan=1):
        """ Read the next block of data and its header

        Returns: (header, data)
            header (dict): dictionary of header metadata
            data (np.array): Numpy array of data, converted into to complex64.
        """
        header, head_idx = self.read_header()
        #print(head_idx)
        n_chan = int(header['OBSNCHAN'])
        n_pol = int(header['NPOL'])  #should be 4
        if n_pol == 2:
            n_pol = 4
        n_bit = int(header['NBITS'])
        blocsize= int(header['BLOCSIZE'])
        if chan > 0:
            data_idx = head_idx + chan * n_pol * int(n_bit / 8)
            blocsize //= (64//nchan)
            n_chan = nchan
        else:
            data_idx = head_idx
        self.file_obj.seek(data_idx,0)


        n_samples = int(blocsize / (n_chan * n_pol * (float(n_bit) / 8)))

        d = np.fromfile(self.file_obj, count=blocsize, dtype='int8')

        # Handle 2-bit and 4-bit data
        if n_bit != 8:
            d = unpack(d, n_bit)

        d = d.reshape((n_chan, n_samples, n_pol))  # Real, imag

        if self._d_x.shape != d[..., 0:2].shape:
            self._d_x = np.ascontiguousarray(np.zeros(d[..., 0:2].shape, dtype='int8'))
            self._d_y = np.ascontiguousarray(np.zeros(d[..., 2:4].shape, dtype='int8'))
        
        self._d_x[:] = d[..., 0:2]
        self._d_y[:] = d[..., 2:4]
        if chan > 0:
            data_idx = head_idx + header['BLOCSIZE']
            self.file_obj.seek(data_idx,0)
        return header, self._d_x, self._d_y


    def read_next_data_block(self):
        """ Read the next block of data and its header

        Returns: (header, data)
            header (dict): dictionary of header metadata
            data (np.array): Numpy array of data, converted into to complex64.
        """
        header, data_idx = self.read_header()
        self.file_obj.seek(data_idx,0)

        # Read data and reshape

        n_chan = int(header['OBSNCHAN'])
        n_pol = int(header['NPOL'])
        n_bit = int(header['NBITS'])
        n_samples = int(int(header['BLOCSIZE']) / (n_chan * n_pol * (n_bit / 8)))

        d = np.ascontiguousarray(np.fromfile(self.file_obj, count=header['BLOCSIZE'], dtype='int8'))

        # Handle 2-bit and 4-bit data
        if n_bit != 8:
            d = unpack(d, n_bit)

        dshape = self.read_next_data_block_shape()

        d = d.reshape(dshape)  # Real, imag

        if self._d.shape != d.shape:
            self._d = np.zeros(d.shape, dtype='float32')

        self._d[:] = d

        return header, self._d[:].view('complex64')

    def find_n_data_blocks(self):
        """ Seek through the file to find how many data blocks there are in the file

        Returns:
            n_blocks (int): number of data blocks in the file
        """
        self.file_obj.seek(0)
        header0, data_idx0 = self.read_header()

        self.file_obj.seek(data_idx0)
        block_size = int(header0['BLOCSIZE'])
        n_bits = int(header0['NBITS'])
        self.file_obj.seek(int(header0['BLOCSIZE']), 1)
        n_blocks = 1
        end_found = False
        while not end_found:
            try:
                header, data_idx = self.read_header()
                self.file_obj.seek(data_idx)
                self.file_obj.seek(header['BLOCSIZE'], 1)
                n_blocks += 1
            except EndOfFileError:
                end_found = True
                break

        self.file_obj.seek(0)
        return n_blocks

    def reset_index(self):
        """ Return file_obj seek to start of file """
        self.file_obj.seek(0)

    def print_stats(self):
        """ Compute some basic stats on the next block of data """

        header, data = self.read_next_data_block()
        data = data.view('float32')

        print("AVG: %2.3f" % data.mean())
        print("STD: %2.3f" % data.std())
        print("MAX: %2.3f" % data.max())
        print("MIN: %2.3f" % data.min())

        #import pylab as plt

   

def cmd_tool():
    path = "/home/yunfanz/Downloads/blc3_guppi_57386_VOYAGER1_0004.0000.raw"
    reader = GuppiRaw(path)
    print(reader.read_next_data_block_shape())
    for i in range(2):
        h, x, y = reader.read_next_data_block_int8(chan=32, nchan=1)
        print(h)
        print(x.shape, y.shape)
    return

if __name__ == "__main__":
    cmd_tool()