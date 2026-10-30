from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager

# Ve Hinh 1 cua bao cao tu model_results.json va test_predictions.csv (ket qua that cua train_models.py).
P = Path(__file__).parent
font_manager.fontManager.addfont('/System/Library/Fonts/Supplemental/Times New Roman.ttf')
plt.rcParams.update({'font.family':'Times New Roman','font.size':10,'text.color':'black','axes.labelcolor':'black',
                     'xtick.color':'black','ytick.color':'black','axes.edgecolor':'#8a8a86','axes.linewidth':0.8})
R = json.loads((P/'model_results.json').read_text())['results']
rows = list(csv.DictReader((P/'test_predictions.csv').open()))
y = np.array([float(r['target']) for r in rows]); svr = np.array([float(r['SVR']) for r in rows])
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
BLUE, GRID = '#2a78d6', '#e4e3df'

fig, (a, b) = plt.subplots(1, 2, figsize=(6.3, 2.75), dpi=300, gridspec_kw={'width_ratios':[1, 1.25], 'wspace':0.38})
names = [('constant','Hằng số'), ('SVR','SVR'), ('RF','Random Forest')]
mae = [R[k]['test']['MAE'] for k,_ in names]
bars = a.bar([n for _,n in names], mae, width=0.5, color=BLUE, zorder=2)
for bar, v in zip(bars, mae):
    a.text(bar.get_x()+bar.get_width()/2, v+0.03, vn(v,3), ha='center', va='bottom', fontsize=9.5)
a.set_ylim(0, 1.35); a.set_ylabel('MAE trên test (điểm)', fontsize=9)
a.set_title('(a) MAE trên test, thấp hơn là tốt hơn', fontsize=10, loc='left')
a.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: vn(v, 1)))
a.grid(axis='y', color=GRID, lw=0.6, zorder=0); a.set_axisbelow(True)

lo, hi = 0, 10
b.scatter(y, svr, s=5, color=BLUE, alpha=0.35, linewidths=0, zorder=2)
b.plot([lo, hi], [lo, hi], color='#52514e', lw=1, ls='--', zorder=3)
b.text(3.1, 2.3, 'y = x (dự đoán đúng)', ha='left', va='center', fontsize=9, color='#52514e')
b.set_xlim(lo, hi); b.set_ylim(lo, hi); b.set_aspect('equal')
b.set_xlabel('Target thật (trung bình 5 giám khảo)', fontsize=9); b.set_ylabel('SVR dự đoán', fontsize=9)
b.set_title(f'(b) SVR trên {len(y):,} câu test'.replace(',', '.'), fontsize=10, loc='left')
b.text(0.4, 9.6, f"PCC = {vn(R['SVR']['test']['PCC'],2)}\nMAE = {vn(R['SVR']['test']['MAE'],2)}", ha='left', va='top', fontsize=9)
b.grid(color=GRID, lw=0.6, zorder=0); b.set_axisbelow(True)
for ax in (a, b):
    ax.spines[['top','right']].set_visible(False); ax.tick_params(labelsize=9)
fig.savefig(P/'figure_results.png', bbox_inches='tight', facecolor='white')
low=y<6
log=["--- [7] Figure from test predictions ---",f"Saved figure_results.png | test points: {len(y)} | SVR prediction range: {svr.min():.2f}..{svr.max():.2f}",
     f"Targets < 6: {low.sum()} utterances | SVR mean (pred - true): {(svr[low]-y[low]).mean():+.2f} | targets >= 6: {(svr[~low]-y[~low]).mean():+.2f}"]
(P/'figure_run.log').write_text('\n'.join(log)+'\n')
json.dump({'low_threshold':6,'n_low':int(low.sum()),'svr_bias_low':float((svr[low]-y[low]).mean()),'svr_bias_high':float((svr[~low]-y[~low]).mean()),'svr_pred_min':float(svr.min()),'svr_pred_max':float(svr.max())},(P/'figure_stats.json').open('w'),indent=2)
print('\n'.join(log))
