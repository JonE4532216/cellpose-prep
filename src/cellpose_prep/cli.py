# -*- coding: utf-8 -*-


# run in CL with something like `python3 cellpose-prep/cli.py data/raw`
# where "data/raw" is directory full of images

from src.cellpose_prep.io import read_image


"""
need to specify in cli.py how path variable is defined (should define in CLI)
"""

#testing path for now:
path = 'data/raw/JE064_FTD_G2384_a_2_normoxia_EdU-TBR2-SOX2_20xA-1um_151025_maxip.tif'

read_image(path)

#%%
def main(path):
    
