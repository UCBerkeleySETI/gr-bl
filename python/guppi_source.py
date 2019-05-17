#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2019 <+YOU OR YOUR COMPANY+>.
# 
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

import numpy as np
from gnuradio import gr
from guppi import GuppiRaw
class guppi_source(gr.sync_block):
    """
    docstring for block guppi_source
    """
    def __init__(self, filename, chan=-1, nchan=1, repeat=0):
        gr.sync_block.__init__(self,
            name="guppi_source",
            in_sig=None,
            out_sig=[np.complex64,np.complex64]*nchan)
        self.reader = GuppiRaw(filename) 
        self.header = self.reader.read_first_header()
        self.nblocks = self.reader.find_n_data_blocks()
        self.chan = chan
        self.nchan = nchan
        self.block_idx = 0
        self.block_size = -1
        self.idx = -1
        self.repeat = bool(repeat)

    def work(self, input_items, output_items):
        #outx, outy = output_items[0], output_items[1]
        self.buffer_size = len(output_items[0])
        work_done = 0
        if self.idx < 0:
            work_done = self.set_data()
            self.data_iterator = self.output_generator()
            self.idx = 0
        try:
            next_outs = next(self.data_iterator)
        except(StopIteration):
            work_done = self.set_data()
            self.data_iterator = self.output_generator()
            self.idx = 0
            next_outs = next(self.data_iterator)
        self.idx += self.buffer_size
        #print("buffer sizes", self.buffer_size, next_outs[0].shape)
        for i in range(self.nchan):
            output_items[2*i][:] = next_outs[0][i]
            output_items[2*i+1][:] = next_outs[1][i]
        if work_done < 0:
            return -1
        else:
            return len(output_items[0])

    def output_generator(self):
        while self.idx + self.buffer_size < self.block_size:
            yield self.dx[:,self.idx:self.idx + self.buffer_size], self.dy[:,self.idx:self.idx + self.buffer_size]

    def set_data(self):
        if self.block_idx >= self.nblocks:
            if self.repeat:
                self.block_idx = 0
                self.reader.reset_index()
            else:
                print("End of file, exiting")
                return -1
        print("block progression", self.block_idx, self.nblocks)
        oldx = None
        if self.idx < self.block_size:
            oldx = self.dx[:,self.idx:]
            oldy = self.dy[:,self.idx:]
        self.header, self.dx, self.dy = self.reader.read_next_data_block_int8(self.chan, self.nchan)
        self.dx = (self.dx[...,0].astype(np.float32) + 1.j*self.dx[...,1].astype(np.float32)).astype(np.complex64)
        self.dy = (self.dy[...,0].astype(np.float32) + 1.j*self.dy[...,1].astype(np.float32)).astype(np.complex64)

        if oldx is not None:
            print(oldx.shape, self.dx.shape)
            self.dx = np.concatenate([oldx, self.dx], axis=-1)
            self.dy = np.concatenate([oldy, self.dy], axis=-1)
            oldx = None
            oldy = None
        self.block_size = self.dx.shape[-1]
        self.n_steps = int(self.block_size//self.buffer_size)
        self.block_idx += 1

        return 0
        



