"""Download only the bounded public reference files in an explicit manifest."""
import argparse
import json
from pathlib import Path
from solar_flare_jepa.data.download import download_manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(download_manifest(args.manifest, Path.cwd()), indent=2))
