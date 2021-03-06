The wave envelope extraction is a multi-step process:

0. Experiment with the location of the north pole and subsequent search paths:
/usr/local/uvcdat/1.2.0/bin/cdat plot_EOF.py 
/mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/eof-sf_Merra_250hPa_monthly-anom-wrt-1979-2011-MAM_native-sh.nc 
world-psa 
--ticks -1 -0.8 -0.6 -0.4 -0.2 0.0 0.2 0.4 0.6 0.8 1.0 
--search_paths 20 260 225 335 -15 15 5


1. Calculate the new meridional wind anomaly and output it on a rotated grid:

a. For monthly data

/usr/local/uvcdat/1.2.0rc1/bin/cdat calc_vwind_rotation.py 
/work/dbirving/datasets/Merra/data/ua_Merra_250hPa_monthly_native.nc ua
/work/dbirving/datasets/Merra/data/va_Merra_250hPa_monthly_native.nc va 
/work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_monthly-anom-wrt-all_y181x360_np30-270.nc
--north_pole 30 270
--anomaly all all
--grid -90.0 181 1.0 0.0 360 1.0

b. For daily data (because cdat doesn't have daily climatology functions)

/usr/local/uvcdat/1.2.0rc1/bin/cdat calc_vwind_rotation.py 
/work/dbirving/datasets/Merra/data/ua_Merra_250hPa_daily_native.nc ua
/work/dbirving/datasets/Merra/data/va_Merra_250hPa_daily_native.nc va 
/work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_daily_y181x360_np30-270.nc
--north_pole 30 270
--grid -90.0 181 1.0 0.0 360 1.0

cdo ydaysub /work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_daily_y181x360_np30-270.nc
-ydayavg /work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_daily_y181x360_np30-270.nc
/work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_daily-anom-wrt-all_y181x360_np30-270.nc


2. Extract the wave envelope (output is still on the grid you gave it - i.e. the rotated grid)

/usr/local/uvcdat/1.2.0rc1/bin/cdat calc_envelope.py 
/work/dbirving/datasets/Merra/data/processed/vrot_Merra_250hPa_monthly-anom-wrt-all_y181x360_np30-270.nc vrot
/work/dbirving/datasets/Merra/data/processed/vrot-env-w567_Merra_250hPa_monthly-anom-wrt-all_y181x360_np30-270.nc
--longitude 195 340


3. Plot the wave envelope together with other relevant variables

/usr/local/uvcdat/1.2.0rc1/bin/cdat plot_envelope.py
/work/dbirving/test_data/vrot-env_Merra_250hPa_monthly-anom-wrt-all_y181x360-np30-270.nc
env 30 270 0 0 monthly
--sf /work/dbirving/datasets/Merra/data/processed/sf_Merra_250hPa_monthly-anom-wrt-1979-2011_native.nc sf
--ofile /work/dbirving/test_data/env-wind-sf_Merra_250hPa_monthly-anom-wrt-all_y181x360-native-np30-270
--time 1979-01-01 1982-12-31 none 
--search_paths 20 260 225 335 -20 20 5


4. Create the Hovmoller diagram

/usr/local/uvcdat/1.2.0rc1/bin/cdat calc_hovmoller.py
/work/dbirving/datasets/Merra/data/processed/vrot-env-w567_Merra_250hPa_daily-anom-wrt-all_y181x360_np30-270.nc 
env absolute 14
/work/dbirving/datasets/Merra/data/processed/hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-all_y181x360_np30-270_absolute14_lon180-340.nc
--latitude -15 15 --longitude 180 340


5. Implement the ROIM method

matlab &
#then run test_roim.m, which will output file.csv


6a. Generate the desired list of PSA-active dates (and output some very basic climatological statistics if you like)

(this requires pandas)

python roim_stat.py 
hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335.txt 
--duration_histogram hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_duration-histogram.png 
--date_list startpoint_temporal endpoint_temporal hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates.txt


6b. Further filter the list of dates

/usr/local/uvcdat/1.2.0/bin/cdat filter_dates.py /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates.txt 
--filter marie_byrd_land /mnt/meteo0/data/simmonds/dbirving/Merra/data/va_Merra_250hPa_daily_native.nc va -5.0 below 
--outfile /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates-filter-marie-byrd-land-va-below-neg5.txt


6c. Parse that list of dates and calculate some date-based statistics (monthly totals etc)

/usr/local/uvcdat/1.2.0/bin/cdat parse_dates.py 
hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va.txt 
--bar_file hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_monthly-totals.png 
--line_file hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_seasonal-values.png
--totals_file hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_monthly-totals.nc


7a. Calculate a composite based on a list of dates

(can use calc_composite.sh)

/usr/local/uvcdat/1.3.0/bin/cdat calc_composite.py 
/mnt/meteo0/data/simmonds/dbirving/Merra/data/tas_Merra_surface_daily-anom-wrt-1979-2012_native.nc tas 
/mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va.txt 
/mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-annual.nc --time 1979-01-01 2012-12-31 none

...then plot that composite

/usr/local/uvcdat/1.2.0/bin/cdat plot_composite.py tas /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/tas-hov-vrot-env-w567_Merra_surface-250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-DJF.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/tas-hov-vrot-env-w567_Merra_surface-250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-MAM.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/tas-hov-vrot-env-w567_Merra_surface-250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-JJA.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/tas-hov-vrot-env-w567_Merra_surface-250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-SON.nc  
--headings DJF MAM JJA SON 
--ticks -3.0 -2.5 -2.0 -1.5 -1.0 -0.5 0.0 0.5 1.0 1.5 2.0 2.5 3.0 
--units temperature_anomaly 
--ofile test_composite_seasons.png 
--contour_var sf 
--contour_files /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/sf-hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-DJF.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/sf-hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-MAM.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/sf-hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-JJA.nc /mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/stats/sf-hov-vrot-env-w567_Merra_250hPa_daily-anom-wrt-1979-2012_y181x360_np20-260_absolute14_lon225-335_dates_filter-west-antartica-northerly-va_composite-SON.nc 
--contour_ticks -30 -25 -20 -15 -10 -5 0 5 10 15 20 25 30 
--dimensions 2 2


7b. Compare some date-based statistics to another metric 

plot_timeseries.py??




##. Unit testing

/home/dbirving/testing/unittest_coordinate_rotation.py
/home/dbirving/testing/unittest_vwind_rotation.py

##. Visualising the process

/home/dbirving/testing/plot_vwind_rotation.py
/home/dbirving/testing/plot_coordinate_rotation.py    
