"""Explicit chronological bounds; no fractional or random-window splits.

Nanosecond bounds use the dataset's declared coordinate system. A partition
includes bins starting at its start and admits support ending exactly at its
end. Supplied event groups are definitions from callers, never derived here.
"""
from dataclasses import asdict, dataclass

from .contracts import TimeSeriesDataset, _category, _string, _time_scalar


@dataclass(frozen=True)
class TemporalPartition:
    name: str
    start_ns: int
    end_ns: int

    def __post_init__(self):
        object.__setattr__(self, 'name', _category(self.name, ('train', 'validation', 'calibration', 'test'),
                                                'chronological partition name'))
        for name in ('start_ns', 'end_ns'):
            object.__setattr__(self, name, _time_scalar(getattr(self, name)))
        if self.start_ns >= self.end_ns:
            raise ValueError('Partition start must precede end')

    def as_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class EventGroup:
    group_id: str
    start_ns: int
    end_ns: int
    maturity_ns: int

    def __post_init__(self):
        object.__setattr__(self, 'group_id', _string(self.group_id, 'Group identity'))
        if not self.group_id.strip():
            raise ValueError('A supplied group identity is required')
        for name in ('start_ns', 'end_ns', 'maturity_ns'):
            object.__setattr__(self, name, _time_scalar(getattr(self, name)))
        if self.start_ns >= self.end_ns or self.maturity_ns < self.end_ns:
            raise ValueError('Group interval must be nonempty and mature at/after end')

    def as_dict(self):
        return asdict(self)


def validate_partition(dataset: TimeSeriesDataset, partition: TemporalPartition):
    """Validate a raw-axis partition before selecting observations or windows."""
    if not isinstance(partition, TemporalPartition):
        raise ValueError('Expected a TemporalPartition')
    origin = int(dataset.starts_ns[0])
    end = int(dataset.ends_ns[-1])
    cadence = dataset.cadence_seconds * 1_000_000_000
    if (partition.start_ns < origin or partition.end_ns > end
            or (partition.start_ns - origin) % cadence
            or (partition.end_ns - origin) % cadence):
        raise ValueError('Partition bounds must be within the dataset on its declared grid')


def chronological_partitions(dataset: TimeSeriesDataset, boundaries, *, embargo_ns=0):
    """Return validated ordered train/validation/[calibration]/test partitions.

    ``boundaries`` is an iterable of TemporalPartition objects, or dictionaries
    with exactly ``name``, ``start_ns``, ``end_ns`` (integer nanoseconds, never
    date strings, fractions or implicit offsets). Entries may mix these forms.
    Touching half-open bounds and explicit gaps are allowed; overlap, reversed
    order, missing/duplicate roles, outside-data or off-grid bounds are rejected.
    A partition in an observed cadence gap is valid and may yield no windows.
    ``embargo_ns`` is an explicit nonnegative integer minimum gap between every
    adjacent pair. It validates supplied bounds and never trims/moves them.
    """
    embargo_ns = _time_scalar(embargo_ns)
    if embargo_ns < 0:
        raise ValueError('Temporal embargo must be nonnegative')
    partitions = []
    for entry in boundaries:
        if isinstance(entry, dict):
            if set(entry) != {'name', 'start_ns', 'end_ns'}:
                raise ValueError('Partition dictionary requires exact name/start_ns/end_ns fields')
            entry = TemporalPartition(**entry)
        validate_partition(dataset, entry)
        partitions.append(entry)
    names = tuple(p.name for p in partitions)
    if names not in (('train', 'validation', 'test'),
                     ('train', 'validation', 'calibration', 'test')):
        raise ValueError('Expected ordered train/validation/[calibration]/test partitions')
    if any(left.end_ns > right.start_ns for left, right in zip(partitions, partitions[1:])):
        raise ValueError('Chronological partitions must not overlap')
    if any(right.start_ns - left.end_ns < embargo_ns
           for left, right in zip(partitions, partitions[1:])):
        raise ValueError('Chronological partition gap is smaller than the declared embargo')
    return tuple(partitions)
