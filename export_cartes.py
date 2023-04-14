# -*- coding: utf-8 -*-
from gimpfu import *

def convert(filename, output, layers):
    img = pdb.gimp_file_load(filename, filename)
    
    for layer in img.layers:
        layer.visible = layer.name in layers
    
    layer = pdb.gimp_image_merge_visible_layers(img, 1)

    pdb.gimp_file_save(img, layer, output, output)
    pdb.gimp_image_delete(img)
