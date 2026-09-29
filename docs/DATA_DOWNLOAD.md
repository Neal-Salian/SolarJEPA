# Data acquisition

Checked 2026-09-29. Do not commit raw files or login credentials.

## Aditya-L1: registered manual route

1. Open [ISSDC Aditya](https://www.issdc.gov.in/adityal1.html), then Data Download,
   or [PRADAN](https://pradan.issdc.gov.in/al1/). The official alternate is
   [pradan1](https://pradan1.issdc.gov.in/al1/).
2. Select **Access Data**. The observed link is
   `https://pradan.issdc.gov.in/al1/protected/payload.xhtml`. It redirects to
   ISSDC's identity provider and offers **Register** and **Sign In**. Register
   personally, complete the portal's verification, and review current terms.
   Never paste passwords, session cookies or signed download URLs into Git.
3. Open **Other Downloads** (`/al1/protected/miscDownloads.xhtml`) for the
   Aditya-L1 handbook, payload product definitions and analysis instructions.
   This link was observed but its authenticated contents have not been read.
   Save manuals and response/calibration products locally under
   `data/raw/aditya/documentation/` and `data/raw/aditya/calibration/`.
4. In the authenticated payload selector, choose SoLEXS and inspect available
   levels, dates, processing versions and displayed sizes. Prefer documented
   calibrated higher-level products; obtain matching lower-level data and
   response files if calibration reproduction requires them. Do not assume
   Level 1 counts are physical flux. The exact post-login control labels and
   current per-payload holdings are **not verified**.
5. Choose one modest continuous interval first, ideally a day with a quiet
   segment and a catalogued flare, plus adjacent context if the archive bundles
   permit. Start with July 1–3, 2024 **only if available**, matching the NOAA
   engineering sample. Otherwise choose an available date and fetch matching
   NOAA data explicitly. Record the selection reason; do not use this selected
   sample as the unbiased final evaluation set.
6. Inspect ASPEX-STEPS and ASPEX-SWIS separately for exactly overlapping dates.
   Prefer Level 2. Keep detector directions, energy edges, uncertainty and
   quality information. Exclude STEPS SR/SP in nominal orientation unless new
   official correction guidance explicitly restores validity.
7. Review displayed download volume; target ≤25 MiB per sample initially, or
   the smallest official bundle if larger. Download using the portal's own
   file/bulk controls. Do not automate undocumented authenticated endpoints.
   Compare selected and received filenames: the FAQ documents ZIP volume limits.
8. Place untouched products in:

   ```text
   data/raw/aditya/solexs/<level>/<version>/
   data/raw/aditya/aspex_steps/<level>/<version>/
   data/raw/aditya/aspex_swis/<level>/<version>/
   ```

9. Inspect files: `python scripts/inspect_data.py <files> --output results/aditya_schema.json`.
   FITS and CDF support is metadata-only until real product mappings are
   reviewed. Install optional dependencies with `pip install -e '.[aditya]'`.
10. Record filename, SHA-256, byte size, product ID, source page, download UTC,
    processing/calibration version, level, native time scale, units, quality
    rules and terms in `data/manifests/aditya_inventory.json`. Exclude tokens
    and personally identifying account details. Ask the POC if epoch, counts,
    dead-time correction or response semantics are unclear; do not infer them.

The public [FAQ](https://pradan1.issdc.gov.in/al1/faq.xhtml) and
[release announcement](https://www.isro.gov.in/Second_Set_of_Aditya_L1_Science_Data.html)
support this route. No public unauthenticated sample or documented download API
was verified. A registered archive is accessible in principle, not validated
programmatically here. The [acknowledgment](https://pradan.issdc.gov.in/al1/ack.xhtml)
and [disclaimer](https://pradan.issdc.gov.in/al1/disclaimer.xhtml) must accompany
the final data-use review; repository MIT licensing does not relicense data.

## NOAA: public, bounded reference sample

Use [NCEI GOES-R EXIS](https://www.ncei.noaa.gov/products/goes-r-extreme-ultraviolet-xray-irradiance),
science-quality XRS L2 1-minute averages and flare summaries. The sample selects
GOES-16, July 1–3 2024, version 2-2-1: three daily flux files and three daily
summary files. It is a parsing/EDA sample, not a training corpus, and its dates
were chosen as a short contiguous interval, not after inspecting model skill.

```bash
python scripts/download_data.py --manifest configs/data/noaa_sample.json
```

The checked official daily directory is:
`https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/xrsf-l2-avg1m_science/2024/07/`.
Replace `xrsf-l2-avg1m_science` with `xrsf-l2-flsum_science` for matching summaries.
Daily filenames and version are explicit in the manifest; no `latest` aliases.
The script refuses more than 16 MiB across the manifest and 4 MiB per file,
validates NetCDF signatures, and writes local retrieval provenance. Expected
checksums in the committed manifest detect subsequent archive revisions.

Read [L2 ReadMe](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_ReadMe.pdf)
and [User Guide](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/docs/GOES-R_XRS_L2_Data_Users_Guide.pdf).
Version 2-2-1 adds short-gap interpolation and changes calibration/event
processing: preserve flags and versions. Science-quality retrospective data
supports a retrospective study; it does not establish operational latency.

## Before expanding acquisition

Validate timestamp convention, science variables/units, flags, native cadence,
missingness, checksums, calibration compatibility and extracted series on the
small sample. Then enumerate all eligible periods and estimated total bytes.
Approve expansion and freeze a split manifest before accessing held-out outcomes.
An archive update creates a new dataset version, never an unnoticed replacement.
