# [EEG](https://openneuro.org/search/modality/eeg) A Resting-state EEG Dataset for Sleep Deprivation

[Files](https://openneuro.org/datasets/ds004902/versions/1.0.8)[Download](https://openneuro.org/datasets/ds004902/versions/1.0.8/download)[Metadata](https://openneuro.org/datasets/ds004902/versions/1.0.8/metadata)

Follow12

Bookmark18

### BIDS Validation

8305 Warnings Valid

Analyze

Clone

## README

# General information

The dataset provides resting-state EEG data (eyes open,partially eyes closed) from 71 participants who underwent two experiments involving normal sleep (NS---session1) and sleep deprivation(SD---session2) .The dataset also provides information on participants' sleepiness and mood states.
（Please note here Session 1 (NS) and Session 2 (SD) is not the time order, the time order is counterbalanced across participants and is listed in metadata.）

# Dataset

## Presentation

The data collection was initiated in March 2019 and was terminated in December 2020. The detailed description of the dataset is currently under working by Chuqin Xiang,Xinrui Fan,Duo Bai,Ke Lv and Xu Lei, and will submit to Scientific Data for publication.

#### EEG acquisition

- EEG system (Brain Products GmbH, Steing- rabenstr, Germany, 61 electrodes)

- Sampling frequency: 500Hz

- Impedances were kept below 5k


## Contact

```
  * If you have any questions or comments, please contact:
  * Xu Lei: xlei@swu.edu.cn
```

## Article

Xiang, C., Fan, X., Bai, D. et al. A resting-state EEG dataset for sleep deprivation. Sci Data 11, 427 (2024). [https://doi.org/10.1038/s41597-024-03268-2](https://doi.org/10.1038/s41597-024-03268-2)

Read MoreCollapse

Files: 1228 Size: 8.29GB

A Resting-state EEG Dataset for Sleep Deprivation

-   CHANGES
-   README
-   dataset\_description.json
-   .gitattributes
-   participants.json
-   participants.tsv
- .datalad

- code

- sub-01

- sub-02

- sub-03

- sub-04

- sub-05

- sub-06

- sub-07

- sub-08

- sub-09

- sub-10

- sub-11

- sub-12

- sub-13

- sub-14

- sub-15

- sub-16

- sub-17

- sub-18

- sub-19

- sub-20

- sub-21

- sub-22

- sub-23

- sub-24

- sub-25

- sub-26

- sub-27

- sub-28

- sub-29

- sub-30

- sub-31

- sub-32

- sub-33

- sub-34

- sub-35

- sub-36

- sub-37

- sub-38

- sub-39

- sub-40

- sub-41

- sub-42

- sub-43

- sub-44

- sub-45

- sub-46

- sub-47

- sub-48

- sub-49

- sub-50

- sub-51

- sub-52

- sub-53

- sub-54

- sub-55

- sub-56

- sub-57

- sub-58

- sub-59

- sub-60

- sub-61

- sub-62

- sub-63

- sub-64

- sub-65

- sub-66

- sub-67

- sub-68

- sub-69

- sub-70

- sub-71


## Comments

Please sign in to contribute to the discussion.

By 雷锋 - over 2 years ago

clear all;clc;close all;

load Px.mat;

conName={'normal sleep','sleep deprivation'};

Hi, what is "Px.mat" in the code?

By [Sheharyar Khan](https://openneuro.org/user/0009-0006-0261-9642) [![ORCID logo](data:image/svg+xml,%3c?xml%20version=%271.0%27%20encoding=%27utf-8%27?%3e%3c!--%20Generator:%20Adobe%20Illustrator%2019.1.0,%20SVG%20Export%20Plug-In%20.%20SVG%20Version:%206.00%20Build%200)%20--%3e%3csvg%20version=%271.1%27%20id=%27Layer_1%27%20xmlns=%27http://www.w3.org/2000/svg%27%20xmlns:xlink=%27http://www.w3.org/1999/xlink%27%20x=%270px%27%20y=%270px%27%20viewBox=%270%200%20256%20256%27%20style=%27enable-background:new%200%200%20256%20256;%27%20xml:space=%27preserve%27%3e%3cstyle%20type=%27text/css%27%3e%20.st0{fill:%23A6CE39;}%20.st1{fill:%23FFFFFF;}%20%3c/style%3e%3cpath%20class=%27st0%27%20d=%27M256,128c0,70.7-57.3,128-128,128C57.3,256,0,198.7,0,128C0,57.3,57.3,0,128,0C198.7,0,256,57.3,256,128z%27/%3e%3cg%3e%3cpath%20class=%27st1%27%20d=%27M86.3,186.2H70.9V79.1h15.4v48.4V186.2z%27/%3e%3cpath%20class=%27st1%27%20d=%27M108.9,79.1h41.6c39.6,0,57,28.3,57,53.6c0,27.5-21.5,53.6-56.8,53.6h-41.8V79.1z%20M124.3,172.4h24.5%20c34.9,0,42.9-26.5,42.9-39.7c0-21.5-13.7-39.7-43.7-39.7h-23.7V172.4z%27/%3e%3cpath%20class=%27st1%27%20d=%27M88.7,56.8c0,5.5-4.5,10.1-10.1,10.1c-5.6,0-10.1-4.6-10.1-10.1c0-5.6,4.5-10.1,10.1-10.1%20C84.2,46.7,88.7,51.3,88.7,56.8z%27/%3e%3c/g%3e%3c/svg%3e)](https://orcid.org/0009-0006-0261-9642) \- 8 months ago

can we have Behavioral Scores associated for each participants can you share.

By clicking "I Agree", I affirm that I have the appropriate institutional permissions to receive de-identified data for secondary data analysis, and that neither I nor my collaborators will attempt to reidentify individuals whose data are contained in downloads from OpenNeuro. Further, if for any reason the identity of participants contained in downloads from OpenNeuro become known to me I will make no effort to recontact such participants and will provide immediate notice to OpenNeuro staff.

I Agree