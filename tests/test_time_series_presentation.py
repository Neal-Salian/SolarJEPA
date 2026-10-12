"""Scientific presentation evidence: masks, distribution diagnostics and reconstruction."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def module():
    from solar_flare_jepa.presentation import time_series
    return time_series


def frame(n=400):
    index = pd.date_range('2024-06-01', periods=n, freq='min', tz='UTC')
    x = np.arange(n)
    return pd.DataFrame(dict(xrsa_flux=10. ** (-7 + .1*np.sin(2*np.pi*x/20)),
        xrsb_flux=10. ** (-6 + .2*np.sin(2*np.pi*x/20)),
        xrsa_valid=True, xrsb_valid=True, observed=True), index=index)


def test_eda_uses_joint_masks_and_distinguishes_absent_rejected():
    data = frame()
    data.loc[data.index[0], 'observed'] = False
    data.loc[data.index[1], 'xrsa_valid'] = False
    data.loc[data.index[2], 'xrsb_valid'] = False
    result = module().eda_diagnostics(data)
    assert result['scatter']['total_pairs'] == len(data)-3
    a = next(r for r in result['statistics'] if r['channel']=='xrsa' and r['transform']=='raw')
    b = next(r for r in result['statistics'] if r['channel']=='xrsb' and r['transform']=='log10')
    assert (a['count'],a['absent_bins'],a['rejected_present_bins']) == (398,1,1)
    assert b['count'] == 398
    np.testing.assert_allclose(a['std'],data.xrsa_flux.iloc[2:].std(ddof=1))
    assert a['units']=='W/m2' and b['units']=='log10(F / (1 W/m2))'
    assert len(result['qq']['xrsa']['observed'])<=301
    assert result['qq']['xrsa']['rows']==398


def test_qq_has_normal_reference_and_preserves_ordered_empirical_support():
    result=module().eda_diagnostics(frame())
    for channel in ('xrsa','xrsb'):
        qq=result['qq'][channel]
        assert np.all(np.diff(qq['theoretical'])>0)
        assert np.all(np.diff(qq['observed'])>=0)
        assert qq['slope']>0 and np.isfinite(qq['intercept'])


def test_stl_components_reconstruct_log_flux_without_changing_timestamps():
    data=frame()
    result=module().seasonal_diagnostic(data,period_minutes=20)
    assert result['period_minutes']==20 and result['rows']==len(data)
    assert result['reconstruction_max_error']<1e-12
    assert result['display']['time_utc'][0]==data.index[0].isoformat()
    for channel in ('xrsa','xrsb'):
        x=result['display'][channel]
        np.testing.assert_allclose(np.array(x['trend'])+x['seasonal']+x['residual'],x['observed'],atol=1e-12)


@pytest.mark.parametrize('mutation',['gap','duplicate','mask','nonpositive','naive'])
def test_stl_refuses_invalid_or_masked_segments(mutation):
    data=frame()
    if mutation=='gap': data=data.drop(data.index[10])
    elif mutation=='duplicate': data.index=pd.DatetimeIndex([data.index[0],*data.index[:-1]])
    elif mutation=='mask': data.loc[data.index[10],'xrsa_valid']=False
    elif mutation=='nonpositive': data.loc[data.index[10],'xrsa_flux']=0
    elif mutation=='naive': data.index=data.index.tz_localize(None)
    with pytest.raises(ValueError): module().seasonal_diagnostic(data,period_minutes=20)


def test_loader_refuses_absent_or_mutated_identity_bundle(tmp_path):
    with pytest.raises(ValueError): module().load_evidence(tmp_path)
    # Production bundle also validates every recorded code/input identity.
    root=Path(__file__).resolve().parents[1]
    if not (root/'docs/presentation/time_series_evidence.json').exists():
        return
    loaded=module().load_evidence(root)
    assert loaded['dataset']['source_files']==123
    assert loaded['dataset']['rows']==177120


@pytest.mark.parametrize('mutation',['report','payload','source','dependency_set'])
def test_evidence_loader_rejects_tampered_report_payload_or_code(tmp_path, monkeypatch, mutation):
    import json
    from solar_flare_jepa.data.download import sha256_file
    m=module()
    monkeypatch.setattr(m,'SOURCES',('source.py',))
    payload=dict(schema_version=1,dataset={'purpose':'synthetic loader test'})
    m._write(tmp_path/m.PAYLOAD,payload)
    report=dict(dataset=payload['dataset'],payload=dict(path=m.PAYLOAD,sha256=sha256_file(tmp_path/m.PAYLOAD)))
    m._write(tmp_path/m.REPORT,report)
    (tmp_path/'source.py').write_text('test source')
    identity=dict(schema_version=1,report=dict(path=m.REPORT,sha256=sha256_file(tmp_path/m.REPORT)),
                  sources=[dict(path='source.py',sha256=sha256_file(tmp_path/'source.py'))])
    m._write(tmp_path/m.IDENTITY,identity)
    assert m.load_evidence(tmp_path)==payload
    if mutation=='dependency_set':
        identity['sources']=[]
        m._write(tmp_path/m.IDENTITY,identity)
    else:
        selected={'report':m.REPORT,'payload':m.PAYLOAD,'source':'source.py'}[mutation]
        with (tmp_path/selected).open('a') as stream: stream.write(' ')
    with pytest.raises(ValueError,match='evidence unavailable'):
        m.load_evidence(tmp_path)


def test_diagnostics_accept_equivalent_utc_microsecond_index():
    data=frame()
    data.index=data.index.as_unit('us')
    assert module().eda_diagnostics(data)['scatter']['total_pairs']==len(data)
    assert module().seasonal_diagnostic(data,period_minutes=20)['rows']==len(data)


def test_diagnostics_refuse_non_utc_offset_in_utc_fields():
    data=frame()
    data.index=data.index.tz_convert('Asia/Kolkata')
    with pytest.raises(ValueError,match='UTC'):
        module().eda_diagnostics(data)
    with pytest.raises(ValueError,match='UTC'):
        module().seasonal_diagnostic(data,period_minutes=20)
