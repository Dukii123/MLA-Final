from pathlib import Path
import csv, json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker
from matplotlib import font_manager

# Bon hinh Tuan 10, ve tu week10_results.json, test_predictions_week10.csv va speaker_errors_test.csv
# (ket qua that cua week10_analysis.py). Mau theo loai dac trung: log-mel xanh, wav2vec 2.0 cam, ngau nhien xam.
P = Path(__file__).parent
_mac_font = Path('/System/Library/Fonts/Supplemental/Times New Roman.ttf')
if _mac_font.exists(): font_manager.fontManager.addfont(str(_mac_font))  # Windows tu dong thay Times New Roman
plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 9, 'text.color': 'black', 'axes.labelcolor': 'black',
                     'xtick.color': 'black', 'ytick.color': 'black', 'axes.edgecolor': '#8a8a86', 'axes.linewidth': 0.8,
                     'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300, 'savefig.facecolor': 'white'})
BLUE, ORANGE, GREEN, GREY, GRID = '#2a78d6', '#eb6834', '#1baf7a', '#8a8a86', '#e4e3df'
vn = lambda x, n: f'{x:.{n}f}'.replace('.', ',')
comma = matplotlib.ticker.FuncFormatter(lambda v, _: vn(v, 1))
R = json.loads((P/'week10_results.json').read_text())['models']
pred = list(csv.DictReader((P/'test_predictions_week10.csv').open()))
y = np.array([float(r['target_total']) for r in pred]); low = y < 6
spk = list(csv.DictReader((P/'speaker_errors_test.csv').open()))
log = ['--- Figures ---']

# Hinh 1: bieu do cham recall@10% (rong) va recall@20% (dac)
names = [('Ngẫu nhiên / hằng số', 'Ngẫu nhiên', GREY), ('SVR chỉ độ dài', 'SVR chỉ độ dài (2 đặc trưng)', GREEN),
         ('SVR log-mel bỏ độ dài', 'SVR log-mel bỏ độ dài', BLUE), ('SVR log-mel', 'SVR log-mel', BLUE), ('RF log-mel', 'RF log-mel', BLUE),
         ('SVR log-mel + trọng số', 'SVR log-mel + trọng số', BLUE), ('LR phân loại cân bằng', 'LR phân loại cân bằng', BLUE),
         ('RF phân loại cân bằng', 'RF phân loại cân bằng', BLUE), ('SVR wav2vec 2.0', 'SVR wav2vec 2.0', ORANGE)]
fig, ax = plt.subplots(figsize=(6.3, 3.0))
for i, (k, lab, col) in enumerate(names[::-1]):
    r10, r20 = R[k]['test']['recall10']*100, R[k]['test']['recall20']*100
    ax.plot([r10, r20], [i, i], color=col, lw=2, alpha=0.45, zorder=1, solid_capstyle='round')
    ax.scatter(r10, i, s=46, facecolor='white', edgecolor=col, linewidth=1.6, zorder=3)
    ax.scatter(r20, i, s=46, color=col, edgecolor='white', linewidth=1, zorder=3)
    ax.text(r20 + 2, i, f'{r20:.0f}%', va='center', fontsize=8)
    ax.text(r10 - 2, i, f'{r10:.0f}%', va='center', ha='right', fontsize=8)
ax.set_yticks(range(len(names)), [n for _, n, _ in names[::-1]])
ax.set_xlim(0, 100); ax.set_xlabel('Recall bài dưới 6 trên test (%)')
ax.scatter([], [], s=40, facecolor='white', edgecolor='black', label='Nghe lại 10% bài thấp nhất')
ax.scatter([], [], s=40, color='black', label='Nghe lại 20% bài thấp nhất')
ax.legend(frameon=False, fontsize=8, loc='lower center', bbox_to_anchor=(0.5, 1.0), ncol=2); ax.grid(axis='x', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P/'fig1_recall.png', bbox_inches='tight'); plt.close(fig)

# Hinh 2: duong cong nghe lai x% bai thap nhat -> bat duoc bao nhieu % bai duoi 6
frac = np.linspace(0, 1, 101)
def curve(p):
    order = np.argsort(p, kind='stable'); hit = np.concatenate([[0], np.cumsum(low[order])])
    return np.array([hit[int(round(f*len(p)))]/low.sum()*100 for f in frac])
fig, ax = plt.subplots(figsize=(3.15, 2.7))
ideal = np.minimum(frac*len(y)/low.sum(), 1)*100
ax.plot(frac*100, ideal, color=GREY, lw=1, ls=':', label='Lý tưởng')
ax.plot(frac*100, frac*100, color=GREY, lw=1, ls='--', label='Ngẫu nhiên')
cl, cw = curve(np.array([float(r['SVR log-mel']) for r in pred])), curve(np.array([float(r['SVR wav2vec 2.0']) for r in pred]))
cd = curve(np.array([float(r['SVR chỉ độ dài']) for r in pred]))
ax.plot(frac*100, cd, color=GREEN, lw=1.6, label='SVR chỉ độ dài'); ax.plot(frac*100, cl, color=BLUE, lw=2, label='SVR log-mel'); ax.plot(frac*100, cw, color=ORANGE, lw=2, label='SVR wav2vec 2.0')
for x in (10, 20): ax.axvline(x, color=GRID, lw=0.8, zorder=0)
ax.set_xlim(0, 60); ax.set_ylim(0, 100); ax.set_xlabel('Số bài giáo viên nghe lại (%)'); ax.set_ylabel('Bài dưới 6 bắt được (%)')
ax.legend(frameon=False, fontsize=7.5, loc='lower right'); ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P/'fig2_curve.png', bbox_inches='tight'); plt.close(fig)
i30 = 30
log.append(f"fig2_curve.png | listen 30%: length-only {cd[i30]:.0f}%, log-mel {cl[i30]:.0f}%, wav2vec2 {cw[i30]:.0f}% of below-6")

# Hinh 3: cot nhom do lech trung binh (du doan - that) theo khoang diem that
edges = [0, 5, 6, 7, 8, 9, 10.01]; labels = ['≤ 4', '5', '6', '7', '8', '≥ 9']
bins = np.digitize(y, edges[1:-1])
bias = {k: [float((np.array([float(r[k]) for r in pred])[bins == b] - y[bins == b]).mean()) for b in range(len(labels))] for k in ['SVR log-mel', 'SVR wav2vec 2.0']}
counts = [int((bins == b).sum()) for b in range(len(labels))]
fig, ax = plt.subplots(figsize=(3.15, 2.7)); xx = np.arange(len(labels)); w = 0.38
ax.bar(xx - w/2 - 0.01, bias['SVR log-mel'], w, color=BLUE, label='SVR log-mel', zorder=2)
ax.bar(xx + w/2 + 0.01, bias['SVR wav2vec 2.0'], w, color=ORANGE, label='SVR wav2vec 2.0', zorder=2)
ax.axhline(0, color='black', lw=0.8)
ax.set_xticks(xx, [f'{l}\n(n={c})' for l, c in zip(labels, counts)], fontsize=7.5)
ax.set_xlabel('Điểm thật (total trong scores.json)'); ax.set_ylabel('Dự đoán − thật (điểm)'); ax.yaxis.set_major_formatter(comma)
ax.legend(frameon=False, fontsize=7.5, loc='upper right'); ax.grid(axis='y', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P/'fig3_bias.png', bbox_inches='tight'); plt.close(fig)
log.append("fig3_bias.png | mean (pred - true) for total <= 4: log-mel " + f"{bias['SVR log-mel'][0]:+.2f}, wav2vec2 {bias['SVR wav2vec 2.0'][0]:+.2f} (n={counts[0]})")

# Hinh 4: box plot MAE theo nguoi noi, tach tuoi, so log-mel va wav2vec 2.0
age = np.array([int(r['age']) for r in spk])
data, pos, cols = [], [], []
for g, (m, base) in enumerate([(age <= 12, 0), (age > 12, 3)]):
    for j, (key, col) in enumerate([('MAE_svr_logmel', BLUE), ('MAE_svr_w2v', ORANGE)]):
        data.append(np.array([float(r[key]) for r in spk])[m]); pos.append(base + j*1.05); cols.append(col)
fig, ax = plt.subplots(figsize=(6.3, 2.4))
bp = ax.boxplot(data, positions=pos, widths=0.75, vert=False, patch_artist=True, showfliers=True,
                medianprops={'color': 'black', 'lw': 1.2}, flierprops={'marker': 'o', 'markersize': 3, 'markeredgecolor': GREY},
                whiskerprops={'color': GREY}, capprops={'color': GREY})
for patch, col in zip(bp['boxes'], cols): patch.set_facecolor(col); patch.set_alpha(0.75); patch.set_edgecolor('white')
ax.set_yticks([0.52, 3.52], [f'Trẻ em ≤ 12 tuổi\n({int((age <= 12).sum())} người)', f'Người lớn > 12 tuổi\n({int((age > 12).sum())} người)'])
ax.set_xlabel('MAE theo từng người nói trên test (điểm)'); ax.xaxis.set_major_formatter(comma)
ax.add_patch(plt.Rectangle((0, 0), 0, 0, color=BLUE, label='SVR log-mel')); ax.add_patch(plt.Rectangle((0, 0), 0, 0, color=ORANGE, label='SVR wav2vec 2.0'))
ax.legend(frameon=False, fontsize=8, loc='center right', ncol=2); ax.grid(axis='x', color=GRID, lw=0.6); ax.set_axisbelow(True)
fig.savefig(P/'fig4_speakers.png', bbox_inches='tight'); plt.close(fig)
log.append(f"fig1_recall.png, fig4_speakers.png | {len(names)} models, {len(spk)} test speakers")
json.dump({'curve_listen30': {'length': float(cd[i30]), 'logmel': float(cl[i30]), 'w2v': float(cw[i30])}, 'bias_by_bin': {'labels': labels, 'counts': counts, **bias}},
          (P/'figure_stats.json').open('w'), indent=2)
(P/'figure_run.log').write_text('\n'.join(log)+'\n')
print('\n'.join(log))
