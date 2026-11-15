# Validation against known analog sites (Phase 3)

Balanced preset. *Score* is the 0-100 similarity at the site's grid cell; *rank pct* is its area-weighted percentile among all Earth land cells. *Check* is PASS when the rank pct is at least 75. Failures are reported, not hidden.

## Lunar south pole

Features dropped (no target value): temp_diurnal_range_c, temp_min_coldest_c, temp_annual_range_c.

| Site | Score | Rank pct | Check | Best matches | Worst matches |
|---|---|---|---|---|---|
| Atacama | 63.1 | 87.2 | PASS | precip_driest_month_mm, hurst_2_32km, precip_annual_mm | slope_20km_deg, relief_20km_m, roughness_20km_m |
| Dry Valleys | 77.6 | 98.5 | PASS | precip_driest_month_mm, roughness_20km_m, slope_20km_deg | ice_proxy, hurst_2_32km, precip_annual_mm |
| Devon Island / Haughton | 48.9 | 69.8 | FAIL | precip_driest_month_mm, roughness_5km_m, roughness_10km_m | slope_20km_deg, hurst_2_32km, relief_20km_m |
| Death Valley | 75.2 | 97.6 | PASS | hurst_2_32km, precip_driest_month_mm, roughness_20km_m | slope_20km_deg, roughness_10km_m, roughness_5km_m |
| Iceland | 57.4 | 80.6 | PASS | hurst_2_32km, relief_20km_m, roughness_20km_m | precip_annual_mm, precip_driest_month_mm, slope_20km_deg |

## Jezero Crater (Mars)

Features dropped (no target value): temp_mean_c, temp_diurnal_range_c, temp_max_warmest_c, temp_min_coldest_c, temp_annual_range_c, ice_proxy.

| Site | Score | Rank pct | Check | Best matches | Worst matches |
|---|---|---|---|---|---|
| Atacama | 89.1 | 99.2 | PASS | precip_driest_month_mm, roughness_10km_m, roughness_20km_m | relief_20km_m, precip_annual_mm, slope_20km_deg |
| Dry Valleys | 59.3 | 46.6 | FAIL | precip_driest_month_mm, relief_20km_m, precip_annual_mm | slope_20km_deg, roughness_10km_m, hurst_2_32km |
| Devon Island / Haughton | 76.6 | 87.2 | PASS | roughness_20km_m, roughness_10km_m, slope_20km_deg | hurst_2_32km, precip_annual_mm, relief_20km_m |
| Death Valley | 82.1 | 95.2 | PASS | roughness_10km_m, precip_driest_month_mm, hurst_2_32km | slope_20km_deg, precip_annual_mm, roughness_20km_m |
| Iceland | 67.7 | 68.5 | FAIL | roughness_10km_m, hurst_2_32km, relief_20km_m | precip_annual_mm, precip_driest_month_mm, slope_20km_deg |

## Reading this

- Scores use scaled physical distance: each skewed feature is log1p-transformed and divided by its Earth P95-P5 span, so equal physical gaps count equally across the scale.
- Moon temperatures are Diviner surface values compared with Earth air temperature. This is not like-for-like and lies beyond the Earth range. They enter only the thermal_cycling preset.
- Mars has no temperature source, so its thermal_cycling score is unavailable.
- Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment.
