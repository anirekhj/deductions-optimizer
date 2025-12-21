import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- PAGE CONFIG ---
st.set_page_config(layout="wide", page_title="Paycheck Optimizer")

# --- 50-STATE TAX DATA ENGINE (2025/2026 ESTIMATES) ---
# Sources: Tax Foundation, State Depts of Revenue (Projected Jan 1, 2025)
STATES = {
    "AL": {"Name": "Alabama", "Type": "Prog", "Brackets": [(500, 0.02), (3000, 0.04), (float('inf'), 0.05)], "StdDed": 3000, "SuppRate": 0.05},
    "AK": {"Name": "Alaska", "Type": "None", "SuppRate": 0.0},
    "AZ": {"Name": "Arizona", "Type": "Flat", "Rate": 0.025, "StdDed": 14600, "SuppRate": 0.025},
    "AR": {"Name": "Arkansas", "Type": "Prog", "Brackets": [(5100, 0.02), (float('inf'), 0.039)], "StdDed": 2340, "SuppRate": 0.039},
    "CA": {"Name": "California", "Type": "Prog", "Brackets": [(10756, 0.011), (25499, 0.022), (40245, 0.044), (55866, 0.066), (70606, 0.088), (360659, 0.1023)], "StdDed": 5540, "SuppRate": 0.1023, "ExtraTaxName": "CA SDI", "ExtraTaxRate": 0.012},
    "CO": {"Name": "Colorado", "Type": "Flat", "Rate": 0.0425, "StdDed": 15000, "SuppRate": 0.0425},
    "CT": {"Name": "Connecticut", "Type": "Prog", "Brackets": [(10000, 0.03), (50000, 0.05), (100000, 0.055), (200000, 0.06), (250000, 0.065), (500000, 0.069), (float('inf'), 0.0699)], "StdDed": 0, "SuppRate": 0.0699},
    "DE": {"Name": "Delaware", "Type": "Prog", "Brackets": [(2000, 0.0), (5000, 0.022), (10000, 0.039), (20000, 0.048), (25000, 0.052), (60000, 0.0555), (float('inf'), 0.066)], "StdDed": 3250, "SuppRate": 0.066},
    "DC": {"Name": "District of Columbia", "Type": "Prog", "Brackets": [(10000, 0.04), (40000, 0.06), (60000, 0.065), (250000, 0.085), (500000, 0.0925), (1000000, 0.0975)], "StdDed": 14600, "SuppRate": 0.0975},
    "FL": {"Name": "Florida", "Type": "None", "SuppRate": 0.0},
    "GA": {"Name": "Georgia", "Type": "Flat", "Rate": 0.0539, "StdDed": 12000, "SuppRate": 0.0539},
    "HI": {"Name": "Hawaii", "Type": "Prog", "Brackets": [(2400, 0.014), (4800, 0.032), (9600, 0.055), (14400, 0.064), (19200, 0.068), (24000, 0.072), (36000, 0.076), (48000, 0.079), (150000, 0.0825), (175000, 0.09), (200000, 0.10), (float('inf'), 0.11)], "StdDed": 2200, "SuppRate": 0.11},
    "ID": {"Name": "Idaho", "Type": "Flat", "Rate": 0.05695, "StdDed": 14600, "SuppRate": 0.05695},
    "IL": {"Name": "Illinois", "Type": "Flat", "Rate": 0.0495, "StdDed": 2775, "SuppRate": 0.0495},
    "IN": {"Name": "Indiana", "Type": "Flat", "Rate": 0.030, "StdDed": 1000, "SuppRate": 0.0305},
    "IA": {"Name": "Iowa", "Type": "Flat", "Rate": 0.038, "StdDed": 14600, "SuppRate": 0.038},
    "KS": {"Name": "Kansas", "Type": "Prog", "Brackets": [(15000, 0.031), (30000, 0.0525), (float('inf'), 0.057)], "StdDed": 3500, "SuppRate": 0.057},
    "KY": {"Name": "Kentucky", "Type": "Flat", "Rate": 0.04, "StdDed": 2980, "SuppRate": 0.04},
    "LA": {"Name": "Louisiana", "Type": "Flat", "Rate": 0.03, "StdDed": 4500, "SuppRate": 0.0425},
    "ME": {"Name": "Maine", "Type": "Prog", "Brackets": [(26050, 0.058), (61600, 0.0675), (float('inf'), 0.0715)], "StdDed": 14600, "SuppRate": 0.0715},
    "MD": {"Name": "Maryland", "Type": "Prog", "Brackets": [(1000, 0.02), (2000, 0.03), (3000, 0.04), (100000, 0.0475), (125000, 0.05), (150000, 0.0525), (250000, 0.055), (float('inf'), 0.0575)], "StdDed": 2550, "SuppRate": 0.0575},
    "MA": {"Name": "Massachusetts", "Type": "Flat", "Rate": 0.05, "StdDed": 4400, "SuppRate": 0.05, "ExtraTaxName": "MA PFML", "ExtraTaxRate": 0.0038},
    "MI": {"Name": "Michigan", "Type": "Flat", "Rate": 0.0425, "StdDed": 5900, "SuppRate": 0.0425},
    "MN": {"Name": "Minnesota", "Type": "Prog", "Brackets": [(30070, 0.0535), (98760, 0.068), (183340, 0.0785), (float('inf'), 0.0985)], "StdDed": 14600, "SuppRate": 0.0985},
    "MS": {"Name": "Mississippi", "Type": "Flat", "Rate": 0.044, "StdDed": 2300, "SuppRate": 0.047},
    "MO": {"Name": "Missouri", "Type": "Prog", "Brackets": [(1273, 0.015), (float('inf'), 0.047)], "StdDed": 14600, "SuppRate": 0.048},
    "MT": {"Name": "Montana", "Type": "Prog", "Brackets": [(float('inf'), 0.059)], "StdDed": 14600, "SuppRate": 0.059},
    "NE": {"Name": "Nebraska", "Type": "Prog", "Brackets": [(3700, 0.0246), (22130, 0.0351), (35730, 0.0501), (float('inf'), 0.0584)], "StdDed": 14600, "SuppRate": 0.0584},
    "NV": {"Name": "Nevada", "Type": "None", "SuppRate": 0.0},
    "NH": {"Name": "New Hampshire", "Type": "None", "SuppRate": 0.0},
    "NJ": {"Name": "New Jersey", "Type": "Prog", "Brackets": [(20000, 0.014), (35000, 0.0175), (40000, 0.035), (75000, 0.05525), (500000, 0.0637), (1000000, 0.0897), (float('inf'), 0.1075)], "StdDed": 1000, "SuppRate": 0.09, "ExtraTaxName": "NJ FLI/DI", "ExtraTaxRate": 0.004},
    "NM": {"Name": "New Mexico", "Type": "Prog", "Brackets": [(5500, 0.017), (11000, 0.032), (16000, 0.047), (float('inf'), 0.059)], "StdDed": 14600, "SuppRate": 0.059},
    "NY": {"Name": "New York", "Type": "Prog", "Brackets": [(8500, 0.04), (11700, 0.045), (13900, 0.0525), (80650, 0.0585), (215400, 0.0625), (1077550, 0.0685)], "StdDed": 8000, "SuppRate": 0.1170, "ExtraTaxName": "NY PFL", "ExtraTaxRate": 0.00388},
    "NC": {"Name": "North Carolina", "Type": "Flat", "Rate": 0.0425, "StdDed": 12750, "SuppRate": 0.0425},
    "ND": {"Name": "North Dakota", "Type": "Prog", "Brackets": [(44725, 0.011), (225975, 0.0204), (float('inf'), 0.025)], "StdDed": 14600, "SuppRate": 0.025},
    "OH": {"Name": "Ohio", "Type": "Prog", "Brackets": [(26050, 0.0), (100000, 0.0275), (float('inf'), 0.035)], "StdDed": 0, "SuppRate": 0.035},
    "OK": {"Name": "Oklahoma", "Type": "Prog", "Brackets": [(7200, 0.0375), (float('inf'), 0.0475)], "StdDed": 7350, "SuppRate": 0.0475},
    "OR": {"Name": "Oregon", "Type": "Prog", "Brackets": [(4050, 0.0475), (10200, 0.0675), (125000, 0.0875), (float('inf'), 0.099)], "StdDed": 2745, "SuppRate": 0.099, "ExtraTaxName": "OR Transit", "ExtraTaxRate": 0.001},
    "PA": {"Name": "Pennsylvania", "Type": "Flat", "Rate": 0.0307, "StdDed": 0, "SuppRate": 0.0307},
    "RI": {"Name": "Rhode Island", "Type": "Prog", "Brackets": [(74150, 0.0375), (168600, 0.0475), (float('inf'), 0.0599)], "StdDed": 14600, "SuppRate": 0.0599},
    "SC": {"Name": "South Carolina", "Type": "Prog", "Brackets": [(3460, 0.0), (17330, 0.03), (float('inf'), 0.063)], "StdDed": 14600, "SuppRate": 0.063},
    "SD": {"Name": "South Dakota", "Type": "None", "SuppRate": 0.0},
    "TN": {"Name": "Tennessee", "Type": "None", "SuppRate": 0.0},
    "TX": {"Name": "Texas", "Type": "None", "SuppRate": 0.0},
    "UT": {"Name": "Utah", "Type": "Flat", "Rate": 0.0455, "StdDed": 0, "SuppRate": 0.0455},
    "VT": {"Name": "Vermont", "Type": "Prog", "Brackets": [(45400, 0.0335), (110050, 0.066), (229550, 0.076), (float('inf'), 0.0875)], "StdDed": 7350, "SuppRate": 0.0875},
    "VA": {"Name": "Virginia", "Type": "Prog", "Brackets": [(3000, 0.02), (5000, 0.03), (17000, 0.05), (float('inf'), 0.0575)], "StdDed": 8500, "SuppRate": 0.0575},
    "WA": {"Name": "Washington", "Type": "None", "SuppRate": 0.0, "ExtraTaxName": "WA CARES", "ExtraTaxRate": 0.0058},
    "WV": {"Name": "West Virginia", "Type": "Prog", "Brackets": [(10000, 0.0236), (25000, 0.0315), (40000, 0.0354), (60000, 0.0472), (float('inf'), 0.0512)], "StdDed": 0, "SuppRate": 0.0512},
    "WI": {"Name": "Wisconsin", "Type": "Prog", "Brackets": [(14320, 0.035), (28640, 0.044), (315310, 0.053), (float('inf'), 0.0765)], "StdDed": 13810, "SuppRate": 0.0765},
    "WY": {"Name": "Wyoming", "Type": "None", "SuppRate": 0.0}
}

# --- FED DEFAULTS ---
FED_DATA = {
    2025: {
        "PRETAX": 23500, "TOTAL": 70000, "MATCH": 6000, "IRA": 7000, "ESPP": 21250, "HSA": 4300, 
        "SS_BASE": 176100, "STD_DED": 15000,
        "BRACKETS": [(11600, 0.10), (47150, 0.12), (100525, 0.22), (191950, 0.24), (243725, 0.32), (609350, 0.35), (float('inf'), 0.37)]
    },
    2026: {
        "PRETAX": 24500, "TOTAL": 72000, "MATCH": 6000, "IRA": 7500, "ESPP": 21250, "HSA": 4400, 
        "SS_BASE": 184500, "STD_DED": 15500,
        "BRACKETS": [(11925, 0.10), (48475, 0.12), (103350, 0.22), (197300, 0.24), (250525, 0.32), (626350, 0.35), (float('inf'), 0.37)]
    }
}

# --- SIDEBAR CONFIG ---
with st.sidebar:
    st.header("1. Location & Year")
    col1, col2 = st.columns(2)
    SEL_YEAR = col1.selectbox("Year", [2026, 2025])
    # Sort states by code
    sorted_states = sorted(STATES.keys())
    # Default to CA
    ca_index = sorted_states.index("CA")
    SEL_STATE = col2.selectbox("State", sorted_states, index=ca_index, format_func=lambda x: f"{x} - {STATES[x]['Name']}")
    
    # Load State Data
    STATE_INFO = STATES[SEL_STATE]
    FED_INFO = FED_DATA[SEL_YEAR]
    
    # Optional Local Tax Override
    LOCAL_TAX_RATE = st.number_input("Local/City Tax Rate % (e.g. NYC)", value=0.0, step=0.1, format="%.2f") / 100

    st.header("2. Income")
    BASE_SALARY = st.number_input("Base Salary ($)", value=196842.00, step=1000.00)
    BONUS_PCT = st.number_input("Bonus Target (%)", value=15.0, step=1.0)
    
    st.header("3. Limits")
    LIMIT_PRETAX = st.number_input("401(k) Pre-Tax", value=FED_INFO["PRETAX"], step=500)
    LIMIT_TOTAL = st.number_input("401(k) Total", value=FED_INFO["TOTAL"], step=500)
    LIMIT_MATCH = st.number_input("Match Cap", value=FED_INFO["MATCH"], step=500)
    LIMIT_ESPP = st.number_input("ESPP Cap", value=FED_INFO["ESPP"], step=250)
    LIMIT_HSA = st.number_input("HSA Limit", value=FED_INFO["HSA"], step=50)
    HSA_EMPLOYER = st.number_input("Employer HSA", value=1000, step=50)

# --- CALCULATOR FUNCTIONS ---
def calc_prog_tax(income, brackets, std_deduction):
    taxable = max(0, income - std_deduction)
    if not brackets: return 0
    tax = 0
    prev_thresh = 0
    for thresh, rate in brackets:
        if taxable > thresh:
            tax += (thresh - prev_thresh) * rate
            prev_thresh = thresh
        else:
            tax += (taxable - prev_thresh) * rate
            return tax
    # Top bracket
    tax += (taxable - prev_thresh) * brackets[-1][1]
    return tax

def get_state_tax_for_period(annual_taxable_base, bonus_taxable, is_bonus_period):
    # Base Tax (Annualized)
    annual_base_tax = 0
    if STATE_INFO["Type"] == "None":
        annual_base_tax = 0
    elif STATE_INFO["Type"] == "Flat":
        annual_base_tax = max(0, annual_taxable_base - STATE_INFO["StdDed"]) * STATE_INFO["Rate"]
    else: # Progressive
        annual_base_tax = calc_prog_tax(annual_taxable_base, STATE_INFO["Brackets"], STATE_INFO["StdDed"])
    
    # Per Period Base Tax
    period_base_tax = annual_base_tax / 24
    
    # Bonus Tax
    bonus_tax = 0
    if is_bonus_period:
        # Most states use flat supplemental rate for bonuses
        bonus_tax = bonus_taxable * STATE_INFO.get("SuppRate", 0)
        
    return period_base_tax + bonus_tax

def calculate_projection(base_pre, base_after, bonus_pre, include_ira):
    # Setup
    bonus_dollars = BASE_SALARY * (BONUS_PCT / 100)
    gross_per_check = BASE_SALARY / 24
    bonus_apr = bonus_dollars * 0.75
    bonus_sept = bonus_dollars * 0.25
    hsa_employee = max(0, LIMIT_HSA - HSA_EMPLOYER)
    hsa_per_check = hsa_employee / 24
    
    data = []
    ytd = {"pre": 0, "after": 0, "match": 0, "gross": 0, "espp": 0, "fica_gross": 0}
    
    for period in range(1, 25):
        # 1. Gross Setup
        cur_gross = gross_per_check
        is_bonus = False
        bonus_amt = 0
        lbl = ""
        
        if period == 8:
            bonus_amt = bonus_apr; is_bonus = True; lbl = "Apr Bonus"
        elif period == 19:
            bonus_amt = bonus_sept; is_bonus = True; lbl = "Sep Bonus"
            
        # 2. Contributions
        # Pre-Tax Base
        pre_amt = 0
        if ytd["pre"] < LIMIT_PRETAX:
            pre_amt = cur_gross * (base_pre / 100)
            if ytd["pre"] + pre_amt > LIMIT_PRETAX: pre_amt = LIMIT_PRETAX - ytd["pre"]
            
        # Match Base
        match_eligible = min(cur_gross * 0.06, cur_gross)
        match_amt = 0
        if ytd["match"] < LIMIT_MATCH:
            match_amt = min(pre_amt, match_eligible)
            match_amt = min(match_amt, LIMIT_MATCH - ytd["match"])
            
        # After-Tax Base
        after_amt = 0
        space = LIMIT_TOTAL - (ytd["pre"] + pre_amt + ytd["match"] + match_amt + ytd["after"])
        if space > 0:
            after_amt = cur_gross * (base_after / 100)
            if after_amt > space: after_amt = space
            
        # Bonus Logic
        bonus_pre_amt = 0; bonus_match_amt = 0; bonus_after_amt = 0
        if is_bonus:
            if ytd["pre"] + pre_amt < LIMIT_PRETAX:
                bonus_pre_amt = bonus_amt * (bonus_pre / 100)
                if ytd["pre"] + pre_amt + bonus_pre_amt > LIMIT_PRETAX:
                    bonus_pre_amt = LIMIT_PRETAX - (ytd["pre"] + pre_amt)
            
            b_match_eligible = min(bonus_amt * 0.06, bonus_amt)
            if ytd["match"] + match_amt < LIMIT_MATCH:
                bonus_match_amt = min(bonus_pre_amt, b_match_eligible)
                bonus_match_amt = min(bonus_match_amt, LIMIT_MATCH - (ytd["match"] + match_amt))
                
        # ESPP
        tot_gross = cur_gross + bonus_amt
        espp_pot = tot_gross * 0.15
        espp_ded = 0
        if ytd["espp"] < LIMIT_ESPP:
            room = LIMIT_ESPP - ytd["espp"]
            espp_ded = min(espp_pot, room)
            
        # 3. Taxes
        # FICA
        fica_basis = tot_gross - hsa_per_check
        ss_tax = 0
        if ytd["fica_gross"] < FED_INFO["SS_BASE"]:
            taxable = min(fica_basis, FED_INFO["SS_BASE"] - ytd["fica_gross"])
            ss_tax = taxable * 0.062
        med_tax = fica_basis * 0.0145
        
        # State Specific Other Taxes (SDI/PFL)
        state_other_tax = 0
        if "ExtraTaxRate" in STATE_INFO:
            state_other_tax = tot_gross * STATE_INFO["ExtraTaxRate"]
            
        # Income Taxes
        # Annualized Base
        taxable_base = max(0, cur_gross - pre_amt - hsa_per_check)
        annual_taxable = taxable_base * 24
        
        # Fed Tax
        fed_tax = calc_prog_tax(annual_taxable, FED_INFO["BRACKETS"], FED_INFO["STD_DED"]) / 24
        bonus_taxable = max(0, bonus_amt - bonus_pre_amt)
        fed_tax += (bonus_taxable * 0.22) # Flat bonus rate
        
        # State Tax
        state_tax = get_state_tax_for_period(annual_taxable, bonus_taxable, is_bonus)
        
        # Local Tax
        local_tax = (tot_gross - pre_amt - bonus_pre_amt - hsa_per_check) * LOCAL_TAX_RATE
        
        total_tax = ss_tax + med_tax + state_other_tax + fed_tax + state_tax + local_tax
        
        # Net Pay
        total_401k = pre_amt + bonus_pre_amt + after_amt + bonus_after_amt
        net_pay = tot_gross - total_401k - hsa_per_check - espp_ded - total_tax
        
        # Updates
        ytd["pre"] += (pre_amt + bonus_pre_amt)
        ytd["match"] += (match_amt + bonus_match_amt)
        ytd["after"] += (after_amt + bonus_after_amt)
        ytd["espp"] += espp_ded
        ytd["gross"] += tot_gross
        ytd["fica_gross"] += fica_basis
        
        # IRA Budgeting
        ira_cost = 0
        if include_ira: ira_cost = FED_INFO["IRA"] / 24
        disp = net_pay - ira_cost
        
        months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        m_idx = (period-1)//2
        p_label = f"{months[m_idx]}-{'A' if period%2!=0 else 'B'}"
        
        data.append({
            "Period": period, "Label": p_label, "Net Pay": net_pay, "Disposable": disp,
            "Taxes": total_tax, "401k": total_401k, "ESPP": espp_ded, "HSA": hsa_per_check,
            "Pre-Tax": pre_amt + bonus_pre_amt, "After-Tax": after_amt + bonus_after_amt,
            "Match": match_amt + bonus_match_amt, "Type": lbl if is_bonus else "Standard"
        })
        
    true_up = max(0, min(ytd["gross"]*0.06, LIMIT_MATCH) - ytd["match"])
    return pd.DataFrame(data), ytd, true_up

# --- UI ---
st.title(f"🇺🇸 50-State Income Optimizer ({SEL_YEAR})")

c1, c2 = st.columns([1, 2])
with c1:
    st.header("Strategy")
    b_pre = st.slider("Base Pre-Tax %", 0, 20, 4)
    b_aft = st.slider("Base After-Tax %", 0, 50, 22)
    bon_pre = st.slider("Bonus Pre-Tax %", 0, 90, 60)
    inc_ira = st.checkbox("Deduct IRA Budget", True)

df, ytd, true_up = calculate_projection(b_pre, b_aft, bon_pre, inc_ira)

with c2:
    st.header(f"Results for {STATE_INFO['Name']}")
    
    tot_save = ytd["pre"] + ytd["after"] + ytd["match"] + true_up + FED_INFO["IRA"] + LIMIT_HSA
    jan_sum = df.iloc[0]["Disposable"] + df.iloc[1]["Disposable"]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Monthly Spendable", f"${jan_sum:,.0f}")
    m2.metric("Total Saved", f"${tot_save:,.0f}")
    m3.metric("ESPP Total", f"${ytd['espp']:,.0f}")
    m4.metric("True-Up", f"${true_up:,.0f}")
    
    if df["Net Pay"].min() < 0: st.error("⚠️ Negative Paycheck Detected! Reduce Bonus Contribution.")
    
    t1, t2, t3 = st.tabs(["Cash Flow", "Buckets", "Breakdown"])
    
    with t1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df["Label"], y=df["Net Pay"], mode='lines+markers', name='Net', line=dict(color='#00CC96', width=3)))
        fig.add_hline(y=df.iloc[0]["Net Pay"], line_dash="dot", line_color="red", opacity=0.5)
        for _, r in df[df["Type"]!="Standard"].iterrows():
            fig.add_annotation(x=r["Label"], y=r["Net Pay"], text=r["Type"], showarrow=True, arrowhead=1, ay=-40)
        fig.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with t2:
        fig = go.Figure(data=[
            go.Bar(name='Pre', x=df['Label'], y=df['Pre-Tax']),
            go.Bar(name='Match', x=df['Label'], y=df['Match']),
            go.Bar(name='After', x=df['Label'], y=df['After-Tax']),
            go.Bar(name='ESPP', x=df['Label'], y=df['ESPP'], marker_color='#FFA15A')
        ])
        fig.update_layout(barmode='stack', height=350, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)
        
    with t3:
        fig = go.Figure(data=[
            go.Bar(name='Net', x=df['Label'], y=df['Net Pay'], marker_color='#00CC96'),
            go.Bar(name='Tax', x=df['Label'], y=df['Taxes'], marker_color='#EF553B'),
            go.Bar(name='401k', x=df['Label'], y=df['401k'], marker_color='#636EFA'),
            go.Bar(name='ESPP', x=df['Label'], y=df['ESPP'], marker_color='#FFA15A'),
            go.Bar(name='HSA', x=df['Label'], y=df['HSA'], marker_color='#AB63FA')
        ])
        fig.update_layout(barmode='stack', height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)