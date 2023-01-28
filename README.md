### Introduction

This is a script I wrote to plot my blood pressure over time, which I get by exporting CSV files from Livongo.
This means that the CSV format expected is for that site in particular.

It has only been tested on Windows with Python 3.11

Readings taken within 1 hour of each other will be averaged together in the plot, so it is beneficial to take 4-5
readings at a time each day.

### How to run
1. Create a venv and install requirements
2. Place CSV files in this directory
3. Run `blood_pressure.py`
4. Profit


### Expected CSV format:


This format is identical to the format exported by Livongo.
Times are assumed to have no timezone information.
Spacing is irrelevant.
```
Date,       Time,     Systolic, Diastolic, Heart Rate
07/01/2022, 10:06 AM, 120,      70,        60,
07/02/2022, 10:06 AM, 120,      70,        60,
```

### Adding plot annotations
You can add markers on the time series indicating dates when a medication was started, stopped, changed, etc.

Make a copy of `dates_template.py` and name it `dates.py`. Follow the format of the examples.

### TODO
- log into liveongo and automatically download the latest data
- Allow a config file to specify custom CSV formats
