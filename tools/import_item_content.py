#!/usr/bin/env python3
import argparse,json
from ark_loot_bible.item_content import import_item_manifest
def main():
    p=argparse.ArgumentParser(); p.add_argument("manifest"); p.add_argument("--commit",action="store_true")
    a=p.parse_args(); r=import_item_manifest(a.manifest,commit=a.commit,actor="cli")
    print(json.dumps(r,indent=2)); return 0 if r["status"] in {"VALIDATED","COMPLETED","NO_CHANGES"} else 1
if __name__=="__main__": raise SystemExit(main())
