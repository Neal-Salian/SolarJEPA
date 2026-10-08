"""Exclusive, reproducible native recorded-value experiment; no gate clearance."""
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import re
import shutil
import tempfile

import numpy as np

from solar_flare_jepa.data.download import sha256_file
from solar_flare_jepa.data.solexs import open_solexs_product, load_light_curve
from solar_flare_jepa.data.storage import load_inventory, repository_relative_path
from solar_flare_jepa.experiments.config import read_finite_json
from solar_flare_jepa.experiments.provenance import code_provenance, _destination, _rename_no_replace
from solar_flare_jepa.forecasting.contracts import canonical_json, fingerprint_payload
from .sequences import LABEL, UNIT, array_hash, sequence_from_native, make_windows, fit_normalization
from .baselines import fit_baselines, evaluate

CONFIG_KEYS={'schema_version','task_id','scientific_label','context_samples','horizon_samples',
             'stride_samples','train_stop_row','expected_rows','inventory_path','inventory_sha256',
             'phase_e_path','phase_e_sha256','sources','neural'}
GATES={'E1':'BLOCKED_EXTERNAL_EVIDENCE','E2':'BLOCKED_EXTERNAL_EVIDENCE',
       'E3':'BLOCKED_EXTERNAL_EVIDENCE','E4':'PARTIALLY_VERIFIED',
       'E5':'PARTIALLY_VERIFIED','E6':'BLOCKED_EXTERNAL_EVIDENCE'}


def validate_config(c):
    if (not isinstance(c,dict) or set(c)!=CONFIG_KEYS or c['schema_version']!=1
            or c['task_id']!='solexs-native-recorded-value-v1' or c['scientific_label']!=LABEL):
        raise ValueError('Only explicit provisional recorded-value configuration is accepted')
    for k,upper in [('context_samples',1024),('horizon_samples',256),('stride_samples',1024),
                    ('train_stop_row',999999),('expected_rows',1000000)]:
        if type(c[k]) is not int or not 1<=c[k]<=upper:
            raise ValueError('Invalid bounded numerical configuration')
    if (c['stride_samples']<c['horizon_samples'] or c['train_stop_row']>=c['expected_rows']
            or min(c['train_stop_row'],c['expected_rows']-c['train_stop_row'])<c['context_samples']+c['horizon_samples']):
        raise ValueError('Invalid split support or overlapping target blocks')
    for k in ('inventory_sha256','phase_e_sha256'):
        if not re.fullmatch('[0-9a-f]{64}',c[k]): raise ValueError('Full manifest hash required')
    if not isinstance(c['sources'],list) or len(c['sources'])!=2:
        raise ValueError('Exactly two separate pilot sources required')
    for s,date in zip(c['sources'],('2024-07-01','2024-07-03')):
        if (not isinstance(s,dict) or set(s)!={'path','bytes','sha256','member','fits_sha256','nominal_date'}
                or s['nominal_date']!=date or type(s['bytes']) is not int or s['bytes']<=0
                or any(not re.fullmatch('[0-9a-f]{64}',s[k]) for k in ('sha256','fits_sha256'))):
            raise ValueError('Invalid source selection identity')
    frozen=dict(context_samples=64,horizon_samples=8,stride_samples=8,
                train_stop_row=60480,expected_rows=86400)
    if any(c[k]!=v for k,v in frozen.items()):
        raise ValueError('Frozen v1 sample lengths/split changed; requires a new reviewed experiment')
    from .neural import _config, DEFAULT_CONFIG
    _config(c['neural'])
    if c['neural']!=DEFAULT_CONFIG:
        raise ValueError('Frozen v1 neural budget changed; requires a new reviewed experiment')
    return json.loads(canonical_json(c))


def load_config(path):
    return validate_config(read_finite_json(path))


def load_selected_sequence(data_root,record,selection):
    if (record['path']!=selection['path'] or record['sha256']!=selection['sha256']
            or record['bytes']!=selection['bytes']
            or record['nominal_observation_date']!=selection['nominal_date']):
        raise ValueError('Selected archive identity mismatch')
    with open_solexs_product(data_root,record,selection['member']) as p:
        if p.provenance['fits_sha256']!=selection['fits_sha256']:
            raise ValueError('Selected expanded FITS identity mismatch')
        if p.hdus[0].header.get('CREATOR')!='solexs_pipeline-1.1':
            raise ValueError('Different pipeline product requires a new task contract')
        sequence=sequence_from_native(load_light_curve(p))
    return sequence


def _write_json(path,value):
    with Path(path).open('x') as f:
        f.write(canonical_json(value)+'\n')


def verify_outputs(directory):
    directory=Path(directory)
    index=read_finite_json(directory/'artifacts.json')
    if (set(index)!={'schema_version','scientific_label','files'} or index['schema_version']!=1
            or index['scientific_label']!=LABEL): raise ValueError('Invalid provisional artifact index')
    expected=[]
    for item in index['files']:
        if set(item)!={'path','bytes','sha256'}: raise ValueError('Invalid artifact identity')
        name=repository_relative_path(item['path'],directory)
        p=directory/name
        if p.is_symlink() or not p.is_file() or p.stat().st_size!=item['bytes'] or sha256_file(p)!=item['sha256']:
            raise ValueError('Artifact identity mismatch')
        expected.append(str(name))
    actual=sorted(p.relative_to(directory).as_posix() for p in directory.rglob('*')
                  if p.is_file() and p.name!='artifacts.json')
    if len(set(expected))!=len(expected) or sorted(expected)!=actual:
        raise ValueError('Artifact file set differs')
    return index


def publish_stage(stage,destination):
    stage,destination=Path(stage).absolute(),Path(destination).absolute()
    if destination.exists() or destination.is_symlink(): raise FileExistsError(str(destination))
    if (destination.parent.name!='experiments' or destination.parent.parent.name!='results'
            or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*',destination.name)
            or any(p.is_symlink() for p in destination.parents)):
        raise ValueError('Output must be a new directory immediately under results/experiments')
    files=[]
    for p in sorted(stage.iterdir()):
        if not p.is_file() or p.is_symlink() or p.name=='artifacts.json':
            raise ValueError('Invalid stage artifact')
        files.append(dict(path=p.name,bytes=p.stat().st_size,sha256=sha256_file(p)))
    _write_json(stage/'artifacts.json',dict(schema_version=1,scientific_label=LABEL,files=files))
    verify_outputs(stage)
    _rename_no_replace(stage,destination)
    return verify_outputs(destination)


def run_experiment(config_path, *, project_root, data_root, output_dir):
    """Fit/choose on train/validation, freeze, THEN score the separate test source."""
    project_root,data_root=Path(project_root).resolve(),Path(data_root).resolve()
    config_path=Path(config_path).resolve()
    c=load_config(config_path)
    config_hash=sha256_file(config_path)
    destination=_destination(project_root,output_dir)
    code=code_provenance(project_root)
    manifest_paths={}
    for key in ('inventory','phase_e'):
        p=project_root/repository_relative_path(c[key+'_path'],project_root)
        if sha256_file(p)!=c[key+'_sha256']: raise ValueError('Frozen manifest hash differs')
        manifest_paths[key]=p
    phase_e=read_finite_json(manifest_paths['phase_e'])
    if {g['id']:g['status'] for g in phase_e['gates']}!=GATES:
        raise ValueError('Phase E gates changed; contract requires independent review')
    inventory=load_inventory(manifest_paths['inventory'])
    sequences=[]
    for selection in c['sources']:
        matches=[r for r in inventory['files'] if r['path']==selection['path']]
        if len(matches)!=1: raise ValueError('Ambiguous selected archive')
        sequence=load_selected_sequence(data_root,matches[0],selection)
        if len(sequence.values)!=c['expected_rows']: raise ValueError('Pilot row count changed')
        sequences.append(sequence)
    params=dict(context=c['context_samples'],horizon=c['horizon_samples'],stride=c['stride_samples'])
    split=c['train_stop_row'];rows=c['expected_rows']
    windows={'train':make_windows(sequences[0],0,split,**params),
             'validation':make_windows(sequences[0],split,rows,**params),
             'test':make_windows(sequences[1],0,rows,**params)}
    normalization=fit_normalization(sequences[0],0,split)
    identities=dict(task=fingerprint_payload(c),code=code['source']['fingerprint'],config=config_hash,
                    dataset=fingerprint_payload([s.fingerprint for s in sequences]),
                    split=fingerprint_payload({k:w.fingerprint for k,w in windows.items()}),
                    normalization=fingerprint_payload(normalization),scientific_label=LABEL)
    models=fit_baselines(windows['train'],normalization)
    validation=windows['validation'];train=windows['train']
    reference=models['persistence'].predict(validation.x,validation.x_mask)
    baseline_validation={}
    for name,model in models.items():
        p=model.predict(validation.x,validation.x_mask)
        if not np.array_equal(p,model.predict(validation.x,validation.x_mask)):
            raise ValueError('Baseline predictions are not deterministic')
        baseline_validation[name]=evaluate(validation.y,p,validation.y_mask,reference)
    if min(len(train.origins),len(validation.origins))<32:
        raise ValueError('Insufficient support for bounded neural experiment; stop after feasibility')
    from .neural import fit_neural,load_checkpoint
    model=fit_neural(train.x,train.y,train.x_mask,train.y_mask,validation.x,validation.y,
                     validation.x_mask,validation.y_mask,mean=normalization['mean'],
                     scale=normalization['scale'],identities=identities,config=c['neural'])
    destination.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='.solexs-stage-',dir=destination.parent))
    try:
        model.save_checkpoint(stage/'best.pt')
        loaded=load_checkpoint(stage/'best.pt',expected_identities=identities)
        # Check train/validation reproducibility before any designated test scoring.
        for w in (train,validation):
            if not np.array_equal(model.predict(w.x,w.x_mask),loaded.predict(w.x,w.x_mask)):
                raise ValueError('Checkpoint prediction mismatch')
        freeze=dict(scientific_label=LABEL,identities=identities,config=c,
                    selected_epoch=model.selected_epoch,history=model.history,
                    selection='earliest minimum validation masked normalized MSE',test_used_for_selection=False)
        _write_json(stage/'selection_frozen.json',freeze)
        scores={};arrays={'scientific_label':np.array(LABEL),'native_unit':np.array(UNIT)}
        prediction_hashes={}
        for partition,w in windows.items():
            scores[partition]={}
            ref=models['persistence'].predict(w.x,w.x_mask)
            all_models=dict(models,numerical_linear=loaded)
            arrays[partition+'_origins']=w.origins
            arrays[partition+'_targets']=w.y
            arrays[partition+'_target_mask']=w.y_mask
            prediction_hashes[partition]={}
            for name,fitted in all_models.items():
                predicted=fitted.predict(w.x,w.x_mask)
                scores[partition][name]=evaluate(w.y,predicted,w.y_mask,ref)
                arrays[partition+'_'+name]=predicted
                prediction_hashes[partition][name]=array_hash(predicted)
        np.savez_compressed(stage/'predictions.npz',**arrays)
        report=dict(schema_version=1,scientific_label=LABEL,task_id=c['task_id'],unit=UNIT,
                    stage_a='PASS_NUMERICAL_ONLY',stage_b='COMPLETED',stage_c='COMPLETED',
                    gates=GATES,configuration=c,identities=identities,code=code,
                    sources=[s.source for s in sequences],normalization=normalization,
                    splits={k:w.summary for k,w in windows.items()},
                    baseline_parameters={k:m.parameters for k,m in models.items()},
                    baseline_validation_reproducible=True,neural=dict(
                        kind='generic_masked_linear_not_JEPA',parameter_count=model.parameter_count,
                        selected_epoch=model.selected_epoch,history=model.history,config=c['neural'],
                        device='cpu',checkpoint_reload_equal=True,
                        checkpoint_sha256=sha256_file(stage/'best.pt')),
                    scores=scores,prediction_hashes=prediction_hashes,
                    software={name:version(name) for name in ('numpy','astropy','torch','pytest')},
                    warnings=['UNCALIBRATED_RECORDED_VALUES','COLUMN_UNITS_UNENCODED',
                              'UTC_EXPOSURE_QUALITY_AND_LC_GENERATION_UNKNOWN','TWO_DAY_ENGINEERING_HOLDOUT_ONLY',
                              'NO_UNCERTAINTY_INTERVALS_OR_FLARE_LABELS'],
                    physical_forecasting_clearance=False)
        _write_json(stage/'report.json',report)
        # Reverify source/configuration bytes at publication, including optional neural imports.
        final_code=code_provenance(project_root)
        if final_code['source']!=code['source'] or sha256_file(config_path)!=config_hash:
            raise ValueError('Code/configuration changed during execution')
        for key,p in manifest_paths.items():
            if sha256_file(p)!=c[key+'_sha256']: raise ValueError('Manifest changed during execution')
        for s in c['sources']:
            if sha256_file(data_root/s['path'])!=s['sha256']: raise ValueError('Archive changed during execution')
        publish_stage(stage,destination)
        return report
    finally:
        if stage.exists(): shutil.rmtree(stage)
