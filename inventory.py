"""Counterfactual replenishment policy replay; no raw outputs are published."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from forecast import load_data, metrics, HORIZON


def simulate(d, predictions, model, lead=2, buffer_days=2):
    joined=predictions[predictions.model==model].merge(d[['site_id','date','planned_pour_tonnes','opening_inventory_tonnes','site_capacity']],left_on=['site_id','target_date'],right_on=['site_id','date'],suffixes=('','_actual'),validate='one_to_one')
    rows=[]
    for (site,origin),z in joined.groupby(['site_id','date']):
        z=z.sort_values('horizon'); assert len(z)==HORIZON
        cap=float(z.site_capacity.iloc[0]); opening=float(z.opening_inventory_tonnes.iloc[0]); stock=min(opening,cap); pending={}
        # Feasible-capacity scenario: excess opening stock is explicitly segregated,
        # not assumed to be waste or written off. Historical stock remains unchanged.
        excess=max(0.,opening-cap)
        f=z.prediction.to_numpy()
        for i,r in enumerate(z.itertuples()):
            arrival=pending.pop(i,0.); stock+=arrival
            available=stock; demand=float(r.actual); served=min(stock,demand); stock-=served
            # Orders decided at end of day, using only forecast and current physical stock.
            future=f[i+1:min(i+1+lead+buffer_days,len(f))]
            target=min(cap,float(future.sum())); position=stock+sum(pending.values())
            qty=max(0.,target-position) if i+lead<len(f) else 0.
            if qty: pending[i+lead]=pending.get(i+lead,0.)+qty
            rows.append(dict(model=model,site_id=site,origin=origin,date=r.target_date,capacity=cap,available=available,closing=stock,actual=demand,served=served,planned=r.planned_pour_tonnes,ready=available>=r.planned_pour_tonnes,ordered=qty,arrived=arrival,overflow=max(0.,available-cap),opening_excess=excess if i==0 else 0.))
    return pd.DataFrame(rows)


def summarise(z):
    scheduled=z.planned>0
    return dict(model=z.model.iloc[0],days=len(z),scheduled_days=int(scheduled.sum()),pour_readiness_pct=float(z.loc[scheduled,'ready'].mean()*100),fill_rate_pct=float(z.served.sum()/z.actual.sum()*100),unserved_tonnes=float((z.actual-z.served).sum()),mean_closing_tonnes=float(z.closing.mean()),mean_capacity_utilisation_pct=float((z.closing/z.capacity).mean()*100),overflow_days=int((z.overflow>0).sum()),orders=int((z.ordered>0).sum()),ordered_tonnes=float(z.ordered.sum()),opening_excess_tonnes=float(z.opening_excess.sum()))


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('database'); parser.add_argument('--output',default='local_outputs'); args=parser.parse_args()
    out=Path(args.output); p=pd.read_csv(out/'predictions.csv',parse_dates=['date','target_date']); d=load_data(args.database)
    validation=p[p.date<p.date.max()]; final=p[p.date==p.date.max()]
    expected=len(validation[validation.model=='Seasonal naive']); final_expected=len(final[final.model=='Seasonal naive'])
    eligible=[m for m in metrics(validation) if m['observations']==expected]
    winner=eligible[0]['model']
    assert len(final[final.model==winner])==final_expected, 'Selected model lacks complete final holdout coverage'
    candidates=[]
    for buffer in [2,4,6,8,10,14]:
        s=summarise(simulate(d,validation,winner,buffer_days=buffer)); s['buffer_days']=buffer; candidates.append(s)
    feasible=[s for s in candidates if s['pour_readiness_pct']>=98]
    chosen=min(feasible,key=lambda s:s['mean_closing_tonnes']) if feasible else max(candidates,key=lambda s:s['pour_readiness_pct'])
    buffer=chosen['buffer_days']
    models=list(dict.fromkeys(['Seasonal naive',winner])); simulations=[simulate(d,final,m,buffer_days=buffer) for m in models]
    pd.concat(simulations).to_csv(out/'inventory.csv',index=False)
    report={'forecast_winner':winner,'selection_metrics':eligible,'final_holdout_metrics':metrics(final),'lead_days':2,'buffer_days':buffer,'buffer_validation':candidates,'scenarios':[summarise(z) for z in simulations]}
    (out/'inventory_summary.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
