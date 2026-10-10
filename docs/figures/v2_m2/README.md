# M2 coverage figure provenance

`bootstrap_coverage.png` plots aggregate synthetic case statistics from
`docs/evidence/v2_m2_synthetic_summary.json`, generated with Matplotlib 3.11.2.
The points are unconditional coverage over 300 simulated datasets, including
unavailable intervals as uncovered. Bars are Wilson 95% **Monte Carlo** intervals,
not the forecast comparison's bootstrap interval. The dashed line is nominal .95.
No raw observation or per-origin synthetic array is embedded in this figure.
The PNG was visually inspected for labels, clipping and agreement with the table.

Recreate from repository root (the aggregate evidence already contains all values):

```python
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows = json.loads(Path('docs/evidence/v2_m2_synthetic_summary.json').read_text())['cases']
fig, ax = plt.subplots(figsize=(10, 10))
for i, row in enumerate(rows):
    p = row['coverage']['rate']
    low, high = row['coverage']['wilson95']
    color = '#187b75' if row['available_intervals']['rate'] == 1 else '#a64b35'
    ax.errorbar(p, i, xerr=[[p-low], [high-p]], fmt='o', color=color, capsize=3)
ax.set_yticks(range(len(rows)), [r['scenario']['name']+' (block '+str(r['block_days'])+')' for r in rows])
ax.invert_yaxis()
ax.axvline(.95, color='#666666', linestyle='--', label='Nominal 95%')
ax.set_xlim(-.02, 1.04)
ax.set_xlabel('Coverage over all 300 datasets; bars: Wilson 95% Monte Carlo intervals')
ax.set_title('M1 crossed bootstrap: controlled synthetic reliability\nUnavailable intervals count as uncovered; no nominal-coverage certification')
ax.grid(axis='x', alpha=.2)
ax.legend(loc='lower right')
fig.tight_layout()
fig.savefig('docs/figures/v2_m2/bootstrap_coverage.png', dpi=160)
```
