# zw3_applications.mk
#
# To execute:
#   make -n -B -f zw3_applications.mk  (-n is a dry run) (-B is a force make)

## Define marcos ##
include zw3_climatology_config.mk
include zw3_climatology.mk


all : ${TARGET}

### Plot the envelope ###

## Step 1: Calculate the contour zonal anomaly ##
CONTOUR_ORIG=${DATA_DIR}/${CONTOUR_VAR}_${DATASET}_${LEVEL}_daily_native.nc
CONTOUR_ZONAL_ANOM=${DATA_DIR}/${CONTOUR_VAR}_${DATASET}_${LEVEL}_daily_native-zonal-anom.nc       
${CONTOUR_ZONAL_ANOM} : ${CONTOUR_ORIG}
	${ZONAL_ANOM_METHOD} $< ${CONTOUR_VAR} $@ ${CDO_FIX_SCRIPT}

## Step 2: Apply temporal averaging to the zonal contour data ##
CONTOUR_ZONAL_ANOM_RUNMEAN=${DATA_DIR}/${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.nc 
${CONTOUR_ZONAL_ANOM_RUNMEAN} : ${CONTOUR_ZONAL_ANOM}
	cdo ${TSCALE} $< $@
	bash ${CDO_FIX_SCRIPT} $@ ${CONTOUR_VAR}

## Step 3: Plot the envelope for a selection of timesteps for publication ##
ENV_PLOT=${MAP_DIR}/env/${TSCALE_LABEL}/${VAR}/env${VAR}-${ENV_WAVE_LABEL}-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}_${PLOT_DATE1}_${PLOT_DATE2}.png 
${ENV_PLOT}: ${ENV_3D} ${CONTOUR_ZONAL_ANOM_RUNMEAN}
	bash ${VIS_SCRIPT_DIR}/plot_envelope.sh $< env${VAR} $(word 2,$^) ${CONTOUR_VAR} ${PLOT_DATE1} ${PLOT_DATE2} ${LAT_SINGLE} $@

## Step 4: Plot the climatological mean envelope ##

ENV_CLIM=${ZW3_DIR}/env${VAR}_zw3_${ENV_WAVE_LABEL}_${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-clim_${GRID}.nc
${ENV_CLIM} : ${ENV_3D} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< env${VAR} $@ --region sh

ENV_CLIM_PLOT=${MAP_DIR}/env${VAR}_zw3_${ENV_WAVE_LABEL}_${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-clim_${GRID}.png
${ENV_CLIM_PLOT} : ${ENV_CLIM}
	bash ${VIS_SCRIPT_DIR}/plot_seasonal_climatology.sh $< env${VAR} $@



### Plot the Hilbert transform for publication ###

HILBERT_PLOT=${INDEX_DIR}/hilbert/${TSCALE_LABEL}/hilbert_zw3_${ENV_WAVE_LABEL}_${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${LAT_LABEL}_${PLOT_DATE1}_${PLOT_DATE2}.png 
${HILBERT_PLOT}: ${V_RUNMEAN}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_hilbert.py $< ${VAR} $@ ${PLOT_DIMS} --latitude ${LAT_SINGLE} --dates ${PLOT_DATE1} ${PLOT_DATE2} --wavenumbers ${WAVE_MIN} ${WAVE_MAX} --figure_size 15 6

### Index comparisons ###

## Plot 1: My metric versus wave 3 ##

METRIC_VS_WAVE3_PLOT=${INDEX_DIR}/${METRIC}-vs-wave3_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png
${METRIC_VS_WAVE3_PLOT} : ${WAVE_STATS} ${FOURIER_INFO}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_scatter.py $(word 1,$^) ${METRIC} $(word 2,$^) wave3_amp $@ --colour $(word 2,$^) wave4_amp --normalise --trend_line --zero_lines --thin 3 --cmap hot_r --ylabel wave_3 --xlabel my_index --ylat ${LAT_SEARCH_MIN} ${LAT_SEARCH_MAX} ${MER_METHOD} --clat ${LAT_SEARCH_MIN} ${LAT_SEARCH_MAX} ${MER_METHOD}

## Plot 2: My metric versus ZW3 index ##

METRIC_VS_ZW3_PLOT=${INDEX_DIR}/${METRIC}-vs-zw3index_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png
${METRIC_VS_ZW3_PLOT} : ${WAVE_STATS} ${ZW3_INDEX} ${FOURIER_INFO}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_scatter.py $(word 1,$^) ${METRIC} $(word 2,$^) zw3 $@ --colour $(word 3,$^) wave3_phase --normalise --trend_line --zero_lines --thin 3 --cmap jet --ylabel ZW3_index --xlabel planetary_wave_index --clat ${LAT_SINGLE} ${LAT_SINGLE} none

## Plot 3: My metric versus SAM and ENSO ##

ENSO_DATA=${DATA_HOME}/Indices/tos_CPC_surface_monthly-anom-wrt-1981-2010_nino34.nc
SAM_DATA=${DATA_HOME}/Indices/psl_Marshall_surface_monthly_SAM.nc

METRIC_VS_ENSO_PLOT=${INDEX_DIR}/${METRIC}-vs-${ENSO_METRIC}_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png
${METRIC_VS_ENSO_PLOT} : ${WAVE_STATS} ${ENSO_DATA} 
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_scatter.py $(word 1,$^) ${METRIC} $(word 2,$^) ${ENSO_METRIC} $@ --trend_line --zero_lines

METRIC_VS_SAM_PLOT=${INDEX_DIR}/${METRIC}-vs-${SAM_METRIC}_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png
${METRIC_VS_SAM_PLOT} : ${WAVE_STATS} ${SAM_DATA} 
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_scatter.py $(word 1,$^) ${METRIC} $(word 2,$^) ${SAM_METRIC} $@ --trend_line --zero_lines

METRIC_VS_ENSO_VS_SAM_PLOT=${INDEX_DIR}/${METRIC}-vs-${ENSO_METRIC}-vs-${SAM_METRIC}_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png
${METRIC_VS_ENSO_VS_SAM_PLOT} : ${ENSO_DATA} ${SAM_DATA} ${WAVE_STATS}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_scatter.py $(word 1,$^) ${ENSO_METRIC} $(word 2,$^) ${SAM_METRIC} $@ --colour $(word 3,$^) ${METRIC} --trend_line --zero_lines



### Climatological stats ###

## Seasonal and monthly summaries ##

SEAS_MON_SUMMARY_PLOT=${INDEX_DIR}/clim/montots-seasvals_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.png 
${SEAS_MON_SUMMARY_PLOT} : ${WAVE_STATS} 
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< ${METRIC} --plot_name $@ --plot_types monthly_totals_histogram seasonal_values_line --metric_threshold ${METRIC_HIGH_THRESH} --scale_annual 0.25 --figure_size 16 6


## Composite envelope (with zg overlay) ##

# Step 1: Generate list of dates for use in composite creation #

DATE_LIST=${COMP_DIR}/dates_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.txt 
${DATE_LIST}: ${WAVE_STATS}
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< ${METRIC} --date_list $@ --metric_threshold ${METRIC_HIGH_THRESH}

# Step 2: Get the composite mean envelope #

COMP_ENV_FILE=${COMP_DIR}/env${VAR}-composite_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}.nc 
${COMP_ENV_FILE} : ${ENV_3D} ${DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< env${VAR} $@ --date_file $(word 2,$^) 

# Step 3: Get the composite mean contour #

CONTOUR_ZONAL_ANOM_RUNMEAN_COMP=${COMP_DIR}/${CONTOUR_VAR}-composite_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.nc 
${CONTOUR_ZONAL_ANOM_RUNMEAN_COMP} : ${CONTOUR_ZONAL_ANOM_RUNMEAN} ${DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< ${CONTOUR_VAR} $@ --date_file $(word 2,$^)

# Step 4: Plot #

COMP_ENV_PLOT=${COMP_DIR}/env${VAR}-composite_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}-${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-zonal-anom.png
${COMP_ENV_PLOT} : ${COMP_ENV_FILE} ${CONTOUR_ZONAL_ANOM_RUNMEAN_COMP}
	bash ${VIS_SCRIPT_DIR}/plot_composite.sh $(word 1,$^) env${VAR} $(word 2,$^) ${CONTOUR_VAR} $@


## Spectral density ##

# Mutli-timescale spectrum #

TSCALE_SPECTRUM=${SPECTRA_DIR}/${VAR}-r2spectrum_${DATASET}_${LEVEL}_daily_${GRID}.png
${TSCALE_SPECTRUM}: ${V_ORIG}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_timescale_spectrum.py $< ${VAR} $@ --latitude ${LAT_SINGLE} --runmean 1 5 10 15 30 60 90 180 365 --scaling R2

# Mutli-file spectrum #

MULTIFILE_SPECTRUM=${SPECTRA_DIR}/${METRIC}-r2spectrum_zw3_${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}-${LAT_LABEL}.png
${MULTIFILE_SPECTRUM} : ${WAVE_STATS}
	${PYTHON} ${VIS_SCRIPT_DIR}/plot_multifile_spectrum.py $< ${METRIC} $@ --scaling R2 --xlim 0 200 



### Calculate composite for variable of interest (e.g. tas, pr, sic) two ways ###

## Step 1: Generate list of dates for use in composite creation (done above) ##

## Step 2: Calculate the anomaly for the variable of interest and apply temporal averaging ##

COMP_VAR_ORIG=${DATA_DIR}/${COMP_VAR}_${DATASET}_surface_daily_${GRID}.nc
COMP_VAR_ANOM_RUNMEAN=${DATA_DIR}/${COMP_VAR}_${DATASET}_surface_${TSCALE_LABEL}-anom-wrt-all_native.nc
${COMP_VAR_ANOM_RUNMEAN} : ${COMP_VAR_ORIG} 
	cdo ${TSCALE} -ydaysub $< -ydayavg $< $@
	bash ${CDO_FIX_SCRIPT} $@ ${COMP_VAR}

## Step 3: Calculate & plot composite - method 1 ##

COMP_VAR_FILE=${COMP_DIR}/${COMP_VAR}-composite_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.nc 
${COMP_VAR_FILE} : ${COMP_VAR_ANOM_RUNMEAN} ${DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< ${COMP_VAR} $@ --date_file $(word 2,$^) --region sh 

COMP_VAR_PLOT=${COMP_DIR}/${COMP_VAR}-composite_zw3_${METRIC}${METRIC_HIGH_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}-${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.png
${COMP_VAR_PLOT} : ${COMP_VAR_FILE} ${CONTOUR_ZONAL_ANOM_RUNMEAN_COMP}
	bash ${VIS_SCRIPT_DIR}/plot_composite.sh $(word 1,$^) ${COMP_VAR} $(word 2,$^) ${CONTOUR_VAR} $@

## Step 4a: Calculate & plot composite - method 2, > 90pct ##

COMP_METRIC_90PCT_FILE=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}90pct-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.nc
${COMP_METRIC_90PCT_FILE} : ${COMP_VAR_ANOM_RUNMEAN} ${WAVE_STATS}
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_index_composite.py $(word 1,$^) ${COMP_VAR} $(word 2,$^) ${METRIC} 90pct $@ --region sh

COMP_METRIC_90PCT_PLOT=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}90pct-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.png
${COMP_METRIC_90PCT_PLOT} : ${COMP_METRIC_90PCT_FILE}
	bash ${VIS_SCRIPT_DIR}/plot_index_composite.sh $< ${METRIC} 90pct $@

## Step 4b: Calculate & plot composite - method 2, < 10pct ##

COMP_METRIC_10PCT_FILE=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}10pct-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.nc
${COMP_METRIC_10PCT_FILE} : ${COMP_VAR_ANOM_RUNMEAN} ${WAVE_STATS}
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_index_composite.py $(word 1,$^) ${COMP_VAR} $(word 2,$^) ${METRIC} 10pct $@ --include below --region sh

COMP_METRIC_10PCT_PLOT=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}10pct-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.png
${COMP_METRIC_10PCT_PLOT} : ${COMP_METRIC_10PCT_FILE}
	bash ${VIS_SCRIPT_DIR}/plot_index_composite.sh $< ${METRIC} 10pct $@

## Step 4c: Calculate & plot composite - method 2, > 90pct abs ##

COMP_METRIC_90PCTABS_FILE=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}90pctabs-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.nc
${COMP_METRIC_90PCTABS_FILE} : ${COMP_VAR_ANOM_RUNMEAN} ${WAVE_STATS}
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_index_composite.py $(word 1,$^) ${COMP_VAR} $(word 2,$^) ${METRIC} 10pct $@ --absolute --region sh

COMP_METRIC_90PCTABS_PLOT=${COMP_DIR}/${METRIC}-composite_zw3_${COMP_VAR}90pctabs-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.png
${COMP_METRIC_90PCTABS_PLOT} : ${COMP_METRIC_90PCTABS_FILE}
	bash ${VIS_SCRIPT_DIR}/plot_index_composite.sh $< ${METRIC} 90pctabs $@



### Calculate composite circulation for the ZW3 index ###

## Step 1: Generate list of dates for use in composite creation ##

ZW3_DATE_LIST=${COMP_DIR}/dates_zw3_zw3${METRIC_HIGH_THRESH}_${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.txt 
${ZW3_DATE_LIST} : ${ZW3_INDEX} 
	${PYTHON} ${DATA_SCRIPT_DIR}/create_date_list.py $< zw3 $@ --metric_threshold ${METRIC_HIGH_THRESH}

## Step 2: Get the composite mean contour ##

CONTOUR_ZONAL_ANOM_RUNMEAN_ZW3COMP=${COMP_DIR}/${CONTOUR_VAR}-composite_zw3_zw3${METRIC_HIGH_THRESH}_${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.nc 
${CONTOUR_ZONAL_ANOM_RUNMEAN_ZW3COMP} : ${CONTOUR_ZONAL_ANOM_RUNMEAN} ${ZW3_DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< ${CONTOUR_VAR} $@ --date_file $(word 2,$^) --region sh

## Step 3: Plot it

ZW3COMP_VAR_PLOT=${COMP_DIR}/${CONTOUR_VAR}-composite_zw3_zw3${METRIC_HIGH_THRESH}_${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.png
${ZW3COMP_VAR_PLOT} : ${CONTOUR_ZONAL_ANOM_RUNMEAN_ZW3COMP}
	bash ${VIS_SCRIPT_DIR}/plot_composite_contour.sh $< ${CONTOUR_VAR} $@


### The anti-composite (i.e. when the metric value is really low) ###

## Step 1: Generate list of dates for use in composite creation ##

ANTI_DATE_LIST=${COMP_DIR}/dates_zw3_${METRIC}${METRIC_LOW_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_${GRID}-${MER_METHOD}.txt 
${ANTI_DATE_LIST}: ${WAVE_STATS}
	${PYTHON} ${DATA_SCRIPT_DIR}/parse_wave_stats.py $< ${METRIC} --date_list $@ --metric_threshold ${METRIC_LOW_THRESH} --threshold_direction less

## Step 2: Get the composite variable mean ##

ANTICOMP_VAR_FILE=${COMP_DIR}/${COMP_VAR}-composite_zw3_${METRIC}${METRIC_LOW_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.nc 
${ANTICOMP_VAR_FILE} : ${COMP_VAR_ANOM_RUNMEAN} ${ANTI_DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< ${COMP_VAR} $@ --date_file $(word 2,$^) --region sh

## Step 3: Get the composite mean contour ##

CONTOUR_ZONAL_ANOM_RUNMEAN_ANTICOMP=${COMP_DIR}/${CONTOUR_VAR}-composite_zw3_${METRIC}${METRIC_LOW_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}_native-zonal-anom.nc 
${CONTOUR_ZONAL_ANOM_RUNMEAN_ANTICOMP} : ${CONTOUR_ZONAL_ANOM_RUNMEAN} ${ANTI_DATE_LIST} 
	${PYTHON} ${DATA_SCRIPT_DIR}/calc_composite.py $< ${CONTOUR_VAR} $@ --date_file $(word 2,$^) --region sh

## Step 4: Plot ## 

ANTICOMP_VAR_PLOT=${COMP_DIR}/${COMP_VAR}-composite_zw3_${METRIC}${METRIC_LOW_THRESH}-${ENV_WAVE_LABEL}_env-${VAR}-${CONTOUR_VAR}_${DATASET}_${LEVEL}_${TSCALE_LABEL}-anom-wrt-all_${GRID}.png
${ANTICOMP_VAR_PLOT} : ${ANTICOMP_VAR_FILE} ${CONTOUR_ZONAL_ANOM_RUNMEAN_ANTICOMP}
	bash ${VIS_SCRIPT_DIR}/plot_composite.sh $(word 1,$^) ${COMP_VAR} $(word 2,$^) ${CONTOUR_VAR} $@


### MEX ###

MEX_INDEX=${ZW3_DIR}/mex_${COMP_VAR}_${DATASET}_surface_${TSCALE_LABEL}-anom-wrt-all_native.nc 
${MEX_INDEX} : ${COMP_VAR_ANOM_RUNMEAN}
	${CDAT} ${DATA_SCRIPT_DIR}/calc_climate_index.py MEX $< ${COMP_VAR} $@

