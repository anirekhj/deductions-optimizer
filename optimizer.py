import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Dynamic Compensation Optimizer")

# --- SIDEBAR: GLOBAL CONFIGURATION ---
with st.sidebar:
    st.header("1. Income Settings")
    BASE_SALARY = st.number_input("Base Salary ($)", value=196842.00, step=1000.00)
    BONUS_TARGET_PCT = st.number_input("Bonus Target (%)", value=15.0, step=1.0)
    
    # Calculate derived OTE for display
    bonus_total_calc = BASE_SALARY * (BONUS_TARGET_PCT / 100)
    ote_calc = BASE_SALARY + bonus_total_calc
    st.caption(f"**Implied Bonus:** ${bonus_total_calc:,.2f}")
    st.caption(f"**Implied OTE:** ${ote_calc:,.2f}")

    st.header("2. IRS & Plan Limits (Annual)")
    LIMIT_PRETAX = st.number_input("401(k) Pre-Tax Limit", value=24500, step=500)
    LIMIT_TOTAL = st.number_input("401(k) Total Limit (Pre+Match+After)", value=72000, step=500)
    LIMIT_MATCH_CAP = st.number_input("Employer Match Cap", value=6000, step=500)
    LIMIT_IRA = st.number_input("IRA Contribution Limit", value=7500, step=500)

    st.subheader("ESPP Limits")
    # IRS Rule: $25k Fair Market Value cap. 
    # With 15% discount, max contribution is $25,000 * 0.85 = $21,250.
    LIMIT_ESPP_CONTRIB = st.number_input("Max ESPP Contribution (IRS Cap)", value=21250, step=250, help="IRS limits purchases to $25k value. At 15% discount, you can only contribute ~$21,250.")
    
    st.subheader("HSA Settings")
    LIMIT_HSA_TOTAL = st.number_input("HSA Total Limit (Family/Self)", value=4400, step=50, help="Total IRS limit for the year")
    HSA_EMPLOYER_CONTRIB = st.number_input("HSA Employer Contribution", value=1000, step=50, help="Amount employer puts in (you don't pay this)")
    
    st.header("3. Tax Assumptions (Estimates)")
    TAX_RATE_FED_MARGINAL = st.number_input("Fed Marginal Rate", value=0.24, step=0.01)
    TAX_RATE_CA_MARGINAL = st.number_input("CA Marginal Rate", value=0.07, step=0.01)
    
    # Constants (Less likely to change)
    LIMIT_SS_WAGE_BASE = 184500  
    TAX_RATE_BONUS_FED = 0.22     
    TAX_RATE_BONUS_CA = 0.1023    
    RATE_FICA_SS = 0.062
    RATE_FICA_MED = 0.0145
    RATE_CA_SDI = 0.013 

def get_period_label(period_num):
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    # Period 1 -> Jan-A, Period 2 -> Jan-B
    month_idx = (period_num - 1) // 2
    suffix = "A" if period_num % 2 != 0 else "B"
    return f"{months[month_idx]}-{suffix}"

def calculate_year(base_pre_pct, base_after_pct, bonus_pre_pct, include_ira_cost, espp_limit):
    # --- INCOME CALCS ---
    # Recalculate based on sidebar inputs
    bonus_dollars = BASE_SALARY * (BONUS_TARGET_PCT / 100)
    
    pay_periods = 24
    gross_per_check = BASE_SALARY / pay_periods
    
    # Bonus Schedule (Assumed 75% / 25% split based on previous convo)
    bonus_apr = bonus_dollars * 0.75
    bonus_sept = bonus_dollars * 0.25
    
    # HSA Employee Cost
    hsa_employee_annual = max(0, LIMIT_HSA_TOTAL - HSA_EMPLOYER_CONTRIB)
    hsa_per_check = hsa_employee_annual / 24
    
    # Tracking Variables
    data = []
    ytd_pretax = 0
    ytd_aftertax = 0
    ytd_match = 0
    ytd_gross = 0
    ytd_espp = 0
    
    # Simulation Loop
    for period in range(1, 25):
        current_gross = gross_per_check
        is_bonus_period = False
        bonus_amount = 0
        bonus_name = ""
        
        # Inject Bonuses
        if period == 8: 
            bonus_amount = bonus_apr
            is_bonus_period = True
            bonus_name = "April Bonus (75%)"
        elif period == 19:
            bonus_amount = bonus_sept
            is_bonus_period = True
            bonus_name = "Sept Bonus (25%)"
            
        # --- CONTRIBUTIONS ---
        # 1. Base Pre-Tax
        if ytd_pretax < LIMIT_PRETAX:
            pre_amt = current_gross * (base_pre_pct / 100)
            if ytd_pretax + pre_amt > LIMIT_PRETAX:
                pre_amt = LIMIT_PRETAX - ytd_pretax
        else:
            pre_amt = 0
            
        # 2. Match Calculation
        eligible_match_base = min(current_gross * 0.06, current_gross)
        if ytd_match < LIMIT_MATCH_CAP:
            potential_match = min(pre_amt, eligible_match_base)
            match_amt = min(potential_match, LIMIT_MATCH_CAP - ytd_match)
        else:
            match_amt = 0
            
        # 3. Base After-Tax
        current_usage = (ytd_pretax + pre_amt) + (ytd_match + match_amt) + ytd_aftertax
        remaining_space = LIMIT_TOTAL - current_usage
        after_amt = 0
        if remaining_space > 0:
            after_amt = current_gross * (base_after_pct / 100)
            if after_amt > remaining_space:
                after_amt = remaining_space

        # 4. Bonus Contributions
        bonus_pre = 0
        bonus_after = 0
        bonus_match = 0
        
        if is_bonus_period:
            # Pre-Tax
            if ytd_pretax + pre_amt < LIMIT_PRETAX:
                bonus_pre = bonus_amount * (bonus_pre_pct / 100)
                if ytd_pretax + pre_amt + bonus_pre > LIMIT_PRETAX:
                    bonus_pre = LIMIT_PRETAX - (ytd_pretax + pre_amt)
            
            # Match
            eligible_match_bonus = min(bonus_amount * 0.06, bonus_amount)
            if ytd_match + match_amt < LIMIT_MATCH_CAP:
                pot_bonus_match = min(bonus_pre, eligible_match_bonus)
                bonus_match = min(pot_bonus_match, LIMIT_MATCH_CAP - (ytd_match + match_amt))
            
            # After-Tax (Kept at 0 for bonus based on strategy, but logic exists)
            current_total_usage_bonus = (ytd_pretax + pre_amt + bonus_pre) + (ytd_match + match_amt + bonus_match) + (ytd_aftertax + after_amt)
            remaining_space_bonus = LIMIT_TOTAL - current_total_usage_bonus
            if remaining_space_bonus > 0:
                bonus_after = 0 

        # Update YTD (Pre/Match/After)
        ytd_pretax += (pre_amt + bonus_pre)
        ytd_aftertax += (after_amt + bonus_after)
        ytd_match += (match_amt + bonus_match)
        ytd_gross += (current_gross + bonus_amount)
        
        # --- ESPP CALCULATION (WITH LIMIT) ---
        total_gross_period = current_gross + bonus_amount
        potential_espp = total_gross_period * 0.15 # Fixed 15% election
        
        espp_deduction = 0
        if ytd_espp < espp_limit:
            # Check how much room is left
            room_left = espp_limit - ytd_espp
            if potential_espp <= room_left:
                espp_deduction = potential_espp
            else:
                espp_deduction = room_left # Fill the rest, then stop
        
        ytd_espp += espp_deduction
        
        # Taxes & Deductions
        total_pretax_period = pre_amt + bonus_pre
        
        # FICA
        ss_tax = 0
        wage_base_prior = ytd_gross - total_gross_period
        if wage_base_prior < LIMIT_SS_WAGE_BASE:
            taxable_ss = min(total_gross_period, LIMIT_SS_WAGE_BASE - wage_base_prior)
            ss_tax = taxable_ss * RATE_FICA_SS
        med_tax = total_gross_period * RATE_FICA_MED
        sdi_tax = total_gross_period * RATE_CA_SDI
        
        # Income Taxes
        taxable_income_base = max(0, current_gross - pre_amt - hsa_per_check)
        fed_tax_base = taxable_income_base * TAX_RATE_FED_MARGINAL
        ca_tax_base = taxable_income_base * TAX_RATE_CA_MARGINAL
        
        taxable_income_bonus = max(0, bonus_amount - bonus_pre)
        fed_tax_bonus = taxable_income_bonus * TAX_RATE_BONUS_FED
        ca_tax_bonus = taxable_income_bonus * TAX_RATE_BONUS_CA
        
        total_taxes = ss_tax + med_tax + sdi_tax + fed_tax_base + ca_tax_base + fed_tax_bonus + ca_tax_bonus
        total_401k_deduction = total_pretax_period + after_amt + bonus_after
        
        net_pay = total_gross_period - total_401k_deduction - hsa_per_check - espp_deduction - total_taxes
        
        # Budgeting View
        ira_monthly_cost = 0
        if include_ira_cost:
             ira_monthly_cost = LIMIT_IRA / 24 
        disposable_cash = net_pay - ira_monthly_cost
        
        data.append({
            "Period": period,
            "Label": get_period_label(period),
            "Net Paycheck": net_pay,
            "Disposable (After IRA)": disposable_cash,
            "Pre-Tax 401k": total_pretax_period,
            "After-Tax 401k": after_amt + bonus_after,
            "Match": match_amt + bonus_match,
            "ESPP": espp_deduction,
            "Type": bonus_name if is_bonus_period else "Standard"
        })

    # True Up
    total_eligible_match = min(ytd_gross * 0.06, LIMIT_MATCH_CAP)
    true_up_owed = max(0, total_eligible_match - ytd_match)
    
    return pd.DataFrame(data), ytd_pretax, ytd_aftertax, ytd_match, true_up_owed, ytd_espp

# --- MAIN UI ---
st.title("💸 Dynamic Income Optimizer - California Single Filer")
st.markdown("Configure your **Income** and **Limits** in the Sidebar ←. Adjust your **Strategy** below ↓.")

col1, col2 = st.columns([1, 2])

with col1:
    st.header("Strategy Controls")
    
    st.subheader("Base Salary")
    base_pre = st.slider("Base Pre-Tax %", 0, 20, 4, help="Low % = Steady cash flow. High % = Early Max.")
    base_after = st.slider("Base After-Tax %", 0, 50, 22, help="Mega Backdoor. Fill the bucket!")
    
    st.subheader("Bonus")
    bonus_pre = st.slider("Bonus Pre-Tax %", 0, 90, 60, help="Shield tax by putting bonus into 401k.")
    
    st.divider()
    include_ira = st.checkbox("Deduct IRA from Monthly Budget", value=True, help="Subtracts manual IRA cost from displayed cash flow")

# Calculate
df, total_pre, total_after, total_match_paid, true_up, total_espp = calculate_year(
    base_pre, base_after, bonus_pre, include_ira, LIMIT_ESPP_CONTRIB
)

# Metrics
with col2:
    st.header("Financial Snapshot")
    
    # Total Saved Logic
    total_saved = total_pre + total_after + total_match_paid + true_up + LIMIT_IRA + LIMIT_HSA_TOTAL
    
    std_checks = df[df['Type'] == "Standard"]
    avg_cash = std_checks['Disposable (After IRA)'].mean() * 2
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly Spendable", f"${avg_cash:,.0f}", help="Avg Net Pay x2 (Standard months)")
    m2.metric("Total Saved", f"${total_saved:,.0f}", help="401k + Match + IRA + HSA")
    m3.metric("ESPP Accumulation", f"${total_espp:,.0f}", help="Cash value before gains")
    m4.metric("True-Up (Q1)", f"${true_up:,.0f}", help="Match paid next year")

    # Safety Check
    if df['Net Paycheck'].min() < 0:
        st.error(f"⚠️ NEGATIVE PAYCHECK DETECTED! Period {df.loc[df['Net Paycheck'] < 0, 'Label'].iloc[0]}. Lower your Bonus Pre-Tax %.")

    # Visuals
    tab1, tab2 = st.tabs(["📈 Cash Flow", "🏦 Savings Buckets"])
    
    with tab1:
        st.caption("Green Line = Actual Deposits. Red Dotted = 'Standard' Paycheck Baseline. Note the jump in Q4 when ESPP fills up.")
        fig_cf = go.Figure()
        
        # Main Line
        fig_cf.add_trace(go.Scatter(
            x=df['Label'], 
            y=df['Net Paycheck'], 
            mode='lines+markers', 
            name='Net Pay', 
            line=dict(color='#00CC96', width=3)
        ))
        
        # Baseline
        baseline = std_checks['Net Paycheck'].mean()
        fig_cf.add_hline(y=baseline, line_dash="dot", line_color="red", opacity=0.5, annotation_text="Standard Pay")
        
        # Bonus Annotations (Restored)
        bonus_rows = df[df['Type'] != "Standard"]
        for _, row in bonus_rows.iterrows():
            fig_cf.add_annotation(
                x=row['Label'], 
                y=row['Net Paycheck'],
                text=row['Type'], 
                showarrow=True, 
                arrowhead=1,
                ay=-40 # Shift arrow up slightly
            )

        fig_cf.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), xaxis_title="Pay Period")
        st.plotly_chart(fig_cf, use_container_width=True)
        
    with tab2:
        st.caption("Contributions per Pay Period")
        fig_bar = go.Figure(data=[
            go.Bar(name='Pre-Tax', x=df['Label'], y=df['Pre-Tax 401k']),
            go.Bar(name='Match', x=df['Label'], y=df['Match']),
            go.Bar(name='After-Tax', x=df['Label'], y=df['After-Tax 401k']),
            go.Bar(name='ESPP', x=df['Label'], y=df['ESPP'], marker_color='#FFA15A')
        ])
        fig_bar.update_layout(barmode='stack', height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_bar, use_container_width=True)

# Summary Text
st.markdown("### 📝 Analysis")
st.info(f"""
**Summary:** With **{base_pre}%** Base and **{bonus_pre}%** Bonus contributions:
- You fill **{(total_pre/LIMIT_PRETAX)*100:.1f}%** of your Pre-Tax Limit.
- You utilize **{((total_pre+total_after+LIMIT_MATCH_CAP)/LIMIT_TOTAL)*100:.1f}%** of your Total 401(k) space.
- You receive **${total_match_paid:,.0f}** match now 
- and **${true_up:,.0f}** later at year end as true up.
""")
