#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2018 <+YOU OR YOUR COMPANY+>.
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

import numpy
from gnuradio import gr
#from blimpy import Waterfall
import numpy as np

def Waterfall(a, b):
	return None
class fb_source(gr.sync_block):
    """
    Generates vectors from a Filterbank file.
	You can use the 'Vector to Stream' block to
	convert this into a stream.
	TODO: save frequency data into variables
    """
    def __init__(self, filename, output_size, time_intervals):
        gr.sync_block.__init__(self,
            name="fb_source",
            in_sig=None,
            out_sig=[(numpy.float32, output_size)])
	self.file_length = None
	self.filename = filename
	self.output_size = output_size
	self.current_time = 0
	self.time_intervals = time_intervals
	self.set_data()
	self.min_freq = self.frequencies[0]
	self.max_freq = self.frequencies[len(self.frequencies) - 1]
	self.num_freq = self.data.shape[1] // self.output_size
	print(self.min_freq, self.max_freq)
        self.data_generator = self.output_generator()

    def work(self, input_items, output_items):
        out = output_items[0]
	try:
            out[:] = next(self.data_generator)
	except StopIteration:
	    print('getting new data...')
	    if self.current_time > self.file_length:
		self.current_time = 0
	    self.set_data()
	    self.data_generator = self.output_generator()
	    out[:] = next(self.data_generator)
        return len(output_items[0])

    def output_generator(self):
	for row in self.data:
	    row = np.nanmean(np.pad(row.astype(float), (0, (self.num_freq - row.size%self.num_freq) %self.num_freq), mode='constant', constant_values=np.NaN).reshape(-1, self.num_freq), axis=1)
	    yield row[:self.output_size] # this slices off the last values; potential need to fix this by averaging whatever's left & appending

    def set_data(self):
	print('time: ' + str(self.current_time))
	self.signals = Waterfall(self.filename, t_start=self.current_time, t_stop=(self.current_time + self.time_intervals))
	if not self.file_length:
	    self.file_length = self.signals.n_ints_in_file
	self.frequencies, self.data = self.signals.grab_data()
	self.current_time += self.time_intervals
	
