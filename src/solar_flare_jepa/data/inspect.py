"""Schema inspection only: deliberately no guessed instrument calibration."""
from dataclasses import asdict, is_dataclass
import json
from pathlib import Path
import numpy as np
from .download import sha256_file


def json_value(value):
    if isinstance(value, bytes):
        return value.decode('utf-8', errors='replace')
    if isinstance(value, np.ndarray):
        return [json_value(v) for v in value.tolist()] if value.ndim else json_value(value.item())
    if isinstance(value, np.generic):
        return json_value(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, dict):
        return {str(k): json_value(v) for k,v in value.items()}
    if isinstance(value, (tuple, list)):
        return [json_value(v) for v in value]
    if is_dataclass(value):
        return json_value(asdict(value))
    return value


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_value(value), indent=2, allow_nan=False, default=str)+'\n')


def inspect_file(path: Path) -> dict:
    path = Path(path)
    report = dict(path=str(path), bytes=path.stat().st_size, sha256=sha256_file(path),
                  status='metadata_only_not_science_validation')
    suffix = path.suffix.lower()
    if suffix == '.nc':
        import xarray as xr
        with xr.open_dataset(path, decode_cf=False, engine='netcdf4') as ds:
            report.update(format='NetCDF', attrs=json_value(ds.attrs), variables={
                name: dict(shape=list(var.shape), dims=list(var.dims), dtype=str(var.dtype),
                           attrs=json_value(var.attrs)) for name,var in ds.variables.items()})
    elif suffix in {'.fits', '.fit', '.fts'}:
        from astropy.io import fits
        with fits.open(path, memmap=True) as hdus:
            report.update(format='FITS', hdus=[dict(name=hdu.name,
                header=[(card.keyword, str(card.value), card.comment) for card in hdu.header.cards],
                columns=[dict(name=c.name, format=c.format, unit=c.unit)
                         for c in getattr(hdu, 'columns', [])]) for hdu in hdus])
    elif suffix == '.cdf':
        import cdflib
        cdf = cdflib.CDF(path)
        info = cdf.cdf_info()
        report.update(format='CDF', attrs=json_value(cdf.globalattsget()), variables={
            name: dict(inquiry=json_value(cdf.varinq(name)), attrs=json_value(cdf.varattsget(name)))
            for name in info.zVariables + info.rVariables})
    else:
        raise ValueError(f'Unsupported extension {suffix}; no automatic format guessing')
    return report
