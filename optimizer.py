import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- CONFIGURATION (2026 CONSTANTS) ---
LIMIT_PRETAX = 24500
LIMIT_TOTAL = 72000
LIMIT_MATCH = 6000
LIMIT_SS_WAGE_BASE = 184500  # Estimate for 2026
LIMIT_HSA = 4400  # Employee portion ($4400 total - $1000 employer)
LIMIT_IRA = 7500  # Backdoor Roth IRA Limit

# Tax Rates (Estimates for CA Single Filer 2026)
TAX_RATE_FED_MARGINAL = 0.24  # Base withholding est
TAX_RATE_CA_MARGINAL = 0.07   # Base withholding est
TAX_RATE_BONUS_FED = 0.22     # Flat Supplemental Rate
TAX_RATE_BONUS_CA = 0.1023    # Flat CA Supplemental Rate
RATE_FICA_SS = 0.062
RATE_FICA_MED = 0.0145
RATE_CA_SDI = 0.013 

def calculate_year(base_pre_pct, base_after_pct, bonus_pre_pct, bonus_after_pct, include_ira_cost):
    # --- EXACT INCOME DATA ---
    base_salary = 196842.00
    ote = 226368.30
    bonus_total = ote - base_salary # Exactly 29,526.30 (approx 15%)
    
    pay_periods = 24
    gross_per_check = base_salary / pay_periods
    
    # Bonus Schedule (75% April, 25% Sept)
    bonus_apr = bonus_total * 0.75
    bonus_sept = bonus_total * 0.25
    
    # Tracking Variables
    data = []
    ytd_pretax = 0
    ytd_aftertax = 0
    ytd_match = 0
    ytd_gross = 0
    ytd_espp = 0
    
    # Simulation Loop (24 Pay Periods)
    for period in range(1, 25):
        # 1. Base Pay Setup
        current_gross = gross_per_check
        is_bonus_period = False
        bonus_amount = 0
        bonus_name = ""
        
        # Inject Bonuses (Assigning to Period 8 [Apr 30] and Period 19 [Oct 15] for sim)
        if period == 8: 
            bonus_amount = bonus_apr
            is_bonus_period = True
            bonus_name = "April Bonus (75%)"
        elif period == 19:
            bonus_amount = bonus_sept
            is_bonus_period = True
            bonus_name = "Sept Bonus (25%)"
            
        # 2. Calculate Contributions (Base Salary)
        # Pre-Tax Base
        if ytd_pretax < LIMIT_PRETAX:
            pre_amt = current_gross * (base_pre_pct / 100)
            if ytd_pretax + pre_amt > LIMIT_PRETAX:
                pre_amt = LIMIT_PRETAX - ytd_pretax
        else:
            pre_amt = 0
            
        # Match Calculation (Per Pay Period Rule)
        # Employer matches 100% up to 6% of eligible comp this period
        eligible_match_base = min(current_gross * 0.06, current_gross)
        
        if ytd_match < LIMIT_MATCH:
            potential_match = min(pre_amt, eligible_match_base)
            match_amt = min(potential_match, LIMIT_MATCH - ytd_match)
        else:
            match_amt = 0
            
        # After-Tax Base (Mega Backdoor)
        # Logic: Fills space up to $72k total
        current_usage = (ytd_pretax + pre_amt) + (ytd_match + match_amt) + ytd_aftertax
        remaining_space = LIMIT_TOTAL - current_usage
        
        after_amt = 0
        if remaining_space > 0:
            after_amt = current_gross * (base_after_pct / 100)
            if after_amt > remaining_space:
                after_amt = remaining_space

        # 3. Calculate Contributions (Bonus)
        bonus_pre = 0
        bonus_after = 0
        bonus_match = 0
        
        if is_bonus_period:
            # Pre-Tax Bonus
            if ytd_pretax + pre_amt < LIMIT_PRETAX:
                bonus_pre = bonus_amount * (bonus_pre_pct / 100)
                # Hard stop at limit
                if ytd_pretax + pre_amt + bonus_pre > LIMIT_PRETAX:
                    bonus_pre = LIMIT_PRETAX - (ytd_pretax + pre_amt)
            
            # Match Bonus
            eligible_match_bonus = min(bonus_amount * 0.06, bonus_amount)
            if ytd_match + match_amt < LIMIT_MATCH:
                pot_bonus_match = min(bonus_pre, eligible_match_bonus)
                bonus_match = min(pot_bonus_match, LIMIT_MATCH - (ytd_match + match_amt))
            
            # After-Tax Bonus
            current_total_usage_bonus = (ytd_pretax + pre_amt + bonus_pre) + (ytd_match + match_amt + bonus_match) + (ytd_aftertax + after_amt)
            remaining_space_bonus = LIMIT_TOTAL - current_total_usage_bonus
            
            if remaining_space_bonus > 0:
                bonus_after = bonus_amount * (bonus_after_pct / 100)
                if bonus_after > remaining_space_bonus:
                    bonus_after = remaining_space_bonus

        # 4. Update YTD
        ytd_pretax += (pre_amt + bonus_pre)
        ytd_aftertax += (after_amt + bonus_after)
        ytd_match += (match_amt + bonus_match)
        ytd_gross += (current_gross + bonus_amount)
        
        # 5. Taxes & Deductions
        total_gross_period = current_gross + bonus_amount
        total_pretax_period = pre_amt + bonus_pre
        
        # ESPP (15% of Gross - Applies to Base AND Bonus)
        espp_deduction = total_gross_period * 0.15
        ytd_espp += espp_deduction
        
        # HSA (Fixed per check)
        hsa_deduction = 141.67
        
        # FICA - Social Security (Caps at 184.5k YTD)
        ss_tax = 0
        wage_base_prior = ytd_gross - total_gross_period
        if wage_base_prior < LIMIT_SS_WAGE_BASE:
            taxable_ss = min(total_gross_period, LIMIT_SS_WAGE_BASE - wage_base_prior)
            ss_tax = taxable_ss * RATE_FICA_SS
            
        # FICA - Medicare (No limit)
        med_tax = total_gross_period * RATE_FICA_MED
        
        # CA SDI (No limit in 2026, 1.3%)
        sdi_tax = total_gross_period * RATE_CA_SDI
        
        # Income Tax: Base Salary (Calculated on Taxable Income)
        # Taxable Income = Gross - PreTax - HSA (ESPP is post-tax)
        taxable_income_base = current_gross - pre_amt - hsa_deduction
        if taxable_income_base < 0: taxable_income_base = 0 # Safety
        fed_tax_base = taxable_income_base * TAX_RATE_FED_MARGINAL
        ca_tax_base = taxable_income_base * TAX_RATE_CA_MARGINAL
        
        # Income Tax: Bonus (Flat Rate on Taxable Portion)
        taxable_income_bonus = bonus_amount - bonus_pre
        if taxable_income_bonus < 0: taxable_income_bonus = 0
        fed_tax_bonus = taxable_income_bonus * TAX_RATE_BONUS_FED
        ca_tax_bonus = taxable_income_bonus * TAX_RATE_BONUS_CA
        
        total_taxes = ss_tax + med_tax + sdi_tax + fed_tax_base + ca_tax_base + fed_tax_bonus + ca_tax_bonus
        total_401k_deduction = total_pretax_period + after_amt + bonus_after
        
        # NET PAY calculation
        net_pay = total_gross_period - total_401k_deduction - hsa_deduction - espp_deduction - total_taxes
        
        # Backdoor Roth IRA Adjustment (Visual only, not payroll deduction)
        # If enabled, we subtract the monthly equivalent cost from the "Disposable" metric
        ira_monthly_cost = 0
        if include_ira_cost:
             ira_monthly_cost = LIMIT_IRA / 24 # Spread across 24 checks for budgeting view
        
        disposable_cash = net_pay - ira_monthly_cost
        
        data.append({
            "Period": period,
            "Gross": total_gross_period,
            "Net Paycheck": net_pay,
            "Disposable (After IRA)": disposable_cash,
            "Pre-Tax 401k": total_pretax_period,
            "After-Tax 401k": after_amt + bonus_after,
            "Match": match_amt + bonus_match,
            "ESPP": espp_deduction,
            "Type": bonus_name if is_bonus_period else "Standard"
        })

    # True Up Calculation (End of Year)
    total_eligible_match = min(ytd_gross * 0.06, LIMIT_MATCH)
    true_up_owed = total_eligible_match - ytd_match
    if true_up_owed < 0: true_up_owed = 0
    
    # FIXED RETURN STATEMENT HERE
    return pd.DataFrame(data), ytd_pretax, ytd_aftertax, ytd_match, true_up_owed, ytd_espp

# --- STREAMLIT UI ---
st.set_page_config(layout="wide", page_title="2026 Compensation Optimizer")

st.title("💸 2026 Income Optimizer (California Single Filer)")
st.markdown("""
**Base Salary**: $196,842.00
""")
st.markdown("""
**Bonus**: 15% ($29,526.30)
""")
st.markdown("""
**OTE**: $226,368.30
""")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("⚙️ Strategy Controls")
    
    st.subheader("Payroll Elections")
    base_pre = st.slider("Base Salary Pre-Tax %", 0, 15, 4, help="Set to 4% for steady cash flow, 13% for early max.")
    base_after = st.slider("Base Salary After-Tax %", 0, 30, 22, help="Mega Backdoor Roth contribution.")
    bonus_pre = st.slider("Bonus Pre-Tax %", 0, 90, 60, help="Don't exceed 60% or paycheck may go negative due to taxes/ESPP.")
    
    st.divider()
    st.subheader("Budgeting")
    include_ira = st.checkbox("Subtract Backdoor Roth IRA ($7,500) from Monthly Budget?", value=True, 
                              help="If checked, we reduce your displayed monthly cash flow by ~$625 to account for the manual IRA transfer.")

    st.info("""
    **Legend:**
    - **Pre-Tax:** 401(k) bucket (Max $24.5k)
    - **After-Tax:** Mega Backdoor bucket (Auto-convert to Roth)
    - **ESPP:** 15% Deduction (Forced Savings)
    """)

# Run Simulation
df, total_pre, total_after, total_match_paid, true_up, total_espp = calculate_year(base_pre, base_after, bonus_pre, 0, include_ira)

# Metrics
with col2:
    st.header("📊 Financial Outcome")
    
    # Filter for standard paychecks (exclude the 2 bonus periods for the 'Monthly' average)
    std_checks = df[df['Type'] == "Standard"]
    avg_monthly_cash = std_checks['Disposable (After IRA)'].mean() * 2
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg Monthly Cash", f"${avg_monthly_cash:,.0f}", delta="Spendable", help="Your 'Safe to Spend' budget (Base Pay - Savings - Bills)")
    m2.metric("Total Saved (Tax Adv)", f"${(total_pre + total_after + total_match_paid + true_up + LIMIT_IRA + LIMIT_HSA):,.0f}", "401k + Match + IRA + HSA")
    m3.metric("ESPP Saved", f"${total_espp:,.0f}", "15% Post-Tax")
    m4.metric("True-Up Payment", f"${true_up:,.0f}", "Paid Q1 2027")

    # Warnings
    if df['Net Paycheck'].min() < 0:
        st.error(f"⚠️ NEGATIVE PAYCHECK DETECTED! Period {df.loc[df['Net Paycheck'] < 0, 'Period'].iloc[0]}. Reduce Bonus Pre-Tax %.")
    
    # Graphs
    tab1, tab2 = st.tabs(["📈 Cash Flow", "🏦 Savings Buckets"])
    
    with tab1:
        st.caption("Green line = Actual Net Pay deposited. Red dotted line = Your 'Standard' month.")
        fig_cf = go.Figure()
        
        # Net Pay Line
        fig_cf.add_trace(go.Scatter(
            x=df['Period'], y=df['Net Paycheck'], 
            mode='lines+markers', name='Actual Deposit',
            line=dict(color='#00CC96', width=3),
            hovertemplate="Period %{x}<br>Net Pay: $%{y:,.2f}<extra></extra>"
        ))
        
        # Bonus Annotations
        bonus_periods = df[df['Type'] != "Standard"]
        for _, row in bonus_periods.iterrows():
            fig_cf.add_annotation(x=row['Period'], y=row['Net Paycheck'],
                                text=row['Type'], showarrow=True, arrowhead=1)

        fig_cf.update_layout(height=350, xaxis_title="Pay Period (1-24)", yaxis_title="Net Pay ($)")
        st.plotly_chart(fig_cf, use_container_width=True)

    with tab2:
        # Stacked Bar
        fig_bar = go.Figure(data=[
            go.Bar(name='Pre-Tax 401k', x=df['Period'], y=df['Pre-Tax 401k']),
            go.Bar(name='Match', x=df['Period'], y=df['Match']),
            go.Bar(name='After-Tax (Roth Conv)', x=df['Period'], y=df['After-Tax 401k']),
            go.Bar(name='ESPP', x=df['Period'], y=df['ESPP'], marker_color='#FFA15A')
        ])
        fig_bar.update_layout(barmode='stack', height=350, title="Where your Money Goes (Per Check)")
        st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("### 📝 Optimization Report")
col_summ1, col_summ2 = st.columns(2)
with col_summ1:
    st.write(f"**Total 401(k) Pre-Tax:** ${total_pre:,.2f} / ${LIMIT_PRETAX:,.0f}")
    st.write(f"**Total 401(k) After-Tax:** ${total_after:,.2f} (Roth Conversion)")
    st.write(f"**Total Match (2026):** ${total_match_paid:,.2f}")
with col_summ2:
    st.write(f"**Total ESPP Payouts:** ~${total_espp:,.2f} (Plus 15% discount profit)")
    st.write(f"**Backdoor Roth IRA:** ${LIMIT_IRA:,.0f} (Manual)")
    st.write(f"**HSA:** ${LIMIT_HSA:,.0f}")
    