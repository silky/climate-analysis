#
# Description: For global daily data, calc_envelope.py can only handle 5 years of data at a time
# (on abyss and/or vortex.earthsci.unimelb.edu.au) 
#

function usage {
    echo "USAGE: bash $0 infile invar outfile cdofix waveopt wavestart waveend typeopt type lonopt lonstart lonend"
    echo "   infile:     Input file name"
    echo "   invar:      Input variable name"
    echo "   outfile:    Output file name"
    echo "   cdofix:     Script for replacing attributes that cdo strips"
    echo "   waveopt:    Type --filter so compatable with makefile"
    echo "   wavestart:  Beginning of wavenumber range"
    echo "   waveend:    End of wavenumber range"
    echo "   typeopt:    Type --outtype so compatable with makefile"
    echo "   type:       Type of analysis [coefficients or hilbert]"
    echo "   lonopt:     Type --longitude so compatable with makefile"
    echo "   lonstart:   Start longitude search"
    echo "   lonend:     End longitude for new grid"
    echo "   (the longitude selection is optional)"
    echo "   e.g. bash $0 vrot_Merra_250hPa_daily-anom-wrt-all_y181x360-np20N260E.nc vrot env-w567-vrot_Merra_250hPa_daily-anom-wrt-all_y181x360-np20N260E.nc --filter 5 7 --outtype hilbert --longitude 225 335 "
    echo "   e.g. bash $0 va_Merra_250hPa_daily-anom-wrt-all_y181x360.nc va env-w234-va_Merra_250hPa_daily-anom-wrt-all_y181x360.nc --filter 2 4 --outtype hilbert"
    exit 1
}

narg_min=9
narg_max=12

if [[ $# -ne $narg_min && $# -ne $narg_max ]] ; then
  usage
fi

infile=$1
invar=$2
outfile=$3
cdofix=$4
waveselect=($5 $6 $7)
typeselect=($8 $9)
temp_dir=/mnt/meteo0/data/simmonds/dbirving/temp

if [ $# == $narg_max ] ; then
  lonselect=($10 ${11} ${12}) 
else
  lonselect=""
fi  
  

if [ ! -f $infile ] ; then
    echo "Input file doesn't exist: " $infile
    usage
fi


years=(1979 1984 1989 1994 1999 2004 2009 2014)
temp_files=()
for year in "${years[@]}"; do
    end=`expr $year + 4`
    temp_file=${temp_dir}/temp-${8}_${year}-${end}.nc
    /usr/local/anaconda/bin/python ~/phd/data_processing/calc_fourier_transform.py $infile $invar ${temp_file} ${waveselect[@]} ${typeselect[@]} ${lonselect[@]} --time ${year}-01-01 ${end}-12-31 none 
    temp_files+=(${temp_file})
done

cdo -O mergetime ${temp_files[@]} $outfile
rm ${temp_files[@]}
bash ${cdofix} ${outfile} env${invar}      # Put back the required attributes that CDO strips
