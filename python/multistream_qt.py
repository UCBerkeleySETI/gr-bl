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
from vispy import gloo
from vispy import app
import numpy as np
from gnuradio import gr
import math

VERT_SHADER = """
#version 120

// y coordinate of the position.
attribute float a_position;

// row, col, and time index.
attribute vec3 a_index;
varying vec3 v_index;

// 2D scaling factor (zooming).
uniform vec2 u_scale;

// Size of the table.
uniform vec2 u_size;

// Number of samples per signal.
uniform float u_n;

// Color.
attribute vec3 a_color;
varying vec4 v_color;

// Varying variables used for clipping in the fragment shader.
varying vec2 v_position;
varying vec4 v_ab;

void main() {
    float nrows = u_size.x;
    float ncols = u_size.y;

    // Compute the x coordinate from the time index.
    float x = -1 + 2*a_index.z / (u_n-1);
    vec2 position = vec2(x - (1 - 1 / u_scale.x), a_position);

    // Find the affine transformation for the subplots.
    vec2 a = vec2(1./ncols, 1./nrows)*.9;
    vec2 b = vec2(-1 + 2*(a_index.x+.5) / ncols,
                  -1 + 2*(a_index.y+.5) / nrows);
    // Apply the static subplot transformation + scaling.
    gl_Position = vec4(a*u_scale*position+b, 0.0, 1.0);

    v_color = vec4(a_color, 1.);
    v_index = a_index;

    // For clipping test in the fragment shader.
    v_position = gl_Position.xy;
    v_ab = vec4(a, b);
}
"""

FRAG_SHADER = """
#version 120

varying vec4 v_color;
varying vec3 v_index;

varying vec2 v_position;
varying vec4 v_ab;

void main() {
    gl_FragColor = v_color;

    // Discard the fragments between the signals (emulate glMultiDrawArrays).
    if ((fract(v_index.x) > 0.) || (fract(v_index.y) > 0.))
        discard;

    // Clipping test.
    vec2 test = abs((v_position.xy-v_ab.zw)/v_ab.xy);
    if ((test.x > 1) || (test.y > 1))
        discard;
}
"""


class Canvas(app.Canvas):
    def __init__(self,nrows=8,ncols=8, n=1000, streamer=None):
        app.Canvas.__init__(self, title='Use your wheel to zoom!',
                            keys='interactive')
        self.streamer = streamer
        # Number of cols and rows in the table.
        self.nrows = nrows
        self.ncols = ncols

        # Number of signals.
        self.m = nrows*ncols

        # Number of samples per signal.
        self.n = n

        # Various signal amplitudes.
        self.amplitudes = .1 + .2 * np.random.rand(self.m, 1).astype(np.float32)

        # Generate the signals as a (m, n) array.
        self.y = self.amplitudes * np.random.randn(self.m, self.n).astype(np.float32)
        self.y = np.zeros_like(self.y)

        # Color of each vertex (TODO: make it more efficient by using a GLSL-based
        # color map and the index).
        self.color = np.repeat(np.random.uniform(size=(self.m, 3), low=.5, high=.9),
                          self.n, axis=0).astype(np.float32)

        # Signal 2D index of each vertex (row and col) and x-index (sample index
        # within each signal).
        self.index = np.c_[np.repeat(np.repeat(np.arange(ncols), nrows), n),
                      np.repeat(np.tile(np.arange(nrows), ncols), n),
                      np.tile(np.arange(n), self.m)].astype(np.float32)

        self.program = gloo.Program(VERT_SHADER, FRAG_SHADER)
        self.program['a_position'] = self.y.reshape(-1, 1)
        self.program['a_color'] = self.color
        self.program['a_index'] = self.index
        self.program['u_scale'] = (1., 1.)
        self.program['u_size'] = (nrows, ncols)
        self.program['u_n'] = n

        gloo.set_viewport(0, 0, *self.physical_size)

        self._timer = app.Timer('auto', connect=self.on_timer, start=False)

        gloo.set_state(clear_color='black', blend=True,
                       blend_func=('src_alpha', 'one_minus_src_alpha'))
        self.show()

    def on_resize(self, event):
        gloo.set_viewport(0, 0, *event.physical_size)

    def on_mouse_wheel(self, event):
        dx = np.sign(event.delta[1]) * .05
        scale_x, scale_y = self.program['u_scale']
        scale_x_new, scale_y_new = (scale_x * math.exp(2.5*dx),
                                    scale_y * math.exp(0.0*dx))
        self.program['u_scale'] = (max(1, scale_x_new), max(1, scale_y_new))
        self.update()

    def on_timer(self, event):
        self.program['a_position'].set_data(self.y.ravel().astype(np.float32))
        self.update()
        print("success2", np.sum(self.y))
        

    def on_draw(self, event):
        gloo.clear()
        self.program.draw('line_strip')


class multistream_qt(gr.sync_block):
    """
    docstring for block multistream_qt
    """
    def __init__(self, nrows, ncols, n, m):
        self.nrows = nrows
        self.ncols = ncols
        self.m = m
        assert self.m == nrows*ncols
        gr.sync_block.__init__(self,
            name="multistream_qt",
            in_sig=[(np.complex64, n)]*self.m,
            out_sig=None)
        self.canvas = Canvas(nrows=nrows, ncols=ncols, n=n, streamer=self)
        app.run()
        print("initialized")

    def work(self, input_items, output_items):
        steps = input_items[0].shape[0]
        for i in range(steps):
            for j in range(self.m):
                print(self.m, self.canvas.y.shape, input_items[0].shape)
                self.canvas.y[j] = input_items[j][i].real
            print(np.sum(self.canvas.y))
            print("success", self.canvas.y[0][0])
        return input_items[0].size


if __name__=="__main__":
    canvas = Canvas(nrows=2, ncols=2, n=1024)
    app.run()
    for i in range(100):
        canvas.on_run(None)

        app.process_events()
        #canvas.events.draw()