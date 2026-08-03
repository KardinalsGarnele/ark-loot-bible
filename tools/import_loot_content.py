#!/usr/bin/env python3
import argparse,json
from ark_loot_bible.loot_content import import_loot_manifest
p=argparse.ArgumentParser();p.add_argument("manifest");p.add_argument("--commit",action="store_true")
a=p.parse_args();r=import_loot_manifest(a.manifest,commit=a.commit);print(json.dumps(r,indent=2))
raise SystemExit(0 if r["status"] in {"VALIDATED","COMPLETED","NO_CHANGES"} else 1)
