# SolarJEPA final time-series presentation

The 21-slide, 16:9 deck (20 original slides plus a V2 pilot research update, slide 21) uses a dark navy theme, orange/cyan channel colors,
nine actual scientific figures, two actual Streamlit captures, seven editable
tables, and explanatory speaker notes with pinned source references on every slide.

- `SolarJEPA_Final_Time_Series_Presentation.pptx`: editable slide text/tables and
  embedded scientific figures. Open the Notes pane for explanations and sources.
- `SolarJEPA_Final_Time_Series_Presentation.pdf`: **STALE 20-page facsimile that predates slide 21** (see "Slide 21" below); a 20-page facsimile using the
  inspected 2560×1440 slide images at 192 dpi. Text in this PDF is flattened.
  The PPTX remains the editable master.
- `slide_evidence.json`: compact verified values, without scientific arrays.
- `assets/chart_manifest.json`: chart inputs, source identities, display policies
  and output hashes. Ten scientific assets are generated; nine appear in the deck.
- `assets/dashboard_capture_metadata.json`: actual browser capture actions,
  source commit, timestamps, scope, dimensions and screenshot hashes. Two of four
  capture assets appear in the deck.
- `verification.json`: final package, values and embedded-asset identity checks.

## Scientific source and limits

The analysis source is commit
`abe4b79d2fe7549552b0a1f467be1cd949b652a7` on
`presentation/time-series-requirements-completion`. The presentation branch starts
from verified `main` and references that analysis commit without integrating or
modifying its scientific implementation. Source references in the speaker notes
point to that exact commit.

Fresh read-only checks loaded the strict evidence identities, revalidated all
123 native files, replayed all 30×2 forecast values, and reproduced the requested
metrics. EDA, STL and ADF/KPSS were also regenerated in memory and matched the
saved evidence. No classical or neural refit and no new full regression-suite run
are claimed for this artifact milestone. Historical test results remain in the
analysis branch's verification report.

The archive contains 177,120 minute bins from May through August 2024, with
channel-specific quality exclusions and no imputation. Local diagnostics use
10,149 complete June minutes. Candidate fitting uses the first 2,880 of those
minutes. Model order selection uses training BIC separately within compatible
channel/differencing/trend/burn groups. The selected orders are ARIMA(1,1,0) for
XRS-A and ARIMA(2,1,0) for XRS-B.

The displayed errors describe one retrospective 30-minute example issued at
2024-08-01 02:00 UTC. They do not estimate overall forecast skill. Target quality
masks determine eligibility of that complete-case scored window, while future
target values do not enter fitting, order selection or inference. Forecasts
represent inverse-log conditional medians, without uncertainty intervals.

STL imposes a 1,440-minute diagnostic period. Stable seasonality remains
unestablished, and no SARIMA fit or score exists. The final slide maps all eleven
requirements and discloses that requirement 8 remains partial under a literal
requirement to fit every listed family. Operational solar-flare forecasting is
unestablished. The original dashboard's interactive observations cover May–June,
distinct from the full May–August evidence used elsewhere in the deck.

## Rebuild

Layout rebuilding uses the committed chart/capture PNGs and compact evidence, so
it does not require scientific data. The authoring runtime is the Codex bundled
Node.js environment with `@oai/artifact-tool` 2.8.93, plus bundled Python packages
ReportLab, Pillow and pypdf. Discover local runtime paths with Codex's
`load_workspace_dependencies` tool. Configure these environment variables:

```text
RUNTIME_NODE_MODULES=<bundled Node.js node_modules directory>
RUNTIME_PYTHON=<bundled Python executable>
PRESENTATIONS_SKILL_DIR=<installed presentations skill directory>
```

Run from this checkout, using the bundled Node executable:

```bash
node scripts/presentation/build_deck.mjs <new-revision-name>
python scripts/presentation/verify_deck.py --report presentations/verification.json
```

Each revision gets a new ignored `.cache/presentation-build/` subdirectory.
The builder validates a private candidate before copying the final PPTX to its
requested name. It exports the PDF through ReportLab because this host's direct
Artifact Tool PDF exporter lacks `#standard-fonts/Helvetica`. Bundled dependencies
were not altered. Intermediate renders and validation receipts remain ignored.

To regenerate scientific figures, restore the exact manifest-selected native
files and ignored diagnostics payload in an analysis checkout at the pinned
commit, with its normally installed package and documented environment:

```bash
<analysis-python> scripts/presentation/build_charts.py --source-root <analysis-checkout>
<analysis-python> scripts/presentation/export_slide_evidence.py \
  --source-root <analysis-checkout> --output presentations/slide_evidence.json
```

The scientific builder verifies source identities, native data, contiguous
support, and forecast replay before plotting. It preserves gaps and documents
display thinning. No synthetic observations or graphs are used. Raw data and
scientific arrays remain outside Git.

For fresh actual UI captures, run the source checkout's Streamlit application,
set `SOURCE_ROOT` to that checkout, configure `BROWSER_EXECUTABLE` if necessary,
and run `node scripts/presentation/capture_dashboard.mjs`. The script uses real
navigation and the saved-inference action without modifying app styling or data.
Screenshots are historical evidence of the capture-time app state. The captures
used in this deck were taken on 12 October 2026 UTC.

## Final verification

Final artifact review completed on 13 October 2026 in Asia/Kolkata:

- PPTX package integrity, dimensions, font policy, seven native tables, heading
  fit and geometry checks passed with zero findings and zero layout warnings.
- All twenty final PPTX slides were imported and rendered again. Independent
  reviewers inspected each final PPTX slide and each Poppler-rendered PDF page.
- Twenty explanatory notes, the exact selected orders, requested AIC/BIC and
  MAE/RMSE values, embedded chart/capture hashes, and final coverage wording pass
  the reusable verification script.
- All twenty PDF pages have 960×540-point dimensions and contain the exact
  inspected 2560×1440 slide images. Review PNGs were rasterized at 96 dpi for
  inspection; the embedded PDF source images remain 192 dpi.
- Scientific review corrected a provenance caption typo and clarified native
  log-axis units and ARIMA level forecasts before finalization.
- Native PowerPoint execution was not performed. This verification covers the
  file package, scientific evidence, Artifact Tool renders and PDF appearance.

Git safety: only this new presentation branch is committed and pushed. Existing
branches, original untracked files, raw products and research worktrees remain
preserved. No PR, merge, force-push, branch deletion or push to `main` is part of
this task.

## Slide 21: V2 pilot research update (20 October 2026)

Slide 21 was added after the original build by `scripts/presentation/add_v2_update_slide.py`. It reads only
`docs/evidence/phase2_v2_m4_pilot_results_20261019.json` (pilot evidence commit `76dc0fa`), asserts the values it
shows, and relabels slides 1–20 as `NN / 21` (slides 1–20 are otherwise byte-identical, as are notes and media).
It reports the completed 20/20-job V2 development pilot descriptively: fine-tuned JEPA did not beat the matched
supervised controls, a frozen JEPA encoder beat a frozen random encoder, with two seeds and one previously used
10-day validation window. It makes no significance or generalization claim.

**Not verified:** after the final edit, slide 21 was checked by package validation, text/geometry checks and an
earlier render of a first layout, but not by a final rendered image, because PowerPoint/Keynote automation timed out
on the review host. The committed PDF is still the 20-page version. Open the PPTX, look at slide 21, and export a
fresh PDF before presenting from the PDF. `build_deck.mjs` still generates only the original 20 slides.
