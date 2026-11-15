export const TARGET_LABELS = {
  moon_south_pole: 'Lunar south pole',
  mars_jezero: 'Jezero Crater',
};

export const PRESET_ORDER = ['balanced', 'rover_mobility', 'cold_trap_ice', 'thermal_cycling'];

export const PRESET_LABELS = {
  balanced: 'Balanced',
  rover_mobility: 'Rover mobility',
  cold_trap_ice: 'Cold-trap ice',
  thermal_cycling: 'Thermal cycling',
};

export const PRESET_HELP = {
  balanced: 'General analog training and instrument testing across all scored features.',
  rover_mobility: 'Rover traverse and driving tests: slope, relief and roughness of the ground.',
  cold_trap_ice: 'Ice prospecting and cold-trap operations: terrain and climate that favour ice.',
  thermal_cycling: 'Hardware thermal testing: surface temperature swings for instruments and rovers.',
};

export const REASON_LABELS = {
  missing_no_source: 'no source dataset',
  missing_site_specific_literature_value: 'no site-specific literature value',
  not_in_mvp: 'not in the MVP scope',
};

export const FEATURE_LABELS = {
  relief_20km_m: 'Relief 20 km',
  slope_20km_deg: 'Slope 20 km',
  roughness_5km_m: 'Roughness 5 km',
  roughness_10km_m: 'Roughness 10 km',
  roughness_20km_m: 'Roughness 20 km',
  hurst_2_32km: 'Hurst 2-32 km',
  precip_annual_mm: 'Annual precipitation',
  precip_driest_month_mm: 'Driest-month precipitation',
  temp_mean_c: 'Mean temperature',
  temp_max_warmest_c: 'Warmest-month max',
  temp_min_coldest_c: 'Coldest-month min',
  temp_diurnal_range_c: 'Diurnal range',
  temp_annual_range_c: 'Annual range',
  ice_proxy: 'Ice proxy',
};
