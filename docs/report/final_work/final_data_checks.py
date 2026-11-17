# -*- coding: utf-8 -*-
# Kiểm tra chất lượng dữ liệu bổ sung cho báo cáo cuối kỳ (rubric: distributions/missingness/duplicates).
# Nguồn: scores.json + scores-detail.json + split_manifest.csv (cùng bộ tuần 11).
# Đầu ra: final_data_checks.json + final_data_checks.log. Chạy độc lập, không đụng lần chạy 9/11.
import json, csv, datetime, collections, sys
from pathlib import Path

P = Path(__file__).parent
W = P.parent / 'week11_work'
log_lines = []
def log(s=''):
    log_lines.append(s)

S = json.loads((W / 'scores.json').read_text(encoding='utf-8'))
D = json.loads((W / 'scores-detail.json').read_text(encoding='utf-8'))
manifest = {}
with open(W / 'split_manifest.csv', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        manifest[row['utterance_id']] = row['speaker_id']

out = {'python': sys.version.split()[0], 'n_utterances': len(S), 'checked_at': datetime.datetime.now().strftime('%H:%M %d/%m/%Y')}

# 1) Missingness: các trường mức câu dùng trong báo cáo phải có và khác null
req_fields = ['accuracy', 'completeness', 'fluency', 'prosodic', 'total', 'text']
missing_by_field = collections.Counter()
missing_ids = []
for uid, rec in S.items():
    bad = [f for f in req_fields if rec.get(f) is None]
    if bad:
        missing_by_field.update(bad)
        missing_ids.append(uid)
# số lượt chấm của từng giám khảo trong scores-detail phải đủ 5
rater_counts = collections.Counter()
for uid, rec in D.items():
    for f in ['accuracy', 'completeness', 'fluency', 'prosodic', 'total']:
        v = rec.get(f)
        if not isinstance(v, list) or len(v) != 5 or any(x is None for x in v):
            rater_counts[uid] += 1
out['missingness'] = {
    'fields_checked': req_fields,
    'n_missing_sentence_fields': sum(missing_by_field.values()),
    'missing_by_field': dict(missing_by_field),
    'n_ids_missing': len(missing_ids),
    'n_ids_not_5_ratings': len(rater_counts),
}

# 2) Duplicates
ids = list(S.keys())
dup_ids = len(ids) - len(set(ids))
text_counts = collections.Counter(rec['text'] for rec in S.values())
dup_texts = {t: c for t, c in text_counts.items() if c > 1}
pair_counts = collections.Counter((manifest.get(uid), rec['text']) for uid, rec in S.items())
dup_pairs = {f'{k[0]}|{k[1]}': c for k, c in pair_counts.items() if c > 1}
out['duplicates'] = {
    'n_ids': len(ids),
    'n_distinct_ids': len(set(ids)),
    'n_distinct_texts': len(text_counts),
    'n_texts_repeated': len(dup_texts),
    'max_text_repeat': max(text_counts.values()),
    'n_speaker_text_pairs_duplicated': len(dup_pairs),
    'dup_texts_top': dict(sorted(dup_texts.items(), key=lambda kv: -kv[1])[:5]),
    'dup_pairs_top': dict(sorted(dup_pairs.items(), key=lambda kv: -kv[1])[:5]),
}

log(f"final_data_checks — {out['checked_at']}")
log(f"records: {out['n_utterances']}")
log(f"missingness: sentence fields missing = {out['missingness']['n_missing_sentence_fields']} "
    f"({out['missingness']['n_ids_missing']} ids); ids khong du 5 diem giam khao = {out['missingness']['n_ids_not_5_ratings']}")
log(f"duplicates: distinct ids = {out['duplicates']['n_distinct_ids']}/{out['duplicates']['n_ids']}; "
    f"distinct texts = {out['duplicates']['n_distinct_texts']}; texts repeated = {out['duplicates']['n_texts_repeated']} "
    f"(max repeat {out['duplicates']['max_text_repeat']}); (speaker,text) duplicated pairs = {out['duplicates']['n_speaker_text_pairs_duplicated']}")
for t, c in out['duplicates']['dup_texts_top'].items():
    log(f"  text x{c}: {t}")
for k, c in out['duplicates']['dup_pairs_top'].items():
    log(f"  pair x{c}: {k}")
log('OK')

(P / 'final_data_checks.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
(P / 'final_data_checks.log').write_text('\n'.join(log_lines) + '\n', encoding='utf-8')
print('\n'.join(log_lines))
