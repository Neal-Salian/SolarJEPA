"""Descriptive paired calendar-block uncertainty on an explicit origin axis."""
import numpy as np

from ..forecasting.contracts import _times, fingerprint_payload, logical_array


def _integer(value, name, *, minimum=0):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    result = int(value)
    if result < minimum:
        raise ValueError(f'{name} must be >= {minimum}')
    return result


def _losses(value, size, name):
    raw = np.asarray(value)
    if raw.shape != (size,) or raw.dtype.kind not in 'fiu':
        raise ValueError(f'{name} requires a numeric per-origin loss vector')
    values = raw.astype(float, copy=True)
    if np.isinf(values).any() or (values[np.isfinite(values)] < 0).any():
        raise ValueError('Losses must be nonnegative, with NaN only for explicitly missing pairs')
    return values


def paired_block_bootstrap(issue_times_ns, model_losses, reference_losses,
                           block_seconds, replicates=2000, seed=17, confidence=0.95,
                           minimum_block_seconds=0):
    """Resample nonoverlapping UTC-epoch calendar blocks jointly, with replacement.

    The full regular chronological origin axis is mandatory, including missing
    target support represented as paired NaNs. Model failures must raise upstream;
    they are never legitimate missing loss support. Losses are scalar per-origin
    aggregates in identical caller-declared loss units; all channels/leads must
    already have been reduced on common valid target support. This utility
    cannot verify that upstream scientific agreement. Negative difference favors
    the model. Unequal-size and partial edge blocks retain their origin counts;
    every replicate pools selected paired sums/counts, never block means.

    ``minimum_block_seconds`` enforces a caller-declared support constraint; the
    caller must include the maximum relevant context/horizon dependency. Neither
    it nor an explicit block duration proves independence, stationarity, or
    captures long active-region/solar-cycle dependence. The percentile interval
    is descriptive and makes no significance claim. NaN pairs are excluded
    jointly; empty-pair blocks remain in resampling and empty replicates are
    reported, rather than treated as zero loss.
    """
    times = _times(issue_times_ns, ndim=1)
    if len(times) < 2:
        raise ValueError('At least two chronological origins are required')
    gaps = [int(b)-int(a) for a,b in zip(times,times[1:])]
    if gaps[0] <= 0 or any(gap != gaps[0] for gap in gaps):
        raise ValueError('Origin axis must be strictly increasing and regular; preserve missing positions')
    block_seconds = _integer(block_seconds, 'block_seconds', minimum=1)
    minimum = _integer(minimum_block_seconds, 'minimum_block_seconds')
    replicates = _integer(replicates, 'replicates', minimum=1)
    seed = _integer(seed, 'seed')
    if (isinstance(confidence, (bool, np.bool_)) or not isinstance(confidence,(int,float,np.integer,np.floating))
            or not np.isfinite(confidence) or not 0 < confidence < 1):
        raise ValueError('confidence must be finite and between zero and one')
    confidence = float(confidence)
    block_ns = block_seconds * 1_000_000_000
    if block_seconds < minimum or block_ns < gaps[0] or block_ns > np.iinfo(np.int64).max:
        raise ValueError('Block duration violates declared minimum support or origin cadence')
    model = _losses(model_losses,len(times),'model_losses')
    reference = _losses(reference_losses,len(times),'reference_losses')
    if not np.array_equal(np.isnan(model),np.isnan(reference)):
        raise ValueError('Paired losses require identical missing-support masks')
    paired = np.isfinite(model) & np.isfinite(reference)
    block_ids = [int(time)//block_ns for time in times]
    ids = sorted(set(block_ids))
    if len(ids) < 2:
        raise ValueError('At least two calendar blocks are required')
    # Scaling before summation preserves finite means at large native loss scales.
    difference = model[paired]-reference[paired]
    scale = float(np.max(np.abs(difference))) if len(difference) else 1.
    scale = scale or 1.
    normalized = np.zeros(len(times))
    normalized[paired] = difference/scale
    blocks, sums, counts = [], [], []
    for block in ids:
        selected = np.array([value == block for value in block_ids], bool)
        count = int((selected & paired).sum())
        sums.append(float(normalized[selected & paired].sum()))
        counts.append(count)
        blocks.append(dict(start_ns=block*block_ns, end_ns=(block+1)*block_ns,
            origin_count=int(selected.sum()), paired_count=count))
    if sum(count > 0 for count in counts) < 2:
        raise ValueError('At least two blocks with valid paired losses are required')
    sums, counts = np.asarray(sums), np.asarray(counts,np.int64)
    observed = float(sums.sum()/counts.sum()*scale)
    rng, draws = np.random.default_rng(seed), []
    undefined = 0
    for _ in range(replicates):
        selected = rng.integers(0,len(blocks),size=len(blocks))
        denominator = int(counts[selected].sum())
        if not denominator:
            undefined += 1
        else:
            draws.append(float(sums[selected].sum()/denominator))
    alpha = (1-confidence)/2
    interval = None if not draws else [float(x*scale) for x in np.quantile(draws,[alpha,1-alpha])]
    fingerprint = fingerprint_payload(dict(schema_version=1, issue_times_ns=logical_array(times),
        model_losses=logical_array(model), reference_losses=logical_array(reference),
        block_seconds=block_seconds, minimum_block_seconds=minimum, replicates=replicates,
        seed=seed, confidence=confidence))
    return dict(schema_version=1, method='paired_nonoverlapping_UTC_calendar_block_percentile_v1',
        input_fingerprint=fingerprint, mean_difference=observed, confidence_interval=interval,
        interval_reason=None if draws else 'no_defined_replicates', confidence=confidence,
        interval_condition='draws_with_at_least_one_valid_paired_origin',
        direction='model_loss - reference_loss; negative favors model',
        loss_units='Caller-declared identical scalar loss units; not inferred by this utility',
        origin_count=len(times), origin_cadence_ns=gaps[0], scored_pair_count=int(paired.sum()),
        excluded_pair_count=int((~paired).sum()), model_missing_count=int(np.isnan(model).sum()),
        reference_missing_count=int(np.isnan(reference).sum()), block_seconds=block_seconds,
        minimum_block_seconds=minimum, block_count=len(blocks),
        informative_block_count=int((counts>0).sum()), blocks=blocks,
        edge_blocks_partial=(int(times[0]) != blocks[0]['start_ns']
            or int(times[-1])+gaps[0] != blocks[-1]['end_ns']),
        replicates=replicates, seed=seed, defined_replicate_count=len(draws),
        undefined_replicate_count=undefined, significance_claim=False,
        reduction='Joint paired calendar-block draws; pooled paired loss sums / paired origin counts',
        limitations=['Block choice does not establish temporal independence or stationarity.',
            'A short interval cannot identify long active-region or solar-cycle uncertainty.',
            'NaN pair exclusion can change the evaluated population; report upstream coverage.',
            'This interval is descriptive; no hypothesis test or significance claim is provided.'])
