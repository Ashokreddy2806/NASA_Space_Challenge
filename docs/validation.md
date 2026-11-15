# Validation against known analog sites (Phase 3)

Balanced preset. *Score* is the 0-100 similarity at the site's grid cell; *rank pct* is its area-weighted percentile among all Earth land cells. *Checks* test the features each site is famous for (sub-score >= 80 counts as a pass). Failures are reported, not hidden.

## Lunar south pole

Features dropped (no target value): temp_diurnal_range_c, temp_min_coldest_c, temp_annual_range_c.

| Site | Score | Rank pct | Checks (sub-score) | Best matches | Worst matches |
|---|---|---|---|---|---|
| Atacama | 80.8 | 94.2 | precip_annual_mm 96.1 OK, precip_driest_month_mm 89.0 OK | hurst_2_32km, precip_annual_mm, precip_driest_month_mm | ice_proxy, temp_mean_c, temp_max_warmest_c |
| Dry Valleys | 87.6 | 98.7 | precip_annual_mm 88.5 OK, ice_proxy 87.9 OK | roughness_20km_m, slope_20km_deg, relief_20km_m | hurst_2_32km, precip_driest_month_mm, ice_proxy |
| Devon Island / Haughton | 67.0 | 71.6 | ice_proxy 91.2 OK | temp_mean_c, ice_proxy, temp_max_warmest_c | hurst_2_32km, relief_20km_m, precip_driest_month_mm |
| Death Valley | 88.2 | 98.8 | precip_annual_mm 91.3 OK, relief_20km_m 91.6 OK | hurst_2_32km, slope_20km_deg, relief_20km_m | temp_max_warmest_c, temp_mean_c, ice_proxy |
| Iceland | 72.8 | 81.8 | relief_20km_m 92.7 OK, roughness_20km_m 87.7 OK | hurst_2_32km, relief_20km_m, temp_max_warmest_c | precip_driest_month_mm, precip_annual_mm, ice_proxy |

## Jezero Crater (Mars)

Features dropped (no target value): temp_mean_c, temp_diurnal_range_c, temp_max_warmest_c, temp_min_coldest_c, temp_annual_range_c, ice_proxy.

| Site | Score | Rank pct | Checks (sub-score) | Best matches | Worst matches |
|---|---|---|---|---|---|
| Atacama | 91.4 | 99.0 | precip_annual_mm 96.1 OK, precip_driest_month_mm 89.0 OK | roughness_10km_m, roughness_20km_m, precip_annual_mm | relief_20km_m, precip_driest_month_mm, roughness_5km_m |
| Dry Valleys | 78.8 | 82.6 | precip_annual_mm 88.5 OK | precip_annual_mm, relief_20km_m, slope_20km_deg | hurst_2_32km, roughness_5km_m, roughness_10km_m |
| Devon Island / Haughton | 81.2 | 87.6 | n/a | roughness_20km_m, roughness_10km_m, roughness_5km_m | hurst_2_32km, precip_driest_month_mm, precip_annual_mm |
| Death Valley | 88.3 | 97.3 | precip_annual_mm 91.3 OK, relief_20km_m 91.6 OK | roughness_5km_m, roughness_10km_m, hurst_2_32km | precip_driest_month_mm, slope_20km_deg, roughness_20km_m |
| Iceland | 73.4 | 70.2 | relief_20km_m 90.5 OK, roughness_20km_m 89.8 OK | roughness_5km_m, roughness_10km_m, slope_20km_deg | precip_driest_month_mm, precip_annual_mm, roughness_20km_m |

## Reading this

- Percentile distance treats a gap of N percentile points as equal everywhere on the scale. Near the extremes of a skewed feature (relief, slope, roughness) that compresses large physical differences.
- Temperatures are not scored: no site-specific literature values exist yet.
- Earth cannot reproduce reduced gravity, vacuum or thin atmosphere, or the radiation environment.
