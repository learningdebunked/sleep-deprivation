# The Sleep-EDF Database \[Expanded\]

**The new PhysioNet website is available at [https://physionet.org](https://physionet.org/).**

This database is described in

B Kemp, AH Zwinderman, B Tuk, HAC Kamphuisen, JJL Oberyé.
[Analysis of a\\
sleep-dependent neuronal feedback loop: the slow-wave microcontinuity\\
of the EEG](https://archive.physionet.org/physiobank/database/sleep-edfx/Papers/2000-Kemp---neurofeedback.pdf).
_IEEE-BME_ **47**(9):1185-1194 (2000).

**Please cite this publication when referencing this material, and also**
**include the standard citation for PhysioNet:**

Goldberger AL, Amaral LAN, Glass L, Hausdorff JM, Ivanov PCh, Mark RG,
Mietus JE, Moody GB, Peng C-K, Stanley HE. PhysioBank, PhysioToolkit, and
PhysioNet: Components of a New Research Resource for Complex Physiologic
Signals.
_Circulation_ **101**(23):e215-e220 \[Circulation Electronic Pages;\
[http://circ.ahajournals.org/cgi/content/full/101/23/e215](http://circ.ahajournals.org/cgi/content/full/101/23/e215)\];
2000 (June 13).

## Introduction

The sleep-edf database contains 197 whole-night PolySomnoGraphic sleep recordings, containing EEG, EOG, chin EMG, and event markers. Some records also contain respiration and body temperature. Corresponding hypnograms (sleep patterns) were manually scored by well-trained technicians according to the Rechtschaffen and Kales manual, and are also available. The data comes from two studies, briefly described below, and in detail in [\[1,2\]](https://archive.physionet.org/physiobank/database/sleep-edfx/#ref1).

## Data and Annotation Files

The **\*PSG.edf** files are whole-night polysmnographic sleep recordings
containing EEG (from Fpz-Cz and Pz-Oz electrode locations), EOG (horizontal),
submental chin EMG, and an event marker. The **SC\*PSG.edf** files (see the 'sleep cassette study') often also
contain oro-nasal respiration and rectal body temperature.

The **\*Hypnogram.edf** files contain annotations of the sleep patterns that
correspond to the PSGs. These patterns (hypnograms) consist of sleep stages W,
R, 1, 2, 3, 4, M (Movement time) and ? (not scored). All hypnograms were
manually scored by well-trained technicians (identified by the eighth letter of
the hypnogram filename) according to the 1968 Rechtschaffen and Kales
manual [\[3\]](https://archive.physionet.org/physiobank/database/sleep-edfx/#ref3), but based on Fpz-Cz/Pz-Oz EEGs instead of
C4-A1/C3-A2 EEGs, as suggested by [\[4\]](https://archive.physionet.org/physiobank/database/sleep-edfx/#ref4)).

All EDF header fields also comply with the EDF+ specs, and unrecorded signals were
removed from the `ST*PSG.edf` files.

The PSG files are formatted in EDF while the hypnograms are in EDF+. The
specifications of EDF and EDF+ are on [www.edfplus.info](http://www.edfplus.info/) and in [\[5,6\]](https://archive.physionet.org/physiobank/database/sleep-edfx/#ref5). Each EDF
and EDF+ file has a header specifying the patient (in these files anonymized to
only gender and age), details of the recording (in particular the recorded time
period), and characteristics of the signals including their amplitude
calibration.

## Sleep Cassette Study and Data

The 153 **SC\*** files (SC = Sleep Cassette) were obtained in a 1987-1991 study of age effects on sleep in healthy Caucasians aged 25-101, without any sleep-related medication \[2\]. Two PSGs of about 20 hours each were recorded during two subsequent day-night periods at the subjects homes. Subjects continued their normal activities but wore a modified Walkman-like cassette-tape recorder described in chapter VI.4 (page 92) of Bob’s 1987 thesis \[7\].

Files are named in the form `SC4ssNEO-PSG.edf` where **ss** is the subject number, and **N** is the night. The first nights of subjects 36 and 52, and the second night of subject 13, were lost due to a failing cassette or laserdisk.

The EOG and EEG signals were each sampled at 100 Hz. The submental-EMG signal was electronically highpass filtered, rectified and low-pass filtered after which the resulting EMG envelope expressed in uV rms (root-mean-square) was sampled at 1Hz. Oro-nasal airflow, rectal body temperature and the event marker were also sampled at 1Hz.

Subjects and recordings are further described in the file headers, the descriptive spreadsheet **SC-subjects.xls**, and in \[2\].

## Sleep Telemetry Study and Data

The 44 **ST\*** files (ST = Sleep Telemetry) were obtained in a 1994 study of temazepam effects on sleep in 22 Caucasian males and females without other medication. Subjects had mild difficulty falling asleep but were otherwise healthy. The PSGs of about 9 hours were recorded in the hospital during two nights, one of which was after temazepam intake, and the other of which was after placebo intake. Subjects wore a miniature telemetry system with very good signal quality described in \[8\].

Files are named in the form `ST7ssNJ0-PSG.edf` where **ss** is the subject number, and **N** is the night.

EOG, EMG and EEG signals were sampled at 100 Hz, and the event marker at 1 Hz. The physical marker dimension ID+M-E relates to the fact that pressing the marker (M) button generated two-second deflections from a baseline value that either identifies the telemetry unit (ID = 1 or 2 if positive) or marks an error (E) in the telemetry link if negative. Subjects and recordings are further described in the file headers, the descriptive spreadsheet **ST-subjects.xls**, and in \[1\].

## Software for viewing EDF and EDF+ files

Both EDF and EDF+ formats are free and can be viewed using free software
such as:

- [Polyman](https://archive.physionet.org/physiobank/database/sleep-edfx/Polyman/) (for MS-Windows only; for details,
   please follow the link)
- [EDFbrowser](http://www.teuniz.net/edfbrowser/)
   (for Linux, Mac OS X, and MS-Windows; at
   [www.teuniz.net](http://www.teuniz.net/))
- [LightWAVE](https://archive.physionet.org/lightwave/) and the [PhysioBank\\
   ATM](https://archive.physionet.org/ATM), platform-independent web applications from PhysioNet
- [WAVE](https://archive.physionet.org/physiotools/wug/) and other applications for Linux, Mac
   OS X, and MS-Windows in the [WFDB Software\\
   Package](https://archive.physionet.org/physiotools/wfdb.shtml), also from PhysioNet

An easy way to view these recordings using Polyman is to
select _File → Open → File(s)..._ to open
a `PSG.edf` file and its corresponding `.Hypnogram.edf`
file; then select
_File → Apply Template → Browse..._ to open
[`SC-cassette.xml`](https://archive.physionet.org/physiobank/database/sleep-edfx/Polyman/SC-cassette.xml) (for an SC PSG)
or [`ST-telemetry.xml`](https://archive.physionet.org/physiobank/database/sleep-edfx/Polyman/ST-telemetry.xml) (for an ST
PSG).

Applications using [WFDB library](https://archive.physionet.org/physiotools/wfdb.shtml#library)
version 10.4.5 (February 2008) or later can read EDF files directly with no
conversion required. Note that the WFDB library does not decode annotations in
EDF+ files, however.

## Version History

- Version 0: A small subset of this dataset was previously contributed in 2002 and remains available
   [here](https://archive.physionet.org/physiobank/database/sleep-edf/) for reference and to support ongoing studies.
- Version 1: In 2013, the database was greatly expanded to contain 61 PSGs with accompanying hypnograms.
- Version 2: In March 2018, the database was greatly expanded to contain 197 PSGs with accompanying hypnograms

## Database Creator and Contact

Bob Kemp, The Netherlands bk at hsr dot nl

## References

1. B Kemp, AH Zwinderman, B Tuk, HAC Kamphuisen, JJL Oberyé.
[Analysis of a sleep-dependent\\
neuronal feedback loop: the slow-wave microcontinuity of the EEG](https://archive.physionet.org/physiobank/database/sleep-edfx/Papers/2000-Kemp---neurofeedback.pdf).
_IEEE-BME_ **47**(9):1185–1194 (2000)
2. MS Mourtazaev, B Kemp, AH Zwinderman, HAC Kamphuisen.
[Age and gender affect different characteristics of slow waves in the sleep EEG](http://www.ncbi.nlm.nih.gov/pubmed/8552926).
_Sleep_ **18**(7):557–564 (1995).
3. A Rechtschaffen, AE Kales. A manual of standardized terminology,
techniques and scoring systems for sleep stages of human subjects. Los Angeles,
CA: UCLA Brain Information Service. Brain Research Institute 10 (1968).
4. B van Sweden, B Kemp, HAC Kamphuisen, EA van der Velde.
[Alternative\\
electrode placement in (automatic) sleep scoring (Fpz-Cz/Pz-Oz versus\\
C4-A1/C3-A2)](http://europepmc.org/abstract/MED/2356401).
_Sleep_ **13**(3):279–283 (1990).
5. B Kemp, A Värri, AC Rosa, KD Nielsen, J Gade.
[A simple\\
format for exchange of digitized polygraphic recordings](http://www.ncbi.nlm.nih.gov/pubmed/1374708).
_Electroencephalography and Clinical Neurophysiology_ **82**:391–393
(1992).
6. B Kemp, J Olivan.
[European data format 'plus' (EDF+), an EDF alike standard format\\
for the exchange of physiological data](http://www.clinph-journal.com/article/S1388-2457(03)00123-8).
_Clinical Neurophysiology_ **114**:1755–1761 (2002).
7. B Kemp.
[Model-based monitoring of human\\
sleep stages](https://archive.physionet.org/physiobank/database/sleep-edfx/Papers/1987-Kemp---sleep-monitor.pdf).
Ph.D. thesis, Twente University (1987).
8. B Kemp, AJMW Janssen, MJ Roessen.
[A digital telemetry system for\\
ambulatory sleep recording](https://archive.physionet.org/physiobank/database/sleep-edfx/Papers/1993-Kemp---telemetry.pdf).
In: _Sleep-Wake Research in The Netherlands_ 4,
eds ML Coenen and J Arends,
Dutch Society for Sleep Wake Research, pp 129–132 (1993).

```
 Name                    Last modified      Size  Description Parent Directory                             -
 DOI                     2018-08-29 16:54   19
 MD5SUMS                 2019-02-13 11:16  272
 RECORDS                 2018-04-05 11:44  6.2K  list of record names
 RECORDS-v1              2018-04-05 11:44  1.0K  list of record names
 SC-subjects.xls         2018-04-05 11:44   24K
 SHA1SUMS                2019-02-13 11:16  320
 SHA256SUMS              2019-02-13 11:16  464
 ST-subjects.xls         2018-04-05 12:14   23K
 sleep-cassette/         2019-02-13 11:18    -
 sleep-telemetry/        2019-02-13 11:20    -
```

[**Questions and Comments**](https://archive.physionet.org/contact-us.shtml)

|     |     |
| --- | --- |
| If you would like help understanding, using, or downloading content, please see our [Frequently Asked Questions](https://archive.physionet.org/faq.shtml).<br>If you have any comments, feedback, or particular questions regarding this page, please send them to the [webmaster](https://archive.physionet.org/contact-us.shtml).<br>Comments and issues can also be raised on PhysioNet's [GitHub](https://github.com/MIT-LCP/physionet) page.<br>Updated <br>Friday, 28 October 2016 at 16:58 EDT | PhysioNet is supported by the [National Institute of General Medical Sciences (NIGMS)](http://www.nigms.nih.gov/) and the [National Institute of Biomedical Imaging and Bioengineering (NIBIB)](https://www.nibib.nih.gov/) under NIH grant number 2R01GM104987-09. |