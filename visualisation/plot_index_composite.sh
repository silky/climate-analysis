function usage {
    echo "USAGE: bash $0 infile var theshold outfile"
    echo "   varfile:    Input file name for colour plot"
    echo "   var:        Variable for colour plot"
    echo "   threshold:  Threshold used for the index composite [90pct, 10pct, 90pctabs]"
    echo "   outfile:    Output file name"
    echo "   e.g. bash $0 ampmedian_data.nc ampmedian 90pct plot.png"
    exit 1
}

nargs=4

if [ $# -ne $nargs ] ; then
  usage
fi

varfile=$1
var=$2
threshold=$3
outfile=$4
  

if [[ $var == 'ampmedian' && $threshold == '90pct' ]] ; then
    palette=hot_r
elif [[ $var == 'ampmedian' && $threshold == '90pctabs' ]] ; then
    palette=jet
elif [[ $var == 'ampmedian' && $threshold == '10pct' ]] ; then
    palette=Blues
else
    echo "Unknown variable: $var and threshold: $threshold combination"
    exit 1
fi


/usr/local/anaconda/bin/python ~/phd/visualisation/plot_map2.py ${varfile} ${var}_annual none none none colour 1 3 2 --infiles ${varfile} ${var}_DJF none none none colour 3 --infiles ${varfile} ${var}_MAM none none none colour 4 --infiles ${varfile} ${var}_JJA none none none colour 5 --infiles ${varfile} ${var}_SON none none none colour 6 --palette ${palette} --output_projection SouthPolarStereo --subplot_headings Annual none DJF MAM JJA SON --figure_size 10 16 --colourbar_type individual --ofile ${outfile} --subplot_spacing 0.15 --infiles ${varfile} p_annual none none none hatching 1 --infiles ${varfile} p_DJF none none none hatching 3 --infiles ${varfile} p_MAM none none none hatching 4 --infiles ${varfile} p_JJA none none none hatching 5 --infiles ${varfile} p_SON none none none hatching 6 --hatch_bounds 0.0 0.01 --hatch_styles \\\\

