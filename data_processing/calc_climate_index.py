#!/usr/bin/env cdat

"""
GIT INFO: $Id$
Filename:     calc_climate_index.py
Author:       Damien Irving, d.irving@student.unimelb.edu.au
Description:  Calculates the selected climate index

Input:        List of netCDF files to plot
Output:       Text file

Updates | By | Description
--------+----+------------
23 February 2012 | Damien Irving | Initial version.

"""

import os
import sys
from optparse import OptionParser

import numpy

module_dir = os.path.join(os.environ['HOME'], 'modules')
print module_dir
sys.path.insert(0, module_dir)
import netcdf_io


def calc_monthly_climatology(base_timeseries, months):
    """Calcuate the monthly climatology.
    
    The base_timeseries must have a monthly
    timescale that begins in January.
    
    """

    assert (months[0] == 1), 'the base period must start in January'

    ntime_base = len(base_timeseries)
    monthly_climatology_mean = numpy.ma.zeros(12)
    monthly_climatology_std = numpy.ma.zeros(12)
    for i in range(0, 12):
        monthly_climatology_mean[i] = numpy.ma.mean(base_timeseries[i:ntime_base:12])
	monthly_climatology_std[i] = numpy.ma.std(base_timeseries[i:ntime_base:12])

    return monthly_climatology_mean, monthly_climatology_std


def calc_monthly_anomaly(complete_timeseries, base_timeseries, months):
    """Calculate monthly anomaly.""" 
    
    monthly_climatology_mean = calc_monthly_climatology(base_timeseries, months)[0]
    
    ntime_complete = len(complete_timeseries)
    monthly_anomaly = numpy.ma.zeros(ntime_complete)
    for i in range(0, ntime_complete):
	month_index = months[i]
	monthly_anomaly[i] = numpy.ma.subtract(complete_timeseries[i], 
	                                       monthly_climatology_mean[month_index-1])
    
    return monthly_anomaly 


def monthly_normalisation(complete_timeseries, base_timeseries, months):
    """Normalise the monthly timeseries: (x - mean) / stdev."""  
    
    # Calculate the monthly climatology #
    
    monthly_climatology_mean, monthly_climatology_std = calc_monthly_climatology(base_timeseries, months)

    # Normalise the entire timeseries #
    
    ntime_complete = len(complete_timeseries)
    monthly_normalised = numpy.ma.zeros(ntime_complete)
    for i in range(0, ntime_complete):
	month_index = months[i]
	monthly_normalised[i] = numpy.ma.divide((numpy.ma.subtract(complete_timeseries[i], 
	                        monthly_climatology_mean[month_index-1])), monthly_climatology_std[month_index-1])
    
    return monthly_normalised


#def write_output(index,ifile,outfile_name,base_period,header,years,months,timeseries,error=None):
#    """Write output file."""
#    
#    fout = open(outfile_name,'w')
#    fout.write(header)
#    base = 'Base period = %s  to %s \n' %(base_period[0],base_period[1])
#    fout.write(base)  
#    fout.write(version_info)
#    fout.write('Input file = '+ifile.fname+'\n')
#    
#    if error:
#        fout.write(' YR   MON   %s   error \n' %(index)) 
#	for ii in range(0,len(timeseries)):
#            print >> fout, '%4i %3i %7.2f %7.2f' %(years[ii],months[ii],timeseries[ii],error[ii])
#    else:
#	fout.write(' YR   MON  %s \n' %(index)) 
#	for ii in range(0,len(timeseries)):
#            print >> fout, '%4i %3i %7.2f' %(years[ii],months[ii],timeseries[ii])
#
#    fout.close()
    

def calc_reg_anomaly_timeseries(data_complete, data_base):
    """Calculate the monthly anomaly timeseries for a given region.

    Input arguments must be netcdf_io.InputData instances.

    """

    assert isinstance(data_complete, netcdf_io.InputData), \
    'input arguments must be netcdf_io.InputData instances'

    assert isinstance(data_base, netcdf_io.InputData), \
    'input arguments must be netcdf_io.InputData instances'

    ntime_complete, nlats, nlons = numpy.shape(data_complete.data)
    ntime_base, nlats, nlons = numpy.shape(data_base.data)

    data_complete_flat = numpy.ma.reshape(data_complete.data, (int(ntime_complete), int(nlats * nlons)))    # Flattens the spatial dimension
    data_base_flat = numpy.ma.reshape(data_base.data, (int(ntime_base), int(nlats * nlons)))

    # Calculate the anomalies #

    complete_timeseries = numpy.ma.mean(data_complete_flat, axis=1)
    base_timeseries = numpy.ma.mean(data_base_flat, axis=1)

    anomaly_timeseries = calc_monthly_anomaly(complete_timeseries, 
                         base_timeseries, data_complete.months())

    return anomaly_timeseries


def calc_sam(index, ifile, var_id, base_period):
    """Calculate an index of the Southern Annular Mode.

    Method as per Marshall (2003) and Gong & Wang (1999).    

    """
    
    # Read data, extract the required latitudes, calculate zonal mean anomalies #
             
    indata_complete = netcdf_io.InputData(ifile, var_id) 
    indata_base = netcdf_io.InputData(ifile, var_id, time=base_period)    
    
    latitude = indata_complete.data.getLatitude()
    lats = [-40, -65]

    monthly_normalised_timeseries = {}    
    for lat in lats: 
	index, value = min(enumerate(latitude), key=lambda x: abs(x[1]-float(lat)))  #Pick closest latitude
	print 'File latitude for', lat, '=', value

	complete_timeseries = numpy.ma.mean(indata_complete.data[:, index, :], axis=1)
	base_timeseries = numpy.ma.mean(indata_base.data[:, index, :], axis=1)

        monthly_normalised_timeseries[lat] = monthly_normalisation(complete_timeseries, base_timeseries, indata_complete.months())

    sami_timeseries = numpy.ma.subtract(monthly_normalised_timeseries[-40], monthly_normalised_timeseries[-65])

    # Determine the attributes #   

    hx = 'Ref: Marshall (2003) and Gong & Wang (1999). Base period: %s to %s' %(base_period[0], 
                                                                                base_period[1])
    attributes = {'id': 'sam',
                  'long_name': 'Southern Annular Mode Index',
                  'units': '',
                  'history': hx}

    return sami_timeseries, attributes, indata_complete
    

def calc_iemi(index, ifile, var_id, base_period):
    """Calculate the Improved ENSO Modoki Index of Li et al (2010)."""
    
    # Calculate the index #
    
    regions = ['emia', 'emib', 'emic']
    anomaly_timeseries = {}
    for reg in regions: 
	indata_complete = netcdf_io.InputData(ifile, var_id, region=reg)
        indata_base = netcdf_io.InputData(ifile, var_id, region=reg, time=base_period) 
        anomaly_timeseries[reg] = calc_reg_anomaly_timeseries(indata_complete, indata_base)
    
    iemi_timeseries = numpy.ma.subtract(numpy.ma.subtract(numpy.ma.multiply(anomaly_timeseries['emia'], 3.0),
                      numpy.ma.multiply(anomaly_timeseries['emib'],2.0)), anomaly_timeseries['emic'])

    # Determine the attributes    

    hx = 'Ref: Li et al 2010, Adv Atmos Sci, 27, 1210-20. Base period: %s to %s' %(base_period[0], 
                                                                                   base_period[1])
    attributes = {'id': 'iemi',
                  'long_name': 'Improved ENSO Modoki Index',
                  'units': 'Celsius',
                  'history': hx}

    return iemi_timeseries, attributes, indata_complete
 

def calc_nino(index, ifile, var_id, base_period):
    """Calculate a NINO SST index."""
    
    # Read the input data #
    
    indata_complete = netcdf_io.InputData(ifile, var_id, region='nino'+index[4:])
    indata_base = netcdf_io.InputData(ifile, var_id, region='nino'+index[4:], time=base_period)  
    
    # Calculate the NINO index #
    
    nino_timeseries = calc_reg_anomaly_timeseries(indata_complete, indata_base)
    
    # Determine the attributes #

    hx = 'lat: %s to %s, lon: %s to %s, base: %s to %s' %(indata_complete.minlat,
                                                          indata_complete.maxlat,
                                                          indata_complete.minlon,
                                                          indata_complete.maxlon,
                                                          base_period[0],
                                                          base_period[1])
    attributes = {'id': 'nino'+index[4:],
                  'long_name': 'nino'+index[4:]+' '+'index',
                  'units': 'Celsius',
                  'history': hx}
    
    return nino_timeseries, attributes, indata_complete
    

def calc_nino_new(index, ifile, var_id, base_period):
    """Calculate a new Nino index of Ren & Jin (2011)"""
    
    # Calculate the traditional NINO3 and NINO4 indices #
    
    regions = ['NINO3','NINO4']
    anomaly_timeseries = {}
    for reg in regions: 
        anomaly_timeseries[reg], temp, indata_complete = calc_nino(reg, ifile, var_id, base_period)       

    # Calculate the new Ren & Jin index #

    ntime = len(anomaly_timeseries['NINO3'])
    
    nino_new_timeseries = numpy.ma.zeros(ntime)
    for i in range(0, ntime):
        nino3_val = anomaly_timeseries['NINO3'][i]
	nino4_val = anomaly_timeseries['NINO4'][i]
        product = nino3_val * nino4_val
	
	alpha = 0.4 if product > 0 else 0.0
	
	if index == 'NINOCT':
	    nino_new_timeseries[i] = numpy.ma.subtract(nino3_val, (numpy.ma.multiply(nino4_val, alpha)))
	elif index == 'NINOWP':
	    nino_new_timeseries[i] = numpy.ma.subtract(nino4_val, (numpy.ma.multiply(nino3_val, alpha)))
    
    # Determine the attributes    

    hx = 'Ref: Ren & Jin 2011, GRL, 38, L04704. Base period: %s to %s'  %(base_period[0], 
                                                                          base_period[1])
    long_name = {}
    long_name['NINOCT'] = 'Nino cold tongue index'
    long_name['NINOWP'] = 'Nino warm pool index'    

    attributes = {'id': 'nino'+index[4:],
                  'long_name': long_name[index],
                  'units': 'Celsius',
                  'history': hx}

    return nino_new_timeseries, attributes, indata_complete


def main(index, infile_name, var, outfile_name, base_period):
    """Run the program."""
        
    ## Initialise relevant index function ##
    
    function_for_index = {'NINO': calc_nino,
                          'NINO_new': calc_nino_new,
                          'IEMI': calc_iemi,
                          'SAM': calc_sam}   
    
    if index[0:4] == 'NINO':
        if index == 'NINOCT' or index == 'NINOWP':
	    calc_index = function_for_index['NINO_new']
	else:
	    calc_index = function_for_index['NINO']
    else:
        calc_index = function_for_index[index]

    ## Calculate the index ##  

    index_data, atts, indata = calc_index(index, infile_name, var, base_period)
    
    ## Write the outfile ##
    
    netcdf_io.write_netcdf(outfile_name, index, (indata,), (index_data,), 
                          (atts,), (indata.data.getTime(),))     

        
if __name__ == '__main__':

    ### Help and manual information ###

    usage = "usage: %prog [options] {}"
    parser = OptionParser(usage=usage)

    parser.add_option("-M", "--manual", action="store_true", dest="manual", default=False,
                      help="output a detailed description of the program")
#    parser.add_option("-e", "--error", action="store_true", dest="error", default=False,
#                      help="Input file contains an additional error variable")
    parser.add_option("-b", "--base", dest="base_period", nargs=2, type='string', default=('1981-01-01', '2010-12-31'),
                      help="Start and end date for base period [default=('1981-01-01', '2010-12-31')]")
    
    (options, args) = parser.parse_args()            # Now that the options have been defined, instruct the program to parse the command line

    if options.manual == True or len(args) != 4:
	print """
	Usage:
            cdat calc_climate_index.py [-M] [-h] [-e] {index} {input file} {variable} {output file}

	Options
            -M  ->  Display this on-line manual page and exit
            -h  ->  Display a help/usage message and exit
	    -b  ->  Start and end date for base period [default=('1981-01-01','2010-12-31')]

        Pre-defined indices
            NINO12, NINO3, NINO4, NINO34
	    NINOCT, NINOWP 
	    IEMI, SAM
	
	Example
	    /usr/local/uvcdat/1.2.0rc1/bin/cdat calc_climate_index.py NINO34 
            /work/dbirving/datasets/Merra/data/processed/ts_Merra_surface_monthly_native-ocean.nc 
	    /work/dbirving/processed/indices/data/ts_Merra_surface_NINO34_monthly_native-ocean.nc
	    
	Author
            Damien Irving, 26 Jun 2012.

        Planned enhancements
            Confidence intervals will be calculated for any SST indices calculated 
            using the ERSSTv3b data (as this contains an additional error variance
            variable, which is the standard error squared). To calculate the error 
            for a region (like a Nino region) you need to average the error variance
            and divide by the effective number of degrees of freedom for the area.
            Then take the square root of that for the standard error for the region.
            A simple way to estimate the effective number of degrees of freedom is 
            to use the S method described by Wang & Shen (1999). J Clim, 12, 1280-91.
            Once you get the standard error for the area average, you can use it to
            define confidence intervals. For example, 1.96 times stardard error for 
            the 95% confidence.   	

        Bugs
            Please report any problems to: d.irving@student.unimelb.edu.au
	"""
	sys.exit(0)
    
    else:
                
        print 'Index:', args[0]
        print 'Input file:', args[1]
        print 'Output file:', args[3]

        main(args[0], args[1], args[2], args[3], options.base_period)
