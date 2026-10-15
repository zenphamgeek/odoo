# Part of Insilos. See LICENSE file for full copyright and licensing details.

import datetime
import json
import os
import subprocess

RELEASE_LEVELS = [ALPHA, BETA, RELEASE_CANDIDATE, FINAL] = ['alpha', 'beta', 'candidate', 'final']
RELEASE_LEVELS_DISPLAY = {ALPHA: 'a',
                          BETA: 'b',
                          RELEASE_CANDIDATE: 'rc',
                          FINAL: ''}

# version_info format: (MAJOR, MINOR, MICRO, RELEASE_LEVEL, SERIAL)
# inspired by Python's own sys.version_info, in order to be
# properly comparable using normal operators, for example:
#  (6,1,0,'beta',0) < (6,1,0,'candidate',1) < (6,1,0,'candidate',2)
#  (6,1,0,'candidate',2) < (6,1,0,'final',0) < (6,1,2,'final',0)
# NOTE: during release, the MAJOR version can become an arbitrary string ('saas~xx')
version_info = (26, 0, 0, FINAL, 0, '')
series = serie = major_version = '.'.join(str(s) for s in version_info[:2])
version = series + RELEASE_LEVELS_DISPLAY[version_info[3]] + str(version_info[4] or '') + version_info[5]

COMPATIBLE_SERIES: frozenset[str] = frozenset({serie, '19.1', '20.0'})


def is_version_compatible(db_version: str | None) -> bool:
    if not db_version or not isinstance(db_version, str):
        return False
    clean_v = db_version.strip()
    prefix_2 = '.'.join(clean_v.split('.')[:2])
    return prefix_2 in COMPATIBLE_SERIES or any(clean_v.startswith(s + '.') or clean_v == s for s in COMPATIBLE_SERIES)

_TZ_UTC7 = datetime.timezone(datetime.timedelta(hours=7))


def _compute_build_metadata():
    here = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(here)
    build_info_path = os.path.join(here, 'build_info.json')

    if os.path.isfile(build_info_path):
        try:
            with open(build_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            b_ts = data.get('build_timestamp') or ''
            b_dt = data.get('build_datetime') or ''
            b_commit = data.get('git_commit') or data.get('build_commit') or ''
            b_tag = data.get('git_tag') or data.get('build_tag') or ''
            b_id = data.get('build_id') or (f"{b_ts}.{b_commit}" if b_ts and b_commit else '')
            if b_ts and b_dt and b_commit and b_tag and b_id:
                return b_ts, b_dt, b_commit, b_tag, b_id
        except Exception:
            pass

    b_ts = ''
    b_dt = ''
    b_commit = 'local'
    b_tag = ''

    try:
        res = subprocess.run(
            ['git', 'log', '-1', '--format=%ct|%h'],
            cwd=root_dir,
            shell=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res.returncode == 0 and '|' in res.stdout.strip():
            ct_str, short_sha = res.stdout.strip().split('|', 1)
            dt_obj = datetime.datetime.fromtimestamp(int(ct_str), tz=_TZ_UTC7)
            b_ts = dt_obj.strftime('%Y%m%d.%H%M')
            b_dt = dt_obj.strftime('%Y-%m-%d %H:%M UTC+7')
            b_commit = short_sha.strip()
    except Exception:
        pass

    if not b_ts:
        try:
            mtime = os.path.getmtime(__file__)
        except OSError:
            mtime = datetime.datetime.now(tz=_TZ_UTC7).timestamp()
        dt_obj = datetime.datetime.fromtimestamp(mtime, tz=_TZ_UTC7)
        b_ts = dt_obj.strftime('%Y%m%d.%H%M')
        b_dt = dt_obj.strftime('%Y-%m-%d %H:%M UTC+7')

    try:
        res_tag = subprocess.run(
            ['git', 'tag', '--points-at', 'HEAD'],
            cwd=root_dir,
            shell=False,
            capture_output=True,
            text=True,
            timeout=3,
        )
        if res_tag.returncode == 0 and res_tag.stdout.strip():
            tags = [t.strip() for t in res_tag.stdout.strip().splitlines() if t.strip()]
            v_tags = [t for t in tags if t.startswith(f'v{series}')]
            b_tag = v_tags[0] if v_tags else tags[0]
    except Exception:
        pass

    if not b_tag:
        b_tag = f"v{series}.{b_ts}"

    b_id = f"{b_ts}.{b_commit}"
    return b_ts, b_dt, b_commit, b_tag, b_id


build_timestamp, build_datetime, build_commit, build_tag, build_id = _compute_build_metadata()
full_version = f"{version} (Build {build_id})"


product_name = 'Insilos'
description = 'Insilos Platform Server'
long_desc = '''Insilos is an enterprise-grade sovereign industrial AI and ERP platform. The main features are accounting (analytic
and financial), stock management, sales and purchases management, tasks
automation, marketing campaigns, help desk, POS, etc. Technical features include
a distributed server, an object database, a dynamic GUI,
customizable reports, and XML-RPC interfaces.
'''
classifiers = """Development Status :: 5 - Production/Stable
License :: OSI Approved :: GNU Lesser General Public License v3

Programming Language :: Python
"""
url = 'https://insilos.com'
author = 'Insilos Core Team'
author_email = 'core@insilos.com'
license = 'LGPL-3'

nt_service_name = "insilos-server-" + series.replace('~','-')

MIN_PY_VERSION = (3, 12)
MAX_PY_VERSION = (3, 14)
MIN_PG_VERSION = 16
