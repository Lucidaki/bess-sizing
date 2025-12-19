"""
Quick Analysis: Combined Rules + Configuration + Analysis

Alternative to the 5-step wizard flow. Allows users to:
1. Configure dispatch rules
2. Select a single BESS/Duration/DG configuration
3. Run full year simulation
4. Explore results by date range
"""

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import date, timedelta

# Add parent directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.wizard_state import (
    init_wizard_state, get_wizard_state, update_wizard_state,
    can_navigate_to_step, get_step_status
)
from src.template_inference import (
    infer_template, get_template_info, get_valid_triggers_for_timing
)


# =============================================================================
# PAGE CONFIG
# =============================================================================

st.set_page_config(
    page_title="BESS Sizing - Quick Analysis",
    page_icon="⚡",
    layout="wide"
)

# Initialize wizard state
init_wizard_state()

# Check if Step 1 completed
if not can_navigate_to_step(2):
    st.warning("Please complete Step 1 (Setup) first.")
    if st.button("Go to Step 1"):
        st.switch_page("pages/8_🚀_Step1_Setup.py")
    st.stop()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def render_template_card(template_id: int, dg_charges_bess: bool = False, dg_load_priority: str = 'bess_first'):
    """Render an informational card showing the inferred template."""
    info = get_template_info(template_id)

    if not info['dg_enabled']:
        border_color = "#2ecc71"
        icon = "☀️"
    else:
        border_color = "#3498db"
        icon = "⚡"

    if not info['dg_enabled']:
        merit_order = info['merit_order']
    elif dg_load_priority == 'dg_first':
        merit_order = "Solar → DG → BESS → Unserved"
        if dg_charges_bess:
            merit_order += " + DG→Battery"
    else:
        merit_order = "Solar → BESS → DG → Unserved"
        if dg_charges_bess:
            merit_order += " + DG→Battery"

    description = info['description']
    if info['dg_enabled']:
        if dg_charges_bess:
            description += " (Excess DG charges battery)"
        else:
            description += " (Battery charges from solar only)"

    st.markdown(f"""
    <div style="
        border: 2px solid {border_color};
        border-radius: 10px;
        padding: 15px;
        background-color: rgba(255,255,255,0.05);
    ">
        <h4 style="margin: 0;">{icon} {info['name']}</h4>
        <p style="color: #888; margin: 5px 0;">{merit_order}</p>
        <p style="margin: 5px 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)


def date_to_hour_index(selected_date, base_year=2024):
    """Convert date to hour index in simulation."""
    base_date = date(base_year, 1, 1)
    days_since_start = (selected_date - base_date).days
    return days_since_start * 24


def create_dispatch_graph(hourly_df: pd.DataFrame, load_mw: float, bess_capacity: float = 100,
                          soc_on: float = 30, soc_off: float = 80) -> go.Figure:
    """Create dispatch visualization with dual y-axis."""
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    hours = list(range(len(hourly_df)))

    # Solar (orange area fill)
    fig.add_trace(go.Scatter(
        x=hours, y=hourly_df['solar_mw'].values,
        name='Solar', fill='tozeroy',
        line=dict(color='#FFA500', width=2),
        fillcolor='rgba(255,165,0,0.3)',
        hovertemplate='Hour %{x}<br>Solar: %{y:.1f} MW<extra></extra>'
    ), secondary_y=False)

    # DG Output (red fill)
    if 'dg_output_mw' in hourly_df.columns and hourly_df['dg_output_mw'].sum() > 0:
        fig.add_trace(go.Scatter(
            x=hours, y=hourly_df['dg_output_mw'].values,
            name='DG Output', fill='tozeroy',
            line=dict(color='#DC143C', width=2, shape='hv'),
            fillcolor='rgba(220,20,60,0.3)',
            hovertemplate='Hour %{x}<br>DG: %{y:.1f} MW<extra></extra>'
        ), secondary_y=False)

    # BESS Power (blue line)
    if 'bess_mw' in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=hours, y=hourly_df['bess_mw'].values,
            name='BESS Power',
            line=dict(color='#1f77b4', width=2, shape='hv'),
            hovertemplate='Hour %{x}<br>BESS: %{y:.1f} MW<extra></extra>'
        ), secondary_y=False)

    # SOC % (green dotted on secondary axis)
    if 'soc_percent' in hourly_df.columns:
        fig.add_trace(go.Scatter(
            x=hours, y=hourly_df['soc_percent'].values,
            name='SOC %',
            line=dict(color='#2E8B57', width=2, dash='dot', shape='hv'),
            hovertemplate='Hour %{x}<br>SOC: %{y:.1f}%<extra></extra>'
        ), secondary_y=True)

    # BESS Energy (MWh)
    if 'soc_percent' in hourly_df.columns:
        bess_energy = hourly_df['soc_percent'].values * bess_capacity / 100
        fig.add_trace(go.Scatter(
            x=hours, y=bess_energy,
            name='BESS Energy (MWh)',
            line=dict(color='#4169E1', width=2, dash='dash', shape='hv'),
            hovertemplate='Hour %{x}<br>Energy: %{y:.1f} MWh<extra></extra>'
        ), secondary_y=True)

    # Delivery (purple line)
    delivery_values = [load_mw if d == 'Yes' else 0 for d in hourly_df['delivery'].values]
    fig.add_trace(go.Scatter(
        x=hours, y=delivery_values,
        name='Delivery',
        line=dict(color='purple', width=3, shape='hv'),
        hovertemplate='Hour %{x}<br>Delivery: %{y:.0f} MW<extra></extra>'
    ), secondary_y=False)

    # Reference lines
    fig.add_hline(y=load_mw, line_dash="dash", line_color="gray",
                  annotation_text=f"Load {load_mw:.0f} MW", secondary_y=False)
    fig.add_hline(y=0, line_color="lightgray", line_width=1, secondary_y=False)
    fig.add_hline(y=soc_on, line_dash="dot", line_color="red",
                  annotation_text=f"DG ON ({soc_on:.0f}%)", secondary_y=True)
    fig.add_hline(y=soc_off, line_dash="dot", line_color="green",
                  annotation_text=f"DG OFF ({soc_off:.0f}%)", secondary_y=True)

    # Day boundary markers
    num_days = len(hours) // 24
    for day in range(1, num_days + 1):
        fig.add_vline(x=day * 24, line_dash="dash", line_color="black", line_width=1,
                      annotation_text=f"Day {day + 1}", annotation_position="top")

    fig.update_layout(
        height=450,
        title="Hourly Dispatch Visualization",
        xaxis_title="Hour",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(l=50, r=50, t=80, b=50),
        xaxis=dict(showgrid=True, dtick=6)
    )
    fig.update_yaxes(title_text="Power (MW)", secondary_y=False)
    fig.update_yaxes(title_text="SOC (%) / Energy (MWh)", secondary_y=True, range=[0, 100])

    return fig


def style_hourly_row(row):
    """Color-code rows based on state."""
    if 'Unmet (MW)' in row.index and row['Unmet (MW)'] > 0:
        return ['background-color: #FFB6C1'] * len(row)
    if 'DG (MW)' in row.index and row['DG (MW)'] > 0:
        return ['background-color: #FFFACD'] * len(row)
    if 'BESS State' in row.index:
        if row['BESS State'] == 'Discharging':
            return ['background-color: #E6E6FA'] * len(row)
        if row['BESS State'] == 'Charging':
            return ['background-color: #90EE90'] * len(row)
    return [''] * len(row)


def run_simulation(bess_mwh, duration, dg_mw, template_id, setup, rules, solar_profile, load_profile):
    """Run simulation for full year and return hourly data."""
    from src.dispatch_engine import SimulationParams, run_simulation as dispatch_run

    power_mw = bess_mwh / duration

    params = SimulationParams(
        load_profile=load_profile if isinstance(load_profile, list) else load_profile.tolist(),
        solar_profile=solar_profile if isinstance(solar_profile, list) else solar_profile.tolist(),
        bess_capacity=bess_mwh,
        bess_charge_power=power_mw,
        bess_discharge_power=power_mw,
        bess_efficiency=setup['bess_efficiency'],
        bess_min_soc=setup['bess_min_soc'],
        bess_max_soc=setup['bess_max_soc'],
        bess_initial_soc=setup['bess_initial_soc'],
        bess_daily_cycle_limit=setup['bess_daily_cycle_limit'],
        bess_enforce_cycle_limit=setup['bess_enforce_cycle_limit'],
        dg_enabled=setup['dg_enabled'],
        dg_capacity=dg_mw,
        dg_charges_bess=rules.get('dg_charges_bess', False),
        dg_load_priority=rules.get('dg_load_priority', 'bess_first'),
        night_start_hour=rules.get('night_start', 18),
        night_end_hour=rules.get('night_end', 6),
        day_start_hour=rules.get('day_start', 6),
        day_end_hour=rules.get('day_end', 18),
        blackout_start_hour=rules.get('blackout_start', 22),
        blackout_end_hour=rules.get('blackout_end', 6),
        dg_soc_on_threshold=rules.get('soc_on_threshold', 30),
        dg_soc_off_threshold=rules.get('soc_off_threshold', 80),
    )

    hourly_results = dispatch_run(params, template_id, num_hours=8760)
    return hourly_results


def convert_results_to_dataframe(hourly_results):
    """Convert hourly results to DataFrame."""
    return pd.DataFrame([{
        'hour': h.t,
        'day': h.day,
        'hour_of_day': h.hour_of_day,
        'solar_mw': h.solar,
        'load_mw': h.load,
        'bess_mw': h.bess_power,
        'soc_percent': h.soc_pct,
        'bess_state': h.bess_state,
        'dg_output_mw': h.dg_to_load + h.dg_to_bess + h.dg_curtailed,
        'dg_state': 'ON' if h.dg_running else 'OFF',
        'solar_to_load': h.solar_to_load,
        'dg_to_load': h.dg_to_load,
        'dg_to_bess': h.dg_to_bess,
        'dg_curtailed': h.dg_curtailed,
        'bess_to_load': h.bess_to_load,
        'unmet_mw': h.unserved,
        'delivery': 'Yes' if h.unserved == 0 else 'No',
        'solar_curtailed': h.solar_curtailed,
    } for h in hourly_results])


# =============================================================================
# MAIN PAGE
# =============================================================================

st.title("⚡ Quick Analysis")
st.markdown("Configure dispatch rules, select a configuration, and analyze results - all in one page.")

st.divider()

# Get current state
state = get_wizard_state()
setup = state['setup']
rules = state['rules']

dg_enabled = setup['dg_enabled']


# =============================================================================
# SECTION 1: DISPATCH RULES
# =============================================================================

st.header("1️⃣ Dispatch Rules")

if not dg_enabled:
    st.info("Your system has no generator. The dispatch strategy is **Solar + BESS Only**.")
    render_template_card(0)
    template_id = 0
    dg_charges_bess = False
    dg_load_priority = 'bess_first'
else:
    col_rules1, col_rules2 = st.columns(2)

    with col_rules1:
        # Question 1: DG Timing
        st.markdown("**When can the generator run?**")
        dg_timing_options = {
            'anytime': "Anytime (no restrictions)",
            'day_only': "Day only (nights must be silent)",
            'night_only': "Night only (days must be green)",
            'custom_blackout': "Custom blackout window",
        }
        dg_timing = st.radio(
            "DG timing:",
            options=list(dg_timing_options.keys()),
            format_func=lambda x: dg_timing_options[x],
            index=list(dg_timing_options.keys()).index(rules.get('dg_timing', 'anytime')),
            key='qa_dg_timing',
            label_visibility="collapsed"
        )
        update_wizard_state('rules', 'dg_timing', dg_timing)

        # Time window settings
        if dg_timing == 'day_only':
            tc1, tc2 = st.columns(2)
            with tc1:
                day_start = st.slider("Day starts", 0, 23, rules.get('day_start', 6), key='qa_day_start')
                update_wizard_state('rules', 'day_start', day_start)
            with tc2:
                day_end = st.slider("Day ends", 0, 23, rules.get('day_end', 18), key='qa_day_end')
                update_wizard_state('rules', 'day_end', day_end)
        elif dg_timing == 'night_only':
            tc1, tc2 = st.columns(2)
            with tc1:
                night_start = st.slider("Night starts", 0, 23, rules.get('night_start', 18), key='qa_night_start')
                update_wizard_state('rules', 'night_start', night_start)
            with tc2:
                night_end = st.slider("Night ends", 0, 23, rules.get('night_end', 6), key='qa_night_end')
                update_wizard_state('rules', 'night_end', night_end)
        elif dg_timing == 'custom_blackout':
            tc1, tc2 = st.columns(2)
            with tc1:
                blackout_start = st.slider("Blackout starts", 0, 23, rules.get('blackout_start', 22), key='qa_blackout_start')
                update_wizard_state('rules', 'blackout_start', blackout_start)
            with tc2:
                blackout_end = st.slider("Blackout ends", 0, 23, rules.get('blackout_end', 6), key='qa_blackout_end')
                update_wizard_state('rules', 'blackout_end', blackout_end)

        # Question 2: DG Trigger
        st.markdown("**What triggers the generator?**")
        valid_triggers = get_valid_triggers_for_timing(dg_timing)
        trigger_options = {t[0]: t[1] for t in valid_triggers}

        current_trigger = rules.get('dg_trigger', 'reactive')
        if current_trigger not in trigger_options:
            current_trigger = list(trigger_options.keys())[0]
            update_wizard_state('rules', 'dg_trigger', current_trigger)

        dg_trigger = st.radio(
            "DG trigger:",
            options=list(trigger_options.keys()),
            format_func=lambda x: trigger_options[x],
            index=list(trigger_options.keys()).index(current_trigger),
            key='qa_dg_trigger',
            label_visibility="collapsed"
        )
        update_wizard_state('rules', 'dg_trigger', dg_trigger)

        # SOC thresholds
        if dg_trigger == 'soc_based':
            st.markdown("**SOC Thresholds:**")
            soc_col1, soc_col2 = st.columns(2)
            with soc_col1:
                soc_on = st.slider(
                    "DG ON below (%)",
                    int(setup['bess_min_soc']), int(setup['bess_max_soc']) - 10,
                    int(rules.get('soc_on_threshold', 30)), step=5, key='qa_soc_on'
                )
                update_wizard_state('rules', 'soc_on_threshold', float(soc_on))
            with soc_col2:
                soc_off = st.slider(
                    "DG OFF above (%)",
                    soc_on + 10, int(setup['bess_max_soc']),
                    max(int(rules.get('soc_off_threshold', 80)), soc_on + 10), step=5, key='qa_soc_off'
                )
                update_wizard_state('rules', 'soc_off_threshold', float(soc_off))

    with col_rules2:
        # Question 3: DG charges BESS
        st.markdown("**Can DG charge the battery?**")
        dg_charges_bess = st.radio(
            "DG charging:",
            options=[False, True],
            format_func=lambda x: "Yes — excess DG charges battery" if x else "No — solar only charges battery",
            index=1 if rules.get('dg_charges_bess', False) else 0,
            key='qa_dg_charges',
            label_visibility="collapsed"
        )
        update_wizard_state('rules', 'dg_charges_bess', dg_charges_bess)

        # Question 4: Load priority
        st.markdown("**Load serving priority:**")
        dg_load_priority = st.radio(
            "Priority:",
            options=['bess_first', 'dg_first'],
            format_func=lambda x: {
                'bess_first': "BESS First — Battery serves load, DG fills gap",
                'dg_first': "DG First — Generator serves load directly"
            }[x],
            index=0 if rules.get('dg_load_priority', 'bess_first') == 'bess_first' else 1,
            key='qa_load_priority',
            label_visibility="collapsed"
        )
        update_wizard_state('rules', 'dg_load_priority', dg_load_priority)

        # Template card
        st.markdown("**Dispatch Strategy:**")
        template_id = infer_template(dg_enabled=True, dg_timing=dg_timing, dg_trigger=dg_trigger)
        update_wizard_state('rules', 'inferred_template', template_id)
        render_template_card(template_id, dg_charges_bess, dg_load_priority)

st.divider()


# =============================================================================
# SECTION 2: CONFIGURATION SELECTION
# =============================================================================

st.header("2️⃣ Configuration")

# Initialize quick analysis state if needed
if 'quick_analysis' not in st.session_state:
    st.session_state.quick_analysis = {
        'bess_capacity': 100.0,
        'duration': 4,
        'dg_capacity': 10.0,
        'simulation_results': None,
        'cache_key': None,
    }

qa_state = st.session_state.quick_analysis

col_config1, col_config2, col_config3 = st.columns(3)

with col_config1:
    st.markdown("**BESS Capacity (MWh)**")
    bess_capacity = st.slider(
        "BESS MWh",
        min_value=10.0, max_value=500.0,
        value=qa_state['bess_capacity'],
        step=10.0,
        key='qa_bess_slider',
        label_visibility="collapsed"
    )
    bess_capacity = st.number_input(
        "Fine-tune",
        min_value=10.0, max_value=500.0,
        value=bess_capacity,
        step=5.0,
        key='qa_bess_input'
    )
    qa_state['bess_capacity'] = bess_capacity

with col_config2:
    st.markdown("**Duration (hours)**")
    duration = st.selectbox(
        "Duration",
        options=[1, 2, 4, 6, 8],
        index=[1, 2, 4, 6, 8].index(qa_state['duration']) if qa_state['duration'] in [1, 2, 4, 6, 8] else 2,
        key='qa_duration',
        label_visibility="collapsed"
    )
    qa_state['duration'] = duration

    power_mw = bess_capacity / duration
    st.info(f"**Power:** {power_mw:.1f} MW")

with col_config3:
    if dg_enabled:
        st.markdown("**DG Capacity (MW)**")
        dg_capacity = st.slider(
            "DG MW",
            min_value=0.0, max_value=50.0,
            value=qa_state['dg_capacity'],
            step=5.0,
            key='qa_dg_slider',
            label_visibility="collapsed"
        )
        dg_capacity = st.number_input(
            "Fine-tune",
            min_value=0.0, max_value=50.0,
            value=dg_capacity,
            step=1.0,
            key='qa_dg_input'
        )
        qa_state['dg_capacity'] = dg_capacity
    else:
        dg_capacity = 0.0
        st.markdown("**DG Capacity**")
        st.info("DG disabled in Setup")

# Configuration summary
st.markdown(f"""
**Selected Configuration:** `{power_mw:.0f} MW × {duration}-hr = {bess_capacity:.0f} MWh` | DG: `{dg_capacity:.0f} MW`
""")

# Run simulation button
run_btn = st.button("🚀 Run Full Year Simulation", type="primary", use_container_width=True)

st.divider()


# =============================================================================
# SECTION 3: RESULTS ANALYSIS
# =============================================================================

# Build cache key
cache_key = f"{bess_capacity}_{duration}_{dg_capacity}_{template_id}_{dg_charges_bess}_{dg_load_priority}"
cache_key += f"_{rules.get('soc_on_threshold', 30)}_{rules.get('soc_off_threshold', 80)}"

# Check if simulation needs to run
if run_btn or (qa_state['simulation_results'] is not None and qa_state['cache_key'] == cache_key):

    if run_btn or qa_state['cache_key'] != cache_key:
        with st.spinner("Running 8760-hour simulation..."):
            # Load solar profile
            solar_source = setup.get('solar_source', 'default')
            if solar_source == 'upload' and setup.get('solar_csv_data') is not None:
                solar_profile = setup['solar_csv_data']
            elif 'default_solar_profile' in st.session_state:
                solar_profile = st.session_state.default_solar_profile.tolist()
            else:
                try:
                    from src.data_loader import load_solar_profile
                    solar_data = load_solar_profile()
                    solar_profile = solar_data.tolist() if solar_data is not None else [0] * 8760
                except:
                    solar_profile = [0] * 8760

            # Build load profile
            from src.load_builder import build_load_profile
            load_params = {
                'mw': setup['load_mw'],
                'start': setup.get('load_day_start', 6),
                'end': setup.get('load_day_end', 18),
                'windows': setup.get('load_windows', []),
                'data': setup.get('load_csv_data'),
            }
            load_profile = build_load_profile(setup['load_mode'], load_params)

            # Run simulation
            hourly_results = run_simulation(
                bess_capacity, duration, dg_capacity,
                template_id, setup, rules,
                solar_profile, load_profile.tolist()
            )

            if hourly_results is not None and len(hourly_results) > 0:
                qa_state['simulation_results'] = hourly_results
                qa_state['cache_key'] = cache_key
                st.success("Simulation complete! Full year (8760 hours) simulated.")
            else:
                st.error("Simulation failed.")
                st.stop()

    # Get results
    hourly_results = qa_state['simulation_results']

    if hourly_results is not None:
        # Convert to DataFrame
        full_year_df = convert_results_to_dataframe(hourly_results)

        st.header("3️⃣ Results")

        # ===========================================
        # PART A: FULL YEAR SUMMARY
        # ===========================================

        st.subheader("📊 Full Year Summary (8760 hours)")

        total_hours = 8760
        delivery_hours = (full_year_df['delivery'] == 'Yes').sum()
        dg_hours = (full_year_df['dg_state'] == 'ON').sum()
        total_solar = full_year_df['solar_mw'].sum()
        solar_curtailed = full_year_df['solar_curtailed'].sum()
        wastage_pct = (solar_curtailed / total_solar * 100) if total_solar > 0 else 0
        avg_soc = full_year_df['soc_percent'].mean()

        metric_cols = st.columns(5)
        metric_cols[0].metric("Delivery Hours", f"{delivery_hours:,}", f"{delivery_hours/total_hours*100:.1f}%")
        metric_cols[1].metric("DG Runtime", f"{dg_hours:,} hrs", f"{dg_hours/total_hours*100:.1f}%")
        metric_cols[2].metric("Avg SOC", f"{avg_soc:.0f}%")
        metric_cols[3].metric("Solar Curtailed", f"{solar_curtailed:,.0f} MWh")
        metric_cols[4].metric("Wastage", f"{wastage_pct:.1f}%")

        # Monthly delivery chart
        st.markdown("#### Monthly Delivery Performance")

        # Calculate monthly stats
        full_year_df['month'] = (full_year_df['hour'] // 24 // 30).clip(0, 11)  # Approximate month
        # More accurate month calculation using day of year
        full_year_df['month'] = full_year_df['hour'].apply(
            lambda h: min(11, (date(2024, 1, 1) + timedelta(hours=h)).month - 1)
        )

        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                       'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        monthly_stats = full_year_df.groupby('month').agg({
            'delivery': lambda x: (x == 'Yes').sum(),
            'dg_state': lambda x: (x == 'ON').sum(),
            'hour': 'count'
        }).reset_index()
        monthly_stats.columns = ['month', 'delivery_hours', 'dg_hours', 'total_hours']
        monthly_stats['delivery_pct'] = (monthly_stats['delivery_hours'] / monthly_stats['total_hours'] * 100)
        monthly_stats['dg_pct'] = (monthly_stats['dg_hours'] / monthly_stats['total_hours'] * 100)
        monthly_stats['month_name'] = monthly_stats['month'].apply(lambda x: month_names[x])

        # Create bar chart
        fig_monthly = go.Figure()

        # Delivery hours bars
        fig_monthly.add_trace(go.Bar(
            x=monthly_stats['month_name'],
            y=monthly_stats['delivery_hours'],
            name='Delivery Hours',
            marker_color='#2ecc71',
            text=monthly_stats['delivery_pct'].apply(lambda x: f'{x:.0f}%'),
            textposition='outside',
            hovertemplate='%{x}<br>Delivery: %{y} hrs (%{text})<extra></extra>'
        ))

        # DG hours bars
        fig_monthly.add_trace(go.Bar(
            x=monthly_stats['month_name'],
            y=monthly_stats['dg_hours'],
            name='DG Hours',
            marker_color='#e74c3c',
            text=monthly_stats['dg_pct'].apply(lambda x: f'{x:.0f}%'),
            textposition='outside',
            hovertemplate='%{x}<br>DG: %{y} hrs (%{text})<extra></extra>'
        ))

        # Reference line for max possible (approximate month hours)
        hours_per_month = [744, 696, 744, 720, 744, 720, 744, 744, 720, 744, 720, 744]  # 2024 is leap year
        fig_monthly.add_trace(go.Scatter(
            x=monthly_stats['month_name'],
            y=hours_per_month[:len(monthly_stats)],
            name='Max Hours',
            mode='lines+markers',
            line=dict(color='gray', dash='dash'),
            marker=dict(size=6),
            hovertemplate='%{x}<br>Max: %{y} hrs<extra></extra>'
        ))

        fig_monthly.update_layout(
            height=350,
            xaxis_title="Month",
            yaxis_title="Hours",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            margin=dict(l=50, r=50, t=50, b=50),
            barmode='group',
            bargap=0.2,
            bargroupgap=0.1
        )

        st.plotly_chart(fig_monthly, use_container_width=True)

        # Monthly breakdown table
        st.markdown("#### Monthly Breakdown")

        # Calculate detailed monthly stats
        monthly_detail = full_year_df.groupby('month').agg({
            'solar_to_load': lambda x: (x > 0).sum(),  # Hours with solar contribution
            'bess_to_load': lambda x: (x > 0).sum(),   # Hours with BESS contribution
            'dg_to_load': lambda x: (x > 0).sum(),     # Hours with DG contribution
            'solar_curtailed': 'sum',                   # Total solar curtailed MWh
            'solar_mw': 'sum',                          # Total solar generated MWh
        }).reset_index()
        monthly_detail.columns = ['month', 'solar_hrs', 'bess_hrs', 'dg_hrs', 'curtailed_mwh', 'total_solar_mwh']
        monthly_detail['wastage_pct'] = (monthly_detail['curtailed_mwh'] / monthly_detail['total_solar_mwh'] * 100).fillna(0)
        monthly_detail['month_name'] = monthly_detail['month'].apply(lambda x: month_names[x])

        # Create display DataFrame
        monthly_table = pd.DataFrame({
            'Month': monthly_detail['month_name'],
            'Solar Hrs': monthly_detail['solar_hrs'].astype(int),
            'BESS Hrs': monthly_detail['bess_hrs'].astype(int),
            'DG Hrs': monthly_detail['dg_hrs'].astype(int),
            'Curtailed (MWh)': monthly_detail['curtailed_mwh'].round(1),
            'Wastage %': monthly_detail['wastage_pct'].round(1),
        })

        st.dataframe(
            monthly_table,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Month': st.column_config.TextColumn('Month'),
                'Solar Hrs': st.column_config.NumberColumn('Solar Hrs', help='Hours with solar contributing to load'),
                'BESS Hrs': st.column_config.NumberColumn('BESS Hrs', help='Hours with BESS contributing to load'),
                'DG Hrs': st.column_config.NumberColumn('DG Hrs', help='Hours with DG contributing to load'),
                'Curtailed (MWh)': st.column_config.NumberColumn('Curtailed (MWh)', format='%.1f', help='Solar energy curtailed'),
                'Wastage %': st.column_config.NumberColumn('Wastage %', format='%.1f%%', help='% of solar energy wasted'),
            }
        )

        # Download button for monthly breakdown
        monthly_csv = monthly_table.to_csv(index=False)
        st.download_button(
            "📥 Download Monthly Breakdown CSV",
            data=monthly_csv,
            file_name=f"monthly_breakdown_{bess_capacity}mwh_{duration}hr.csv",
            mime="text/csv",
        )

        st.divider()

        # ===========================================
        # PART B: DATE RANGE ANALYSIS
        # ===========================================

        st.subheader("📈 Date Range Analysis")

        # Date selection
        date_col1, date_col2, date_col3 = st.columns([1, 1, 2])

        with date_col1:
            start_date = st.date_input(
                "Start Date",
                value=date(2024, 1, 1),
                min_value=date(2024, 1, 1),
                max_value=date(2024, 12, 31),
                key='qa_start_date'
            )

        with date_col2:
            max_end = min(start_date + timedelta(days=6), date(2024, 12, 31))
            default_end = min(start_date + timedelta(days=2), max_end)
            end_date = st.date_input(
                "End Date",
                value=default_end,
                min_value=start_date,
                max_value=max_end,
                key='qa_end_date'
            )

        with date_col3:
            days_selected = (end_date - start_date).days + 1
            st.info(f"📅 Viewing **{days_selected} days** ({days_selected * 24} hours)")

        # Filter to date range
        start_hour = date_to_hour_index(start_date)
        end_hour = date_to_hour_index(end_date) + 24
        hourly_df = full_year_df.iloc[start_hour:end_hour].reset_index(drop=True)

        # Period metrics
        period_hours = len(hourly_df)
        period_delivery = (hourly_df['delivery'] == 'Yes').sum()
        period_dg = (hourly_df['dg_state'] == 'ON').sum()
        period_soc = hourly_df['soc_percent'].mean()
        period_curtailed = hourly_df['solar_curtailed'].sum()
        period_solar = hourly_df['solar_mw'].sum()
        period_wastage = (period_curtailed / period_solar * 100) if period_solar > 0 else 0

        pm_cols = st.columns(5)
        pm_cols[0].metric("Delivery", f"{period_delivery}/{period_hours}", f"{period_delivery/period_hours*100:.1f}%")
        pm_cols[1].metric("DG Hours", f"{period_dg}", f"{period_dg/period_hours*100:.1f}%")
        pm_cols[2].metric("Avg SOC", f"{period_soc:.0f}%")
        pm_cols[3].metric("Curtailed", f"{period_curtailed:.1f} MWh")
        pm_cols[4].metric("Wastage", f"{period_wastage:.1f}%")

        # Dispatch graph
        soc_on = rules.get('soc_on_threshold', 30)
        soc_off = rules.get('soc_off_threshold', 80)
        fig = create_dispatch_graph(hourly_df, setup['load_mw'], bess_capacity, soc_on, soc_off)
        st.plotly_chart(fig, use_container_width=True)

        st.caption("""
        **Orange**: Solar | **Red**: DG Output | **Blue**: BESS Power (negative=charging) | **Purple**: Delivery
        **Green dotted**: SOC % | **Royal Blue dashed**: BESS Energy (MWh)
        """)

        # Hourly table
        with st.expander("📊 Hourly Data Table", expanded=False):
            display_df = hourly_df.copy()
            display_df['Hour'] = display_df['hour']
            display_df['Day'] = display_df['day']
            display_df['HoD'] = display_df['hour_of_day']
            display_df['Solar (MW)'] = display_df['solar_mw'].round(1)
            display_df['DG (MW)'] = display_df['dg_output_mw'].round(1)
            display_df['DG→Load'] = display_df['dg_to_load'].round(1)
            display_df['DG→BESS'] = display_df['dg_to_bess'].round(1)
            display_df['DG Curt'] = display_df['dg_curtailed'].round(1)
            display_df['BESS (MW)'] = display_df['bess_mw'].round(1)
            display_df['SOC (%)'] = display_df['soc_percent'].round(1)
            display_df['BESS State'] = display_df['bess_state']
            display_df['DG State'] = display_df['dg_state']
            display_df['To Load (MW)'] = (display_df['solar_to_load'] + display_df['dg_to_load'] + display_df['bess_to_load']).round(1)
            display_df['Unmet (MW)'] = display_df['unmet_mw'].round(1)
            display_df['Delivery'] = display_df['delivery']

            display_cols = [
                'Hour', 'Day', 'HoD',
                'Solar (MW)', 'DG (MW)', 'DG→Load', 'DG→BESS', 'DG Curt',
                'BESS (MW)', 'SOC (%)',
                'BESS State', 'DG State',
                'To Load (MW)', 'Unmet (MW)', 'Delivery'
            ]

            styled_df = display_df[display_cols].style.apply(style_hourly_row, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=400)

            st.markdown("""
            **Row Colors:** 🟢 Green = Charging | 🟣 Lavender = Discharging | 🟡 Yellow = DG Running | 🔴 Pink = Unmet Load
            """)

        # Export
        csv_data = hourly_df.to_csv(index=False)
        st.download_button(
            "📥 Download Selected Range CSV",
            data=csv_data,
            file_name=f"quick_analysis_{bess_capacity}mwh_{duration}hr_{start_date}_to_{end_date}.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.divider()

        # ===========================================
        # SECTION 4: 10-YEAR PROJECTION
        # ===========================================

        st.header("4️⃣ 10-Year Projection")
        st.markdown("Battery degradation impact on system performance over 10 years (2% linear degradation per year).")

        # Year 1 baseline metrics from simulation
        year1_delivery = (full_year_df['delivery'] == 'Yes').sum()
        year1_dg_hours = (full_year_df['dg_state'] == 'ON').sum()
        year1_curtailed = full_year_df['solar_curtailed'].sum()
        year1_total_solar = full_year_df['solar_mw'].sum()

        # Calculate delivery contribution percentages from Year 1
        delivery_df = full_year_df[full_year_df['delivery'] == 'Yes']
        if len(delivery_df) > 0:
            # Hours where each source contributed to delivery
            solar_delivery_hrs = (delivery_df['solar_to_load'] > 0).sum()
            bess_delivery_hrs = (delivery_df['bess_to_load'] > 0).sum()
            dg_delivery_hrs = (delivery_df['dg_to_load'] > 0).sum()

            year1_solar_delivery_pct = (solar_delivery_hrs / len(delivery_df) * 100)
            year1_bess_delivery_pct = (bess_delivery_hrs / len(delivery_df) * 100)
            year1_dg_delivery_pct = (dg_delivery_hrs / len(delivery_df) * 100)
        else:
            year1_solar_delivery_pct = 0
            year1_bess_delivery_pct = 0
            year1_dg_delivery_pct = 0

        year1_solar_wastage_pct = (year1_curtailed / year1_total_solar * 100) if year1_total_solar > 0 else 0

        # Calculate battery-critical hours (where battery was essential for delivery)
        battery_critical = full_year_df[
            (full_year_df['bess_to_load'] > 0) &
            (full_year_df['delivery'] == 'Yes')
        ]
        battery_critical_hours = len(battery_critical)

        # Estimate annual cycles from Year 1
        # Cycles = total energy discharged / capacity
        total_discharge = full_year_df[full_year_df['bess_mw'] < 0]['bess_mw'].abs().sum()
        year1_cycles = total_discharge / bess_capacity if bess_capacity > 0 else 0

        # Build 10-year projection
        degradation_rate = 0.02  # 2% per year
        projection_data = []

        for year in range(1, 11):
            capacity_factor = 1 - degradation_rate * (year - 1)
            effective_capacity = bess_capacity * capacity_factor
            capacity_loss_pct = (year - 1) * degradation_rate

            # Estimate lost delivery hours due to degradation
            # Simplified model: linear reduction based on battery-critical hours
            lost_hours = int(battery_critical_hours * capacity_loss_pct)

            # Smart distribution: DG covers if available, else becomes unmet
            if dg_enabled and dg_capacity > 0:
                # DG can potentially cover the shortfall
                proj_delivery = year1_delivery  # Delivery maintained
                proj_dg_hours = min(8760, year1_dg_hours + lost_hours)  # DG usage increases
                # DG contribution increases as BESS degrades
                proj_dg_delivery_pct = min(100, year1_dg_delivery_pct + (capacity_loss_pct * 100))
                proj_bess_delivery_pct = max(0, year1_bess_delivery_pct - (capacity_loss_pct * 50))
            else:
                # No DG - shortfall becomes unmet
                proj_delivery = max(0, year1_delivery - lost_hours)
                proj_dg_hours = 0
                proj_dg_delivery_pct = 0
                proj_bess_delivery_pct = max(0, year1_bess_delivery_pct * capacity_factor)

            # Scale other metrics
            proj_cycles = year1_cycles * capacity_factor
            proj_solar_wastage = year1_solar_wastage_pct * (1 + capacity_loss_pct)  # More wastage as BESS shrinks

            projection_data.append({
                'Year': year,
                'Capacity (MWh)': round(effective_capacity, 1),
                'Delivery Hrs': int(proj_delivery),
                'Delivery %': round(proj_delivery / 8760 * 100, 1),
                'DG Hrs': int(proj_dg_hours),
                'Cycles': int(proj_cycles),
                '% Solar': round(year1_solar_delivery_pct, 1),  # Solar contribution stays constant
                '% BESS': round(proj_bess_delivery_pct, 1),
                '% DG': round(proj_dg_delivery_pct, 1),
                '% Wastage': round(proj_solar_wastage, 1),
            })

        projection_df = pd.DataFrame(projection_data)

        # Display table
        st.dataframe(
            projection_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                'Year': st.column_config.NumberColumn('Year', format='%d'),
                'Capacity (MWh)': st.column_config.NumberColumn('Capacity', format='%.1f'),
                'Delivery Hrs': st.column_config.NumberColumn('Delivery Hrs', format='%d'),
                'Delivery %': st.column_config.NumberColumn('Delivery %', format='%.1f%%'),
                'DG Hrs': st.column_config.NumberColumn('DG Hrs', format='%d'),
                'Cycles': st.column_config.NumberColumn('Cycles', format='%d'),
                '% Solar': st.column_config.NumberColumn('% Solar', format='%.1f%%', help='% of delivery hours with solar contribution'),
                '% BESS': st.column_config.NumberColumn('% BESS', format='%.1f%%', help='% of delivery hours with BESS contribution'),
                '% DG': st.column_config.NumberColumn('% DG', format='%.1f%%', help='% of delivery hours with DG contribution'),
                '% Wastage': st.column_config.NumberColumn('% Wastage', format='%.1f%%', help='% of solar energy curtailed'),
            }
        )

        # Download button for 10-year projection
        projection_csv = projection_df.to_csv(index=False)
        st.download_button(
            "📥 Download 10-Year Projection CSV",
            data=projection_csv,
            file_name=f"10year_projection_{bess_capacity}mwh_{duration}hr.csv",
            mime="text/csv",
        )

        # Projection logic explanation
        with st.expander("ℹ️ How are these projections calculated?", expanded=False):
            st.markdown(f"""
**Degradation Model:**
- Battery capacity degrades linearly at **2% per year**
- Year 1: 100% → Year 10: 82% of original capacity

**Key Year 1 Metrics (from simulation):**
- Battery-critical hours: **{battery_critical_hours:,}** (hours where BESS was essential for delivery)
- Annual cycles: **{year1_cycles:.0f}**
- Solar wastage: **{year1_solar_wastage_pct:.1f}%**

**Projection Logic:**
1. **Capacity**: `Original × (1 - 0.02 × (Year - 1))`
2. **Lost Hours**: As battery shrinks, some delivery hours are lost = `Battery-critical hours × Capacity loss %`
3. **DG Compensation**: {"DG runtime increases to cover lost battery hours" if dg_enabled else "No DG available - lost hours become unmet"}
4. **Delivery %**: {"Maintained (DG compensates)" if dg_enabled else "Decreases as battery degrades"}
5. **Cycles**: Decrease proportionally with capacity (less energy to cycle)
6. **% Wastage**: Increases as smaller battery absorbs less excess solar

**Assumptions:**
- Solar generation pattern remains constant year-over-year
- Load profile remains constant
- DG availability and capacity unchanged
- No replacement or augmentation of battery
            """)

        # Summary insights
        year10 = projection_df[projection_df['Year'] == 10].iloc[0]
        delivery_drop = year1_delivery - year10['Delivery Hrs']
        delivery_drop_pct = (delivery_drop / year1_delivery * 100) if year1_delivery > 0 else 0

        if dg_enabled:
            dg_increase = year10['DG Hrs'] - year1_dg_hours
            st.info(f"📉 **Year 10 Impact:** Battery at {year10['Capacity (MWh)']:.0f} MWh ({100-18}% of original). "
                    f"DG runtime increases by ~{dg_increase:,} hrs/year to compensate.")
        else:
            st.info(f"📉 **Year 10 Impact:** Battery at {year10['Capacity (MWh)']:.0f} MWh ({100-18}% of original). "
                    f"Delivery drops by ~{delivery_drop:,} hrs ({delivery_drop_pct:.1f}%).")

        st.divider()

        # ===========================================
        # 20-YEAR MONTHLY BREAKDOWN CSV
        # ===========================================

        st.markdown("### 📊 20-Year Monthly Projection Export")
        st.markdown("Download detailed monthly breakdown with battery degradation projections for 20 years.")

        # Build 20-year monthly projection data
        monthly_20yr_data = []

        # Get Year 1 monthly baseline from simulation
        year1_monthly = monthly_detail.copy()

        for year in range(1, 21):
            capacity_factor = 1 - degradation_rate * (year - 1)
            effective_capacity = bess_capacity * capacity_factor
            capacity_loss_pct = (year - 1) * degradation_rate

            for _, month_row in year1_monthly.iterrows():
                month_idx = month_row['month']
                month_name = month_row['month_name']

                # Scale metrics based on degradation
                # Battery-critical hours for this month
                month_battery_critical = full_year_df[
                    (full_year_df['month'] == month_idx) &
                    (full_year_df['bess_to_load'] > 0) &
                    (full_year_df['delivery'] == 'Yes')
                ]
                month_critical_hrs = len(month_battery_critical)
                month_lost_hrs = int(month_critical_hrs * capacity_loss_pct)

                # Year 1 monthly delivery hours
                year1_month_delivery = full_year_df[
                    (full_year_df['month'] == month_idx) &
                    (full_year_df['delivery'] == 'Yes')
                ].shape[0]

                year1_month_dg = full_year_df[
                    (full_year_df['month'] == month_idx) &
                    (full_year_df['dg_state'] == 'ON')
                ].shape[0]

                # Apply degradation logic
                if dg_enabled and dg_capacity > 0:
                    proj_month_delivery = year1_month_delivery
                    proj_month_dg = min(hours_per_month[month_idx], year1_month_dg + month_lost_hrs)
                else:
                    proj_month_delivery = max(0, year1_month_delivery - month_lost_hrs)
                    proj_month_dg = 0

                # Scale other metrics
                proj_solar_hrs = int(month_row['solar_hrs'])  # Solar stays constant
                proj_bess_hrs = max(0, int(month_row['bess_hrs'] * capacity_factor))
                proj_dg_hrs = int(month_row['dg_hrs']) if year == 1 else int(proj_month_dg)
                proj_curtailed = month_row['curtailed_mwh'] * (1 + capacity_loss_pct)
                proj_wastage_pct = month_row['wastage_pct'] * (1 + capacity_loss_pct)

                monthly_20yr_data.append({
                    'Year': year,
                    'Month': month_name,
                    'Month_Num': month_idx + 1,
                    'Capacity_MWh': round(effective_capacity, 1),
                    'Capacity_%': round(capacity_factor * 100, 1),
                    'Delivery_Hrs': proj_month_delivery,
                    'Delivery_%': round(proj_month_delivery / hours_per_month[month_idx] * 100, 1),
                    'Solar_Hrs': proj_solar_hrs,
                    'BESS_Hrs': proj_bess_hrs,
                    'DG_Hrs': proj_dg_hrs,
                    'Curtailed_MWh': round(proj_curtailed, 1),
                    'Wastage_%': round(proj_wastage_pct, 1),
                })

        monthly_20yr_df = pd.DataFrame(monthly_20yr_data)

        # Download button
        monthly_20yr_csv = monthly_20yr_df.to_csv(index=False)
        st.download_button(
            "📥 Download 20-Year Monthly Projection CSV",
            data=monthly_20yr_csv,
            file_name=f"20year_monthly_projection_{bess_capacity}mwh_{duration}hr.csv",
            mime="text/csv",
            use_container_width=True
        )

        st.caption(f"Contains {len(monthly_20yr_df)} rows (12 months × 20 years) with degradation-adjusted metrics.")

else:
    st.info("👆 Configure your settings above and click **Run Full Year Simulation** to see results.")


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("### ⚡ Quick Analysis")

    st.markdown("**Setup (from Step 1):**")
    st.markdown(f"- Load: {setup['load_mw']} MW")
    st.markdown(f"- Solar: {setup['solar_capacity_mw']} MWp")
    st.markdown(f"- DG: {'Enabled' if dg_enabled else 'Disabled'}")

    st.markdown("---")

    st.markdown("**Configuration:**")
    st.markdown(f"- BESS: {bess_capacity:.0f} MWh")
    st.markdown(f"- Duration: {duration} hrs")
    st.markdown(f"- Power: {bess_capacity/duration:.0f} MW")
    if dg_enabled:
        st.markdown(f"- DG: {dg_capacity:.0f} MW")

    st.markdown("---")

    if st.button("← Back to Step 1", use_container_width=True):
        st.switch_page("pages/8_🚀_Step1_Setup.py")

    st.markdown("---")

    st.caption("Alternative to the 5-step wizard. Use this for quick single-configuration analysis.")
