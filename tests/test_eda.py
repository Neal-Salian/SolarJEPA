import numpy as np
import pandas as pd
from solar_flare_jepa.data.eda import summarize, summarize_events


def test_gaps_and_invalid_samples_are_distinct():
    ix = pd.to_datetime(['2024-01-01T00:00Z','2024-01-01T00:01Z','2024-01-01T00:03Z'])
    df = pd.DataFrame(index=ix)
    df['time_end'] = ix + pd.Timedelta(minutes=1)
    df['electron_correction_flag'] = 0
    for ch in ['xrsa','xrsb']:
        df[ch+'_flux'] = [1e-6, np.nan, 1e-4]
        df[ch+'_flux_raw'] = [1e-6, -1, 1e-4]
        df[ch+'_valid'] = [True,False,True]
        df[ch+'_flag'] = [0,2,0]
        df[ch+'_num'] = [60,0,60]
    report = summarize(df)
    assert report['rows'] == 3
    assert report['absent_grid_rows'] == 1
    assert report['channels']['xrsb']['invalid_present_rows'] == 1
    assert report['channels']['xrsb']['valid_rows'] == 2
    assert report['channels']['xrsb']['maximum_flux_w_m2'] == 1e-4


def test_event_states_do_not_inflate_event_count_and_boundary_states_retained():
    records = pd.DataFrame(dict(flare_id=[11,11,11,12],
        status=['EVENT_START','EVENT_PEAK','EVENT_END','POST_EVENT'],
        flare_class=['','M1.0','',''], xrsb_flux=[1e-6,1e-5,5e-6,2e-6],
        time=pd.to_datetime(['2024-01-01T00:00Z','2024-01-01T00:02Z','2024-01-01T00:04Z','2024-01-01T00:05Z'])))
    report = summarize_events(records)
    assert report['state_records'] == 4
    assert report['distinct_event_ids'] == 2
    assert report['events_with_start_peak_end'] == 1
    assert report['peak_classes'] == {'M':1}
    assert report['incomplete_event_ids'] == [12]
