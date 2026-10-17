"""Private subprocess entry point: artificial fixtures only, no native data access.

This file runs directly under Python -I. Reviewed package modules are copied by
solexs_reference into the explicitly supplied temporary directory; no setup.py is
executed. Nothing here is a reconstruction of the external tools' algorithms.
"""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
import warnings

import numpy as np
from astropy.io import fits


def run(stage):
    if hasattr(time, 'tzset'):
        time.tzset()
    sys.path.insert(0, str(stage))
    from solexs_tools.solexs_genlc import rebin_lc, solexs_genlc, write_lc
    from solexs_tools.solexs_genspec import solexs_genspec
    from solexs_tools.time_utils import unix_time_to_utc, utc_to_unix_time

    epoch = 1719792000
    times = epoch + np.arange(7, dtype=np.float64)
    channels = np.arange(340)
    counts = np.arange(1, 8)[:, None] * np.arange(1, 341)[None, :]
    exposures = np.array([2., 3., 5., 7., 11., 13., 17.])
    table = fits.BinTableHDU.from_columns([
        fits.Column(name='TSTART', format='D', array=times),
        fits.Column(name='TELAPSE', format='D', array=np.ones(7)),
        fits.Column(name='SPEC_NUM', format='J', array=np.arange(1, 8)),
        fits.Column(name='CHANNEL', format='340J', array=np.tile(channels, (7, 1))),
        fits.Column(name='COUNTS', format='340D', array=counts),
        fits.Column(name='EXPOSURE', format='D', array=exposures)], name='SPECTRUM')
    table.header['FILTER'] = 'SDD2'
    primary = fits.PrimaryHDU()
    primary.header['CONTENT'] = 'Type II PHA file'
    spectrum = stage/'artificial.pi'
    fits.HDUList([primary, table]).writeto(spectrum, overwrite=True)

    try:
        utc_to_unix_time(unix_time_to_utc(epoch))
    except ValueError:
        aware_rejected = True
    else:
        aware_rejected = False
    result = dict(epoch=dict(input=epoch, utc=unix_time_to_utc(epoch),
        inverse_input='2024-07-01T00:00:00',
        aware_helper_output_rejected=aware_rejected,
        round_trip=utc_to_unix_time('2024-07-01T00:00:00')),
        fixture=dict(tstart=times.tolist(), channel_first_last=[0, 339],
            counts_formula='(row + 1) * (channel + 1)', exposure=exposures.tolist(),
            telapse=[1.]*7), genlc={}, rebin={})
    for label, bin_size in [('none', None), ('explicit_one', 1), ('even_two', 2), ('odd_three', 3)]:
        path = solexs_genlc(str(spectrum), 2, 22, bin_size,
                            outfile=str(stage/('lc_'+label)), clobber=True)
        with fits.open(path) as opened:
            hdu = opened['RATE']
            result['genlc'][label] = dict(time=hdu.data['TIME'].tolist(),
                counts=hdu.data['COUNTS'].tolist(), time_format=hdu.columns['TIME'].format,
                counts_unit=hdu.columns['COUNTS'].unit,
                tstart=hdu.header['TSTART'], tstop=hdu.header['TSTOP'],
                timedel=hdu.header['TIMEDEL'], date_obs=hdu.header['DATE-OBS'],
                date_end=hdu.header['DATE-END'])
    for size in (1, 2, 3):
        rebinned, coordinates = rebin_lc(np.arange(1., 8.), times, size)
        result['rebin'][str(size)] = dict(counts=rebinned.tolist(), time=coordinates.tolist())
    path = write_lc(times[:2]+0.75, np.array([1., 2.]), 1, 'SDD2', str(stage/'fractional'))
    with fits.open(path) as opened:
        result['fractional_writer'] = dict(time=opened[1].data['TIME'].tolist(),
            tstart=opened[1].header['TSTART'], tstop=opened[1].header['TSTOP'])

    def gti(name, start, stop):
        path = stage/name
        fits.HDUList([fits.PrimaryHDU(), fits.BinTableHDU.from_columns([
            fits.Column(name='START', format='D', array=[start]),
            fits.Column(name='STOP', format='D', array=[stop])])]).writeto(path, overwrite=True)
        return path
    narrow = gti('narrow.gti', epoch+1, epoch+3)
    broad = gti('broad.gti', epoch, epoch+6)
    result['genspec'] = {}
    for label, start, stop, gt in [('request_half_open', epoch+1, epoch+3, narrow),
            ('closed_gti_endpoint', epoch+1, epoch+4, narrow),
            ('clamped_stop', epoch, epoch+99, broad)]:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            path = solexs_genspec(str(spectrum), start, stop, str(gt),
                outfile=str(stage/label), clobber=True)
        with fits.open(path) as opened:
            hdu = opened['SPECTRUM']
            channel = hdu.data['CHANNEL']
            values = hdu.data['COUNTS']
            result['genspec'][label] = dict(channel_first_last=[int(channel[0]), int(channel[-1])],
                channel_sha256=hashlib.sha256(np.asarray(channel, dtype='>i4').tobytes()).hexdigest(),
                counts_at_channels=[float(values[c]) for c in (0, 41, 313, 339)],
                counts_sum=float(values.sum()), exposure=hdu.header['EXPOSURE'],
                tstart=hdu.header['TSTART'], tstop=hdu.header['TSTOP'],
                counts_unit=hdu.columns['COUNTS'].unit,
                stop_clamp_warning=any('Setting tstop' in str(w.message) for w in caught))
    return result


if __name__ == '__main__':
    stage = Path(sys.argv[1]).resolve()
    # External tools print temporary CALDB paths; keep these out of stable JSON.
    with contextlib.redirect_stdout(io.StringIO()):
        report = run(stage)
    Path(sys.argv[2]).write_text(json.dumps(report, sort_keys=True, allow_nan=False)+'\n')
