#
# Description: Automates the process of plotting the wave envelope for multiple days.
# Note: This script is for non rotated data (i.e va, not vrot). For the rotated data,
# use plot_envelope.py 
#

function usage {
    echo "USAGE: bash $0 envfile sffile start end timescale"
    echo "   infile:     Envelope file name"
    echo "   sffile:     Streamfunction file"
    echo "   outfile:    Output file name"
    echo "   start:      Start date"
    echo "   tsteps:     Number of timesteps to plot"
    echo "   timescale:  Daily"
    echo "   e.g. bash $0 va_Merra_250hPa_daily-anom-wrt-all_y181x360.nc va env-w234-va_Merra_250hPa_daily-anom-wrt-all_y181x360.nc --wavenumbers 2 4"
    exit 1
}


envfile=/mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/va-env-w234_Merra_250hPa_monthly_r360x181.nc
sffile=/mnt/meteo0/data/simmonds/dbirving/Merra/data/processed/sf_Merra_250hPa_monthly_native.nc
start1=2000-04-01
end1=2000-04-29
start2=1996-04-01
end2=1996-04-29


for year in 2000 ; do
    for month in 01 02 03 04 05 06 07 08 09 10 11 12 ; do
        for day in 
 
        start=${year}-${month}-01
	end=${year}-${month}-26
     
        test=`printf "%02d" $x`
     
        /usr/local/uvcdat/1.3.0/bin/cdat plot_map.py ${envfile} env ${start} ${end} none --projection spstere --draw_axis --contour --delat 15 --contour_file ${sffile} sf ${start} ${end} none --colourbar_colour Oranges --ticks 0 1.5 3 4.5 6 7.5 9 10.5 12 --contour_ticks -140 -120 -100 -80 -60 -40 -20 0 20 40 60 80 100 120 140  --image_size 9 --ofile test-${year}-${month}.png --units ms-1 --region world-dateline-duplicate360 

    done
done


#/usr/local/uvcdat/1.3.0/bin/cdat plot_map.py ${envfile} env ${start1} ${end1} none --projection spstere --draw_axis --contour --delat 15 --contour_file ${sffile} sf ${start1} ${end1} none --colourbar_colour Oranges --ticks 0 1.5 3 4.5 6 7.5 9 10.5 --contour_ticks -140 -120 -100 -80 -60 -40 -20 0 20 40 60 80 100 120 140  --image_size 9 --ofile test-two.png --inline_row_headings April_2000 April_1996 --infiles ${envfile} env ${start2} ${end2} none --contour_file ${sffile} sf ${start2} ${end2} none --dimensions 2 1 --units ms-1 --region world-dateline-duplicate360


start=1996-04-01
end=1996-04-29

/usr/local/uvcdat/1.3.0/bin/cdat plot_map.py ${envfile} env ${start} ${end} none --projection spstere --draw_axis --contour --delat 15 --contour_file ${sffile} sf ${start} ${end} none --colourbar_colour Oranges --ticks 0 1.5 3 4.5 6 7.5 9 10.5 --contour_ticks -140 -120 -100 -80 -60 -40 -20 0 20 40 60 80 100 120 140  --image_size 9 --ofile test_env_Apr1996.png --col_headings April_1996 --units ms-1 --region world-dateline-duplicate360 --image_size 10
