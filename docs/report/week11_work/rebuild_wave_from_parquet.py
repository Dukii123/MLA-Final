# Dung lai bo WAVE 5.000 file .wav cho dataset week09_work\data\speechocean762
# boi vi thu muc WAVE da bi xoa khoi may (ngay 9/11/2026). Nguon bytes: 2 parquet HF
# (train/test, moi hang co audio.path = '000010011.wav' + audio.bytes) tai thu muc parquet.
# Cau truc xuat dung nhu dataset goc tren GitHub: WAVE/SPEAKERxxxx/<uid>.WAV, trong do
# SPEAKERxxxx = 'SPEAKER' + speaker_id 4 chu so LAY TRUC TIEP TU split_manifest.csv
# (kiem tra mau: 000010011 -> 0001 = SPEAKER0001 theo link GitHub chu the).
# Chay: python rebuild_wave_from_parquet.py <thu_muc_parquet>
from pathlib import Path
import csv, sys, time
import pyarrow.parquet as pq

P = Path(__file__).parent
PARQ = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r'C:\Users\DucAnh\AppData\Local\Temp\opencode\sp762')
WAVE = P.parent / 'week09_work' / 'data' / 'speechocean762' / 'WAVE'
t0 = time.perf_counter()

# map uid -> speaker_id (4 chu so) tu manifest cua du an — an toan hon doan tu uid
man = {r['utterance_id']: r['speaker_id'] for r in csv.DictReader((P.parent / 'week10_work' / 'split_manifest.csv').open(encoding='utf-8'))}
assert len(man) == 5000, len(man)

n = 0
for part in ['train-00000-of-00001.parquet', 'test-00000-of-00001.parquet']:
    pf = pq.ParquetFile(PARQ / part)
    for b in pf.iter_batches(batch_size=128, columns=['audio']):
        for r in b.to_pylist():
            a = r['audio']
            uid = Path(a['path']).stem
            assert uid in man, f'{uid} khong co trong split_manifest.csv'
            spk = man[uid]
            out = WAVE / f'SPEAKER{spk}' / f'{uid}.WAV'
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(a['bytes'])
            n += 1

# Kiem chung sau khi xong: dung 5.000 file, khong thua, khong thieu, du 5 worst5
files = list(WAVE.glob('SPEAKER*/*.WAV'))
assert len(files) == 5000, len(files)
assert set(f.stem for f in files) == set(man), 'bo WAVE khac split_manifest.csv'
for uid in ['014040089', '069020059', '014040122', '014040090', '069020075']:
    assert (WAVE / f'SPEAKER{man[uid]}' / f'{uid}.WAV').exists(), uid

print(f'REBUILD WAVE OK: {n} hang parquet -> 5000 file, {time.perf_counter() - t0:.0f} s, tai {WAVE}')
