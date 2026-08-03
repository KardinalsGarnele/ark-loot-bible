#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'packages/api'))
from ark_loot_bible.promotion import preview_promotion, promote_review
p=argparse.ArgumentParser(); p.add_argument('review_case_id'); p.add_argument('--actor',default='cli-promoter'); p.add_argument('--commit',action='store_true'); p.add_argument('--db',type=Path)
a=p.parse_args()
if a.db: os.environ['ARK_LOOT_BIBLE_DB']=str(a.db)
result=promote_review(a.review_case_id,a.actor) if a.commit else preview_promotion(a.review_case_id,a.actor)
print(json.dumps(result,indent=2,sort_keys=True))
