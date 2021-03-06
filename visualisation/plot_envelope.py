"""
Filename:     plot_envelope.py
Author:       Damien Irving, d.irving@student.unimelb.edu.au
Description:  Plot wave envelope and associated streamfunction anomalies

"""

# Import general Python modules #

import os, sys, pdb
import argparse

import numpy
import cdms2


# Import my modules #

cwd = os.getcwd()
repo_dir = '/'
for directory in cwd.split('/')[1:]:
    repo_dir = os.path.join(repo_dir, directory)
    if directory == 'phd':
        break

modules_dir = os.path.join(repo_dir, 'modules')
sys.path.append(modules_dir)
vis_dir = os.path.join(repo_dir, 'visualisation')
sys.path.append(vis_dir)

try:
    import coordinate_rotation as rot
    import netcdf_io as nio
    import general_io as gio
    import plot_map
except ImportError:
    raise ImportError('Must run this script from anywhere within the phd git repo')


# Define functions #

def extract_data(inargs):
    """Extract input data"""

    env_data = nio.InputData(inargs.env_file, inargs.env_var,
                             **nio.dict_filter(vars(inargs), ['time', 'region']))
    opt_data = {}
    for opt in ['uwind', 'vwind', 'contour']:    
        try:
            opt_data[opt] = nio.InputData(eval('inargs.'+opt+'[0]'), 
                                          eval('inargs.'+opt+'[1]'), 
                                          **nio.dict_filter(vars(inargs), ['time', 'region']))
        except AttributeError:
            opt_data[opt] = None
    
    return env_data, opt_data['uwind'], opt_data['vwind'], opt_data['contour']


def restore_env(indata_env, rotation_details):
    """Restore the rotated envelope data to a typical lat/lon grid
    
    rotation_details   : [np_lat, np_lon, pm_lat, pm_lon]
    
    """
    
    lat_axis = indata_env.data.getLatitude()
    lon_axis = indata_env.data.getLongitude()
    lats, lons = nio.coordinate_pairs(lat_axis[:], lon_axis[:])
    grid = indata_env.data.getGrid()

    new_np = rotation_details[0:2]
    pm_point = rotation_details[2:4]
    
    env_restored = rot.switch_regular_axes(indata_env.data, lats, lons, 
                                           lat_axis[:], lon_axis[:],
                                           new_np, pm_point=pm_point, invert=False)
    
    if 't' in indata_env.data.getOrder():
        axis_list = [indata_env.data.getTime(), lat_axis, lon_axis]
    else: 
        axis_list = [lat_axis, lon_axis]
    
    env_restored = cdms2.createVariable(env_restored, grid=grid, axes=axis_list)
    
    return env_restored
 

def extract_extent(fname):
    """Extract the extent information from an input file"""
    
    f = open(fname, 'r')
    lines = f.readlines()
    f.close()

    extent_output = {}
    for line in lines[2:]:  #$ skip the header row
        data = line.split(',')
    year, month, day = data[0].split('-')
    date = (int(year), int(month), int(day))
    start_lon = float(data[1])
    end_lon = float(data[2])
    
    extent_output[date] = (start_lon, end_lon)

    return extent_output


def plot_settings(timescale, timestep, variable, user_ticks):
    """Define the settings for the wind barbs and colourbar.
    
    If user_ticks is None (i.e. the user didn't supply the ticks),
    then the decision is based on the timescale and timestep.
    
    timescale  -->   e.g. 30day-runmean
    timestep   -->   e.g. daily, monthly
    
    """

    # Wind barbs
    if timestep == 'monthly':
        keyval = 5
        quiv_scale = 200
        quiv_width = 0.002
    else:
        keyval = 10
        quiv_scale = 300
        quiv_width = 0.002

    # Colourbar
    ticks_tscale_dict = {('va', '001day-runmean'): numpy.arange(0, 50, 4),
                         ('va', '005day-runmean'): numpy.arange(0, 30, 2),
                         ('va', '030day-runmean'): numpy.arange(0, 19.5, 1.5),
                         ('va', '090day-runmean'): numpy.arange(0, 12, 1),
                         ('va', '180day-runmean'): numpy.arange(0, 12, 1),
                         ('zg', '030day-runmean'): numpy.arange(0, 275, 25)}
    ticks_tstep_dict = {('va', 'daily'): ticks_tscale_dict[('va', '001day-runmean')],
                        ('va', 'monthly'): ticks_tscale_dict[('va', '030day-runmean')],
                        ('zg', 'monthly'): ticks_tscale_dict[('zg', '030day-runmean')]}

    if user_ticks:
        ticks = user_ticks
    elif (variable in map(lambda x:x[0], ticks_tscale_dict.keys())) and (timescale in map(lambda x:x[1], ticks_tscale_dict.keys())):
        ticks = list(ticks_tscale_dict[(variable, timescale)])
    elif (variable in map(lambda x:x[0], ticks_tstep_dict.keys())) and (timestep in map(lambda x:x[1], ticks_tstep_dict.keys())):
        ticks = list(ticks_tstep_dict[(variable, timestep)])
    else:
        ticks = None

    return keyval, quiv_scale, quiv_width, ticks


def main(inargs):
    """Create the plot"""

    # Read input data
    indata_env, indata_u, indata_v, indata_contour = extract_data(inargs) 
    if inargs.extent:
        indata_extent = extract_extent(inargs.extent[0])

    # Restore env data to standard lat/lon grid
    if inargs.rotation:
        env_data = restore_env(indata_env, inargs.rotation)
        np = inargs.rotation[0:2]
    else:
        env_data = indata_env.data
        np = None

    # Plot settings
    keyval, quiv_scale, quiv_width, ticks = plot_settings(inargs.timescale, inargs.timestep, inargs.env_var, inargs.ticks)      

    # Initialise any boxes that need to be plotted
    box_list = []
    if inargs.search_region:
        south_lat, north_lat, west_lon, east_lon = inargs.search_region[0:4]
        box_list.append([south_lat, north_lat, west_lon, east_lon, 'green', 'dashed'])
    if inargs.raphael:
        for region in ['zw31', 'zw32', 'zw33']:
            box_list.append([region, 'purple', 'solid'])            

    # Plot each timestep
    for date in indata_env.data.getTime().asComponentTime()[::inargs.stride]:

        date_bounds, date_abbrev = nio.get_cdms2_tbounds(date, inargs.timescale)
    
        env_data_select = [env_data(time=(date_bounds[0], date_bounds[1]), squeeze=1),]
        u_data = [indata_u.data(time=(date_bounds[0], date_bounds[1]), squeeze=1),] if indata_u else None
        v_data = [indata_v.data(time=(date_bounds[0], date_bounds[1]), squeeze=1),] if indata_v else None
        contour_data = [indata_contour.data(time=(date_bounds[0], date_bounds[1]), squeeze=1),] if indata_contour else None
        
        if inargs.extent:
            west_lon, east_lon = indata_extent[(int(year), int(month), int(day))]
            if west_lon != east_lon:
                south_lat, north_lat = inargs.extent[1:]
                box_list.append([float(south_lat), float(north_lat), west_lon, east_lon, 'blue', 'solid'])
        
        if inargs.no_title:
            title = None
        else:
            title = 'Wave envelope, %s' %(date_abbrev)

        ofile = gio.set_outfile_date(inargs.ofile, date_abbrev)

        plot_map.multiplot(env_data_select,
                           ofile=ofile,
                           title=title,
                           region=inargs.region,
                           units='$m s^{-1}$',
                           draw_axis=True,
                           delat=10, delon=30,
                           contour=True,
                           ticks=ticks, discrete_segments=inargs.segments, colourbar_colour=inargs.palette,
                           contour_data=contour_data, contour_ticks=inargs.contour_ticks,
                           uwnd_data=u_data, vwnd_data=v_data, quiver_thin=9, key_value=keyval,
                           quiver_scale=quiv_scale, quiver_width=quiv_width,
                           projection=inargs.projection, 
                           extend='max',
                           box=box_list,
                           box_np=np,
                           image_size=inargs.image_size)

        if ticks:
            ticks = ticks[0: -1]   # Fix for weird thing where it keeps appending to 
                                   # the end of the ticks list, presumably due to the 
                                   # extend = 'max' 


if __name__ == '__main__':

    extra_info="""
example (vortex.earthsci.unimelb.edu.au):
    /usr/local/uvcdat/1.3.0/bin/cdat plot_envelope.py 
    /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/zw3/env-w234-va_Merra_250hPa_30day-runmean_r360x181.nc 
    env daily
    --timescale 030day-runmean 
    --extent /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/zw3/zw3-stats_Merra_250hPa_30day-runmean_r360x181-mermax-lat70S40S_env-w234-va-ampmin7.csv -70 -40 
    --contour /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/sf_Merra_250hPa_30day-runmean-zonal-anom_native.nc sf 
    --time 2003-01-01 2003-12-31 none 
    --projection spstere 
    --ofile /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/zw3/figures/env-w234-va_Merra_250hPa_30day-runmean_r360x181_2003-12-31.png

    /usr/local/uvcdat/1.3.0/bin/cdat plot_envelope.py
    /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260.nc
    env 20 260 0 0 daily 
    --contour /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/sf_Merra_250hPa_daily-anom-wrt-all_native.nc sf
    --ofile /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/figures/env/vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np26-260
    --time 1981-06-01 1981-06-30 none
    --search_region 20 260 225 335
    --region world-psa
    
    /usr/local/uvcdat/1.3.0/bin/cdat plot_envelope.py
    /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/env-w234-va_Merra_250hPa_daily_r360x181.nc 
    env daily
    --time 2003-06-01 2003-06-30 none
    --region world-dateline-duplicate360
    --contour /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/sf_Merra_250hPa_daily_native.nc sf
    --ofile /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/figures/env-w234-va_Merra_250hPa_daily_r360x181
    --ticks 0 4 8 12 16 20 24 28 32
    --contour_ticks -140 -120 -100 -80 -60 -40 -20 0 20 40 60 80 100 120 140
    --projection spstere
    
"""
  
    description='Plot wave envelope and associated wind quivers and/or contour lines (e.g. for the streamfunction)'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("env_file", type=str, help="envelope file")
    parser.add_argument("env_var", type=str, help="envelope variable")
    parser.add_argument("timestep", type=str, help="distance between timesteps (e.g. daily, monthly)")
    
    parser.add_argument("--timescale", type=str, default=None, 
                        help="timescale of the input data (e.g. 005day-runmean) - use this when timescale differs from timestep")
    parser.add_argument("--time", type=str, nargs=3, metavar=('START_DATE', 'END_DATE', 'MONTHS'),
                        help="Time period [default = entire]")
    parser.add_argument("--region", type=str, choices=nio.regions.keys(), default='world-dateline',
                        help="name of region to plot [default: world-dateline]")
    parser.add_argument("--stride", type=int, default=1,
                        help="Stride for dates to plot (e.g. 3 would plot every third timestep)")

    parser.add_argument("--rotation", type=float, nargs=4, metavar=('NP_LAT', 'NP_LON', 'PM_LAT', 'PM_LON'), default=None,
                        help="Details of the rotation that has been applied to the envelope data") 

    parser.add_argument("--uwind", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="zonal wind anomaly file and variable")
    parser.add_argument("--vwind", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="meridional wind anomaly file and variable")
    parser.add_argument("--contour", type=str, nargs=2, metavar=('FILE', 'VAR'),
                        help="file and variable for contour lines")
    parser.add_argument("--ofile", type=str, default='test_envelope_1979-01-01.png', 
                        help="name of output file (include the date of one of the timesteps in YYYY-MM-DD format - it will be replaced in place)")
                        
    parser.add_argument("--ticks", type=float, nargs='*', default=None,
                        help="List of tick marks to appear on the colour bar [default: auto]")
    parser.add_argument("--contour_ticks", type=float, nargs='*', default=15, 
                        help="list of tick marks for the contours, or just the number of contour lines")
    parser.add_argument("--segments", type=str, nargs='*', default=None,
                        help="List of colours to appear on the colour bar")
    parser.add_argument("--palette", type=str, default='Oranges',
                        help="Colourbar name [default: Organges]")

    parser.add_argument("--no_title", action="store_true", default=False,
                        help="switch for turning off the title")
    parser.add_argument("--projection", type=str, default='cyl', choices=['cyl', 'nsper', 'spstere'],
                        help="Map projection [default: nsper]")
    parser.add_argument("--image_size", type=float, default=9, 
                        help="size of image [default: 9]")

    parser.add_argument("--search_region", type=float, nargs=4, default=None,
                        metavar=('SOUTH_LAT', 'NORTH_LAT', 'WEST_LON', 'EAST_LON'),
                        help="draw an outline of the search region [default: None]")
    parser.add_argument("--extent", type=str, default=None, nargs=3, metavar=('FILE', 'LAT_MIN', 'LAT_MAX'),
                        help='File with the extent information (so extent box can be plotted) for each timestep, search lat1, lat2')
    parser.add_argument("--raphael", action="store_true", default=False, 
                        help="switch for drawing in the regions used in the Raphael2004 ZW3 index [default: False]")
                        
    args = parser.parse_args() 

    main(args)
