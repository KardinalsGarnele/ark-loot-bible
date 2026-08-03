#!/usr/bin/env python3
import argparse, json
from ark_loot_bible.review import create_review_case, get_review_case, list_review_cases, review_claim, decide_case

def main():
    p=argparse.ArgumentParser(description='Review staged ARK Loot Bible claims')
    sub=p.add_subparsers(dest='cmd',required=True)
    a=sub.add_parser('open'); a.add_argument('import_record_id'); a.add_argument('--priority',type=int,default=50); a.add_argument('--assign')
    a=sub.add_parser('list'); a.add_argument('--status'); a.add_argument('--assigned-to')
    a=sub.add_parser('show'); a.add_argument('review_case_id')
    a=sub.add_parser('claim'); a.add_argument('review_case_id'); a.add_argument('claim_candidate_id'); a.add_argument('decision',choices=['ACCEPT','REJECT','CONFLICT']); a.add_argument('--reviewer',required=True); a.add_argument('--value'); a.add_argument('--notes')
    a=sub.add_parser('decide'); a.add_argument('review_case_id'); a.add_argument('decision',choices=['APPROVE','REJECT','REQUEST_CHANGES','MARK_CONFLICT']); a.add_argument('--reviewer',required=True); a.add_argument('--notes')
    x=p.parse_args()
    if x.cmd=='open': out=create_review_case(x.import_record_id,x.priority,x.assign)
    elif x.cmd=='list': out=list_review_cases(x.status,x.assigned_to)
    elif x.cmd=='show': out=get_review_case(x.review_case_id)
    elif x.cmd=='claim': out=review_claim(x.review_case_id,x.claim_candidate_id,x.reviewer,x.decision,x.value,x.notes)
    else: out=decide_case(x.review_case_id,x.reviewer,x.decision,x.notes)
    print(json.dumps(out,indent=2))
if __name__=='__main__': main()
