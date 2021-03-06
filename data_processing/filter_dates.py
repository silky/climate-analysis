"""
Filename:     filter_dates.py
Author:       Damien Irving, d.irving@student.unimelb.edu.au
Description:  Take a list of dates and filter according to a supplied dataset

"""

import sys
import os

import argparse
import itertools
import numpy

import cdutil

module_dir = os.path.join(os.environ['HOME'], 'phd', 'modules')
sys.path.insert(0, module_dir)
import netcdf_io as nio
import general_io as gio


def filter_spatial_ave(filter_name, date_list, data_file, var, threshold, select):
    """Filter the data according to a spatial averaged value.
    
    filter_name options:
      antarctic-peninsula  --  Filter according to the sign of the meridional wind anomaly
                               over the region 90W to 50W and 65S to 75S (based on Ding2013)
      marie-byrd-land      --  Filter according to the sign of the meridional wind anomaly
                               over the region 100W to 160W and 70S to 75S (based in Ding2011)
      tropical-pacific     --  Filter according to the sign of the SST anomaly
                               over the region 180 to 240E and 5S to 5N. This is an 
			       approximate area based on the findings of Ding2013

    """  
    
    print float(threshold)
    
    # Read meridional wind data and extract region of interest
    bounds = {'antarctic-peninsula': [(-75, -65, 'cc'), (270, 310, 'cc')],
              'marie-byrd-land': [(-75, -70, 'cc'), (200, 260, 'cc')],
              'tropical-pacific': [(-5, 5, 'cc'), (180, 240, 'cc')],}
    lats, lons = bounds[filter_name]
    indata = nio.InputData(data_file, var, latitude=lats, longitude=lons)
    
    # Select data corresponding to input date list
    matching_date_list = nio.match_dates(date_list, indata.data.getTime().asComponentTime())
    input_selection = nio.temporal_extract(indata.data, matching_date_list, indexes=False) 
    
    # Calculate the spatial average of the data
    ave_axes = indata.data.getOrder().translate(None, 't')  #all but the time axis
    spatial_ave = cdutil.averager(input_selection, axis=ave_axes, weights=['unweighted']*len(ave_axes))

    # Select data where mean meridional wind is less or more than threshold
    assert select in ['above', 'below']
    test = spatial_ave < float(threshold) if select == 'below' else spatial_ave > float(threshold)
    
    new_date_list = list(itertools.compress(matching_date_list, test))
    
    return map(lambda x: str(x).split()[0], new_date_list)


def main(inargs):
    """Run program."""
	       
    date_list = gio.read_dates(inargs.dates)
    for ifilter in inargs.filter:
	filter_name, infile, var, threshold, selection = ifilter
        date_list = filter_spatial_ave(filter_name, date_list, 
                                       infile, var, 
                                       threshold, selection)
    
    # Write output file
    gio.write_dates(inargs.outfile, date_list)


if __name__ == '__main__':

    extra_info =""" 
example:
  /usr/local/uvcdat/1.3.0/bin/cdat filter_dates.py 
  hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates.txt 
  --filter antarctic-peninsula /mnt/meteo0/data/simmonds/dbirving/Merra/data/va_Merra_250hPa_daily_native.nc va 0 below
  --filter tropical_pacific /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/tas_Merra_surface_daily-anom-wrt-1979-2012_native.nc tas 0.5 above
  --outfile hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates-filter-antarctic-peninsula-va-below-0.txt

note:
  Mutliple filters can be applied, each with five arguments supplied:
    - name: antarctic_peninsula, marie_byrd_land, tropical_pacific
    - infile: file containing data to be used for the filtering method 
    - var: variable to extract from the infile
    - threshold: threshold value against which the selection is made
    - selection: segment of the selection to retain (i.e. 'above' or 'below' threshold)
        

author:
  Damien Irving, d.irving@student.unimelb.edu.au

"""

    description='Take a list of dates and filter according to a supplied dataset'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("dates", type=str, 
                        help="File containing dates of interest (one date per line)")
    parser.add_argument("--filter", type=str, nargs=5, action='append', metavar=('NAME', 'INFILE', 'VAR', 'THRESHOLD', 'SELECTION'), 
                        help="Filter details (name, infile, var, threshold, selection)") 
    parser.add_argument("--outfile", type=str, default='test.txt',
                        help="Name of output file")   
                        
    args = parser.parse_args()            
    main(args)

