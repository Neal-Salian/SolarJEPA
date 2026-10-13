/** Build the SolarJEPA deck from verified compact evidence and actual charts.
 * Runtime dependencies come from Codex's bundled artifact-tool environment.
 * Scientific chart PNGs intentionally preserve the scientific plotting workflow.
 */
import fs from 'node:fs/promises';
import path from 'node:path';
import {createRequire} from 'node:module';
import {execFileSync} from 'node:child_process';
import {fileURLToPath, pathToFileURL} from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const skillDir = process.env.PRESENTATIONS_SKILL_DIR;
const modules = process.env.RUNTIME_NODE_MODULES;
const python = process.env.RUNTIME_PYTHON;
if (!skillDir || !modules || !python) throw new Error('Set PRESENTATIONS_SKILL_DIR, RUNTIME_NODE_MODULES and RUNTIME_PYTHON');
const requireRuntime = createRequire(path.join(modules, '__runtime__.cjs'));
const {Presentation, PresentationFile} = await import(pathToFileURL(requireRuntime.resolve('@oai/artifact-tool')));
const {finalizePresentation} = await import(pathToFileURL(path.join(skillDir, 'container_tools/artifact_tool_utils.mjs')));
const revision = process.argv[2] || 'v1';
const build = path.join(root, '.cache/presentation-build', revision);
const output = path.join(root, 'presentations');
const assets = path.join(output, 'assets');
await fs.mkdir(build, {recursive: true});
const E = JSON.parse(await fs.readFile(path.join(output, 'slide_evidence.json'), 'utf8'));
const sourceBase = `https://github.com/Neal-Salian/SolarJEPA/blob/${E.source_commit}/`;
const C = {bg:'#080F1D', text:'#F1F5FB', muted:'#9AACCA', orange:'#FFAB49', cyan:'#4CD9E8', rule:'#27354B'};
const font = 'Arial';
const P = Presentation.create({slideSize:{width:1280,height:720}});
const slideContent = [];
const objects = [];

function text(s, value, x, y, w, h, size=26, color=C.text, bold=false, align='left') {
  const sh = s.shapes.add({geometry:'textbox',name:`text-${objects.length}`,position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=value;
  sh.text.style={fontSize:size,typeface:font,color,bold,alignment:align,verticalAlignment:'top',autoFit:'none',wrap:'square',insets:0};
  objects.push({slide:P.slides.items.length,kind:'text',text:value,x,y,w,h,size});
  return sh;
}
function slide(title, subtitle, notes, sources=[]) {
  const s=P.slides.add(); s.background.fill=C.bg;
  text(s,title,56,38,1168,64,43,C.text,true);
  if(subtitle) text(s,subtitle,58,111,1150,48,23,C.muted);
  text(s,'SolarJEPA',58,677,500,24,15,C.muted);
  text(s,String(P.slides.items.length).padStart(2,'0')+' / 20',1120,677,104,24,15,C.muted,false,'right');
  const citations=sources.map(x=>sourceBase+x).join('\n');
  s.speakerNotes.text=notes+'\n\nSources at pinned analysis commit '+E.source_commit+':\n'+citations;
  slideContent.push({number:P.slides.items.length,title,subtitle,notes,sources});
  return s;
}
async function image(s,name,x,y,w,h,alt) {
  const bytes=await fs.readFile(path.join(assets,name));
  s.images.add({blob:bytes.buffer.slice(bytes.byteOffset,bytes.byteOffset+bytes.byteLength),contentType:'image/png',alt,fit:'contain',position:{left:x,top:y,width:w,height:h}});
  objects.push({slide:P.slides.items.length,kind:'image',name,x,y,w,h});
}
function table(s,values,x,y,w,h,widths,size=24,highlight=[],padding=12) {
  const tb=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
  tb.borders.assign({fill:C.rule,width:0.5,style:'solid'});
  const margins={top:padding,bottom:padding,left:12,right:12};
  tb.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins});
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++) {
    const cell=tb.getCell(r,c);
    cell.fill=r===0?'#152438':C.bg;
    cell.text.style={fontSize:size,typeface:font,color:r===0?C.muted:highlight.includes(r)?C.orange:C.text,bold:r===0||highlight.includes(r),autoFit:'none',insets:margins,verticalAlignment:'middle'};
  }
  objects.push({slide:P.slides.items.length,kind:'table',values,x,y,w,h});
  return tb;
}
function take(s,value,y=608,color=C.orange) {text(s,value,58,y,1152,55,25,color);}
const edaSources=['docs/presentation/time_series_evidence.json','docs/presentation/eda_evidence.json','src/solar_flare_jepa/presentation/eda.py'];
const modelSources=['docs/presentation/time_series_evidence.json','src/solar_flare_jepa/presentation/classical.py','src/solar_flare_jepa/presentation/time_series.py'];
const f3=x=>x.toFixed(3), f6=x=>x.toFixed(6);

// 01: Minimal typographic cover with the objective visible.
{
 const s=slide('','','SolarJEPA is a solar X-ray research project with a broader interest in joint embedding predictive representation learning. This presentation focuses on the completed classical time-series analysis of GOES-16 XRS observations. The objective is to characterize the observations, diagnose quality and dependence, compare appropriate classical candidates, and demonstrate reproducible local inference. The analysis concerns continuous irradiance. Event-level solar-flare labels, alert thresholds and operational warning skill have not been established. Evidence terms throughout: DOCUMENTED describes method definitions, OBSERVED describes actual file or execution evidence, INFERRED describes interpretation, and UNKNOWN describes unestablished claims.',['docs/PRESENTATION_TIME_SERIES_GUIDE.md','docs/PRESENTATION_TIME_SERIES_VERIFICATION.md']);
 text(s,'SolarJEPA',58,120,1160,110,92,C.orange,true);
 text(s,'Solar X-ray\ntime-series analysis',62,260,1120,152,58,C.text,true);
 text(s,'GOES-16 XRS-A / XRS-B\nMay–August 2024',64,453,1000,86,30,C.muted);
 text(s,'Objective: characterize solar observations and demonstrate\nreproducible 30-minute classical forecasting',64,577,1150,77,28,C.text);
 slideContent.at(-1).title='SolarJEPA: Solar X-ray time-series analysis';
}
// 02: Collection and temporal scope.
{
 const s=slide('Data collection','GOES-16 EXIS/XRS science products at one-minute cadence',
 'OBSERVED: four explicit manifests pin 123 daily NetCDF files, totaling 36,535,474 bytes. The native loader validates identities, platform, instrument, clock and units. The observed grid spans May 1 through August 31, 2024, with end-exclusive September 1 at 00:00 UTC. There are 177,120 unique minute bins. This is the number of recorded time bins before channel QC rejection, not the valid sample count for both channels. The product supplies primary electron-corrected irradiance in W/m². These are GOES observations, not Aditya-L1 observations. The analysis assumes retrospective availability at bin end. Actual operational delivery latency is UNKNOWN. Raw scientific files remain immutable and outside Git.',['data/manifests/goes_v1_202405.json','data/manifests/goes_v1_202406.json','data/manifests/goes_p2_july2024.json','data/manifests/goes_v1_202408.json','src/solar_flare_jepa/data/goes.py']);
 text(s,'123',62,180,490,90,76,C.orange,true);text(s,'pinned daily files',65,274,490,44,28);
 text(s,'177,120',630,180,590,90,76,C.cyan,true);text(s,'recorded minute bins',634,274,570,44,28);
 table(s,[['Month (2024)','May','June','July','August'],['Daily files','31','30','31','31'],['Minute bins','44,640','43,200','44,640','44,640']],62,357,1156,186,[292,216,216,216,216],26);
 take(s,'UTC bin starts • Irradiance in W/m² • Four manifest-pinned collections'.replaceAll(' • ','   /   '),581,C.muted);
}
// 03: Full archive line graph.
{
 const s=slide('Solar X-ray flux over time','Full May–August archive with QC-rejected values retained as gaps',
 'OBSERVED: this line graph uses the full manifest-validated minute grid and channel-specific QC-valid irradiance. The vertical axis displays native irradiance in W/m² on a logarithmic scale. Every native minute is supplied to the plotted series, with missing/rejected values preserved as NaN gaps and no imputation. Channel colors remain orange for A and cyan for B. Transient peaks and changing background levels motivate distributional and local dependence analysis. They are continuous observations and are not counted as labeled flares. INFERRED: the strong variation makes a single global stationary model questionable. A local diagnostic block provides controlled comparisons on complete support.',edaSources);
 await image(s,'chart_log.png',44,166,1190,424,'Actual irradiance time series on logarithmic axes for both GOES channels, May–August 2024');
 take(s,'Transient peaks and a changing background motivate local diagnostics');
}
// 04: Paired scatter.
{
 const s=slide('Paired channel behavior','Log irradiance scatter from jointly valid one-minute observations',
 'OBSERVED: the Pearson correlation is 0.963905768 on all 172,646 jointly QC-valid log-space pairs. The scatter displays 2,500 chronologically evenly spaced pairs for legibility. Display thinning does not change the correlation population and is not a statistical resample. The positive relationship reflects paired channel observations on shared timestamps. INFERRED: both channels respond to common changing solar activity, with channel-specific amplitude and spectral response. Correlation does not identify causal effects, predictive skill or independent flare events. The two channel validity masks are intersected explicitly for this chart.',edaSources);
 await image(s,'chart_scatter.png',50,166,790,439,'Actual paired log-space scatter, 2500 display points from 172646 valid pairs');
 text(s,'0.9639',884,234,330,90,62,C.orange,true);
 text(s,'Pearson correlation\n172,646 paired minutes',885,335,330,100,28);
 text(s,'2,500 pairs displayed\nFull-sample statistic',885,484,330,80,23,C.muted);
}
// 05: Histogram.
{
 const s=slide('Flux distributions','Histograms use each channel’s full QC-valid May–August population',
 'OBSERVED: these histograms count all valid minute bins, 172,646 for XRS-A and 174,845 for XRS-B. They display log10 irradiance in equally spaced log bins. Thus a bar describes a log-space interval and cannot be read as an equal-width interval of native irradiance. Native irradiance has a pronounced right tail, and the log transformation spreads the dynamic range. INFERRED: log space offers a useful numerical scale for diagnostics and error reporting. It does not make the series Gaussian, stationary or independent. Counts are minute bins, not independent events or flare classes.',edaSources);
 await image(s,'chart_histogram.png',44,166,1190,430,'Full-population log-space histograms for XRS-A and XRS-B');
 take(s,'Log scaling makes the dynamic range easier to inspect');
}
// 06: QQ.
{
 const s=slide('Normal Q–Q diagnostics','Marginal log distributions show departures from a fitted normal reference',
 'OBSERVED: the normal Q–Q curves use the saved 301 theoretical/observed order-statistic display ranks per channel. Fitted reference lines use the full channel-specific valid log samples, not only the displayed ranks. Departures in the tails show that the marginal distribution does not follow the fitted normal reference exactly. INFERRED: treating rare extreme observations as a Gaussian sample needs caution. This chart assesses marginal shape. It does not test innovation normality after model fitting and does not establish independence because neighboring minutes are correlated. No normality p-value or residual-normality claim is invented.',edaSources);
 await image(s,'chart_qq.png',44,166,1190,430,'Actual normal Q–Q plots of the valid log irradiance distributions');
 take(s,'Tail departures caution against a simple Gaussian marginal assumption');
}
// 07: Descriptive stats and missing values.
{
 const stats=E.statistics.filter(r=>r.transform==='raw');
 const s=slide('Descriptive statistics and missing values','Unlogged QC-valid irradiance in W/m², May–August 2024',
 'OBSERVED: the table summarizes native-unit, unlogged QC-valid irradiance. Here unlogged does not mean raw detector counts or unfiltered measurements. Standard deviation uses sample ddof=1. Mean exceeds median in both channels, consistent with a right tail. There are zero absent timestamps and zero duplicate timestamps. QC rejects 4,474 A values and 2,275 B values. Each channel has 2,153 nonfinite original values already included inside those rejection counts, so the counts must not be added. Missing/rejected measurements retain NaN and false validity masks. The workflow applies no imputation. Local stationarity, dependence and STL diagnostics use a contiguous jointly valid training segment and never bridge a rejected gap.',['docs/presentation/time_series_evidence.json','src/solar_flare_jepa/presentation/time_series.py','src/solar_flare_jepa/data/goes.py']);
 const exp=x=>x.toExponential(3);
 table(s,[['Statistic','XRS-A','XRS-B'],['Valid bins',...stats.map(r=>r.count.toLocaleString('en-US'))],['Mean',...stats.map(r=>exp(r.mean))],['Median',...stats.map(r=>exp(r.median))],['Sample std.',...stats.map(r=>exp(r.std))],['Minimum',...stats.map(r=>exp(r.min))],['Maximum',...stats.map(r=>exp(r.max))]],58,176,724,380,[260,232,232],25);
 text(s,'0 absent timestamps',832,195,388,72,30,C.cyan,true);
 text(s,'QC-rejected values\nA: 4,474   (2.53%)\nB: 2,275   (1.28%)',832,297,388,150,26);
 text(s,'No imputation\nNaN gaps and masks persist',832,482,388,90,26,C.orange);
 take(s,'Complete timestamp coverage still includes unusable measurements',607,C.muted);
}
// 08: Stationarity.
{
 const s=slide('Stationarity: ADF and KPSS','10,149 consecutive June training minutes, with 5% decision threshold',
 'DOCUMENTED: ADF tests a unit-root null, while level KPSS tests a stationarity null. OBSERVED: ADF uses constant regression, 30 fixed lags and no autolag. KPSS uses a constant and automatic bandwidth. The common segment spans June 11 16:38 through June 18 17:46 UTC. Log levels reject both nulls, which is mixed evidence rather than proof of stationarity. First log differences reject the ADF null and do not reject KPSS, supporting a bounded d=1 demonstration. Stored ADF p=0 for differenced series is a numerical approximation cutoff and is shown as approximately zero, not exact probability zero. KPSS p>0.10 is a bound. Tests on one segment do not prove stationarity across the four-month archive. Raw numerically scaled levels also reject ADF and do not reject KPSS, illustrating sensitivity to transformation and assumptions.',['docs/presentation/stationarity.csv','src/solar_flare_jepa/presentation/eda.py']);
 table(s,[['Series','ADF statistic','ADF p','KPSS statistic','KPSS p'],['A: log level','−8.763','2.64 × 10⁻¹⁴','0.554','0.02944'],['A: Δlog','−22.395','≈ 0*','0.00245','> 0.10'],['B: log level','−8.224','6.32 × 10⁻¹³','0.658','0.01734'],['B: Δlog','−21.191','≈ 0*','0.00273','> 0.10']],58,184,1164,292,[270,230,220,230,214],25);
 text(s,'ADF null: unit root',60,514,550,43,26,C.orange,true);
 text(s,'KPSS null: level stationarity',650,514,570,43,26,C.cyan,true);
 take(s,'First differences support the local d = 1 demonstration',588);
 text(s,'* Numerical p-value cutoff. Non-rejection does not prove global stationarity.',60,639,1160,24,17,C.muted);
}
// 09: Transformations.
{
 const s=slide('Log transformation and differencing','Before and after views use the same complete June training segment',
 'DOCUMENTED: define y_t = log10(F_t / (1 W/m²)); y is dimensionless and its differences are expressed in dex. The first difference Δy_t = y_t − y_(t−1) describes one-minute multiplicative change. OBSERVED: native irradiance, log levels and first log differences use the same 10,149-row contiguous June block, with one fewer differenced value. The log transformation compresses scale. Differencing removes local level persistence but may preserve correlated changes and changing variability. Neither operation invents missing measurements. INFERRED: differencing supports a bounded d=1 model of log irradiance levels given the local ADF/KPSS results. This is a modeling decision, not proof that every solar regime is stationary.',edaSources);
 await image(s,'chart_transform.png',40,166,1200,400,'Actual native irradiance, log level and first log difference for both channels');
 text(s,'yₜ = log₁₀(Fₜ / (1 W m⁻²))',62,588,640,53,29,C.orange);
 text(s,'Δyₜ = yₜ − yₜ₋₁',755,588,460,53,29,C.cyan);
}
// 10: STL.
{
 const s=slide('Exploratory STL decomposition','Robust STL with an assumed period of 1,440 minutes',
 'OBSERVED: robust STL decomposes log flux on the full 10,149-minute June segment. The plotting arrays retain 1,100 chronological display positions and the component values evaluated at those positions. Settings are period=1440, seasonal=7, robust=True, seasonal_jump=1, trend_jump=144, low_pass_jump=144. The reconstruction maximum error is 8.88e−16 dex. LOESS jump interpolation approximates smoothing and is unrelated to filling missing observations. DOCUMENTED: STL returns a seasonal component for the supplied period. INFERRED: approximately seven days of data and weak differenced daily-lag correlations, A 0.0142 and B 0.00816, do not establish stable physical daily seasonality. The daily component shown is exploratory and imposed. UNKNOWN: a defensible stable seasonal period for SARIMA. No genuine SARIMA fit or score exists.',['docs/presentation/time_series_evidence.json','src/solar_flare_jepa/presentation/time_series.py']);
 await image(s,'chart_stl.png',44,158,1190,445,'Actual STL components for both channels with explicitly assumed daily component');
 take(s,'An imposed daily component does not establish stable solar seasonality',612);
}
// 11: ACF.
{
 const s=slide('Autocorrelation','ACF of log levels and first log differences, with lag units in minutes',
 'OBSERVED: the saved ACF uses FFT with biased covariance normalization on the same complete June training segment. The display reaches 120 minutes. Log levels are highly persistent: lag-one ACF is about 0.987 for A and 0.992 for B. First differences retain short-lag correlation, with lag-one ACF 0.543 and 0.644. By lag 60 the differenced ACF is near zero, −0.00986 and −0.0160. INFERRED: this motivates a small short-memory candidate set rather than a seasonal model. High autocorrelation can arise from persistent levels or trends and alone does not imply seasonality. No iid confidence bands are plotted, because minute observations and changing regimes need careful interpretation.',edaSources);
 await image(s,'chart_acf.png',44,166,1190,429,'Actual ACF up to 120 minute lags in log levels and differences');
 take(s,'Differencing reduces level persistence but leaves short-lag structure');
}
// 12: PACF and lags.
{
 const s=slide('Partial autocorrelation and lag selection','PACF guides a bounded candidate set. Training BIC makes the order choice',
 'OBSERVED: PACF uses Yule–Walker MLE (ywm) and shows 60 minute lags for levels and first differences on the June segment. DOCUMENTED: p is the number of AR lags, d the number of differences, and q the number of innovation lags. d is not a time lag. ACF/PACF cutoff heuristics motivate candidate orders but do not determine a uniquely correct model in these transient data. The fixed candidates explore short AR/MA orders 1 and 2. Within the prespecified d=1 group, training BIC chooses p=1, d=1, q=0 for XRS-A and p=2, d=1, q=0 for XRS-B. q=0 reflects the candidate comparison and does not prove all innovation effects absent. A 120-bin inference context and 30-bin horizon are separate design choices and are not p or q.',edaSources.concat(['src/solar_flare_jepa/presentation/classical.py']));
 await image(s,'chart_pacf.png',44,164,1190,407,'Actual Yule–Walker MLE PACF up to 60 minute lags');
 text(s,'XRS-A: (p, d, q) = (1, 1, 0)',60,600,590,45,27,C.orange,true);
 text(s,'XRS-B: (p, d, q) = (2, 1, 0)',660,600,560,45,27,C.cyan,true);
}
// 13: Candidate identification.
{
 const s=slide('Classical model identification','Seven fixed candidates per channel on the same 2,880 June training minutes',
 'DOCUMENTED: AR uses lagged observations, MA uses lagged innovations, ARMA combines both, and ARIMA includes differencing. MA(q) is not the same as smoothing observations with a moving-average window. OBSERVED: the existing statistical adapter fitted AR(1), AR(2), MA(1), MA(2), ARMA(1,1), ARIMA(1,1,0), and ARIMA(2,1,0) for each channel. All 14 fits converged. The fitting interval is June 11 16:38 through June 13 16:37 UTC. d=0 candidates include a constant. d=1 candidates have no deterministic trend and burn one observation in their likelihood. INFERRED: a stable seasonal period is unestablished, so a genuine seasonal SARIMA specification is deferred. There is no seasonal fit, AIC/BIC or forecast score. Under a literal rubric requiring every family to be fitted, requirement 8 remains partial. All applicable nonseasonal family demonstrations are covered.',modelSources);
 table(s,[['Family','Candidate specification','Role'],['AR','AR(1), AR(2)','Past observations'],['MA','MA(1), MA(2)','Past innovations'],['ARMA','ARMA(1,1)','Both components'],['ARIMA','(1,1,0), (2,1,0)','First log difference'],['SARIMA','Deferred','Stable period unestablished']],58,180,1164,358,[225,420,519],26);
 take(s,'All 14 nonseasonal fits converged. No seasonal fit or score is claimed',588);
}
// 14: IC table.
{
 const rows=[['Channel / order','AIC','BIC','ΔBIC within channel']];
 for(const ch of ['xrsa','xrsb']) {
  const group=E.candidates.filter(r=>r.channel===ch&&r.order[1]===1);
  const best=Math.min(...group.map(r=>r.bic));
  for(const r of group) rows.push([`${ch==='xrsa'?'A':'B'} / (${r.order.join(',')})`,f3(r.aic),f3(r.bic),f3(r.bic-best)]);
 }
 const s=slide('AIC/BIC comparison and selection','Comparable d = 1 candidates only, ranked separately for each channel',
 'DOCUMENTED: AIC = −2ℓ + 2k and BIC = −2ℓ + k ln(n_eff), balancing likelihood and parameter count. OBSERVED: this table compares the two d=1 candidates per channel. Within each channel the transformation, support, deterministic terms and likelihood burn are fixed: no trend, burn=1 and effective n=2879. Training BIC prefers A (1,1,0) by 6.7705 and B (2,1,0) by 64.2862. AIC also favors these orders within the displayed groups. The d=1 choice is a prespecified diagnostic decision. It is not obtained by globally ranking all seven model fits. Do not compare criteria across channels, transformations or incompatible d/trend/burn groups. The d=0 family fits have a separate constant/burn0/n2880 comparison support. Future August target values do not enter fitting or order selection. Lower BIC does not establish physical truth or guarantee lowest held-out error.',modelSources);
 table(s,rows,58,181,1164,282,[340,260,260,304],26,[1,4]);
 text(s,'AIC = −2ℓ + 2k',62,509,530,55,31,C.orange);
 text(s,'BIC = −2ℓ + k ln(nₑff)',650,509,570,55,31,C.cyan);
 take(s,'Selected: A (1,1,0) and B (2,1,0) by training BIC',596);
}
// 15: Forecast.
{
 const s=slide('Actual versus predicted irradiance','1 August 2024, 02:00 UTC. Axes show log₁₀(F / (1 W m⁻²)) in dex',
 'OBSERVED: this chart uses saved native context, actual targets and inverse-log forecasts verified by a fresh saved-parameter replay. Context contains 120 completed minute bins with start times 00:00 through 01:59 UTC. Targets have start times 02:00 through 02:29. The issue line is 02:00 UTC. Parameters fitted in June remain frozen, while filtering uses only the supplied past context. Forecasts returned in native units are inverse-log conditional medians. No uncertainty intervals are supplied or claimed. Future target values do not enter fitting, selection or inference. The retrospective demonstration origin is the first chronological window with complete valid past context and target support, so target QC validity participates in choosing the scored window. This one example does not estimate general forecast skill.',modelSources);
 await image(s,'chart_forecast.png',44,166,1190,432,'Actual context, held-out irradiance and saved-parameter forecasts for both channels');
 take(s,'120 observed past minutes and a 30-minute forecast horizon');
}
// 16: Metrics and protocol.
{
 const rows=[['Channel','Selected order','Log MAE (dex)','Log RMSE (dex)']];
 for(const ch of ['xrsa','xrsb']) rows.push([ch==='xrsa'?'XRS-A':'XRS-B',`(${E.selected[ch].order.join(',')})`,f6(E.deployment.metrics[ch].log_mae),f6(E.deployment.metrics[ch].log_rmse)]);
 const s=slide('Forecast demonstration results','One retrospective held-out 30-minute example',
 'OBSERVED: exact log errors reproduced by fresh inference are A MAE 0.2188352957 and RMSE 0.2566354851, B MAE 0.0943474238 and RMSE 0.1090553488. The table rounds to six decimals. These are absolute and squared errors between log10 actual and log10 predicted flux, summarized across only 30 target minutes for each channel. Both values are in dex, not W/m² or a percentage. The formula uses n=30 and e_t = y_t − ŷ_t in log space. June training support has 2880 observations. The first eligible August example was selected chronologically using complete-case masks, not by lowest error. No aggregate evaluation, uncertainty interval or significance result follows from this single window. These selected models are BIC-preferred within the d=1 training groups, not necessarily the lowest-error models across all families at this one origin. Archived V1 multi-origin scores use a different protocol and are intentionally kept separate.',modelSources);
 table(s,rows,58,189,1164,204,[240,310,307,307],29);
 text(s,'MAE = (1/n) Σ |eₜ|',62,445,550,58,31,C.orange);
 text(s,'RMSE = √[(1/n) Σ eₜ²]',650,445,570,58,31,C.cyan);
 text(s,'n = 30 target minutes per channel.  Errors use log₁₀ irradiance.',62,524,1150,48,25,C.muted);
 take(s,'These values do not represent overall forecasting skill',608);
}
// 17: Deployment architecture with actual screenshot.
{
 const s=slide('Local Streamlit deployment','Thin presentation layer over reusable scientific and inference modules',
 'OBSERVED: the local Streamlit app has Overview, Data Explorer, Time-Series Analysis and Model Results views. The actual screenshot shows the current application, not a design mockup. Native interactive observations on the original views cover May–June. The later evidence tables and decomposition use the full May–August collection or the stated June segment. The architecture keeps manifest verification, native loading, diagnostics, saved-parameter inference and evaluation in UI-independent modules. Streamlit loads verified outputs and displays Plotly charts and tables. Scientific fitting occurs in the offline builder. Dashboard rendering and saved-model replay do not refit the ARIMA model. This is a local offline demonstration, not public production hosting or an operational warning service. A future frontend can reuse the core, but this task does not implement React or FastAPI.',['streamlit_app.py','src/solar_flare_jepa/dashboard/time_series.py','src/solar_flare_jepa/presentation/time_series.py','src/solar_flare_jepa/presentation/classical.py']);
 await image(s,'dashboard_explorer.png',44,174,809,438,'Actual local Streamlit Data Explorer screenshot');
 text(s,'Scientific core',892,192,327,42,28,C.orange,true);
 text(s,'Pinned data and QC\nReusable diagnostics',892,242,327,88,25);
 text(s,'Saved inference',892,357,327,42,28,C.cyan,true);
 text(s,'Frozen parameters\nPast context only',892,407,327,87,25);
 text(s,'Streamlit views',892,522,327,42,28,C.orange,true);
 text(s,'Charts and tables',892,570,327,43,25);
 text(s,'Screenshot: original interactive observation scope is May–June 2024',60,635,1160,25,17,C.muted);
}
// 18: Actual replay UI.
{
 const s=slide('Saved-model inference in the dashboard','Detail of the actual Streamlit replay action and XRS-A forecast',
 'OBSERVED: this screenshot comes from the running local Streamlit Model Results view after clicking Run saved-model inference. The app filters the selected frozen parameters on the saved 120-minute context, aligns all 30 forecast timestamps with the saved payload, and checks channel metrics before reporting replay success. No future target values enter infer(), and no fitting occurs when pressing this action. The displayed saved actual values support retrospective scoring. The screenshot and capture metadata identify the pinned source commit. The original archived V1 comparison appears elsewhere on the same long page and uses a different multi-origin protocol. It should not be conflated with the separate single-window classical teaching demonstration shown here. Local files and dependencies are required; operational uptime, delivery latency and live alerts remain outside the demonstrated scope.',['streamlit_app.py','src/solar_flare_jepa/dashboard/time_series.py','tests/test_time_series_ui.py']);
 await image(s,'dashboard_replay_detail.png',44,170,1190,451,'Actual Streamlit replay button, success message and complete XRS-A forecast panel');
 take(s,'Issue: 1 August 2024, 02:00 UTC. 120 past bins, 30 target bins',625,C.muted);
}
// 19: Conclusion and limits.
{
 const s=slide('Conclusion and future improvements','A reproducible classical analysis with explicit scientific boundaries',
 'OBSERVED: the project now has pinned GOES collection, EDA, quality analysis, complementary stationarity tests, transformations, exploratory STL, dependence analysis, bounded nonseasonal model identification, training IC selection and verified local inference. INFERRED: these support a defensible educational demonstration. UNKNOWN: overall operational forecasting skill, stable physical seasonality, real delivery latency and event-level flare warning performance. A four-month collection and one short demonstration cannot establish generalization across solar regimes. Future work should assess many held-out chronological origins against persistence baselines, use leakage-controlled tuning, evaluate residual dependence and changing variance, and calibrate uncertainty on separate support. Seasonal modeling should follow evidence for a stable period. Event-level forecasting requires an independently defined flare catalogue/label rule and operational evaluation. None of those future results is claimed here.',['docs/PRESENTATION_TIME_SERIES_CHECKLIST.md','docs/PRESENTATION_TIME_SERIES_VERIFICATION.md','docs/PRESENTATION_TIME_SERIES_GUIDE.md']);
 text(s,'What the evidence supports',60,186,570,45,29,C.orange,true);
 text(s,'Verified GOES data and diagnostics\nBounded classical model comparison\nReproducible local inference',60,254,565,174,28);
 text(s,'What needs further evaluation',684,186,540,45,29,C.cyan,true);
 text(s,'Many chronological forecast origins\nResidual checks and uncertainty\nRegime robustness and delivery latency',684,254,540,174,28);
 text(s,'SARIMA awaits a defensible stable period',60,494,1160,47,30,C.orange);
 text(s,'Operational solar-flare forecasting remains unestablished',60,578,1160,60,30,C.text,true);
}
// 20: The professor's 11 original requirements.
{
 const s=slide('Professor’s 11-requirement summary','All topics covered, with the SARIMA applicability decision disclosed',
 'This final matrix maps the professor’s eleven original requirements to the actual slides. The expanded fifteen-topic user request organizes the same content, with introduction, limitations and conclusion in addition. OBSERVED: collection, EDA, missing-value handling, stationarity, transformations, exploratory decomposition, ACF/PACF, lag selection, IC comparison and local deployment are implemented. Model identification covers AR, MA, ARMA and ARIMA. SARIMA is scientifically deferred because stable seasonality is not established. The repository therefore conservatively records ten requirements complete and requirement 8 partial under a literal rule requiring a fit of every family. Rubric acceptance of a justified SARIMA deferral is UNKNOWN and belongs to the assessor. Do not describe all eleven as unconditionally complete. The slides provide the available evidence and explain that remaining boundary.',['docs/PRESENTATION_TIME_SERIES_CHECKLIST.md']);
 const rows=[['Requirement','Slides','Coverage'],['1  Data collection','2','Verified'],['2  EDA and descriptive statistics','3–7','Actual plots and tables'],['3  Missing values','7','QC masks, no imputation'],['4  Stationarity testing','8','ADF + KPSS'],['5  Transformations','9','Log + first difference'],['6  Seasonal decomposition','10','Exploratory STL'],['7  ACF / PACF','11–12','Actual dependence plots'],['8  Model identification','13–14','Nonseasonal fits, SARIMA deferred'],['9  Lag selection','12–14','p, d, q and training BIC'],['10  AIC / BIC','14','Compatible comparisons'],['11  Model deployment','17–18','Local saved-model inference']];
 table(s,rows,58,171,1164,432,[490,130,544],23,[],0);
 text(s,'Ten requirements complete. #8 remains partial under an all-family fitting rubric.',60,628,1160,35,23,C.orange);
}

await fs.writeFile(path.join(build,'slide_content.json'),JSON.stringify(slideContent,null,2));
await fs.writeFile(path.join(build,'objects.json'),JSON.stringify(objects,null,2));
const candidate=path.join(build,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(candidate);
console.log('Draft exported:',candidate);
for(let i=0;i<P.slides.items.length;i++) {
 const png=await P.export({slide:P.slides.items[i],format:'png',scale:2});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));
 const layout=await P.slides.items[i].export({format:'layout'});
 await fs.writeFile(path.join(build,`slide-${String(i+1).padStart(2,'0')}.layout.json`),await layout.text());
 console.log('Rendered slide',i+1);
}
const validated=path.join(build,'export/validated.pptx');
await fs.mkdir(path.dirname(validated),{recursive:true});
const owners=[2,7,8,13,14,16,20];
await finalizePresentation({
 workspaceDir:root,candidatePath:candidate,finalPath:validated,pythonExecutable:python,
 integrityValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_package_integrity.py'),
 layoutValidatorPath:path.join(skillDir,'container_tools/inspect_presentation_layout_geometry.py'),
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:20,requiredNativeTableOwnerSlides:owners,
 requiredNativeChartOwnerSlides:[],fontPolicy:{basis:'design',families:[font]},
 verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json'),
});
await fs.copyFile(validated,path.join(output,'SolarJEPA_Final_Time_Series_Presentation.pptx'));
// The bundled direct PDF exporter lacks its standard-fonts module on this host.
// Export the inspected 192-dpi slide renders with ReportLab instead, preserving
// exact appearance and slide order without modifying bundled dependencies.
execFileSync(python,[path.join(root,'scripts/presentation/export_pdf.py'),
 '--render-dir',build,'--output',path.join(output,'SolarJEPA_Final_Time_Series_Presentation.pdf')],{stdio:'inherit'});
console.log(JSON.stringify({slides:P.slides.items.length,pptx:path.join(output,'SolarJEPA_Final_Time_Series_Presentation.pptx'),pdf:path.join(output,'SolarJEPA_Final_Time_Series_Presentation.pdf')}));
