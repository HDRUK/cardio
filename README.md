| **Authors**  | **Project** |
|:------------:|:-----------:|
| [**N. Curti**](https://github.com/Nico-Curti) <br/> [**L. Dall'Olio**](https://github.com/Lorenzo-DallOlio) <br/> [**V. Recaldini**](https://github.com/valentinorecaldini)  |    Cardio   |

<a href="https://github.com/UniboDIFABiophysics">
<div class="image">
<img src="https://cdn.rawgit.com/physycom/templates/697b327d/logo_unibo.png" width="90" height="90">
</div>
</a>

# Cardio
### (Cardiological data processing)

The project is developed at the University of Bologna and all rights are reserved.

- [Cardio](#cardio)
    - [(Cardiological data processing)](#cardiological-data-processing)
  - [Prerequisites](#prerequisites)
  - [Description](#description)
    - [Database Generation](#database-generation)
    - [Signal Processing Modules](#signal-processing-modules)
    - [Pipelines](#pipelines)
  - [Authors](#authors)
  - [License](#license)
  - [Acknowledgments](#acknowledgments)

## Prerequisites

The project is written in python language and it uses the most common scientific packages (numpy, pandas, matplotlib, sklearn, ...), so the installation of [Anaconda](https://www.anaconda.com/) is recommended.

## Description

The project, still in progress, proposes to analyze cardiological PPG data through a machine learning approach.

### Database Generation

The analysis work-flow is centred around the pre-processing of "raw" data with some initial feature extraction (e.g. computation of RR, which is the distance between two consecutives peaks in the PPG signal). The modules for the database generation are:

- (1) [pre_process.py](https://github.com/Nico-Curti/cardio/blob/master/pre_process.py):

  The first step is the pre-processing of raw data. In this step we perform the demodulation and the smoothing of the signal, focusing only on the red channel of an RGB signal (since G and B are mostly absorbed by skin). From now on we will call as signal the variation of R channel respect time. The smoothing is made possible through the use of a central simple moving average whose window length is equal to approximately 1 second (so its length expressed in number of points is numerically equivalent to the sampling frequency of the acquired signal divided by 1Hz). This procedure acts like a high-pass filter. Then the Hilbert transform of the signal is computed. This last procedure allows to obtain the analytic signal (a complex evaluated function whose real and imaginary part are one the Hilbert tranform of the other). From the analytic signal we can extract the instantaneous amplitude (also called envelope) and the instantaneous phase. Dividing the analytic signal element-wise by its envelope we obtain the demodulated signal which is sent as output. Please note that, due to the usage of a movinga average window, the output signal will be shorter than the input signal, with difference equal to the window length.

  
  - INPUT:
  
    Raw data --> data must be stored in such a way that data.R is the sequence of R values and data.Time is the ordered sequence of acquisition time values. For obvious reasons the signal must be longer than 1 second.
  
  - OUTPUT:

    high-pass filtered and demodulated signal, shortened by approximately 1 second, splitted in its signal values (stored into the variable "sign") and its ordered time values (stored into the variable "time").

- (2) [create_db.py](https://github.com/Nico-Curti/cardio/blob/master/create_db.py): 
  
  The pre-process step is called inside the DB creation, in which we process each signal (joined with its information labels) and we extract many features in order to store them in a DB. the code implements the most common features of cardiological data, like the BPM (beats per minute), SDNN (standard deviation normal to normal), SDSD (standard deviation of successive difference), PNN20 (percentage normal to normal < 20ms), PNN50 (percentage normal to normal < 50ms) or TPR (turning point ratio) and some similar features. More complex (and dynamical) features like the mutual information and the embedding dimension (see. Takens theorem) are also computed.

  - INPUT:
  
    data directory and info directory (optionally different from data directory, but we used the same) where data and info are stored. Inside these directories filenames must be set to:
    -  yadda_number_data.txt for data
    -  yadda_number_info.txt for info

    where yadda can be any text not containing underscores ("_"), it is substatially ignored (so it can be different from data and info about the same patient), we highly recommend to use the same yadda for every data and every info; since data and info are first alphabetically sorted, writing different yadda can lead to wrong coupling of data and info. number must be a sequence of digits, the only request is to use the same number only twice, one for data and one for info, both of the same patient.

    Data needs to be a CSV and needs to contain a column called "Time" and a column called "R".
    
    Info needs to be a CSV in which the first row will be skipped (since it is the header), and the following rows have the structure

        FIELDNAME, VALUE
    
    Each FIELDNAME must be unique, and the necessary FIELDNAMEs are: Device, Sex, Age, Length, Weight, City, Country, Lifestyle, Smoking, Afib, Rhythm, Class.

    Length is supposed to be expressed in cm.

    Each text is a valid VALUE, but some [replacements](https://github.com/Nico-Curti/cardio/blob/master/create_db.py#L122) will be employed.

    Optional FIELDNAMEs can be added but will be discarded.

    For further information about the generation of the data and info files please see [here](https://github.com/Nico-Curti/cardio/blob/master/test/test_create_db.py). Please note that the *.info* file must be UTF-8 compatible. The user may want to avoid special characters (i.e. accents, diereses and the like).


  - OUTPUT:

    A .json file in the current working directory as *cardio.json*, containing a dictionary of dictionaries. The outer dictionary has the patient filename as key and, as value, an inner dictionary whose structure is shown [here](https://github.com/Nico-Curti/cardio/blob/master/cardio/create_db.py#L250).

  create_db.py can be executed from terminal with the following arguments:
  
  - -f DATA_DIR; data directory (required)
  - -i INFO_DIR; info directory (optional; default=DATA_DIR)

### Signal Processing Modules

The following modules are used for database loading/cleaning and feature extraction pipelines. Please note that they only contain functions.

  - [clean_db.py](https://github.com/Nico-Curti/cardio/blob/master/clean_db.py): 
    
    Python module before analyzing the data, the database must be cleaned; clean_db offers a way to load and clean a database by removing useless columns or patients with incomplete or incorrect data wherever specified. It contains only functions; it cannot be executed as     \_\_main\_\_.

    Please note that we consider incomplete or incorrect data those with fields of interest with NaN values or meaningless zero values. The zeros are generally considered when checking the fields Age, Weight and Length.

  - [sdppg_features.py](https://github.com/Nico-Curti/cardio/blob/master/sdppg_features.py): 
    
    Python module to allow feature extraction from SDPPG, which is the second derivative of a PPG signal with respect to time. A few examples of intersting features are the waves "a", "b", "c", "d" and "e", the AGI index and the time intervals between consecutive waves. It contains only functions; it cannot be executed as \_\_main\_\_. 

    An explanation of the *waves* within an SDPPG signal and the AGI index can be found [here](https://www.hindawi.com/journals/tswj/2013/169035/). They are supposedly features that correlate with age.

    The computation of the  *waves* is done through the analysis of the zero crossing from the FDPPG (fourth derivative of PPG signal).
    
    We assume 1D arrays for time and signal. The SDPPG and the FDPPG can be splined to increase the number of data points. However, this can slightly change the positions and the heights of the peaks.

    Please note that the signal acquired from smartphone PPG might need to be flipped.

  - [double_gaussian_features.py](https://github.com/Nico-Curti/cardio/blob/master/double_gaussian_features.py): 
    
    Python module to allow feature extraction from dicrotic notch by performing a double gaussian fit over each single beat of a PPG signal; it cannot be executed as \_\_main\_\_.

    Initially the indices of all the local minima below a certain threshold are found. If less than two minima are found a RuntimeError is raised and the function stops working. Please note that first/last point can not be considered as local minimum since it has no point before/after.
    
    If no errors are raised, then each portion of signal between two local minima is considered as a single PPG peak. The fit is performed on it by using the following fitting function:
     
        y = A1*e^[(x-m1)^2/(2*s1^2)] + A2*e^[(x-m2)^2/(2*s2^2)] 

    where:
    - Ai is the maximum of the i-th gaussian;
    - mi is the mean of the i-th gaussian;
    - si is the standard deviation of the i-th gaussian;
    - x is the time;
    - y is the peak value at time x.

    If one of the above fits raises a RuntimeError or a TypeError, the results for that peak are ignored.

    In addition to the 6 fit parameters, the beat duration (distance in time between local minima at the ends of considered peak) and the beat height (maximum vertical difference between two points of the considered peak) are computed and given as output.
    
    The output consists of a list of lists:
    - list of fitting parameters (1 list of 6 values for each evaluated peak)
    - list of beat durations (1 element for each evaluated peak)
    - list of beat heights (1 element for each evaluated peak)
  
Further information about called functions available [here](https://github.com/Nico-Curti/cardio/blob/master/doc.md).

### Pipelines 

- [feature_extraction.py](https://github.com/Nico-Curti/cardio/blob/master/pipeline/feature_extraction.py):

  Pipeline to add features to the cardiological database. It must be executed from the folder cardio/pipeline. 
  
  Its command-line arguments are:

  - -in INPUT_JSON    Input json file
  - -out OUTPUT_JSON  Output json file. Default = cadio_final.json
  
  The input *.json* file must follow the guidelines provided in [Database Generation](#database-generation). The database must have the following fields: time (array), signal (array), weight (scalar), length (scalar), age (scalar).

  The output is a *.json* file which contains the initial features and the new ones. Please note that if the keys of the new features are already used, the extracted features will overwrite the old ones.

- [data_analysis](https://github.com/Nico-Curti/cardio/blob/master/pipeline/data_analysis.py):  
  An example of script for the processing of the data to estimate the patients' age. We suggest that the user execute it cell by cell within an IDE such as Spyder.

  It can be executed from command line inside the folder pipeline. In this case it takes an optional argument:
  - -in INPUT_JSON: input json file; default=../cardio_final.json

  The database is loaded and cleaned by removing the rhythm, city, country, filename, filenumber columns (if present) and the array-like columns ('RR', 'AA', 'Rpeakvalues', 'time', 'signal'). 
  
  Rows with NaN values in the fields 'weight', 'tpr', 'madRR', 'medianRR', 'opt_delay', 'afib', 'age', 'sex','smoke', 'afib', 'bmi', 'lifestyle' are removed after checking the existence of the key. If any of the previous keys does not exist, it is skipped.

  Rows with 0s in 'age', 'weight' and 'length' are removed because they are meaningless within this dataset.

  Before any data analysis, we perform an outlier removal in a subset of meaningful features such that patients with at least a feature outside the interval \[median - 4\*mad, median + 4\*mad\] are discarded, where
    - "median" is the median value of the feature;
    - "mad" is the median absolute deviation of the feature.

  The features are standardised. We perform a PCA and extract enough components to have the 99% of explained variance. We use a ridge regression, whose target is age, and we validate the model with a 10-fold validation.

  

## Authors

* **Nico Curti** [git](https://github.com/Nico-Curti), [unibo](https://www.unibo.it/sitoweb/nico.curti2)
* **Lorenzo Dall'Olio** [git](https://github.com/Lorenzo-DallOlio)
* **Valentino Recaldini** [git](https://github.com/valentinorecaldini)

See also the list of [contributors](https://github.com/Nico-Curti/cardio/contributors) [![GitHub contributors](https://img.shields.io/github/contributors/Naereen/StrapDown.js.svg)](https://GitHub.com/Nico-Curti/cardio/graphs/contributors/) who participated in this project.

## License

NO LICENSEs are available. All rights are reserved.

## Acknowledgments

Thanks goes to all contributors of this project:

[<img src="https://avatars0.githubusercontent.com/u/1419337?s=400&v=4" width="100px;"/><br /><sub><b>Enrico Giampieri</b></sub>](https://github.com/EnricoGiampieri) <br />
