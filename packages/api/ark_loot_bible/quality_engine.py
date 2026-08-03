from __future__ import annotations
import uuid
from datetime import datetime,timezone
from decimal import Decimal, ROUND_HALF_UP
from .database import connection

FORMULA_VERSION="1.0"
def now(): return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
def uid(): return f"QCALC-{uuid.uuid4().hex[:16].upper()}"

def _number(value,name):
    if value is None:return None
    value=Decimal(str(value))
    if value < 0: raise ValueError(f"{name} must be >= 0")
    return value

def calculate_quality_range(source_min,source_max,item_multiplier_percent,
                            additional_multiplier=1.0,rounding_digits=2,
                            persist=False,quality_profile_id=None,notes=None):
    values=[source_min,source_max,item_multiplier_percent]
    if any(v is None for v in values):
        return {"status":"INCOMPLETE","formula_version":FORMULA_VERSION,
                "result_min_percent":None,"result_max_percent":None,
                "missing":[n for n,v in zip(
                    ["source_quality_min_percent","source_quality_max_percent","item_quality_multiplier_percent"],values
                ) if v is None]}
    lo=_number(source_min,"source_min"); hi=_number(source_max,"source_max")
    item=_number(item_multiplier_percent,"item_multiplier_percent")
    extra=_number(additional_multiplier,"additional_multiplier")
    if hi < lo: raise ValueError("source_max must be >= source_min")
    if not 0 <= rounding_digits <= 8: raise ValueError("rounding_digits must be between 0 and 8")
    factor=(item/Decimal("100"))*extra
    quantum=Decimal("1").scaleb(-rounding_digits)
    result_min=(lo*factor).quantize(quantum,rounding=ROUND_HALF_UP)
    result_max=(hi*factor).quantize(quantum,rounding=ROUND_HALF_UP)
    result={"status":"CALCULATED","formula_version":FORMULA_VERSION,
      "formula":"source_quality_percent × (item_quality_multiplier_percent / 100) × additional_multiplier",
      "source_quality_min_percent":float(lo),"source_quality_max_percent":float(hi),
      "item_quality_multiplier_percent":float(item),"additional_multiplier":float(extra),
      "result_min_percent":float(result_min),"result_max_percent":float(result_max),
      "rounding_digits":rounding_digits}
    if persist:
        run_id=uid()
        with connection() as con:
            if quality_profile_id and not con.execute(
                "SELECT 1 FROM quality_profiles WHERE quality_profile_id=?",(quality_profile_id,)
            ).fetchone(): raise KeyError("Quality profile not found")
            con.execute("""INSERT INTO quality_calculation_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
              (run_id,quality_profile_id,float(lo),float(hi),float(item),float(extra),
               float(result_min),float(result_max),rounding_digits,FORMULA_VERSION,now(),notes))
            con.commit()
        result["quality_calculation_run_id"]=run_id
    return result

def create_profile(profile_id,profile_code,display_name,source_min=None,source_max=None,
                   difficulty_multiplier=None,crate_quality_multiplier=None,rounding_digits=2,
                   verification_status="NEEDS_VERIFICATION",source_url=None,notes=None):
    if source_min is not None and source_max is not None and source_max < source_min:
        raise ValueError("source_max must be >= source_min")
    with connection() as con:
        con.execute("""INSERT INTO quality_profiles VALUES(?,?,?,?,?,?,?,?,?,?,?)
          ON CONFLICT(quality_profile_id) DO UPDATE SET profile_code=excluded.profile_code,
          display_name=excluded.display_name,source_quality_min_percent=excluded.source_quality_min_percent,
          source_quality_max_percent=excluded.source_quality_max_percent,
          difficulty_multiplier=excluded.difficulty_multiplier,
          crate_quality_multiplier=excluded.crate_quality_multiplier,
          rounding_digits=excluded.rounding_digits,verification_status=excluded.verification_status,
          source_url=excluded.source_url,notes=excluded.notes""",
          (profile_id,profile_code,display_name,source_min,source_max,difficulty_multiplier,
           crate_quality_multiplier,rounding_digits,verification_status,source_url,notes))
        con.commit()
    return get_profile(profile_id)

def get_profile(profile_id):
    with connection() as con:
        row=con.execute("SELECT * FROM quality_profiles WHERE quality_profile_id=?",(profile_id,)).fetchone()
        return dict(row) if row else None

def list_profiles():
    with connection() as con:
        return [dict(r) for r in con.execute("SELECT * FROM quality_profiles ORDER BY display_name")]

def calculate_from_profile(profile_id,item_multiplier_percent,additional_multiplier=None,persist=False,notes=None):
    profile=get_profile(profile_id)
    if not profile: raise KeyError("Quality profile not found")
    extra=additional_multiplier
    if extra is None:
        extra=(profile["difficulty_multiplier"] if profile["difficulty_multiplier"] is not None else 1.0) * \
              (profile["crate_quality_multiplier"] if profile["crate_quality_multiplier"] is not None else 1.0)
    return calculate_quality_range(profile["source_quality_min_percent"],profile["source_quality_max_percent"],
      item_multiplier_percent,extra,profile["rounding_digits"],persist,profile_id,notes)
