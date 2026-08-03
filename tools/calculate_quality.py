#!/usr/bin/env python3
import argparse,json
from ark_loot_bible.quality_engine import calculate_quality_range
p=argparse.ArgumentParser()
p.add_argument("minimum",type=float);p.add_argument("maximum",type=float);p.add_argument("item_multiplier",type=float)
p.add_argument("--additional-multiplier",type=float,default=1.0);p.add_argument("--rounding-digits",type=int,default=2)
a=p.parse_args()
print(json.dumps(calculate_quality_range(a.minimum,a.maximum,a.item_multiplier,a.additional_multiplier,a.rounding_digits),indent=2))
