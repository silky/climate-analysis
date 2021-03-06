"""
Filename:     plot_timescale_spectrum.py
Author:       Damien Irving, d.irving@student.unimelb.edu.au
Description:  Plot the density spectrum of a single data file for mutliple timescales

"""

# Import general Python modules

import os, sys, pdb
import numpy
import argparse

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# Import my modules

cwd = os.getcwd()
repo_dir = '/'
for directory in cwd.split('/')[1:]:
    repo_dir = os.path.join(repo_dir, directory)
    if directory == 'phd':
        break

modules_dir = os.path.join(repo_dir, 'modules')
sys.path.append(modules_dir)
anal_dir = os.path.join(repo_dir, 'data_processing')
sys.path.append(anal_dir)
try:
    import netcdf_io as nio
    import general_io as gio
    import calc_fourier_transform as cft
except ImportError:
    raise ImportError('Must run this script from anywhere within the phd git repo')


colors = ['blue', 'cyan', 'green', 'yellow', 'orange', 'red', 'magenta', 'purple', 'brown', 'black']    


def main(inargs):
    """Run the program."""
    
    plt.figure() 
    if inargs.runmean:
        runmean_windows = inargs.runmean
    else:
        runmean_windows = [1]
    
    for index, step in enumerate(runmean_windows):
        
        indata = nio.InputData(inargs.infile, inargs.variable, runave=step,
                               **nio.dict_filter(vars(inargs), ['latitude', 'time']))
    
        signal = indata.data
        indep_var = signal.getLongitude()[:]

        sig_fft, sample_freq = cft.fourier_transform(signal, indep_var)
        spectrum, spectrum_freqs = cft.spectrum(sig_fft, sample_freq, 
                                                scaling=inargs.scaling, 
                                                variance=numpy.var(signal))
	
        spectrum_temporal_mean = numpy.mean(spectrum, axis=0)
        spectrum_freqs_1D = numpy.mean(spectrum_freqs, axis=0)
        
        plt.plot(spectrum_freqs_1D, spectrum_temporal_mean, 
                 label=str(step), marker='o', color=colors[index])

    plt.xlim(1, inargs.window)
    plt.xlabel('frequency [cycles / domain]')
    
    if inargs.scaling == 'R2':
        ylabel = 'variance explained'
    else:
        ylabel = inargs.scaling
    plt.ylabel('average %s' %(ylabel))
    plt.legend()
    
    plt.savefig(inargs.outfile, bbox_inches='tight')
    plt.clf()
    metadata = {indata.fname: indata.global_atts['history']}
    gio.write_metadata(inargs.outfile, file_info=metadata)
    

if __name__ == '__main__':

    extra_info =""" 
example (vortex.earthsci.unimelb.edu.au):
  /usr/local/anaconda/bin/python plot_timescale_spectrum.py 
  /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/va_Merra_250hPa_daily_r360x181.nc va 
  /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/rwid/zw3/figures/tscale_anal/amp-spectra-va_Merra_250hPa_daily-2000-2009_r360x181-55S.png 
  --runmean 1 5 10 15 30 60 90 180 365 
  --latitude -55

author:
  Damien Irving, d.irving@student.unimelb.edu.au

"""

    description='Plot the density spectrum of a single data file for mutliple timescales'
    argparser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    argparser.add_argument("infile", type=str, help="Input file name")
    argparser.add_argument("variable", type=str, help="Input file variable")
    argparser.add_argument("outfile", type=str, help="Output file name")
			
    # Input data options
    argparser.add_argument("--latitude", type=float,
                           help="Latitude over which to perform the Fourier Transform [default = entire]")
    argparser.add_argument("--time", type=str, nargs=2, metavar=('START_DATE', 'END_DATE'),
                           help="Time period [default = entire]")

    # Output options
    argparser.add_argument("--window", type=int, default=10,
                           help="upper limit on the frequencies included in the plot [default=10]")
    argparser.add_argument("--runmean", type=int, nargs='*',
                           help="running mean windows to include (e.g. 1 5 30 90 180)")
    argparser.add_argument("--scaling", type=str, choices=('amplitude', 'power', 'R2'), default='amplitude',
                           help="scaling applied to the amplitude of the spectal density [default=None]")
  
    args = argparser.parse_args()            

    print 'Input file: ', args.infile
    print 'Output file: ', args.outfile  

    main(args)
