#!/bin/sh
export VOLK_GENERIC=1
export GR_DONT_LOAD_PREFS=1
export srcdir=/home/shaynak/Documents/gnuradio/gr-bl/python
export PATH=/home/shaynak/Documents/gnuradio/gr-bl/build/python:$PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH
export PYTHONPATH=/home/shaynak/Documents/gnuradio/gr-bl/build/swig:$PYTHONPATH
/usr/bin/python2 /home/shaynak/Documents/gnuradio/gr-bl/python/qa_ml.py 
