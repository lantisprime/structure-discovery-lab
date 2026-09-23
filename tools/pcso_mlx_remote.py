"""Bound every M5 command and descendants to <=300 seconds; install nothing."""
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HOST = 'charltondho@10.18.8.150'
SUPERVISOR = '''import os, signal, subprocess, sys
seconds = int(sys.argv[1])
p = subprocess.Popen(sys.argv[2:], start_new_session=True)
try:
    code = p.wait(timeout=seconds)
except subprocess.TimeoutExpired:
    code = 124
finally:
    try: os.killpg(p.pid, signal.SIGKILL)
    except ProcessLookupError: pass
    p.wait()
sys.exit(code)
'''


def timeout(seconds, command):
    if not 0 < seconds <= 300:
        raise ValueError('deadline must be in (0, 300] seconds')
    code = 'exec(bytes.fromhex("' + SUPERVISOR.encode().hex() + '"))'
    return shlex.join(['/usr/bin/python3', '-c', code, str(seconds), *command])


def ssh(command, seconds=300):
    return subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', HOST,
                           timeout(seconds, ['/bin/sh', '-c', command])]).returncode


def sync(pull=False):
    # Bootstrap the tracked supervisor before rsync (its --rsync-path crosses two shells).
    target = '/Users/charltondho/sdl-gpu-dev/tools/pcso_mlx_supervisor.py'
    code = 'from pathlib import Path; p=Path(' + repr(target) + '); p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(bytes.fromhex(' + repr(SUPERVISOR.encode().hex()) + '))'
    result = ssh('/usr/bin/python3 -c ' + shlex.quote(code), 20)
    if result:
        return result
    paths = ([HOST + ':sdl-gpu-dev/results/exploratory/', str(ROOT / 'results/exploratory/') + '/']
             if pull else [str(ROOT) + '/', HOST + ':sdl-gpu-dev/'])
    return subprocess.run(['rsync', '-a', '--exclude', '.git', '--exclude', '.venv',
        '--exclude', '.pi', '--exclude', 'results', '--exclude', '__pycache__', '--exclude', '.pytest_cache',
        '--exclude', 'pcso_mlx_tests_local*', '--exclude', 'pcso_mlx_collection*',
        '--exclude', 'pcso_mlx_matched_probe*', '--exclude', '_CHECKPOINT.md',
        '--exclude', 'pcso_mlx_cpu_without_mlx.json',
        '-e', 'ssh -o BatchMode=yes -o ConnectTimeout=10',
        '--rsync-path', '/usr/bin/python3 ' + target + ' 300 rsync', *paths]).returncode


def leftovers():
    code = '''import json, os, subprocess
rows = [line.strip().split(None, 3) for line in subprocess.check_output(
    ["ps", "-axo", "pid,ppid,pgid,command"], text=True).splitlines()[1:]]
parents = {int(row[0]): int(row[1]) for row in rows}
ancestors, pid = set(), os.getpid()
while pid and pid not in ancestors:
    ancestors.add(pid)
    pid = parents.get(pid, 0)
matches = [row for row in rows if int(row[0]) not in ancestors and
           any(word in row[3] for word in ("pcso_mlx", "sdl-gpu-dev", "multiprocessing.spawn", "multiprocessing.resource_tracker"))]
print(json.dumps({"matching_processes": matches, "supervision": "<=300 seconds; process group killed on every exit"}, indent=2))
raise SystemExit(bool(matches))
'''
    encoded = 'exec(bytes.fromhex("' + code.encode().hex() + '"))'
    return ssh('/usr/bin/python3 -c ' + shlex.quote(encoded), 20)


if __name__ == '__main__':
    action = sys.argv[1]
    if action in ('sync', 'pull'):
        code = sync(action == 'pull')
    elif action == 'leftovers':
        code = leftovers()
    else:
        code = ssh(action)
    sys.exit(code)
