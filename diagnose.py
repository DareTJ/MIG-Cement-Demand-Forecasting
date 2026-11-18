"""Local conditional forecast and data-quality experiments; no site-level data exported."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from lightgbm import LGBMRegressor, LGBMClassifier
from forecast import load_data, ORIGINS, HORIZON, metrics


def matrix(train, test, weather):
    # This scenario assumes target-day pour plans are available at forecast issue.
    # Observed target-day weather is admitted ONLY in the hindsight scenario.
    cols=['site_id','region','behavior','site_capacity','planned_pour_tonnes','weekday','month']
    if weather: cols+=['rain_mm','avg_temp_c']
    a=pd.get_dummies(train[cols],dtype=float); b=pd.get_dummies(test[cols],dtype=float).reindex(columns=a.columns,fill_value=0)
    return a,b


def experiment(d):
    d=d.copy(); d['weekday']=d.date.dt.dayofweek; d['month']=d.date.dt.month
    predictions=[]
    for origin in ORIGINS:
        train=d[d.date<origin]; test=d[d.date.between(origin,origin+pd.Timedelta(days=HORIZON-1))]
        plan=test.planned_pour_tonnes.to_numpy(); y=train.consumed_tonnes.to_numpy(); positive=y>0
        def add(name,pred):
            z=test[['date','site_id','consumed_tonnes']].rename(columns={'consumed_tonnes':'actual'}).copy(); z['origin']=origin; z['model']=name; z['prediction']=np.clip(pred,0,plan); predictions.append(z)
        add('Plan unchanged',plan)
        # Median observed realisation ratio, among all positive-plan days.
        eligible=train.planned_pour_tonnes>0
        ratio=train.loc[eligible,'consumed_tonnes']/train.loc[eligible,'planned_pour_tonnes']
        add('Plan × historical median ratio',plan*ratio.median())
        for weather in [False,True]:
            a,b=matrix(train,test,weather); label='Hindsight weather + plan' if weather else 'Conditional plan'
            kw=dict(n_estimators=250,learning_rate=.04,num_leaves=23,min_child_samples=50,n_jobs=2,random_state=42,verbosity=-1)
            reg=LGBMRegressor(objective='regression_l1',**kw).fit(a,y)
            add(label+' | LightGBM MAE',reg.predict(b))
            rf=RandomForestRegressor(n_estimators=80,max_depth=12,min_samples_leaf=20,n_jobs=2,random_state=42).fit(a,y)
            add(label+' | RF',rf.predict(b))
            # Weighted absolute loss minimises conditional MAPE on positive days.
            reg_pct=LGBMRegressor(objective='regression_l1',**kw).fit(a.loc[positive],y[positive],sample_weight=1/y[positive])
            add(label+' | LightGBM MAPE',reg_pct.predict(b))
            clf=LGBMClassifier(**kw).fit(a,positive.astype(int)); reg_positive=LGBMRegressor(objective='regression',**kw).fit(a.loc[positive],y[positive]); add(label+' | Hurdle expected demand',clf.predict_proba(b)[:,1]*reg_positive.predict(b))
        print('Completed',origin.date(),flush=True)
    return pd.concat(predictions,ignore_index=True)


def physical_audit(d):
    p=d.planned_pour_tonnes; y=d.consumed_tonnes
    available=d.opening_inventory_tonnes+d.deliveries_tonnes
    bound=np.minimum(p,available)
    g=d.groupby('site_id'); centered=y-g.consumed_tonnes.transform('mean')
    test=d[d.date.between(ORIGINS[-1],ORIGINS[-1]+pd.Timedelta(days=HORIZON-1))].copy()
    test['actual']=test.consumed_tonnes; test['prediction']=np.minimum(test.planned_pour_tonnes,test.opening_inventory_tonnes+test.deliveries_tonnes); test['model']='Hindsight physical bound'
    active=d[p>0].copy(); active['ratio']=active.consumed_tonnes/active.planned_pour_tonnes
    rain_groups=active.groupby(active.rain_mm>15).ratio.agg(n='size',mean='mean',zero=lambda x:(x==0).mean())
    return {'records':len(d),'plan_correlation':float(y.corr(p)), 'lag1_correlation':float(y.corr(g.consumed_tonnes.shift(1))), 'lag7_correlation':float(y.corr(g.consumed_tonnes.shift(7))), 'mean_within_site_lag1_correlation':float(centered.groupby(d.site_id).apply(lambda z:z.autocorr(1)).mean()), 'consumption_above_plan':int((y>p).sum()),'consumption_above_available':int((y>available+.011).sum()), 'matches_physical_bound_within_rounding':int((abs(y-bound)<=.011).sum()),'overcapacity_records':int((d.closing_inventory_tonnes>d.site_capacity).sum()),'overcapacity_sites':int(d.loc[d.closing_inventory_tonnes>d.site_capacity,'site_id'].nunique()),'max_capacity_ratio':float((d.closing_inventory_tonnes/d.site_capacity).max()),'opening_continuity_discrepancies':int((abs(d.opening_inventory_tonnes-g.closing_inventory_tonnes.shift(1))>.011).sum()),'rain_group_aggregate':rain_groups.to_dict('index'),'hindsight_physical_bound_metrics':metrics(test)}


def main():
    p=argparse.ArgumentParser();p.add_argument('database');p.add_argument('--output',default='local_outputs');args=p.parse_args();d=load_data(args.database);pred=experiment(d)
    val=pred[pred.origin<ORIGINS[-1]];test=pred[pred.origin==ORIGINS[-1]]
    report={'physical_audit':physical_audit(d),'validation':metrics(val),'final_reused_holdout':metrics(test)}
    out=Path(args.output);out.mkdir(exist_ok=True,parents=True);(out/'conditional_benchmark.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))

if __name__=='__main__':main()
