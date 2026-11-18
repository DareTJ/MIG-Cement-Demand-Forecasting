"""Local decision-support dashboard. Run only with authorised local outputs."""
from pathlib import Path
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, dash_table
from forecast import metrics
from inventory import summarise

OUT=Path('local_outputs')
p=pd.read_csv(OUT/'predictions.csv',parse_dates=['date','target_date'])
i=pd.read_csv(OUT/'inventory.csv',parse_dates=['date','origin'])
complete=[m for m in metrics(p) if m['observations']==len(p[p.model=='Seasonal naive'])]
winner=i.model.iloc[-1]
sites=sorted(p.site_id.unique())
app=Dash(__name__,title='MIG | Supply Chain Intelligence')
app.layout=html.Div([
    html.Header([html.H1('MIG | Cement supply intelligence'),html.P('56-day forecasts • Inventory planning • Local research demonstration')],style={'background':'#12334b','color':'white','padding':'24px','borderRadius':'12px'}),
    html.P('Historical replay, not a live forecast. Results reflect observed consumption and simplified delivery assumptions.'),
    dcc.Tabs([
        dcc.Tab(label='Executive overview',children=[dcc.Graph(figure=px.bar(pd.DataFrame(complete),x='model',y='mae',color='model',title='Network forecast error | MAE (tonnes)',template='plotly_white')),dash_table.DataTable(data=pd.DataFrame(complete).round(3).to_dict('records'),columns=[{'name':k,'id':k} for k in complete[0]],style_table={'overflowX':'auto'},style_cell={'textAlign':'left','padding':'8px'}),html.H3('Final-window inventory policy comparison'),dash_table.DataTable(data=pd.DataFrame([summarise(z) for _,z in i.groupby('model')]).round(3).to_dict('records'),style_table={'overflowX':'auto'},style_cell={'textAlign':'left','padding':'8px'})]),
        dcc.Tab(label='Demand forecasting',children=[dcc.Dropdown(sites,sites[0],id='site'),dcc.Dropdown(sorted(p.model.unique()),winner,id='model'),dcc.Graph(id='forecast')]),
        dcc.Tab(label='Inventory planning',children=[dcc.Dropdown(sites,sites[0],id='inv-site'),dcc.Graph(id='inventory'),dash_table.DataTable(id='orders',page_size=12,style_table={'overflowX':'auto'},style_cell={'textAlign':'left','padding':'8px'})])
    ])
],style={'maxWidth':'1320px','margin':'20px auto','fontFamily':'Arial','color':'#12334b','padding':'12px'})

@app.callback(Output('forecast','figure'),Input('site','value'),Input('model','value'))
def plot_forecast(site,model):
    z=p[(p.site_id==site)&(p.model==model)].sort_values('target_date')
    return px.line(z,x='target_date',y=['actual','prediction'],title=f'{site} | {model} | Historical replay',template='plotly_white')

@app.callback(Output('inventory','figure'),Output('orders','data'),Output('orders','columns'),Input('inv-site','value'))
def plot_inventory(site):
    z=i[(i.site_id==site)&(i.model==winner)].sort_values('date')
    fig=px.line(z,x='date',y=['closing','capacity'],title=f'{site} | Simulated stock and capacity',template='plotly_white')
    orders=z.loc[z.ordered>0,['date','ordered','arrived','closing']].copy(); orders['date']=orders.date.dt.strftime('%Y-%m-%d'); orders=orders.round(2)
    return fig,orders.to_dict('records'),[{'name':k,'id':k} for k in orders.columns]

if __name__=='__main__': app.run(host='127.0.0.1',port=8050,debug=False)
