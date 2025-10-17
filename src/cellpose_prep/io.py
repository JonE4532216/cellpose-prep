#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import tifffile as tiff
from .scale import real_pixel_size_um

def read_image(path):
    """
    Open a TIFF image and return:
        img: a NumPy array of pixels
        info: a dictionary with simple fields like shape, dtype and pixel size
    Raises FileNotFoundError if the file doesn't exist.
    
    Uses real_pixel_size_um function from scale module.
    
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"No such file: {path}")
    
    with tiff.TiffFile(path) as tf:
        img = tf.asarray()
        
        px = real_pixel_size_um(path)
        
    return px
    
    