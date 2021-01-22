#!/usr/bin/python3

# Importing necessary Packages
import pandas as pd
import numpy as np
import time
import matplotlib.ticker as ticker
from collections import OrderedDict
import os

import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import plotly.express as px
import plotly.offline as pyo
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from plotly import tools
import plotly.graph_objects as go

import psycopg2 # python package for Postgres


# Postgres settings
conn = psycopg2.connect(
    host = "postgres_dwh",
    port = "5432",
    dbname = "postgres",
    user = "postgres",
    password = "postgres1234"
)
# count_tracks_distribution
sql = """SELECT * FROM count_tracks_distribution ORDER BY count DESC """
df3 = pd.read_sql(sql, conn)

# Manipulate counts
df3['0-50'] = np.where((df3['count'].between(0,50)), True, False)
df3['51-100'] = np.where((df3['count'].between(51,100)), True, False)
df3['101-200'] = np.where((df3['count'].between(101,200)), True, False)
df3['201-500'] = np.where((df3['count'].between(201,500)), True, False)
df3['501-1000'] = np.where((df3['count'].between(501,1000)), True, False)
df3['1001+'] = np.where(df3['count']>1000, True, False)
columns=['0-50','51-100','101-200','201-500','501-1000','1001+']
lenght = []
for item in columns:
    lenght.append(len(df3[df3[item] == True]))

# counts
counts = pd.DataFrame(data = lenght, index=columns, columns=["count"])

# audiofeatures_stat
sql = """SELECT * FROM audiofeatures_stat ORDER BY timestamp DESC """
audiofeature = pd.read_sql(sql, conn)
audiofeature = audiofeature[audiofeature['timestamp']>='2020-01']

# month_distribution
sql = """SELECT * FROM month_distribution ORDER BY year_month DESC """
month_distribution = pd.read_sql(sql, conn)

# Close connection
conn.close()


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Figures
counts_fig = px.bar(counts, 
                    y='count', 
                    title="Distribution of songs in playlists",
                    labels={
                     "index": "Range of values",
                     "count": "Count (units)"
                    })

audiofeature_mean = px.line(audiofeature, 
                            x="timestamp", 
                            y=["mean_danceability", "mean_energy", "mean_valence"], 
                            title="Audiofeature means per month",
                            labels={
                            "timestamp": "Period",
                            "value": "Mean"
                            })

audiofeature_stdev = px.line(audiofeature, 
                            x="timestamp", 
                            y=["stdev_danceability", "stdev_energy", "stdev_valence"], 
                            title="Audiofeature standard deviation per month",
                            labels={
                            "timestamp": "Period",
                            "value": "Mean"
                            })

month_dis = px.bar(month_distribution, 
                    x='year_month', 
                    y='count', 
                    title='Distribution of playlist during pandemic period',
                    labels={
                    "year_month": "Period",
                    "count": "Count (units)"
                })

# Layout
app.layout = html.Div(children=[
    html.H1(children='Spotify analysis about Covid playlists'),
    html.H3(children='Big Data project'),

    html.P(children='''
        Battista Francesco
    '''),
     html.P(children='''
        Parolin Irene
    '''),

    html.Div(children=[
        html.Div(children=[
            dcc.Graph(
                id='counts_fig',
                figure=counts_fig,
                config={"displayModeBar": False}
            ), 
            html.P(children='''
                The graph represents the distribution, divided into chunks, of the number of songs in the playlists. 
                The study unearthed playlists of nearly 10,000 songs.



            ''', style={'padding':'2em'})],
            style={'width': '45%',
            'margin':'10px',
            'display': 'inline-block', 
            'vertical-align':'top',
            'box-shadow': '0 4px 6px 0 rgba(0, 0, 0, 0.18)'
            }),
        
        html.Div(children=[
            dcc.Graph(
                id='month_dis',
                figure=month_dis,
                config={"displayModeBar": False}
            ),
           
            html.P(children='''
            The distribution of playlists throughout the pandemic is shown here.
            Some playlists were created long before the pandemic (around 2014).
            Later the name or even just the description was changed.
            The Spotify API considers these as playlists related to covid.
            They have not been taken into account in this graph.
            ''', style={'padding':'2em'})],
            style={'width': '45%',
            'margin':'10px',
            'display': 'inline-block', 
            'vertical-align':'top',
            'box-shadow': '0 4px 6px 0 rgba(0, 0, 0, 0.18)'
            })

    ],style={'width': '100%', 'display': 'inline-block'}),

    html.Div(children=[
            dcc.Graph(
                id='audiofeature_mean',
                figure=audiofeature_mean,
                config={"displayModeBar": False}
            ),
           
            html.P(children='''
                In this graph we can see the averages of the 3 audio features over the months.
                We can see that the average for each feature does not vary drastically from March, the month from which almost all playlists begin to be created.
                The average energy and danceability values reflect similar values of 0.62/0.63, but danceability remains the variable that reaches the highest values.
                Valence that describe the musical positiveness conveyed by a track, on the other hand, remains on average values around 0.5 and a continuous growth can 
                be seen from March to July and then decreases by 0.05 points in October.
            ''', style={'padding':'2em'})],
            style={
            'display': 'inline-block',
            'margin':'10px',
            'vertical-align':'top',
            'box-shadow': '0 4px 6px 0 rgba(0, 0, 0, 0.18)'
            }),

    html.Div(children=[
            dcc.Graph(
                id='audiofeature_stdev',
                figure=audiofeature_stdev,
                config={"displayModeBar": False}
            ),
           
            html.P(children='''
                Regarding standard deviation, the highest values are reached by the valence (0.20), so we can assume that tracks assume different values especially for this characteristic. 
                From March they are similar to 3 horizontal lines, and there is a small decrease in August for both valence and energy.

                Overall we can say that in these months there are no big differences in the variability of the spirit of the songs within the 2020 playlists. 
            ''', style={'padding':'2em'})],
            style={
            'display': 'inline-block', 
            'vertical-align':'top',
            'margin':'10px',
            'box-shadow': '0 4px 6px 0 rgba(0, 0, 0, 0.18)'
            })
], style={ 'margin':'0',
            'padding': '4em',
            'justify-content': 'center',
            'align-items': 'center'
            })
    

if __name__=="__main__":
    app.run_server(host=os.getenv('IP', '0.0.0.0'), 
            port=int(os.getenv('PORT', 7777)))