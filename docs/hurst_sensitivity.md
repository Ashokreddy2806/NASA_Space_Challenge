# Earth Hurst robustness — with and without the 2 km lag

ETOPO 2022 is a 60 arc-second product (~1.85 km), so the shortest configured
Hurst lag (2 km) is close to the sampling limit. This check recomputes the
exponent from real ETOPO patches with the full lag list and with the 2 km lag
removed.

- Samples requested / used: 600 / 504 (seed 42, skipped 0, undefined 96).
- Patch size: 96 km on a 2.00 km working grid; Hurst window 32 km.

| Lag set | Median H | p16 | p84 | Min | Max |
|---|---|---|---|---|---|
| Full [2.0, 4.0, 8.0, 16.0, 32.0] | 0.6248 | 0.4169 | 0.8908 | 0.2111 | 1.5000 |
| Drop 2 km → [4.0, 8.0, 16.0, 32.0] | 0.5830 | 0.3378 | 0.8982 | 0.0680 | 1.5000 |

- Median shift: +0.0397
- Median absolute difference: 0.0472
- Pearson r between the two estimates: 0.9901
- Thresholds: |Δmedian| ≤ 0.05, r ≥ 0.99

**Verdict: robust.** The fitted Hurst exponent is not an artefact of the shortest lag, so it can be compared with the Moon and Mars where those bodies resolve different lag sets.
