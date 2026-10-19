"""Thin Streamlit presentation of the bounded retrospective inference service."""
from datetime import date, time

import pandas as pd
import streamlit as st

from solar_flare_jepa.dashboard import prediction
from solar_flare_jepa.dashboard.prediction_charts import prediction_figure


def render(root):
    st.subheader('Solar Flux Prediction')
    st.write('Inspect a fixed seed 17 JEPA forecast from historical GOES-16 XRS observations. '
             'Choose an August 2024 UTC issue time with 120 completed, quality-valid context minutes.')
    st.caption('Retrospective archive inference · operational delivery latency is UNKNOWN. '
               'This is a historical reconstruction using bin-end availability, with no operational forecast claim.')
    day_column, time_column = st.columns(2)
    day=day_column.date_input('Observation issue date · UTC',value=date(2024,8,1),
        min_value=date(2024,8,1),max_value=date(2024,8,31))
    minute=time_column.time_input('Observation issue time · UTC',value=time(2,0),step=60)
    comparator=st.checkbox('Include supervised comparator · seed 17',value=False)
    actual=st.checkbox('Show quality-valid actual future observations',value=True)
    st.caption('The unchanged V1 specification uses 120 context bins and 30 forecast bins, with original stride 30. '
               'Additional minute issue times are retrospective inference examples; they do not extend the original '
               '1,436-origin benchmark cohort. Both models use exactly the same context and future grid.')
    issue=pd.Timestamp.combine(day,minute).tz_localize('UTC')
    try:
        result=prediction.forecast(root,issue,include_supervised=comparator)
        context=result.inputs.context; grid=result.inputs.grid
        start=pd.Timestamp(context.starts_ns[0,0],tz='UTC')
        end=pd.Timestamp(grid.ends_ns[0,-1],tz='UTC')
        st.caption(f'Context [{start:%d %b %Y %H:%M}, {issue:%d %b %Y %H:%M}) UTC · '
                   f'Forecast [{issue:%d %b %Y %H:%M}, {end:%d %b %Y %H:%M}) UTC. '
                   'Vertical lines mark context start, issue time and forecast end. '
                   'Lead 1 starts at issue time and ends one minute later; no time shift is applied.')
        figure=prediction_figure(result,show_actual=actual)
        st.plotly_chart(figure,use_container_width=True,theme=None,
            config={'displayModeBar':True,'responsive':True},key='solar_flux_prediction')
        st.caption('JEPA median and nominal central 50% (q25–q75) / 90% (q05–q95) quantile bands, '
                   'in W/m² on logarithmic axes. These intervals are uncalibrated; nominal coverage is not '
                   'a measured coverage guarantee. XRS-A: 0.05–0.4 nm; XRS-B: 0.1–0.8 nm. '
                   'Primary composite channels preserve the native detector-selection semantics.')
        rows=[]
        for support,channels in result.inputs.quality.items():
            for channel,counts in channels.items():
                rows.append({'Support':support.capitalize(),'Channel':'XRS-'+channel[-1].upper(),
                    'Valid bins':counts['valid'],'Masked bins':counts['masked'],'Missing bins':counts['missing']})
        st.dataframe(pd.DataFrame(rows),hide_index=True,width='stretch')
        st.caption('Counts are channel-specific minute bins. Masked includes missing bins and quality rejection. '
                   'Context eligibility requires all 120 × 2 cells; no filling or interpolation. '
                   'Optional future actuals remain gaps when missing, nonpositive, nonfinite or rejected; '
                   'they never enter either model. Native quality policy: status flag zero, channel-specific '
                   'electron-correction bits clear, sample count 1–60 and native flux bounds respected.')
        with st.expander('Scientific source and checkpoint provenance',expanded=False):
            st.caption('OBSERVED: immutable checkpoint and source hashes are reverified before inference. '
                       'Fixed seed 17 is neither an ensemble nor a best-seed selection. '
                       'Saved train-only normalization applies log₁₀(flux / [1 W/m²]) and stored means/scales; '
                       'no statistics are fitted on August. Parent dataset identity names the frozen V1 lineage; '
                       'only its August partition is opened here. The page does not open saved prediction arrays. '
                       'No flare labels, event claims, accuracy or model-superiority claims are inferred.')
            st.json(result.provenance,expanded=False)
    except (OSError,ValueError,KeyError,TypeError,RuntimeError,ImportError) as error:
        st.error('Verified solar flux prediction unavailable')
        st.caption(str(error))
        st.caption('Check the pinned local August observations, source identities and seed 17 checkpoints. '
                   'Optional inference dependencies are listed in requirements-dashboard-prediction.txt.')
