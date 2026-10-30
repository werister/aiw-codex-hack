"""Run only in Colab: three prespecified historical seasons, no test-set tuning."""
import argparse, hashlib, json, pathlib, time
import joblib, numpy as np, pandas as pd
from ml import train
from ml.features import FEATURES
from ml.predict import probability

p=argparse.ArgumentParser();p.add_argument('--version',required=True);a=p.parse_args()
root=pathlib.Path.cwd();out=pathlib.Path('/content/fra-seasonal-results')/a.version;out.mkdir(parents=True,exist_ok=True)
started=time.time(); frame,truth,obs,skipped=train.dataset(24)
keys=['issue_time','time','lead_h']
manifest={'version':a.version,'issue_stride_h':24,'months':['2026-01','2026-04','2026-07'],'feature_rows':len(frame),'skipped':skipped,'runs':{},'source_sha256':{str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (root/'ml').rglob('*.py')},'data_sha256':{name:hashlib.sha256((root/name).read_bytes()).hexdigest() for name in ['data/ground_truth/dfld_hourly.csv','data/eddf_metar.parquet','data/openmeteo_previous_runs.parquet','data/openmeteo_previous_runs_multimodel.parquet','data/openmeteo_previous_runs_pressure.parquet']}}
for month in manifest['months']:
    period=pd.Period(month,freq='M');start=period.start_time.tz_localize('UTC');end=(period+1).start_time.tz_localize('UTC')
    fit=frame[frame.label_available_at<start].copy()
    test=frame[(frame.issue_time>=start)&(frame.issue_time<end)&(frame.label_available_at<end)].copy()
    assert len(fit)>0 and len(test)>0 and fit.label_available_at.max()<test.issue_time.min()
    assert fit.y_od.equals(train.without_stuck_feed(fit).y_od),'Training label policies differ'
    assert test.lead_h.between(1,48).all()
    assert not test.duplicated(keys).any()
    print('FITTING',a.version,month,len(fit),len(test),flush=True)
    model=train.fit(fit);pred=train.predict(model,test)
    pred['p_18_usable_raw']=probability(model['r18'],test[FEATURES])
    pred['certainty']=100*np.minimum(abs(2*pred.p_od25-1),abs(2*pred.p_18_usable-1))
    for col in ['p_od25','p_od25_raw','p_18_usable','p_18_usable_raw']:
        assert np.isfinite(pred[col]).all() and pred[col].between(0,1).all()
    cols=keys+['y_od','y_r18','od_at_issue','persistence_18','rule_od25','rule_18_usable','rule_od25_ens','rule_18_ens','changed_within_lead','p_od25','p_od25_raw','p_18_usable','p_18_usable_raw','certainty']
    pred[cols].to_parquet(out/f'{month}-predictions.parquet',index=False)
    tk=fit[keys+['y_od','y_r18','label_available_at']].sort_values(keys).to_csv(index=False)
    (out/f'{month}-training-keys.csv').write_text(tk)
    joblib.dump(model,out/f'{month}-model.joblib',compress=3)
    manifest['runs'][month]={'train_rows':len(fit),'test_rows':len(test),'train_label_end':fit.label_available_at.max().isoformat(),'training_keys_sha256':hashlib.sha256(tk.encode()).hexdigest(),'model_sha256':hashlib.sha256((out/f'{month}-model.joblib').read_bytes()).hexdigest()}
    print('SEASON_FIT_COMPLETE',a.version,month,flush=True)
manifest['sampling_note']='Deadline-limited midnight-issue seasonal check; not directly comparable with six-hourly team folds.'
manifest['elapsed_s']=time.time()-started
(out/'manifest.json').write_text(json.dumps(manifest,indent=2,default=str))
print('SEASONAL_VERSION_COMPLETE',a.version,round(time.time()-started,1),flush=True)
