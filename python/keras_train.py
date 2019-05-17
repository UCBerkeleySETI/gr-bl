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
from keras.layers import Dense, Dropout, Input, Flatten
from keras.models import Model, Sequential, load_model
import keras.models
import numpy as np


class keras_train(gr.sync_block):
    """
    Block that outputs the result of running a single-layer
    Keras model on input vectors from a signal source.
    Requires an input_size for the vector length.
    """
    def __init__(self, input_size, path=None):
        gr.sync_block.__init__(self,
            name="keras_train",
            in_sig=[(numpy.float32, input_size)],
            out_sig=None)
       	self.input = Input(shape=(input_size,))
       	self.z = Dense(32, activation='relu')(self.input)
       	self.x = Dense(input_size, activation='tanh')(self.z)
        self.input_size = input_size
       	self.model = Model(self.input, self.x)
       	self.model.compile(loss='mean_squared_error', optimizer='sgd')
        self.model.summary()
    

    def work(self, input_items, output_items):
        in0 = input_items[0][:]
        print(in0.shape,input_items[0].shape, "inshape")
        loss = self.model.train_on_batch(in0, in0)
        print(loss)
        return input_items[0].size
