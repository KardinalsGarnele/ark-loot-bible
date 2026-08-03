#!/usr/bin/env python3
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'packages/importer'))
from ark_loot_bible_importer import IngestionEngine
from ark_loot_bible_importer.adapters import ADAPTERS
p=argparse.ArgumentParser(description='Validate or stage an import without canonical promotion.')
p.add_argument('input',type=Path); p.add_argument('--adapter',choices=sorted(ADAPTERS),default='canonical-entity-csv-v1'); p.add_argument('--db',type=Path,default=ROOT/'database/generated/ark_loot_bible.sqlite'); p.add_argument('--commit',action='store_true')
a=p.parse_args(); result=IngestionEngine(a.db).run(a.input,a.adapter,commit=a.commit); print(json.dumps(result.to_dict(),indent=2))
