"""Rolling 56-day forecast benchmark using a private SQLite source."""
import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge

HORIZON = 56
ORIGINS = pd.to_datetime(['2024-07-01', '2024-08-26', '2024-10-21'])


def load_data(path):
    with sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True) as con:
        assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
        assert not con.execute('PRAGMA foreign_key_check').fetchall()
        d = pd.read_sql_query('SELECT o.*, s.region, s.behavior, s.silo_capacity AS site_capacity FROM Operations o JOIN Sites s USING(site_id)', con)
    d['date'] = pd.to_datetime(d.date, errors='raise')
    d = d.sort_values(['site_id', 'date']).reset_index(drop=True)
    assert not d.isna().any().any() and not d.duplicated(['site_id','date']).any()
    assert (d.silo_capacity == d.site_capacity).all()
    assert (d.groupby('site_id').date.diff().dropna() == pd.Timedelta(days=1)).all()
    cols = ['consumed_tonnes','planned_pour_tonnes','opening_inventory_tonnes','deliveries_tonnes','closing_inventory_tonnes','rain_mm']
    assert (d[cols] >= 0).all().all()
    return d


def features(d):
    """Features at forecast issue date use only the preceding observations."""
    g = d.groupby('site_id', sort=False)
    x = d[['site_id','date','region','behavior','site_capacity']].copy()
    for col in ['consumed_tonnes','planned_pour_tonnes','rain_mm','avg_temp_c']:
        for lag in [1,7,14,28]:
            x[f'{col}_lag{lag}'] = g[col].shift(lag)
        for window in [7,28,56]:
            x[f'{col}_mean{window}'] = g[col].transform(lambda z: z.shift(1).rolling(window).mean())
    x['last_inventory'] = g.closing_inventory_tonnes.shift(1)
    x['last_cement_type'] = g.cement_type.shift(1)
    return x.dropna()


def direct_rows(x, d, origins):
    base = x[x.date.isin(origins)].copy()
    z = base.loc[base.index.repeat(HORIZON)].copy()
    z['horizon'] = np.tile(np.arange(1,HORIZON+1), len(base))
    z['target_date'] = z.date + pd.to_timedelta(z.horizon-1, unit='D')
    z['weekday'] = z.target_date.dt.dayofweek
    z['month'] = z.target_date.dt.month
    return z.merge(d[['site_id','date','consumed_tonnes']].rename(columns={'date':'target_date','consumed_tonnes':'actual'}), on=['site_id','target_date'], how='left')


def matrices(train, test):
    cols = ['date','target_date','actual']
    a = pd.get_dummies(train.drop(columns=cols), dtype=float)
    b = pd.get_dummies(test.drop(columns=cols), dtype=float).reindex(columns=a.columns, fill_value=0)
    return a, b


def statistical(history, model):
    y = history.consumed_tonnes.to_numpy()
    if model == 'Seasonal naive':
        return np.resize(y[-7:], HORIZON)
    if model == 'AR(7)':
        # Ridge-stabilised autoregression; recursive multi-step prediction.
        a = np.lib.stride_tricks.sliding_window_view(y, 8)
        m = Ridge(alpha=1).fit(a[:,:7], a[:,7])
        state = list(y[-7:]); out = []
        for _ in range(HORIZON):
            p = max(0., float(m.predict([state[-7:]])[0])); state.append(p); out.append(p)
        return np.asarray(out)
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    # Calendar is known across the full horizon; actual future weather and plans are not.
    index = pd.DatetimeIndex(history.date)
    future = pd.date_range(index[-1]+pd.Timedelta(days=1), periods=HORIZON)
    def calendar(t):
        return np.column_stack([np.sin(2*np.pi*t.dayofweek/7),np.cos(2*np.pi*t.dayofweek/7)])
    fitted = SARIMAX(y, exog=calendar(index), order=(1,0,1), seasonal_order=(1,0,0,7), enforce_stationarity=True).fit(disp=False,maxiter=60)
    if not fitted.mle_retvals.get('converged', False):
        raise RuntimeError('SARIMAX did not converge')
    return np.maximum(0, fitted.forecast(HORIZON,exog=calendar(future)))


def benchmark(d, include_optional=True):
    x = features(d); results = []; failures = []
    models = ['Seasonal naive','AR(7)'] + (['SARIMAX'] if include_optional else [])
    for origin in ORIGINS:
        train = direct_rows(x,d,pd.date_range(x.date.min(),origin-pd.Timedelta(days=HORIZON),freq='7D'))
        train = train[train.target_date < origin].dropna(subset=['actual'])
        test = direct_rows(x,d,[origin]); assert test.actual.notna().all()
        assert train.target_date.max() < origin
        a,b = matrices(train,test)
        estimators = {'Random Forest':RandomForestRegressor(n_estimators=100,max_depth=12,min_samples_leaf=10,n_jobs=2,random_state=42)}
        if include_optional:
            from lightgbm import LGBMRegressor
            estimators['LightGBM'] = LGBMRegressor(n_estimators=300,learning_rate=.05,num_leaves=31,min_child_samples=30,n_jobs=2,random_state=42,verbosity=-1)
        def add(rows, name, pred):
            q = rows[['site_id','date','target_date','horizon','actual']].copy()
            q['model'] = name; q['prediction'] = np.maximum(0,pred); results.append(q)
        for name,m in estimators.items():
            m.fit(a,train.actual); add(test,name,m.predict(b))
        for site,rows in test.groupby('site_id'):
            h = d[(d.site_id==site)&(d.date<origin)]
            for name in models:
                try: add(rows,name,statistical(h,name))
                except Exception as exc: failures.append((name,str(origin.date()),site,type(exc).__name__))
        print('Completed origin',origin.date(),flush=True)
    return pd.concat(results,ignore_index=True), failures


def metrics(p):
    rows=[]
    for name,z in p.groupby('model'):
        e=z.prediction-z.actual; nonzero=z.actual>0
        rows.append({'model':name,'observations':len(z),'mae':float(abs(e).mean()),'rmse':float(np.sqrt((e**2).mean())),'wape_pct':float(abs(e).sum()/z.actual.sum()*100) if z.actual.sum() else None,'mape_nonzero_pct':float((abs(e[nonzero])/z.actual[nonzero]).mean()*100) if nonzero.any() else None,'nonzero_observations':int(nonzero.sum()),'bias_tonnes':float(e.mean())})
    return sorted(rows,key=lambda z:z['mae'])


def main():
    p=argparse.ArgumentParser(); p.add_argument('database'); p.add_argument('--output',default='local_outputs'); p.add_argument('--core-only',action='store_true'); args=p.parse_args()
    d=load_data(args.database); pred,failures=benchmark(d,not args.core_only)
    out=Path(args.output); out.mkdir(parents=True,exist_ok=True)
    pred.to_csv(out/'predictions.csv',index=False)
    report={'horizon_days':HORIZON,'origins':[str(o.date()) for o in ORIGINS],'expected_per_model':len(ORIGINS)*HORIZON*d.site_id.nunique(),'core_only':args.core_only,'metrics':metrics(pred),'failed_fits':len(failures)}
    (out/'benchmark.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report,indent=2))


if __name__=='__main__': main()
