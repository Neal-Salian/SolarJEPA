"""Add slide 21 (V2 pilot research update) to the committed 20-slide deck.

Reads the 20-slide deck from git (`presentations/` at --base-ref), adds one slide whose numbers come only from
`docs/evidence/phase2_v2_m4_pilot_results_20261019.json`, relabels pages "NN / 21" and writes the PPTX.
Needs the PPTX skill's `add_slide.py` (set PPTX_SKILL_SCRIPTS to its scripts directory) and `lxml`-free Python only.

    PPTX_SKILL_SCRIPTS=<dir> python scripts/presentation/add_v2_update_slide.py --base-ref a41c3dd --out presentations/SolarJEPA_Final_Time_Series_Presentation.pptx
"""
import argparse, hashlib, json, os, re, shutil, subprocess, sys, zipfile
from pathlib import Path
from xml.sax.saxutils import escape
ap = argparse.ArgumentParser(); ap.add_argument('--base-ref', default='a41c3dd'); ap.add_argument('--out', required=True, type=Path); args = ap.parse_args()
K = Path(os.environ['PPTX_SKILL_SCRIPTS'])
REPO = Path(__file__).resolve().parents[2]; EV = REPO / 'docs/evidence/phase2_v2_m4_pilot_results_20261019.json'
ev = json.loads(EV.read_text()); ev_sha = hashlib.sha256(EV.read_bytes()).hexdigest()
assert ev['status'] == 'COMPLETE' and ev['jobs_succeeded'] == 20 and ev['inference_status'] == 'INFERENCE_UNAVAILABLE'
W = REPO / '.cache/slide21-build'; shutil.rmtree(W, ignore_errors=True)
BASE = 'presentations/SolarJEPA_Final_Time_Series_Presentation.pptx'
ORIG = REPO / '.cache/slide21-base.pptx'; ORIG.parent.mkdir(parents=True, exist_ok=True)
ORIG.write_bytes(subprocess.run(['git', 'show', f'{args.base_ref}:{BASE}'], cwd=REPO, capture_output=True, check=True).stdout)
zipfile.ZipFile(ORIG).extractall(W)
out = subprocess.run([sys.executable, str(K / 'add_slide.py'), str(W), 'slide16.xml'], capture_output=True, text=True, check=True).stdout
assert 'slide21.xml' in out, out
pres = W / 'ppt/presentation.xml'; px = pres.read_text(encoding='utf-8-sig')
R = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
new_ids = re.findall(r'<p:sldId id="\d+" r:id="[^"]+"/>', px); assert len(new_ids) == 1, new_ids
pres.write_text(px.replace(new_ids[0], new_ids[0][:-2] + f' xmlns:r="{R}" />'), encoding='utf-8')
per = ev['validation_mean_dex_pinball_per_seed']; comp = ev['comparisons']
rows = [('Fine-tuned JEPA', 'primary:jepa_finetune'), ('Supervised', 'primary:supervised'),
        ('Supervised + extra updates', 'primary:supervised_extra_updates'), ('TCN', 'primary:tcn'),
        ('Frozen JEPA encoder', 'primary:jepa_frozen'), ('Random frozen encoder', 'primary:random_frozen')]
fmt = lambda v: f'{v:.5f}'
signed = lambda t: t.replace(' -', ' \u2212')  # typographic minus, as elsewhere in the deck
# Two-seed means from the report's exact comparison means, not from rounded per-seed values.
means = {'primary:jepa_finetune': comp['primary:jepa_finetune-supervised']['mean_a'],
         'primary:supervised': comp['primary:jepa_finetune-supervised']['mean_b'],
         'primary:supervised_extra_updates': comp['primary:jepa_finetune-supervised_extra_updates']['mean_b'],
         'primary:tcn': comp['primary:jepa_finetune-tcn']['mean_b'],
         'primary:jepa_frozen': comp['primary:jepa_frozen-random_frozen']['mean_a'],
         'primary:random_frozen': comp['primary:jepa_frozen-random_frozen']['mean_b']}
for k, m in means.items():
    assert abs(m - sum(per[k]) / 2) < 1e-5, k   # consistent with per-seed values to rounding
table = [['Model', 'Mean dex pinball', 'Seed 1261866429', 'Seed 1291916211']] + \
        [[label, fmt(means[k]), fmt(per[k][0]), fmt(per[k][1])] for label, k in rows]
js = comp['primary:jepa_finetune-supervised']['mean_difference']; fr = comp['primary:jepa_frozen-random_frozen']['mean_difference']
jb = comp['primary:jepa_finetune-supervised_extra_updates']['mean_difference']
assert js > 0 and jb > 0 and fr < 0
p = W / 'ppt/slides/slide21.xml'; s = p.read_text(encoding='utf-8-sig')
def put(old, new, count=1):
    global s
    assert s.count(old) == count, (old, s.count(old)); s = s.replace(old, new)
put('<a:t>Forecast demonstration results</a:t>', '<a:t>Research update: V2 controlled pilot</a:t>')
put('<a:t>One retrospective held-out 30-minute example</a:t>', '<a:t>19 Oct 2026 · 20/20 jobs · two seeds · one previously used 10-day validation window</a:t>')
put('<a:t>16 / 20</a:t>', '<a:t>21 / 21</a:t>')
put('<a:t>MAE = (1/n) Σ |eₜ|</a:t>', '<a:t>' + escape(signed(f'Fine-tuned JEPA vs supervised: {js:+.4f} dex')) + '</a:t>')
put('<a:t>RMSE = √[(1/n) Σ eₜ²]</a:t>', '<a:t>' + escape(signed(f'Frozen JEPA vs random frozen: {fr:+.3f} dex')) + '</a:t>')
put('<a:t>n = 30 target minutes per channel.  Errors use log₁₀ irradiance.</a:t>',
    '<a:t>Fine-tuned JEPA did not beat supervised; frozen JEPA beat random frozen.</a:t>')
put('<a:t>These values do not represent overall forecasting skill</a:t>',
    '<a:t>Post-selection validation; descriptive only, no significance claim</a:t>')
# Rebuild the table: keep header styling from row 1, data styling from row 2, 7 rows of reduced height.
i0, i1 = s.index('<a:tbl>'), s.index('</a:tbl>') + len('</a:tbl>'); tbl = s[i0:i1]
trs = re.findall(r'<a:tr h="\d+">.*?</a:tr>', tbl, re.S); assert len(trs) == 3
def row_xml(template, values, height):
    cells = re.findall(r'<a:tc>.*?</a:tc>', template, re.S); assert len(cells) == 4
    new = []
    for cell, value in zip(cells, values):
        cell = re.sub(r'<a:t>[^<]*</a:t>', '<a:t>' + escape(value) + '</a:t>', cell, count=1)
        cell = re.sub(r'(<a:r>.*?</a:r>)(<a:r>.*?</a:r>)+', r'\1', cell, flags=re.S)  # one run per cell
        cell = cell.replace('sz="2175"', 'sz="1500"').replace('sz="2325"', 'sz="1500"').replace('sz="1875"', 'sz="1500"')
        cell = re.sub(r'(lIns|tIns|rIns|bIns|marL|marR|marT|marB)="114300"', r'\1="57150"', cell)
        new.append(cell)
    return f'<a:tr h="{height}">' + ''.join(new) + '</a:tr>'
H = 400050
body = row_xml(trs[0], table[0], H) + ''.join(row_xml(trs[1], r, H) for r in table[1:])
tbl_new = tbl[:tbl.index(trs[0])] + body + tbl[tbl.index(trs[-1]) + len(trs[-1]):]
tbl_new = tbl_new.replace('<a:gridCol w="2286000" /><a:gridCol w="2952750" /><a:gridCol w="2924175" /><a:gridCol w="2924175" />',
    '<a:gridCol w="3200400" /><a:gridCol w="2581275" /><a:gridCol w="2652713" /><a:gridCol w="2652712" />')
assert '3200400' in tbl_new
s = s[:i0] + tbl_new + s[i1:]
# Resize table frame and move the callout/caption shapes below it.
s = re.sub(r'(<p:graphicFrame>.*?<a:off x="552450" y="1800225" />\s*<a:ext cx="\d+" cy=")\d+', lambda m: m.group(1) + str(H * 7), s, count=1, flags=re.S)
for name, y in (('text-112', 4743450), ('text-113', 4743450), ('text-114', 5295900), ('text-115', 5810250)):
    s = re.sub(r'(name="' + name + r'".*?<a:off x="\d+" y=")\d+', lambda m: m.group(1) + str(y), s, count=1, flags=re.S)
s = s.replace('sz="2325"', 'sz="1875"')  # callouts: match the deck's 18.75 pt caption size so both fit on one line
p.write_text(s, encoding='utf-8')
# Notes slide 21 cloned from notes 16 with new text and registration.
nsrc = (W / 'ppt/notesSlides/notesSlide16.xml').read_text(encoding='utf-8-sig')
A = 'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main"'
notes = [
 'OBSERVED: research update after the classical analysis. On 19 October 2026 the guarded V2 development pilot completed all 20 planned jobs '
 f'(two shared JEPA pretraining runs and 18 selected models) with zero retries, in {ev["total_wall_seconds"]:.0f} s of a {ev["budget_seconds"]} s budget, '
 'on an Apple M4 (16 GiB, macOS 27.0.1, Python 3.13.7) under the ratified Protocol v1. Owner approval was recorded for this changed host.',
 'The table shows validation mean dex pinball after checkpoint selection, averaged over 412 complete validation origins, 30 one-minute leads and both channels, for the two '
 'seeds 1261866429 and 1291916211. Lower is better. Fine-tuned JEPA did not beat the matched supervised control '
 f'({js:+.5f} dex on average; per-seed signs differ) nor the step-matched extra-updates control ({jb:+.5f} dex, worse in both seeds). '
 f'A frozen JEPA encoder beat a frozen random encoder ({fr:+.5f} dex, both seeds), so the pretrained representation carries information.',
 'Limits: May–July 2024 data are exposed development data; validation is a single previously used 10-day window that also selected checkpoints, so values are optimistic. '
 'Two seeds cannot estimate variability. No interval, p-value, significance or generalization claim is made (inference unavailable: M3.1 found no validated replacement). '
 'Differences below 0.001 dex are about 1–2% of the loss and comparable to seed-to-seed variation.',
 f'Sources: docs/evidence/phase2_v2_m4_pilot_results_20261019.json (SHA-256 {ev_sha}) and docs/PHASE2_V2_M4_PILOT_RESULTS_20261019.md at pilot evidence commit '
 '76dc0fa348fc2e129d41c057195fbb7e121ea05d on codex/v2-m4-host-preparation; execution from codex/v2-experimental-validation-readiness at 1c5b699.',
]
paras = ''.join(f'<a:p {A}><a:r><a:t>{escape(t)}</a:t></a:r></a:p><a:p {A} />' for t in notes)
i = nsrc.index('<a:lstStyle'); j = nsrc.index('/>', i) + 2; k = nsrc.index('</p:txBody>', j)
(W / 'ppt/notesSlides/notesSlide21.xml').write_text(nsrc[:j] + paras + nsrc[k:], encoding='utf-8')
nrel = (W / 'ppt/notesSlides/_rels/notesSlide16.xml.rels').read_text(encoding='utf-8-sig').replace('/ppt/slides/slide16.xml', '/ppt/slides/slide21.xml')
(W / 'ppt/notesSlides/_rels/notesSlide21.xml.rels').write_text(nrel, encoding='utf-8')
srel = W / 'ppt/slides/_rels/slide21.xml.rels'; r = srel.read_text(encoding='utf-8-sig')
assert 'notesSlide' not in r
srel.write_text(r.replace('</Relationships>', '<Relationship Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide" '
    'Target="/ppt/notesSlides/notesSlide21.xml" Id="RnotesV2pilot21" /></Relationships>'), encoding='utf-8')
ct = W / '[Content_Types].xml'; c = ct.read_text(encoding='utf-8-sig')
c = c.replace('</Types>', '<Override PartName="/ppt/notesSlides/notesSlide21.xml" '
    'ContentType="application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml" /></Types>')
ct.write_text(c, encoding='utf-8')
# Page labels on slides 1-20.
for n in range(1, 21):
    f = W / f'ppt/slides/slide{n}.xml'; t = f.read_text(encoding='utf-8-sig')
    assert t.count(f'<a:t>{n:02d} / 20</a:t>') == 1, n
    f.write_text(t.replace(f'<a:t>{n:02d} / 20</a:t>', f'<a:t>{n:02d} / 21</a:t>'), encoding='utf-8')
out = args.out; out.parent.mkdir(parents=True, exist_ok=True)
orig_order = [i.filename for i in zipfile.ZipFile(ORIG).infolist() if not i.filename.endswith('/')]
members = [f for f in orig_order if (W / f).is_file()] + sorted(
    str(f.relative_to(W)) for f in W.rglob('*') if f.is_file() and str(f.relative_to(W)) not in set(orig_order))
assert members[0] == '[Content_Types].xml' or '[Content_Types].xml' in members
members.sort(key=lambda n: n != '[Content_Types].xml')   # content types first, otherwise original order
with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
    for name in members: z.write(W / name, name)
print('built', out, out.stat().st_size, 'evidence sha', ev_sha[:12]); print(table)
