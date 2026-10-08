# Phase E scientific evidence matrix

Final evidence date: **2026-10-09, Asia/Kolkata**. Applies only to the registered
July 1/3 2024 sample and inspected resources. The [scientific report](SOLEXS_PHASE_E_SCIENTIFIC_VALIDATION.md)
explains decisions; the [evidence manifest](../data/manifests/solexs_phase_e_evidence.json)
records full hashes, software versions and gate outcomes.

## Original sources, versions and applicability

| ID | Original source and exact version/locator | Applicability and residual uncertainty |
|---|---|---|
| M | URSC/ISRO [SoLEXS Data Analysis Guide](https://pradan1.issdc.gov.in/al1/protected/downloadFile/solexs/SoLEXS-UserManual.pdf), v1.0, January 2025. §§2.1–2.2: PDF pp5–6 / printed pp2–3; §2.4: PDF p7 / printed p4; §3.3: PDF p8 / printed p5; §§4.5.1–4.5.5: PDF pp17–19 / printed pp14–16. | Original locally read; user-reported official download. Generic L1 guidance predating re-release; no release-1.1 clock/correction/index contract. 363,311 bytes; SHA-256 `d97c83618c85a0984e7dd0300ce5c16c4748ed5facde525949f902fe9f72abda`. |
| U | Locally supplied official `SoLEXS_Release_Updates.txt`, updated 2026-06-09, sections (1), (2), (3). [Existing source pin](../data/manifests/solexs_guidance_sources.json). | User-reported PRADAN origin; direct acquisition URL UNKNOWN. Separates data/processing/tools releases; no row-level repair instructions. 2,481 bytes; SHA-256 `7fc0229985fef2bd60ab23bc554c09e64f526719f11825e44a60eed12f5396ce`. |
| P | Sarwade et al. [versioned full paper](https://arxiv.org/html/2509.26292v2), v2, 2025-11-03; JATIS 11(4),045005, DOI [10.1117/1.JATIS.11.4.045005](https://doi.org/10.1117/1.JATIS.11.4.045005). §§4.1–4.5: PDF pp7–16; §§5.2–5.4: pp18–23. | Instrument calibration evidence; not exact July-file applicability. PDF locally pinned in Phase E record; publisher page unavailable to retrieval. |
| G | Woods et al. [GOES-R XRS design and pre-flight calibration](https://doi.org/10.1029/2024JA032925), JGR Space Physics 129(11),e2024JA032925 (2024), published 2024-11-21; §§3.2/4.1, Equations1–3/Figure5; [original Paperclip response lines](https://paperclip.gxl.ai/citations/papers/PMC11582350#L137-L142). | Original article read through primary full text and Paperclip. Wavelength-dependent photodiode response/assumptions explain why nominal energy overlap is insufficient. Does not establish local source alignment. |
| N | NOAA [XRS L2 User's Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf), 2025-12-15, §§2–2.4 pp4–6 and §§3–4 pp6–8. | Defines GOES bands/clock/science-quality semantics. Existing 3,159,163-byte pin SHA-256 `5736ef81e8a34aef8a0672c14193ed641f846f4d8008c66ee80ec12e243f3cee`; no new GOES processing performed. |
| NR | NOAA [XRS L2 ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf), 2025-12-15, §5/Table4 p5. | Official version/caveat context for v2-2-1; not proof of SoLEXS compatibility or a new local GOES acceptance test. |
| F | [FITS standard4.0](https://fits.gsfc.nasa.gov/standard40/fits_standard40aa-le.pdf), updated2016-07-22 / language edits2018-08-13, §§9.2–9.5. | Timing keywords/reference/bin semantics; standards do not authorize mission-specific repair. Local pin in D sources. |
| O | HEASARC [OGIP CAL/GEN/92-002](https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/docs/memos/cal_gen_92_002/cal_gen_92_002.html), version2020-12-08 / URL edits2022-10-11, §§2.1–2.3,3.2.2,4. | RMF/ARF roles and channel correspondence; not instrument calibration approval. Local PDF pin in D sources. |
| B11 | Supplied PRADAN tools1.1 archive, CALDB1; [D.1 evidence and TAR member pins](../data/manifests/solexs_phase_d1_evidence.json). | User-reported authenticated download; independently checked local package/member bytes. All outer regular members rehashed, no install/execution. Nested distributions not recursively reviewed. |
| T11 | [Author tools1.1](https://github.com/abhilash-sw/solexs_tools/tree/24693afeeab5f67ce0277fe84de059bbe54223cb), exact commit `24693afeeab5f67ce0277fe84de059bbe54223cb`, README/time_utils.py/solexs_genlc.py/solexs_genspec.py and CALDB. | Selected bytes match B11. Timezone-sensitive writer/header construction and uncorrected aggregation are source observations, not the generating pipeline's certified behavior. |
| T13 | [Author tools1.3](https://github.com/abhilash-sw/solexs_tools/tree/a2db6a92da6399fb3abafc115a430e9be08ddce1), exact commit `a2db6a92da6399fb3abafc115a430e9be08ddce1`, deadtime.py lines17–27/40–67. | HK-dependent candidate workflow; compatibility to older products UNKNOWN. |
| T16 | [Author tools1.6](https://github.com/abhilash-sw/solexs_tools/tree/51403b02fbb7ae2eb0b4eb539e881ffd56c1c772), exact commit `51403b02fbb7ae2eb0b4eb539e881ffd56c1c772`, deadtime.py lines19–30/42–80; caldb_utils.py; genlc.py lines186–241; CALDB index. | Public HEAD independently rechecked on continuation; date-selection and matching row counts do not validate pipeline/cadence/HK acquisition. No external algorithm adopted. |
| W | [ISRO–ESA workshop](https://github.com/ISRO-ESA-Heliophysics-Workshop/hands-on-materials/tree/d7453029cfac574c0cf444ca47d2ce97fcc17245/aditya-l1/solexs), commit `d7453029cfac574c0cf444ca47d2ce97fcc17245`, data-introduction cells11/19 and tools guide. | Stored example uses pipeline2.0-beta.1 despite a v1.1 path; not an applicable pipeline1.1 certificate. Notebooks inspected, not run. |
| R | [URSC SoLEXS page](https://www.ursc.gov.in/SoLEXS.jsp), states last updated2026-06-22, instrument specifications. | General detector roles and temporal capabilities only; current official page checked by timing/calibration investigators. Anonymous PRADAN catalogue redirects to login; authenticated current contents UNKNOWN. |

All C/D/D.1 local source pins were independently rechecked (39 distinct paths).
Original manifests retain their dated provenance and are linked rather than
duplicated. Source access failure never means a resource is globally unavailable.

## Requirement-to-evidence mapping

Statuses below concern the named requirement, not a blanket approval. Native
verification and scientific applicability are explicitly separate.

| Claim / requirement | Documentation / literature | Actual observation and validation code | Verification status | Uncertainty / action |
|---|---|---|---|---|
| Immutable pilot identity | Registration/storage policy; B11/source pins | Both full ZIP sizes/SHA-256 match [inventory](../data/manifests/aditya_inventory.json); CRC/gzip/FITS checks in [native loader](../src/solar_flare_jepa/data/solexs.py). | VERIFIED, OBSERVED identity | Portal checksums/acquisition timestamps not independently supplied. |
| E1 native order/cadence/LC–PI association | M §§2.1.2–2.1.3 | 86,400 equal coordinates/day; every step1; no duplicate/backwards steps. [Probe](../scripts/probe_solexs_readiness.py), [tests](../tests/test_solexs_readiness_probe.py). | VERIFIED, OBSERVED numerical relation | Equality does not prove UTC or bin placement. |
| E1 absolute clock | M §2.2; U(1)/(3); F §§9.2–9.5 | LC fractional MJD/date conflict; PI reference cards absent in both HDUs; GTI units/epoch absent. Inspector preserves warnings. | BLOCKED_EXTERNAL_EVIDENCE | Obtain mission precedence/clock/leap/correction/uncertainty policy; do not shift by5.5h. |
| E1 LC integration/completion | M §2.1.3; F bin support; T11 | LC TIME matches PI start, TIMEPIXR absent. | BLOCKED_EXTERNAL_EVIDENCE | LC-start hypothesis INFERRED; completed-bin availability UNKNOWN. |
| E2 actual CALDB availability | M §2.4; B11 | Official bundle exists; exact member equality with RMF/ARF/bounds; hashes in evidence record. | VERIFIED, OBSERVED local availability | Older Phase E checklist predated this positive D.1 fact; scientific acceptance unchanged. |
| E2 response structural grids | O §§2–4 | 2,250 incident energy rows match RMF/ARF with keV; 340 PI-ARF rows match EBOUNDS. Matrix finite/nonnegative. | VERIFIED, OBSERVED structure | Not a measured calibration accuracy or applicability check. |
| E2 PI/response channel rule | M §4.5.1; O §3.2.2; B11 | Native labels0–339, official RMF1–340, F_CHAN1; [probe](../scripts/probe_solexs_readiness.py) keeps mapping_validated=false. | BLOCKED_EXTERNAL_EVIDENCE | Approved mapping or compatible response, with reference output. |
| E2 gain/epoch/software validity | M §§2.4/4.5; P §§4.1/4.4; T16 index | RMF/ARF creator1.0, science creator1.1; no response gain/validity dates. Public index start2024-01-01 not compatibility proof. | BLOCKED_EXTERNAL_EVIDENCE | Mission release/detector/temperature/gain lineage and valid epoch. |
| E2 spectral energy/uncertainty | M §§4.5.2/4.5.4/4.5.5; P §4.4 | No applied response/energy mapping; no sample uncertainty estimate. | BLOCKED_EXTERNAL_EVIDENCE | Applicable range/background/statistical/systematic rules; dated guidance cannot become invented local errors. |
| E3 native missingness | M GTI intent | LC NaNs128/2; PI same all-NaN rows, zero partial-NaN rows; finite LC range3–1554/2–943. | VERIFIED, OBSERVED diagnostics | Preserve masks; do not assign random missingness or health causes. |
| E3 GTI/sample relation | M §2.1.1 | Inclusive points86272/86398 match finite masks/card strings; endpoint differences86268/86395. No filtering in loader. | VERIFIED numerical relation; continuous exposure BLOCKED_EXTERNAL_EVIDENCE | Approved continuous endpoint/bin/partial exposure arithmetic. |
| E3 effective exposure/correction | M §2.1.3; P §5.3; T13/T16 | PI EXPOSURE=TELAPSE=1s even on NaN rows; DTCORR absent. Same-basename parameters differ. | BLOCKED_EXTERNAL_EVIDENCE | Confirm applied/required corrections; no double correction or coefficient selection by name. |
| E3 matching HK | W; T13/T16 | No HK in either ZIP or inspected local Aditya tree. | BLOCKED_DATA if chosen approved workflow requires HK | Exact July acquisition/schema/mode/clock pairing and route UNKNOWN. |
| E3 operational quality/saturation | M §§2.1.1/4.5.5; P §5.2 | No quality/error columns, no finite-value numeric anomalies; no direct health-state evidence. | BLOCKED_EXTERNAL_EVIDENCE | Numerical cleanliness does not clear saturation/pile-up/pointing/background. |
| E4 detector role/selection | M §4.5.3; R; P §2 | SDD2 FILTER association OBSERVED; GTI detector names INFERRED; empty SDD1 GTIs. | PARTIALLY_VERIFIED | SDD2 inspection supported; SDD1 science BLOCKED_DATA, local absence cause UNKNOWN. |
| E4 LC/PI quantity equivalence | M LC band; T11 generation | `[41:313]` residual19/15 rows; `[41:314]` residual14/5; full sums equal0 rows; NUMBAND4 undefined. | BLOCKED_EXTERNAL_EVIDENCE | Require exact LC generation policy, no fitted band or automatic stream fusion. |
| E5 distinct response and band concepts | N/G; P §5.4 | Native counts/PI and GOES W/m2 identities remain separate in [foundation](../src/solar_flare_jepa/data/foundation.py). | VERIFIED distinction; gate PARTIALLY_VERIFIED | Nominal intersection is INFERRED, not response equivalence. |
| E5 numeric comparison/transfer | P §5.4; N clock/quality; G response | No local calibrated alignment/conversion. Published corrected comparison is outside sample acceptance. | BLOCKED_EXTERNAL_EVIDENCE | Resolve E1–E3, observer/1-AU convention, response tail and paired reference before target design. |
| E6 native inspection | M structure; existing bounded access | Eight products, four native plots; [exploration](../src/solar_flare_jepa/data/solexs_exploration.py) reports OBSERVED_NATIVE. | VERIFIED for diagnostics | Plots are EXPERIMENTAL_UNCALIBRATED; no physical timeline. |
| E6 sequence/forecast contract | E1–E5; [P1 causal contracts](../src/solar_flare_jepa/forecasting/contracts.py) | Training/conversions refused; no labels/target/causal availability or supported splits. | BLOCKED_EXTERNAL_EVIDENCE, then data/implementation dependencies | Mission contract first; bounded historical selection and independent chronological evaluation later. |

Gate-level outcomes: **E1/E2/E3/E6 BLOCKED_EXTERNAL_EVIDENCE; E4/E5
PARTIALLY_VERIFIED**. No gate is fully VERIFIED. A partial gate does not allow
any dependent physical analysis or training.

## Source conflicts and reconciliation

- The historical C reconnaissance says native loading was missing at that
  checkpoint; actual P2 has implemented loaders/tests. Its dated record is
  preserved rather than rewritten or used to justify reimplementation.
- The original Phase E checklist retains pre-D.1 unknown official-package
  equivalence. D.1 and this audit establish local byte identity; the additive
  `phase_e_validation` extension supersedes that fact only. Applicability remains
  blocked and all historical requirements retain their original meaning.
- R distinguishes 0.1s instrument temporal-channel capability from 1s spectral
  cadence; M's dated table lists1s. Delivered L1 LC rows are observed at one
  native unit and documented at1s, so no0.1s observations are manufactured.
- T16 deadtime.py's HISTORY mode/offset text at line80 reverses the actual
  `np.where` association at line61. This is observed external source ambiguity,
  not a repository defect to patch. Clarify approved mode semantics before use.
- M's timing example and T11 timezone-dependent headers conflict with explicit
  UTC projection. U records later header updates but gives no exact1.1 policy.
- P's duty-cycle/cross-calibration claims cannot prove these files' uninterrupted
  usable coverage, local uncertainty or calibration identity.

## Paperclip trace and citation checks

The repository skill was read, `paperclip skill` succeeded, and searches used
explicit `-s arxiv`. Exact `lookup arxiv 2509.26292`, metadata and original
`content.lines` were cross-checked with the versioned v2 PDF/HTML because the
Paperclip body version was not explicit. Discovery also returned early concept
and mission papers; they were not substituted for calibration evidence.

P original evidence: [energy/response](https://paperclip.gxl.ai/citations/papers/arx_2509.26292#L51-L110),
[deadtime](https://paperclip.gxl.ai/citations/papers/arx_2509.26292#L111-L146),
[cross-calibration](https://paperclip.gxl.ai/citations/papers/arx_2509.26292#L148-L157).
G exact DOI lookup and original lines137–143 were read, with metadata confirming
publication identity. No Paperclip map/reduce or generated summary was used to
support a claim. Research command traces are retained in ignored verification
records; primary locators remain usable from a fresh clone.
