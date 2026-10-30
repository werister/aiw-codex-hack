// Generated from ml/models/forecast.joblib (first tree of the operating-direction model). Do not edit by hand.
export const TREE = {
 "n_trees": 80,
 "tree_index": 0,
 "n_leaves": 15,
 "n_nodes": 29,
 "learning_rate": 0.08,
 "max_leaf_nodes": 15,
 "baseline": 0.6010683291068342,
 "version": "walk-forward-v6",
 "trained_through": "2026-10-29T18:00:00+00:00",
 "class_1": "west (25)",
 "note": "left branch = value <= threshold; leaf value = log-odds push toward west (positive) or east (negative)",
 "root": {
  "count": 192398,
  "lean": 7.264593948327216e-05,
  "feature": "ens_tailwind_25_mean",
  "threshold": 1.484939890885488,
  "missing_left": true,
  "left": {
   "count": 126756,
   "lean": 0.09820411343163131,
   "feature": "rule_od25_ens",
   "threshold": 0.5,
   "missing_left": false,
   "left": {
    "count": 14108,
    "lean": -0.002161145000950111,
    "feature": "geo_tailwind_25",
    "threshold": -0.5897259152289305,
    "missing_left": true,
    "left": {
     "count": 7989,
     "lean": 0.04005889369704156,
     "feature": "od_at_issue",
     "threshold": 0.5,
     "missing_left": false,
     "more": true
    },
    "right": {
     "count": 6119,
     "lean": -0.057283859359220334,
     "leaf": true,
     "value": -0.057283859359220334
    }
   },
   "right": {
    "count": 112648,
    "lean": 0.11077382675070363,
    "feature": "ens_votes_25",
    "threshold": 0.875,
    "missing_left": false,
    "left": {
     "count": 17983,
     "lean": 0.08018961079203887,
     "feature": "geo_tailwind_25",
     "threshold": -0.7766291113544515,
     "missing_left": true,
     "more": true
    },
    "right": {
     "count": 94665,
     "lean": 0.11658374547023745,
     "feature": "season_sin",
     "threshold": -0.981947190186646,
     "missing_left": false,
     "more": true
    }
   }
  },
  "right": {
   "count": 65642,
   "lean": -0.18942115823215555,
   "feature": "ens_tailwind_25_mean",
   "threshold": 2.934672356363653,
   "missing_left": false,
   "left": {
    "count": 14337,
    "lean": -0.10622248653065319,
    "feature": "dp_ns",
    "threshold": -0.1999999999999318,
    "missing_left": true,
    "left": {
     "count": 7250,
     "lean": -0.06364109167196073,
     "feature": "od_at_issue",
     "threshold": 0.5,
     "missing_left": false,
     "more": true
    },
    "right": {
     "count": 7087,
     "lean": -0.14978324746271474,
     "leaf": true,
     "value": -0.14978324746271474
    }
   },
   "right": {
    "count": 51305,
    "lean": -0.21267073149371757,
    "feature": "ens_tailwind_25_mean",
    "threshold": 4.158115558266678,
    "missing_left": false,
    "left": {
     "count": 13583,
     "lean": -0.18726172815069647,
     "leaf": true,
     "value": -0.18726172815069647
    },
    "right": {
     "count": 37722,
     "lean": -0.22182004734145247,
     "leaf": true,
     "value": -0.2218200473414525
    }
   }
  }
 },
 "source": "ml/models/forecast.joblib od model, boosting iteration 1"
};
