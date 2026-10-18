"""Native-bin catalog labels adapted from external validation's flare_alignment.

Final peak classes are retrospective truth. Coverage is a declared selection
envelope, never a claim of complete physical-flare detection. No catalog field
is a predictor input. Partial events remain explicit and conservatively censor
the supplied selection until the caller obtains the missing catalog states.
"""
from dataclasses import dataclass
import hashlib
import json
import re

import numpy as np
import pandas as pd

MINUTE_NS = 60_000_000_000
CALIBRATION = 'GOES_science_quality_W_m2_no_legacy_scaling'


def integer(value, name, minimum=None):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f'{name} must be an integer')
    value = int(value)
    if not np.iinfo(np.int64).min <= value <= np.iinfo(np.int64).max:
        raise ValueError(f'{name} outside int64 range')
    if minimum is not None and value < minimum:
        raise ValueError(f'{name} must be >= {minimum}')
    return value


def times(value, name):
    if isinstance(value,(list,tuple)) and any(isinstance(v,(bool,np.bool_)) for v in value):
        raise ValueError(f'{name} cannot contain boolean coordinates')
    a = np.asarray(value)
    if a.ndim != 1 or a.dtype.kind not in 'iu':
        raise ValueError(f'{name} must be an integer vector')
    return np.array([integer(v, name) for v in a], dtype=np.int64)


def digest(value):
    if not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None:
        raise ValueError('Invalid SHA-256 identity')
    return value


def class_threshold(value):
    match = re.fullmatch(r'([ABCMX])([0-9]+(?:\.[0-9]+)?)', value) if isinstance(value,str) else None
    if match is None:
        raise ValueError('Expected explicit A/B/C/M/X flare class and magnitude')
    number = float(match[2])
    if not np.isfinite(number) or number < 1 or (match[1] != 'X' and number >= 10):
        raise ValueError('Invalid flare class magnitude')
    return {'A':1e-8,'B':1e-7,'C':1e-6,'M':1e-5,'X':1e-4}[match[1]]*number


@dataclass(frozen=True)
class CatalogEvent:
    event_id: str
    source: str
    catalog_id: str
    catalog_sha256: str
    start_ns: int | None
    peak_ns: int | None
    end_ns: int | None
    flare_class: str | None
    peak_flux: float | None
    calibration: str
    peak_saturated: bool = False

    def __post_init__(self):
        for name in ('event_id','source','catalog_id'):
            if not isinstance(getattr(self,name),str) or not getattr(self,name).strip():
                raise ValueError(f'Explicit {name} required')
        digest(self.catalog_sha256)
        if self.calibration != CALIBRATION:
            raise ValueError('Explicit science-quality native W/m2 calibration required')
        known = []
        for name in ('start_ns','peak_ns','end_ns'):
            value = getattr(self,name)
            if value is not None:
                value = integer(value,name)
                if value % MINUTE_NS:
                    raise ValueError('Catalog times must retain native UTC minute precision')
                known.append(value)
        if known != sorted(known):
            raise ValueError('Catalog state times must be ordered')
        if self.flare_class is not None:
            class_threshold(self.flare_class)
        if self.peak_flux is not None and (isinstance(self.peak_flux,bool)
                or not isinstance(self.peak_flux,(float,int,np.floating))
                or not np.isfinite(self.peak_flux) or self.peak_flux <= 0):
            raise ValueError('Peak flux must be positive W/m2')
        if type(self.peak_saturated) is not bool:
            raise ValueError('Saturation must be an explicit boolean')


def states_to_events(records, *, source, catalog_id, source_hashes, calibration):
    """Group explicit flsum states; IDs never supply missing state timestamps.

    ``records`` is the existing data.goes.read_event_records dataframe. Caller
    verifies bytes before reading; this function fingerprints declared hashes.
    Conflicting duplicate states raise; identical repeated states are deduplicated.
    The collection hash is canonical JSON of filename-to-SHA256 declarations.
    """
    if (not isinstance(source,str) or not re.fullmatch(r'GOES-([1-9]|1[0-9])',source)
            or not isinstance(catalog_id,str) or not catalog_id.strip() or calibration!=CALIBRATION):
        raise ValueError('Explicit source, catalog ID and science-quality calibration required')
    if not isinstance(source_hashes,dict) or not source_hashes:
        raise ValueError('Explicit source hashes required')
    for key,value in source_hashes.items():
        if not isinstance(key,str) or not key:
            raise ValueError('Invalid source filename')
        digest(value)
    collection = hashlib.sha256(json.dumps(source_hashes,sort_keys=True,
                             separators=(',',':')).encode()).hexdigest()
    required = {'flare_id','status','time','flare_class','xrsb_flux','source_file'}
    if not required.issubset(records.columns):
        raise ValueError('Missing flsum record fields')
    groups = {}
    for row in records.to_dict('records'):
        ident = row['flare_id']
        if isinstance(ident,bool) or not isinstance(ident,(int,float,np.number)) or not np.isfinite(ident) or ident < 0 or ident != int(ident):
            raise ValueError('Invalid flare ID')
        if row['source_file'] not in source_hashes:
            raise ValueError('Unpinned state source')
        stamp = pd.Timestamp(row['time'])
        if pd.isna(stamp) or stamp.tzinfo is None:
            raise ValueError('Explicit UTC state timestamp required')
        ns = stamp.tz_convert('UTC').value
        status = row['status']
        if status not in ('EVENT_START','EVENT_PEAK','EVENT_END','POST_EVENT'):
            raise ValueError('Unrecognized catalog state')
        value = (ns,str(row['flare_class']),float(row['xrsb_flux']))
        state = groups.setdefault(str(int(ident)),{})
        if status in state and state[status] != value:
            raise ValueError('Conflicting duplicate catalog state')
        state[status] = value
    events = []
    for ident,state in sorted(groups.items()):
        peak = state.get('EVENT_PEAK')
        events.append(CatalogEvent(ident,source,catalog_id,collection,
            state['EVENT_START'][0] if 'EVENT_START' in state else None,
            peak[0] if peak else None,
            state['EVENT_END'][0] if 'EVENT_END' in state else None,
            peak[1] if peak else None,peak[2] if peak else None,calibration))
    return events


def label_events(events, issues_ns, *, starts_ns, valid_b, coverage, partition,
                 catalog_identities, source, calibration, horizon_seconds=1800, context_seconds=7200,
                 minimum_class='M1.0', target='onset', feature_available_ns=None):
    """Label catalog onset/peak in [issue,end), with separate zero-lead flags.

    Maturity includes ALL candidate peaks, even subthreshold candidates. Input
    QC describes native XRS-B bins, not feature availability. Partition checks
    enforce temporal support; they do not certify event-disjoint training.
    """
    if target not in ('onset','peak'):
        raise ValueError('Target must be onset or peak')
    if source!='GOES-16' or calibration!=CALIBRATION:
        raise ValueError('Explicit GOES-16 science-quality calibration required')
    if not isinstance(events,(list,tuple)):
        raise ValueError('Events require an explicit list or tuple')
    issues = times(issues_ns,'issues_ns'); starts = times(starts_ns,'starts_ns')
    for axis in (issues,starts):
        if len(axis)>1 and np.any(axis[1:]<=axis[:-1]):
            raise ValueError('Coordinates must be strictly chronological and unique')
        if np.any(axis % MINUTE_NS):
            raise ValueError('Coordinates require native UTC minute precision')
    valid = np.asarray(valid_b)
    if valid.dtype.kind != 'b' or valid.shape != starts.shape:
        raise ValueError('valid_b requires a boolean mask on starts_ns')
    h = integer(horizon_seconds,'horizon_seconds',1)*10**9
    c = integer(context_seconds,'context_seconds',0)*10**9
    if h % MINUTE_NS or c % MINUTE_NS:
        raise ValueError('Support must contain whole native minutes')
    cs,ce = (integer(v,'coverage') for v in coverage)
    ps,pe = (integer(v,'partition') for v in partition)
    if ce<=cs or pe<=ps:
        raise ValueError('Coverage and partition must be ordered')
    identities = set(catalog_identities)
    if not identities:
        raise ValueError('Pinned catalog identity required even for empty events')
    by_name={}
    for name,sha in identities:
        if not isinstance(name,str) or not name:
            raise ValueError('Catalog name required')
        digest(sha)
        if name in by_name and by_name[name]!=sha:
            raise ValueError('Conflicting SHA-256 for one catalog name')
        by_name[name]=sha
    seen = set()
    for event in events:
        if not isinstance(event,CatalogEvent):
            raise ValueError('Explicit CatalogEvent records required')
        key = (event.catalog_id,event.event_id)
        if key in seen:
            raise ValueError('Duplicate catalog event ID')
        seen.add(key)
        if (event.catalog_id,event.catalog_sha256) not in identities:
            raise ValueError('Catalog provenance mismatch')
    available = issues if feature_available_ns is None else times(feature_available_ns,'feature_available_ns')
    if available.shape != issues.shape:
        raise ValueError('Availability axis mismatch')
    incomplete = any(e.start_ns is None or e.peak_ns is None or e.flare_class is None
                     or e.peak_flux is None for e in events)
    def supported(a,b):
        selected = (starts>=a)&(starts<b)
        rows=starts[selected]
        count=(b-a)//MINUTE_NS
        return (len(rows)==count and (not count or (rows[0]==a and rows[-1]==b-MINUTE_NS
                and np.all(np.diff(rows)==MINUTE_NS))) and bool(valid[selected].all()))
    outcomes, masks, deadlines, reasons, ids, zero = [],[],[],[],[],[]
    threshold = class_threshold(minimum_class)
    for issue,avail in zip(issues,available):
        issue = int(issue); end = integer(issue+h,'horizon end')
        candidate = [e for e in events if getattr(e,'start_ns' if target=='onset' else 'peak_ns') is not None
                     and issue<=getattr(e,'start_ns' if target=='onset' else 'peak_ns')<end]
        matching = [e for e in candidate if e.flare_class is not None and class_threshold(e.flare_class)>=threshold]
        maturity = max([end]+[e.peak_ns+MINUTE_NS for e in candidate if e.peak_ns is not None])
        why = []
        if incomplete: why.append('incomplete_catalog_event')
        if issue<cs or end>ce: why.append('horizon_outside_catalog_coverage')
        if issue-c<ps or end>pe: why.append('support_outside_partition')
        if maturity>pe: why.append('maturity_outside_partition')
        if avail>issue: why.append('feature_not_available')
        if not supported(issue,end): why.append('horizon_missing_or_invalid_xrsb')
        for e in candidate:
            if e.source!='GOES-16': why.append('source_mismatch')
            if e.peak_saturated: why.append('peak_saturated')
            if e.start_ns is not None and e.peak_ns is not None:
                last = e.peak_ns+MINUTE_NS
                if e.start_ns<max(cs,ps) or last>min(ce,pe): why.append('class_support_outside_selection')
                if not supported(e.start_ns,last): why.append('class_support_missing_or_invalid_xrsb')
        outcomes.append(bool(matching)); masks.append(not why); deadlines.append(maturity)
        reasons.append(sorted(set(why))); ids.append([e.event_id for e in matching])
        zero.append(any(getattr(e,'start_ns' if target=='onset' else 'peak_ns')==issue for e in matching))
    return dict(label_status='CANDIDATE_CATALOG_LABELS',target=target,
        occurrence_interval='issue_inclusive_horizon_end_exclusive',
        minimum_class=minimum_class, catalog_completeness='UNKNOWN',
        operational_availability='UNKNOWN', outcomes=outcomes,valid_mask=masks,
        calibration=calibration,source=source,
        maturity_ns=deadlines,reasons=reasons,event_ids=ids,zero_lead_mask=zero,
        issue_times_ns=issues.tolist(),catalog_identities=sorted(identities))
