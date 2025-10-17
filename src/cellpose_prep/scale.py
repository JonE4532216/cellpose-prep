#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tifffile as tiff

def real_pixel_size_um(path):
    """
    Function used in io.py while opening images to calculate um/pixel.
    Therefore determines the scale and real dimensions of TIF files.

    Parameters
    ----------
    path : TYPE
        DESCRIPTION.

    Returns
    -------
    TYPE
        DESCRIPTION.

    """
    with tiff.TiffFile(path) as tf:
        page = tf.pages[0]
        def rational_to_float(tag):
            if tag is None: return None
            num, den = tag.value
            return float(num) / float(den) if den else None
        xres = rational_to_float(page.tags.get("XResolution"))
        yres = rational_to_float(page.tags.get("YResolution"))
        res_unit = page.tags.get("ResolutionUnit").value if page.tags.get("ResolutionUnit") else 1
        
        if xres is None or yres is None:
            return {"source": "none", "physical_size_x_um": None, "physical_size_y_um": None}
        
        if res_unit == 2:
            um_per_px_x = 25400 / xres
            um_per_px_y = 25400 /yres
        elif res_unit == 3:
            um_per_px_x = 10000 / xres
            um_per_px_y = 10000 / yres
        else:
            um_per_px_x = 1 / xres
            um_per_px_y = 1 /yres

        if int(round(um_per_px_x, 5)) == int(round(um_per_px_y, 5)):
            return {
                "pixel_size (um)": um_per_px_x
                }
        else:
            return {
                "source": "tiff_tags",
                "pyhsical_size_x_um": um_per_px_x,
                "physical_size_y_um": um_per_px_y,
                "assumed_units": "um (since ResolutionUnit == None)"
                }