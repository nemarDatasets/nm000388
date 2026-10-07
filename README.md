# Training datasets for epilepsy analysis: Freiburg-derived sliding-window features (processed-data release)

This is a **processed-data (derivative) dataset**. It redistributes, unchanged, the 20 feature tables of Zenodo record
[10.5281/zenodo.10808054](https://doi.org/10.5281/zenodo.10808054) (Riccio, Martone, Zazzaro, Pavone; version 1, 2024-03-12,
CC-BY-4.0), described in Riccio C, Martone A, Zazzaro G, Pavone L. Training Datasets for Epilepsy Analysis: Preprocessing and Feature Extraction from Electroencephalography Time Series. Data 2024, 9(5), 61. doi:10.3390/data9050061. **No raw recordings are part of this release**: the Freiburg intracranial EEG recordings
themselves are not included and are not redistributed here.

## What the tables contain
- One CSV table per patient of the Freiburg EEG database (20 patients; patient 12 is missing in the source release).
- Each row is one 2-s window of the intracranial EEG (window length L = 2 s, step S = 1 s; 256 Hz source sampling rate),
  2,291,408 rows in total.
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
  Zenodo record for all 20 files; see `sourcedata/zenodo-10808054/checksums.tsv`). Kept as CSV rather than re-expressed as TSV, so
  the bytes stay those of the authors' release.
- `sub-PatNNN/features/sub-PatNNN_desc-L2S1_features.json`: column dictionary (feature and band codes, window parameters).
- `participants.tsv`: per-patient counts computed from the tables (rows, registrations, rows per seizure phase). Age and sex
  are not reported per patient in the paper or the record, so they are `n/a`.
- `sourcedata/zenodo-10808054/`: the original `README.md` of the record, the Zenodo record metadata (`record.json`) and the
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
CC-BY-4.0 (Zenodo record). Cite Riccio C, Martone A, Zazzaro G, Pavone L. Training Datasets for Epilepsy Analysis: Preprocessing and Feature Extraction from Electroencephalography Time Series. Data 2024, 9(5), 61. doi:10.3390/data9050061 and doi:10.5281/zenodo.10808054. Contact for the source data (from the record
README): G. Zazzaro and A. Martone (CIRA).
