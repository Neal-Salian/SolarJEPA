"""Read-only, byte-pinned adaptation of previously published frozen forecasts.

No model inference, training, calibration or test-based policy selection. This
adapter deliberately consumes the external-validation native half-open labels.
Its max-flux alarm is exploratory; it does not reproduce NOAA event detection.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

from .labels import CALIBRATION, CatalogEvent, MINUTE_NS, class_threshold, digest, integer, times
from .matching import match_events
from .scoring import binary_scores, block_intervals


POLICY = 'xrsb_point_max_native_threshold_v1'


def _fingerprint(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),
                                    allow_nan=False,ensure_ascii=False).encode()).hexdigest()


def native_label_definition(letter):
    """The full preserved external-validation definition, not a new label rule."""
    return dict(version=1,event_quantity='cataloged_flare_start_occurrence',
        occurrence_interval='issue_inclusive_horizon_end_exclusive',minimum_class=letter+'1.0',
        minimum_peak_irradiance_W_m2=class_threshold(letter+'1.0'),
        classification='retrospective_catalog_peak_class',
        classification_maturity='max_horizon_end_and_all_candidate_onset_peak_bin_ends',
        alignment_policy='native_UTC_catalog_times_known_state_bins_no_snapping_v1',
        timestamp_precision_seconds=60,physical_timing_uncertainty='UNKNOWN',
        quality_policy='complete_xrsb_horizon_and_all_candidate_starts_through_peak_bins',
        source_policy='GOES-16_only_no_cross_spacecraft_substitution',
        saturation_policy='any_saturated_onset_invalid_even_if_reported_below_threshold',
        catalog_interval_meaning='selection_coverage_not_detection_completeness',
        catalog_completeness='UNKNOWN',physical_event_absence='UNKNOWN',
        operational_availability='UNKNOWN',predictor_label_separation='labels_returned_separately')


def _pairs(items):
    result = {}
    for key,value in items:
        if key in result:
            raise ValueError('Duplicate JSON key')
        result[key] = value
    return result


def _decode(data):
    def invalid(value):
        raise ValueError(f'Nonfinite JSON constant: {value}')
    return json.loads(data,object_pairs_hook=_pairs,parse_constant=invalid)


def read_json(path):
    return _decode(Path(path).read_bytes())


def _boolean(value,shape,name):
    a = np.asarray(value)
    if a.dtype.kind!='b' or a.shape!=shape:
        raise ValueError(f'{name} must be an explicit boolean array of shape {shape}')
    return a


def _has_boolean(value):
    if isinstance(value,(bool,np.bool_)):
        return True
    if isinstance(value,(list,tuple)):
        return any(_has_boolean(part) for part in value)
    return False


def _numeric(value,shape,name):
    a = np.asarray(value)
    if _has_boolean(value) or a.dtype.kind not in 'fiu' or a.shape!=shape or not np.isfinite(a).all() or (a<=0).any():
        raise ValueError(f'{name} must be finite positive W/m2 of shape {shape}')
    return a.astype(float)


def _coordinates(value,expected,name):
    a = np.asarray(value)
    if _has_boolean(value) or a.dtype.kind not in 'iu' or a.shape!=expected.shape or not np.array_equal(a,expected):
        raise ValueError(f'{name} coordinate mismatch')
    return a


def threshold_alarms(xrsb, issues_ns, *, minimum_class='M1.0'):
    """Threshold each entire native point trajectory; report interval, not onset."""
    issues = times(issues_ns,'issues_ns')
    values = np.asarray(xrsb)
    if values.ndim!=2 or values.shape[0]!=len(issues) or values.shape[1]<1:
        raise ValueError('Forecast requires [origin, native minute] XRS-B array')
    values = _numeric(xrsb,values.shape,'xrsb')
    crossed = values>=class_threshold(minimum_class)
    positive = crossed.any(axis=1)
    first = crossed.argmax(axis=1)
    starts = [integer(int(t)+int(j)*MINUTE_NS,'crossing start') if yes else None
              for t,j,yes in zip(issues,first,positive)]
    ends = [integer(t+MINUTE_NS,'crossing end') if t is not None else None for t in starts]
    return dict(positive=positive.tolist(),first_crossing_start_ns=starts,
                first_crossing_end_ns=ends,
                first_crossing_completion_lead_seconds=[(b-int(t))/10**9 if b is not None else None for t,b in zip(issues,ends)],
                quantity='predicted_native_bin_threshold_exceedance',
                caveat='Bin interval and completion lead are not catalog or physical onset.')


def _load(config,roots):
    documents,identities = {},{}
    required = {'inputs','predictions','protocol','summary','events','labels_C','labels_M','labels_X'}
    if set(config['resources'])!=required:
        raise ValueError('Expected explicit frozen inputs, predictions, protocol, summary, events and C/M/X labels')
    # Read and verify every byte before any scientific interpretation.
    for role,identity in config['resources'].items():
        root = Path(roots[identity['root']]).resolve()
        relative = Path(identity['path'])
        path = (root/relative).resolve()
        if relative.is_absolute() or '..' in relative.parts or not path.is_relative_to(root):
            raise ValueError('Unsafe artifact path')
        data = path.read_bytes()
        if len(data)!=integer(identity['bytes'],'bytes',0) or hashlib.sha256(data).hexdigest()!=digest(identity['sha256']):
            raise ValueError(f'Artifact identity mismatch: {role}')
        documents[role] = _decode(data)
        identities[role] = dict(identity)
    return documents,identities


def evaluate_frozen(config,roots):
    """Bind frozen forecast coordinates, label semantics and catalog identities.

    Roots locate immutable historical artifacts; portable config pins all bytes.
    Inputs are trusted research artifacts after identity/semantic validation,
    not an authenticity attestation or independent raw-data reconstruction.
    """
    if config.get('schema_version')!=1 or config.get('policy')!=POLICY or config.get('calibration')!=CALIBRATION:
        raise ValueError('Unsupported frozen decision policy')
    lead = integer(config['minimum_lead_seconds'],'minimum_lead_seconds',1)
    if lead<60 or lead>=1800 or lead%60:
        raise ValueError('Advance matching requires at least one native minute lead')
    ps,pe = (integer(v,'partition') for v in config['partition'])
    if pe<=ps:
        raise ValueError('Invalid chronological partition')
    docs,identities = _load(config,roots)
    inputs,protocol,summary = (docs[k] for k in ('inputs','protocol','summary'))
    if summary['fit_performed'] is not False or summary['input_fingerprint']!=inputs['input_fingerprint']:
        raise ValueError('Frozen source provenance mismatch')
    if summary['protocol_fingerprint']!=_fingerprint(protocol):
        raise ValueError('Historical protocol fingerprint mismatch')
    input_lineage=inputs.get('input_identities')
    if (not isinstance(input_lineage,dict) or input_lineage!=summary.get('input_identities')
            or _fingerprint(input_lineage)!=inputs['input_fingerprint']
            or input_lineage.get('protocol_fingerprint')!=summary['protocol_fingerprint']
            or not isinstance(input_lineage.get('preparation_artifacts'),list)):
        raise ValueError('Historical input lineage/fingerprint mismatch')
    historical=input_lineage['preparation_artifacts']
    declared = {row['path']:row for row in historical}
    for role in ('events','labels_C','labels_M','labels_X'):
        current=identities[role]
        previous=declared.get(current['path'])
        if previous is None or any(previous[k]!=current[k] for k in ('bytes','sha256')):
            raise ValueError('Label preparation lineage mismatch')
    grid = inputs['future_grid']; spec = grid['spec']; context=inputs['context']
    if spec!=protocol['forecast'] or spec!=context['spec']:
        raise ValueError('Forecast specification mismatch')
    for name,value in [('cadence_seconds',60),('context_steps',120),('horizon_steps',30),('stride_steps',30),
                       ('availability_mode','retrospective_bin_end'),('target_names',['xrsa_flux','xrsb_flux']),
                       ('target_units',['W/m2','W/m2']),('feature_names',['xrsa_flux','xrsb_flux']),
                       ('feature_units',['W/m2','W/m2'])]:
        if spec.get(name)!=value:
            raise ValueError(f'Unsupported native forecast {name}')
    dataset_id = digest(grid['dataset_fingerprint'])
    if dataset_id!=context['dataset_fingerprint'] or dataset_id!=summary['external_dataset_fingerprint']:
        raise ValueError('Dataset fingerprint mismatch')
    issues = times(grid['issue_times_ns'],'issue_times_ns'); n=len(issues)
    if not n or np.any(issues%MINUTE_NS) or np.any(np.diff(issues)<=0):
        raise ValueError('Issues require unique chronological native minute coordinates')
    gaps=[int(b)-int(a) for a,b in zip(issues,issues[1:])]
    if any(gap<30*MINUTE_NS or gap%(30*MINUTE_NS) for gap in gaps):
        raise ValueError('Frozen exposure requires nonoverlapping stride-aligned issue intervals')
    candidates=times(inputs['candidate_issue_times_ns'],'candidate issue times')
    positions=times(inputs['retained_candidate_indices'],'retained candidate indices')
    if (positions.shape!=(n,) or np.any(positions<0) or np.any(positions>=len(candidates))
            or np.any(np.diff(positions)<=0) or not np.array_equal(candidates[positions],issues)
            or np.any(candidates%MINUTE_NS) or any(int(b)-int(a)!=30*MINUTE_NS for a,b in zip(candidates,candidates[1:]))):
        raise ValueError('Candidate/retained origin mapping mismatch')
    # Candidate positions excluded by historical QC stay explicitly unscored,
    # including entire empty calendar blocks if any.
    def full_axis(values):
        full=np.zeros(len(candidates),bool);full[positions]=values
        return full
    ids = grid['origin_ids']
    if len(ids)!=n or len(set(ids))!=n or any(not isinstance(x,str) or not x for x in ids):
        raise ValueError('Invalid origin IDs')
    if context['origin_ids']!=ids:
        raise ValueError('Context origin order mismatch')
    _coordinates(context['issue_times_ns'],issues,'context issue')
    starts=issues[:,None]+np.arange(30)*MINUTE_NS; ends=starts+MINUTE_NS
    _coordinates(grid['starts_ns'],starts,'future start'); _coordinates(grid['ends_ns'],ends,'future end')
    cstarts=issues[:,None]+np.arange(-120,0)*MINUTE_NS; cends=cstarts+MINUTE_NS
    _coordinates(context['starts_ns'],cstarts,'context start'); _coordinates(context['ends_ns'],cends,'context end')
    # Unknown actual availability stays unknown; bin-end availability is a
    # retrospective assumption, never substituted for historical delivery times.
    availability = context.get('availability_ns')
    if availability is not None:
        avail=np.asarray(availability)
        if _has_boolean(availability) or avail.dtype.kind not in 'iu' or avail.shape!=cends.shape or (avail<cends).any() or (avail>issues[:,None]).any():
            raise ValueError('Feature availability violates issue chronology')
    if (cstarts[:,0]<ps).any() or (ends[:,-1]>pe).any():
        raise ValueError('Forecast support crosses partition')
    truth_flux=_numeric(inputs['targets']['values'],(n,30,2),'truth')
    truth_mask=_boolean(inputs['targets']['mask'],(n,30,2),'target mask')
    context_values=_numeric(context['values'],(n,120,2),'context')
    context_mask=_boolean(context['mask'],(n,120,2),'context mask')
    if not truth_mask.all() or not context_mask.all():
        raise ValueError('This frozen adapter requires historical complete retained support')
    events=[]
    for row in docs['events']:
        fields={key:row[key] for key in CatalogEvent.__dataclass_fields__ if key!='calibration'}
        fields['calibration']=config['calibration']
        events.append(CatalogEvent(**fields))
    keys=[(e.catalog_id,e.event_id) for e in events]
    if len(keys)!=len(set(keys)):
        raise ValueError('Duplicate aligned catalog identity')
    if any(e.start_ns is None or e.peak_ns is None or e.flare_class is None or e.peak_flux is None for e in events):
        raise ValueError('Aligned catalog events must retain complete onset and peak')
    known_evolution=np.array([any(e.start_ns<t and t<=(e.end_ns if e.end_ns is not None else e.peak_ns)
                                  for e in events) for t in issues])
    unknown_end=np.array([any(e.start_ns<t and e.end_ns is None and e.peak_ns<t
                              for e in events) for t in issues])
    strata=dict(known_catalog_evolution=known_evolution,unresolved_prior_end=unknown_end,
                no_known_catalog_evolution=~known_evolution)
    predictions=docs['predictions']
    if not isinstance(predictions,dict) or not predictions:
        raise ValueError('No frozen model predictions')
    cohort=protocol['classical_models']+[item['model'] for item in protocol['checkpoint_cohort']]
    if len(cohort)!=len(set(cohort)) or set(predictions)!=set(cohort):
        raise ValueError('Frozen model cohort mismatch; selection is prohibited')
    if summary['prediction_content_fingerprint']!=_fingerprint(predictions):
        raise ValueError('Historical prediction content fingerprint mismatch')
    model_values={}
    for name,pred in predictions.items():
        if pred['model_id']!=name:
            raise ValueError('Model identity mismatch')
        model_values[name]=_numeric(pred['values'],(n,30,2),'forecast')[:,:,1]
    report=dict(schema_version=1,claim='exploratory_retrospective_candidate_alarms',
        policy=POLICY,policy_fingerprint=hashlib.sha256(json.dumps(config,sort_keys=True,
            separators=(',',':'),allow_nan=False).encode()).hexdigest(),
        fit_performed=False,inference_performed=False,event_probabilities='UNAVAILABLE',
        confirmatory_status='UNAVAILABLE',operational_readiness='NOT_ESTABLISHED',
        catalog_completeness='UNKNOWN',source_identities=identities,
        origin_count=n,partition=[ps,pe],availability='retrospective_bin_end_assumption_actual_delivery_UNKNOWN',
        candidate_count=len(candidates),excluded_origin_count=len(candidates)-n,
        model_count=len(model_values),
        classes={},limitations=[
            'Prior August/January inspection: results are exploratory, with no policy or model selection.',
            'Complete future two-channel QC conditions the evaluated population.',
            'Catalog absence is not established physical absence; detection completeness is UNKNOWN.',
            'Native reprocessed input causality and actual delivery timestamps are UNKNOWN.',
            'Marginal flux quantiles do not identify joint horizon-event probabilities.',
            'Calendar-block intervals are descriptive sampling uncertainty, not predictive calibration.',
            'No debounce: each positive issuance is an alarm; unmatched repeats are false alarms.',
            'One-month/satellite support and scarce X events cannot establish generalization.'])
    for letter in 'CMX':
        label=docs['labels_'+letter]; threshold=class_threshold(letter+'1.0')
        definition=label['definition']
        if (label['label_status']!='CANDIDATE_CATALOG_ONSET_LABELS'
                or definition!=native_label_definition(letter)
                or label['definition_id']!=_fingerprint(definition)
                or label['spec_fingerprint']!=_fingerprint(spec)
                or label['dataset_fingerprint']!=dataset_id or label['origin_ids']!=ids):
            raise ValueError('Label definition, fingerprint or origin order mismatch')
        _coordinates(label['issue_times_ns'],issues,'label issue')
        truth=_boolean(label['outcomes'],(n,),'label outcomes')
        valid=_boolean(label['valid_mask'],(n,),'label validity')
        mature=_boolean(label['mature_mask'],(n,),'label maturity mask')
        maturity=times(label['maturity_ns'],'label maturity')
        if maturity.shape!=(n,) or (valid & (~mature | (maturity>pe) | (maturity<ends[:,-1]))).any():
            raise ValueError('Label maturity violates chronological partition')
        catalog_ids={(row['catalog_id'],row.get('catalog_sha256',row.get('sha256'))) for row in label['catalog_identities']}
        if any((e.catalog_id,e.catalog_sha256) not in catalog_ids for e in events):
            raise ValueError('Label/catalog identity mismatch')
        qualified=[e for e in events if class_threshold(e.flare_class)>=threshold]
        rebuilt=np.array([any(t<=e.start_ns<end for e in qualified) for t,end in zip(issues,ends[:,-1])])
        if not np.array_equal(truth,rebuilt):
            raise ValueError('Label truth contradicts aligned catalog')
        for i,(t,end) in enumerate(zip(issues,ends[:,-1])):
            candidate=[e for e in events if t<=e.start_ns<end]
            required=max([int(end)]+[e.peak_ns+MINUTE_NS for e in candidate])
            if valid[i] and (maturity[i]<required or any(e.peak_saturated or e.source!='GOES-16' for e in candidate)):
                raise ValueError('Unsupported or prematurely matured catalog label')
            cs,ce=label['catalog_interval']
            if valid[i] and (t<cs or end>ce or any(e.start_ns<max(ps,cs) or e.peak_ns+MINUTE_NS>min(pe,ce) for e in candidate)):
                raise ValueError('Catalog classification support crosses selection/partition')
            provenance=label['origin_provenance'][i]
            if (provenance['origin_id']!=ids[i] or provenance['issue_time_ns']!=t
                    or provenance['horizon_end_ns']!=end or provenance['maturity_ns']!=maturity[i]):
                raise ValueError('Label support provenance coordinate mismatch')
            if valid[i]:
                support=provenance['horizon_support']
                if (provenance['reasons'] or support['start_ns']!=t or support['end_ns']!=end
                        or support['observed_bins']!=30 or support['invalid_xrsb_bins']!=0
                        or any(support[k] for k in ('before_dataset','after_dataset','missing_cadence'))):
                    raise ValueError('Valid label contradicts horizon support diagnostics')
                supports={(row['catalog_id'],row['event_id']):row for row in provenance['event_support']}
                if set(supports)!={(e.catalog_id,e.event_id) for e in candidate}:
                    raise ValueError('Candidate event support provenance mismatch')
                for e in candidate:
                    support=supports[e.catalog_id,e.event_id]
                    if (support['catalog_sha256']!=e.catalog_sha256 or support['start_ns']!=e.start_ns
                            or support['end_ns']!=e.peak_ns+MINUTE_NS or support['invalid_xrsb_bins']!=0
                            or support['observed_bins']!=(e.peak_ns-e.start_ns)//MINUTE_NS+1
                            or any(support[k] for k in ('before_dataset','after_dataset','missing_cadence'))):
                        raise ValueError('Valid label contradicts event support diagnostics')
        zero=np.array([any(e.start_ns==t for e in qualified) for t in issues])
        early=np.array([any(t<=e.start_ns<t+lead*10**9 for e in qualified) for t in issues])
        advance_valid=valid & mature & ~early
        flux_truth=(truth_flux[:,:,1]>=threshold).any(axis=1)
        # Count nominally forecastable events on eligible support, not every
        # catalog event in a month with large QC exclusions.
        eligible=[e for e in qualified if any(ok and t+lead*10**9<=e.start_ns<end
                    for ok,t,end in zip(advance_valid,issues,ends[:,-1]))]
        event_rows=[dict(event_id=e.catalog_id+':'+e.event_id,start_ns=e.start_ns) for e in eligible]
        models={}
        for name,values in model_values.items():
            alarm=threshold_alarms(values,issues,minimum_class=letter+'1.0')
            predicted=np.asarray(alarm['positive'],bool)
            alarms=[dict(alarm_id=ids[i],issue_ns=int(t),window_end_ns=int(end))
                    for i,(t,end) in enumerate(zip(issues,ends[:,-1])) if advance_valid[i] and predicted[i]]
            matching=match_events(alarms,event_rows,decision_policy_id=POLICY+':'+letter,
                                  minimum_lead_seconds=lead)
            duplicate=sum(any(a['issue_ns']+lead*10**9<=e['start_ns']<a['window_end_ns'] for e in event_rows)
                          for a in alarms)-matching['counts']['hits']
            exposed_days=float(advance_valid.sum()*(1800-lead)/86400)
            models[name]=dict(catalog_opportunities=binary_scores(truth,predicted,valid & mature),
                advance_opportunities=binary_scores(truth,predicted,advance_valid),
                flux_exceedance=binary_scores(flux_truth,predicted),
                uncertainty=block_intervals(candidates,full_axis(truth),full_axis(predicted),full_axis(advance_valid),
                    block_seconds=config['block_seconds'],replicates=config['replicates'],seed=config['seed']),
                event_matching=matching,duplicate_eligible_alarms=duplicate,
                catalog_strata={key:dict(origins=int(selected.sum()),
                    scores=binary_scores(truth,predicted,valid & mature & selected))
                    for key,selected in strata.items()},
                false_alarms_per_exposed_day=(matching['counts']['false_alarms']/exposed_days if exposed_days else None),
                warning_time_fraction=(float(predicted[advance_valid].mean()) if advance_valid.any() else None),
                last_context_above_threshold=int((context_values[:,-1,1]>=threshold).sum()),
                first_crossing=alarm)
        report['classes'][letter]=dict(threshold_W_m2=threshold,positive_origins=int(truth[valid&mature].sum()),
            zero_lead_origins=int(zero.sum()),valid_origins=int((valid&mature).sum()),
            short_lead_origins=int(early.sum()),
            advance_valid_origins=int(advance_valid.sum()),qualified_catalog_events=len(qualified),
            eligible_events=len(eligible),events_outside_evaluated_exposure=len(qualified)-len(eligible),
            exposed_days=float(advance_valid.sum()*(1800-lead)/86400),
            exposure_definition='Union of nonoverlapping eligible [issue+minimum_lead,horizon_end) intervals',
            issued_horizon_days=float(advance_valid.sum()*1800/86400),
            label_definition=definition,models=models)
    return report
