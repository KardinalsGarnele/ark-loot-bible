#!/usr/bin/env python3
import argparse,json
from ark_loot_bible.content_pipeline import import_map_manifest
p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--commit",action="store_true");p.add_argument("--actor",default="content-cli");a=p.parse_args();r=import_map_manifest(a.manifest,a.commit,a.actor);print(json.dumps(r,indent=2));raise SystemExit(0 if r["status"] in {"VALIDATED","COMPLETED","NO_CHANGES"} else 1)
