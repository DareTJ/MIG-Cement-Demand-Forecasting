"""Small synthetic tests; no case-study data is needed."""
import unittest
import numpy as np
import pandas as pd
from forecast import features, direct_rows, HORIZON, metrics
from inventory import simulate


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        n=140
        self.d=pd.DataFrame(dict(site_id='TEST',date=pd.date_range('2024-01-01',periods=n),region='test',behavior='test',site_capacity=100,consumed_tonnes=np.arange(n,dtype=float),planned_pour_tonnes=10.,rain_mm=0.,avg_temp_c=12.,closing_inventory_tonnes=50.,opening_inventory_tonnes=50.,cement_type='TEST'))

    def test_origin_features_do_not_read_current_or_future_consumption(self):
        origin=self.d.date.iloc[70]
        before=features(self.d); altered=self.d.copy(); altered.loc[altered.date>=origin,'consumed_tonnes']=9999
        after=features(altered)
        pd.testing.assert_frame_equal(before[before.date==origin],after[after.date==origin])
        rows=direct_rows(before,self.d,[origin]); self.assertEqual(len(rows),HORIZON)
        self.assertEqual(rows.target_date.min(),origin)
        self.assertEqual(rows.target_date.max(),origin+pd.Timedelta(days=55))

    def test_zero_safe_metrics(self):
        z=pd.DataFrame(dict(model='test',actual=[0.,10.],prediction=[2.,8.]))
        self.assertEqual(metrics(z)[0]['mae'],2.)
        self.assertEqual(metrics(z)[0]['mape_nonzero_pct'],20.)

    def test_inventory_balance(self):
        origin=self.d.date.iloc[70]; rows=direct_rows(features(self.d),self.d,[origin]); rows['model']='test'; rows['prediction']=20.
        z=simulate(self.d,rows,'test'); self.assertTrue((z.closing>=0).all()); self.assertTrue((z.ordered>=0).all())
        np.testing.assert_allclose(z.closing,z.available-z.served)
        np.testing.assert_allclose(z.available.iloc[1:],z.closing.iloc[:-1].to_numpy()+z.arrived.iloc[1:].to_numpy())


if __name__=='__main__': unittest.main()
