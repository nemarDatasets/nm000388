#!/usr/bin/env python3
"""FINISHER 014/043 (2026-10-07): build the IEEG014 derivative tree (Riccio et al. 2024 Freiburg-derived feature tables).
- CSV bytes kept unchanged (copied, md5 re-checked against the Zenodo record) into sub-PatNNN/features/.
- JSON sidecar per table; participants.tsv/json (per-file statistics computed here, demographics n/a: not in the paper);
  sourcedata/zenodo-10808054/ = original README.md + record.json + checksums + mapping; code/ = this script.
- Privacy scan: every row's first three fields and every value character class.
Usage: fin1443_build014.py  (env NPROC)"""
import os, sys, json, hashlib, shutil, re, collections, datetime
from concurrent.futures import ProcessPoolExecutor
ROOT = '/voyager/ceph/groups/sdp190/bpinto/ieeg-nemar-20261005'
SRC = f'{ROOT}/work/IEEG014/sourcedata'
FIN = f'{ROOT}/work/IEEG014/finisher'
T = f'{ROOT}/work/IEEG014/bids'
REC = '10808054'
TAGS = ['PRE', 'PRE_IKTAL', 'IKTAL', 'IKTAL_POST', 'POST', 'INTER']
ALLOWED = set(b'0123456789.eE+-,NaInfinf\r\n')

def md5sha(fn):
    m, s = hashlib.md5(), hashlib.sha256()
    with open(fn, 'rb') as f:
        for b in iter(lambda: f.read(1 << 24), b''): m.update(b); s.update(b)
    return m.hexdigest(), s.hexdigest()

def scan(key):
    """copy + hash + per-row checks for one PatNNN.csv"""
    pat = key[:-4]; sub = f'sub-{pat}'
    dst_dir = f'{T}/{sub}/features'; os.makedirs(dst_dir, exist_ok=True)
    dst = f'{dst_dir}/{sub}_desc-L2S1_features.csv'
    if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(f'{SRC}/{key}')):
        shutil.copyfile(f'{SRC}/{key}', dst + '.tmp'); os.replace(dst + '.tmp', dst)
    md5, sha = md5sha(dst)
    regs, tags = collections.Counter(), collections.Counter()
    bad_ts = bad_tag = bad_chars = bad_ncol = 0; rows = 0; first_ts = last_ts = None; samples_bad = []
    with open(dst, 'rb') as f:
        header = f.readline().rstrip(b'\r\n').decode()
        ncol = header.count(',') + 1
        for line in f:
            rows += 1
            parts = line.split(b',', 3)
            if len(parts) < 4: bad_ncol += 1; continue
            reg, ts, tag, rest = parts
            regs[reg.decode('latin1')] += 1
            t = tag.decode('latin1'); tags[t] += 1
            if t not in TAGS: bad_tag += 1
            tsd = ts.decode('latin1')
            if not re.fullmatch(r'\d+_\d+', tsd): bad_ts += 1
            if first_ts is None: first_ts = tsd
            last_ts = tsd
            if rest.count(b',') != ncol - 4: bad_ncol += 1
            if rest.translate(None, bytes(ALLOWED)):
                bad_chars += 1
                if len(samples_bad) < 3: samples_bad.append(rest.translate(None, bytes(ALLOWED))[:40].decode('latin1'))
    return dict(key=key, sub=sub, dst=os.path.relpath(dst, T), md5=md5, sha256=sha, bytes=os.path.getsize(dst), header=header,
                ncol=ncol, rows=rows, registrations=dict(regs), tags=dict(tags), bad_ts=bad_ts, bad_tag=bad_tag,
                bad_chars=bad_chars, bad_chars_samples=samples_bad, bad_ncol=bad_ncol, first_ts=first_ts, last_ts=last_ts)

def wj(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f: json.dump(o, f, indent=2, ensure_ascii=False); f.write('\n')

def main():
    rec = json.load(open(f'{FIN}/record.json'))
    zmd5 = {f['key']: f['checksum'].split(':', 1)[1] for f in rec['files']}
    zsize = {f['key']: f['size'] for f in rec['files']}
    keys = sorted(k for k in zmd5 if k.endswith('.csv'))
    assert len(keys) == 20, keys
    os.makedirs(T, exist_ok=True)
    with ProcessPoolExecutor(int(os.environ.get('NPROC', '20'))) as ex:
        res = list(ex.map(scan, keys))
    # round-trip (byte identity) against the Zenodo record
    for r in res:
        r['zenodo_md5'] = zmd5[r['key']]; r['md5_match'] = (r['md5'] == zmd5[r['key']] and r['bytes'] == zsize[r['key']])
    headers = {r['header'] for r in res}
    hdr = res[0]['header'].split(',')
    feats = hdr[3:]
    pat = re.compile(r'E(\d)B(\d+)([A-Z]{2})M([UAB])')
    parsed = [pat.fullmatch(c) for c in feats]
    electrodes = sorted({int(m.group(1)) for m in parsed if m}); bands = sorted({int(m.group(2)) for m in parsed if m})
    codes = sorted({m.group(3) for m in parsed if m}); methods = sorted({m.group(4) for m in parsed if m})
    summary = dict(n_files=len(res), all_md5_match=all(r['md5_match'] for r in res), identical_headers=len(headers) == 1,
                   n_feature_columns=len(feats), unparsed_feature_columns=[c for c, m in zip(feats, parsed) if not m],
                   electrodes=electrodes, band_codes=bands, feature_codes=codes, methods=methods,
                   total_rows=sum(r['rows'] for r in res),
                   privacy=dict(bad_ts=sum(r['bad_ts'] for r in res), bad_tag=sum(r['bad_tag'] for r in res),
                                bad_chars=sum(r['bad_chars'] for r in res), bad_ncol=sum(r['bad_ncol'] for r in res),
                                registration_values=sorted({k for r in res for k in r['registrations']})))
    wj(f'{FIN}/build_summary.json', dict(summary=summary, files=res))
    print(json.dumps(summary, indent=1)[:4000])
    # ---------- text files ----------
    paper = 'Riccio C, Martone A, Zazzaro G, Pavone L. Training Datasets for Epilepsy Analysis: Preprocessing and Feature Extraction from Electroencephalography Time Series. Data 2024, 9(5), 61. doi:10.3390/data9050061'
    ethics = ('The training datasets derive from the EEG Database provided by Epilepsy Center Freiburg as well as the Freiburg Center '
              'for Data Analysis and Modelling. Authors obtained prior written consent from the Epilepsy Center Freiburg to publish these '
              'data or to use them for publication (agreement was signed by one of the authors, L.P., on 16 March 2012). '
              '(Riccio et al. 2024, Data 9(5):61, "Institutional Review Board Statement"; "Informed Consent Statement: Not applicable.")')
    band_desc = {8: 'alpha (8-13 Hz)', 13: 'beta1 (13-21 Hz)', 21: 'beta2 (21-30 Hz)', 30: 'low gamma (30-40 Hz)',
                 40: 'medium gamma (40-70 Hz)', 70: 'high gamma (70-120 Hz)'}
    table4 = [('SD', 'Standard Deviation', 'U'), ('KU', 'Kurtosis', 'U'), ('HM', 'Hjorth Mobility', 'U'), ('SH', 'Shannon Entropy', 'U'),
              ('LE', 'Log-Energy Entropy', 'U'), ('KC', 'Kolmogorov Complexity', 'U'), ('LU', 'Upper Limit Lempel–Ziv Complexity', 'U'),
              ('LL', 'Lower Limit Lempel–Ziv Complexity', 'U'), ('PD', 'Peak Displacement', 'U'), ('PP', 'Predominant Period', 'U'),
              ('AP', 'Averaged Period', 'U'), ('SG', 'Squared Grade', 'U'), ('SP', 'Squared Time to Peak', 'U'), ('IP', 'Inverted Time to Peak', 'U'),
              ('CE', 'Conditional Entropy', 'B'), ('JE', 'Joint Entropy', 'B'), ('MI', 'Mutual Information', 'B'), ('CC', 'Cross Correlation Index', 'B'),
              ('ED', 'Euclidean Distance', 'B'), ('LD', 'Levenshtein Distance', 'B'), ('DT', 'Dynamic Time Warping', 'B'), ('LC', 'Longest Common Sub-Sequence', 'B')]
    dd = {
        'Name': 'Training datasets for epilepsy analysis: sliding-window features derived from the Freiburg intracranial EEG database (Riccio et al. 2024), processed-data release',
        'BIDSVersion': '1.10.0', 'DatasetType': 'derivative', 'License': 'CC-BY-4.0',
        'Authors': ['Christian Riccio', 'Angelo Martone', 'Gaetano Zazzaro', 'Luigi Pavone'],
        'GeneratedBy': [
            {'Name': 'Training Builder (TrB)', 'Description': 'Authors\' feature-extraction software (Riccio et al. 2024, Section 3): band-pass filtering of 6 intracranial EEG electrodes (3 in focus, 3 out of focus) of each Freiburg patient into 6 bands (alpha 8-13, beta1 13-21, beta2 21-30, low gamma 30-40, medium gamma 40-70, high gamma 70-120 Hz), sliding window L = 2 s, step S = 1 s, 14 univariate and 8 bivariate features per electrode and band (bivariate against the previous window, MA, or against the zero signal, MB) = 1080 features per window; each window labelled PRE/IKTAL/POST/INTER.'},
            {'Name': 'ieeg-nemar repackaging', 'Version': '2026-10-07', 'Description': 'CSV files copied byte-for-byte from Zenodo record 10808054 (md5 verified) into per-patient folders, with JSON sidecars, participants.tsv and README; no value changed. Script in code/.'}],
        'SourceDatasets': [{'DOI': 'doi:10.5281/zenodo.10808054', 'Version': '1'},
                           {'URL': 'http://epilepsy.uni-freiburg.de/freiburg-seizure-prediction-project/eeg-database'}],
        'HowToAcknowledge': 'Please cite ' + paper + ', and the Zenodo record doi:10.5281/zenodo.10808054.',
        'ReferencesAndLinks': ['https://doi.org/10.3390/data9050061', 'https://doi.org/10.5281/zenodo.10808054',
                               'https://doi.org/10.3390/biomedicines10071491', 'https://doi.org/10.1016/j.iot.2019.03.002',
                               'https://doi.org/10.1109/HPCC-SmartCity-DSS50907.2020.00175', 'https://doi.org/10.5281/zenodo.3455611'],
        'DatasetDOI': 'doi:10.5281/zenodo.10808054',
        'Keywords': ['epilepsy', 'intracranial EEG', 'seizure detection', 'feature extraction', 'sliding window', 'Freiburg EEG database', 'derivative', 'machine learning'],
        'Funding': ['This research received no external funding.'],
        'EthicsApprovals': [ethics],
    }
    wj(f'{T}/dataset_description.json', dd)
    # participants
    rows = ['participant_id\tfreiburg_patient\tsource_file\tn_windows\tn_registrations\tn_PRE\tn_PRE_IKTAL\tn_IKTAL\tn_IKTAL_POST\tn_POST\tn_INTER\tage\tsex']
    for r in res:
        t = r['tags']
        rows.append('\t'.join([r['sub'], r['key'][3:6], r['key'], str(r['rows']), str(len(r['registrations']))] +
                              [str(t.get(k, 0)) for k in TAGS] + ['n/a', 'n/a']))
    open(f'{T}/participants.tsv', 'w').write('\n'.join(rows) + '\n')
    wj(f'{T}/participants.json', {
        'participant_id': {'Description': 'sub-PatNNN, NNN = patient number of the Freiburg EEG database as used in the source file name PatNNN.csv (patient 12 is not in the release).'},
        'freiburg_patient': {'Description': 'Freiburg EEG database patient number (from the file name).'},
        'source_file': {'Description': 'File name in Zenodo record 10808054.'},
        'n_windows': {'Description': 'Number of data rows (2-s windows, 1-s step) in the feature table; computed by the repackaging script.'},
        'n_registrations': {'Description': 'Number of distinct values of the Registration column (Freiburg recordings the windows come from); computed.'},
        'n_PRE': {'Description': 'Rows with Actual TAG = PRE (pre-ictal); computed.'},
        'n_PRE_IKTAL': {'Description': 'Rows with Actual TAG = PRE_IKTAL (window spanning the pre-ictal/ictal boundary; label present in the files, not described in the paper); computed.'},
        'n_IKTAL': {'Description': 'Rows with Actual TAG = IKTAL (ictal); computed.'},
        'n_IKTAL_POST': {'Description': 'Rows with Actual TAG = IKTAL_POST (window spanning the ictal/post-ictal boundary; label present in the files, not described in the paper); computed.'},
        'n_POST': {'Description': 'Rows with Actual TAG = POST (post-ictal); computed.'},
        'n_INTER': {'Description': 'Rows with Actual TAG = INTER (inter-ictal); computed.'},
        'age': {'Description': 'Not reported per patient in Riccio et al. 2024 or the Zenodo record: n/a.'},
        'sex': {'Description': 'Not reported per patient in Riccio et al. 2024 or the Zenodo record: n/a.'}})
    side = {
        'Description': 'Sliding-window feature table of one Freiburg patient (Riccio et al. 2024). Comma-separated values, header row, bytes identical to the file of the same patient in Zenodo record 10808054.',
        'Delimiter': ',', 'SourceSamplingFrequency': 256, 'WindowLength': 2, 'WindowLengthUnits': 's', 'WindowStep': 1, 'WindowStepUnits': 's',
        'Columns': {
            'Registration': 'Registration (recording) number of the Freiburg EEG database the window was extracted from.',
            'Actual Timestamp': 'Initial and final sample of the window, "first_last" (e.g. 1_512 = 2 s at 256 Hz).',
            'Actual TAG': 'Seizure phase of the window: PRE (pre-ictal), IKTAL (ictal), POST (post-ictal), INTER (inter-ictal); the files also contain PRE_IKTAL and IKTAL_POST for the few windows that span a phase boundary (not described in the paper).',
            'E<i>B<j><FC>M<k>': '1080 feature columns. i = electrode 1-6 (1-3 in the epileptic focus, 4-6 outside the focus); j = lower edge of the band (8, 13, 21, 30, 40, 70 Hz); FC = feature code (FeatureCodes); k = method: U = univariate, A = bivariate against the previous window, B = bivariate against the zero signal.'},
        'BandCodes': {f'B{b}': band_desc[b] for b in bands if b in band_desc},
        'FeatureCodes': {c: {'Name': n, 'Type': 'univariate' if u == 'U' else 'bivariate'} for c, n, u in table4},
        'Sources': ['bids::sourcedata/zenodo-10808054/README.md'],
        'Reference': 'Riccio et al. 2024, Data 9(5):61, Section 2 and Table 4; Zenodo record README.md.'}
    for r in res:
        s = dict(side); s['RowCount'] = r['rows']; s['ZenodoFile'] = r['key']; s['ZenodoMD5'] = r['zenodo_md5']
        wj(f'{T}/{r["sub"]}/features/{r["sub"]}_desc-L2S1_features.json', s)
    open(f'{T}/.bidsignore', 'w').write('sub-*/features/\n')
    # sourcedata
    sd = f'{T}/sourcedata/zenodo-{REC}'; os.makedirs(sd, exist_ok=True)
    shutil.copyfile(f'{SRC}/README.md', f'{sd}/README.md')
    shutil.copyfile(f'{FIN}/record.json', f'{sd}/record.json')
    with open(f'{sd}/checksums.tsv', 'w') as f:
        f.write('zenodo_key\tbytes\tmd5_zenodo\tmd5_local\tsha256_local\tlocation_in_this_dataset\n')
        rm5, rsha = md5sha(f'{sd}/README.md')
        f.write(f'README.md\t{zsize["README.md"]}\t{zmd5["README.md"]}\t{rm5}\t{rsha}\tsourcedata/zenodo-{REC}/README.md\n')
        for r in res:
            f.write(f'{r["key"]}\t{r["bytes"]}\t{r["zenodo_md5"]}\t{r["md5"]}\t{r["sha256"]}\t{r["dst"]}\n')
    os.makedirs(f'{T}/code', exist_ok=True); shutil.copyfile(__file__, f'{T}/code/fin1443_build014.py')
    nwin = summary['total_rows']
    readme = f"""# Training datasets for epilepsy analysis: Freiburg-derived sliding-window features (processed-data release)

This is a **processed-data (derivative) dataset**. It redistributes, unchanged, the 20 feature tables of Zenodo record
[10.5281/zenodo.10808054](https://doi.org/10.5281/zenodo.10808054) (Riccio, Martone, Zazzaro, Pavone; version 1, 2024-03-12,
CC-BY-4.0), described in {paper}. **No raw recordings are part of this release**: the Freiburg intracranial EEG recordings
themselves are not included and are not redistributed here.

## What the tables contain
- One CSV table per patient of the Freiburg EEG database (20 patients; patient 12 is missing in the source release).
- Each row is one 2-s window of the intracranial EEG (window length L = 2 s, step S = 1 s; 256 Hz source sampling rate),
  {nwin:,} rows in total.
- 1083 columns: 3 metadata columns (`Registration`, `Actual Timestamp`, `Actual TAG`) and 1080 features named `EiBjFCMk`:
  - electrode i = 1-6 (electrodes 1-3 in the epileptic focus, 4-6 outside it);
  - band j given by its lower edge: B8 alpha 8-13 Hz, B13 beta1 13-21 Hz, B21 beta2 21-30 Hz, B30 low gamma 30-40 Hz,
    B40 medium gamma 40-70 Hz, B70 high gamma 70-120 Hz;
  - feature code FC from Table 4 of the paper (14 univariate: SD, KU, HM, SH, LE, KC, LU, LL, PD, PP, AP, SG, SP, IP;
    8 bivariate: CE, JE, MI, CC, ED, LD, DT, LC);
  - method Mk: MU univariate; MA bivariate against the previous window; MB bivariate against the zero signal.
- `Actual TAG` gives the seizure phase of the window: PRE (pre-ictal), IKTAL (ictal), POST (post-ictal), INTER (inter-ictal).
  The files also contain two labels the paper does not describe, PRE_IKTAL and IKTAL_POST, on a few windows per patient
  that span a phase boundary (counts in `participants.tsv`).
- The authors note that the L = 2 s, S = 2 s variant is obtained by dropping the odd rows.

## How the features were produced (from the paper)
The authors' Training Builder (TrB) tool filtered the signals of six electrodes per patient into the six bands and
computed the features of Table 4 in sliding windows (Riccio et al. 2024, Sections 2-3). Formulas: see the paper's
references [5,8].

## Layout
- `sub-PatNNN/features/sub-PatNNN_desc-L2S1_features.csv`: the source file `PatNNN.csv`, **byte-identical** (md5 equal to the
  Zenodo record for all 20 files; see `sourcedata/zenodo-{REC}/checksums.tsv`). Kept as CSV rather than re-expressed as TSV, so
  the bytes stay those of the authors' release.
- `sub-PatNNN/features/sub-PatNNN_desc-L2S1_features.json`: column dictionary (feature and band codes, window parameters).
- `participants.tsv`: per-patient counts computed from the tables (rows, registrations, rows per seizure phase). Age and sex
  are not reported per patient in the paper or the record, so they are `n/a`.
- `sourcedata/zenodo-{REC}/`: the original `README.md` of the record, the Zenodo record metadata (`record.json`) and the
  checksum/location table of all 21 record files.
- `code/fin1443_build014.py`: the repackaging script.
- `.bidsignore` lists `sub-*/features/` because feature tables are not a BIDS datatype.

## How to load
```python
import pandas as pd
df = pd.read_csv("sub-Pat001/features/sub-Pat001_desc-L2S1_features.csv")
X = df.iloc[:, 3:].to_numpy()      # 1080 features
y = df["Actual TAG"].to_numpy()     # PRE / IKTAL / POST / INTER
```

## Ethics approval
Verbatim from Riccio et al. 2024, Data 9(5):61, "Institutional Review Board Statement":
> The training datasets derive from the EEG Database provided by Epilepsy Center Freiburg as well as the Freiburg Center for Data
> Analysis and Modelling. Authors obtained prior written consent from the Epilepsy Center Freiburg to publish these data or to use
> them for publication (agreement was signed by one of the authors, L.P., on 16 March 2012).

"Informed Consent Statement: Not applicable." (same article).

## Funding
"This research received no external funding." (Riccio et al. 2024, Funding). Acknowledgments of the article mention the Big
Data Facility project, funded by the Italian PRORA.

## Privacy
The tables hold window positions (sample indices), Freiburg registration numbers, phase labels and numeric features only.
The repackaging script checked every row: timestamps match `first_last`, tags are in the six-value set above, and all feature
values are numeric. No names, dates or hospital identifiers.

## License and citation
CC-BY-4.0 (Zenodo record). Cite {paper} and doi:10.5281/zenodo.10808054. Contact for the source data (from the record
README): G. Zazzaro and A. Martone (CIRA).
"""
    open(f'{T}/README.md', 'w').write(readme)
    open(f'{T}/CHANGES', 'w').write('1.0.0 2026-10-07\n  - Processed-data release of Zenodo record 10808054 v1 (feature tables unchanged), with sidecars, participants and README.\n')
    ok = summary['all_md5_match'] and summary['identical_headers'] and not any(summary['privacy'][k] for k in ('bad_ts', 'bad_tag', 'bad_chars', 'bad_ncol'))
    print('BUILD_OK' if ok else 'BUILD_CHECKS_FAILED')
    sys.exit(0 if ok else 5)

if __name__ == '__main__':
    main()
