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
from blimpy import Waterfall
import numpy as np

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
	self.filename = filename
	self.output_size = output_size
	self.current_time = 0
	self.time_intervals = time_intervals
	self.set_data()
        self.data_generator = self.output_generator()
	

    def work(self, input_items, output_items):
        out = output_items[0]
	try:
            out[:] = next(self.data_generator)
	except StopIteration:
	    self.set_data()
	    self.data_generator = self.output_generator()
        return len(output_items[0])

    def output_generator(self):
	norm = np.average(np.random.choice(self.data[0], 10))
	for row in self.data:
	    yield self.normalize(row, norm)
    
    def normalize(self, row, norm):
	return np.divide(row, norm)

    def set_data(self):
	self.signals = Waterfall(self.filename, t_start=self.current_time, t_stop=(self.current_time + self.time_intervals))
	self.frequencies, self.data = self.signals.grab_data()
	num_freq = self.data.shape[1] // self.output_size
	range_keep = np.arange(start=0, stop=self.output_size * num_freq, step=num_freq)
	self.data = self.data[:,range_keep]
	self.current_time += self.time_intervals
	
