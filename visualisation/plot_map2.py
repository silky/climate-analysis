"""
Collection of commonly used functions for plotting spatial data.

Included functions: 

"""

# Import general Python modules #

import os, sys, pdb, re
import argparse

import iris
from iris.time import PartialDateTime
import iris.plot as iplt
import iris.quickplot as qplt

import matplotlib.pyplot as plt
import matplotlib.cm as mpl_cm

import cartopy
import cartopy.crs as ccrs

import numpy


# Import my modules #

cwd = os.getcwd()
repo_dir = '/'
for directory in cwd.split('/')[1:]:
    repo_dir = os.path.join(repo_dir, directory)
    if directory == 'phd':
        break

modules_dir = os.path.join(repo_dir, 'modules')
sys.path.append(modules_dir)

try:
    import general_io as gio
except ImportError:
    raise ImportError('Must run this script from anywhere within the phd git repo')

# Define functions

def get_time_constraint(start, end):
    """Set the time constraint"""
    
    date_pattern = '([0-9]{4})-([0-9]{1,2})-([0-9]{1,2})'
    assert re.search(date_pattern, start) or start == None
    assert re.search(date_pattern, end) or end == None
    
    if not start and not end:
        time_constraint = iris.Constraint()
    elif (start and not end) or (start == end):
        year, month, day = start.split('-')    
        time_constraint = iris.Constraint(time=iris.time.PartialDateTime(year=year, month=month, day=day))
    elif end and not start:
        year, month, day = end.split('-')    
        time_constraint = iris.Constraint(time=iris.time.PartialDateTime(year=year, month=month, day=day))
    else:  
        start_year, start_month, start_day = start.split('-') 
        end_year, end_month, end_day = end.split('-')
        time_constraint = iris.Constraint(time=lambda t: PartialDateTime(year=start_year, month=start_month, day=start_day) <= t <= PartialDateTime(year=start_year, month=start_month, day=start_day))

    return time_constraint


def _main(inargs):
    """Run program."""

    # Extract data #
    
    time_constraint = get_time_constraint(inargs.start, inargs.end)
    lat_constraint = iris.Constraint(latitude=lambda y: y <= 0.0)

    with iris.FUTURE.context(cell_datetime_objects=True):
        u_cube = iris.load_cube(inargs.u_file, inargs.u_var & time_constraint & lat_constraint)
        v_cube = iris.load_cube(inargs.u_file, inargs.u_var & time_constraint & lat_constraint)

    u_temporal_mean = u_cube.collapsed('time', iris.analysis.MEAN)  
    v_temporal_mean = v_cube.collapsed('time', iris.analysis.MEAN)

    ## Define the data
    x = u_temporal_mean.coords('longitude')[0].points
    y = u_temporal_mean.coords('latitude')[0].points
    u = u_temporal_mean.data
    v = v_temporal_mean.data

    plt.figure(figsize=(8, 10))

    ## Select the map projection
    ax = plt.axes(projection=ccrs.SouthPolarStereo())
   
    ax.set_extent((x.min(), x.max(), y.min(), -30.0), crs=ccrs.PlateCarree())
    
    ## Plot coast and gridlines (currently an error with coastline plotting)
    ax.coastlines()
    ax.gridlines()
    #ax.set_global()

    ## Plot the data
    # Streamplot
    magnitude = (u ** 2 + v ** 2) ** 0.5
    ax.streamplot(x, y, u, v, transform=ccrs.PlateCarree(), linewidth=2, density=2, color=magnitude)

    # Wind vectors
    #ax.quiver(x, y, u, v, transform=ccrs.PlateCarree(), regrid_shape=40) 

    # Contour
    #qplt.contourf(u_temporal_mean)

    plt.savefig(inargs.ofile)


if __name__ == '__main__':

    extra_info = """
improvements:
  

"""

    description='Plot spatial map.'
    parser = argparse.ArgumentParser(description=description, 
                                     epilog=extra_info,
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("u_file", type=str, help="input file name for the zonal wind")
    parser.add_argument("u_var", type=str, help="standard_name for the zonal wind")
    parser.add_argument("v_file", type=str, help="input file name for the meridional wind")
    parser.add_argument("v_var", type=str, help="standard_name for the meridional wind")
#    parser.add_argument("zg_file", type=str, help="input file name for the geopoential height")
#    parser.add_argument("zg_var", type=str, help="standard_name for the geopotential height")

    parser.add_argument("--start", type=str, default=None,
                        help="start date in YYYY-MM-DD format [default = None])")
    parser.add_argument("--end", type=str, default=None,
                        help="end date in YYY-MM-DD format [default = None], let START=END for single time step (can be None)")
 
    parser.add_argument("--ofile", type=str, default='test.png',
                        help="name of output file [default: test.png]")

    
    parser.add_argument("--quiver_type", type=str, choices=('wind', 'waf'),
                        help="type of quiver being plotted [defualt: wind]")
    parser.add_argument("--quiver_thin", type=int, 
                        help="thinning factor for plotting quivers [defualt: 1]")
    parser.add_argument("--key_value", type=float, 
                        help="size of the wind quiver in the key (plot is not scaled to this) [defualt: 1]")
    parser.add_argument("--quiver_scale", type=float, 
                        help="data units per arrow length unit (smaller value means longer arrow) [defualt: 170]")
    parser.add_argument("--quiver_width", type=float,
                        help="shaft width in arrow units [default: 0.0015, i.e. 0.0015 times the width of the plot]")
    parser.add_argument("--quiver_headwidth", type=float,
                        help="head width as multiple of shaft width [default: 3.5]")
    parser.add_argument("--quiver_headlength", type=float, 
                        help="head length as multiple of shaft width [default: 4.0]")


    args = parser.parse_args()              

    main(args)