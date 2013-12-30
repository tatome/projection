projection
==========

Distortion correction for complex multi-projector systems.

This is currently not a complete program, but rather a framework which may be
filled in by the user or just used for inspiration.

In particular, no implementation of a camera module is included as that is 
likely to be specific to a given hardware setup.  detection.py still imports 
_our_ camera implementation and will therefore therefore fail if called, 
unless a camera is implemented.

See http://www.tatome.de for details.
