// Generated from web/public/data/quality.json. Do not edit by hand.
export const DATA = {
 "model_version": "walk-forward-v6",
 "rows": [
  {
   "lead_h": 1,
   "n": 1416,
   "model": 0.9569209039548022,
   "rules": 0.9307909604519774,
   "same": 0.9590395480225988,
   "model_ci": [
    0.9470263747110941,
    0.9674693241115879
   ],
   "n_days": 361
  },
  {
   "lead_h": 6,
   "n": 1416,
   "model": 0.9272598870056498,
   "rules": 0.8813559322033898,
   "same": 0.8884180790960452,
   "model_ci": [
    0.9090219764063255,
    0.9435446851704585
   ],
   "n_days": 361
  },
  {
   "lead_h": 24,
   "n": 1383,
   "model": 0.918293564714389,
   "rules": 0.8770788141720897,
   "same": 0.7505422993492408,
   "model_ci": [
    0.8982783276895024,
    0.9364989271966175
   ],
   "n_days": 357
  },
  {
   "lead_h": 48,
   "n": 1338,
   "model": 0.8886397608370703,
   "rules": 0.8400597907324364,
   "same": 0.6420029895366218,
   "model_ci": [
    0.865167918326116,
    0.9102581009796533
   ],
   "n_days": 346
  }
 ],
 "test_period": "2025-11-01 to 2026-10-27",
 "source": "web/public/data/quality.json out_of_sample.od + significance.od (95% issue-day bootstrap CI)"
};
