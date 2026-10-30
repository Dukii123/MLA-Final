from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib.lines import Line2D
from matplotlib import font_manager

# Ba hinh Tuan 11, ve tu week11_results.json + test_predictions_week11.csv (lan chay chinh thuc).
# Kieu moi so voi tuan 10: (1) lollipop CV-vs-test, (2) grouped bar theo nua doc nhanh/cham, (3) histogram giay/tu.
# Mau theo loai dac trung: log-mel xanh #2a78d6, wav2vec 2.0 cam #eb6834, chi do dai xanh luc #1baf7a, ngau nhien xam #8a8a86.
P = Path(__file__).parent
_mac = Path('/System/Library/Fonts/Supplemental/Times New Roman.ttf')
_win = Path('C:/Windows/Fonts/times.ttf')
for f in (_mac, _win):
    if f.exists():
        font_manager.fontManager.addfont(str(f)); break
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 9, 'text.color': 'black', 'axes.labelcolor': 'black',
                     'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': '#8a8a86', 'axes.linewidth': 0.8,
                     'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300, 'savefig.facecolor': 'white'})
BLUE, ORANGE, GREEN, GREY, GRID = '#2a78d6', '#eb6834', '#1baf7a', '#8a8a86', '#e4e3df'
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
comma = matplotlib.ticker.FuncFormatter(lambda v, _: vn(v, 1))
R = json.loads((P / 'week11_results.json').read_text(encoding='utf-8'))
pred = list(csv.DictReader((P / 'test_predictions_week11.csv').open(encoding='utf-8')))
y = np.array([float(r['target_total']) for r in pred]); spw = np.array([float(r['sec_per_word']) for r in pred])
log = ['--- Figures week11 ---']

# ---------------- Hinh 1: lollipop CV (rong, kem SD) vs test (dac) cho moi cau hinh ----------------
rows = [('SVR log-mel', BLUE), ('RF log-mel', BLUE), ('SVR log-mel bỏ độ dài', BLUE), ('SVR log-mel + trọng số', BLUE),
        ('LR phân loại cân bằng', BLUE), ('RF phân loại cân bằng', BLUE), ('SVR chỉ độ dài', GREEN),
        ('SVR wav2vec 2.0', ORANGE), ('SVR wav2vec + độ dài', ORANGE), ('LR phân loại cân bằng (wav2vec)', ORANGE),
        ('Ngẫu nhiên / hằng số', GREY)]
fig, ax = plt.subplots(figsize=(6.3, 4.1))
for i, (k, col) in enumerate(rows[::-1]):
    t = R['models'][k]['test']['recall20'] * 100
    cv = R['cv_table'].get(k)
    if cv:
        c = cv['recall20'][0] * 100; sd = cv['recall20'][1] * 100
        ax.plot([c, t], [i, i], color=GREY, lw=1.0, alpha=0.55, zorder=1)
        ax.errorbar(c, i, xerr=sd, fmt='o', ms=5.2, mfc='white', mec=col, mew=1.6, ecolor=col, elinewidth=1.0, capsize=2.5, zorder=3)
    ax.scatter(t, i, s=26, color=col, edgecolor='white', linewidth=0.8, zorder=4)
    ax.text(t, i - 0.34, f'{t:.0f}%', va='top', ha='center', fontsize=7.5)
ax.set_yticks(range(len(rows)), [r[0] for r in rows[::-1]])
ax.set_ylim(-0.7, len(rows) - 0.15)
ax.set_xlim(0, 100); ax.set_xlabel('Recall@20% trên test cho bài dưới 6 (%)')
ax.axvline(20, color=GREY, lw=0.8, ls=':', zorder=0)
ax.text(21, len(rows) - 1.0, 'ngẫu nhiên 20%', fontsize=7, color=GREY, va='center')
ax.legend(handles=[Line2D([], [], marker='o', ls='', mfc='white', mec='black', ms=5.5, label='CV (TB ± SD, GroupKFold-5)'),
                   Line2D([], [], marker='o', ls='', color='black', ms=5.5, label='Test (chạy một lần)')],
          frameon=False, fontsize=7.5, loc='lower center', bbox_to_anchor=(0.5, 1.01), ncol=2)
ax.grid(axis='x', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P / 'fig1_cv_test.png', bbox_inches='tight'); plt.close(fig)
log.append('fig1_cv_test.png | CV vs test recall@20 for all configurations')

# ---------------- Hinh 2: grouped bar recall@20% theo nua doc nhanh / doc cham ----------------
h = R['halves']; sides = ['fast', 'slow']
lab = {s: ('Đọc nhanh' if s == 'fast' else 'Đọc chậm') + '\n(giây/từ ' + ('<' if s == 'fast' else '≥') + ' trung vị)\n' +
          f"n={h[s]['n']} · dưới 6: {h[s]['n_below6']}" for s in sides}
fig, ax = plt.subplots(figsize=(4.6, 3.3)); xx = np.arange(2); w = 0.34
for j, (m, title, col) in enumerate([('length', 'SVR chỉ độ dài', GREEN), ('w2v', 'SVR wav2vec 2.0', ORANGE)]):
    vals = [h[s]['recall20'][m] * 100 for s in sides]
    bars = ax.bar(xx + (j - 0.5) * w, vals, w, color=col, label=title, zorder=2)
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 2.2, f"{b.get_height():.0f}%",
                ha='center', va='bottom', fontsize=7.5)
ax.axhline(20, color=GREY, lw=0.9, ls='--', zorder=1, label='Ngẫu nhiên 20%')
ax.set_xticks(xx, [lab[s] for s in sides]); ax.set_ylim(0, 115); ax.set_xlim(-0.6, 1.6); ax.set_ylabel('Recall@20% trong từng nửa (%)')
ax.legend(frameon=False, fontsize=7.5, loc='upper center', ncol=3, bbox_to_anchor=(0.5, 1.13))
ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P / 'fig2_halves.png', bbox_inches='tight'); plt.close(fig)
log.append(f"fig2_halves.png | fast: length {h['fast']['recall20']['length']*100:.0f}% vs w2v {h['fast']['recall20']['w2v']*100:.0f}%; "
           f"slow: length {h['slow']['recall20']['length']*100:.0f}% vs w2v {h['slow']['recall20']['w2v']*100:.0f}%")

# ---------------- Hinh 3: phan bo giay/tu tren test, vach trung vi ----------------
thr = h['threshold_sec_per_word']; fast = spw < thr
fig, ax = plt.subplots(figsize=(4.6, 2.9))
ax.hist(spw, bins=30, color=GREY, alpha=0.75, edgecolor='white', zorder=2)
ax.axvline(thr, color='black', lw=1.2, ls='--', zorder=3)
ymax = ax.get_ylim()[1]
ax.set_ylim(0, ymax * 1.22)
ax.set_title(f"n = {int(fast.sum())} câu đọc nhanh ({h['fast']['n_below6']} bài dưới 6) · "
             f"{int((~fast).sum())} câu đọc chậm ({h['slow']['n_below6']} bài dưới 6)", fontsize=7.5)
ax.text(0.03, 0.96, 'Đọc nhanh', fontsize=7.5, ha='left', transform=ax.transAxes, va='top')
ax.text(0.97, 0.96, 'Đọc chậm', fontsize=7.5, ha='right', transform=ax.transAxes, va='top')
ax.text(thr + 0.02, 0.96, f'trung vị {vn(thr, 2)} s/từ', fontsize=7.5, rotation=0, transform=ax.get_xaxis_transform(), va='top')
ax.set_xlabel('Giây trên mỗi từ (test)'); ax.set_ylabel('Số câu'); ax.xaxis.set_major_formatter(comma)
ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P / 'fig3_speed_dist.png', bbox_inches='tight'); plt.close(fig)
log.append(f"fig3_speed_dist.png | median sec/word {thr:.3f}; fast {int(fast.sum())} utt, slow {int((~fast).sum())} utt")

stats = {'listen20': {k: R['models'][k]['test']['recall20'] for k, _ in rows if k != 'Ngẫu nhiên / hằng số'},
         'halves': {s: {'n': h[s]['n'], 'n_below6': h[s]['n_below6'], 'recall20': h[s]['recall20']} for s in sides},
         'speed': {'median': thr, 'n_fast': int(fast.sum()), 'n_slow': int((~fast).sum()),
                   'below6_fast': h['fast']['n_below6'], 'below6_slow': h['slow']['n_below6']}}
(P / 'figure_stats.json').write_text(json.dumps(stats, indent=2, ensure_ascii=False), encoding='utf-8')
(P / 'figure_run.log').write_text('\n'.join(log) + '\n', encoding='utf-8')
print('\n'.join(log))
