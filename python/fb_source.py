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
    def __init__(self, filename, output_size):
        gr.sync_block.__init__(self,
            name="fb_source",
            in_sig=None,
            out_sig=[(numpy.float32, output_size)])
 	self.signals = Waterfall(filename)
	self.frequencies, self.data = self.signals.grab_data()
#	self.data = np.arange(8192 * output_size) # for testing when filterbank files are too big to load
	self.data = self.data.reshape(-1, output_size)
        self.data_generator = output_generator(self.data)
	

    def work(self, input_items, output_items):
        out = output_items[0]
	try:
            out[:] = next(self.data_generator)
	except StopIteration:
	    self.data_generator = output_generator(self.data)
        return len(output_items[0])

def output_generator(data):
    for row in data:
	yield row
