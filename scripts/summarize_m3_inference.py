#!/usr/bin/env python3
"""Verify immutable M3 runs and export aggregate evidence and a coverage figure."""
import argparse
import io
import json
import math
from importlib.metadata import version
from pathlib import Path

from solar_flare_jepa.experiments.provenance import verify_artifacts
from solar_flare_jepa.forecasting.contracts import fingerprint_payload


def write_once(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():
        if path.read_bytes()!=data: raise FileExistsError('Refusing to overwrite different evidence: '+str(path))
        return
    with path.open('xb') as stream: stream.write(data)


def load_run(root, relative):
    directory=root/relative
    directory.resolve().relative_to(root.resolve())
    verify_artifacts(directory)
    science=json.loads((directory/'scientific.json').read_text())
    metadata=json.loads((directory/'metadata.json').read_text())
    if fingerprint_payload(science)!=metadata['scientific_payload_sha256']: raise ValueError('Scientific hash mismatch')
    provenance=metadata['provenance']
    info=dict(artifact=str(directory.relative_to(root)),scientific_payload_sha256=metadata['scientific_payload_sha256'],
              config_fingerprint=metadata['config_fingerprint'],git_commit=provenance['git_commit'],
              source_fingerprint=provenance['source']['fingerprint'],python=provenance['python'],platform=provenance['platform'],
              packages=provenance['packages'],dependencies=metadata['dependencies'],started_utc=metadata['started_utc'],
              peak_rss_raw=metadata['peak_rss_raw'],peak_rss_unit=metadata['peak_rss_unit'],
              tolerances=metadata['tolerances'],performance=json.loads((directory/'performance.json').read_text()))
    return science,info


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    for name in ('evaluation','repeat','development','pilot'):parser.add_argument('--'+name,required=True)
    args=parser.parse_args();root=args.root.resolve();runs={}
    if (root/args.evaluation).resolve()==(root/args.repeat).resolve():
        raise ValueError('A deterministic repeat requires distinct executions')
    for name in ('evaluation','repeat','development','pilot'):runs[name]=load_run(root,getattr(args,name))
    final,metadata=runs['evaluation'];repeat,other=runs['repeat']
    if metadata['started_utc']==other['started_utc']:
        raise ValueError('A deterministic repeat requires distinct execution identities')
    if final!=repeat or metadata['git_commit']!=other['git_commit'] or metadata['source_fingerprint']!=other['source_fingerprint']:
        raise ValueError('Final scientific payload/source did not repeat')
    frozen=json.loads((root/'configs/validation/m3_evaluation.json').read_text())
    if final['config']!=frozen or final['stage']!='evaluation':raise ValueError('Final configuration differs from frozen evaluation')
    diagnostics={}
    for row in final['cases']:
        cfg=row['case']['scenario'];rho=cfg['rho'];seed_count=cfg['seeds'];correlation=cfg['seed_correlation']
        ess=[n*n/(n+2*math.fsum((n-k)*rho**k for k in range(1,n))) for n in cfg['days']]
        diagnostics[cfg['name']]=dict(ar1_unit_marginal_mean_effective_days=ess if rho else None,
            equicorrelated_seed_component_effective_runs=seed_count/(1+(seed_count-1)*correlation))
    summary=dict(schema_version=1,synthetic_only=True,scientific=final,figure_matplotlib_version=version('matplotlib'),
        verified_runs={name:info for name,(_,info) in runs.items()},deterministic_repeat=True,
        analytic_design_diagnostics=diagnostics,
        diagnostic_scope='Known-DGP component ESS, not estimated solar effective sample sizes or whole-estimator ESS')
    write_once(root/'docs/evidence/v2_m3_inference_summary.json',(json.dumps(summary,sort_keys=True,indent=2,allow_nan=False)+'\n').encode())
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,3,figsize=(14,8),sharey=True)
    groups=[('Joint target',['m1_joint']),('Fixed calendar: seed target',['seed_t']),
            ('Fixed seeds: calendar target',['hac_l3','hac_l7','stationary_l3','stationary_l7'])]
    colors=['#0072B2','#D55E00','#009E73','#CC79A7']
    for ax,(title,methods) in zip(axes,groups):
        for j,label in enumerate(methods):
            offset=(j-(len(methods)-1)/2)*.16
            for i,case in enumerate(final['cases']):
                row=case['methods'][label];y=i+offset
                if row['availability']['rate']==0:continue
                rate=row['coverage']['rate'];lo,hi=row['coverage']['wilson95']
                ax.errorbar(rate,y,xerr=[[rate-lo],[hi-rate]],fmt='o',markersize=3,color=colors[j],linewidth=.9)
            ax.plot([],[],color=colors[j],marker='o',label=label)
        ax.axvline(.95,color='.4',linestyle='--',linewidth=1)
        ax.set(xlim=(0,1.02),title=title,xlabel='True-target coverage (Wilson 95% bars)')
        ax.grid(axis='x',alpha=.2);ax.legend(loc='lower left',fontsize=8)
    axes[0].set_yticks(range(len(final['cases'])),[x['case']['scenario']['name'].removeprefix('eval_') for x in final['cases']])
    axes[0].invert_yaxis()
    fig.suptitle('M3 frozen synthetic evaluation: distinct estimands, R=400, B=399',fontsize=13)
    fig.text(.5,.01,'Blank points indicate unavailable inference. Dashed line: 95%. Different targets are not interchangeable.',ha='center',fontsize=9)
    fig.tight_layout(rect=(0,.035,1,.96));buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=180);plt.close(fig)
    write_once(root/'docs/figures/v2_m3/coverage.png',buffer.getvalue())
    print('Verified repeat and exported summary/coverage figure')


if __name__=='__main__':main()
