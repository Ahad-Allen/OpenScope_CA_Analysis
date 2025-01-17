import copy
import logging
import warnings

import numpy as np
import pandas as pd

from util import logger_util, gen_util, plot_util

logger = logging.getLogger(__name__)

# skip tight layout warning
warnings.filterwarnings("ignore", message="This figure includes*")


VDASH = (0, (3, 2))
HDASH = (0, (4, 2))
DARKRED = "#871719"
NEARBLACK = "#656565"
MOUSE_COL_INTERVAL = 0.3

N_LINPLA = 4


#############################################
def get_colors(col_name, line="L2/3"):
    """
    get_colors(col_name)

    Returns exact color for a specific line.

    Required args:
        - col_name (str): 
            color name

    Optional args:
        - line (str): 
            line to plot
            default: "L2/3"
    
    Returns:
        - col (str): color
    """
    
    if line in ["L23", "L23-Cux2"] :
        col = plot_util.get_color_range(1, col_name)[0]
    elif line in ["L5", "L5-Rbp4"]:
        col = plot_util.get_color_range(6, col_name)[4]
    else:
        raise ValueError(f"Line '{line}' not recognized")

    return col


#############################################
def get_line_plane_name(line="L2/3-Cux2", plane="soma"):
    """
    get_line_plane_name()

    Returns line/plane short name.

    Optional args:
        - line (str):
            line name
            default: "L2/3-Cux2"
        - plane (str):
            plane_name
            default: "soma"

    Returns:
        - line_plane_name (str):
            short name for the line/plane
    """

    line = line.split("-")[0].replace("23", "2/3")
    line_plane_name = f"{line}-{plane[0].upper()}"

    return line_plane_name


#############################################
def get_line_plane_idxs(line="L23-Cux2", plane="soma", flat=False):
    """
    get_line_plane_idxs()

    Returns parameters for a line/plane combination graph.

    Optional args:
        - line (str):
            line name
            default: "L2/3-Cux2"
        - plane (str):
            plane_name
            default: "soma"

    Returns:
        if flat:
        - idx (int):
            line/plane index
        
        else:
        - li (int): 
            line index
        - pl (int): 
            plane index

        and in both cases:
        - col (str): 
            color hex code
        - dash (tuple or None): 
            dash pattern
    """

    lines, planes = ["L23-Cux2", "L5-Rbp4"], ["dend", "soma"]
    pla_col_names = ["green", "blue"]

    if line not in lines:
        gen_util.accepted_values_error("line", line, lines)
    if plane not in planes:
        gen_util.accepted_values_error("plane", plane, planes)

    li = lines.index(line)
    pl = planes.index(plane)
    col = get_colors(pla_col_names[pl], line=line)
    dash = VDASH if "L5" in line else None

    if flat:
        idx = pl + li * len(lines)
        return idx, col, dash

    else:
        return li, pl, col, dash


