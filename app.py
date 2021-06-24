
import pandas as pd
import numpy as np
import bisect
import numpy_financial as npf
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import plotly.express as px
from scipy.stats import binom
import math
from Assets.calculator_sim import calculator_sim


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server

###############
#Set up the inputs that aren't dynamic
#So that it's vaguely more efficient than running literally everything every time any change is made
###############

house_price_increments = 5000
absolute_min_house_price = 500000

num_reps = 2000
months = 60
house_additional_costs = 1200 / 3

# The LMI rates table to determine LMI costs on any purchase
lmi_rates_table = [
    (100, 1.0),
    (95, 0.0399),
    (94, 0.0376),
    (93, 0.034),
    (92, 0.0324),
    (91, 0.0309),
    (90, 0.0221),
    (89, 0.0184),
    (88, 0.0143),
    (87, 0.0134),
    (86, 0.0119),
    (85, 0.0108),
    (84, 0.0092),
    (83, 0.0086),
    (82, 0.0073),
    (81, 0.0072),
    (80, 0)
]

lmi_rates_table.sort()

# Decision of buy or rent, along with the odds for this to occur
# Set up the probability list first (0-1 in 0.01 increments)
s = 0
e = 1
step = 0.005
probability_list = [round(num, 2) for num in np.linspace(s, e, (e - s) * int(1 / step) + 1).tolist()]

# Determine what the correct probability is that at least 90% of outcomes over the trial should be buy
# We don't need to fix for the possibility that no probability returns a 90% success rate FYI - Our probability list goes to 1, which of course produces a result of 1.
for pr in probability_list:
    binomial_pr = pr
    if 1 - binom.cdf(0, months, pr) >= 0.85:
        break

decisions = ['Buy', 'Rent']
decisions_odds = [binomial_pr, 1 - binomial_pr]

###############
#Set up the layout
###############

#Left hand card inputs
lhc_label_width = 5
lhc_input_width = 7


house_price_inputs = dbc.Row(
    [
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Minimum House Price', html_for='house-price-min-input'),
                    dbc.Input(
                        type='number', id='house-price-min-input', value='600000', min=absolute_min_house_price, step=house_price_increments
                    )
                ]
            ),
            width=6
        ),
        dbc.Col(
            dbc.FormGroup(
                [
                    dbc.Label('Maximum House Price', html_for='house-price-max-input'),
                    dbc.Input(
                        type='number', id='house-price-max-input', value='650000', min=absolute_min_house_price, step=house_price_increments
                    )
                ]
            ),
            width=6
        )
    ],
    form=True,
    style={'margin-top': '-10px', 'margin-bottom': '-5px'}
)


monthly_savings_input = dbc.Row(
    [
        dbc.Col(
            dbc.Label('Monthly Savings:', html_for= 'savings-input'),
            width=5,
            style={'margin-bottom': '5px'}
        ),
        dbc.Col(
            dbc.Input(id='savings-input', value='3000', type='number', min=0),
            width=7,
            style={'margin-bottom': '5px'}
        )
    ]
)

purchase_cost_input =dbc.FormGroup(
    [
        dbc.Label('Purchase Costs:', html_for='purchase_costs-input', width=lhc_label_width),
        dbc.Col(
            dbc.Input(id='purchase_costs-input', value='2000', type='number', min=0),
            width=lhc_input_width
        )
    ],
    row=True,
    style={'margin-bottom': '5px'}
)

monthly_rent_input = dbc.FormGroup(
    [
        dbc.Label('Monthly Rent:', html_for='monthly_rent-input', width=lhc_label_width),
        dbc.Col(
            dbc.Input(id='monthly_rent-input', value='1600', type='number', min=0),
            width=lhc_input_width
        )
    ],
    row=True,
    style={'margin-bottom': '5px'}
)

initial_savings_inputs = dbc.FormGroup(
    [
        dbc.Label('Initial Savings: ', html_for='initial_savings-input', width=lhc_label_width),
        dbc.Col(
            dbc.Input(id='initial_savings-input', value='32500', type='number', min=0),
            width=lhc_input_width
        )
    ],
    row=True,
    style={'margin-bottom': '5px'}
)

home_loan_rate_input = dbc.FormGroup(
    [
        dbc.Label('Home Loan Rate', html_for='home-loan-interest-rate-input', width=lhc_label_width),
        dbc.Col(
            dbc.Input(id='home-loan-interest-rate-input', value=0.0299, step=0.0001, min=0, type='number'),
            width=lhc_input_width
        )
    ],
    row=True,
    style={'margin-bottom': '5px'}
)

savings_rate_input = dbc.FormGroup(
    [
        dbc.Label('Savings Rate', html_for='savings-interest-rate-input', width=lhc_label_width),
        dbc.Col(
            dbc.Input(type='number', id='savings-interest-rate-input', value='0.012', min=0, step=0.0001),
            width=lhc_input_width
        )
    ],
    row=True,
    style={'margin-bottom': '5px'}
)

#This is the submit button required to run the choices
lhc_submit_button = dbc.Col(
    dbc.Button("Calculate", id="calculate-button", size="md", style={"width": '20vH'}),
    width={"size": 12, "offset": 2},
    style={'margin-bottom': '-15px'}
)

row_one = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1('Home Buying Calculator'),
                    width={"size": 6, "offset": 2}
                )
            ]
        )
    ]
)

left_card = dbc.Card(
    [
        dbc.CardHeader("Calculator inputs below"),
        dbc.CardBody(
                    [
                    house_price_inputs,
                    monthly_savings_input,
                    purchase_cost_input,
                    monthly_rent_input,
                    initial_savings_inputs,
                    home_loan_rate_input,
                    savings_rate_input,
                    lhc_submit_button
                    ]
        )
    ]
)

row_three = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(left_card, width=3),
                dbc.Col(
                    dcc.Graph(id='net-value-graph'),
                    width=9
                )
            ]
        )
    ]
)

left_metrics_card = dbc.Card(
    [
        dbc.CardHeader("Metrics"),
        dbc.CardBody([
            html.H6("Purchase median net value:"),
            html.Div(id='median-buy-output'),
            html.Br(),
            html.H6("Renting net value:"),
            html.Div(id='median-rent-output'),
            html.Br(),
            html.H6("Median Return:"),
            html.Div(id='median-return-output')
        ])
    ]
)

row_four = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    left_metrics_card,
                    width=3
                ),
                dbc.Col(
                    dcc.Graph(id='median-yearly-graph'),
                    width=9
                )
            ]
        )
    ]
)

app.layout = dbc.Container(fluid=True, children=([
                            row_one,
                            row_three,
                            html.Br(),
                            row_four
                            ]
                            )
                        )

@app.callback(
    Output('net-value-graph', 'figure'),
    Output('median-yearly-graph', 'figure'),
    Output('median-buy-output', 'children'),
    Output('median-rent-output', 'children'),
    Output('median-return-output', 'children'),
    Input('calculate-button', 'n_clicks'),
    State('house-price-min-input', 'value'),
    State('house-price-max-input', 'value'),
    State('savings-input', 'value'),
    State('purchase_costs-input', 'value'),
    State('monthly_rent-input', 'value'),
    State('initial_savings-input', 'value'),
    State('home-loan-interest-rate-input', 'value'),
    State('savings-interest-rate-input', 'value')
    )
def update_figure(n_clicks, house_price_min, house_price_max, selected_monthly_savings, selected_purchase_costs, monthly_rent_input, initial_savings_input, interest_rate_input, savings_interest_rate_input):
    # These are our input variables

    monthly_savings = int(selected_monthly_savings)
    monthly_rent = int(monthly_rent_input)
    initial_savings = int(initial_savings_input)
    purchase_costs = int(selected_purchase_costs)
    interest_rate = float(interest_rate_input)
    savings_rate = float(savings_interest_rate_input)
    house_price_min = int(house_price_min)
    house_price_max = int(house_price_max)

    #Error handling for when someone puts figures in
    if house_price_min <= absolute_min_house_price:
        house_price_min = absolute_min_house_price
    if house_price_max <= house_price_min + house_price_increments:
        house_price_max = house_price_min + house_price_increments
    if monthly_savings < 0:
        monthly_savings = 0
    if monthly_rent < 0:
        monthly_rent = 0
    if initial_savings < 0:
        initial_savings = 0
    if purchase_costs < 0:
        purchase_costs = 0
    if interest_rate < 0:
        interest_rate = 0
    if savings_rate < 0:
        savings_rate = 0

# Creating house prices
    # This gives random house prices in increments of $5K between $600K and $650K
    house_price_low_int = (house_price_min/house_price_increments)
    house_price_high_int = (house_price_max/house_price_increments)+1
    house_price = np.random.randint(low=house_price_low_int, high=house_price_high_int, size=(num_reps,)) * house_price_increments

    full_df = calculator_sim(house_price,
                            num_reps,
                            months,
                            initial_savings,
                            monthly_savings,
                            monthly_rent,
                            house_additional_costs,
                            purchase_costs,
                            interest_rate,
                            savings_rate,
                            lmi_rates_table,
                            decisions,
                            decisions_odds)

    df = full_df
    df['Net_Value'] = (df['Home_Price'] + df['Savings_Balance']) - df['Loan_Amount']
    df = df[df['Month'] == months].reset_index()
    df['Purchase_Year'] = df['Purchase_Month'].apply(lambda x: math.floor(x / 12) + 1)
    df.loc[df['Home_status'] == 'Mortgage', 'Home_status'] = 'Buy'
    df['PCT_Rank'] = df['Net_Value'].rank(pct=True)
    df['Comparison_Net_Value'] = df['Net_Value'] - df[df['Home_status'] == 'Rent']['Net_Value'].median()

    #This will set the colour scheme for the first two graphs
    home_status_colour_scheme = {
        "Buy": "rgb(253,192,134)",
        "Rent": "rgb(190,174,212)"
    }

    pct_fig = px.histogram(df, x="Comparison_Net_Value", color='Home_status',
                           color_discrete_map=home_status_colour_scheme,
                           title="Outcome by Percentile Ranking"
                           )

    median_groups = df.groupby(['Home_status', 'Purchase_Year'])['Net_Value'].median()
    median_groups.columns = ['Home_status', 'Purchase_Year', 'Median_Net_Value']
    median_groups = median_groups.reset_index()
    median_groups = median_groups.loc[(median_groups['Home_status'] != 'Rent') & (median_groups['Purchase_Year'] != 6)]

    median_value_year_fig = px.bar(median_groups, x='Purchase_Year', y='Net_Value',
                                   template='simple_white',
                                   labels={
                                       "Net_Value": "Net Value",
                                       "Purchase_Year": "Year of Purchase"
                                   },
                                   title='Median net value by purchase year compared to rent net value',
                                   height=400)

    median_value_year_fig.add_hrect(
        y0=0,
        y1=df[df['Home_status'] == 'Rent']['Net_Value'].median(),
        fillcolor='rgb(190,174,212)',
        opacity=0.5
    )

    median_value_year_fig.update_traces(marker_color='rgb(253,192,134)')

    median_value_year_fig.update_layout(
        title=dict(
        x=0.5,
        font_size=18
        )
    )

    net_value_fig = px.histogram(df, x="Net_Value", color='Home_status',
                                 color_discrete_map=home_status_colour_scheme,
                                 labels={
                                     "Net_Value": "Net Value",
                                     "Home_status": "Ownership"
                                 },
                                 template="simple_white",
                                 title="Number of scenarios within given outcome")

    net_value_fig.update_layout(
        yaxis_title='Number of Outcomes',
        title=dict(
        x=0.5,
        font_size=18
        )
    )

    buy_median_value = "$" + str(int(df[df['Home_status'] == 'Buy']['Net_Value'].median()))

    rent_median_value = "$" + str(int(df[df['Home_status'] == 'Rent']['Net_Value'].median()))

    median_return = "$" + str(int(df[df['Home_status'] == 'Buy']['Net_Value'].median()) -
                              int(df[df['Home_status'] == 'Rent']['Net_Value'].median()))

    return net_value_fig, median_value_year_fig, buy_median_value, rent_median_value, median_return


if __name__ == '__main__':
    app.run_server(debug=True)
