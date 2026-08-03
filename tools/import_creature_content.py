#!/usr/bin/env python3
import argparse,json
from ark_loot_bible.creature_content import import_creature_manifest
p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--commit",action="store_true");a=p.parse_args();r=import_creature_manifest(a.manifest,a.commit);print(json.dumps(r,indent=2));raise SystemExit(0 if r["status"] in {"VALIDATED","COMPLETED","NO_CHANGES"} else 1)
