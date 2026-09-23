"""Run the fixed review evidence jobs, each under its own <=300 s M5 supervisor."""
import argparse
import shlex
import subprocess
from pathlib import Path

import pcso_mlx_remote as remote

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['uniform', 'tilt_high31', 'tilt_linear', 'pair_parity', 'cp_nest']


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('suite', choices=('bench', 'matched', 'paired', 'power', 'tests'))
    args = ap.parse_args()
    sha = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    jobs = []
    if args.suite == 'tests':
        code = remote.ssh('cd ~/sdl-gpu-dev && printf "{}\\n" > results/exploratory/pcso_mlx_equivalence_2026-09-23.json && '
            'PCSO_GIT_SHA=' + sha + ' PCSO_MLX_EQUIV_REPORT=results/exploratory/pcso_mlx_equivalence_2026-09-23.json '
            '~/Developer/projects/structure-discovery-lab/.venv/bin/python -m pytest tests/test_pcso_mlx_sim.py -q -p no:cacheprovider '
            '> results/exploratory/pcso_mlx_tests_m5_2026-09-23.log 2>&1')
        raise SystemExit(code)
    if args.suite == 'bench':
        for name in MODELS:
            for backend, n in [('cpu', 400), ('mlx', 400), ('mlx', 10000)]:
                # Disjoint generator seeds, including the 400 and 10000 MLX samples.
                seed = 20260923 if backend == 'cpu' else 20260924 if n == 10000 else 20260926
                out = f'results/exploratory/pcso_mlx_bench_{name}_{backend}_{n}.json'
                jobs.append(['src/pcso_mlx_benchmark.py', '--model', name, '--backend', backend,
                             '--streams', str(n), '--seed', str(seed), '--max-draws', '994', '--out', out])
    else:
        configs = [('cp_nest', 128), ('tilt_linear', 128)] if args.suite == 'power' else [(n, 32) for n in MODELS[1:]] + [('cp_nest', 128)]
        for name, m in configs:
            n = 16 if args.suite == 'matched' else 200 if args.suite == 'power' else 400
            out = f'results/exploratory/pcso_mlx_{args.suite}_{name}_m{m}.json'
            job = ['tools/pcso_mlx_validate.py', '--model', name, '--streams', str(n), '--m', str(m), '--out', out]
            if args.suite == 'matched':
                job += ['--devices', 'gpu', 'cpu', '--check-drift']
            if args.suite == 'power':
                job += ['--theta1', '0.05', '--seed', '20260927']
            jobs.append(job)
            if args.suite == 'power':
                jobs.append(['src/pcso_mlx_sim.py', '--models', name, '--null-streams', '2000',
                    '--m', '128', '--theta1', '0.05', '--seed', '20260928', '--max-draws', '994',
                    '--device', 'gpu', '--out', f'results/exploratory/pcso_mlx_power_{name}_mlx_2000.json'])
    for job in jobs:
        print('START', shlex.join(job), flush=True)
        command = ('cd ~/sdl-gpu-dev && PCSO_GIT_SHA=' + sha +
                   ' ~/Developer/projects/structure-discovery-lab/.venv/bin/python ' + shlex.join(job))
        code = remote.ssh(command)
        print('END', code, flush=True)
        if code:
            raise SystemExit(code)
        if remote.leftovers():
            raise SystemExit('M5 leftovers after job')


if __name__ == '__main__':
    main()
