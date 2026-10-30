"""Common v6 scorer for both versions; no fitting or model selection."""
import json,pathlib
import numpy as np,pandas as pd
from ml import quality
ROOT=pathlib.Path('/content/fra-v6-verify'); OUT=pathlib.Path('/content/fra-seasonal-results')
half=pd.read_csv(ROOT/'data/ground_truth/dfld_half_hourly.csv.gz',dtype={'od':str})
local=pd.to_datetime(half.date_local)+pd.to_timedelta(half.hour_local,unit='h')+pd.to_timedelta(half.minute_local,unit='m')
half['time']=local.dt.tz_localize('Europe/Berlin',ambiguous='NaT',nonexistent='NaT').dt.tz_convert('UTC');half=half.dropna(subset=['time'])
ms={v:json.loads((OUT/v/'manifest.json').read_text()) for v in ('v5','v6')}
assert ms['v5']['data_sha256']==ms['v6']['data_sha256']
records=[];events={};parity=[];checks=[]
reference=json.loads((ROOT/'reference-quality.json').read_text()); keys=['issue_time','time','lead_h']
for month in ['2026-01','2026-04','2026-07']:
    frames={v:pd.read_parquet(OUT/v/f'{month}-predictions.parquet').sort_values(keys).reset_index(drop=True) for v in ('v5','v6')}
    assert ms['v5']['runs'][month]['training_keys_sha256']==ms['v6']['runs'][month]['training_keys_sha256'],'Training keys/labels differ'
    pd.testing.assert_frame_equal(frames['v5'][keys+['y_od','y_r18']],frames['v6'][keys+['y_od','y_r18']])
    events[month]={}
    for target,y,p,r,b in [('od','y_od','p_od25','rule_od25','od_at_issue'),('r18','y_r18','p_18_usable','rule_18_usable','persistence_18')]:
        eligible=np.ones(len(frames['v5']),dtype=bool)
        for v in ('v5','v6'): eligible &= frames[v][[y,p,r,b]].notna().all(axis=1).to_numpy()
        for version in ('v5','v6'):
            frame=frames[version].loc[eligible].copy()
            for row in quality.skill(frame,target):
                sub=frame[frame.lead_h.eq(row['lead_h'])]
                assert row['n']==len(sub)
                assert np.isclose(((sub[p]-sub[y])**2).mean(),row['model_brier'],rtol=0,atol=1e-12)
                assert np.isclose(((sub[p]>=.5)==sub[y]).mean(),row['model_acc'],rtol=0,atol=1e-12)
                for method,prefix in [('blend','model'),('raw','raw_model'),('rules','rule'),('persistence','persistence')]:
                    records.append(dict(month=month,version=version,target=target,method=method,lead_h=row['lead_h'],n=row['n'],accuracy=row[prefix+'_acc'],brier=row[prefix+'_brier'],changed_n=row['change_n'],changed_accuracy=row[prefix+'_change_acc']))
        ref=next(f for f in reference['folds'] if f['month']==month)['out_of_sample'][target]
        for actual,expected in zip(quality.skill(frames['v6'],target),ref):
            for field in ('model_acc','model_brier','raw_model_acc','raw_model_brier'):
                parity.append(dict(month=month,target=target,lead_h=actual['lead_h'],field=field,n_match=actual['n']==expected['n'],actual=actual[field],reference=expected[field],delta=actual[field]-expected[field],within_1e_9=abs(actual[field]-expected[field])<1e-9))
    for version in ('v5','v6'):
        f=frames[version]
        events[month][version]={'next_change':quality.next_change_timing(f,half),'unique_changes':quality.od_change_events(f,half),'r18':quality.r18_events(f)}
        f.to_csv(OUT/version/f'{month}-prediction-traces.csv',index=False)
    checks.append({'month':month,'test_rows':len(frames['v5']),'training_keys_and_labels_identical':True,'test_keys_and_labels_identical':True})
    print('MATCHED_SEASON_AUDIT_PASS',month,len(frames['v5']),flush=True)
table=pd.DataFrame(records);table.to_csv(OUT/'seasonal_metrics.csv',index=False)
pd.DataFrame(parity).to_csv(OUT/'reference_parity.csv',index=False)
(OUT/'event_metrics.json').write_text(json.dumps(events,indent=2,default=str))
summary={'months':['2026-01','2026-04','2026-07'],'checks':checks,'same_raw_data_hashes':True,'v6_reference_parity_all':all(r['within_1e_9'] and r['n_match'] for r in parity),'metric_rows':len(table),'scorer':'v6 quality.py for both versions; complete windows','limitations':['Reused historical development months; not untouched forward evaluation.','No tuning or seasonal model selection from these results.','R18 labels are weather-rule proxies.','Version-specific feature construction differs; raw data and train/test keys and labels match.','Lead rows and 48-hour windows overlap; no independent-row significance claim.']}
(OUT/'audit.json').write_text(json.dumps(summary,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
plt.rcParams['svg.fonttype']='none'
fig,axes=plt.subplots(1,3,figsize=(12,4),sharey=True)
for ax,month in zip(axes,summary['months']):
    for version in ('v5','v6'):
        s=table[(table.month==month)&(table.version==version)&(table.target=='od')&(table.method=='blend')]
        ax.plot(s.lead_h,s.brier,'o-',label=version)
    ax.set_title(month);ax.set_xticks([1,6,24,48]);ax.set_xlabel('Lead (hours)');ax.grid(alpha=.2)
axes[0].set_ylabel('OD Brier (lower is better)');axes[-1].legend();fig.suptitle('Fresh seasonal v5 / v6 comparison - matched rows; historical development data')
fig.tight_layout();fig.savefig(OUT/'seasonal_comparison.svg');fig.savefig(OUT/'seasonal_comparison.png',dpi=150)
print('SEASONAL_OD_RESULTS',table[(table.target=='od')&(table.method=='blend')].to_csv(index=False),flush=True)
print('SEASONAL_REFERENCE_PARITY',summary['v6_reference_parity_all'],flush=True)
print('SEASONAL_AUDIT_COMPLETE',flush=True)
