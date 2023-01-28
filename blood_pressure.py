import os, sys
import pandas as pd
import datetime as dt
import pytz
import numpy as np

from bokeh.io import show
from bokeh.plotting import figure
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, DatetimeTickFormatter, HoverTool, Range1d, Span, Label

# import dates
try:
    from dates import DATES
except:
    DATES = []


# color of the grey scatter dots
GREY_COLOR = "#CCCCCC"


# Bokeh time tick mark formatter
tick_formatter = DatetimeTickFormatter(
        years="%Y",
        months="%Y %b",
        days="%y %b %d",
        hours="%b %d %H:00",
        hourmin="%d %H:%M",
        minutes="%d %H:%M",
        minsec="%H:%M %Ss",
        seconds="%Ss",
        milliseconds='%S.%3Ns',
        microseconds='%S.%fs'
    )


def fit(df, y):
    """ Given a dataframe, plot a polyfit line"""
    print(min(df["datetime"]), max(df["datetime"]))
    x = [t.timestamp() for t in df["datetime"]]
    print(min(x), max(x))
    y = df[y]
    model = np.poly1d(np.polyfit(x, y, 2))
    x_fit = np.linspace(min(x), max(x), 1000)
    y_fit = model(x_fit)
    x_fit = [pd.Timestamp(t, unit='s') for t in x_fit]
    return x_fit, y_fit

# Read all CSV files in this directory and convert to one big Pandas DataFrame
df = pd.DataFrame()
for file in os.listdir("./"):
    if file.endswith(".csv"):
        print(file, end=' ...')  # printing file name
        file_df = pd.read_csv(file)
        file_df = file_df[["Date", "Time", "Systolic", "Diastolic", "Heart Rate"]]
        df = pd.concat([df, file_df])  # add to main dataframe
        print("[done]")

# convert "Date" and "Time" columns to a single "datetime" column
datetimes = []
for i, row in df.iterrows():
    # read time strings and use UTC (default is to use local time)
    datetime = dt.datetime.strptime(f"{row['Date']} {row['Time']}", '%m/%d/%Y %I:%M %p').replace(tzinfo=pytz.timezone('UTC'))
    datetimes.append(datetime)
df = df.drop(["Date", "Time"], axis="columns")  # remove Date and Time columns
df.insert(0, "datetime", datetimes)  # add combined datetime column

# Sort by datetime
df.sort_values("datetime", inplace=True)
df.reset_index(inplace=True)  # reorder indexes

# combine and average readings taken within 60 mins of each other, store in a new df
clumped_df = pd.DataFrame(columns=df.columns.values)  # new dataframe to populate with clumped data
clump = []  # current clump of rows to be averaged
delta = dt.timedelta(minutes=60)  # time interval to clump by
for i in range(len(df)):  # iterate through rows
    row = df.iloc[i]  # current row
    next = None  # next row
    prev = None  # previous row
    if i > 0: prev = df.iloc[i-1]
    if i+1 < len(df): next = df.iloc[i+1]

    # if current reading is in the clump (first in a clump or within the time range of the previous row in the clump)
    if prev is None or len(clump) == 0 or (row['datetime'] - prev['datetime']) <= delta:
        clump.append(row)  # add current row to the clump

        # if that was the last row in the clump (last reading total or the next reading is out of time range)
        if next is None or (next['datetime'] - row['datetime']) > delta:
            if len(clump) == 1:  # only 1 reading in the clump, and this was it
                clumped_df.loc[i] = row  # add this row to the new df as-is without clumping anything
            if len(clump) > 1:  # multiple readings in the clump
                clumped_df.loc[i] = {
                    "datetime": dt.datetime.utcfromtimestamp(np.average([r['datetime'].timestamp() for r in clump])).replace(tzinfo=pytz.timezone('UTC')),
                    "Systolic": np.average([r['Systolic'] for r in clump]),
                    "Diastolic": np.average([r['Diastolic'] for r in clump]),
                    "Heart Rate": np.average([r['Heart Rate'] for r in clump])
                }
            clump = []  # start a new clump

clumped_df.sort_values("datetime", inplace=True)  # sort the clumped data again just in case

# create Bokeh sources from the dataframes
source = ColumnDataSource(df)  # raw data
clumped_source = ColumnDataSource(clumped_df)  # clumped data

# Blood Pressure Figure

hovertool = HoverTool(
    tooltips=[('', '@datetime{%I:%M %p}:  @Systolic / @Diastolic')],
    formatters={'@datetime': 'datetime'}
)

fig1 = figure(tools=['xpan', 'xwheel_zoom', 'reset', hovertool],
              active_drag="xpan", active_scroll="xwheel_zoom",
              toolbar_location="above",
              y_axis_label="Blood Pressure (mmHg)",
              height=500,  # width is dynamic
              width=2000,
              x_range=(df.iloc[0]["datetime"], df.iloc[-1]["datetime"]),  # set x-range to start and end of data (it gets messed up by the invisible legend lines)
              y_range=(df['Diastolic'].min()-5, df['Systolic'].max()+5)   # give y-range a little buffer around min and max
)
fig1.xaxis.formatter = tick_formatter  # format x-axis time values

fig1.circle(x='datetime', y='Systolic', source=source, fill_color=GREY_COLOR, line_color=None, size=7)  # raw scatter
fig1.line(x='datetime', y='Systolic', source=clumped_source, color='red', line_width=5, legend_label="Systolic")  # clumped line
fig1.circle(x='datetime', y='Systolic', source=clumped_source, fill_color='red', line_color="black", size=10)  # clumped scatter
#x, y = fit(df, "Systolic")
#fig1.line(x=x, y=y, line_color="red", line_width=5)

fig1.circle(x='datetime', y='Diastolic', source=source, fill_color=GREY_COLOR, line_color=None, size=7)
fig1.line(x='datetime', y='Diastolic', source=clumped_source, color='orange', line_width=5, legend_label="Diastolic")
fig1.circle(x='datetime', y='Diastolic', source=clumped_source, fill_color='orange', line_color="black", size=10)


fig1.add_layout(fig1.legend[0], 'right')  # move legend to the right of the plot

# 120/70 baselines
sys_line  = Span(location=120, dimension='width', line_color='black', line_dash='dashed', line_width=3)
dia_line  = Span(location=70, dimension='width', line_color='black', line_dash='dashed', line_width=3)
fig1.line(x=0, y=0, color='black', line_width=3, line_dash="dashed", legend_label="120/70 baseline")  # invisible line for the legend
fig1.add_layout(sys_line)
fig1.add_layout(dia_line)

# Mark dates from DATES dict
for info in DATES:
    label = info['label']
    color = info['color']
    dates = info['dates']

    # add an invisible line for the legend
    fig1.line(x=0, y=0, color=color, line_width=3, line_dash="dashed", legend_label=label)
    for date in dates:
        span = Span(location=date, dimension='height', line_color=color, line_dash='dashed', line_width=3)
        fig1.add_layout(span)


# Heart Rate Figure

hovertool = HoverTool(
    tooltips=[('', '@datetime{%I:%M %p}:  @{Heart Rate}')],
    formatters={'@datetime': 'datetime'}
)

fig2 = figure(tools=['xpan', 'xwheel_zoom', 'reset', hovertool],
              active_drag="xpan", active_scroll="xwheel_zoom",
              x_range=fig1.x_range,
              height=150, width=2000,
              toolbar_location=None,
              x_axis_label="Date", y_axis_label="Heart Rate (cnt/min)"
)

fig2.xaxis.formatter = tick_formatter

fig2.circle(x='datetime', y='Heart Rate', source=source, fill_color=GREY_COLOR, line_color=None, size=7)
fig2.line(x='datetime', y='Heart Rate', source=clumped_source, color='green', line_width=5)
fig2.circle(x='datetime', y='Heart Rate', source=clumped_source, fill_color='green', line_color="black", size=10)


# Mark dates from DATES dict
for info in DATES:
    label = info['label']
    color = info['color']
    dates = info['dates']
    for date in dates:
        span = Span(location=date, dimension='height', line_color=color, line_dash='dashed', line_width=3)
        fig2.add_layout(span)


# Layout
col = column(fig1, fig2, sizing_mode="stretch_width")
show(col)


