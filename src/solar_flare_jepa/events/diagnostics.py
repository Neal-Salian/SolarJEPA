"""Deterministic diagnostics of exposed, immutable research trajectories.

Sensitivity tables are post hoc descriptions, never development selection. This
module neither fits a rule nor converts a threshold-bin time to catalog onset.
"""
import numpy as np

from .frozen import _load, _numeric, evaluate_frozen
from .labels import MINUTE_NS, class_threshold, integer
from .matching import match_events


THRESHOLD_FACTORS = (0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
LEADS_SECONDS = (0, 60, 300, 600, 900)


def trajectory_error(context, prediction, observed, *, issue_ns, start_ns,
                     peak_ns, threshold_W_m2):
    """Describe one native XRS-B trajectory and one retrospective event.

    Max timing uses the first tied bin's **start**, not bin completion, catalog
    onset, or physical onset. Peak class may mature beyond this horizon.
    """
    vectors = []
    for value, name in ((context, 'context'), (prediction, 'prediction'), (observed, 'observed')):
        array = np.asarray(value)
        if array.ndim != 1 or not len(array):
            raise ValueError(f'{name} requires a nonempty native minute vector')
        vectors.append(_numeric(value, array.shape, name))
    context, prediction, observed = vectors
    if prediction.shape != observed.shape:
        raise ValueError('Prediction and observed horizon lengths differ')
    issue, start, peak = (integer(v, name) for v, name in
                         ((issue_ns, 'issue'), (start_ns, 'start'), (peak_ns, 'peak')))
    if any(v % MINUTE_NS for v in (issue, start, peak)) or start > peak:
        raise ValueError('Ordered native-minute catalog coordinates required')
    threshold = _numeric([threshold_W_m2], (1,), 'threshold')[0]
    end = integer(issue + len(prediction)*MINUTE_NS, 'horizon end')
    pmax, omax = float(prediction.max()), float(observed.max())
    return dict(onset_lead_seconds=(start-issue)/1e9,
        catalog_peak_lead_seconds=(peak-issue)/1e9,
        onset_to_peak_seconds=(peak-start)/1e9,
        catalog_peak_in_horizon=bool(issue <= peak < end),
        last_context_W_m2=float(context[-1]),
        background_already_above_threshold=bool(context[-1] >= threshold),
        predicted_max_W_m2=pmax, observed_max_W_m2=omax,
        predicted_max_first_bin_start_ns=issue+int(prediction.argmax())*MINUTE_NS,
        observed_max_first_bin_start_ns=issue+int(observed.argmax())*MINUTE_NS,
        predicted_threshold_exceedance=bool(pmax >= threshold),
        observed_threshold_exceedance=bool(omax >= threshold),
        predicted_to_observed_max_ratio=pmax/omax,
        mean_log10_error=float(np.mean(np.log10(prediction)-np.log10(observed))),
        mean_absolute_log10_error=float(np.mean(np.abs(np.log10(prediction)-np.log10(observed)))))


def _event_key(event):
    return event['catalog_id']+':'+event['event_id']


def _evaluation(issues, ends, ids, valid, events, predicted, lead, policy):
    # Same censoring/eligibility as the preserved adapter. A short-lead onset
    # invalidates that origin; it must not be relabeled as a valid negative.
    early = np.array([any(t <= e['start_ns'] < int(t)+lead*10**9 for e in events)
                      for t in issues], dtype=bool)
    eligible_mask = valid & ~early
    eligible = [e for e in events if any(ok and int(t)+lead*10**9 <= e['start_ns'] < end
                for ok, t, end in zip(eligible_mask, issues, ends))]
    alarms = [dict(alarm_id=ids[i], issue_ns=int(t), window_end_ns=int(end))
              for i, (t, end) in enumerate(zip(issues, ends)) if eligible_mask[i] and predicted[i]]
    result = match_events(alarms, [dict(event_id=_event_key(e), start_ns=e['start_ns'])
                          for e in eligible], decision_policy_id=policy, minimum_lead_seconds=lead)
    result['eligible_origin_count'] = int(eligible_mask.sum())
    result['censored_short_lead_origins'] = int((valid & early).sum())
    result['eligible_days'] = float(eligible_mask.sum()*(1800-lead)/86400)
    return result, eligible_mask


def diagnose_frozen(config, roots):
    """Validate the complete frozen cohort before reporting M+/X+ diagnostics.

    The old evaluator is unchanged and remains the authority for its protocol.
    Every threshold factor retains the native class-defined observed event set.
    Lead sensitivity changes eligible exposure explicitly. No winner is selected.
    C+ baseline counts are retained; detailed error/sensitivity tables concern M/X.
    """
    baseline = evaluate_frozen(config, roots)
    docs, identities = _load(config, roots)
    inputs = docs['inputs']
    issues = np.asarray(inputs['future_grid']['issue_times_ns'], dtype=np.int64)
    ends = issues+30*MINUTE_NS
    ids = inputs['future_grid']['origin_ids']
    context = np.asarray(inputs['context']['values'])[:, :, 1]
    observed = np.asarray(inputs['targets']['values'])[:, :, 1]
    events = sorted(docs['events'], key=lambda e: (e['start_ns'], _event_key(e)))
    lead = int(config['minimum_lead_seconds'])
    report = dict(schema_version=1, claim='exposed_period_error_diagnostics_only',
        rule_selection_performed=False, fit_performed=False, inference_performed=False,
        source_identities=identities, frozen_policy_fingerprint=baseline['policy_fingerprint'],
        origin_count=baseline['origin_count'], candidate_count=baseline['candidate_count'],
        excluded_origin_count=baseline['excluded_origin_count'],
        threshold_grid=list(THRESHOLD_FACTORS), lead_grid_seconds=list(LEADS_SECONDS),
        sensitivity_status='POST_HOC_DESCRIPTIVE_NO_SELECTION',
        event_uncertainty=dict(status='NOT_ESTIMATED', reason=
            'Existing UTC-block intervals are for binary opportunities. Event intervals require dependence-aware resampling with rematching and boundary handling; window intervals are not event intervals.'),
        limitations=baseline['limitations']+[
            'Error strata and catalog states use future truth for explanation only.',
            'First tied forecast/observed maximum is not a unique flare peak estimator.',
            'January diagnostics cannot select any onset-rule parameter or model.'], classes={})
    for letter in 'CMX':
        old = baseline['classes'][letter]
        section = {key: old[key] for key in ('eligible_events', 'qualified_catalog_events',
            'events_outside_evaluated_exposure', 'valid_origins', 'advance_valid_origins',
            'short_lead_origins', 'exposed_days')}
        section['models'] = {}
        report['classes'][letter] = section
        threshold = class_threshold(letter+'1.0')
        qualified = [e for e in events if class_threshold(e['flare_class']) >= threshold]
        labels = docs['labels_'+letter]
        valid = np.asarray(labels['valid_mask'], bool) & np.asarray(labels['mature_mask'], bool)
        for name in sorted(docs['predictions']):
            legacy = old['models'][name]
            matching = legacy['event_matching']
            model = dict(legacy_counts=matching['counts'], legacy_metrics=matching['metrics'],
                matched_events=matching['matches'],
                false_alarms_per_exposed_day=legacy['false_alarms_per_exposed_day'],
                warning_time_fraction=legacy['warning_time_fraction'],
                duplicate_eligible_alarms=legacy['duplicate_eligible_alarms'],
                opportunity_scores=legacy['advance_opportunities'],
                opportunity_uncertainty=legacy['uncertainty'])
            reference = old['models'].get('persistence')
            if reference is None:
                model['paired_persistence_comparison'] = dict(status='UNAVAILABLE',
                    reason='Persistence is absent from this declared cohort')
            else:
                hits = {row['event_id'] for row in matching['matches']}
                ref_hits = {row['event_id'] for row in reference['event_matching']['matches']}
                cohort = hits | set(matching['unmatched_event_ids'])
                ref_cohort = ref_hits | set(reference['event_matching']['unmatched_event_ids'])
                if cohort != ref_cohort:
                    raise ValueError('Paired event populations differ')
                model['paired_persistence_comparison'] = dict(status='DESCRIPTIVE_PAIRED_EVENTS',
                    reference='persistence', both_hit_event_ids=sorted(hits & ref_hits),
                    model_only_hit_event_ids=sorted(hits-ref_hits),
                    persistence_only_hit_event_ids=sorted(ref_hits-hits),
                    both_miss_event_ids=sorted(cohort-hits-ref_hits),
                    paired_uncertainty='NOT_ESTIMATED')
            section['models'][name] = model
            if letter == 'C':
                continue
            prediction = np.asarray(docs['predictions'][name]['values'])[:, :, 1]
            maxima = prediction.max(axis=1)
            check, eligible_mask = _evaluation(issues, ends, ids, valid, qualified,
                                              maxima >= threshold, lead, 'diagnostic:legacy')
            if check['counts'] != matching['counts']:
                raise ValueError('Diagnostic matching contradicts preserved evaluator')
            hit_ids = {m['event_id'] for m in matching['matches']}
            eligible_ids = hit_ids | set(matching['unmatched_event_ids'])
            model['events'] = []
            for event in qualified:
                key = _event_key(event)
                row = dict(event_id=key, catalog_sha256=event['catalog_sha256'],
                    flare_class=event['flare_class'], start_ns=event['start_ns'],
                    peak_ns=event['peak_ns'], end_ns=event['end_ns'],
                    catalog_peak_W_m2=event['peak_flux'],
                    status='hit' if key in hit_ids else ('miss' if key in eligible_ids else 'outside_evaluated_exposure'),
                    opportunities=[])
                for i, (t, end) in enumerate(zip(issues, ends)):
                    if t <= event['start_ns'] < end:
                        error = trajectory_error(context[i], prediction[i], observed[i],
                            issue_ns=int(t), start_ns=event['start_ns'], peak_ns=event['peak_ns'],
                            threshold_W_m2=threshold)
                        row['opportunities'].append(dict(origin_id=ids[i], issue_ns=int(t),
                            horizon_end_ns=int(end), eligible=bool(eligible_mask[i]), **error))
                model['events'].append(row)
            false_ids = set(matching['unmatched_alarm_ids'])
            model['false_alarms'] = []
            for i, (t, end) in enumerate(zip(issues, ends)):
                if ids[i] not in false_ids:
                    continue
                known = [_event_key(e) for e in events if e['start_ns'] < t <=
                         (e['end_ns'] if e['end_ns'] is not None else e['peak_ns'])]
                unresolved = [_event_key(e) for e in events if e['start_ns'] < t and
                              e['end_ns'] is None and e['peak_ns'] < t]
                model['false_alarms'].append(dict(origin_id=ids[i], issue_ns=int(t),
                    horizon_end_ns=int(end), last_context_W_m2=float(context[i, -1]),
                    predicted_max_W_m2=float(maxima[i]), observed_max_W_m2=float(observed[i].max()),
                    background_already_above_threshold=bool(context[i, -1] >= threshold),
                    observed_threshold_exceedance=bool(observed[i].max() >= threshold),
                    known_catalog_evolution_ids=known, unresolved_prior_end_ids=unresolved))
            model['threshold_sensitivity'] = []
            for factor in THRESHOLD_FACTORS:
                sensitivity, _ = _evaluation(issues, ends, ids, valid, qualified,
                    maxima >= factor*threshold, lead, f'diagnostic:factor:{factor}:{letter}')
                model['threshold_sensitivity'].append(dict(factor=factor,
                    decision_threshold_W_m2=factor*threshold, counts=sensitivity['counts'],
                    metrics=sensitivity['metrics'], eligible_days=sensitivity['eligible_days']))
            model['lead_sensitivity'] = []
            for minimum in LEADS_SECONDS:
                sensitivity, _ = _evaluation(issues, ends, ids, valid, qualified,
                    maxima >= threshold, minimum, f'diagnostic:lead:{minimum}:{letter}')
                model['lead_sensitivity'].append({key: sensitivity[key] for key in
                    ('minimum_lead_seconds', 'counts', 'metrics', 'eligible_origin_count',
                     'censored_short_lead_origins', 'eligible_days')})
    return report
