"""Bounded synthetic compute benchmark for the V2 arms and comparators (development only).

Generates a deterministic synthetic two-channel 1-minute series with the V1 GOES
dimensions (82 training days, 10 validation days, 120/30/30 spec), then times
short schedules of every controlled arm, the TCN and the quantile-linear
comparator, each in its own subprocess so ``ru_maxrss`` is a per-job peak.
It never reads scientific data, never builds a test partition and trains
nothing to convergence. Projections in the output are extrapolations from the
measured per-epoch times, labelled as such, not measurements.

Usage::

    python scripts/benchmark_v2_feasibility.py --out results/v2_m4a/benchmark.json
"""
import argparse
import json
import os
from pathlib import Path
import platform
import resource
import statistics
import subprocess
import sys
import tempfile
import time

import numpy as np

NS = 1_000_000_000
MINUTE = 60
LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)
# First proposed V2.1 paired seed (docs/V2_EXPERIMENTAL_PROTOCOL.md on research/v2-independent-validation).
SEED = 1261866429
# Proposed V2.1 schedule used only for extrapolation (PROPOSED - REQUIRES APPROVAL).
PROPOSED = dict(ssl_epochs=8, warmup_epochs=8, downstream_epochs=15, linear_epochs=100, linear_lambdas=5)
JOBS = ('ssl', 'jepa_finetune', 'jepa_frozen', 'supervised', 'supervised_extra_updates', 'random_frozen',
        'tcn', 'quantile_linear', 'microbench')


def _peak_rss_bytes():
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == 'darwin' else peak * 1024)


def synthetic_partitions(train_days, validation_days):
    """Deterministic positive log-AR(1) series with bursts; complete masks; no test partition."""
    from solar_flare_jepa.forecasting.contracts import ForecastSpec, TimeSeriesDataset
    from solar_flare_jepa.forecasting.splitting import TemporalPartition
    from solar_flare_jepa.forecasting.windows import build_partition_windows
    rows = (train_days + validation_days) * 1440
    rng = np.random.default_rng(20261010)
    logs = np.empty((rows, 2))
    logs[0] = (-7.5, -6.3)
    noise = rng.standard_normal((rows, 2)) * (0.02, 0.015)
    for t in range(1, rows):
        logs[t] = logs[t - 1] + 0.01 * ((-7.5, -6.3) - logs[t - 1]) + noise[t]
    bursts = rng.choice(rows - 120, size=rows // 2000, replace=False)
    for start in bursts:
        logs[start:start + 60] += np.linspace(0, 1, 60)[:, None] * rng.uniform(0.3, 1.5)
    values = 10. ** logs
    ticks = np.arange(rows, dtype=np.int64)
    mask = np.ones_like(values, bool)
    names, units = ('xrsa_flux', 'xrsb_flux'), ('W/m2', 'W/m2')
    data = TimeSeriesDataset('v2_m4a_synthetic', 'synthetic_fixture', ticks * MINUTE * NS,
                             (ticks + 1) * MINUTE * NS, values, mask, values, mask.copy(), names, names, units,
                             units, MINUTE, availability_policy='bin_end_earliest')
    spec = ForecastSpec(MINUTE, 120, 30, names, names, units, units, stride_steps=30, transform='log10',
                        feature_reference=(1., 1.), target_reference=(1., 1.), target_minimum=(0., 0.),
                        availability_mode='retrospective_bin_end', eligibility_policy='complete')
    split = train_days * 1440 * MINUTE * NS
    end = rows * MINUTE * NS
    return {name: build_partition_windows(data, spec, TemporalPartition(name, a, b))
            for name, a, b in (('train', 0, split), ('validation', split, end))}


def _jepa_config(args, **changes):
    from solar_flare_jepa.training.jepa import JepaConfig
    # V1 confirmatory architecture (configs/experiments/v1_models.json), proposed for V2 J/S/B.
    values = dict(patch_steps=5, width=32, depth=3, heads=4, predictor_depth=2, mlp_ratio=4, head_hidden=128,
                  dropout=0.0, ema_start=0.996, ema_end=1.0, quantiles=LEVELS, batch_size=256, lr=1e-3,
                  weight_decay=1e-4, gradient_clip=1.0, seed=SEED, max_train_windows=args.max_train_windows,
                  threads=args.threads, jepa_loss='smooth_l1', context_block_mask=True, context_mask_patches=4,
                  monitor_windows=2048)
    values.update(changes)
    return JepaConfig(**values)


def _schedule(arm, args):
    from solar_flare_jepa.training.controlled import SSL_ARMS, TrainingSchedule
    return TrainingSchedule(arm=arm, pretrain_epochs=args.ssl_epochs if arm in SSL_ARMS else 0,
                            warmup_epochs=args.ssl_epochs if arm == 'supervised_extra_updates' else 0,
                            downstream_epochs=args.downstream_epochs, early_stopping_patience=None,
                            train_loss='dex_pinball_equal_channel_v2',
                            selection_metric='dex_pinball_equal_channel_v2',
                            diagnostic_metrics=('normalized_pinball_v1',))


def _phase_summary(record):
    phases = []
    for phase in record['budget']['phases'] if 'budget' in record else []:
        steps = phase.get('optimizer_steps') or 0
        epochs = phase.get('epochs_executed') or 0
        phases.append(dict(phase=phase['phase'], epochs=epochs, optimizer_steps=steps,
                           wall_seconds=phase['wall_seconds'],
                           seconds_per_epoch=phase['wall_seconds'] / epochs if epochs else None,
                           seconds_per_step_incl_overhead=phase['wall_seconds'] / steps if steps else None))
    epochs = [dict(phase=h['phase'], epoch=h['epoch'], wall_seconds=h['wall_seconds'], steps=h.get('steps'))
              for h in record.get('history', []) if 'wall_seconds' in h]
    return phases, epochs


def _time_predict(model, validation):
    began = time.perf_counter()
    model.predict(validation.context, validation.targets.grid)
    return time.perf_counter() - began


def run_job(job, args, workdir):
    import torch
    from solar_flare_jepa.training import comparators, controlled
    baseline_rss = _peak_rss_bytes()
    began = time.perf_counter()
    windows = synthetic_partitions(args.train_days, args.validation_days)
    train, validation = windows['train'].training_slice, windows['validation']
    out = dict(job=job, data_seconds=time.perf_counter() - began, rss_after_imports_bytes=baseline_rss,
               rss_after_data_bytes=_peak_rss_bytes(), validation_origins=len(validation.context.origin_ids))
    ssl_path = Path(workdir) / 'ssl.pt'
    if job == 'ssl':
        config = controlled.ControlledConfig(_jepa_config(args), _schedule('jepa_finetune', args))
        artifact = controlled.pretrain_controlled(train, config)
        artifact.save(ssl_path)
        budget = artifact.record['budget']
        out.update(phases=[dict(phase='pretrain', epochs=budget['epochs_executed'],
                                optimizer_steps=budget['optimizer_steps'], wall_seconds=budget['wall_seconds'],
                                seconds_per_epoch=budget['wall_seconds'] / budget['epochs_executed'],
                                seconds_per_step_incl_overhead=budget['wall_seconds'] / budget['optimizer_steps'])],
                   train_windows=artifact.record['identity']['train_windows'],
                   artifact_bytes=ssl_path.stat().st_size)
    elif job in controlled.ARMS:
        config = controlled.ControlledConfig(_jepa_config(args), _schedule(job, args))
        reuse = controlled.PretrainingArtifact.load(ssl_path) if job in controlled.SSL_ARMS else None
        model = controlled.fit_controlled(train, validation, config, pretraining=reuse)
        out['phases'], out['epochs'] = _phase_summary(model.record)
        out.update(parameters=model.record['parameters'], train_windows=model.record['train_windows'],
                   budget_totals=model.record['budget']['totals'], selection=model.record['selection'],
                   predict_validation_seconds=_time_predict(model, validation))
        path = Path(workdir) / f'{job}.pt'
        model.save(path)
        out['checkpoint_bytes'] = path.stat().st_size
    elif job == 'tcn':
        config = comparators.TcnConfig(width=32, kernel_size=3, dilations=(1, 2, 4, 8, 16, 32), dropout=0.0,
                                       seed=SEED, threads=args.threads, batch_size=256, lr=1e-3, weight_decay=1e-4,
                                       gradient_clip=1.0, quantiles=LEVELS, max_train_windows=args.max_train_windows)
        schedule = comparators.ComparatorSchedule(
            downstream_epochs=args.downstream_epochs, early_stopping_patience=None,
            train_loss='dex_pinball_equal_channel_v2', selection_metric='dex_pinball_equal_channel_v2',
            diagnostic_metrics=('normalized_pinball_v1',))
        model = comparators.fit_tcn(train, validation, config, schedule)
        out['phases'], out['epochs'] = _phase_summary(model.record)
        out.update(parameters=sum(p.numel() for p in model.model.parameters()),
                   receptive_field_bins=comparators.receptive_field(config),
                   train_windows=model.record['train_windows'],
                   predict_validation_seconds=_time_predict(model, validation))
        path = Path(workdir) / 'tcn.pt'
        model.save(path)
        out['checkpoint_bytes'] = path.stat().st_size
    elif job == 'quantile_linear':
        config = comparators.QuantileLinearConfig(
            lambdas=(0.0, 0.001, 0.01, 0.1, 1.0), lr=0.01, batch_size=256, epochs=args.linear_epochs, seed=SEED,
            threads=args.threads, gradient_clip=None, quantiles=LEVELS, max_train_windows=args.max_train_windows,
            train_loss='dex_pinball_equal_channel_v2', selection_metric='dex_pinball_equal_channel_v2')
        fit_began = time.perf_counter()
        model = comparators.fit_quantile_linear(train, validation, config)
        out.update(fit_wall_seconds=time.perf_counter() - fit_began, lambdas=len(config.lambdas),
                   epochs_per_lambda=config.epochs, parameters=sum(p.numel() for p in model.model.parameters()),
                   train_windows=model.record['train_windows'],
                   lambda_candidates=[{k: c.get(k) for k in ('lambda', 'validation_metric', 'wall_seconds',
                                                              'optimizer_steps') if k in c}
                                      for c in model.record['lambda_candidates']],
                   predict_validation_seconds=_time_predict(model, validation))
        path = Path(workdir) / 'quantile_linear.pt'
        model.save(path)
        out['checkpoint_bytes'] = path.stat().st_size
    elif job == 'microbench':
        out['microbench'] = microbench(train.spec, args)
    else:
        raise ValueError(f'Unknown job {job!r}')
    out['peak_rss_bytes'] = _peak_rss_bytes()
    out['torch_threads'] = torch.get_num_threads()
    return out


def microbench(spec, args):
    """Isolated forward+backward+clip+AdamW step times on random batches (no data loading/validation)."""
    import torch
    from solar_flare_jepa.training import comparators
    from solar_flare_jepa.training.jepa import build_jepa_model
    from solar_flare_jepa.training.losses import forecast_loss
    tcn_config = comparators.TcnConfig(width=32, kernel_size=3, dilations=(1, 2, 4, 8, 16, 32), dropout=0.0,
                                       seed=SEED, threads=1, batch_size=256, lr=1e-3, weight_decay=1e-4,
                                       gradient_clip=1.0, quantiles=LEVELS, max_train_windows=None)
    linear_config = comparators.QuantileLinearConfig(
        lambdas=(0.0,), lr=0.01, batch_size=256, epochs=1, seed=SEED, threads=1, gradient_clip=None,
        quantiles=LEVELS, max_train_windows=None, train_loss='dex_pinball_equal_channel_v2',
        selection_metric='dex_pinball_equal_channel_v2')
    builders = dict(
        jepa_full_finetune=lambda: (lambda m: (m, [m.encoder, m.predictor, m.head]))(
            build_jepa_model(spec, _jepa_config(args))),
        jepa_head_only=lambda: (lambda m: (m, [m.head]))(build_jepa_model(spec, _jepa_config(args))),
        tcn=lambda: (lambda m: (m, [m]))(comparators.build_tcn(spec, tcn_config)),
        quantile_linear=lambda: (lambda m: (m, [m]))(comparators.build_quantile_linear(spec, linear_config)))
    generator = torch.Generator().manual_seed(0)
    batch = 256
    cpu_batch = (torch.randn(batch, spec.context_steps, 2, generator=generator),
                 torch.ones(batch, spec.context_steps, 2, dtype=torch.bool),
                 torch.randn(batch, spec.horizon_steps, 2, generator=generator),
                 torch.ones(batch, spec.horizon_steps, 2, dtype=torch.bool))
    sync = dict(cpu=lambda: None, mps=lambda: torch.mps.synchronize(), cuda=lambda: torch.cuda.synchronize())
    results = []
    for device, threads in [(d, t) for d in args.micro_devices for t in args.micro_threads]:
        torch.set_num_threads(threads)
        features, mask, targets, target_mask = (x.to(device) for x in cpu_batch)
        for name, build in builders.items():
            torch.manual_seed(0)
            model, trainable = build()
            model.to(device)
            parameters = [p for module in trainable for p in module.parameters()]
            selected = {id(p) for p in parameters}
            for parameter in model.parameters():  # frozen modules receive no gradient, as in train_downstream
                parameter.requires_grad_(id(parameter) in selected)
            optimizer = torch.optim.AdamW(parameters, lr=1e-3, weight_decay=1e-4)
            model.train()
            times = []
            for step in range(args.micro_warmup + args.micro_steps):
                sync[device]()
                began = time.perf_counter()
                optimizer.zero_grad(set_to_none=True)
                loss = forecast_loss('dex_pinball_equal_channel_v2', model.forecast(features, mask), targets,
                                     target_mask, LEVELS, (0.3, 0.4))
                loss.backward()
                torch.nn.utils.clip_grad_norm_(parameters, 1.0)
                optimizer.step()
                sync[device]()
                if step >= args.micro_warmup:
                    times.append(time.perf_counter() - began)
            results.append(dict(model=name, device=device, threads=threads, batch_size=batch, warmup_steps=args.micro_warmup,
                                timed_steps=len(times), median_seconds=statistics.median(times),
                                p90_seconds=float(np.quantile(times, 0.9)), min_seconds=min(times),
                                trainable_parameters=sum(p.numel() for p in parameters)))
    return results


def environment():
    import torch
    info = dict(python=sys.version.split()[0], platform=platform.platform(), machine=platform.machine(),
                processor=platform.processor(), cpu_count=os.cpu_count(), torch=torch.__version__,
                numpy=np.__version__, device='cpu', precision='float32',
                mps_available=bool(torch.backends.mps.is_available()),
                cuda_available=bool(torch.cuda.is_available()))
    if sys.platform == 'darwin':
        for key in ('hw.model', 'machdep.cpu.brand_string', 'hw.memsize', 'hw.perflevel0.physicalcpu',
                    'hw.perflevel1.physicalcpu'):
            try:
                info[key] = subprocess.run(['sysctl', '-n', key], capture_output=True, text=True,
                                           check=True).stdout.strip()
            except (OSError, subprocess.CalledProcessError):
                info[key] = None
    return info


def project(results):
    """EXTRAPOLATED wall seconds per job under the proposed schedule from measured epoch times.

    A phase of N epochs is projected as first epoch + (N - 1) x last measured epoch,
    so one-off warm-up cost is counted once; with a single measured epoch it is
    N x that epoch (conservative). Epoch times include validation and monitoring.
    Data preparation is reported separately and added once per job.
    """
    def phase_seconds(job, phase, epochs):
        measured = [e['wall_seconds'] for e in results.get(job, {}).get('epochs', []) if e['phase'] == phase]
        if not measured:
            return None
        return measured[0] + (epochs - 1) * measured[-1]

    projection = dict(status='EXTRAPOLATED_NOT_MEASURED', schedule=PROPOSED,
                      method='first epoch + (N-1) x last epoch; data preparation added once per job', seconds={})
    for job in ('jepa_finetune', 'jepa_frozen', 'supervised', 'supervised_extra_updates', 'random_frozen', 'tcn'):
        downstream = phase_seconds(job, 'downstream', PROPOSED['downstream_epochs'])
        if downstream is None:
            continue
        seconds = downstream + results[job]['data_seconds']
        if job == 'supervised_extra_updates':
            seconds += phase_seconds(job, 'supervised_warmup', PROPOSED['warmup_epochs']) or 0.
        projection['seconds'][f'{job}_job_excluding_ssl'] = seconds
    ssl = phase_seconds('ssl', 'pretrain', PROPOSED['ssl_epochs'])
    if ssl is not None:
        projection['seconds']['ssl_phase'] = ssl
    linear = results.get('quantile_linear')
    if linear:
        per_lambda = [c['wall_seconds'] for c in linear['lambda_candidates']]
        steady = per_lambda[-1] * PROPOSED['linear_epochs'] / linear['epochs_per_lambda']
        projection['seconds']['quantile_linear_per_lambda'] = steady
        projection['seconds']['quantile_linear_5_lambdas'] = (
            linear['data_seconds'] + per_lambda[0] - per_lambda[-1] + PROPOSED['linear_lambdas'] * steady)
    return projection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--out', type=Path)
    parser.add_argument('--job', choices=JOBS)
    parser.add_argument('--jobs', nargs='+', choices=JOBS, default=list(JOBS))
    parser.add_argument('--workdir', type=Path)
    parser.add_argument('--train-days', type=int, default=82)
    parser.add_argument('--validation-days', type=int, default=10)
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--max-train-windows', type=int, default=20000)
    parser.add_argument('--ssl-epochs', type=int, default=1)
    parser.add_argument('--downstream-epochs', type=int, default=2)
    parser.add_argument('--linear-epochs', type=int, default=2)
    parser.add_argument('--micro-threads', type=int, nargs='+', default=[1, 4, 8])
    parser.add_argument('--micro-devices', nargs='+', choices=('cpu', 'mps', 'cuda'), default=['cpu'],
                        help='microbench devices; non-CPU timings are informational (the protocol is CPU-only)')
    parser.add_argument('--micro-warmup', type=int, default=5)
    parser.add_argument('--micro-steps', type=int, default=30)
    parser.add_argument('--timeout', type=int, default=1800, help='per-job subprocess timeout in seconds')
    args = parser.parse_args(argv)
    if args.job:
        print(json.dumps(run_job(args.job, args, args.workdir)))
        return 0
    if args.out is None:
        parser.error('--out is required')
    if args.out.exists():
        parser.error(f'{args.out} exists; benchmark outputs are never overwritten')
    passthrough = [f'--{k}={v}' for k, v in (('train-days', args.train_days),
                                              ('validation-days', args.validation_days),
                                              ('threads', args.threads),
                                              ('max-train-windows', args.max_train_windows),
                                              ('ssl-epochs', args.ssl_epochs),
                                              ('downstream-epochs', args.downstream_epochs),
                                              ('linear-epochs', args.linear_epochs),
                                              ('micro-warmup', args.micro_warmup),
                                              ('micro-steps', args.micro_steps))]
    passthrough += ['--micro-threads'] + [str(x) for x in args.micro_threads]
    passthrough += ['--micro-devices'] + list(args.micro_devices)
    jobs = [j for j in JOBS if j in args.jobs]
    if any(j in ('jepa_finetune', 'jepa_frozen') for j in jobs) and 'ssl' not in jobs:
        parser.error('JEPA arms reuse the ssl job artifact; include ssl')
    results, failures = {}, {}
    began = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix='v2_m4a_bench_') as workdir:
        for job in jobs:
            command = [sys.executable, __file__, '--job', job, '--workdir', workdir] + passthrough
            print(f'[benchmark] {job} ...', file=sys.stderr, flush=True)
            try:
                completed = subprocess.run(command, capture_output=True, text=True, timeout=args.timeout)
            except subprocess.TimeoutExpired:
                failures[job] = f'timeout after {args.timeout} s'
                continue
            if completed.returncode:
                failures[job] = completed.stderr[-2000:]
                continue
            results[job] = json.loads(completed.stdout.strip().splitlines()[-1])
    report = dict(kind='solarjepa_v2_m4a_compute_benchmark', schema_version=1,
                  status='SYNTHETIC_DEVELOPMENT_BENCHMARK', environment=environment(),
                  settings=dict(train_days=args.train_days, validation_days=args.validation_days,
                                cadence_seconds=MINUTE, context_steps=120, horizon_steps=30, stride_steps=30,
                                threads=args.threads, batch_size=256, max_train_windows=args.max_train_windows,
                                ssl_epochs=args.ssl_epochs, downstream_epochs=args.downstream_epochs,
                                linear_epochs=args.linear_epochs, seed=SEED, precision='float32', device='cpu',
                                train_loss='dex_pinball_equal_channel_v2',
                                diagnostic_metric='normalized_pinball_v1',
                                rss_scope='per-job subprocess ru_maxrss (process high-water mark)'),
                  results=results, failures=failures, projection=project(results),
                  total_wall_seconds=time.perf_counter() - began)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open('x') as stream:
        json.dump(report, stream, indent=1, sort_keys=True)
    print(json.dumps(dict(out=str(args.out), failures=sorted(failures)), indent=1))
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
