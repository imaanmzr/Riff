"""Copy canonical workflows into the installable skill; --check detects drift."""
import argparse
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / 'distribution/skills/riff/references'


def sync(check=False):
    differences = []
    for phase in ('planning', 'execution', 'recovery', 'routing'):
        for source in (ROOT / phase).rglob('*'):
            if not source.is_file() or '__pycache__' in source.parts or source.suffix == '.pyc': continue
            target = BUNDLE / source.relative_to(ROOT)
            if not target.exists() or target.read_bytes() != source.read_bytes():
                differences.append(str(source.relative_to(ROOT)))
                if not check:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(source, target)
    if check and differences:
        raise SystemExit('Bundled references differ: ' + ', '.join(differences))
    print(('Verified' if check else 'Synchronized') + ' canonical workflow references')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    sync(parser.parse_args().check)
