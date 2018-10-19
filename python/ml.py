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
import tensorflow as tf
from keras.layers import Dense, Dropout
from keras.models import Model, Sequential, load_model
import keras.models
import numpy as np


class ml(gr.sync_block):
    """
    Block that outputs the result of running a single-layer
	Keras model on input vectors from a signal source.
	Requires an input_size for the vector length.
    """
    def __init__(self, input_size, path=None):
        gr.sync_block.__init__(self,
            name="ml",
            in_sig=[(numpy.float32, input_size)],
            out_sig=[(numpy.float32, input_size)])
	try:
	    self.model = load_model(path)
	except: # just for running right now
 	    self.model = Sequential()
	    self.model.add(Dense(input_size, input_dim=input_size))
	    self.model.compile(optimizer='rmsprop',
	          loss='binary_crossentropy',
	          metrics=['accuracy'])
	    self.model._make_predict_function()
	start_input = np.array([[0.1]*input_size]*input_size) # initializes model to avoid lazy eval errors
	# there's probably a better way to do that though
	self.model.predict(start_input)
	print("Initialized block.")



    def work(self, input_items, output_items):
        in0 = input_items[0]
        out = output_items[0]
        print(in0.shape, type(in0))
	prediction = self.model.predict(in0)
	print(prediction)
        out[:] = prediction
        return len(output_items[0])

