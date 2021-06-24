import bisect
import numpy_financial as npf
import numpy as np
import pandas as pd

def calculator_sim(house_price,
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
                   decisions_odds):

    # Required lists
    rows = []

    for idx, purchase_price in enumerate(house_price):
        savings_balance = initial_savings
        home_status = 'Rent'
        month_count = []
        loan_amount = 0
        for month_count in range(0, months + 1):
            temp_lvr = (((purchase_price + purchase_costs) - savings_balance) / purchase_price) * 100
            lvr_calc = (
                    ((purchase_price * lmi_rates_table[bisect.bisect_left(lmi_rates_table, (temp_lvr,))][1]) + (
                                (purchase_price + purchase_costs) - savings_balance))
                    / purchase_price) if home_status == 'Rent' else 0
            home_status = 'Mortgage' if home_status == 'Buy' or home_status == 'Mortgage' else \
            np.random.choice(decisions, 1, p=decisions_odds)[0]
            if lvr_calc > 0.95:
                savings_balance *= 1 + (savings_rate / 12)
                savings_balance += monthly_savings
                home_status = 'Rent'
                home_price = 0
                lvr = 0
                monthly_payments = 0
                loan_amount = 0
                monthly_interest_payment = 0
                monthly_principal_payment = 0
                purchase_month = months + 1
            elif lvr_calc <= 0.95:
                # Now that we have made updates to home status as applicable, we can run the calculations we need.
                if home_status == 'Rent':
                    savings_balance *= 1 + (savings_rate / 12)
                    savings_balance += monthly_savings
                    home_price = 0
                    purchase_month = months + 1
                if home_status == 'Buy':
                    savings_balance *= 1 + (savings_rate / 12)
                    home_price = purchase_price
                    lvr = (((home_price + purchase_costs) - savings_balance) / home_price) * 100
                    lmi_rate = lmi_rates_table[bisect.bisect_left(lmi_rates_table, (lvr,))][1]
                    loan_amount = (home_price + purchase_costs + (lmi_rate * home_price)) - savings_balance
                    savings_balance = monthly_savings  # This comes second to effectively reset the savings balance.
                    monthly_payments = -1 * npf.pmt(interest_rate / 12, 360,
                                                    loan_amount)  # This is the next thing to work on
                    purchase_month = month_count
                if home_status == 'Mortgage':
                    savings_balance *= 1 + (savings_rate / 12)
                    savings_balance += (monthly_savings + monthly_rent - monthly_payments - house_additional_costs)
                    home_price += home_price * (np.random.normal(.014,
                                                                 .0285) / 4)  # Mean & Std.Dev come from RBA Quarterly house price index in Sydney
                    monthly_payments = monthly_payments
                    monthly_interest_payment = (loan_amount - savings_balance) * (interest_rate / 12)
                    monthly_principal_payment = monthly_payments - (loan_amount - savings_balance) * (
                                interest_rate / 12)
                    loan_amount -= monthly_principal_payment
            rows.append([idx, month_count, loan_amount, home_price, savings_balance, monthly_payments, purchase_month, lvr_calc, home_status])

    monthly_df = pd.DataFrame(rows, columns=['Scenario', 'Month', 'Loan_Amount', 'Home_Price', 'Savings_Balance', 'Monthly_Repayment', 'Purchase_Month', 'LVR_CALC', 'Home_status'])

    return monthly_df