"""Native numerical diagnostic helpers; no scientific mapping or correction."""
import numpy as np


def candidate_slice(bounds):
    """Reproduce the pinned author-tools strict bounds/exclusive-stop hypothesis.

    The text table has no encoded unit. Thresholds 2 and 22 are diagnostic inputs
    from the documented nominal LC band, not an approved channel-energy mapping.
    """
    bounds = np.asarray(bounds)
    if (bounds.ndim != 2 or bounds.shape[1] != 2 or not np.isfinite(bounds).all()
            or not (bounds[:, 1] > bounds[:, 0]).all()
            or not (np.diff(bounds[:, 0]) > 0).all()
            or not (np.diff(bounds[:, 1]) > 0).all()):
        raise ValueError('Malformed candidate bounds')
    low, high = np.flatnonzero(bounds[:, 0] > 2), np.flatnonzero(bounds[:, 1] < 22)
    if not low.size or not high.size or low[0] >= high[-1]:
        raise ValueError('Empty candidate band')
    return int(low[0]), int(high[-1])


def compare_native_rows(lc, spectra, band, response_channels):
    """Compare only identical native row coordinates; propagate missing values.

    Spectra is an iterator of small column dictionaries from iter_spectra. The
    upper-inclusive control tests the excluded endpoint of the tools hypothesis.
    Equality does not certify a response, band definition or detector correction.
    """
    time, counts = lc['TIME'], lc['COUNTS']
    if time.ndim != 1 or counts.shape != time.shape:
        raise ValueError('Incompatible light-curve dimensions')
    if counts.dtype.kind != 'f':
        raise ValueError('This sample diagnostic supports floating COUNTS only')
    first, stop = band
    summaries = {k: dict(equal_rows=0, maximum_absolute_difference=None)
                 for k in ('tool_slice', 'inclusive_upper_control', 'all_channel_sum')}
    offset, compared, missing = 0, 0, 0
    nan_equal = True
    channel_equal = True
    channel_constant = True
    reference = None
    exposure_one, telapse_one = True, True
    for columns in spectra:
        t, pi = columns['TSTART'], columns['COUNTS']
        n = len(t)
        selection = slice(offset, offset + n)
        if offset + n > len(time) or not np.array_equal(
                t.astype(object), time[selection].astype(object)):
            raise ValueError('Native LC/PI coordinates differ; positional comparison refused')
        channels = columns['CHANNEL']
        if (pi.ndim != 2 or channels.shape != pi.shape or pi.shape[0] != n
                or not 0 <= first < stop < pi.shape[1]):
            raise ValueError('Incompatible PI dimensions or candidate slice')
        if pi.dtype.kind != 'f':
            raise ValueError('This sample diagnostic supports floating COUNTS only')
        if n:
            if reference is None:
                reference = channels[0].copy()
            channel_constant &= bool(np.all(channels == reference))
            channel_equal &= bool(channels.shape[1] == len(response_channels)
                                  and np.all(channels == response_channels))
        nan_rows = np.isnan(pi).all(axis=1)
        missing += int(nan_rows.sum())
        nan_equal &= bool(np.array_equal(nan_rows, np.isnan(counts[selection])))
        exposure_one &= bool(np.all(columns['EXPOSURE'] == 1))
        telapse_one &= bool(np.all(columns['TELAPSE'] == 1))
        valid = np.isfinite(counts[selection]) & np.isfinite(pi).all(axis=1)
        compared += int(valid.sum())
        finite_pi, finite_lc = pi[valid], counts[selection][valid]
        try:
            with np.errstate(over='raise', invalid='raise'):
                for key, values in [('tool_slice', finite_pi[:, first:stop]),
                                    ('inclusive_upper_control', finite_pi[:, first:stop + 1]),
                                    ('all_channel_sum', finite_pi)]:
                    difference = values.sum(axis=1) - finite_lc
                    summaries[key]['equal_rows'] += int((difference == 0).sum())
                    if difference.size:
                        previous = summaries[key]['maximum_absolute_difference']
                        summaries[key]['maximum_absolute_difference'] = max(
                            previous or 0, float(np.abs(difference).max()))
        except FloatingPointError as exc:
            raise ValueError('Native count arithmetic exceeds the finite range') from exc
        offset += n
    if offset != len(time):
        raise ValueError('Native LC/PI lengths differ; positional comparison refused')
    return dict(rows=offset, finite_compared_rows=compared, pi_nan_rows=missing,
                pi_nan_mask_equals_lc=nan_equal, pi_channel_labels_equal_rmf=channel_equal,
                pi_channel_labels_constant=channel_constant,
                pi_channel_first_last=[int(reference[0]), int(reference[-1])]
                if reference is not None else None,
                exposure_all_one=exposure_one, telapse_all_one=telapse_one,
                mapping_validated=False, **summaries)
