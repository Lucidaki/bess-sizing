"""
Hourly Operation Examples Page
Detailed hour-by-hour simulation tables for various dispatch scenarios
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Page config
st.set_page_config(page_title="Hourly Examples", page_icon="📊", layout="wide")

st.title("📊 Hourly Operation Examples")
st.markdown("""
This page provides detailed hour-by-hour simulation tables demonstrating various dispatch strategies.
Compare different DG operating modes and their impact on delivery and efficiency.
""")
st.markdown("---")

# Try to load the Excel data
excel_path = Path("extra/Dispatch_Simulation_Results.xlsx")


@st.cache_data
def load_scenario_data():
    """Load all scenario data from Excel file."""
    if not excel_path.exists():
        return None

    xlsx = pd.ExcelFile(excel_path)
    scenarios = {}
    for sheet in xlsx.sheet_names:
        scenarios[sheet] = pd.read_excel(xlsx, sheet_name=sheet)
    return scenarios


# Load data
scenarios = load_scenario_data()

if scenarios is None:
    st.error("Could not load scenario data from extra/Dispatch_Simulation_Results.xlsx")
    st.stop()

# Create tabs for different scenario groups
main_tab1, main_tab2, main_tab3 = st.tabs([
    "📋 All Dispatch Scenarios (2-Day Simulations)",
    "📈 Summary Comparison",
    "⚡ Dispatch & Charging Logic"
])

with main_tab1:
    st.markdown("## Dispatch Strategy Scenarios")

    st.info("""
    **Configuration:** 40 MWh BESS | 27 MW DG | 25 MW Load | SOC Limits: 10%-90%

    Each scenario demonstrates a different DG dispatch strategy over 2 days (48 hours).
    The solar profile varies between days to show system behavior under different conditions.
    """)

    # Create tabs for each scenario
    scenario_tabs = st.tabs([
        "T0: Solar+BESS",
        "T1: Green Priority",
        "T2: DG Night Charge",
        "T3: DG Blackout",
        "T4: DG Emergency",
        "T5: DG Day Charge",
        "T6: DG Night SoC"
    ])

    # Scenario descriptions
    scenario_info = {
        'T0_Solar_BESS': {
            'title': 'T0: Solar + BESS Only (No DG)',
            'description': '''
            **Strategy:** Pure renewable operation - no diesel generator backup.

            **When DG runs:** Never - system relies entirely on solar and battery.

            **Result:** High deficit during night hours when BESS depletes and no solar is available.
            This demonstrates why DG backup is critical for 24/7 operations.
            ''',
            'color_rule': 'deficit'
        },
        'T1_Green_Priority': {
            'title': 'T1: Green Priority (DG Always Available)',
            'description': '''
            **Strategy:** DG is always available as backup but solar+BESS is prioritized.

            **Merit Order:** Solar → BESS → DG

            **When DG runs:** Whenever solar+BESS cannot meet load (25 MW).

            **Result:** Zero deficit - 100% delivery achieved. DG fills all gaps.
            ''',
            'color_rule': 'dg_on'
        },
        'T2_DG_Night_Charge': {
            'title': 'T2: DG Night Charge (Night Hours Only)',
            'description': '''
            **Strategy:** DG runs only during night hours (18:00-06:00) to charge BESS.

            **When DG runs:** Night period only - serves load and charges battery.

            **Day operation:** Solar + BESS only (no DG support).

            **Result:** Deficit occurs during day when solar is insufficient and BESS depletes.
            ''',
            'color_rule': 'period'
        },
        'T3_DG_Blackout': {
            'title': 'T3: DG Blackout (Unavailable Periods)',
            'description': '''
            **Strategy:** DG is unavailable during blackout periods (simulating fuel shortage or maintenance).

            **Blackout hours:** 0-6 and 22-24 (early morning and late night).

            **When DG runs:** Only during "Normal" periods when available.

            **Result:** High deficit during blackout periods - system falls back to Solar+BESS only.
            ''',
            'color_rule': 'period'
        },
        'T4_DG_Emergency': {
            'title': 'T4: DG Emergency Recovery (SOC-Triggered)',
            'description': '''
            **Strategy:** DG starts in recovery mode when SOC drops critically low.

            **Trigger:** DG turns ON when BESS needs emergency recovery.

            **Operation:** Once triggered, DG charges BESS back to safe level before turning OFF.

            **Result:** Lower deficit than pure Solar+BESS, but some gaps remain.
            ''',
            'color_rule': 'dg_mode'
        },
        'T5_DG_Day_Charge': {
            'title': 'T5: DG Day Charge (Day Hours Only)',
            'description': '''
            **Strategy:** DG runs during day hours (06:00-18:00) to supplement solar charging.

            **When DG runs:** Day period only - helps charge BESS faster.

            **Night operation:** Solar + BESS only (no DG support).

            **Result:** Night deficits remain as BESS must carry the full night load alone.
            ''',
            'color_rule': 'period'
        },
        'T6_DG_Night_SoC': {
            'title': 'T6: DG Night + SOC Control',
            'description': '''
            **Strategy:** DG runs at night with SOC-based control to optimize charging.

            **When DG runs:** Night hours, modulated by battery SOC level.

            **Charging strategy:** DG charges BESS to target SOC for next day's operation.

            **Result:** Same as T2 - night charging provides buffer for daytime gaps.
            ''',
            'color_rule': 'period'
        }
    }

    sheet_names = ['T0_Solar_BESS', 'T1_Green_Priority', 'T2_DG_Night_Charge',
                   'T3_DG_Blackout', 'T4_DG_Emergency', 'T5_DG_Day_Charge', 'T6_DG_Night_SoC']

    for idx, (tab, sheet_name) in enumerate(zip(scenario_tabs, sheet_names)):
        with tab:
            info = scenario_info[sheet_name]
            st.markdown(f"### {info['title']}")
            st.markdown(info['description'])

            df = scenarios[sheet_name].copy()

            # Calculate summary metrics for this scenario
            total_deficit = df['Deficit_MW'].sum()
            dg_hours = (df['DG_MW'] > 0).sum()
            total_dg_energy = df['DG_MW'].sum()
            delivery_hours = (df['Deficit_MW'] == 0).sum()

            # Display metrics
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Delivery Hours", f"{delivery_hours}/48", f"{delivery_hours/48*100:.1f}%")
            col2.metric("Total Deficit", f"{total_deficit:.1f} MWh")
            col3.metric("DG Runtime", f"{dg_hours} hours")
            col4.metric("DG Energy", f"{total_dg_energy:.1f} MWh")

            st.markdown("---")

            # Styling function based on scenario type
            def style_row(row):
                styles = [''] * len(row)

                # Always highlight deficit rows in red
                if row['Deficit_MW'] > 0:
                    return ['background-color: #FFB6C1'] * len(row)

                # DG running in yellow
                if row['DG_MW'] > 0:
                    return ['background-color: #FFFACD'] * len(row)

                # BESS discharging in lavender
                if row['BESS_State'] == 'Discharging':
                    return ['background-color: #E6E6FA'] * len(row)

                # BESS charging in green
                if row['BESS_State'] == 'Charging':
                    return ['background-color: #90EE90'] * len(row)

                return styles

            # Select columns to display
            display_cols = ['Hour', 'Day', 'Solar_MW', 'DG_MW', 'BESS_Power_MW',
                          'BESS_Energy_MWh', 'SoC_%', 'BESS_State', 'Load_MW',
                          'Deficit_MW', 'Solar_to_Load_MW', 'BESS_to_Load_MW', 'DG_to_Load_MW']

            # Add Period column if it exists
            if 'Period' in df.columns:
                display_cols.insert(2, 'Period')
            if 'DG_Mode' in df.columns:
                display_cols.insert(3, 'DG_Mode')

            # Filter to available columns
            display_cols = [c for c in display_cols if c in df.columns]

            st.dataframe(
                df[display_cols].style.apply(style_row, axis=1),
                use_container_width=True,
                height=500
            )

            st.caption("""
            **Color Legend:**
            Pink = Deficit (delivery failed) | Yellow = DG Running | Lavender = BESS Discharging | Green = BESS Charging

            **BESS Power:** Positive = Discharging, Negative = Charging
            """)

            # Key events for this scenario
            st.markdown("#### Key Observations")

            # Find key events
            deficit_hours = df[df['Deficit_MW'] > 0]['Hour'].tolist()
            dg_start_hours = []
            for i in range(1, len(df)):
                if df.iloc[i]['DG_MW'] > 0 and df.iloc[i-1]['DG_MW'] == 0:
                    dg_start_hours.append(df.iloc[i]['Hour'])

            max_deficit_row = df.loc[df['Deficit_MW'].idxmax()]
            max_charge_row = df.loc[df['BESS_Power_MW'].idxmin()] if df['BESS_Power_MW'].min() < 0 else None

            obs_col1, obs_col2 = st.columns(2)

            with obs_col1:
                st.markdown("**Deficit Analysis:**")
                if total_deficit > 0:
                    st.markdown(f"- Total deficit: **{total_deficit:.1f} MWh** over {len(deficit_hours)} hours")
                    st.markdown(f"- Worst hour: Hour {int(max_deficit_row['Hour'])} Day {int(max_deficit_row['Day'])} ({max_deficit_row['Deficit_MW']:.1f} MW deficit)")
                    if len(deficit_hours) <= 10:
                        st.markdown(f"- Deficit hours: {deficit_hours}")
                else:
                    st.success("No deficit - 100% delivery achieved!")

            with obs_col2:
                st.markdown("**DG Analysis:**")
                if dg_hours > 0:
                    st.markdown(f"- DG ran for **{dg_hours} hours** ({dg_hours/48*100:.1f}% of time)")
                    st.markdown(f"- Total DG energy: **{total_dg_energy:.1f} MWh**")
                    if dg_start_hours:
                        st.markdown(f"- DG starts: {len(dg_start_hours)} times")
                else:
                    st.warning("DG never ran in this scenario")

with main_tab2:
    st.markdown("## Summary Comparison")

    # Load summary data
    summary_df = scenarios['Summary'].copy()

    st.markdown("### Performance Metrics by Scenario")

    # Enhance summary with calculated metrics
    summary_df['Delivery_Rate_%'] = ((48 * 25 - summary_df['Total_Deficit_MWh']) / (48 * 25) * 100).round(1)
    summary_df['DG_Utilization_%'] = (summary_df['DG_Hours'] / 48 * 100).round(1)

    # Reorder columns
    summary_display = summary_df[['Template', 'Total_Deficit_MWh', 'Delivery_Rate_%',
                                   'DG_Hours', 'DG_Utilization_%', 'Total_DG_MWh']]
    summary_display.columns = ['Scenario', 'Total Deficit (MWh)', 'Delivery Rate (%)',
                               'DG Hours', 'DG Utilization (%)', 'DG Energy (MWh)']

    st.dataframe(summary_display, use_container_width=True, hide_index=True)

    st.markdown("---")

    # Visual comparison
    st.markdown("### Visual Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Deficit vs DG Runtime")
        chart_df = summary_df[['Template', 'Total_Deficit_MWh', 'DG_Hours']].copy()
        chart_df.columns = ['Scenario', 'Deficit (MWh)', 'DG Hours']
        chart_df = chart_df.set_index('Scenario')
        st.bar_chart(chart_df)

    with col2:
        st.markdown("#### Delivery Rate by Scenario")
        rate_df = summary_df[['Template', 'Delivery_Rate_%']].copy()
        rate_df.columns = ['Scenario', 'Delivery Rate (%)']
        rate_df = rate_df.set_index('Scenario')
        st.bar_chart(rate_df)

    st.markdown("---")

    # Recommendations
    st.markdown("### Strategy Recommendations")

    rec_col1, rec_col2, rec_col3 = st.columns(3)

    with rec_col1:
        st.markdown("#### Best for 100% Delivery")
        st.success("""
        **T1: Green Priority**
        - Zero deficit
        - DG as always-available backup
        - Highest fuel consumption
        """)

    with rec_col2:
        st.markdown("#### Best Fuel Efficiency")
        st.info("""
        **T5: DG Day Charge**
        - Only 11 DG hours
        - 121.5 MWh DG energy
        - But 557.5 MWh deficit
        """)

    with rec_col3:
        st.markdown("#### Balanced Approach")
        st.warning("""
        **T2/T6: Night Charging**
        - 23 DG hours
        - 133.8 MWh deficit
        - Good balance of fuel vs delivery
        """)

    st.markdown("---")

    st.markdown("### Key Insights")

    st.markdown("""
    | Finding | Implication |
    |---------|-------------|
    | **T0 has 730 MWh deficit** | Pure Solar+BESS cannot provide 24/7 power with this configuration |
    | **T1 achieves 0 deficit** | DG-always-available ensures 100% delivery but uses most fuel |
    | **T2 = T6 performance** | Night charging strategies yield identical results |
    | **T3 Blackout impact** | DG unavailability during critical hours causes 376 MWh deficit |
    | **T5 Day Charge** | Charging during day leaves nights exposed - worst DG strategy |
    """)

    st.markdown("---")

    # Configuration reference
    st.markdown("### Configuration Reference")

    config_col1, config_col2, config_col3 = st.columns(3)

    with config_col1:
        st.markdown("#### BESS Parameters")
        st.code("""
Capacity: 40 MWh
Min SOC: 10%
Max SOC: 90%
Usable: 32 MWh
Max Power: 10 MW
        """, language='text')

    with config_col2:
        st.markdown("#### DG Parameters")
        st.code("""
Capacity: 27 MW
Operation: Full capacity when ON
Excess: Charges BESS
        """, language='text')

    with config_col3:
        st.markdown("#### Load Parameters")
        st.code("""
Load: 25 MW (constant)
Duration: 48 hours (2 days)
Total Energy: 1,200 MWh
        """, language='text')

with main_tab3:
    st.markdown("## Dispatch & Charging Logic")

    st.markdown("""
    This section explains the core logic governing how power flows between Solar, BESS, DG, and Load
    in the simulation scenarios shown in this page.
    """)

    st.markdown("---")

    # Merit Order Dispatch
    st.markdown("### Merit Order Dispatch (Load Serving)")

    st.info("""
    **Priority Order for Serving Load:**
    1. **Solar** (highest priority - free, zero emissions)
    2. **DG** (when running - serves load before BESS to preserve battery)
    3. **BESS** (last resort - discharge only if Solar + DG insufficient)
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Dispatch Flow Diagram")
        st.code("""
    Load Requirement: 25 MW
           |
           v
    +------------------+
    |  1. SOLAR        |
    |  (Direct to Load)|
    +------------------+
           |
           | Remaining Load?
           v
    +------------------+
    |  2. DG           |
    |  (If Running)    |
    +------------------+
           |
           | Still Remaining?
           v
    +------------------+
    |  3. BESS         |
    |  (Discharge)     |
    +------------------+
           |
           | Any Deficit?
           v
    [Delivery Failed]
        """, language='text')

    with col2:
        st.markdown("#### Dispatch Logic Code")
        st.code("""
remaining_load = 25  # MW

# Step 1: Solar to Load (always first)
solar_to_load = min(solar_mw, remaining_load)
remaining_load -= solar_to_load

# Step 2: DG to Load (if DG is ON)
if dg.state == 'ON':
    dg_output = dg.capacity  # Full capacity
    dg_to_load = min(dg_output, remaining_load)
    remaining_load -= dg_to_load

# Step 3: BESS to Load (last resort)
if remaining_load > 0:
    bess_to_load = battery.discharge(remaining_load)
    remaining_load -= bess_to_load

# Check delivery
if remaining_load <= 0.001:
    delivery = 'Yes'
else:
    delivery = 'No'
    deficit = remaining_load
        """, language='python')

    st.markdown("---")

    # Charging Logic
    st.markdown("### BESS Charging Logic")

    st.warning("""
    **Charging Priority Order:**
    1. **Excess Solar** (after load is served) - highest priority
    2. **Excess DG** (when DG output exceeds load) - secondary source

    **Key Rule:** BESS charges ONLY from Solar and DG - never from grid!
    """)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("#### Charging Flow Diagram")
        st.code("""
    After Load is Served:
           |
           v
    +----------------------+
    |  Excess Solar?       |
    |  (Solar - Load > 0)  |
    +----------------------+
           |
           | Yes
           v
    +----------------------+
    |  Charge BESS from    |
    |  Excess Solar        |
    +----------------------+
           |
           v
    +----------------------+
    |  Excess DG?          |
    |  (DG - DG_to_Load)   |
    +----------------------+
           |
           | Yes
           v
    +----------------------+
    |  Charge BESS from    |
    |  Excess DG           |
    +----------------------+
           |
           v
    [Any remaining excess
     is wasted/curtailed]
        """, language='text')

    with col4:
        st.markdown("#### Charging Logic Code")
        st.code("""
# After load dispatch...
excess_solar = solar_mw - solar_to_load
excess_dg = dg_output - dg_to_load

# Priority 1: Charge from excess solar
if excess_solar > 0:
    headroom = battery.get_charge_headroom()
    if headroom > 0:
        # Apply efficiency: 93.3% one-way
        charged = battery.charge(excess_solar)
        solar_charged += charged

# Priority 2: Charge from excess DG
if excess_dg > 0:
    headroom = battery.get_charge_headroom()
    if headroom > 0:
        charged = battery.charge(excess_dg)
        dg_to_bess += charged

# Wastage: Excess that couldn't be stored
solar_wasted = excess_solar - solar_charged
        """, language='python')

    st.markdown("---")

    # DG Control Logic
    st.markdown("### DG Control Strategies")

    st.markdown("""
    Different DG control strategies determine **when** the diesel generator runs.
    Each strategy has trade-offs between delivery reliability and fuel consumption.
    """)

    dg_col1, dg_col2 = st.columns(2)

    with dg_col1:
        st.markdown("#### SOC-Triggered (Hysteresis)")
        st.code("""
DG Hysteresis Control:
- Turn ON when: SOC <= 20%
- Turn OFF when: SOC >= 80%

This prevents frequent on/off cycling
by using different thresholds.

Timeline Example:
Hour 0: SOC=50%, DG=OFF
Hour 5: SOC=22%, DG=OFF (not yet <= 20%)
Hour 6: SOC=18%, DG=ON  (triggered!)
Hour 7: SOC=35%, DG=ON  (stays on)
Hour 10: SOC=78%, DG=ON (not yet >= 80%)
Hour 11: SOC=82%, DG=OFF (turned off)
        """, language='text')

        st.code("""
def update_dg_state(battery_soc):
    if dg.state == 'OFF':
        if battery_soc <= SOC_ON_THRESHOLD:
            dg.state = 'ON'
    elif dg.state == 'ON':
        if battery_soc >= SOC_OFF_THRESHOLD:
            dg.state = 'OFF'
        """, language='python')

    with dg_col2:
        st.markdown("#### Time-Based Strategies")
        st.code("""
Night Charge (T2, T6):
- DG runs: 18:00 - 06:00
- Purpose: Charge BESS for next day
- Day operation: Solar + BESS only

Day Charge (T5):
- DG runs: 06:00 - 18:00
- Purpose: Supplement solar charging
- Night operation: BESS only (risky!)

Blackout Periods (T3):
- DG unavailable: 00:00-06:00, 22:00-24:00
- Simulates: Fuel shortage, maintenance
- Result: Higher deficit during blackouts
        """, language='text')

        st.code("""
def get_dg_availability(hour):
    hour_of_day = hour % 24

    # Night Charge strategy
    if strategy == 'night_charge':
        return hour_of_day >= 18 or hour_of_day < 6

    # Day Charge strategy
    if strategy == 'day_charge':
        return 6 <= hour_of_day < 18

    # Green Priority (always available)
    return True
        """, language='python')

    st.markdown("---")

    # Energy Flow Summary
    st.markdown("### Complete Energy Flow Summary")

    st.code("""
    HOURLY SIMULATION LOOP
    ======================

    For each hour:

    1. UPDATE DG STATE (before dispatch)
       - Check SOC thresholds
       - Check time-based availability
       - Update DG ON/OFF status

    2. DISPATCH TO LOAD (merit order)
       Solar --> DG --> BESS --> [Deficit]
       |        |       |
       v        v       v
       Load    Load    Load

    3. CHARGE BESS (from excess)
       Excess Solar --> BESS
       Excess DG -----> BESS
       (Apply 93.3% efficiency)

    4. TRACK METRICS
       - Delivery success/failure
       - SOC after operations
       - Energy flows (kWh/MWh)
       - Wastage (curtailed solar)

    5. ADVANCE TO NEXT HOUR
    """, language='text')

    st.markdown("---")

    # Efficiency Calculations
    st.markdown("### Efficiency Calculations")

    eff_col1, eff_col2 = st.columns(2)

    with eff_col1:
        st.markdown("#### Round-Trip Efficiency")
        st.latex(r"\eta_{RT} = 87\%")
        st.latex(r"\eta_{one-way} = \sqrt{0.87} = 93.3\%")

        st.markdown("""
        **Charging:** Energy stored = Input × 0.933

        **Discharging:** Energy delivered = Stored × 0.933

        **Combined:** Round-trip = 0.933 × 0.933 = 87%
        """)

    with eff_col2:
        st.markdown("#### Example Calculation")
        st.code("""
# Charging 10 MW for 1 hour
input_energy = 10  # MWh (AC)
stored_energy = 10 * 0.933 = 9.33 MWh (DC)

# Discharging to deliver 10 MW
required_from_battery = 10 / 0.933 = 10.72 MWh
actual_delivered = 10 MWh (AC)

# SOC Impact (40 MWh battery)
delta_soc_charge = 9.33 / 40 = 23.3%
delta_soc_discharge = 10.72 / 40 = 26.8%
        """, language='python')

    st.markdown("---")

    # Column definitions
    st.markdown("### Data Column Definitions")

    st.markdown("""
    | Column | Description | Units |
    |--------|-------------|-------|
    | **Hour** | Simulation hour (0-47 for 2 days) | - |
    | **Day** | Day number (1 or 2) | - |
    | **Solar_MW** | Solar PV generation | MW |
    | **DG_MW** | Diesel generator output (0 or 27) | MW |
    | **BESS_Power_MW** | Battery power (+discharge, -charge) | MW |
    | **BESS_Energy_MWh** | Battery energy content | MWh |
    | **SoC_%** | State of Charge | % |
    | **BESS_State** | Charging / Discharging / Idle | - |
    | **Load_MW** | Load requirement (always 25) | MW |
    | **Deficit_MW** | Unmet load (0 = delivery success) | MW |
    | **Solar_to_Load_MW** | Solar power serving load | MW |
    | **BESS_to_Load_MW** | Battery power serving load | MW |
    | **DG_to_Load_MW** | DG power serving load | MW |
    | **Period** | Time period (Day/Night/Blackout) | - |
    | **DG_Mode** | DG operating mode (Normal/Emergency) | - |
    """)
