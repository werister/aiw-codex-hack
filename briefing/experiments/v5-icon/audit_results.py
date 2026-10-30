# Independent recomputation and historical shadow-decision evidence; no model fitting.
import hashlib, json, pathlib, shutil, subprocess, sys
import numpy as np
import pandas as pd
ROOT = pathlib.Path('/content/fra-v5-icon')
OUT = pathlib.Path('/content/fra-v5-icon-results')
all_summary = []
for lag in (6, 12):
    dest = OUT / f'lag{lag}'
    df = pd.read_parquet(dest/'per_row_traces.parquet')
    metrics = pd.read_csv(dest/'metrics.csv')
    policy = json.loads((dest/'selector_table.json').read_text())
    headline = metrics[metrics['slice'].eq('all_recorded')]
    for row in headline.itertuples():
        subset = df[df.lead_h.eq(row.lead_h)]
        values = subset[row.method].to_numpy(float)
        truth = subset.y_od.to_numpy(float)
        assert len(subset) == row.n
        assert np.isclose(((values >= .5) == truth).mean(), row.accuracy)
        assert np.isclose(((values-truth)**2).mean(), row.brier)
    # A frozen-policy transfer must be compared with a global choice on the same models.
    df['global_core'] = df['icon_blend'] if policy['global_arm'] == 'candidate' else df['baseline_blend']
    rows = []
    for lead in (1, 6, 24, 48):
        sub = df[df.lead_h.eq(lead)].copy()
        for method in ('baseline_blend','icon_blend','equalblend','selector','global_core','selector_frozen','global_arm','p_frozen_baseline','p_frozen_candidate','persistence','rules'):
            rows.append(dict(lag=lag,lead_h=lead,method=method,n=len(sub),accuracy=float(((sub[method]>=.5)==sub.y_od).mean()),brier=float(((sub[method]-sub.y_od)**2).mean())))
    summary = pd.DataFrame(rows)
    summary.to_csv(dest/'audited_headline.csv',index=False)
    all_summary.append(summary)
    # Paired whole-issue-day resampling preserves within-day rows and candidate pairing.
    cis = []
    for lead in (6,24,48):
        sub = df[df.lead_h.eq(lead)].copy()
        sub['day'] = pd.to_datetime(sub.issue_time,utc=True).dt.tz_convert('Europe/Berlin').dt.date
        for candidate,reference in [('icon_blend','baseline_blend'),('equalblend','baseline_blend'),('selector','global_core'),('selector_frozen','global_arm')]:
            sub['delta'] = (sub[candidate]-sub.y_od)**2-(sub[reference]-sub.y_od)**2
            daily = sub.groupby('day')['delta'].agg(['sum','count'])
            rng = np.random.default_rng(42)
            starts = rng.integers(0,len(daily),size=(2000,int(np.ceil(len(daily)/7))))
            draws = ((starts[:,:,None] + np.arange(7)) % len(daily)).reshape(2000,-1)[:,:len(daily)]
            samples = daily['sum'].to_numpy()[draws].sum(axis=1)/daily['count'].to_numpy()[draws].sum(axis=1)
            low,high=np.quantile(samples,[.025,.975])
            cis.append(dict(lag=lag,lead_h=lead,candidate=candidate,reference=reference,n=len(sub),n_issue_days=len(daily),brier_delta=float(sub.delta.mean()),ci_low=float(low),ci_high=float(high),bootstrap_replicates=2000,seed=42))
    pd.DataFrame(cis).to_csv(dest/'paired_7day_bootstrap.csv',index=False)
    slices=[]
    for (lead,cell),sub in df[df.lead_h.isin([6,24,48])].groupby(['lead_h','selector_cell']):
        for method in ('baseline_blend','icon_blend','selector','global_core','selector_frozen','global_arm'):
            slices.append(dict(lag=lag,lead_h=int(lead),cell=cell,n=len(sub),method=method,brier=float(((sub[method]-sub.y_od)**2).mean()),accuracy=float(((sub[method]>=.5)==sub.y_od).mean())))
    pd.DataFrame(slices).to_csv(dest/'regime_scores.csv',index=False)
    models_sha=hashlib.sha256((dest/'models.joblib').read_bytes()).hexdigest()
    script_sha=hashlib.sha256((ROOT/'experiment_v5_icon.py').read_bytes()).hexdigest()
    cases=[]
    # Deterministic first example per validation-defined cell, never chosen by correctness.
    for row in df.sort_values(['issue_time','lead_h']).groupby('selector_cell',sort=True).head(1).itertuples():
        cases.append(dict(mode='historical shadow replay; not a deployed decision API',issue_time=str(row.issue_time),target_time=str(row.time),lead_h=int(row.lead_h),task='OD direction probability',cell=row.selector_cell,selected_arm=row.selector_arm,reason=row.selector_reason,eligible=bool(row.selector_eligible),selector_frozen_probability=float(row.selector_frozen),frozen_candidates=dict(baseline=float(row.p_frozen_baseline),icon=float(row.p_frozen_candidate)),core_candidates=dict(baseline=float(row.baseline_blend),icon=float(row.icon_blend)),observed_target_for_retrospective_scoring=float(row.y_od),models_sha256=models_sha,experiment_script_sha256=script_sha,delay_counterfactual_supported=False))
    (dest/'shadow_decision_examples.json').write_text(json.dumps(cases,indent=2))
    audit=dict(lag=lag,headline_rows_recomputed=len(headline),scored_rows=len(df),global_arm_selected_on_september=policy['global_arm'],models_sha256=models_sha,experiment_script_sha256=script_sha,limitations=['October was previously used in development; exploratory only.','Circular 7-day issue-date blocks preserve pairing; October has few blocks, so intervals remain exploratory.','No test-outcome-based policy selection.','New full-trajectory OD timing scores are not computed from label-filtered traces; do not reinterpret changed-flag accuracy as event recall.','Runway-18 labels are inferred, not actual closure logs.','BTS does not support FRA flight-level delay counterfactuals.'])
    (dest/'audit.json').write_text(json.dumps(audit,indent=2))
    print('AUDIT_PASS',lag,len(headline),'headline rows',len(df),'predictions',flush=True)
    print(summary.round(5).to_string(index=False),flush=True)
    print(pd.DataFrame(cis).round(5).to_string(index=False),flush=True)
combined=pd.concat(all_summary,ignore_index=True)
combined.to_csv(OUT/'audited_headline_all_lags.csv',index=False)
subprocess.run([sys.executable,'-m','pip','freeze'],stdout=(OUT/'requirements-lock.txt').open('w'),check=True)
shutil.copy2(ROOT/'experiment_v5_icon.py',OUT/'experiment_v5_icon.py')
shutil.copy2(ROOT/'icon_supplement.py',OUT/'icon_supplement.py')
print('BOTH_LAGS_AUDITED',flush=True)

# Separate runway-18 hourly scores and complete-window sensitivity.
r18_scores=[]
r18_events=[]
for lag in (6,12):
    dest=OUT/f'lag{lag}'
    r=pd.read_parquet(dest/'r18_traces.parquet')
    for lead in (1,6,24,48):
        s=r[r.lead_h.eq(lead)]
        for method in ('p18_baseline','p18_candidate','rule_18_usable','persistence_18'):
            r18_scores.append(dict(lag=lag,lead_h=lead,method=method,n=len(s),accuracy=float(((s[method]>=.5)==s.y_r18).mean()),brier=float(((s[method]-s.y_r18)**2).mean())))
    for horizon in (1,6,24):
        eligible=[]
        for issue,g in r[r.lead_h.le(horizon)].groupby('issue_time'):
            if sorted(g.lead_h.tolist())==list(range(1,horizon+1)):
                eligible.append(g)
        for method in ('p18_baseline','p18_candidate','rule_18_usable','persistence_18'):
            tp=fp=fn=tn=0
            for g in eligible:
                actual=bool((g.y_r18<.5).any()); pred=bool((g[method]<.5).any())
                tp+=int(actual and pred); fp+=int(not actual and pred)
                fn+=int(actual and not pred); tn+=int(not actual and not pred)
            r18_events.append(dict(lag=lag,horizon_h=horizon,method=method,eligible_windows=len(eligible),total_issue_windows=107,excluded_windows=107-len(eligible),tp=tp,fp=fp,fn=fn,tn=tn,label_type='weather-rule proxy; overlapping windows'))
pd.DataFrame(r18_scores).to_csv(OUT/'r18_hourly_metrics.csv',index=False)
pd.DataFrame(r18_events).to_csv(OUT/'r18_complete_window_events.csv',index=False)
print('R18_HOURLY',pd.DataFrame(r18_scores).round(6).to_csv(index=False))
print('R18_EVENTS',pd.DataFrame(r18_events).to_csv(index=False))
# Standalone chart: matched comparisons only, separately by lag.
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(11,4),sharey=True)
for ax,lag in zip(axes,(6,12)):
    for method in ('baseline_blend','icon_blend','equalblend','selector'):
        s=combined[(combined.lag==lag)&(combined.method==method)]
        ax.plot(s.lead_h,s.brier,marker='o',label=method)
    ax.set_title(f'October exploratory / lag proxy {lag} h')
    ax.set_xlabel('Forecast lead (hours)'); ax.set_xticks([1,6,24,48]); ax.grid(alpha=.2)
axes[0].set_ylabel('OD Brier score (lower is better)')
axes[1].legend(fontsize=8)
fig.suptitle('Matched v5 vs raw ICON and scenario selection — not v6 comparison')
fig.tight_layout(); fig.savefig(OUT/'colab_comparison.svg'); fig.savefig(OUT/'colab_comparison.png',dpi=160); plt.close(fig)
print('AUDITED_CSV_BEGIN')
print(combined.to_csv(index=False))
print('AUDITED_CSV_END')
print('EVIDENCE_AUDIT_COMPLETE')
