projection
==========

Distortion correction for complex multi-projector systems.

This is currently not a complete program, but rather a framework which may be
filled in by the user or just used for inspiration.

It is also not complete, yet --- I'm adding parts as I'm describing the 
project on my website and cleaning up the code presentable to the general
public.

In particular, no implementation of a camera module is included as that is 
likely to be specific to a given hardware setup.  detection.py still imports 
_our_ camera implementation and will therefore fail if called, unless a 
camera is implemented.

See http://www.tatome.de for details and a way to contact me.
