import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

import json
import os
import pandas as pd
import plotly.graph_objs as go
from collections import Counter

import utils
from app import app

########## importing in data ##########

work_dir = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(work_dir, "..", "data", "master_flags_dataset.csv"))

########## defining main elements ##########

title = "Part 1: Does the Bachelor/ette have a representation problem?"
subtitle = "..Yes. And here are the numbers to prove it."

########## helper classes ##########

class MultiDropDown(dcc.Dropdown):
  def __init__(self, values, **kwargs):
    super().__init__(
      options=utils.get_form_options(values),
      value=list(values),
      multi=True,
      **kwargs)

class Tab(dcc.Tab):
  def __init__(self, children, **kwargs):
    super().__init__(**kwargs)
    self.children = [html.Br()] + children

########## designing general ui ##########

##### dashboard #####

dashboard = html.Div(
  className="col-sm-3",
  children=[
    html.H5("Change what this figure shows:"),
    html.Br(),
    utils.FormElement(
      label="Contestants",
      element=dcc.Dropdown(
        id="leads",
        options=[
          {"label": "Leads", "value": True}, 
          {"label": "Contestants", "value": False}
        ],
        value=[True, False],
        multi=True
      )
    ),
    utils.FormElement(
      label="Show(s)",
      element=MultiDropDown(
        id="shows",
        values=["Bachelor", "Bachelorette"]
      )
    ),
    utils.FormElement(
      label="Year(s)",
      element=dcc.RangeSlider(
        id="years",
        min=2002,
        max=2018,
        step=1,
        marks={2002: 2002, 2010: 2010, 2018: 2018},
        value=[2002, 2018]
      ),
      add_elements=[
        html.Br(), 
        html.P(id="selected-years", className="text-right small")
      ]
    ),
    utils.FormElement(
      label="Comparison Specificity",
      element=dcc.Dropdown(
        id="race",
        options=[
          {"label": "POC / Non-POC", "value": "poc_flag"},
          {"label": "All categories", "value": "all"}
        ],
        value="poc_flag"
      )
    )
  ]
)

##### tabs #####

overall_tab = Tab(
  label="Overall", 
  value="overall", 
  children=[
    html.Div(id="overall-value", style=dict(display="none")),
    html.H3("POC are under-represented on the Bachelor/ette"),
    dcc.Graph(id="overall-graph"),
    html.H4(
      "However you cut it, very few people of color make it onto the " \
      + "Bachelor and Bachelorette. Within this data selection:"),
    html.Br(),
    dcc.Markdown(id="overall-caption", className="caption"),
  ]
)

evolution_tab = Tab(
  label="Evolution", 
  value="evolution",
  children=[
    html.H3("The representation of POC has been improving over time"),
    dcc.Graph(id="evolution-graph")
  ]
)

comparison_tab = Tab(
  label="Comparison", 
  value="comparison",
  children=[
    html.H3("The Bachelor/ette is still less diverse than the U.S. at large")
  ]
)

panel = html.Div(
  className="col-sm-9 text-center",
  children=utils.Tabs(
    value="overall",
    children=[
      overall_tab,
      evolution_tab,
      comparison_tab,
    ]
  )
)

main_content = html.Div(
  className="row",
  children=[dashboard, panel]
)

layout = utils.BSContainer(
  title=title,
  subtitle=subtitle,
  main_content=main_content)

########## interactive routes ##########

@app.callback(
  Output(component_id="selected-years", component_property="children"),
  [Input(component_id="years", component_property="value")])
def update_selected_years(years):
  """ shows user what the selected year range is """
  start, end = years
  return "Selected: ({start}, {end})".format(start=start, end=end)

##### overall tab routes #####

@app.callback(
  Output("overall-value", "children"),
  [Input(input_id, "value") for input_id in 
    ["leads", "shows", "years", "race"] ]
)
def clean_overall_data(leads, shows, years, race):
  start, end = years
  filtered_df = df[
    (df["race_data_flag"] == True)
    & (df["show"].isin(shows))
    & (df["year"] >= start)
    & (df["year"] <= end)
  ]
  lead_data = {}
  print("years:", years)
  for lead in leads:
    lead_df = filtered_df[filtered_df["lead_flag"] == lead]
    if race == "poc_flag":
      poc_series = lead_df["poc_flag"] \
                   .map(lambda x: {True: "POC", False: "White"}[x])
      counter = Counter(poc_series)
      lead_data[lead] = dict(counter)
    # when we want disaggregated race categories
    elif race == "all":
      race_flags = ["white", "afam", "amin", "hisp", "asn_paci", "oth", "mult"]
      race_titles = ["White", "African American", "American Indian", "Hispanic",
                     "Asian & Pacific Islander", "Other", "Multi"]
      race_title_dict = dict(zip(race_flags, race_titles))
      counts = lead_df.count()
      counter = {race_title_dict.get(race_flag): int(counts[race_flag]) 
                 for race_flag in race_flags}
      lead_data[lead] = dict(counter)
  return json.dumps(lead_data)

@app.callback(
  Output("overall-graph", "figure"),
  [Input("overall-value", "children"), Input("race", "value")]
)
def update_overall_graph(cleaned_data, race):
  """ generates figure for overall tab """
  data = json.loads(cleaned_data)
  if not data:
    return dict(data=[], layout=go.Layout())
  groupings = ["White", "POC"] if race == "poc_flag" else \
              ["White", "African American", "American Indian", "Hispanic",
                     "Asian & Pacific Islander", "Other", "Multi"]
  colors = dict(zip(groupings, utils.COLORSCHEME))
  traces = []
  for val in groupings:
    x_init = data.keys()
    y = [data.get(x).get(val) for x in x_init]
    x = list(map(lambda x: {"true": "Leads", "false": "Contestants"}[x], x_init))
    strat_bar = go.Bar(
      x=x,
      y=y,
      hoverinfo="x+y",
      marker=dict(color=colors.get(val, utils.PRIMARY_COLOR)),
      name=val
    )
    traces.append(strat_bar)
  layout = go.Layout(
    xaxis=dict(tickfont=dict(size=14)),
    yaxis=dict(title="Number of People", titlefont=dict(size=16)),
  )
  return dict(data=traces, layout=layout)

@app.callback(
  Output("overall-caption", "children"),
  [Input("overall-value", "children"), Input("race", "value")]
)
def update_overall_caption(cleaned_data, race):
  data = json.loads(cleaned_data)
  if not data or race != "poc_flag":
    return "##### Sorry! There are no stats available about this selection"
  caption_elts = []
  for v in data.keys():
    title = {"true": "leads", "false": "contestants"}[v]
    num_poc = data.get(v).get("POC")
    num_npoc = data.get(v).get("White")
    if num_npoc and not num_poc:
      temp = "##### There are no POC {title} for this selection"
      caption_elts.append(temp.format(title=title))
    elif num_poc and not num_npoc:
      temp = "##### There are no white {title} for this selection"
      caption_elts.append(temp.format(title=title))
    elif num_poc and num_npoc:
      temp = "##### There are {mult} times as many white {title} " \
             + "as there are POC {title}"
      mult = round(float(num_npoc)/num_poc, 1)
      caption_elts.append(temp.format(mult=mult, title=title))
  caption = "  \n".join(caption_elts)
  return caption


##### evolution tab routes #####

@app.callback(
  Output("evolution-graph", "figure"),
  [Input(input_id, "value") for input_id in 
    ["leads", "shows", "years", "race"] ]
)
def update_evolution_graph(leads, shows, years, race):
  return
