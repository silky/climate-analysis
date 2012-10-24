#!/bin/bash
#
# Author: David Kent (David.Kent@csiro.au)
# Date:   3/05/2011
#
# Calculates climatological mean for the annual and each month
# USAGE: seasmean_vars.sh ifile ofile 
#    ifile:     input netcdf file 
#    ofile:     output netcdf file
#
# Copyright 2011, CSIRO
#

version='$Revision: 479 $'

function usage {
    echo "USAGE: seas_vars.sh -a|(vname newvname) ifile ofile "
    echo "    -a:        Process all variables in the file "
    echo "    -m:        Multiply values by days in month "
    echo "    vname:     Original input variable name "
    echo "    newvname:  The base varaible name to use in the output file"
    echo "    ifile:     input netcdf file"
    echo "    ofile:     output netcdf file"
    exit 1
}


all=0
daysinmonth=0
while getopts ":am" opt; do
  case $opt in
    a)
      all=1
      ;;
    m)
      daysinmonth=1
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done
shift $((OPTIND-1))

if [ ${all} -eq 1 ] ; then

  in=$1
  out=$(readlink -f $2)
  vars=`cdo showname $in`

elif [ 4 -eq $# ] ; then

  vars=$1
  varorigout=$2
  in=$3
  out=$(readlink -f $4)

else
  usage
fi

which cdo > /dev/null 2>&1 
if [ $? -ne 0 ] ; then
    echo "Can't find cdo executable"
    exit 1
fi
which ncatted > /dev/null 2>&1
if [ $? -ne 0 ] ; then
    echo "Can't find ncatted executable"
    exit 1
fi

if [ ! -f $in ] ; then
    echo "Input file doesn't exist: " $in
    exit 1
fi

if [ -f $out ] ; then
   echo "Outfile exists. Skipping: " $out
   exit 1
fi

TMPDIR=/work/dbirving/temp_data   ## Override default $TMPDIR

inbase=`basename $in`
extn=`expr match "${inbase}" '.*\.\(.*\)'`
if [ $extn = 'xml' ] ; then
  tmp_in=$TMPDIR/xml_concat.$$.nc
  python $CCT/processing/cdml_cat/xml_to_nc.py None $in $tmp_in   ### xml_to_nc.py is in my git_repo
  in=$tmp_in
fi

if [ ! -f $in ] ; then
    echo "Conversion of file from XML catalogue failed."
    exit 1
fi

# Check that we start in Jan and end in Dec
monstart=`cdo showmon $in | awk '{print $1 }'`
monend=`cdo showmon $in | awk '{print $NF }'`
if [ $monstart -ne 1 -o $monend -ne 12 ] ; then
  if [ $monstart -ne 1 ] ; then
    yrstart=`cdo showyear $in | awk '{ print $2 }'`
  else
    yrstart=`cdo showyear $in | awk '{ print $1 }'`
  fi
  if [ $monend -ne 12 ] ; then
    yrend=`cdo showyear $in | awk '{ print $(NF-1) }'`
  else
    yrend=`cdo showyear $in | awk '{ print $NF }'`
  fi
  tmp_in2=$TMPDIR/strip_months.$$.nc
  echo "There are extra months at the start or end. Stripping..."
  cdo seldate,${yrstart}-1-1,${yrend}-12-31 $in $tmp_in2
  in=$tmp_in2
fi

if [ ! -f $in ] ; then
    echo "Stripping extra months failed."
    exit 1
fi

tmp=$TMPDIR/seasmean.$$

if [ ${daysinmonth} -eq 1 ] ; then
  tmp1_in=$tmp_in
  tmp_in=$TMPDIR/daysin_mon.$$.nc 
  cdo muldpm $in $tmp_in
  in=$tmp_in
  summean=sum
else
  summean=mean
fi

for var in $vars ; do

  if [ -n "${varorigout}" ] ; then
      varout=$varorigout
  else
      varout=$var
  fi
  tmpmerged=$TMPDIR/seasmerged.$$.$var.nc 
  
  # Ensure we have a real, normalised file rather than a symlink or a relative
  # path
  in=`readlink -f $in`
  mkdir $tmp
  cd $tmp

  # Get the mean annual
  cdo chname,$var,${varout}_annual -year${summean} -selname,$var $in ann.nc
  ncatted -h -a cell_methods,${varout}_annual,a,c,"time: ${summean} within years" ann.nc
  
  # Get the mean for each standard season
  firstmon=`cdo showmon -seltimestep,1 $in`
  
  ## Select first year's jan and feb (then set to missing anyway....)
  cdo chname,$var,${varout}_djf -tim${summean} -seltimestep,0,1 -selname,$var $in djf_1.nc
  cdo setrtomiss,-1e36,1e36 djf_1.nc djf_2.nc

  #DJF, skip is first 11 months
  t0=`expr 11 - $firstmon + 1`
  cdo chname,$var,${varout}_djf -timsel${summean},3,$t0,9 -selname,$var $in djf_3.nc
  nyrs=`cdo ntime djf_3.nc`
  endyr=`expr ${nyrs} - 2`
  # Keep all but last (the single december)
  ncks -dtime,0,$endyr djf_3.nc djf_4.nc

  # DJF concat missing value for first year then chop off last year's december
  cdo mergetime djf_2.nc djf_4.nc djf.nc
  ncatted -h -a cell_methods,${varout}_djf,a,c,"time: ${summean} within years" djf.nc
  rm djf_1.nc djf_2.nc djf_3.nc djf_4.nc
  
  #MAM, skip is first 2 months
  t0=`expr 2 - $firstmon + 1`
  cdo chname,$var,${varout}_mam -timsel${summean},3,$t0,9 -selname,$var $in mam.nc
  ncatted -h -a cell_methods,${varout}_mam,a,c,"time: ${summean} within years" mam.nc
  
  #JJA, skip is first 5 months
  t0=`expr 5 - $firstmon + 1`
  cdo chname,$var,${varout}_jja -timsel${summean},3,$t0,9 -selname,$var $in jja.nc
  ncatted -h -a cell_methods,${varout}_jja,a,c,"time: ${summean} within years" jja.nc
  
  #SON, skip is first 8 months
  t0=`expr 8 - $firstmon + 1`
  cdo chname,$var,${varout}_son -timsel${summean},3,$t0,9 -selname,$var $in son.nc
  ncatted -h -a cell_methods,${varout}_son,a,c,"time: ${summean} within years" son.nc
  
  #NDJFMA, skip is first 10 months
  ## Select first year's jan - april (then set to missing anyway....)
  cdo chname,$var,${varout}_ndjfma -tim${summean} -seltimestep,1,2,3,4 -selname,$var $in ndjfma_1.nc
  cdo setrtomiss,-1e36,1e36 ndjfma_1.nc ndjfma_2.nc
  t0=`expr 10 - $firstmon + 1`
  cdo chname,$var,${varout}_ndjfma -timsel${summean},6,$t0,6 -selname,$var $in ndjfma_3.nc
  nyrs=`cdo ntime ndjfma_3.nc`
  endyr=`expr ${nyrs} - 2`
  # Keep all but last (the single december)
  ncks -dtime,0,$endyr ndjfma_3.nc ndjfma_4.nc

  # NDJFMA concat missing value for first year then chop off 
  # last year's december
  cdo mergetime ndjfma_2.nc ndjfma_4.nc ndjfma.nc
  ncatted -h -a cell_methods,${varout}_ndjfma,a,c,"time: ${summean} within years" ndjfma.nc
  rm ndjfma_1.nc ndjfma_2.nc ndjfma_3.nc ndjfma_4.nc
  
  #MJJASO, skip is first 4 months
  t0=`expr 4 - $firstmon + 1`
  cdo chname,$var,${varout}_mjjaso -timsel${summean},6,$t0,6 -selname,$var $in mjjaso.nc
  ncatted -h -a cell_methods,${varout}_mjjaso,a,c,"time: ${summean} within years" mjjaso.nc
  
  # Get the mean for each month
  cdo chname,$var,${varout}_january -selmon,1 -selname,$var $in jan.nc
  cdo chname,$var,${varout}_february -selmon,2 -selname,$var $in feb.nc
  cdo chname,$var,${varout}_march -selmon,3 -selname,$var $in mar.nc
  cdo chname,$var,${varout}_april -selmon,4 -selname,$var $in apr.nc
  cdo chname,$var,${varout}_may -selmon,5 -selname,$var $in may.nc
  cdo chname,$var,${varout}_june -selmon,6 -selname,$var $in jun.nc
  cdo chname,$var,${varout}_july -selmon,7 -selname,$var $in jul.nc
  cdo chname,$var,${varout}_august -selmon,8 -selname,$var $in aug.nc
  cdo chname,$var,${varout}_september -selmon,9 -selname,$var $in sep.nc
  cdo chname,$var,${varout}_october -selmon,10 -selname,$var $in oct.nc
  cdo chname,$var,${varout}_november -selmon,11 -selname,$var $in nov.nc
  cdo chname,$var,${varout}_december -selmon,12 -selname,$var $in dec.nc
  
  cdo merge ann.nc djf.nc mam.nc jja.nc son.nc ndjfma.nc mjjaso.nc jan.nc feb.nc mar.nc apr.nc may.nc jun.nc jul.nc aug.nc sep.nc oct.nc nov.nc dec.nc $tmpmerged
  
  allmerged="`echo $allmerged` $tmpmerged"
  cd ..
  rm -rf $tmp 
  
done ### for loop var in vars

cdo merge ${allmerged} $out
rm -rf $allmerged

ncatted -h -a script_version,global,a,c,"Calculated by $0 version $version" $out

if [ -f $tmp_in ] ; then
  rm -rf $tmp_in
fi
if [ -f $tmp_in2 ] ; then
  rm -rf $tmp_in2
fi
if [ -f ${tmp1_in} ] ; then
  rm -rf ${tmp1_in}
fi

