# Provisional SoLEXS recorded-sequence experiment

The user's detailed milestone authorizes autonomous research, design, implementation,
conditional training, independent review and feature-branch publication. It supersedes
additional skill approval handoffs. Base is Phase E `83b54435c1634f7de0a3ec6494439c023a4d0296`;
only `research/solexs-provisional-sequence-modeling` may receive commits/pushes.

Stage A is a feasibility investigation. Existing bounded ZIP/gzip/FITS loaders and
independent array inspection must establish exact identities, strictly increasing
recorded coordinates, usable finite LC values and separable contiguous segments.
The task is numerical prediction of recorded SDD2 LC RATE.COUNTS; TUNIT is absent.
`UNKNOWN_UNENCODED_NATIVE_VALUE` identifies that absence, not a physical unit.
All artifacts carry `EXPLORATORY / PROVISIONAL / NOT SCIENTIFICALLY CALIBRATED`.
Native TIME is retained for order/discontinuity diagnostics only. No seconds/UTC,
rate, exposure, calibrated flux, response mapping, health clearance or flare target
is inferred. Phase E E1/E2/E3/E6 remain blocked; E4/E5 remain partially verified.

Use separate sample-index contracts, never fictional P1 time coordinates. Preserve
P1/P2 GOES/source gates. Reuse native access, canonical fingerprints, P2's numeric
linear model factory and masked MSE. No P3 dependency or modification.

Initial frozen engineering configuration: context 64, horizon 8, stride 8, one
recorded coordinate unit as the expected step. These are sample counts, chosen as
small fixed engineering budgets, not inferred physical variability timescales.
July 1 raw rows [0,60480) train, [60480,86400) validation; July 3 is a distinct test
product. Nominal dates specify source selection, not verified UTC chronology.
Windows stay wholly inside each split, source and finite contiguous segment. No
sorting/deduplication, stitching, padding or interpolation. Duplicate/reversed or
nonfinite coordinates abort. Unexpected positive coordinate steps break segments.
NaNs are retained in source masks and excluded from complete windows; infinities
abort. Excluded windows/missing rows are reported. GTI point membership is a
separate diagnostic, never live exposure or a new quality screen.

Unique valid raw training rows alone fit population mean/std (scale 1 if constant).
Identity transform; no physical reference/log conversion. Comparators: persistence,
training mean, trailing 16-sample mean, fixed mean-reverting AR(1)-style phi=0.9,
and direct Ridge alpha=1 on standardized complete training windows. Existing P1
baseline classes cannot consume sample-index contracts, so isolated numerical
implementations are necessary. No ARIMA search.

A generic masked linear predictor (1,032 parameters) is permissible only after
reproducible baselines and sufficient train/validation support. Eight seeded CPU
Adam epochs, batch 128, learning rate .001, clip 1; validation masked normalized
MSE selects earliest minimum epoch. No JEPA claim or hyperparameter search.
Test metrics are computed only after all parameters and validation selection are
frozen. Reproduction reruns fixed configuration solely for consistency checks.

MAE/RMSE and skill 1 - error/persistence error share exact target masks; report
prediction coverage and excluded/missing support. No physical units or uncertainty
intervals are invented. Two noncontiguous days support engineering holdout only,
not statistical generalization, operational causality or scientific superiority.

Publish outputs exclusively under ignored results with source/config/code/data/
split/window/prediction/checkpoint hashes, versions and finite JSON. Existing output
paths fail. Preserve prior identities and archive bytes. Track only small code,
config, tests, provenance summary and new reports. Independent scientific and code
reviews, full suite, normal package import/CLI and final preservation/ref checks
are required before final feature-only push. No PR or merge.
