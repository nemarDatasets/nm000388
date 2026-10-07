## EEG Training Datasets for Seizure Analysis
 
This dataset comprises 20 CSV files, each corresponding to a distinct patient of the Freiburg Seizure Prediction Database analyzed using the Training Builder tool (the data of patient number 12 are missing). 
The file names are uniquely identified by the patient number, such that `Pat001.csv` corresponds to the training data of patient number 001.
 
Each CSV file contains 1083 columns (3 metadata + 1080 features):

### Metadata 
- **Registration**: Denotes the registration number from the Freiburg EEG database, specifying the source from which the training data are extracted.
- **Actual Timestamp**: Represents the time interval indicating the initial and final sample for feature extraction. The interval is related to the length of the selected window (L parameter). For instance, the notation `1_512` signifies the utilization of a 2-second window due to its 512 samples (i.e., 2 × 256 at a sample frequency of 256 Hz).
- **Actual TAG**: Indicates the class value identified within the specified timestamp interval, with possible values from the set {PRE, IKTAL, POST, INTER}, summarizing the portion of the signal.
 
### Features
Each feature column name is denoted by the format **EiBjFCMk**, where:
 
- **Ei**: Represents the i-th electrode number (i=1,2,...,6).
- **Bj**: Denotes the j-th band number, corresponding to specific frequency bands: α (8–13 Hz), β1 (13–21 Hz), β2 (21-30 Hz), low γ (30–40 Hz), medium γ (40-70 Hz), and high γ (70-120 Hz).
- **FC**: Refers to the feature extraction code.
- **Mk**: Represents the calculation method for the feature. For univariate features, the value is always MU. In contrast, for bivariate features, the value can be MA if the reference signal is sourced from the preceding L window, or MB if the reference signal is the zero constant signal.
 
### Notes
The provided 20 patient files are calculated with window parameters L = 2 and sliding S = 1.
Other sets of data related to L = 2 and S = 2 can be obtained by excluding odd rows from the training dataset.

For further details on feature extraction codes and calculation methods, refer to Table 4 in the related paper.

We would like to highlight the adaptability of our proposed methodology, which allows for the extraction of more detailed data by adjusting the parameters, like the windowing temporal parameters L and S. 
Should users need more specialized data, we are open to providing it upon request.

For any inquiries or issues regarding the dataset, please contact [g.zazzaro@cira.it](mailto:g.zazzaro@cira.it) and/or [a.martone@cira.it](mailto:a.martone@cira.it)
