# Import general Python modules #

import os, sys, re, pdb
from collections import OrderedDict

import operator
import numpy
import pandas

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from itertools import groupby
from operator import itemgetter

from datetime import datetime
from dateutil.rrule import *
from dateutil.relativedelta import relativedelta
from matplotlib.dates import date2num
import calendar

import argparse


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
    import netcdf_io as nio
    import convenient_anaconda as aconv
    import convenient_universal as uconv
except ImportError:
    raise ImportError('Must run this script from anywhere within the phd git repo')


# Define functions #

def add_duration(DataFrame, metric, metric_threshold):
    """Add a duration column to the input DataFrame, where an event is defined by
    the number of consecutive timesteps greater than the metric_threshold.
    
    Note that every timestep is assigned a duration value equal to the number of
    days in the entire event.
    
    """

    events = DataFrame[metric].map(lambda x: x > metric_threshold)
    event_list = events.tolist()
    grouped_events = [(k, sum(1 for i in g)) for k,g in groupby(event_list)]

    duration = []
    for event in grouped_events:
        if event[0]:
            data = [event[1]] * event[1]
        else:
            data = [0] * event[1]
        duration.append(data)

    DataFrame['duration'] = reduce(operator.add, duration)
    DataFrame['event'] = events

    return DataFrame  
    

def basic_stats(DataFrame, stats, before_filtering=True):
    """Return basic statistics (for printing to the screen)"""
    
    if before_filtering:
        stats.append('# Before filtering')     
    else:
        stats.append(' ') 
        stats.append('# After filtering')
         
    stats.append('total number of days: ' + str(len(DataFrame['duration'])))
    stats = duration_stats(DataFrame['duration'].tolist(), stats)

    return stats


def bin_dates(date_list, start_year, start_month, end_year, end_month):
    """Take a list of dates and return totals in bins, according to 
    the requested timescale.
    
    """
    
    dt_list = map(lambda x: datetime.strptime(x, '%Y-%m-%d'), date_list)
    num_list = map(date2num, dt_list)
    
    start_dt = datetime(start_year, start_month, 1)
    end_dt = datetime(end_year, end_month, 1) + relativedelta(months=1)
    dt_bin_edges = list(rrule(MONTHLY, dtstart=start_dt, until=end_dt)) #interval=1
    num_bin_edges = date2num(dt_bin_edges)
    
    hist_data, edges = numpy.histogram(num_list, bins=num_bin_edges)
    assert len(hist_data) == len(dt_bin_edges[:-1])

    histogram = {}
    for i in range(0, len(hist_data)):
        histogram[dt_bin_edges[i]] = hist_data[i]
    
    bins_dict = OrderedDict(sorted(histogram.items(), key=lambda t: t[0])) 
    #t[1] would sort by value instead of key  

    # Calculate monthly totals and values
    monthly_totals = dict((month, 0) for month in range(1,13))
    monthly_values = dict((month, []) for month in range(1,13))
    for key, value in histogram.iteritems():
        monthly_totals[key.month] = monthly_totals[key.month] + value
        monthly_values[key.month].append(value)

    return monthly_totals, monthly_values


def calc_seasonal_values(monthly_values, month_years):
    """Calculate the seasonal values from the monthly values"""
    
    months = {'DJF': [12, 1, 2], 'MAM': [3, 4, 5],
              'JJA': [6, 7, 8], 'SON': [9, 10, 11],
              'annual': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]}
    
    seasonal_values = {}
    for season in months.keys():
        seasonal_values[season] = []
    
    year_lists = {}
    for season, months in months.iteritems():    
        years = get_intersection(month_years, months)
        for year in years:
            season_total = 0
            for month in months:
                index = month_years[month].index(year)
                month_total = monthly_values[month][index]
                season_total = season_total + month_total
            seasonal_values[season].append(season_total)
        year_lists[season] = years

    return seasonal_values, year_lists


def create_histogram(data, bin_width=1, min_val=None, max_val=None, 
                     cumulative=False, percentage=False, duration=False):
    """Create the histogram"""
    
    low_bound = numpy.min(data) if not min_val else min_val
    high_bound = numpy.max(data) if not max_val else max_val
    
    edges = numpy.arange((low_bound - (bin_width / 2.0)), (high_bound + bin_width), bin_width) 
    bin_centres = numpy.arange(low_bound, high_bound + bin_width, bin_width)
    bin_counts, bin_edges = numpy.histogram(data, edges)
    
    if duration:
        if bin_centres[0] == 0.0:
            bin_counts[1:] = bin_counts[1:] / bin_centres[1:] 
        else:    
            bin_counts = bin_counts / bin_centres

    if cumulative:
        bin_counts = numpy.cumsum(bin_counts)

    if percentage:
        bin_counts = (bin_counts.astype(float) / len(data)) * 100
    
    return bin_counts, bin_centres, bin_edges 


def crop_dates(start_date, end_date):
    """Adjust a start and end date so the data only includes complete months"""
    
    # Crop to complete month
    if start_date.day != 1:
        start_date = start_date + relativedelta(months=1)
    
    if end_date.day != calendar.monthrange(end_date.year, end_date.month)[1]:
        end_date = end_date - relativedelta(months=1)
    
    # Get the year corresponding to each month
    month_years = {}
    for month in range(1,13):
        month_years[month] = []
    date_list = list(rrule(MONTHLY, dtstart=start_date, until=end_date))
    for date in date_list:
        month_years[date.month].append(date.year)

    
    return start_date, end_date, month_years


def duration_stats(duration_list, stats_list):
    """Append some duration data to a list of statistics"""

    bin_counts, bin_centres, bin_edges = create_histogram(duration_list, duration=True)
    nevents = sum(bin_counts[1:]) if bin_centres[0] == 0.0 else sum(bin_counts)
    stats_list.append('number of events: ' + str(nevents)) 
    stats_list.append('maximum duration: ' + str(numpy.max(duration_list))) 
    stats_list.append('mean duration: ' + "%.2f" % round(numpy.mean(duration_list), 2))
    stats_list.append('median duration: ' + "%.2f" % round(numpy.median(duration_list), 2))

    return stats_list


def get_date_bounds(indata, dt_selection):
    """For a given list of dates, return the year/month bounds for 
    months of complete data (i.e. incomplete start or end 
    months are not included)
    
    """
        
    temp_data = indata[dt_selection]
    date_list = temp_data.index.tolist()
    
    start_date = datetime.strptime(date_list[0], '%Y-%m-%d')
    end_date = datetime.strptime(date_list[-1], '%Y-%m-%d')
    
    start_date, end_date, month_years = crop_dates(start_date, end_date)

    return start_date.year, start_date.month, end_date.year, end_date.month, month_years


def get_intersection(dictionary, key_list):
    """Return the common values from a dictionary of lists"""
  
    base_key = key_list[0]
    result = set(dictionary[base_key])
    for key in key_list[1:]:
        result.intersection_update(dictionary[key])

    return list(result)


def get_years(date_list):
    """Return a list of integer years"""
    
    start_year = int(date_list[0][0:4])
    end_year = int(date_list[-1][0:4])
    
    return numpy.arange(start_year, end_year + 1, 1)


def plot_duration_histogram(data):
    """Plot a duration histogram"""

    bin_counts, bin_centres, bin_edges = create_histogram(data, duration=True)
  
    width = (bin_edges[1]-bin_edges[0]) * .9
    plt.bar(bin_edges[:-1], bin_counts, width=width)
    
    plt.xlim(bin_edges[0], bin_edges[-1])    
    plt.xlabel('Duration (days)')
    plt.ylabel('Frequency')


def plot_monthly_totals(ax, data, start_year, start_month, end_year, end_month, month_years):
    """Plot a bar chart showing the totals for each month"""

    date_list = data.index.tolist()
    monthly_totals, monthly_values = bin_dates(date_list, start_year, start_month, end_year, end_month)
    monthly_pct = numpy.zeros(12)
    for i in range(0, 12):
        ndays = calendar.mdays[i+1] * len(month_years[i+1])
        if i == 1:
            start = start_year if start_month <= 2 else start_year + 1
            end = end_year if end_month >= 2 else end_year - 1
            nleap = calendar.leapdays(start, end)
            ndays = ndays + nleap
        monthly_pct[i] = (monthly_totals[i+1] / float(ndays)) * 100     

    ind = numpy.arange(12)    # the x locations for the bars
    width = 0.8               # the width of the bars
    p1 = plt.bar(ind, monthly_pct, width)

    plt.ylabel('Percentage of days')
    plt.xticks(ind+width/2., calendar.month_abbr[1:])


def plot_seasonal_values(ax, data, 
                         start_year, start_month, end_year, end_month, month_years,
                         leg_loc=7, scale_annual=1.0):
    """Plot a line graph showing the seasonal values for each year"""
    
    for month, years in month_years.iteritems():
        assert len(years) > 1, \
        """Must have more than one year of data for each season or plot_seasonal_values() won't work""" 

    date_list = data.index.tolist()
    monthly_totals, monthly_values = bin_dates(date_list, start_year, start_month, end_year, end_month)
    seasonal_values, years = calc_seasonal_values(monthly_values, month_years)

    colors = {'DJF': 'red', 'MAM': 'orange',
             'JJA': 'blue', 'SON': 'green',
             'annual': 'black'}

    if scale_annual == 0.0:
        season_list = ['DJF', 'MAM', 'JJA', 'SON']
    else:
        season_list = ['DJF', 'MAM', 'JJA', 'SON', 'annual']
        seasonal_values['annual'] = numpy.array(seasonal_values['annual']) * scale_annual

    for season in season_list:
        ax.plot(years[season], seasonal_values[season], color=colors[season], lw=2.0, label=season)       

    ax.set_xlim(start_year, end_year)
    ax.set_xlabel('year')
    ax.set_ylabel('total days')
    ax.legend(loc=leg_loc, fontsize='small', ncol=5)


def main(inargs):
    """Run the program"""
   
    # Read data 
    indata, metadata = aconv.nc_to_df(inargs.infile, ['ampmean', 'ampmedian', 'extent', 'startlon', 'endlon'])
    metric_threshold = uconv.get_threshold(indata[inargs.metric], inargs.metric_threshold) 
    
    # Add relevant columns
    indata = add_duration(indata, inargs.metric, metric_threshold)
    stats = basic_stats(indata, [], before_filtering=True)    

    # Apply filters
    dt_selector = aconv.pandas_dt_selector(indata.index, inargs.season, inargs.start, inargs.end)
    selector = dt_selector
    
    assert inargs.threshold_direction in ['greater', 'less']
    if inargs.threshold_direction == 'greater':
        metric_selection = indata[inargs.metric] >= metric_threshold
    elif inargs.threshold_direction == 'less':
        metric_selection = indata[inargs.metric] <= metric_threshold

    selector = selector & metric_selection 
    
    if inargs.duration_filter:
        min_duration_selection = indata['duration'] >= inargs.duration_filter[0]
        max_duration_selection = indata['duration'] <= inargs.duration_filter[1]
        selector = selector & min_duration_selection & max_duration_selection
 
    data = indata[selector]

    # Print basic stats to screen
    stats = basic_stats(data, stats, before_filtering=False)

    for line in stats:
        print line

    # Metadata
    metadata_dict = {inargs.infile: metadata}

    # Create optional outputs
    if inargs.date_list:   
        gio.write_dates(inargs.date_list, data.index.tolist())
        gio.write_metadata(inargs.date_list, file_info=metadata_dict)

    if inargs.plot_name:

        fig = plt.figure(figsize=inargs.figure_size)
        if not inargs.figure_size:
            print 'figure width: %s' %(str(fig.get_figwidth()))
            print 'figure height: %s' %(str(fig.get_figheight()))

        if inargs.dimensions:
            nrows, ncols = inargs.dimensions
        else:
            nrows = 1
            ncols = len(inargs.plot_types)

        for index, plot_type in enumerate(inargs.plot_types):
            plotnum = index + 1
            ax = plt.subplot(nrows, ncols, plotnum)
            plt.sca(ax)

            assert plot_type in ('duration_histogram', 'monthly_totals_histogram', 'seasonal_values_line')
            if plot_type == 'duration_histogram':
                plot_duration_histogram(ax, data['duration'])
            elif plot_type == 'monthly_totals_histogram':
                start_year, start_month, end_year, end_month, month_years = get_date_bounds(indata, dt_selector)
                plot_monthly_totals(ax, data, 
                                    start_year, start_month, end_year, end_month, month_years)
            elif plot_type == 'seasonal_values_line':
                start_year, start_month, end_year, end_month, month_years = get_date_bounds(indata, dt_selector)
                plot_seasonal_values(ax, data, 
                                     start_year, start_month, end_year, end_month, month_years,
                                     leg_loc=inargs.leg_loc, scale_annual=inargs.scale_annual)

        fig.savefig(inargs.plot_name, bbox_inches='tight')
        gio.write_metadata(inargs.plot_name, file_info=metadata_dict)


if __name__ == '__main__':

    extra_info =""" 
example:
  env_amp_mean
note:
    This script assumes daily input data.
    At the moment season selection will mess with the duration statistics
    (i.e. cut events short)
    
author:
    Damien Irving, d.irving@student.unimelb.edu.au

"""

    description='Calculate various statistics from calc_wave_stat.py output'
    parser = argparse.ArgumentParser(description=description,
                                     epilog=extra_info, 
                                     argument_default=argparse.SUPPRESS,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)

    # Required arguments
    parser.add_argument("infile", type=str, help="Input file name - it is the .nc output of calc_wave_stats.py")
    parser.add_argument("metric", type=str, help="Name of the input file metric to be used")
    
    # Time filters
    parser.add_argument("--start", type=str, help="Time start filter (e.g. 1979-02-31)", default=None)
    parser.add_argument("--end", type=str, help="Time end filter (e.g. 2012-12-31)", default=None)
    parser.add_argument("--season", type=str, choices=('DJF', 'MAM', 'JJA', 'SON'), default=None,
                        help="Season selector [default = all]")
    
    # Other filters
    parser.add_argument("--metric_threshold", type=str, default='90pct', 
                        help="Threshold metric value. Can be percentile (e.g. 90pct) or raw value.")
    parser.add_argument("--threshold_direction", type=str, choices=('greater', 'less'), default='greater', 
                        help="Keep values greater or less than the threshold.")
    parser.add_argument("--duration_filter", type=float, nargs=2, default=None, metavar=('MIN', 'MAX'),
                        help="Duration filter - only events of length equal to or within these bounds are included")
                        
    # Optional outputs
    parser.add_argument("--plot_name", type=str, default=None, 
                        help="Name of output plot")
    parser.add_argument("--plot_types", type=str, nargs='*', default=('seasonal_values_line', 'monthly_totals_histogram'), 
                        choices=('duration_histogram', 'monthly_totals_histogram', 'seasonal_values_line'), 
                        help="Types of plots to include")
    parser.add_argument("--date_list", type=str, default=None, 
                        help="Name of output file for list of filtered dates")      

    # Plot options
    parser.add_argument("--leg_loc", type=int, default=0,
                        help="Location of legend for line graph [default = 0 = top right] (7 = centre right)")
    parser.add_argument("--scale_annual", type=float, default=1,
                        help="scale factor (multply by) for the annual season in the seasonal values plot (can be zero for no plot) [default = 1]")
    parser.add_argument("--dimensions", type=int, nargs=2, metavar=("NROWS", "NCOLS"), default=None,
                        help="dimensions of the plot")
    parser.add_argument("--figure_size", type=float, default=None, nargs=2, metavar=('WIDTH', 'HEIGHT'),
                        help="size of the figure (in inches)")


    args = parser.parse_args()            
    main(args)
