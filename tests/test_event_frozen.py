import hashlib
import json
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from solar_flare_jepa.events import frozen

MIN = 60_000_000_000
DAY = 1440*MIN
SHA = 'a'*64


def fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


@pytest.fixture
def bundle(tmp_path):
    issues = np.array([120,150,1560,1590],dtype=np.int64)*MIN
    ids = [f'origin:{t}' for t in issues]
    spec = dict(cadence_seconds=60,context_steps=120,horizon_steps=30,stride_steps=30,
                availability_mode='retrospective_bin_end',target_names=['xrsa_flux','xrsb_flux'],
                target_units=['W/m2','W/m2'],feature_names=['xrsa_flux','xrsb_flux'],
                feature_units=['W/m2','W/m2'])
    grid = dict(dataset_fingerprint=SHA,origin_ids=ids,issue_times_ns=issues.tolist(),spec=spec,
                starts_ns=(issues[:,None]+np.arange(30)*MIN).tolist(),
                ends_ns=(issues[:,None]+(np.arange(30)+1)*MIN).tolist())
    values = np.full((4,30,2),1e-6); values[[0,2],10,1]=2e-5
    context = dict(dataset_fingerprint=SHA,origin_ids=ids,issue_times_ns=issues.tolist(),spec=spec,
                   starts_ns=(issues[:,None]+np.arange(-120,0)*MIN).tolist(),
                   ends_ns=(issues[:,None]+np.arange(-119,1)*MIN).tolist(),
                   availability_ns=(issues[:,None]+np.arange(-119,1)*MIN).tolist(),
                   values=np.full((4,120,2),1e-6).tolist(), mask=np.ones((4,120,2),bool).tolist())
    events=[dict(event_id=f'e{i}',catalog_id='cat',catalog_sha256=SHA,source='GOES-16',
                 start_ns=int(issues[i]+10*MIN),peak_ns=int(issues[i]+20*MIN),end_ns=None,
                 flare_class='M2.0',peak_flux=2e-5,peak_saturated=False) for i in (0,2)]
    parts=dict(name='test',start_ns=0,end_ns=2*DAY)
    docs = dict(inputs=dict(input_fingerprint='b'*64,future_grid=grid,context=context,
                            candidate_issue_times_ns=(np.arange(120,1591,30)*MIN).tolist(),
                            retained_candidate_indices=[0,1,48,49],
                            targets=dict(values=values.tolist(),mask=np.ones_like(values,bool).tolist()),
                            preparation_summary=dict(partition=parts)),
                predictions=dict(persistence=dict(model_id='persistence',values=values.tolist())),
                protocol=dict(forecast=spec,exposure=dict(confirmatory_status='UNAVAILABLE'),
                              classical_models=['persistence'],checkpoint_cohort=[]),
                summary=dict(input_fingerprint='b'*64,external_dataset_fingerprint=SHA,fit_performed=False),
                events=events)
    docs['summary']['prediction_content_fingerprint']=fingerprint(docs['predictions'])
    docs['summary']['protocol_fingerprint']=fingerprint(docs['protocol'])
    provenance=[]
    for ident,t in zip(ids,issues):
        candidate=[e for e in events if t<=e['start_ns']<t+30*MIN]
        def support(a,b):
            return dict(start_ns=int(a),end_ns=int(b),observed_bins=int((b-a)//MIN),
                        invalid_xrsb_bins=0,before_dataset=False,after_dataset=False,missing_cadence=False)
        provenance.append(dict(origin_id=ident,issue_time_ns=int(t),horizon_end_ns=int(t+30*MIN),
            maturity_ns=int(t+30*MIN),reasons=[],horizon_support=support(t,t+30*MIN),
            event_support=[dict(catalog_id=e['catalog_id'],catalog_sha256=e['catalog_sha256'],
                                event_id=e['event_id'],**support(e['start_ns'],e['peak_ns']+MIN)) for e in candidate]))
    for letter in 'CMX':
        definition=frozen.native_label_definition(letter)
        docs['labels_'+letter] = dict(label_status='CANDIDATE_CATALOG_ONSET_LABELS',
            dataset_fingerprint=SHA,origin_ids=ids,issue_times_ns=issues.tolist(),
            catalog_identities=[dict(catalog_id='cat',catalog_sha256=SHA)],
            catalog_completeness='UNKNOWN',definition=definition,definition_id=fingerprint(definition),
            spec_fingerprint=fingerprint(spec),catalog_interval=[0,2*DAY],origin_provenance=provenance,
            outcomes=[letter!='X',False,letter!='X',False],valid_mask=[True]*4,mature_mask=[True]*4,
            maturity_ns=(issues+30*MIN).tolist())
    config = dict(schema_version=1,policy='xrsb_point_max_native_threshold_v1',
                  calibration='GOES_science_quality_W_m2_no_legacy_scaling',
                  minimum_lead_seconds=60,block_seconds=86400,replicates=20,seed=17,
                  partition=[0,2*DAY],resources={})
    def write(name,doc):
        path=tmp_path/(name+'.json'); path.write_text(json.dumps(doc))
        data=path.read_bytes()
        config['resources'][name]=dict(root='bundle',path=path.name,bytes=len(data),
                                       sha256=hashlib.sha256(data).hexdigest())
    for name,doc in docs.items(): write(name,doc)
    lineage=dict(protocol_fingerprint=fingerprint(docs['protocol']),
        preparation_artifacts=[{key:value for key,value in config['resources'][role].items() if key!='root'}
                               for role in ('events','labels_C','labels_M','labels_X')])
    docs['inputs']['input_identities']=lineage
    docs['summary']['input_identities']=json.loads(json.dumps(lineage))
    docs['inputs']['input_fingerprint']=fingerprint(lineage)
    docs['summary']['input_fingerprint']=fingerprint(lineage)
    write('inputs',docs['inputs']);write('summary',docs['summary'])
    return config,dict(bundle=tmp_path),docs,write


def test_pinned_bundle_reproduces_separate_onset_and_flux_scores(bundle):
    config,roots,_,_=bundle
    result=frozen.evaluate_frozen(config,roots)
    assert result['claim']=='exploratory_retrospective_candidate_alarms'
    assert result['fit_performed'] is False
    m=result['classes']['M']['models']['persistence']
    assert m['catalog_opportunities']['counts']['tp']==2
    assert m['event_matching']['counts']['hits']==2
    assert m['flux_exceedance']['counts']['tp']==2
    assert result['classes']['X']['positive_origins']==0


def test_changed_bytes_and_unsafe_paths_fail_before_scoring(bundle):
    config,roots,_,_=bundle
    p=roots['bundle']/'predictions.json'; p.write_bytes(p.read_bytes()+b' ')
    with pytest.raises(ValueError,match='identity'): frozen.evaluate_frozen(config,roots)
    config['resources']['predictions']['path']='../outside.json'
    with pytest.raises(ValueError,match='path'): frozen.evaluate_frozen(config,roots)


@pytest.mark.parametrize('defect',['order','grid','units','maturity','truth','class','mask','fingerprint','available',
                                  'quality','definition_id','spec_id','support','catalog_interval','stride',
                                  'prediction_order','cohort','protocol','missing_peak_flux','missing_lineage'])
def test_semantic_mismatch_rejected_even_when_rehashed(bundle,defect):
    config,roots,docs,write=bundle
    name='labels_M'
    if defect=='order': docs[name]['origin_ids']=list(reversed(docs[name]['origin_ids']))
    if defect=='maturity': docs[name]['maturity_ns'][0]=3*DAY
    if defect=='truth': docs[name]['outcomes'][0]=False
    if defect=='class': docs[name]['definition']['minimum_class']='C1.0'
    if defect=='mask': docs[name]['valid_mask'][0]=1
    if defect=='fingerprint': docs[name]['dataset_fingerprint']='f'*64
    if defect=='quality':
        docs[name]['definition']['quality_policy']='ignore_gaps'
        docs[name]['definition_id']=fingerprint(docs[name]['definition'])
    if defect=='definition_id': docs[name]['definition_id']='f'*64
    if defect=='spec_id': docs[name]['spec_fingerprint']='f'*64
    if defect=='support': docs[name]['origin_provenance'][0]['event_support'][0]['invalid_xrsb_bins']=1
    if defect=='catalog_interval': docs[name]['catalog_interval']=[0,10*MIN]
    if defect=='prediction_order':
        name='predictions';docs[name]['persistence']['values'].reverse()
    if defect in ('protocol','cohort'):
        name='protocol'
        if defect=='protocol': docs[name]['exposure']['confirmatory_status']='changed'
        else:
            docs[name]['classical_models'].append('missing-model')
            docs['summary']['protocol_fingerprint']=fingerprint(docs[name])
            write('summary',docs['summary'])
    if defect=='missing_peak_flux': name='events';docs[name][0]['peak_flux']=None
    if defect=='missing_lineage': name='inputs';docs[name].pop('input_identities')
    if defect in ('grid','units','available','stride'):
        name='inputs'
        if defect=='grid': docs[name]['future_grid']['starts_ns'][0][0]+=MIN
        if defect=='units': docs[name]['future_grid']['spec']['target_units'][1]='counts'
        if defect=='available': docs[name]['context']['availability_ns'][0][-1]+=MIN
        if defect=='stride': docs[name]['future_grid']['issue_times_ns'][1]-=15*MIN
    write(name,docs[name])
    if name.startswith('labels_') or name=='events':
        lineage=docs['inputs']['input_identities']
        for row in lineage['preparation_artifacts']:
            if row['path']==config['resources'][name]['path']:
                row.update({k:config['resources'][name][k] for k in ('bytes','sha256')})
        docs['summary']['input_identities']=json.loads(json.dumps(lineage))
        docs['inputs']['input_fingerprint']=fingerprint(lineage)
        docs['summary']['input_fingerprint']=fingerprint(lineage)
        write('inputs',docs['inputs']);write('summary',docs['summary'])
    with pytest.raises(ValueError): frozen.evaluate_frozen(config,roots)


def test_threshold_proxy_reports_bin_interval_and_rejects_invalid_forecast():
    values=np.array([[1e-6,1e-5,2e-5],[1e-6,1e-6,1e-6]])
    result=frozen.threshold_alarms(values,np.array([0,DAY]),minimum_class='M1.0')
    assert result['positive']==[True,False]
    assert result['first_crossing_start_ns']==[MIN,None]
    assert result['first_crossing_end_ns']==[2*MIN,None]
    with pytest.raises(ValueError): frozen.threshold_alarms(values*float('nan'),[0,DAY])
    with pytest.raises(ValueError): frozen.threshold_alarms([[True,1e-6]],[0])


def test_json_duplicate_keys_are_rejected(tmp_path):
    p=tmp_path/'bad.json';p.write_text('{"a":1,"a":2}')
    with pytest.raises(ValueError,match='Duplicate'): frozen.read_json(p)


def test_advance_opportunities_respect_declared_lead_and_report_catalog_strata(bundle):
    config,roots,_,_=bundle
    config['minimum_lead_seconds']=900
    result=frozen.evaluate_frozen(config,roots)
    m=result['classes']['M']
    assert m['short_lead_origins']==2
    assert m['models']['persistence']['advance_opportunities']['counts']['excluded']==2
    assert m['models']['persistence']['catalog_strata']['unresolved_prior_end']['origins']>=1


def test_excluded_candidate_positions_are_preserved_in_block_resampling(bundle):
    config,roots,docs,write=bundle
    result=frozen.evaluate_frozen(config,roots)
    assert result['candidate_count']==50
    assert result['excluded_origin_count']==46
    assert result['classes']['M']['models']['persistence']['uncertainty']['observed']['counts']['total']==50


def test_cli_writes_real_report_and_refuses_overwrite(bundle,monkeypatch):
    config,roots,_,_=bundle
    task_root=roots['bundle']
    for identity in config['resources'].values(): identity['root']='forecasts'
    config_path=task_root/'config.json';config_path.write_text(json.dumps(config))
    script=Path(__file__).resolve().parents[1]/'scripts/evaluate_flare_events.py'
    spec=importlib.util.spec_from_file_location('event_cli',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    monkeypatch.setattr(module,'__file__',str(task_root/'scripts/evaluate_flare_events.py'))
    output=task_root/'results/report.json'
    args=['--config',str(config_path),'--forecast-root',str(task_root),'--label-root',str(task_root),'--output',str(output)]
    module.main(args)
    data=output.read_bytes()
    assert json.loads(data)['model_count']==1
    with pytest.raises(SystemExit) as failure: module.main(args)
    assert failure.value.code==2 and output.read_bytes()==data
