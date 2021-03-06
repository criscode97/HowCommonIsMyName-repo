from functools import total_ordering
import plotly.graph_objs as go
from pandas.io import gbq  # to communicate with Google BigQuery
from google.oauth2 import service_account


from dash import Dash, dcc, html
import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
import pandas as pd

# initialize app and link to bootstrap
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

app.title = "How Common Is My Name?"
app_color = {"graph_bg": "#ffffff", "graph_line": "#ffffff"}


# load bigQuery credentials from json file
project_id = "hwocommonismyname"
credentials = service_account.Credentials.from_service_account_file(
    "hwocommonismyname-634c2e9f8359.json"
)

empty_figure = go.Figure()
empty_figure.update_layout(plot_bgcolor=app_color["graph_bg"], paper_bgcolor=app_color["graph_bg"],
                          yaxis = dict(showgrid=False, zeroline=False, tickfont = dict(color = app_color["graph_line"])),
                          xaxis = dict(showgrid=False, zeroline=False, tickfont = dict(color = app_color["graph_line"])))

alert = dbc.Alert("Your name selection did not generate any results.", color="danger",
                  dismissable=True)

# html/dash app layout config
app.layout = html.Div(
    [
        html.Div(
            [
                html.H1("How Common Is My Name?", style={"text-align": "center"}),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.Div(
                                                    [
                                                        html.Div(
                                                            dcc.Input(
                                                                id="input-on-submit",
                                                                type="text",
                                                                placeholder="Enter Your Name",
                                                                className="form-control mb-2",
                                                            ),
                                                        ),
                                                    ],
                                                    className="col-auto",
                                                ),
                                                html.Div(
                                                    children=[
                                                        html.Button(
                                                            "Submit",
                                                            id="submit-button",
                                                            n_clicks=0,
                                                            className="btn btn-primary mb-2",
                                                        ), html.Div(id="the-alert", children=[]),
                                                    ],
                                                    className="col-md-12",
                                                ),
                                            ],
                                            className="col-md-6",
                                        ),
                                    ],
                                    className="row justify-content-center align-items-center",
                                ),
                            ],
                            className="container",
                        ),
                    ],
                    className="container py-5 h-100",
                ),
            ],
            className="container p-5 align-middle text-center",
        ),
        html.Div(
            [
                html.Div(  # app content
                    [
                        html.Div(  # container fluid
                            [
                                html.Div(  # row justify-content-md-center
                                    [
                                        html.Div(
                                            [
                                                dcc.Graph(
                                                    id="names_map",
                                                    figure=dict(
                                                        layout=dict(
                                                            plot_bgcolor=app_color[
                                                                "graph_bg"
                                                            ],
                                                            paper_bgcolor=app_color[
                                                                "graph_bg"
                                                            ],
                                                        )
                                                    ),
                                                ),
                                            ],
                                            className="col-8",
                                        ),
                                        html.Div(  # col
                                            [
                                                # total indicator
                                                html.Div(  # row
                                                    [
                                                        html.Div(  # row
                                                            [
                                                                html.Div(
                                                                    [
                                                                        dcc.Graph(
                                                                            id="name-indicator",
                                                                            figure=dict(
                                                                                layout=dict(
                                                                                    plot_bgcolor=app_color[
                                                                                        "graph_bg"
                                                                                    ],
                                                                                    paper_bgcolor=app_color[
                                                                                        "graph_bg"
                                                                                    ],
                                                                                )
                                                                            ),
                                                                        ),
                                                                    ],
                                                                    className="col-4",
                                                                ),
                                                            ],
                                                            className="row",
                                                        ),
                                                        # Year graph
                                                        html.Div(  # col-sm-4
                                                            [
                                                                dcc.Graph(
                                                                    id="display_chart",
                                                                    figure=dict(
                                                                        layout=dict(
                                                                            plot_bgcolor=app_color[
                                                                                "graph_bg"
                                                                            ],
                                                                            paper_bgcolor=app_color[
                                                                                "graph_bg"
                                                                            ],
                                                                        )
                                                                    ),
                                                                ),
                                                            ],
                                                            className="col-4",
                                                        ),
                                                    ],
                                                    className="row ",
                                                ),
                                            ],
                                            className="col",
                                        ),
                                    ],
                                    className="row justify-content-md-center",
                                ),
                            ],
                            className="container d-flex justify-content-around",
                        ),
                    ],
                    className="app__content",
                ),
            ],
            className="container-fluid",
        ),
        html.Br(),
    ]
)
@app.callback(
    Output("the-alert", "children"),
    Input('submit-button', 'n_clicks'),
    State('input-on-submit', 'value'),
)
def err(n_clicks, name):
    if not name:
        return None
    name_query = f"""
    SELECT *
        FROM `hwocommonismyname.myname123456.ss_names`
        WHERE
        UPPER(name) LIKE '{name.upper()}'
        LIMIT 2;
    """
    name_df = gbq.read_gbq(
        name_query,
        project_id=project_id,
        dialect="standard",
        credentials=credentials,
    )
    if len(name_df)==0:
        return alert
    return None

# U.S. States map funtion:
@app.callback(
    Output("names_map", 'figure'),
    Input('submit-button', 'n_clicks'),
    State('input-on-submit', 'value'),
)
def display_map(n_clicks, name):
    # query string for big query
    if n_clicks == 0:
        return empty_figure
    name_query = f"""
    SELECT state, SUM(number) AS total
        FROM `hwocommonismyname.myname123456.ss_names`
        WHERE
        UPPER(name) LIKE '{name.upper()}'
        GROUP BY state;
    """
    # query data from BigQuery for table
    name_df = gbq.read_gbq(
        name_query,
        project_id=project_id,
        dialect="standard",
        credentials=credentials,
    )
    if len(name_df) == 0:
        return empty_figure
    # data dictiorary for the choropleth plot
    data = dict(
        type="choropleth",
        locations=name_df.state,
        locationmode="USA-states",
        z=name_df.total,
        colorscale="Plotly3",
        colorbar={"title": "colorbar"},
    )
    # Map Layout
    layout = dict(
        title={
            "font_size": 25,
            "text": "U.S. MAP",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        geo=dict(scope="usa", showlakes=True, lakecolor="rgb(0,191,255)"),
        height=600,
        width=700,
        margin=dict(autoexpand=True),
    )
    # create figure
    fig = go.Figure(data=[data], layout=layout)
    return fig


# Year/total Scatter plot funtion
@app.callback(
    Output("display_chart", "figure"),
    Input('submit-button', 'n_clicks'),
    State("input-on-submit", "value"),
)
def display_chart(n_clicks, name):
    if n_clicks == 0:
    # prevent the None callbacks is important with the store component.
    # you don't want to update the store for nothing.
        return empty_figure
    name_query = f"""
    SELECT year, SUM(number) AS total
        FROM `hwocommonismyname.myname123456.ss_names`
        WHERE
        UPPER(name) LIKE '{name.upper()}'
        GROUP BY year
        ORDER BY year;
    """
    # query for a new table for the year/total
    name_df = gbq.read_gbq(
        name_query,
        project_id=project_id,
        dialect="standard",
        credentials=credentials,
    )
    if len(name_df) == 0:
        return empty_figure
    # create scatter plot with new table
    fig = go.Figure(
        go.Scatter(x=name_df.year, y=name_df.total, mode="lines", name=name)
    )
    fig.update_layout(
        title={
            "font_size": 25,
            "text": "TOTAL PER YEAR",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        xaxis_title="Year",
        yaxis_title="S.S. Applications",
        paper_bgcolor=app_color["graph_bg"],
        xaxis=dict(
            showline=True,
            showgrid=False,
            showticklabels=True,
            linecolor="rgb(204, 204, 204)",
            linewidth=2,
            ticks="outside",
            tickfont=dict(
                family="Arial",
                size=12,
                color="rgb(82, 82, 82)",
            ),
        ),
        yaxis=dict(
            showgrid=False, zeroline=False, showline=False, showticklabels=False
        ),
        autosize=False,
        margin=dict(
            autoexpand=True,
        ),
        showlegend=False,
        plot_bgcolor=app_color["graph_bg"],
        height=350,
        width=350,
    )
    return fig


# Total indicator figure function
@app.callback(
    Output("name-indicator", "figure"),
    Input('submit-button', 'n_clicks'),
    State("input-on-submit", "value"),
)
def indicator(n_clicks, name):
    if n_clicks == 0:
    # prevent the None callbacks is important with the store component.
    # you don't want to update the store for nothing.
        return empty_figure
    name_query = f"""
    SELECT SUM(number) AS name_sum
        FROM `hwocommonismyname.myname123456.ss_names`
        WHERE
        UPPER(name) LIKE '{name.upper()}';
    """
    # Query for the sum of all names
    total = gbq.read_gbq(
        name_query,
        project_id=project_id,
        dialect="standard",
        credentials=credentials,
    )
    if total.dropna().empty:
        return empty_figure

    # initialize figure
    fig = go.Figure(
        go.Indicator(
            mode="number",
            value=int(total.name_sum),
            domain={"x": [0, 1], "y": [0, 1]},
        )
    )

    fig.update_layout(
        title={
            "font_size": 25,
            "text": "U.S. TOTAL",
            "y": 0.9,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
        },
        paper_bgcolor=app_color["graph_bg"],
        height=300,
        width=300,
        margin=dict(autoexpand=True),
    )
    return fig


if __name__ == "__main__":
    app.run_server(debug=True)
