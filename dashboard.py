# -*- coding: utf-8 -*-
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import sqlite3
import plotly
from datetime import datetime, timedelta
import plotly.graph_objs as go

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

data = {'x': [], 'y': []}

colorway = ['#385891', '#9089A3', '#8098BF', '#B1B4B1', '#66BB6A', '#ed1c40']

def generate_card(title, figure):
    return html.Div(
        className="two columns",
        style={"textAlign": "center"},
        children=[
            html.Div(children=title),
            html.Div(children=figure)
        ]
    )

def generate_line(input_dir, name):
    return go.Scatter(
            x=input_dir['x'],
            y=input_dir['y'],
            mode='lines+markers',
            name=name,
            text=input_dir['text'],
            textposition='middle right',
            textfont={
                "size": 9
            },
            hoverinfo='y'
        )

def generate_pies(yes, no, name, iteration):
    return {
        'values': [yes, no],
        'labels': ['yes', 'no'],
        'title': name,
        'titlefont': {
            'color': '#7f7f7f',
            'size': 20
        },
        'type': 'pie',
        'domain': {'x': [1 - 0.2*iteration, 1.2 - 0.2*iteration]},
    }

        # go.Pie(
        #         labels=["Yes", 'No'],
        #         values=[yes, no],
        #         title=name
        #     )

app.layout = html.Div(children=[

    html.Img(src='https://secure.meetupstatic.com/s/img/286374644891845767035/logo/meetup-logo-script-1200x630.png',
             style={'width': '200px', 'float': 'left', 'top': '-20px', 'position': 'absolute'}),
    html.H1(children='RSVP DASHBOARD', style={'float': 'none', 'margin-bottom': '0', 'text-align': 'center',
                                              'font-family': 'Courier', 'color': '#424242'}),

    # html.Div(className='row', id='live-update-cards', children=[
    # ]),

    dcc.Graph(id='live-update-cards'),

    html.Div(className='row', children=[
        html.Div(className='six columns', children=dcc.Graph(id='live-update-bars')),
        html.Div(className='six columns', children=dcc.Graph(id='live-update-lines')),
        html.Div(className='mt-0 twelve columns', children=dcc.Graph(id='live-update-pies')),
    ]),

    dcc.Interval(
        id='interval-component',
        interval=1 * 5000,  # in milliseconds
        n_intervals=1
    )
])

@app.callback(Output('live-update-bars', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_bar_live(n):

    data['x'] = []
    data['y'] = []

    conn = sqlite3.connect('meetup.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(topic_name), topic_name FROM rsvp"
              " WHERE response = 'yes'"
              " GROUP BY topic_name ORDER BY COUNT(topic_name) DESC LIMIT 10")
    for point in c.fetchall():
        data['x'].insert(0, point[0])
        data['y'].insert(0, point[1])

    conn.close()

    figure1 = {
        'data': [
            {'x': data['x'], 'y': data['y'], 'type': 'bar', 'orientation': 'h', 'name': '1'},
        ],
        'layout': {
            'title': 'Top Categories by confirmed rsvps',
            'margin': {"l": 180,},
            'colorway': colorway
        }
    }

    return figure1

@app.callback(Output('live-update-lines', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_line_live(n):

    conn = sqlite3.connect('meetup.db')
    c = conn.cursor()

    data2 = {}

    first_point_time = datetime.now() - timedelta(minutes=5)

    c.execute("SELECT topic_name, COUNT(topic_name) FROM rsvp"
              " WHERE topic_name IN (SELECT topic_name FROM rsvp GROUP BY topic_name ORDER BY COUNT (urlkey) DESC LIMIT 5)"
              " AND strftime('%Y-%m-%dT%H:%M:%S.000', date) <= strftime('%Y-%m-%dT%H:%M:%S.000', ?)"
              " AND response = 'yes'"
              " GROUP BY topic_name ORDER BY COUNT(topic_name) DESC", (first_point_time,))

    for point in c.fetchall():
        data2.setdefault(point[0], {'x': [], 'y': [], 'current_point': 0, "text": []})
        data2[point[0]]['current_point'] += point[1]
        data2[point[0]]['x'].append(str(first_point_time))
        data2[point[0]]['y'].append(data2[point[0]]['current_point'])
        data2[point[0]]['text'].append('')

    c.execute("SELECT topic_name, COUNT(urlkey), strftime('%Y-%m-%dT%H:%M:%S.000', date) FROM rsvp"
              " WHERE topic_name IN (SELECT topic_name FROM rsvp GROUP BY topic_name ORDER BY COUNT (urlkey) DESC LIMIT 5)"
              " AND strftime('%Y-%m-%dT%H:%M:%S.000', date) > strftime('%Y-%m-%dT%H:%M:%S.000', ?)"
              " AND response = 'yes'"
              " GROUP BY strftime('%Y-%m-%dT%H:%M:%S.000', date), topic_name"
              " ORDER BY strftime('%Y-%m-%dT%H:%M:%S.000', date)", (first_point_time,)
              )

    for point in c.fetchall():
        data2[point[0]]['current_point'] += point[1]
        data2[point[0]]['x'].append(point[2])
        data2[point[0]]['y'].append(data2[point[0]]['current_point'])
        data2[point[0]]['text'].append('')

    conn.close()

    fig2_data = []
    for key in data2:
        data2[key]["text"][-1:] = data2[key]["y"][-1:]
        fig2_data.append(generate_line(data2[key], key))

    figure2 = {
        'data': fig2_data,
        'layout': {
            'title': 'RSVPs by category (top 5) per minute',
            #'xaxis': dict(range=[last_hour_date_time, datetime.now()])
            'colorway': colorway
        }
    }

    return figure2

@app.callback(Output('live-update-pies', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_pies(n):

    conn = sqlite3.connect('meetup.db')
    c = conn.cursor()

    c.execute("SELECT COUNT(topic_name), topic_name FROM rsvp"
              " WHERE topic_name IN (SELECT topic_name FROM rsvp GROUP BY topic_name ORDER BY COUNT (urlkey) DESC LIMIT 5)"
              " AND response = 'no'"
              " GROUP BY topic_name ORDER BY COUNT(topic_name)")

    data3 = {}

    for point in c.fetchall():
        data3[point[1]] = point[0]

    conn.close()

    fig = {'data': [], 'layout': {'colorway': ['#66BB6A', '#EF5350']}}

    i = 1

    for x, y in zip(data['x'], data['y']):
        if y in data3:
            fig['data'].append(generate_pies(x, data3[y], y, i))
            i += 1

    return fig


@app.callback(Output('live-update-cards', 'figure'),
              [Input('interval-component', 'n_intervals')])
def update_cards(n):

    return {
        'data': [go.Table(
            header=dict(values=list(reversed(data['y']))[:5], fill = dict(color=colorway),
                        font = dict(color = 'white', size = 16), height = 30),
            cells=dict(values=list(reversed(data['x']))[:5], font = dict(size = 24), height = 35)
        )],
        'layout': go.Layout(
            autosize=False,
            height=80,
            margin=go.layout.Margin(
                l=5,
                r=5,
                b=5,
                t=5,
                pad=4
            ),
            colorway=colorway
        )
    }


if __name__ == '__main__':
    app.run_server(debug=True)