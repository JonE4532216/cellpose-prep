#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#%% packages and parameter set up
from pathlib import Path
import numpy as np 
import tifffile as tiff
import re
import xml.etree.ElementTree as ET

#parameters
input_dir = Path('data/raw')
pixel_size_um = 0.325
roi_size_um = 100

#%% list image files in input_dir
 + sorted(input_dir.glob('*.tiff'))
print(f'found {len(tifs)} tif files.')
if not tifs:
    raise SystemExit('put test tif in data/raw first.')
    
#%% read one tif
path = tifs[0] 
with tiff.TiffFile(path) as tf: 
    arr = tf.asarray()
print('shape:', arr.shape, 'dtype:', arr.dtype)

#%% finding the dimension of the tiff that equates 
if arr.ndim == 3:
    channel_axis = int(np.argmin(arr.shape))
else:
    print(f'array has {arr.ndim} dimensions.')
    raise SystemExit("need 3d multichannel image")

arrC = np.moveaxis(arr, channel_axis, 0)
channels = {f"ch{i}": arrC[i] for i in range (arrC.shape[0])}
print("channels:", list(channels.keys()), "single channel shape:", arrC.shape[1:])

#%% 
slide_px = int(round(roi_size_um / pixel_size_um))
print(f"100 um = {slide_px} pixels")

#%%
def pixel_size_um_from_tif(path: Path):
    # returns (um_per_pixel_x, um_per_pixel_y) or (None, None) 
    with tiff.TiffFile(path) as tf:
        ij = getattr(tf, "imagej_metadata", None)
        if ij:
            unit = str(ij.get("unit", "micron")).lower()
            pxw = ij.get("pixel_width") or ij.get("pixelWidth")
            pxh = ij.get("pixel_height") or ij.get("pixelHeight")
            def ij_to_um(v):
                if v is None:
                    return None
                v = float(v)
                if unit in ['micron', ' um', 'µm']:
                    return v
                else:
                    return unit
            x_um = ij_to_um(pxw)
            y_um = ij_to_um(pxh) if pxh is not None else x_um
            if x_um and y_um:
                return x_um, y_um
       # except Exception:
            #pass
    return None, None

test_path = Path("data/raw") / (sorted([p.name for p in Path("data/raw").glob("*.tif")]+[p.name for p in Path("data/raw").glob("*.tiff")])[0])
x_um, y_um = pixel_size_um_from_tif(test_path)
print("pixel size (um):", x_um, y_um)
if x_um is None:
    print("no pixel size metadata found: enter it by hand")
    
#%% test

path = tifs[0]

    
def um_per_px_from_resolution_tags(p: Path):
    with tiff.TiffFile(p) as tf:
        page = tf.pages[0]
        xres = page.tags.get("XResolution")
        yres = page.tags.get("YResolution")
        unit = page.tags.get("ResolutionUnit")
        if not (xres and yres and unit):
            return None, None
        
        def to_float(v):
            try:
                num, den = v.value 
                return float(num) / float(den)
            except Exception:
                try:
                    return float(v.value)
                except Exception:
                    return float(v)
        x_ppu = to_float(xres)
        y_ppu = to_float(yres)
        u = unit.value
        
        if u ==2:
            x_um = 25400.0 / x_ppu
            y_um = 25400.0 / y_ppu
            return x_um, y_um
        if u == 3:   # per centimeter
            x_um = 10000.0 / x_ppu
            y_um = 10000.0 / y_ppu
            return x_um, y_um
        return None, None

x_um, y_um = um_per_px_from_resolution_tags(path)
print("pixel size (µm):", x_um, y_um)

#%%
with tiff.TiffFile(path) as tf:
    arr = tf.asarray()                  # numpy array
    shape = arr.shape                   # e.g., (Z, Y, X) or (C, Z, Y, X, T)
    dtype = arr.dtype

    # Core TIFF tags
    page = tf.pages[0]
    xres = page.tags.get("XResolution")
    yres = page.tags.get("YResolution")
    resolution_unit = page.tags.get("ResolutionUnit")
#    xres = xres.value if xres else None
#    yres = yres.value if yres else None
    res_unit = resolution_unit.value if resolution_unit else None

    # OME-XML (if present) – super useful for pixel size & axes
    omexml = tf.ome_metadata  # string or None
print(f'shape: {shape}, datatype: {dtype}, xres: {xres}, yres: {yres}, res_unit: {res_unit}')
# If omexml is not None, parse it for physical pixel sizes & axes order.
#%%
def pixel_size_from_tiff(path):
    with tiff.TiffFile(path) as tf:
        # Try OME-XML first
        if tf.ome_metadata:
            root = ET.fromstring(tf.ome_metadata)
            ns = {"ome": "http://www.openmicroscopy.org/Schemas/OME/2016-06"}
            px = root.find(".//ome:Pixels", ns)
            if px is not None:
                def f(a):
                    v = px.get(a)
                    return float(v) if v is not None else None
                return {
                    "source": "ome",
                    "um_per_px_x": 1.0 / f("PhysicalSizeX") if f("PhysicalSizeX") else None,  # NOTE: PhysicalSizeX is µm/px, so invert if you want px/µm
                    "um_per_px_y": 1.0 / f("PhysicalSizeY") if f("PhysicalSizeY") else None,
                    "physical_size_x_um": f("PhysicalSizeX"),
                    "physical_size_y_um": f("PhysicalSizeY"),
                }

        # Fallback to TIFF tags
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

        if res_unit == 2:  # inch
            um_per_px_x = 25400.0 / xres
            um_per_px_y = 25400.0 / yres
        elif res_unit == 3:  # centimeter
            um_per_px_x = 10000.0 / xres
            um_per_px_y = 10000.0 / yres
        else:  # no unit — heuristically treat as px/µm
            um_per_px_x = 1.0 / xres
            um_per_px_y = 1.0 / yres

        return {
            "source": "tiff_tags",
            "physical_size_x_um": um_per_px_x,
            "physical_size_y_um": um_per_px_y,
            "assumed_units": "µm (since ResolutionUnit==None)",
            "method": "TIFF tags"
        }
    
#%%
from src.cellpose_prep.scale import real_pixel_size_um
output = real_pixel_size_um(path)
print(output)

#%%
from src.cellpose_prep.io import read_image

read_image(path)