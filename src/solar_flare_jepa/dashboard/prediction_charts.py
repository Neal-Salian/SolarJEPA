"""Interactive physical-unit charts for already computed retrospective forecasts."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from solar_flare_jepa.dashboard.charts import COLORS, _style


def prediction_figure(result, *, show_actual=True):
    inputs = result.inputs
    past = pd.to_datetime(inputs.context.starts_ns[0], utc=True).to_pydatetime()
    future = pd.to_datetime(inputs.grid.starts_ns[0], utc=True).to_pydatetime()
    ends = pd.to_datetime(inputs.grid.ends_ns[0], utc=True)
    lead_data = [[lead, end.isoformat()] for lead, end in enumerate(ends, 1)]
    figure = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=.15,
                          subplot_titles=('XRS-A · 0.05–0.4 nm', 'XRS-B · 0.1–0.8 nm'))
    for k, channel in enumerate(('xrsa', 'xrsb')):
        row=k+1; label='XRS-'+channel[-1].upper(); color=COLORS[channel]
        def trace(values, name, *, x=future, **style):
            figure.add_trace(go.Scatter(x=x,y=values,name=label+' · '+name,mode='lines',
                connectgaps=False,customdata=lead_data if x is future else None,
                hovertemplate=('%{x|%d %b %Y %H:%M} UTC · interval start<br>%{y:.3e} W/m²'
                               + ('<br>Lead %{customdata[0]} · bin ends %{customdata[1]}' if x is future else '')
                               + '<extra>%{fullData.name}</extra>'),**style),row=row,col=1)
        trace(inputs.context.values[0,:,k], 'context', x=past, line=dict(color=color,width=1.5))
        quantiles=result.jepa.quantiles[0,:,k,:]
        for lower, upper, coverage, fill in ((0,4,'90%','rgba(80,160,225,.13)'),
                                             (1,3,'50%','rgba(80,160,225,.26)')):
            trace(quantiles[:,lower], 'q'+('05' if lower==0 else '25'),
                  line=dict(width=0),showlegend=False,hoverinfo='skip')
            trace(quantiles[:,upper], 'central '+coverage, line=dict(width=0),
                  fill='tonexty',fillcolor=fill)
        trace(result.jepa.values[0,:,k], 'JEPA median', line=dict(color=color,width=2.4))
        if show_actual:
            trace(inputs.actual_future[:,k], 'actual future', line=dict(color='#E7EDF6',width=1.4))
        if result.supervised is not None:
            trace(result.supervised.values[0,:,k], 'supervised median',
                  line=dict(color='#F2B869',width=1.8,dash='dash'))
        figure.update_yaxes(type='log',title_text='Solar X-ray flux · W/m²',exponentformat='power',row=row,col=1)
        boundaries=((inputs.context.starts_ns[0,0],'dot'),(inputs.grid.issue_times_ns[0],'dash'),
                    (inputs.grid.ends_ns[0,-1],'dot'))
        for value,dash in boundaries:
            t=pd.Timestamp(value,tz='UTC').to_pydatetime()
            figure.add_shape(type='line',x0=t,x1=t,y0=0,y1=1,
                xref='x' if row==1 else 'x2',yref='y domain' if row==1 else 'y2 domain',
                line=dict(color='#7D91AD',width=1,dash=dash))
    _style(figure,height=760)
    figure.update_layout(legend=dict(orientation='h',y=-.13,x=0),
        meta=dict(time_coordinates='UTC interval starts; lead1 ends issue+1minute',
                  quantiles='Nominal uncalibrated central50% and90%',seed=17))
    figure.update_xaxes(title_text='UTC interval-start time',tickformat='%d %b %H:%M',row=2,col=1)
    return figure
