import datetime as dt

# Important dates to mark on the plot.
# For each item added, a vertical line is drawn on the time series.

DATES = [
    {"label": "Started Medication X",
     "color": "purple",
     "dates": [dt.datetime(year=2022, month=6, day=1)]
     },
    {"label": "Started/Stopped Medication Y",
     "color": "blue",
     "dates": [dt.datetime(year=2022, month=7, day=1), dt.datetime(year=2022, month=8, day=1)]
    }
]