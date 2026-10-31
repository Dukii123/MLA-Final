'use strict';

/* Demo nội bộ MLA Nhóm 05. Mọi số hiển thị lấy từ /api/meta, /api/results,
   /api/utterances hoặc kết quả chấm trả về từ server. Không có số bịa. */

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const state = {
  meta: null,
  results: null,
  utts: [],
  byId: new Map(),
  tab: 'overview',
  learn: 'qa',
  // giáo viên
  budget: 0.2,
  model: 'SVR wav2vec 2.0',
  search: '',
  limit: 12,
  ranking: [],
  showAllModels: false,
  revealed: new Set(),
  // chấm thử
  scoreFile: null,
  scoreMode: null,
  activeSample: null,
  scoreBusy: false,
  transcriptAuto: '',
  record: { recorder: null, stream: null, chunks: [], started: 0, timer: null, autoStop: null, busy: false },
  // phiếu chấm nhóm
  group: {
    data: null,
    fileLabel: '',
    pauses: [],
    marks: [],
    speed: 'vừa',
    audio: null,
    stopAt: 0,
    fullPlaying: false,
    reviews: [],
  },
  // ngân sách ở tab Học
  learnBudget: 20,
  // biểu đồ
  compressionModel: 'SVR wav2vec 2.0',
  charts: { compression: null, recall: null },
  // audio
  player: null,
  toastTimer: null,
};

const FAMILY_LABEL = {
  'log-mel': 'log-mel',
  'wav2vec': 'wav2vec 2.0',
  'length': 'độ dài câu',
  'classifier': 'phân loại',
  'random': 'ngẫu nhiên',
};

const COLORS = {
  wav2vec: '#eb6834',
  logmel: '#2a78d6',
  length: '#1baf7a',
  random: '#8a8a86',
  ink: '#122019',
  muted: '#647168',
  line: '#cfc5b3',
};

const GROUP_KEY = 'mla_group_reviews_v1';

/* ---------------- Định dạng ---------------- */
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({
  '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
}[c]));

function fmt(n, digits = 0) {
  if (n === null || n === undefined || !Number.isFinite(Number(n))) return '—';
  return Number(n).toLocaleString('vi-VN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function fmtTrim(n) {
  if (!Number.isFinite(Number(n))) return '—';
  return Number(n).toLocaleString('vi-VN', { maximumFractionDigits: 2 });
}

function pct(x, digits = 0) {
  if (!Number.isFinite(Number(x))) return '—';
  return fmt(Number(x) * 100, digits) + '%';
}

function median(values) {
  const a = values.map(Number).sort((x, y) => x - y);
  if (!a.length) return 0;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

function mean(values) {
  return values.length ? values.reduce((s, v) => s + Number(v), 0) / values.length : 0;
}

function svg(name, cls = 'icon') {
  return `<svg class="${cls}"><use href="#i-${name}"/></svg>`;
}

function toast(message) {
  const el = $('#toast');
  el.textContent = message;
  el.classList.remove('hidden');
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => el.classList.add('hidden'), 3200);
}

async function fetchJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) {
    let msg = `Lỗi HTTP ${r.status}`;
    try {
      const j = await r.json();
      if (j.detail) msg = typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail);
    } catch (_) { /* giữ nguyên */ }
    throw new Error(msg);
  }
  return r.json();
}

/* ---------------- Khởi động ---------------- */
async function init() {
  bindTabs();
  bindOverview();
  bindPlayer();
  bindMedian();
  bindScore();
  bindGroup();
  bindLearn();
  bindTeacher();

  try {
    const [meta, results, utts] = await Promise.all([
      fetchJSON('/api/meta'),
      fetchJSON('/api/results'),
      fetchJSON('/api/utterances'),
    ]);
    state.meta = meta;
    state.results = results;
    state.utts = utts;
    state.byId = new Map(utts.map((u) => [u.id, u]));
    state.model = meta.teacher_models.includes('SVR wav2vec 2.0')
      ? 'SVR wav2vec 2.0' : meta.teacher_models[0];

    renderOverview();
    populateTeacherSelect();
    renderTeacher();
    initWorst5();
    initMedianValues();
    renderFiveDots();
    routeFromHash();
    pollStatus();
    setInterval(pollStatus, 5000);
  } catch (err) {
    $('#modelTableBody').innerHTML = `<tr><td colspan="6" class="loading-cell">Không tải được dữ liệu: ${esc(err.message)}</td></tr>`;
    $('#serverLabel').textContent = 'Chưa kết nối được máy chủ';
    $('#serverDot').className = 'dot err';
    toast('Không tải được dữ liệu demo. Kiểm tra cửa sổ chạy server.');
  }
}

/* ---------------- Điều hướng ---------------- */
function bindTabs() {
  $('#tabs').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-tab]');
    if (b) go(b.dataset.tab);
  });

  document.addEventListener('click', (e) => {
    const step = e.target.closest('.script-step');
    if (step) {
      go(step.dataset.go || 'overview', step.dataset.learn || null);
      if (step.dataset.sampleGo) {
        setTimeout(() => runSample(step.dataset.sampleGo), 240);
      }
      return;
    }
    const nav = e.target.closest('[data-go]');
    if (nav) {
      go(nav.dataset.go, nav.dataset.learn || null);
      return;
    }
    const learn = e.target.closest('[data-learn]');
    if (learn) go('learn', learn.dataset.learn);
  });

  window.addEventListener('hashchange', routeFromHash);
}

function go(tab, learn = null, opts = {}) {
  const changedTab = state.tab !== tab;
  state.tab = tab;
  $$('#tabs button').forEach((b) => b.classList.toggle('active', b.dataset.tab === tab));
  $$('.tab-panel').forEach((p) => p.classList.toggle('active', p.id === `tab-${tab}`));

  if (tab === 'learn') {
    setLearn(learn || state.learn);
  } else if (learn) {
    setLearn(learn);
  }

  const hash = tab === 'learn' ? `#learn/${state.learn}` : `#${tab}`;
  if (opts.hash !== false) {
    try { history.replaceState(null, '', hash); } catch (_) { /* file:// */ }
  }

  if (opts.scroll !== false) {
    if (changedTab) window.scrollTo({ top: 0, behavior: 'smooth' });
    else if (tab === 'learn') {
      const nav = $('#learnNav');
      const header = $('.site-header');
      if (nav) {
        const top = nav.getBoundingClientRect().top + window.scrollY
          - (header?.offsetHeight || 0) - 14;
        window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
      }
    }
  }
  if (tab === 'learn') requestAnimationFrame(() => ensureLearnCharts(state.learn));
}

function setLearn(name) {
  const valid = $$('#learnNav button').map((b) => b.dataset.learn);
  state.learn = valid.includes(name) ? name : 'qa';
  $$('#learnNav button').forEach((b) => b.classList.toggle('active', b.dataset.learn === state.learn));
  $$('.learn-section').forEach((s) => s.classList.toggle('active', s.id === `learn-${state.learn}`));
}

function routeFromHash() {
  const raw = (location.hash || '#overview').replace(/^#/, '');
  const [tab, learn] = raw.split('/');
  const valid = ['overview', 'teacher', 'score', 'learn'];
  if (!valid.includes(tab)) { go('overview', null, { hash: false }); return; }
  go(tab, learn || null, { hash: false, scroll: false });
}

function ensureLearnCharts(section) {
  if (!state.results) return;
  if (section === 'compression') ensureCompressionChart();
  if (section === 'budget') ensureRecallChart();
}

/* ---------------- Tổng quan ---------------- */
function bindOverview() {
  $('#toggleAllModels').addEventListener('click', () => {
    state.showAllModels = !state.showAllModels;
    renderModelTable();
  });
}

function budgetStats(model, frac) {
  const ranked = getRanking(model);
  const k = Math.round(state.utts.length * frac);
  const top = ranked.slice(0, k);
  const caught = top.filter((r) => r.u.below6).length;
  return {
    k, caught, recall: caught / belowTotal(), precision: k ? caught / k : 0,
    expected: belowTotal() * (k / state.utts.length),
  };
}

function belowTotal() {
  return state.results?.below6?.test?.[0] ?? 330;
}

function getRanking(model = state.model) {
  const random = model === 'Ngẫu nhiên / hằng số';
  return state.utts
    .map((u) => ({ u, score: random ? u.rand : Number(u.pred[model] ?? 0) }))
    .sort((a, b) => a.score - b.score || a.u.id.localeCompare(b.u.id));
}

function renderOverview() {
  const w2v = budgetStats('SVR wav2vec 2.0', 0.2);
  const len = budgetStats('SVR chỉ độ dài', 0.2);
  const total = belowTotal();

  $('#mRecall20').textContent = pct(w2v.recall, 0);
  $('#mCaught').textContent = fmt(w2v.caught);
  $('#mRecallLen').textContent = pct(len.recall, 0);
  $('#mRandom').textContent = '20%';
  $('#mBase').textContent = pct(state.results.base_rate_test, 1);
  $('#mTarget').textContent = fmt(state.results.target_check.floor_median);

  const top3 = getRanking('SVR wav2vec 2.0').slice(0, 3);
  $('#heroList').innerHTML = top3.map(({ u, score }) => `
    <div class="mini-row">
      <div>
        <div class="mini-title">${esc(u.text)}</div>
        <div class="mini-sub"><span>${esc(u.id)}</span><span>${fmt(u.age)} tuổi</span><span class="mini-score">${fmt(score, 2)}</span></div>
      </div>
      <button class="play-round" data-play="${esc(u.id)}" aria-label="Nghe bài ${esc(u.id)}">${svg('play')}</button>
    </div>`).join('');

  $('#heroList').onclick = (e) => {
    const b = e.target.closest('[data-play]');
    if (!b) return;
    const u = state.byId.get(b.dataset.play);
    if (u) openPlayer(makePlayerItem(u, 'SVR wav2vec 2.0'), 'test');
  };

  renderModelTable();
}

function renderModelTable() {
  if (!state.meta) return;
  const all = state.meta.models || [];
  const compactKeys = [
    'SVR wav2vec 2.0', 'SVR log-mel', 'RF log-mel', 'SVR chỉ độ dài',
    'SVR log-mel bỏ độ dài', 'Ngẫu nhiên / hằng số',
  ];
  const rows = state.showAllModels ? all : all.filter((m) => compactKeys.includes(m.key));

  $('#modelTableBody').innerHTML = rows.map((m) => {
    const cv = m.cv?.recall20;
    const test = m.test || {};
    const mae = Number.isFinite(test.MAE) ? fmt(test.MAE, 3) : '—';
    const pcc = Number.isFinite(test.PCC) ? fmt(test.PCC, 3) : '—';
    const main = m.key === 'SVR wav2vec 2.0' ? '<span class="badge ok">chính</span>' : '';
    return `<tr>
      <td><div class="model-name"><span class="family-dot" style="background:${esc(m.color)}"></span>${esc(m.label)} ${main}</div></td>
      <td><span class="family-label">${esc(FAMILY_LABEL[m.family] || m.family)}</span></td>
      <td class="num">${cv ? `${fmt(cv[0] * 100, 1)}% ± ${fmt(cv[1] * 100, 1)}` : '—'}</td>
      <td class="num val-strong">${pct(test.recall20, 0)}</td>
      <td class="num">${mae}</td>
      <td class="num">${pcc}</td>
    </tr>`;
  }).join('');

  const btn = $('#toggleAllModels');
  btn.textContent = state.showAllModels ? 'Thu gọn' : 'Xem đủ 11 mô hình';
}

/* ---------------- Chế độ giáo viên ---------------- */
function bindTeacher() {
  $('#budgetSeg').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-budget]');
    if (!b) return;
    state.budget = Number(b.dataset.budget);
    $$('#budgetSeg button').forEach((x) => x.classList.toggle('active', x === b));
    state.limit = 12;
    renderTeacher();
  });

  $('#teacherModel').addEventListener('change', (e) => {
    state.model = e.target.value;
    state.limit = 12;
    renderTeacher();
  });

  let t = null;
  $('#teacherSearch').addEventListener('input', (e) => {
    clearTimeout(t);
    t = setTimeout(() => {
      state.search = e.target.value.trim().toLowerCase();
      renderTeacherRows();
    }, 140);
  });

  $('#loadMoreBtn').addEventListener('click', () => {
    state.limit += 12;
    renderTeacherRows();
  });

  $('#downloadCsv').addEventListener('click', downloadCsv);

  $('#teacherBody').addEventListener('click', (e) => {
    const reveal = e.target.closest('[data-reveal]');
    if (reveal) {
      toggleReveal(reveal.dataset.reveal);
      return;
    }
    const play = e.target.closest('[data-play]');
    if (play) {
      const u = state.byId.get(play.dataset.play);
      if (u) openPlayer(makePlayerItem(u, state.model), 'test');
    }
  });
}

function populateTeacherSelect() {
  const sel = $('#teacherModel');
  sel.innerHTML = state.meta.teacher_models
    .map((k) => `<option value="${esc(k)}"${k === state.model ? ' selected' : ''}>${esc(k)}</option>`)
    .join('');
}

function renderTeacher() {
  if (!state.results) return;
  const stats = budgetStats(state.model, state.budget);
  const total = belowTotal();
  const baseRate = total / state.utts.length;
  state.ranking = getRanking(state.model);

  $('#budgetCount').textContent = fmt(stats.k);
  $('#recallValue').textContent = pct(stats.recall, 1);
  $('#recallFrac').textContent = `${fmt(stats.caught)}/${fmt(total)} bài dưới 6`;
  $('#precisionValue').textContent = pct(stats.precision, 0);
  $('#precisionText').textContent = `${fmt(stats.caught)}/${fmt(stats.k)} bài nghe được là dưới 6`;
  if (state.model === 'Ngẫu nhiên / hằng số') {
    $('#randomCompare').textContent = 'mức nền';
    $('#randomText').textContent = `Kỳ vọng ~${fmt(stats.expected)}/${fmt(total)} bài; lần này ${fmt(stats.caught)}`;
  } else {
    $('#randomCompare').textContent = `${fmt(stats.recall / baseRate, 1)}×`;
    $('#randomText').textContent = `Nghe ngẫu nhiên bắt ~${fmt(stats.expected)}/${fmt(total)} bài`;
  }

  const missed = total - stats.caught;
  const budgetPct = Math.round(state.budget * 100);
  const extra = state.budget === 0.1 || state.budget === 0.2
    ? '' : ' Mức này được tính thêm từ cùng bộ dự đoán đã lưu.';
  $('#teacherNote').innerHTML = state.model === 'Ngẫu nhiên / hằng số'
    ? `<b>Đây là mức nền:</b> xếp hạng ngẫu nhiên ${fmt(stats.k)} bài, bắt ${fmt(stats.caught)}/${fmt(total)} bài dưới 6 (${pct(stats.recall, 1)}). Mọi mô hình nên được so với mức này.`
    : `<b>Đọc đúng con số:</b> ở ngân sách ${budgetPct}%, mô hình bắt ${fmt(stats.caught)}/${fmt(total)} bài dưới 6 (${pct(stats.recall, 1)}); precision ${pct(stats.precision, 0)}. Còn ${fmt(missed)} bài dưới 6 nằm ngoài danh sách.${extra}`;

  renderTeacherRows();
}

function renderTeacherRows() {
  if (!state.results) return;
  const k = Math.round(state.utts.length * state.budget);
  const ranking = state.ranking;
  const searching = state.search.length > 0;
  const isRandom = state.model === 'Ngẫu nhiên / hằng số';
  let items;
  if (searching) {
    items = ranking
      .map((r, i) => ({ ...r, rank: i + 1 }))
      .filter(({ u }) => u.id.includes(state.search) || u.text.toLowerCase().includes(state.search))
      .slice(0, 60);
  } else {
    items = ranking.slice(0, Math.min(state.limit, k)).map((r, i) => ({ ...r, rank: i + 1 }));
  }

  $('#teacherBody').innerHTML = items.length ? items.map(({ u, score, rank }) => {
    const revealed = state.revealed.has(u.id);
    const trueCell = revealed
      ? `<span class="true-value${u.below6 ? ' low' : ''}">${fmt(u.total, 1)}</span>${u.below6 ? ' <span class="badge low">dưới 6</span>' : ''}`
      : '<span class="true-hidden">•••</span>';
    return `<tr data-id="${esc(u.id)}">
      <td class="rank">${rank}</td>
      <td class="utt-cell">
        <div class="utt-text">${esc(u.text)}</div>
        <div class="utt-id"><span>${esc(u.id)}</span><span>${fmt(u.words)} từ</span><span>${fmt(u.sec_per_word, 2)} giây/từ</span></div>
      </td>
      <td class="spk-cell">${esc(u.speaker)}<small>${fmt(u.age)} tuổi</small></td>
      <td>${isRandom ? '<span class="family-label">ngẫu nhiên</span>' : `<span class="pred-score">${fmt(score, 2)}</span>`}</td>
      <td class="true-cell" data-true-cell="${esc(u.id)}">${trueCell}</td>
      <td><div class="row-actions">
        <button class="play-btn" data-play="${esc(u.id)}" aria-label="Nghe bài ${esc(u.id)}">${svg('play')}</button>
        <button class="reveal-btn" data-reveal="${esc(u.id)}">${revealed ? 'Ẩn' : 'Lộ điểm'}</button>
      </div></td>
    </tr>`;
  }).join('') : `<tr><td colspan="6" class="loading-cell">${searching ? 'Không tìm thấy mã bài hoặc câu đọc khớp.' : 'Không có bài trong ngân sách này.'}</td></tr>`;

  const shown = items.length;
  $('#tableMeta').textContent = searching
    ? `${fmt(shown)} kết quả khớp “${state.search}” trên toàn bộ 2.500 bài`
    : `Ngân sách ${Math.round(state.budget * 100)}% · ${fmt(k)} bài · xếp tăng dần theo điểm dự đoán`;
  $('#tableFootNote').textContent = searching
    ? 'Tìm kiếm chỉ lọc danh sách hiển thị; các con số phía trên vẫn tính trên toàn bộ ngân sách.'
    : `Đang hiện ${fmt(shown)}/${fmt(Math.min(k, ranking.length))} bài ưu tiên. Bấm nghe để mở trình phát; điểm thật bị ẩn cho tới khi bạn lộ.`;

  const more = $('#loadMoreBtn');
  const remain = Math.min(k, ranking.length) - shown;
  if (!searching && remain > 0) {
    more.classList.remove('hidden');
    more.textContent = `Xem thêm (còn ${fmt(remain)})`;
  } else {
    more.classList.add('hidden');
  }
}

function paintTrueCell(id) {
  const u = state.byId.get(id);
  if (!u) return;
  const cell = $(`[data-true-cell="${id}"]`);
  if (!cell) return;
  cell.innerHTML = state.revealed.has(id)
    ? `<span class="true-value${u.below6 ? ' low' : ''}">${fmt(u.total, 1)}</span>${u.below6 ? ' <span class="badge low">dưới 6</span>' : ''}`
    : '<span class="true-hidden">•••</span>';
  $$(`[data-reveal="${id}"]`).forEach((b) => { b.textContent = state.revealed.has(id) ? 'Ẩn' : 'Lộ điểm'; });
}

function revealRow(id) {
  state.revealed.add(id);
  paintTrueCell(id);
}

function toggleReveal(id) {
  if (state.revealed.has(id)) state.revealed.delete(id);
  else state.revealed.add(id);
  paintTrueCell(id);
}

function downloadCsv() {
  if (!state.ranking.length) return;
  const k = Math.round(state.utts.length * state.budget);
  const cell = (v) => {
    const s = String(v ?? '');
    return /[;"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const isRandom = state.model === 'Ngẫu nhiên / hằng số';
  const lines = [['Hang', 'Ma bai', 'Nguoi noi', 'Tuoi', 'Cau doc', 'Diem du doan', 'Diem that', 'Duoi 6', 'Trong ngan sach']];
  state.ranking.forEach(({ u, score }, i) => {
    lines.push([
      i + 1, u.id, u.speaker, u.age, u.text, isRandom ? 'ngau nhien' : fmt(score, 3), fmt(u.total, 1),
      u.below6 ? 'co' : 'khong', i < k ? 'co' : 'khong',
    ]);
  });
  const csv = '\uFEFFsep=;\r\n' + lines.map((r) => r.map(cell).join(';')).join('\r\n');
  downloadBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }),
    `nhom05_uu_tien_nghe_${Math.round(state.budget * 100)}pct.csv`);
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 4000);
}

/* ---------------- Trình phát audio ---------------- */
function makePlayerItem(u, model) {
  const random = model === 'Ngẫu nhiên / hằng số';
  return {
    id: u.id,
    text: u.text,
    speaker: u.speaker,
    age: u.age,
    total: u.total,
    five: u.five,
    predVal: random ? null : u.pred[model],
    predName: random ? 'Xếp ngẫu nhiên' : model,
    mode: 'test',
  };
}

function bindPlayer() {
  const audio = $('#playerAudio');
  const toggle = $('#playerToggle');
  const player = $('#player');

  toggle.addEventListener('click', () => {
    if (!audio.src) return;
    if (audio.paused) audio.play().catch(() => toast('Không phát được audio này.'));
    else audio.pause();
  });

  const syncIcon = () => {
    const icon = audio.paused ? 'play' : 'pause';
    toggle.innerHTML = svg(icon);
    toggle.setAttribute('aria-label', audio.paused ? 'Phát' : 'Tạm dừng');
  };
  audio.addEventListener('play', syncIcon);
  audio.addEventListener('pause', syncIcon);

  audio.addEventListener('timeupdate', () => {
    const d = Number.isFinite(audio.duration) && audio.duration > 0 ? audio.duration : 0;
    const p = d ? Math.min(100, (audio.currentTime / d) * 100) : 0;
    $('#playerFill').style.width = `${p}%`;
    $('#playerTime').textContent = `${clock(audio.currentTime)} / ${clock(d)}`;
  });
  audio.addEventListener('loadedmetadata', () => {
    $('#playerTime').textContent = `0:00 / ${clock(audio.duration)}`;
  });
  audio.addEventListener('ended', () => {
    syncIcon();
    $('#playerFill').style.width = '0%';
  });

  const seek = (e) => {
    if (!Number.isFinite(audio.duration) || !audio.duration) return;
    const r = $('#playerTrack').getBoundingClientRect();
    const ratio = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
    audio.currentTime = ratio * audio.duration;
  };
  $('#playerTrack').addEventListener('click', seek);
  $('#playerTrack').addEventListener('keydown', (e) => {
    if (!Number.isFinite(audio.duration) || !audio.duration) return;
    if (e.key === 'ArrowLeft') { audio.currentTime = Math.max(0, audio.currentTime - 5); e.preventDefault(); }
    if (e.key === 'ArrowRight') { audio.currentTime = Math.min(audio.duration, audio.currentTime + 5); e.preventDefault(); }
    if (e.key === 'Home') { audio.currentTime = 0; e.preventDefault(); }
    if (e.key === 'End') { audio.currentTime = audio.duration; e.preventDefault(); }
  });

  $('#playerClose').addEventListener('click', () => {
    audio.pause();
    player.classList.add('hidden');
    state.player = null;
  });

  $('#playerReveal').addEventListener('click', () => {
    const item = state.player;
    if (!item) return;
    revealRow(item.id);
    const suffix = ` · điểm thật ${fmt(item.total, 1)}${item.total < 6 ? ' (dưới 6)' : ''}`;
    $('#playerSub').textContent = `${item.id} · người nói ${item.speaker} · ${fmt(item.age)} tuổi · ${item.predName}: ${fmt(item.predVal, 2)}${suffix}`;
    $('#playerReveal').textContent = `Điểm thật: ${fmt(item.total, 1)}`;
    $('#playerReveal').disabled = true;
  });
}

function openPlayer(item, mode = 'test') {
  const audio = $('#playerAudio');
  state.player = item;
  audio.pause();
  audio.src = mode === 'worst' ? `/audio/worst5/${item.id}` : `/audio/${item.id}`;
  audio.load();
  const btn = $('#playerReveal');
  btn.disabled = false;
  btn.textContent = 'Lộ điểm thật';
  if (mode === 'worst') {
    btn.textContent = `Điểm thật: ${fmt(item.total, 1)}`;
    btn.disabled = true;
  }
  $('#playerTitle').textContent = item.text || item.id;
  $('#playerSub').textContent = `${item.id} · người nói ${item.speaker} · ${fmt(item.age)} tuổi · ${item.predName}: ${fmt(item.predVal, 2)}`;
  $('#playerTime').textContent = '0:00';
  $('#playerFill').style.width = '0%';
  $('#player').classList.remove('hidden');
  audio.play().catch(() => { /* trình duyệt chặn autoplay: người dùng bấm nút phát */ });
}

function clock(sec) {
  if (!Number.isFinite(sec) || sec < 0) return '0:00';
  const s = Math.round(sec);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`;
}

/* ---------------- Chấm thử ---------------- */
function bindScore() {
  const dz = $('#dropzone');
  const input = $('#fileInput');

  dz.addEventListener('click', () => input.click());
  dz.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); }
  });
  input.addEventListener('change', () => {
    if (input.files?.[0]) pickFile(input.files[0]);
    input.value = '';
  });
  ['dragenter', 'dragover'].forEach((ev) => dz.addEventListener(ev, (e) => {
    e.preventDefault();
    dz.classList.add('drag');
  }));
  ['dragleave', 'drop'].forEach((ev) => dz.addEventListener(ev, (e) => {
    e.preventDefault();
    dz.classList.remove('drag');
  }));
  dz.addEventListener('drop', (e) => {
    const f = e.dataTransfer?.files?.[0];
    if (f) pickFile(f);
  });

  $('#recordBtn').addEventListener('click', startRecording);
  $('#stopBtn').addEventListener('click', () => stopRecording());
  $('#scoreBtn').addEventListener('click', () => {
    if (state.scoreMode === 'sample' && state.activeSample) {
      runSample(state.activeSample);
      return;
    }
    if (state.scoreMode === 'file' && state.scoreFile) {
      scoreFile(state.scoreFile);
      return;
    }
    toast('Chọn file audio hoặc câu mẫu trước.');
  });

  $$('.chip-btn[data-sample]').forEach((b) => {
    b.addEventListener('click', () => runSample(b.dataset.sample));
  });
}

function pickFile(file) {
  if (!/^audio\//.test(file.type) && !/\.(wav|mp3|m4a|ogg|webm|flac|aac)$/i.test(file.name)) {
    toast('File này không giống audio. Thử WAV, MP3, M4A hoặc ghi âm trực tiếp.');
    return;
  }
  if (file.size > 25 * 1024 * 1024) {
    toast('File quá lớn (giới hạn 25 MB).');
    return;
  }
  if (file.size < 2000) {
    toast('File quá nhỏ hoặc rỗng.');
    return;
  }
  if (state.transcriptAuto && $('#transcript').value === state.transcriptAuto) {
    $('#transcript').value = '';
  }
  state.transcriptAuto = '';
  state.scoreFile = file;
  state.scoreMode = 'file';
  state.activeSample = null;
  const size = file.size < 1024 * 1024 ? `${fmt(file.size / 1024, 0)} KB` : `${fmt(file.size / 1048576, 1)} MB`;
  const strong = $('#dropzone strong');
  const span = $('#dropzone span');
  strong.textContent = file.name;
  span.textContent = `${size} · bấm để đổi file · tối đa 25 MB`;
  $('#recordState').textContent = 'File đã sẵn sàng để chấm.';
  $$('.chip-btn[data-sample]').forEach((b) => b.classList.remove('active'));
  hideGroup();
}

async function scoreFile(file) {
  if (state.scoreBusy) return;
  scoreBusy(true);
  scoreLoading('Đang đọc audio và trích đặc trưng…');
  const slowTimer = setTimeout(() => {
    scoreLoading('Đang chấm. Lần đầu wav2vec 2.0 có thể mất 20–60 giây để nạp model…');
  }, 5000);

  try {
    const fd = new FormData();
    fd.append('file', file, file.name || 'audio.wav');
    fd.append('transcript', $('#transcript').value.trim());
    const data = await fetchJSON('/api/score', { method: 'POST', body: fd });
    renderScore(data, { fileName: file.name });
  } catch (err) {
    scoreError(err.message);
  } finally {
    clearTimeout(slowTimer);
    scoreBusy(false);
  }
}

async function runSample(kind) {
  if (state.scoreBusy || !state.meta) return;
  const id = state.meta.samples?.[kind];
  if (!id) return;
  const u = state.byId.get(id);
  state.scoreMode = 'sample';
  state.activeSample = kind;
  $$('.chip-btn[data-sample]').forEach((b) => b.classList.toggle('active', b.dataset.sample === kind));
  scoreBusy(true);
  scoreLoading(`Đang chấm câu mẫu ${id}…`);
  const slowTimer = setTimeout(() => {
    scoreLoading('Đang chấm. Lần đầu wav2vec 2.0 có thể mất 20–60 giây để nạp model…');
  }, 5000);
  try {
    const q = u?.text ? `?transcript=${encodeURIComponent(u.text)}` : '';
    const data = await fetchJSON(`/api/score-sample/${id}${q}`);
    renderScore(data, { sampleId: id, fileName: `Câu mẫu ${id}` });
  } catch (err) {
    scoreError(err.message);
  } finally {
    clearTimeout(slowTimer);
    scoreBusy(false);
  }
}

function scoreBusy(busy) {
  state.scoreBusy = busy;
  $('#scoreBtn').disabled = busy;
  $$('.chip-btn[data-sample]').forEach((b) => { b.disabled = busy; });
  $('#recordBtn').disabled = busy;
}

function scoreLoading(message) {
  hideGroup();
  $('#scoreEmpty').classList.add('hidden');
  $('#scoreResult').classList.remove('hidden');
  $('#scoreResult').innerHTML = `<div class="scoring-state"><div class="spinner"></div><p>${esc(message)}</p></div>`;
}

function scoreError(message) {
  hideGroup();
  $('#scoreEmpty').classList.add('hidden');
  $('#scoreResult').classList.remove('hidden');
  $('#scoreResult').innerHTML = `<div class="scoring-state">
    <div class="empty-orbit" style="background:var(--w2v-soft);color:var(--danger)">${svg('alert', 'icon big')}</div>
    <h3 style="font-family:var(--serif);color:var(--ink)">Không chấm được</h3>
    <p>${esc(message)}</p>
    <button class="btn ghost small" id="retryScore">Thử lại</button>
  </div>`;
  const retry = $('#retryScore');
  if (retry) retry.addEventListener('click', () => {
    if (state.scoreMode === 'sample' && state.activeSample) runSample(state.activeSample);
    else if (state.scoreFile) scoreFile(state.scoreFile);
    else toast('Chọn file hoặc câu mẫu rồi thử lại.');
  });
}

function renderScore(d, context = {}) {
  const preds = d.predictions || {};
  const comparators = [
    ['SVR wav2vec 2.0', preds.wav2vec, COLORS.wav2vec, 'wav2vec'],
    ['SVR log-mel', preds.logmel, COLORS.logmel, 'log-mel'],
    ['SVR chỉ độ dài', preds.length, COLORS.length, 'độ dài'],
  ];
  const pctLeft = Math.max(0, Math.min(100, Number(d.percentile) || 0));

  const compareRows = comparators.map(([label, value, color, note]) => {
    const width = Number.isFinite(value) ? Math.max(0, Math.min(100, (value / 10) * 100)) : 0;
    return `<div class="compare-row">
      <span>${esc(note)}</span>
      <div class="compare-bar"><i style="width:${width}%;background:${color}"></i></div>
      <span class="compare-val">${Number.isFinite(value) ? fmt(value, 2) : '—'}</span>
    </div>`;
  }).join('');

  const proba = Math.max(0, Math.min(1, Number(d.below6_prob) || 0));
  const probaRow = `<div class="compare-row">
      <span>P(dưới 6)</span>
      <div class="compare-bar"><i style="width:${proba * 100}%;background:${COLORS.random}"></i></div>
      <span class="compare-val">${pct(proba, 0)}</span>
    </div>`;

  const gt = d.ground_truth;
  const gtBox = gt ? `
    <div class="gt-box">
      <div class="gt-line"><span>Điểm thật <b>total</b> · 5 giám khảo</span><b>${fmt(gt.total, 1)}</b></div>
      ${fiveDotsHtml(gt.five, 'five-scores')}
      <div class="gt-note">Câu mẫu ${esc(gt.id)} · ${esc(gt.text)} · dự đoán trong báo cáo tuần 11: wav2vec ${fmt(gt.pred_report?.wav2vec, 2)}, log-mel ${fmt(gt.pred_report?.logmel, 2)}${gt.below6 ? ' · đây là bài thật sự dưới 6.' : ''}</div>
    </div>` : `
    <div class="gt-box">
      <div class="gt-note">File tải lên không có điểm thật. Đây là mức ưu tiên để nghe lại, không phải điểm chấm chính thức.</div>
    </div>`;

  $('#scoreEmpty').classList.add('hidden');
  $('#scoreResult').classList.remove('hidden');
  $('#scoreResult').innerHTML = `
    <div class="score-hero">
      <div>
        <span class="score-label">Điểm dự đoán · wav2vec 2.0</span>
        <div class="score-number">${fmt(d.score, 2)}<small>/10</small></div>
      </div>
      <span class="priority-pill ${esc(d.priority)}">${esc(d.priority_label)}</span>
    </div>
    <div class="percentile-block">
      <div class="percentile-labels"><span>0%</span><span>20%</span><span>50%</span><span>100%</span></div>
      <div class="percentile-track"><div class="percentile-marker" style="left:${pctLeft}%"></div></div>
      <p class="percentile-caption">Cao hơn ${fmt(d.percentile, 1)}% trong 2.500 bài test. Ngưỡng 20% thấp nhất của wav2vec là ${fmt(d.cutoffs?.wav2vec?.p20, 2)} điểm.</p>
    </div>
    <div class="compare-block">
      <div class="compare-title">Ba mô hình trên cùng file</div>
      ${compareRows}${probaRow}
    </div>
    <div class="meta-row">
      <span class="meta-pill">${fmt(d.duration, 2)} giây</span>
      ${d.words ? `<span class="meta-pill">${fmt(d.words)} từ</span>` : '<span class="meta-pill">chưa nhập câu đọc</span>'}
      ${d.sec_per_word ? `<span class="meta-pill">${fmt(d.sec_per_word, 2)} giây/từ</span>` : ''}
      <span class="meta-pill">${context.fileName ? esc(context.fileName) : 'audio tải lên'}</span>
    </div>
    ${gtBox}
    <p class="disclaimer">Điểm bị nén về giữa thang 0–10. Mức ưu tiên dựa trên xếp hạng 2.500 bài test, không phải xác suất đúng. Giáo viên vẫn cần nghe để kết luận.</p>`;

  if (context.sampleId) {
    const u = state.byId.get(context.sampleId);
    if (u) {
      $('#transcript').value = u.text;
      state.transcriptAuto = u.text;
    }
  }
  renderGroup(d, context);
  if (window.matchMedia('(max-width: 1000px)').matches) {
    $('#resultCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

/* ---------------- Phiếu chấm nhóm ---------------- */
function pauseTime(sec) {
  const s = Number(sec);
  if (!Number.isFinite(s) || s < 0) return '0:00,00';
  const m = Math.floor(s / 60);
  return `${m}:${(s - m * 60).toFixed(2).padStart(5, '0').replace('.', ',')}`;
}

function reviewDate(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return '';
  return d.toLocaleString('vi-VN', { hour: '2-digit', minute: '2-digit', day: '2-digit', month: '2-digit' });
}

function loadGroupReviews() {
  try {
    const arr = JSON.parse(localStorage.getItem(GROUP_KEY) || '[]');
    return Array.isArray(arr) ? arr : [];
  } catch (_) {
    return [];
  }
}

function persistGroupReviews() {
  try {
    localStorage.setItem(GROUP_KEY, JSON.stringify(state.group.reviews));
  } catch (_) {
    toast('Không lưu được vào trình duyệt. Thử xuất CSV ngay.');
  }
}

function bindGroup() {
  state.group.reviews = loadGroupReviews();
  renderSavedReviews();
  hideGroup();

  $('#gSpeed').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-speed]');
    if (!b) return;
    state.group.speed = b.dataset.speed;
    $$('#gSpeed button').forEach((x) => x.classList.toggle('active', x === b));
  });

  $('#gPauseList').addEventListener('click', (e) => {
    const play = e.target.closest('[data-play]');
    if (play) {
      playGroupPause(Number(play.dataset.play), play);
      return;
    }
    const mark = e.target.closest('button[data-mark]');
    if (!mark) return;
    const row = mark.closest('[data-pause-index]');
    if (!row) return;
    const i = Number(row.dataset.pauseIndex);
    state.group.marks[i] = mark.dataset.mark;
    $$('button[data-mark]', row).forEach((x) => x.classList.toggle('active', x === mark));
  });

  $('#gSave').addEventListener('click', saveGroupReview);
  $('#gReset').addEventListener('click', resetGroupForm);
  $('#gPlayAll').addEventListener('click', toggleGroupFull);
  $('#jumpGroup').addEventListener('click', jumpToGroup);
  $('#gExport').addEventListener('click', exportGroupCsv);
  $('#gClearAll').addEventListener('click', clearGroupReviews);
  $('#gSavedList').addEventListener('click', (e) => {
    const del = e.target.closest('[data-del-review]');
    if (del) deleteGroupReview(del.dataset.delReview);
  });
}

function jumpToGroup() {
  const card = $('#groupCard');
  const header = document.querySelector('.site-header') || document.querySelector('header');
  if (!card) return;
  const top = card.getBoundingClientRect().top + window.scrollY - (header?.offsetHeight || 0) - 14;
  window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
}

function hideGroup() {
  const card = $('#groupCard');
  if (!card) return;
  card.classList.remove('hidden');
  $('#groupEmpty')?.classList.remove('hidden');
  $('#groupBody')?.classList.add('hidden');
  $('#gPlayAll')?.classList.add('hidden');
  const badge = $('#groupAutoSpeed');
  if (badge) badge.textContent = 'Chưa chấm bài';
  const hint = $('#gSpeedHint');
  if (hint) hint.textContent = 'app đo để tham khảo';
  const count = $('#gPauseCount');
  if (count) count.textContent = '';
  state.group.data = null;
  state.group.pauses = [];
  state.group.marks = [];
  state.group.stopAt = 0;
  state.group.fullPlaying = false;
  setGroupFull(false);
  if (state.group.audio) state.group.audio.pause();
  $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
}

function setGroupFull(on) {
  const btn = $('#gPlayAll');
  if (!btn) return;
  btn.querySelector('use').setAttribute('href', on ? '#i-pause' : '#i-play');
  btn.querySelector('span').textContent = on ? 'Dừng' : 'Nghe cả bài';
}

function toggleGroupFull() {
  const a = state.group.audio;
  if (!a || !a.src) {
    toast('Chưa có audio để nghe lại. Chấm lại bài để tạo bản mới.');
    return;
  }
  if (!a.paused) {
    a.pause();
    return;
  }
  $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
  state.group.stopAt = 0;
  a.currentTime = 0;
  state.group.fullPlaying = true;
  setGroupFull(true);
  a.play().catch(() => {
    state.group.fullPlaying = false;
    setGroupFull(false);
    toast('Trình duyệt không phát được audio. Bấm lại thử.');
  });
}

function ensureGroupAudio(url) {
  if (!state.group.audio) {
    const a = new Audio();
    a.preload = 'auto';
    a.addEventListener('timeupdate', () => {
      if (state.group.stopAt && a.currentTime >= state.group.stopAt) {
        a.pause();
        state.group.stopAt = 0;
        $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
      }
    });
    a.addEventListener('pause', () => {
      state.group.fullPlaying = false;
      setGroupFull(false);
      if (a.paused) $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
    });
    a.addEventListener('ended', () => {
      state.group.stopAt = 0;
      state.group.fullPlaying = false;
      setGroupFull(false);
      $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
    });
    state.group.audio = a;
  }
  const a = state.group.audio;
  a.pause();
  state.group.stopAt = 0;
  state.group.fullPlaying = false;
  setGroupFull(false);
  if (url) {
    a.src = url;
    a.load();
  } else {
    a.removeAttribute('src');
  }
}

function playGroupPause(i, btn) {
  const p = state.group.pauses[i];
  const a = state.group.audio;
  if (!p || !a || !a.src) {
    toast('Không còn audio để nghe lại. Chấm lại bài để tạo bản mới.');
    return;
  }
  $$('.pause-play.playing').forEach((b) => b.classList.remove('playing'));
  a.pause();
  state.group.fullPlaying = false;
  setGroupFull(false);
  a.currentTime = Math.max(0, p.start - 0.25);
  const dur = Number.isFinite(a.duration) && a.duration > 0 ? a.duration : p.end + 2;
  state.group.stopAt = Math.min(dur, p.end + 0.35);
  btn.classList.add('playing');
  a.play().catch(() => {
    btn.classList.remove('playing');
    toast('Trình duyệt không phát được đoạn này. Bấm lại thử.');
  });
}

function renderGroup(d, context = {}) {
  const sp = d.speech || {};
  const speed = sp.speed || {};
  const pauses = Array.isArray(sp.pauses) ? sp.pauses : [];
  state.group.data = d;
  state.group.pauses = pauses;
  state.group.marks = pauses.map(() => 'ok');
  state.group.fileLabel = context.fileName || 'audio tải lên';
  ensureGroupAudio(d.audio_url || '');
  $('#groupEmpty').classList.add('hidden');
  $('#groupBody').classList.remove('hidden');
  $('#gPlayAll').classList.toggle('hidden', !d.audio_url);

  $('#gReader').value = '';
  $('#gNote').value = '';
  state.group.speed = speed.label || 'vừa';
  $$('#gSpeed button').forEach((b) => b.classList.toggle('active', b.dataset.speed === state.group.speed));

  if (Number.isFinite(speed.sec_per_word)) {
    $('#gSpeedHint').textContent = `gợi ý ${fmt(speed.sec_per_word, 2)} giây/từ · ${speed.label || '—'} so với mốc ${fmt(speed.median_ref, 3)}`;
    $('#groupAutoSpeed').textContent = `Tự đo: ${fmt(speed.sec_per_word, 2)} giây/từ · ${speed.label || '—'}`;
  } else {
    $('#gSpeedHint').textContent = 'chưa có câu đọc để đo giây/từ';
    $('#groupAutoSpeed').textContent = 'Chưa đo được tốc độ';
  }

  const punct = Number(sp.punctuation_marks) || 0;
  $('#gPauseCount').textContent = Number(sp.words)
    ? `${pauses.length} khoảng · ${punct} dấu câu`
    : `${pauses.length} khoảng`;

  if (!pauses.length) {
    $('#gPauseList').innerHTML = '<div class="pause-empty">Không thấy khoảng lặng ≥ 0,25 giây. Nếu tai nghe thấy ngắt, ghi rõ vào phần ghi chú.</div>';
  } else {
    $('#gPauseList').innerHTML = pauses.map((p, i) => `
      <div class="pause-row" data-pause-index="${i}">
        <button class="pause-play" data-play="${i}" aria-label="Nghe khoảng ngắt ${i + 1}" ${d.audio_url ? '' : 'disabled'}>
          <svg class="icon"><use href="#i-play"/></svg>
        </button>
        <div class="pause-time">
          <b>${pauseTime(p.start)} – ${pauseTime(p.end)}</b>
          <span>${fmt(p.dur, 2)} giây · bắt đầu ở ${fmt(p.start, 2)} giây</span>
        </div>
        <div class="pause-mark">
          <button data-mark="ok" class="active">Đúng</button>
          <button data-mark="bad">Sai</button>
        </div>
      </div>`).join('');
  }

  $('#groupCard').classList.remove('hidden');
}

function resetGroupForm() {
  $('#gReader').value = '';
  $('#gEvaluator').value = '';
  $('#gNote').value = '';
  state.group.marks = state.group.pauses.map(() => 'ok');
  $$('#gPauseList [data-mark]').forEach((b) => b.classList.toggle('active', b.dataset.mark === 'ok'));
  toast('Đã xoá form chấm.');
}

function saveGroupReview() {
  const d = state.group.data;
  if (!d) {
    toast('Chấm một bài trước rồi lưu phiếu.');
    return;
  }
  const reader = $('#gReader').value.trim();
  if (!reader) {
    $('#gReader').focus();
    toast('Nhập tên người đọc trước.');
    return;
  }
  const pauses = state.group.pauses;
  const wrong = pauses.filter((_, i) => state.group.marks[i] === 'bad');
  const record = {
    id: (crypto.randomUUID ? crypto.randomUUID() : String(Date.now())),
    at: new Date().toISOString(),
    reader,
    evaluator: $('#gEvaluator').value.trim() || 'Nhóm',
    speed: state.group.speed,
    sec_per_word: d.speech?.speed?.sec_per_word ?? d.sec_per_word ?? null,
    fileLabel: state.group.fileLabel,
    ai_score: Number.isFinite(Number(d.score)) ? Number(d.score) : null,
    pause_count: pauses.length,
    wrong: wrong.map((p) => ({ start: p.start, end: p.end, dur: p.dur })),
    note: $('#gNote').value.trim(),
  };
  state.group.reviews.unshift(record);
  persistGroupReviews();
  renderSavedReviews();
  toast(`Đã lưu phiếu cho ${reader}.`);
}

function renderSavedReviews() {
  const reviews = state.group.reviews;
  $('#groupSavedCard').classList.toggle('hidden', !reviews.length);
  $('#gSavedCount').textContent = `${reviews.length} phiếu`;
  if (!reviews.length) {
    $('#gSavedList').innerHTML = '<div class="saved-empty">Chưa có phiếu. Chấm một bài, nghe từng khoảng ngắt rồi bấm “Lưu phiếu”.</div>';
    return;
  }
  $('#gSavedList').innerHTML = reviews.map((r) => {
    const wrong = Array.isArray(r.wrong) ? r.wrong : [];
    return `<div class="saved-item">
      <div class="saved-main"><b>${esc(r.reader)}</b><span>${esc(r.evaluator || 'Nhóm')} · ${esc(reviewDate(r.at))}</span></div>
      <div class="saved-speed">${esc(r.speed || '—')}</div>
      <div class="saved-note">${esc(r.note || '—')}</div>
      <div class="saved-meta">${esc(r.fileLabel || 'audio')}<br>${wrong.length ? `${wrong.length} chỗ ngắt bị đánh sai` : 'không đánh dấu ngắt sai'}</div>
      <button class="saved-del" data-del-review="${esc(r.id)}" aria-label="Xoá phiếu">×</button>
    </div>`;
  }).join('');
}

function deleteGroupReview(id) {
  if (!confirm('Xoá phiếu này?')) return;
  state.group.reviews = state.group.reviews.filter((r) => String(r.id) !== String(id));
  persistGroupReviews();
  renderSavedReviews();
  toast('Đã xoá phiếu.');
}

function clearGroupReviews() {
  if (!state.group.reviews.length) {
    toast('Chưa có phiếu để xoá.');
    return;
  }
  if (!confirm('Xoá tất cả phiếu chấm nhóm đã lưu trên máy này?')) return;
  state.group.reviews = [];
  persistGroupReviews();
  renderSavedReviews();
  toast('Đã xoá tất cả phiếu.');
}

function exportGroupCsv() {
  if (!state.group.reviews.length) {
    toast('Chưa có phiếu để xuất.');
    return;
  }
  const cell = (v) => {
    const s = String(v ?? '');
    return /[;"\n\r]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  const rows = [['Thoi gian', 'Nguoi doc', 'Nguoi cham', 'Toc do', 'Giay/tu', 'So khoang ngat',
    'So cho ngat sai', 'Thoi diem ngat sai', 'Ghi chu', 'File', 'Diem AI']];
  state.group.reviews.forEach((r) => {
    const wrong = Array.isArray(r.wrong) ? r.wrong : [];
    rows.push([
      reviewDate(r.at), r.reader, r.evaluator, r.speed,
      r.sec_per_word !== null && r.sec_per_word !== undefined ? fmt(r.sec_per_word, 2) : '',
      r.pause_count ?? 0, wrong.length,
      wrong.map((p) => `${pauseTime(p.start)}-${pauseTime(p.end)}`).join('; '),
      r.note || '', r.fileLabel || '',
      r.ai_score !== null && r.ai_score !== undefined ? fmt(r.ai_score, 2) : '',
    ]);
  });
  const csv = '\uFEFFsep=;\r\n' + rows.map((row) => row.map(cell).join(';')).join('\r\n');
  downloadBlob(new Blob([csv], { type: 'text/csv;charset=utf-8' }), 'nhom05_phieu_cham_nhom.csv');
  toast('Đã xuất CSV phiếu chấm nhóm.');
}

/* ---------------- Ghi âm ---------------- */
async function startRecording() {
  if (state.record.busy) return;
  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    $('#recordState').textContent = 'Trình duyệt không hỗ trợ ghi âm. Hãy dùng file WAV/MP3.';
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const types = ['audio/webm;codecs=opus', 'audio/webm', 'audio/ogg;codecs=opus'];
    const type = types.find((t) => MediaRecorder.isTypeSupported(t));
    const rec = type ? new MediaRecorder(stream, { mimeType: type }) : new MediaRecorder(stream);
    state.record = { recorder: rec, stream, chunks: [], started: Date.now(), timer: null, autoStop: null, busy: false };
    rec.ondataavailable = (e) => { if (e.data?.size) state.record.chunks.push(e.data); };
    rec.onstop = () => {
      clearInterval(state.record.timer);
      clearTimeout(state.record.autoStop);
      const seconds = (Date.now() - state.record.started) / 1000;
      const blob = new Blob(state.record.chunks, { type: rec.mimeType || 'audio/webm' });
      state.record.stream?.getTracks().forEach((t) => t.stop());
      state.record.busy = false;
      $('#recordBtn').classList.remove('hidden');
      $('#stopBtn').classList.add('hidden');
      $('#recordTimer').classList.add('hidden');
      $('#recordState').textContent = `Đã ghi ${fmt(seconds, 1)} giây · sẵn sàng chấm.`;
      if (blob.size > 2000) {
        pickFile(new File([blob], `ghi-am-${Date.now()}.webm`, { type: blob.type || 'audio/webm' }));
        $('#recordState').textContent = `Đã ghi ${fmt(seconds, 1)} giây · sẵn sàng chấm.`;
      } else {
        toast('Bản ghi quá ngắn, thử lại.');
      }
    };
    rec.start(200);
    state.record.busy = true;
    $('#recordBtn').classList.add('hidden');
    $('#stopBtn').classList.remove('hidden');
    $('#recordTimer').classList.remove('hidden');
    $('#recordTimer').textContent = '00:00';
    $('#recordState').textContent = 'Đang ghi… bấm Dừng ghi khi đọc xong.';
    state.record.timer = setInterval(() => {
      const s = (Date.now() - state.record.started) / 1000;
      $('#recordTimer').textContent = clock(s);
    }, 200);
    state.record.autoStop = setTimeout(() => {
      if (state.record.recorder?.state === 'recording') {
        stopRecording();
        toast('Bản ghi tự dừng ở 30 giây.');
      }
    }, 30000);
  } catch (err) {
    $('#recordState').textContent = `Không mở được micro: ${err.message}. Thử tải file lên.`;
  }
}

function stopRecording() {
  const rec = state.record.recorder;
  if (rec && rec.state !== 'inactive') rec.stop();
}

/* ---------------- Học & vấn đáp ---------------- */
function bindLearn() {
  $('#learnNav').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-learn]');
    if (b) go('learn', b.dataset.learn);
  });

  $('#randomQuestion').addEventListener('click', () => {
    if (state.tab !== 'learn' || state.learn !== 'qa') go('learn', 'qa');
    const qs = $$('#qaList .qa');
    if (!qs.length) return;
    const pick = qs[Math.floor(Math.random() * qs.length)];
    qs.forEach((q) => { q.open = false; });
    pick.open = true;
    setTimeout(() => pick.scrollIntoView({ behavior: 'smooth', block: 'center' }), 80);
  });

  $('#compressionModelSeg').addEventListener('click', (e) => {
    const b = e.target.closest('button[data-model]');
    if (!b) return;
    state.compressionModel = b.dataset.model;
    $$('#compressionModelSeg button').forEach((x) => x.classList.toggle('active', x === b));
    if (state.charts.compression) updateCompression();
    else ensureCompressionChart();
  });

  $('#budgetRange').addEventListener('input', (e) => {
    state.learnBudget = Number(e.target.value);
    $('#budgetReadout').textContent = `${state.learnBudget}%`;
    updateRecallReadout();
    if (state.charts.recall) state.charts.recall.update('none');
  });

  $('#exportNotes').addEventListener('click', exportNotes);
  $('#clearNotes').addEventListener('click', clearNotes);
}

function bindMedian() {
  $('#medianSliders').addEventListener('input', (e) => {
    const i = Number(e.target.dataset.slider);
    if (!Number.isFinite(i)) return;
    state.medianValues[i] = Number(e.target.value);
    updateMedian();
  });
  $$('.preset-row [data-preset]').forEach((b) => {
    b.addEventListener('click', () => {
      const presets = {
        outlier: [8.3, 8.0, 10.0, 5.0, 2.27],
        agree: [8.6, 8.4, 8.5, 8.7, 8.5],
        zero: [0, 0, 0, 0, 0],
      };
      state.medianValues = (presets[b.dataset.preset] || presets.outlier).slice();
      $$('#medianSliders input').forEach((inp, i) => { inp.value = state.medianValues[i]; });
      updateMedian();
    });
  });
}

function initMedianValues() {
  const ex = state.results?.raters?.example?.five || [8.3, 8.0, 10.0, 5.0, 2.27];
  state.medianValues = ex.slice();
  const wrap = $('#medianSliders');
  wrap.innerHTML = state.medianValues.map((v, i) => `
    <div class="slider-row">
      <label for="gk${i}">GK ${i + 1}</label>
      <input id="gk${i}" type="range" min="0" max="10" step="0.1" value="${v}" data-slider="${i}" aria-label="Điểm giám khảo ${i + 1}">
      <span class="slider-val" data-val="${i}">${fmt(v, 1)}</span>
    </div>`).join('');
  updateMedian();
}

function updateMedian() {
  const vals = state.medianValues;
  const m = mean(vals);
  const med = median(vals);
  const floor = Math.floor(med);
  $$('#medianSliders [data-val]').forEach((el, i) => { el.textContent = fmt(vals[i], 1); });
  $('#meanOut').textContent = fmt(m, 2);
  $('#medianOut').textContent = fmt(med, 2);
  $('#floorOut').textContent = fmt(floor);
  const diff = Math.abs(m - med);
  $('#medianNote').innerHTML = `Chấm lớn màu cam = trung vị; chấm nhỏ xám = trung bình; chấm xanh = từng giám khảo. ${diff >= 0.4
    ? `Một hoặc vài giám khảo lệch đang kéo trung bình đi <b>${fmt(diff, 2)}</b> điểm, nhưng total vẫn là floor(trung vị) = <b>${fmt(floor)}</b>.`
    : `Năm giám khảo khá đồng thuận: trung bình và trung vị chỉ lệch <b>${fmt(diff, 2)}</b> điểm.`}`;

  const ticks = [0, 2, 4, 6, 8, 10].map((t) => `<span class="scale-tick" style="left:${t * 10}%">${t}</span>`).join('');
  const dots = vals.map((v, i) => `<span class="scale-dot" style="left:${v * 10}%" title="Giám khảo ${i + 1}: ${fmt(v, 1)}"></span>`).join('');
  $('#medianScale').innerHTML = `<div class="scale-line"></div>${ticks}${dots}
    <span class="scale-dot mean" style="left:${m * 10}%" title="Trung bình: ${fmt(m, 2)}"></span>
    <span class="scale-dot med" style="left:${med * 10}%" title="Trung vị: ${fmt(med, 2)}"></span>`;
}

function fiveDotsHtml(five, cls = 'five-dots') {
  if (!Array.isArray(five) || !five.length) return '';
  const med = median(five);
  return `<div class="${cls}">${five.map((v) => {
    const out = Math.abs(Number(v) - med) >= 3;
    return `<span class="dotscore${out ? ' out' : ''}" title="Giám khảo chấm ${fmtTrim(v)}">${fmtTrim(v)}</span>`;
  }).join('')}</div>`;
}

function renderFiveDots() {
  $$('.five-dots[data-five]').forEach((el) => {
    const vals = el.dataset.five.split(',').map(Number).filter((v) => Number.isFinite(v));
    el.outerHTML = fiveDotsHtml(vals);
  });
}

/* ---------------- Biểu đồ ---------------- */
function chartDefaults() {
  if (!window.Chart) return false;
  Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;
  Chart.defaults.font.size = 11;
  Chart.defaults.color = COLORS.muted;
  Chart.defaults.plugins.legend.labels.usePointStyle = true;
  Chart.defaults.plugins.legend.labels.boxWidth = 7;
  return true;
}

function compressionPoints(model) {
  const normal = [];
  const low = [];
  state.utts.forEach((u) => {
    const p = Number(u.pred[model]);
    if (!Number.isFinite(p)) return;
    const point = { x: p, y: Number(u.total), id: u.id, text: u.text };
    (u.below6 ? low : normal).push(point);
  });
  const mae = mean(state.utts.map((u) => Math.abs(Number(u.pred[model]) - Number(u.total))));
  return { normal, low, mae };
}

function ensureCompressionChart() {
  if (state.charts.compression) { state.charts.compression.resize(); return; }
  if (!chartDefaults()) { $('#compressionStats').textContent = 'Không tải được Chart.js.'; return; }
  const canvas = $('#compressionChart');
  if (!canvas) return;
  const { normal, low } = compressionPoints(state.compressionModel);
  state.charts.compression = new Chart(canvas.getContext('2d'), {
    type: 'scatter',
    data: {
      datasets: [
        {
          label: 'Trên 6',
          data: normal,
          pointRadius: 2.2,
          pointHoverRadius: 5,
          pointBackgroundColor: 'rgba(100,113,104,.30)',
          pointBorderColor: 'rgba(100,113,104,.22)',
        },
        {
          label: 'Dưới 6',
          data: low,
          pointRadius: 3,
          pointHoverRadius: 6,
          pointBackgroundColor: 'rgba(235,104,52,.62)',
          pointBorderColor: 'rgba(235,104,52,.30)',
        },
        {
          label: 'Dự đoán hoàn hảo',
          type: 'line',
          data: [{ x: 0, y: 0 }, { x: 10, y: 10 }],
          borderColor: COLORS.line,
          borderDash: [5, 5],
          borderWidth: 1.2,
          pointRadius: 0,
          fill: false,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      interaction: { mode: 'nearest', intersect: true },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (items) => {
              const raw = items[0]?.raw;
              return raw?.id || 'Điểm dự đoán';
            },
            label: (ctx) => {
              const p = ctx.raw;
              if (ctx.dataset.type === 'line') return 'Dự đoán = điểm thật';
              return [`Câu: ${p.text}`, `Dự đoán: ${fmt(p.x, 2)} · Điểm thật: ${fmt(p.y, 2)}`];
            },
          },
        },
      },
      scales: {
        x: {
          min: 0, max: 10,
          title: { display: true, text: 'Điểm dự đoán' },
          grid: { color: 'rgba(207,197,179,.35)' },
        },
        y: {
          min: 0, max: 10,
          title: { display: true, text: 'Điểm thật (total)' },
          grid: { color: 'rgba(207,197,179,.35)' },
        },
      },
    },
  });
  updateCompression();
}

function updateCompression() {
  const chart = state.charts.compression;
  if (!chart) return;
  const { normal, low, mae } = compressionPoints(state.compressionModel);
  chart.data.datasets[0].data = normal;
  chart.data.datasets[1].data = low;
  chart.update('none');
  const all = normal.concat(low);
  const xs = all.map((p) => p.x);
  const nLow = low.length;
  $('#compressionStats').innerHTML = `<span>Dự đoán thấp nhất <b>${fmt(Math.min(...xs), 2)}</b></span>
    <span>cao nhất <b>${fmt(Math.max(...xs), 2)}</b></span>
    <span>MAE <b>${fmt(mae, 3)}</b></span>
    <span><b>${fmt(nLow)}</b> bài dưới 6</span>`;
}

function recallPoints() {
  const budgets = [5, 10, 15, 20, 25, 30, 35, 40];
  const series = {
    wav2vec: budgets.map((b) => {
      const s = budgetStats('SVR wav2vec 2.0', b / 100);
      return s.recall * 100;
    }),
    length: budgets.map((b) => {
      const s = budgetStats('SVR chỉ độ dài', b / 100);
      return s.recall * 100;
    }),
    random: budgets.map((b) => b),
  };
  return { budgets, series };
}

function ensureRecallChart() {
  if (state.charts.recall) { state.charts.recall.resize(); return; }
  if (!chartDefaults()) return;
  const canvas = $('#recallChart');
  if (!canvas) return;
  const { budgets, series } = recallPoints();
  updateRecallReadout();
  $('#budgetRange').value = state.learnBudget;
  $('#budgetReadout').textContent = `${state.learnBudget}%`;

  const linePlugin = {
    id: 'currentBudgetLine',
    afterDatasetsDraw(chart) {
      const idx = chart.data.labels.indexOf(`${state.learnBudget}%`);
      if (idx < 0) return;
      const x = chart.scales.x.getPixelForValue(idx);
      const { top, bottom } = chart.chartArea;
      const ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = 'rgba(235,104,52,.55)';
      ctx.setLineDash([4, 4]);
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(x, top);
      ctx.lineTo(x, bottom);
      ctx.stroke();
      ctx.restore();
    },
  };

  state.charts.recall = new Chart(canvas.getContext('2d'), {
    type: 'line',
    data: {
      labels: budgets.map((b) => `${b}%`),
      datasets: [
        {
          label: 'SVR wav2vec 2.0',
          data: series.wav2vec,
          borderColor: COLORS.wav2vec,
          backgroundColor: COLORS.wav2vec,
          borderWidth: 2.4,
          pointRadius: 3,
          tension: 0.25,
        },
        {
          label: 'SVR chỉ độ dài',
          data: series.length,
          borderColor: COLORS.length,
          backgroundColor: COLORS.length,
          borderWidth: 2,
          pointRadius: 2.6,
          tension: 0.25,
        },
        {
          label: 'Ngẫu nhiên',
          data: series.random,
          borderColor: COLORS.random,
          backgroundColor: COLORS.random,
          borderWidth: 1.6,
          borderDash: [6, 5],
          pointRadius: 0,
          tension: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      plugins: {
        legend: { position: 'bottom' },
        tooltip: {
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: bắt ${fmt(ctx.parsed.y, 1)}% bài dưới 6`,
          },
        },
      },
      scales: {
        x: {
          title: { display: true, text: 'Ngân sách nghe lại (% số bài test)' },
          grid: { color: 'rgba(207,197,179,.3)' },
        },
        y: {
          min: 0, max: 100,
          title: { display: true, text: 'Recall (%)' },
          grid: { color: 'rgba(207,197,179,.35)' },
          ticks: { callback: (v) => `${v}%` },
        },
      },
    },
    plugins: [linePlugin],
  });
}

function updateRecallReadout() {
  const frac = state.learnBudget / 100;
  const w = budgetStats('SVR wav2vec 2.0', frac);
  const l = budgetStats('SVR chỉ độ dài', frac);
  const total = belowTotal();
  const missed = total - w.caught;
  $('#recallTable').innerHTML = `
    <div class="recall-cell hot"><span>wav2vec 2.0 · bắt được</span><b>${fmt(w.caught)}/${fmt(total)}</b>${pct(w.recall, 1)} recall · precision ${pct(w.precision, 0)}</div>
    <div class="recall-cell"><span>Chỉ độ dài · bắt được</span><b>${fmt(l.caught)}/${fmt(total)}</b>${pct(l.recall, 1)} recall</div>
    <div class="recall-cell"><span>Ngẫu nhiên (kỳ vọng)</span><b>${fmt(w.expected)}</b>${fmt(state.learnBudget)}% của ${fmt(total)} bài dưới 6</div>
    <div class="recall-cell"><span>Bỏ sót</span><b>${fmt(missed)}</b>bài dưới 6 nằm ngoài ${fmt(w.k)} bài ưu tiên</div>`;
}

/* ---------------- Worst5 + phiếu nghe ---------------- */
const NOTES_KEY = 'mla_worst5_notes_v2';

function initWorst5() {
  const ws = state.results.worst5 || [];
  $('#worst5Cards').innerHTML = ws.map((w, i) => `
    <article class="worst-card">
      <div class="worst-head">
        <span class="id">#${i + 1} · ${esc(w.id)}</span>
        <span class="badge high">total ${fmt(w.total, 1)}</span>
      </div>
      <div class="worst-text">${esc(w.text)}</div>
      <div class="worst-meta">
        <span>Người nói ${esc(w.speaker)} · ${fmt(w.age)} tuổi</span>
        <span>${fmt(w.duration, 2)} giây</span>
        <span>${fmt(w.words_per_s, 2)} từ/giây</span>
      </div>
      ${fiveDotsHtml(w.five, 'five-scores')}
      <div class="worst-meta">
        <span>Dự đoán wav2vec ${fmt(w.pred_w2v, 2)}</span>
        <span>log-mel ${fmt(w.pred_logmel, 2)}</span>
      </div>
      <div class="worst-actions">
        <button class="btn small ghost" data-worst-play="${esc(w.id)}">${svg('play')} Nghe câu này</button>
      </div>
    </article>`).join('');

  $('#worst5Cards').addEventListener('click', (e) => {
    const b = e.target.closest('[data-worst-play]');
    if (!b) return;
    const w = ws.find((x) => x.id === b.dataset.worstPlay);
    if (!w) return;
    openPlayer({
      id: w.id, text: w.text, speaker: w.speaker, age: w.age,
      total: w.total, five: w.five, predVal: w.pred_w2v, predName: 'SVR wav2vec 2.0',
    }, 'worst');
  });

  renderNotes(ws);
}

function loadNotes() {
  try {
    const obj = JSON.parse(localStorage.getItem(NOTES_KEY) || '{}');
    return obj && typeof obj === 'object' ? obj : {};
  } catch (_) { return {}; }
}

function renderNotes(ws) {
  const notes = loadNotes();
  $('#notesList').innerHTML = ws.map((w) => {
    const n = notes[w.id] || {};
    return `<div class="note-row" data-note-id="${esc(w.id)}">
      <div class="note-id">${esc(w.id)}<br><span class="badge high">total ${fmt(w.total, 1)}</span></div>
      <div><label class="note-label" for="n1-${esc(w.id)}">Người nghe 1</label>
        <textarea class="note-input" id="n1-${esc(w.id)}" data-slot="nghe1" placeholder="Ghi hiện tượng nghe được, không suy đoán…">${esc(n.nghe1 || '')}</textarea></div>
      <div><label class="note-label" for="n2-${esc(w.id)}">Người nghe 2</label>
        <textarea class="note-input" id="n2-${esc(w.id)}" data-slot="nghe2" placeholder="Ghi độc lập, không xem người kia trước…">${esc(n.nghe2 || '')}</textarea></div>
    </div>`;
  }).join('');

  $('#notesList').addEventListener('input', (e) => {
    if (!e.target.matches('.note-input')) return;
    const row = e.target.closest('[data-note-id]');
    const all = loadNotes();
    const id = row.dataset.noteId;
    all[id] = all[id] || {};
    all[id][e.target.dataset.slot] = e.target.value;
    try { localStorage.setItem(NOTES_KEY, JSON.stringify(all)); } catch (_) { /* chế độ riêng tư */ }
  });
}

function exportNotes() {
  if (!state.results) return;
  const notes = loadNotes();
  const payload = {
    project: 'MLA Nhóm 05 · speechocean762 · báo cáo tuần 11',
    exported_at: new Date().toISOString(),
    note: 'Ghi chú do người dùng nhập trong trình duyệt. Không có nội dung nghe nào được tạo tự động.',
    utterances: state.results.worst5.map((w) => ({
      id: w.id, text: w.text, total: w.total, five: w.five,
      pred_w2v: w.pred_w2v, pred_logmel: w.pred_logmel, duration: w.duration,
      nghe1: notes[w.id]?.nghe1 || '', nghe2: notes[w.id]?.nghe2 || '',
    })),
  };
  const has = payload.utterances.some((u) => u.nghe1 || u.nghe2);
  const date = new Date().toISOString().slice(0, 10);
  downloadBlob(new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json;charset=utf-8' }),
    `nhom05_ghi_chu_worst5_${date}.json`);
  toast(has ? 'Đã xuất phiếu nghe kèm ghi chú hiện có.' : 'Đã xuất phiếu trống — nhóm chưa điền ghi chú.');
}

function clearNotes() {
  if (!confirm('Xóa toàn bộ ghi chú đã lưu trong trình duyệt này?')) return;
  try { localStorage.removeItem(NOTES_KEY); } catch (_) { /* bỏ qua */ }
  $$('.note-input').forEach((t) => { t.value = ''; });
  toast('Đã xóa ghi chú trên trình duyệt này.');
}

/* ---------------- Máy chủ ---------------- */
async function pollStatus() {
  const dot = $('#serverDot');
  const label = $('#serverLabel');
  try {
    const s = await fetchJSON('/api/status');
    if (s.models && s.wav2vec) {
      dot.className = 'dot ok';
      label.textContent = 'Sẵn sàng · dữ liệu cục bộ';
    } else if (s.models) {
      dot.className = 'dot wait';
      label.textContent = 'Đang tải wav2vec…';
    } else {
      dot.className = 'dot wait';
      label.textContent = 'Đang nạp model…';
    }
    if (s.error) {
      dot.className = 'dot err';
      label.textContent = 'Lỗi tải wav2vec';
      label.title = s.error;
    }
  } catch (_) {
    dot.className = 'dot err';
    label.textContent = 'Máy chủ chưa chạy';
  }
}

document.addEventListener('DOMContentLoaded', init);
