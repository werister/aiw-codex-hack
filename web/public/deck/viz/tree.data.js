// Generated from ml/models/forecast.joblib (first tree of the operating-direction model). Do not edit by hand.
export const TREE = {
 "n_trees": 80,
 "tree_index": 0,
 "n_leaves": 15,
 "n_nodes": 29,
 "learning_rate": 0.08,
 "max_leaf_nodes": 15,
 "baseline": 0.6115617703981753,
 "version": "walk-forward-v5",
 "trained_through": "2026-10-29T18:00:00+00:00",
 "class_1": "west (25)",
 "note": "left branch = value <= threshold; leaf value = log-odds push toward west (positive) or east (negative)",
 "root": {
  "count": 191366,
  "lean": 0.00012794179519963857,
  "feature": "ens_tailwind_25_mean",
  "threshold": 1.348702473554569,
  "missing_left": true,
  "left": {
   "count": 124577,
   "lean": 0.10127191801073013,
   "feature": "rule_od25_ens",
   "threshold": 0.5,
   "missing_left": false,
   "left": {
    "count": 12880,
    "lean": 0.0014719526265438352,
    "feature": "geo_tailwind_25",
    "threshold": -0.5382503390580646,
    "missing_left": true,
    "left": {
     "count": 7410,
     "lean": 0.04335055076824711,
     "feature": "od_at_issue",
     "threshold": 0.5,
     "missing_left": false,
     "more": true
    },
    "right": {
     "count": 5470,
     "lean": -0.05525938416139425,
     "feature": "season_cos",
     "threshold": -0.16587819893463143,
     "missing_left": true,
     "more": true
    }
   },
   "right": {
    "count": 111697,
    "lean": 0.11278004763057954,
    "feature": "ens_votes_25",
    "threshold": 0.875,
    "missing_left": false,
    "left": {
     "count": 17881,
     "lean": 0.08046594836386342,
     "feature": "geo_tailwind_25",
     "threshold": -0.7597006588600613,
     "missing_left": true,
     "more": true
    },
    "right": {
     "count": 93816,
     "lean": 0.1189390014229833,
     "leaf": true,
     "value": 0.1189390014229833
    }
   }
  },
  "right": {
   "count": 66789,
   "lean": -0.18852906946417156,
   "feature": "ens_tailwind_25_mean",
   "threshold": 2.895745945169816,
   "missing_left": false,
   "left": {
    "count": 15007,
    "lean": -0.1015129505250324,
    "feature": "dp_ns",
    "threshold": -0.39999999999997726,
    "missing_left": false,
    "left": {
     "count": 6998,
     "lean": -0.05544213507614248,
     "feature": "od_at_issue",
     "threshold": 0.5,
     "missing_left": false,
     "more": true
    },
    "right": {
     "count": 8009,
     "lean": -0.1417681092853435,
     "feature": "ecmwf_ifs025_tailwind_25",
     "threshold": -0.07331581420238416,
     "missing_left": false,
     "more": true
    }
   },
   "right": {
    "count": 51782,
    "lean": -0.21374730933361774,
    "feature": "ens_tailwind_25_mean",
    "threshold": 4.178045460562162,
    "missing_left": false,
    "left": {
     "count": 14260,
     "lean": -0.18818246011922346,
     "leaf": true,
     "value": -0.18818246011922346
    },
    "right": {
     "count": 37522,
     "lean": -0.22346306941562996,
     "leaf": true,
     "value": -0.22346306941562996
    }
   }
  }
 },
 "source": "ml/models/forecast.joblib od model, boosting iteration 1"
};
