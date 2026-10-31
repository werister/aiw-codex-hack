"""Fresh October v6 fits; execute in Colab, never against post-cutoff model weights."""
import hashlib, json, pathlib, platform, time
import joblib
import numpy as np
import pandas as pd
import sklearn
from ml import train, quality
from ml.features import FEATURES

STARTED=time.time()
ROOT=pathlib.Path(__file__).resolve().parent
OUT=pathlib.Path('/content/fra-v6-results')
OLD=pathlib.Path('/content/fra-v5-icon-results/lag6')
manifest=json.loads((ROOT/'source-manifest.json').read_text())
reference=json.loads((ROOT/'reference-quality.json').read_text())
assert train.MODEL_VERSION=='walk-forward-v6'
assert len(FEATURES)==45
frame,truth,obs,skipped=train.dataset(6)
start=pd.Timestamp('2026-10-01',tz='UTC')
end=pd.Timestamp('2026-11-01',tz='UTC')
training=frame[frame.label_available_at<start].copy()
test=frame[(frame.issue_time>=start)&(frame.issue_time<end)&(frame.label_available_at<end)].copy()
assert training.label_available_at.max()<test.issue_time.min()
assert (test.groupby('issue_time').size()==48).all()
old=pd.read_parquet(OLD/'per_row_traces.parquet')
old_manifest=json.loads((OLD/'manifest.json').read_text())
keys=['issue_time','time','lead_h']
assert not old.duplicated(keys).any() and not test.duplicated(keys).any()
match=old[keys+['y_od']].merge(test[keys+['y_od']],on=keys,validate='one_to_one',suffixes=('_v5','_v6'))
assert len(match)==len(old)==5068
np.testing.assert_array_equal(match.y_od_v5,match.y_od_v6)
restricted=training[training.issue_time>=pd.Timestamp('2025-01-01',tz='UTC')].copy()
assert len(restricted)==old_manifest['train_rows']==122280
assert frame.loc[frame.issue_time>=pd.Timestamp('2025-01-01',tz='UTC'),'issue_time'].nunique()==old_manifest['complete_issues']
assert restricted.y_od.equals(train.without_stuck_feed(restricted).y_od), 'Prior filtering differs in training'
half=pd.read_csv(ROOT/'data/ground_truth/dfld_half_hourly.csv.gz',dtype={'od':str})
local=pd.to_datetime(half.date_local)+pd.to_timedelta(half.hour_local,unit='h')+pd.to_timedelta(half.minute_local,unit='m')
half['time']=local.dt.tz_localize('Europe/Berlin',ambiguous='NaT',nonexistent='NaT').dt.tz_convert('UTC')
half=half.dropna(subset=['time'])
records=[]; audits={}; predictions={}; events={}
for name,fit_rows in [('v6_full_history',training),('v6_matched_2025plus',restricted)]:
    print('FITTING',name,len(fit_rows),'train rows',len(test),'test rows',flush=True)
    models=train.fit(fit_rows)
    models.update(version=train.MODEL_VERSION,features=FEATURES,trained_through=fit_rows.label_available_at.max().isoformat(),publication_lag_h=6,od_training_label_policy='all-recorded')
    assert models['trained_through']<test.issue_time.min().isoformat()
    assert models['od_blend_validation_period']['end']<start.isoformat()
    pred=train.predict(models,test)
    for col in ['p_od25_raw','p_od25','p_18_usable_raw','p_18_usable']:
        assert np.isfinite(pred[col]).all() and pred[col].between(0,1).all()
    pred['certainty']=100*np.minimum(abs(2*pred.p_od25-1),abs(2*pred.p_18_usable-1))
    dest=OUT/name;dest.mkdir(exist_ok=True)
    pred.to_parquet(dest/'full_48h_traces.parquet',index=False)
    joblib.dump(models,dest/'models.joblib',compress=3)
    # Compact trace includes missing targets, so complete-window event replay remains possible.
    cols=keys+['y_od','y_r18','od_at_issue','persistence_18','rule_od25','rule_18_usable','rule_od25_ens','rule_18_ens','changed_within_lead','p_od25_raw','p_od25','p_18_usable_raw','p_18_usable','certainty']
    pred[cols].to_csv(dest/'prediction_traces.csv',index=False)
    scores={target:quality.skill(pred,target) for target in ('od','r18')}
    for target,rs in scores.items():
        for row in rs:
            for method,prefix in [('blend','model'),('raw','raw_model'),('rules','rule'),('persistence','persistence')]:
                records.append(dict(experiment=name,target=target,method=method,lead_h=row['lead_h'],n=row['n'],accuracy=row[prefix+'_acc'],brier=row[prefix+'_brier'],changed_n=row['change_n'],changed_accuracy=row[prefix+'_change_acc']))
    # Independent arithmetic audit, separate from the production skill helper.
    for target,y,p,r,b in [('od','y_od','p_od25','rule_od25','od_at_issue'),('r18','y_r18','p_18_usable','rule_18_usable','persistence_18')]:
        for row in scores[target]:
            s=pred[pred.lead_h.eq(row['lead_h'])].dropna(subset=[y,p,r,b])
            assert len(s)==row['n']
            assert np.isclose(np.mean((s[p]-s[y])**2),row['model_brier'],rtol=0,atol=1e-12)
            assert np.isclose(np.mean((s[p]>=.5)==s[y]),row['model_acc'],rtol=0,atol=1e-12)
    events[name]={'next_change':quality.next_change_timing(pred,half),'unique_changes':quality.od_change_events(pred,half),'r18':quality.r18_events(pred),'certainty_reliability':quality.reliability(pred,'certainty')}
    train_keys=fit_rows[keys+['y_od','y_r18','label_available_at']].sort_values(keys).to_csv(index=False)
    (dest/'training_keys.csv').write_text(train_keys)
    audits[name]={'train_rows':len(fit_rows),'training_keys_sha256':hashlib.sha256(train_keys.encode()).hexdigest(),'test_rows':len(test),'test_issues':test.issue_time.nunique(),'train_label_end':models['trained_through'],'od_blend_validation_period':models['od_blend_validation_period'],'od_model_weight':models['od_model_weight'],'r18_model_weight':models['r18_model_weight'],'r18_validation_support':models['r18_blend_validation_support'],'model_sha256':hashlib.sha256((dest/'models.joblib').read_bytes()).hexdigest()}
    predictions[name]=pred
    print('FIT_AND_METRIC_AUDIT_PASS',name,flush=True)
    print(pd.DataFrame(scores['od'])[['lead_h','n','model_acc','model_brier','raw_model_acc','rule_acc','persistence_acc']].to_string(index=False),flush=True)

# Compare the full-history fresh fit with the committed October fold, never the all-data serving model.
fold=next(f for f in reference['folds'] if f['month']=='2026-10')
parity=[]
for target in ('od','r18'):
    actual=quality.skill(predictions['v6_full_history'],target)
    for a,b in zip(actual,fold['out_of_sample'][target]):
        assert a['lead_h']==b['lead_h'] and a['n']==b['n']
        for field in ('model_acc','model_brier','raw_model_acc','raw_model_brier','rule_acc','persistence_acc'):
            delta=a[field]-b[field]
            parity.append(dict(target=target,lead_h=a['lead_h'],field=field,actual=a[field],reference=b[field],delta=delta,within_1e_9=abs(delta)<1e-9))
pd.DataFrame(parity).to_csv(OUT/'committed_october_parity.csv',index=False)

joined=old.merge(predictions['v6_matched_2025plus'][keys+['y_od','p_od25','p_od25_raw']],on=keys,validate='one_to_one',suffixes=('_v5','_v6'))
assert len(joined)==len(old)
np.testing.assert_array_equal(joined.y_od_v5,joined.y_od_v6)
comparisons=[]
for lead in (1,6,24,48):
    s=joined[joined.lead_h.eq(lead)].copy()
    for method,col in [('v5_baseline','baseline_blend'),('v5_icon','icon_blend'),('v5_selector','selector'),('v6_matched','p_od25')]:
        comparisons.append(dict(lead_h=lead,method=method,n=len(s),accuracy=float(((s[col]>=.5)==s.y_od_v6).mean()),brier=float(((s[col]-s.y_od_v6)**2).mean())))
pd.DataFrame(comparisons).to_csv(OUT/'paired_version_comparison.csv',index=False)
# Prespecified paired circular seven-day block bootstrap, descriptive on reused October data.
intervals=[]
for lead in (1,6,24,48):
    s=joined[joined.lead_h.eq(lead)].copy()
    s['day']=pd.to_datetime(s.issue_time,utc=True).dt.tz_convert('Europe/Berlin').dt.date
    s['delta']=(s.p_od25-s.y_od_v6)**2-(s.baseline_blend-s.y_od_v6)**2
    days=s.groupby('day').delta.agg(['sum','count'])
    rng=np.random.default_rng(42);n=len(days)
    starts=rng.integers(0,n,size=(2000,int(np.ceil(n/7))))
    indices=((starts[:,:,None]+np.arange(7))%n).reshape(2000,-1)[:,:n]
    samples=days['sum'].to_numpy()[indices].sum(axis=1)/days['count'].to_numpy()[indices].sum(axis=1)
    low,high=np.quantile(samples,[.025,.975])
    intervals.append(dict(lead_h=lead,n=len(s),days=n,brier_delta_v6_minus_v5=float(s.delta.mean()),ci_low=float(low),ci_high=float(high),block_days=7,replicates=2000,seed=42))
pd.DataFrame(intervals).to_csv(OUT/'paired_7day_bootstrap.csv',index=False)
pd.DataFrame(records).to_csv(OUT/'metrics.csv',index=False)
(OUT/'event_metrics.json').write_text(json.dumps(events,indent=2,default=str))
report={'source_commit':manifest['source_commit'],'source_file_sha256':manifest['file_sha256'],'data_sha256':manifest['data_sha256'],'script_sha256':hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),'feature_rows':len(frame),'skipped_issues':skipped,'features':FEATURES,'runs':audits,'october_reference_all_48_fields_match':all(p['within_1e_9'] for p in parity),'matched_prior_v5_rows':len(joined),'python':platform.python_version(),'sklearn':sklearn.__version__,'elapsed_s':time.time()-STARTED,'limitations':['October previously influenced development; not untouched forward validation.','Refit only October, not twelve monthly folds.','Matched comparison fixes raw data, labels and rows; version-specific feature construction legitimately differs.','6 h forecast-release proxy remains unverified.','Runway-18 labels are weather proxies, not operational closures.','Circular block intervals from 27 issue days are exploratory.','No model or router promoted from these tests.']}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2,default=str))
report['limitations'].append('Earlier training keys were not exported: matched training eligibility is reconstructed from identical frozen data, date bounds, complete-issue counts and label-filter equivalence; exact old training-key hashes cannot be compared. Test keys and OD labels are exactly verified.')
(OUT/'manifest.json').write_text(json.dumps(report,indent=2,default=str))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.fonttype']='none'
fig,axes=plt.subplots(1,2,figsize=(10,4))
table=pd.DataFrame(comparisons)
for method in table.method.unique():
    s=table[table.method==method]
    axes[0].plot(s.lead_h,s.accuracy*100,'o-',label=method)
    axes[1].plot(s.lead_h,s.brier,'o-',label=method)
for ax in axes: ax.set_xticks([1,6,24,48]); ax.set_xlabel('Lead (hours)'); ax.grid(alpha=.2)
axes[0].set_ylabel('OD accuracy (%)');axes[1].set_ylabel('OD Brier (lower is better)');axes[1].legend(fontsize=8)
fig.suptitle('Matched October version comparison / 2025+ training / exploratory')
fig.tight_layout();fig.savefig(OUT/'v6_comparison.svg');fig.savefig(OUT/'v6_comparison.png',dpi=150);plt.close(fig)
print('REFERENCE_PARITY',report['october_reference_all_48_fields_match'],flush=True)
print('PAIRED_COMPARISON',pd.DataFrame(comparisons).to_csv(index=False),flush=True)
print('PAIRED_INTERVALS',pd.DataFrame(intervals).to_csv(index=False),flush=True)
print('V6_EXPERIMENT_COMPLETE',round(time.time()-STARTED,1),flush=True)
