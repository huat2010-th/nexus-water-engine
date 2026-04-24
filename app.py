import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import io
import matplotlib
import matplotlib.pyplot as plt

# --- CRITICAL FIX: Force Matplotlib to run in 'headless' mode for Web App ---
matplotlib.use('Agg') 
# ----------------------------------------------------------------------------

# ==========================================
# 1. PAGE CONFIGURATION & HEADER
# ==========================================
st.set_page_config(page_title="Nexus Water Simulator v3.0", layout="wide")

st.title("💧 Dynamic Water Demand Simulation Engine (v3.0)")
st.markdown("""
**Hybrid Simulation Tool:** Toggle between **Method A** (Component-Based Engineering) and **Method B** (Smart Inference Architecture).
""")

# ==========================================
# 2. SIDEBAR - MASTER CONTROL PANEL
# ==========================================
with st.sidebar:
    st.header("⚙️ Master Settings")
    
    # --- MASTER SWITCH ---
    calc_method = st.radio(
        "Select Calculation Method:",
        ["Method A: Component-Based (Detailed)", "Method B: Smart Inference Architecture"]
    )
    st.divider()

    # ==========================================
    # SIDEBAR: METHOD A CONTROLS
    # ==========================================
    if calc_method == "Method A: Component-Based (Detailed)":
        st.info("ℹ️ **Category Definitions:**\n\n**Hotel:** Resort, Hotel, Club, Villa\n**Non-Hotel:** Residential, Condo, Apartment")

        # --- INITIALIZE VARIABLES ---
        h_shower = h_toilet = h_misc = h_laundry = 100
        h_meals = h_water_meal = h_pool_evap = h_pool_bw = 0
        n_shower = n_toilet = n_misc = n_laundry = 100
        n_meals = n_water_meal = n_pool_evap = n_pool_bw = 0
        b_cooling = b_irrigation = b_staff = 0
        bench_hotel_pax = bench_non_pax = bench_staff_pax = 0

        tab_hotel, tab_non = st.tabs(["🏨 HOTEL Settings", "🏠 NON-HOTEL Settings"])
        
        with tab_hotel:
            st.markdown("### Guest Behavior")
            h_shower = st.number_input("Shower (L/pax)", value=120, key="h_sh")
            h_toilet = st.number_input("Toilet (L/pax)", value=45, key="h_tl")
            h_misc = st.number_input("Faucet/Misc (L/pax)", value=40, key="h_ms")
            h_laundry = st.number_input("Laundry (L/pax)", value=60, key="h_ln")
            
            st.markdown("### F&B & Pools")
            h_meals = st.slider("Meals per Guest/Day", 1.0, 3.0, 2.5, key="h_ml")
            h_water_meal = st.number_input("Water per Meal (L)", value=25, key="h_wpm")
            h_pool_evap = st.number_input("Pool Evap (L/m²)", value=10, key="h_pe")
            h_pool_bw = st.number_input("Pool Backwash (L/m²)", value=5, key="h_pbw")

        with tab_non:
            st.markdown("### Resident Behavior")
            n_shower = st.number_input("Shower (L/pax)", value=90, key="n_sh")
            n_toilet = st.number_input("Toilet (L/pax)", value=40, key="n_tl")
            n_misc = st.number_input("Faucet/Misc (L/pax)", value=30, key="n_ms")
            n_laundry = st.number_input("Laundry (L/pax)", value=25, key="n_ln")
            
            st.markdown("### F&B & Pools")
            n_meals = st.slider("Dining Out/Cafe (Meals/Day)", 0.0, 2.0, 0.2, key="n_ml")
            n_water_meal = st.number_input("Water per Meal (L)", value=20, key="n_wpm")
            n_pool_evap = st.number_input("Pool Evap (L/m²)", value=10, key="n_pe")
            n_pool_bw = st.number_input("Pool Backwash (L/m²)", value=5, key="n_pbw")

        with st.expander("Engineering (Shared)", expanded=True):
            b_cooling = st.number_input("Cooling Makeup (L/m² GFA)", value=2.0)
            b_irrigation = st.number_input("Irrigation (L/m² Landscape)", value=5)
            b_staff = st.number_input("Staff Usage (L/staff)", value=100)

        with st.expander("Inference Logic (Missing Data)", expanded=False):
            st.caption("Staff Ratios")
            ratio_hotel = st.slider("Staff per HOTEL Key", 0.5, 2.5, 1.2)
            ratio_non = st.slider("Staff per NON-HOTEL Key", 0.0, 1.0, 0.2)
            
            st.caption("Assumed Areas")
            inf_pool = st.number_input("Pool Area (m²/unit)", value=3.0)
            inf_land = st.number_input("Landscape Area (m²/unit)", value=20.0)
            inf_gfa = st.number_input("Avg Unit GFA (m²)", value=120.0)

        with st.expander("Seasonality & Scenarios", expanded=True):
            st.markdown("### Occupancy Rates")
            peak_occ = st.slider("Peak Season (High)", 70, 100, 90, key='occ_h') / 100
            avg_occ = st.slider("Annual Average", 50, 80, 65, key='occ_a') / 100
            
            st.markdown("### Weather Impact (Irrigation)")
            irr_peak_mult = st.slider("Dry Season Irrig Multiplier", 1.0, 2.0, 1.5)

            st.markdown("### Future")
            growth_rate = st.number_input("Annual Demand Growth (%)", value=3.5) / 100
            nrw_loss = st.slider("NRW / Leakage (%)", 0, 20, 10) / 100

    # ==========================================
    # SIDEBAR: METHOD B CONTROLS
    # ==========================================
    else:
        st.header("⚙️ Modeling Assumptions")
        st.markdown("Set the relative consumption weights for different features. (Baseline: 1-Bed = 1.0 Equivalent Unit)")

        st.subheader("Room Equivalents")
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            w_1bed = st.number_input("1-Bedroom Weight", value=1.0, step=0.1)
            w_3bed = st.number_input("3-Bedroom Weight", value=2.0, step=0.1)
            w_unspec = st.number_input("Unspecified Unit Weight", value=1.5, step=0.1)
        with col_w2:
            w_2bed = st.number_input("2-Bedroom Weight", value=1.5, step=0.1)
            w_4bed = st.number_input("4+ Bedroom Weight", value=2.5, step=0.1)

        st.subheader("Swimming Pool Equivalents")
        w_shared_pool = st.number_input("Shared Pool Weight", value=20.0, step=1.0)
        w_private_pool = st.number_input("Private Pool Weight", value=3.0, step=0.5)

        weights = {
            '1-Bed': w_1bed, '2-Bed': w_2bed, '3-Bed': w_3bed, '4+ Bed': w_4bed, 
            'Unspecified Units': w_unspec, 'Shared Pools': w_shared_pool, 'Private Pools': w_private_pool
        }


# ==========================================
# 3. MAIN INTERFACE - METHOD A LOGIC
# ==========================================
if calc_method == "Method A: Component-Based (Detailed)":
    
    st.subheader("📁 Project Data Input (Method A)")

    default_data = pd.DataFrame([
        {'Year': 2026, 'Project': 'Skypark 2', 'Category': 'Non-Hotel', 'Type': '1BR', 'Count': 236},
        {'Year': 2026, 'Project': 'Banyan Tree Oceanfront', 'Category': 'Hotel', 'Type': 'Villa', 'Count': 6},
        {'Year': 2027, 'Project': 'Lakeland Waterfront', 'Category': 'Non-Hotel', 'Type': '2BR', 'Count': 47},
        {'Year': 2030, 'Project': 'Laguna Golf Residences', 'Category': 'Non-Hotel', 'Type': '1BR', 'Count': 139},
    ])

    project_df = st.data_editor(default_data, num_rows="dynamic", use_container_width=True)

    def calculate_demand(df, method):
        results = []
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce').fillna(2026).astype(int)
        df = df.sort_values('Year')
        
        start_year = int(df['Year'].min())
        end_year = int(df['Year'].max()) + 10
        HOTEL_KEYWORDS = ['Hotel', 'Resort', 'Club', 'Villa'] 

        for year in range(start_year, end_year + 1):
            active_projects = df[df['Year'] <= year]
            if active_projects.empty: continue
                
            sum_variable_L = 0 
            sum_fixed_L = 0     
            sum_irrigation_L = 0 
            sum_pool_L = 0      

            breakdown_dom = 0
            breakdown_fnb = 0
            breakdown_staff = 0
            breakdown_irr = 0
            breakdown_pool = 0

            for _, row in active_projects.iterrows():
                count = row['Count']
                cat = str(row.get('Category', 'Non-Hotel'))
                u_type = str(row.get('Type', '1BR'))
                
                is_hotel = any(k in cat for k in HOTEL_KEYWORDS) or (cat == 'Hotel')
                
                pax_map = {'1BR': 2, '2BR': 4, '3BR': 5, '4BR': 6, '5BR': 8, 'Villa': 6}
                pax_per_unit = pax_map.get(u_type, 2)
                total_pax = count * pax_per_unit
                s_ratio = ratio_hotel if is_hotel else ratio_non
                total_staff = count * s_ratio
                
                if "Method A" in method:
                    if is_hotel:
                        v_sh, v_tl, v_mc, v_ln = h_shower, h_toilet, h_misc, h_laundry
                        v_ml, v_wm = h_meals, h_water_meal
                        v_pe, v_pbw = h_pool_evap, h_pool_bw
                    else:
                        v_sh, v_tl, v_mc, v_ln = n_shower, n_toilet, n_misc, n_laundry
                        v_ml, v_wm = n_meals, n_water_meal
                        v_pe, v_pbw = n_pool_evap, n_pool_bw

                    row_dom = (total_pax * (v_sh + v_tl + v_mc + v_ln))
                    row_fnb = (total_pax * v_ml * v_wm)
                    row_stf = (total_staff * b_staff)
                    row_irr = (count * inf_land * b_irrigation)
                    row_pol = (count * inf_pool * (v_pe + v_pbw))
                    row_col = (count * inf_gfa * b_cooling)
                    
                    row_variable = row_dom + row_fnb
                    row_fixed = row_stf + row_col
                    row_irrigation = row_irr
                    row_pool = row_pol
                    
                    breakdown_dom += (row_dom * avg_occ)
                    breakdown_fnb += (row_fnb * avg_occ)
                    breakdown_staff += row_fixed 
                    breakdown_irr += row_irr     
                    breakdown_pool += row_pool   
                    
                else:
                    pax_bench = bench_hotel_pax if is_hotel else bench_non_pax
                    row_variable = (total_pax * pax_bench)
                    row_fixed = (total_staff * bench_staff_pax)
                    row_irrigation = 0
                    row_pool = 0
                    
                    breakdown_dom += (row_variable * avg_occ)
                    breakdown_staff += row_fixed

                sum_variable_L += row_variable
                sum_fixed_L += row_fixed
                sum_irrigation_L += row_irrigation
                sum_pool_L += row_pool

            years_passed = year - start_year
            growth_factor = (1 + growth_rate) ** years_passed
            nrw_factor = (1 + nrw_loss)
            
            peak_m3 = ( (sum_variable_L * peak_occ) + sum_fixed_L + sum_pool_L + (sum_irrigation_L * irr_peak_mult) )
            peak_m3 = (peak_m3 * growth_factor * nrw_factor) / 1000
            
            avg_m3 = ( (sum_variable_L * avg_occ) + sum_fixed_L + sum_pool_L + sum_irrigation_L )
            avg_m3 = (avg_m3 * growth_factor * nrw_factor) / 1000
            
            annual_m3 = avg_m3 * 365
            
            bd_factor = (growth_factor * nrw_factor) / 1000
            
            results.append({
                'Year': year,
                'Daily Peak (m3/day)': round(peak_m3, 2),
                'Daily Avg (m3/day)': round(avg_m3, 2),
                'Annual Total (m3/year)': round(annual_m3, 2),
                'Domestic (Avg m3/d)': round(breakdown_dom * bd_factor, 2),
                'F&B (Avg m3/d)': round(breakdown_fnb * bd_factor, 2),
                'Staff/Cooling (Avg m3/d)': round(breakdown_staff * bd_factor, 2),
                'Pools (Avg m3/d)': round(breakdown_pool * bd_factor, 2),
                'Irrigation (Avg m3/d)': round(breakdown_irr * bd_factor, 2),
            })
            
        return pd.DataFrame(results)

    if not project_df.empty:
        try:
            df_results = calculate_demand(project_df, calc_method)

            st.divider()
            st.subheader("📈 Projected Demand Scenarios (Method A)")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(df_results['Year'], df_results['Daily Peak (m3/day)'], 
                        label='Peak (Infra Cap)', color='#d62728', linewidth=2, marker='o')
                ax.plot(df_results['Year'], df_results['Daily Avg (m3/day)'], 
                        label='Average (Operational)', color='black', linewidth=2, linestyle='--')
                
                ax.fill_between(df_results['Year'], df_results['Daily Avg (m3/day)'], 
                                df_results['Daily Peak (m3/day)'], color='gray', alpha=0.15)
                
                ax.set_ylabel("Water Demand (m³/day)")
                ax.set_title("Operational Range: Average vs. Peak")
                ax.grid(True, linestyle='--', alpha=0.6)
                ax.legend()
                st.pyplot(fig)

            with col2:
                st.markdown("### Key Metrics")
                curr = df_results.iloc[0]
                end = df_results.iloc[-1]
                st.metric("Future Peak (Day)", f"{end['Daily Peak (m3/day)']} m³")
                st.metric("Future Annual (Year)", f"{end['Annual Total (m3/year)']:,.0f} m³")
                st.metric("Growth", f"+{round(end['Daily Peak (m3/day)']-curr['Daily Peak (m3/day)'],1)} m³")

            st.divider()
            st.subheader("📋 Yearly Water Consumption Breakdown")
            
            cols = ['Year', 'Daily Peak (m3/day)', 'Daily Avg (m3/day)', 'Annual Total (m3/year)', 
                    'Domestic (Avg m3/d)', 'Irrigation (Avg m3/d)', 'Pools (Avg m3/d)']
            
            st.dataframe(
                df_results[cols].style.format({
                    'Daily Peak (m3/day)': '{:,.2f}',
                    'Daily Avg (m3/day)': '{:,.2f}',
                    'Annual Total (m3/year)': '{:,.0f}',
                    'Domestic (Avg m3/d)': '{:,.1f}',
                    'Irrigation (Avg m3/d)': '{:,.1f}',
                    'Pools (Avg m3/d)': '{:,.1f}'
                }), 
                use_container_width=True,
                height=400
            )
            
            csv = df_results.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Full Data as CSV",
                data=csv,
                file_name="nexus_water_forecast_MethodA.csv",
                mime="text/csv"
            )
                
        except Exception as e:
            st.error(f"An error occurred during calculation: {e}")
    else:
        st.warning("Please enter data to simulate.")


# ==========================================
# 4. MAIN INTERFACE - METHOD B LOGIC
# ==========================================
elif calc_method == "Method B: Smart Inference Architecture":
    
    # --- STEP 1: Baseline Data Input ---
    st.header("Step 1: Current Baseline Data Input (Method B)")
    st.markdown("Pre-loaded with existing properties to derive Master Inference Rates.")

    default_baseline = pd.DataFrame([
        {"Project Name": "Laguna Fairway", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 24, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 14865, "Peak Month Demand (m³)": 1743},
        {"Project Name": "Laguna Waters", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 10, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 100, "Peak Month Demand (m³)": 10},
        {"Project Name": "Laguna Vista", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 8, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 753, "Peak Month Demand (m³)": 354},
        {"Project Name": "Laguna Cove", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 16, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 345, "Peak Month Demand (m³)": 36},
        {"Project Name": "Laguna Homes", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 56, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 51827, "Peak Month Demand (m³)": 6552},
        {"Project Name": "Cassia Residence", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 193, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 16372, "Peak Month Demand (m³)": 2210},
        {"Project Name": "Beachside", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 184, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 16922, "Peak Month Demand (m³)": 1410},
        {"Project Name": "Lakeside", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 114, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 7757, "Peak Month Demand (m³)": 1058},
        {"Project Name": "Skypark", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 416, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 28017, "Peak Month Demand (m³)": 4047},
        {"Project Name": "ANBR", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 42, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 19326, "Peak Month Demand (m³)": 2300},
        {"Project Name": "ANOV", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 67, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 4788, "Peak Month Demand (m³)": 345},
        {"Project Name": "LVR 1", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 12, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 17641, "Peak Month Demand (m³)": 1789},
        {"Project Name": "LVR 2", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 12, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 23033, "Peak Month Demand (m³)": 3141},
        {"Project Name": "LVR 3", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 13, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 22022, "Peak Month Demand (m³)": 2117},
        {"Project Name": "LVR 4", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 12, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 21164, "Peak Month Demand (m³)": 2137},
        {"Project Name": "LVR 6 + 7", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 19, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 19210, "Peak Month Demand (m³)": 2253},
        {"Project Name": "LVR 8", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 17, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 15101, "Peak Month Demand (m³)": 1800},
        {"Project Name": "LVV", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 36, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 36782, "Peak Month Demand (m³)": 4409},
        {"Project Name": "LVTH 1", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 30, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 23407, "Peak Month Demand (m³)": 2773},
        {"Project Name": "LVTH 2", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 26, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 24996, "Peak Month Demand (m³)": 2469},
        {"Project Name": "LVTH 3 + LVR 5", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 17, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 21377, "Peak Month Demand (m³)": 2877},
        {"Project Name": "LVTH 4", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 8, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 3730, "Peak Month Demand (m³)": 583},
        {"Project Name": "Laguna Parkside (Park 1)", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 251, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 1960, "Peak Month Demand (m³)": 159},
        {"Project Name": "Laguna Park 2 (PR2)", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 61, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 2023, "Peak Month Demand (m³)": 430},
        {"Project Name": "BTGR", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 8, "Shared Pools": 0, "Private Pools": 0, "Annual Demand (m³)": 27862, "Peak Month Demand (m³)": 3183}
    ])

    edited_baseline = st.data_editor(
        default_baseline,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Type": st.column_config.SelectboxColumn("Type", options=["Condo", "Villa"], required=True),
            "Annual Demand (m³)": st.column_config.NumberColumn("Annual Demand (m³)", min_value=0, format="%d"),
            "Peak Month Demand (m³)": st.column_config.NumberColumn("Peak Month (Jan) Demand (m³)", min_value=0, format="%d")
        }
    )

    # --- Core Inference Engine (Calculating Reference Rates) ---
    def extract_rates(df, p_type):
        type_df = df[df['Type'] == p_type]
        rates = {k: {'avg_daily': [], 'peak_daily': []} for k in weights.keys()}
        
        for _, row in type_df.iterrows():
            eq_units = sum(row.get(k, 0) * w for k, w in weights.items())
            if eq_units > 0:
                base_avg_daily = (row['Annual Demand (m³)'] / eq_units) / 365
                base_peak_daily = (row['Peak Month Demand (m³)'] / eq_units) / 31
                for k, w in weights.items():
                    if row.get(k, 0) > 0:
                        rates[k]['avg_daily'].append(base_avg_daily * w)
                        rates[k]['peak_daily'].append(base_peak_daily * w)
                        
        master_rates = {}
        for k in weights.keys():
            master_rates[f"{k} Avg Daily"] = np.mean(rates[k]['avg_daily']) if rates[k]['avg_daily'] else 0.0
            master_rates[f"{k} Peak Daily"] = np.mean(rates[k]['peak_daily']) if rates[k]['peak_daily'] else 0.0
            
        return master_rates

    condo_rates = extract_rates(edited_baseline, "Condo")
    villa_rates = extract_rates(edited_baseline, "Villa")

    st.divider()

    # --- STEP 2: Future Project Input ---
    st.header("Step 2: Future Project Water Demand Simulation")
    st.markdown("Pre-loaded with projects to 2050. The engine uses rates inferred from Step 1.")

    future_2026_2030 = [
        {"Year": 2026, "Project Name": "Laguna Seashore", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 50, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2026, "Project Name": "Skypark 2", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 398, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2026, "Project Name": "Banyan Tree Oceanfront (Villas)", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 10, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2026, "Project Name": "Sea View Residences", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 40, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2026, "Project Name": "Beach Terrace", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 15, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lakeland Waterfront Condo - 4 Storey", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 95, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lakeland Waterfront Condo - 7 Storey", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 232, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lakeland Villa", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 14, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lagoon Pool Villa 3", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 5, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lagoon Pool Villa 4", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 3, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2027, "Project Name": "Lagoon Pool Villa 5", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 4, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2028, "Project Name": "Lakeside 2", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 159, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2028, "Project Name": "Bayside", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 237, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2028, "Project Name": "Oceanus", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 16, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2029, "Project Name": "Skypark Elara", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 234, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2029, "Project Name": "Garrya Residences 1", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 25, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2029, "Project Name": "Garrya Residences 2", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 9, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2029, "Project Name": "Garrya Hotel", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 154, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2029, "Project Name": "Angsana Golf Residences", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 106, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2030, "Project Name": "Laguna Golf Residences 1", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 179, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2030, "Project Name": "Laguna Golf Residences 2", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 181, "Shared Pools": 0, "Private Pools": 0},
        {"Year": 2030, "Project Name": "Lotus Lake Condo", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 319, "Shared Pools": 0, "Private Pools": 0}
    ]

    future_planning = []
    for y in range(2031, 2051):
        future_planning.append({"Year": y, "Project Name": "Planning 1", "Type": "Condo", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 340, "Shared Pools": 0, "Private Pools": 0})
        future_planning.append({"Year": y, "Project Name": "Planning 2", "Type": "Villa", "1-Bed": 0, "2-Bed": 0, "3-Bed": 0, "4+ Bed": 0, "Unspecified Units": 60, "Shared Pools": 0, "Private Pools": 0})

    default_future = pd.DataFrame(future_2026_2030 + future_planning)

    edited_future = st.data_editor(
        default_future,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Type": st.column_config.SelectboxColumn("Type", options=["Condo", "Villa"], required=True),
            "Year": st.column_config.NumberColumn("Year", format="%d")
        }
    )

    # --- Future Projection Calculations ---
    results_list = []

    for _, row in edited_future.iterrows():
        p_type = row['Type']
        rates = condo_rates if p_type == "Condo" else villa_rates
        
        avg_daily_demand = sum(row.get(k, 0) * rates[f"{k} Avg Daily"] for k in weights.keys())
        peak_daily_demand = sum(row.get(k, 0) * rates[f"{k} Peak Daily"] for k in weights.keys())
        
        total_units = sum(row.get(k, 0) for k in ['1-Bed', '2-Bed', '3-Bed', '4+ Bed', 'Unspecified Units'])
        
        results_list.append({
            "Year": row['Year'],
            "Project Name": row['Project Name'],
            "Type": row['Type'],
            "Total Units": total_units,
            "Average Daily Demand (m³/day)": avg_daily_demand,
            "Peak Daily Demand (m³/day)": peak_daily_demand,
            "Average Month Demand (m³)": avg_daily_demand * (365/12),
            "Peak Month Demand (m³)": peak_daily_demand * 31,
            "Average Annual Demand (m³)": avg_daily_demand * 365,
            "Peak Annual Demand (m³)": peak_daily_demand * 365
        })

    df_results = pd.DataFrame(results_list)

    # --- Cumulative Totals Math ---
    if not df_results.empty:
        df_yearly_new = df_results.groupby('Year')[['Average Daily Demand (m³/day)', 'Peak Daily Demand (m³/day)']].sum().reset_index()
        df_yearly_new = df_yearly_new.sort_values('Year')
        
        # Calculate cumulative sums (NEW PROJECTS ONLY - Baseline Excluded)
        df_yearly_new['Cumulative New Avg Daily Demand (m³/day)'] = df_yearly_new['Average Daily Demand (m³/day)'].cumsum()
        df_yearly_new['Cumulative New Peak Daily Demand (m³/day)'] = df_yearly_new['Peak Daily Demand (m³/day)'].cumsum()

    # --- Dashboard Display ---
    st.header("Step 3: Output & Visualizations (Method B)")

    if not df_results.empty:
        tab1, tab2, tab3 = st.tabs(["🗄️ Individual Project Projections", "📈 Cumulative Yearly Totals (New Projects)", "📊 Type Breakdown"])

        with tab1:
            st.markdown("**Simulated Project Data (Individual Future Developments Only)**")
            st.dataframe(df_results.style.format({
                "Average Daily Demand (m³/day)": "{:,.1f}",
                "Peak Daily Demand (m³/day)": "{:,.1f}",
                "Average Month Demand (m³)": "{:,.1f}",
                "Peak Month Demand (m³)": "{:,.1f}",
                "Average Annual Demand (m³)": "{:,.1f}",
                "Peak Annual Demand (m³)": "{:,.1f}"
            }), use_container_width=True)

        with tab2:
            st.markdown("**Cumulative Demand by Year (New Projects Only - Excluding Existing Baseline)**")
            
            df_display_cum = df_yearly_new[['Year', 'Cumulative New Avg Daily Demand (m³/day)', 'Cumulative New Peak Daily Demand (m³/day)']]
            st.dataframe(df_display_cum.style.format({
                "Cumulative New Avg Daily Demand (m³/day)": "{:,.1f}",
                "Cumulative New Peak Daily Demand (m³/day)": "{:,.1f}"
            }), use_container_width=True)
            
            fig_total = go.Figure()
            fig_total.add_trace(go.Bar(x=df_yearly_new["Year"], y=df_yearly_new["Cumulative New Avg Daily Demand (m³/day)"], name="New Avg Daily (m³/day)", marker_color='#3498db'))
            fig_total.add_trace(go.Scatter(x=df_yearly_new["Year"], y=df_yearly_new["Cumulative New Peak Daily Demand (m³/day)"], name="New Peak Daily (m³/day)", mode='lines+markers', line=dict(color='#e74c3c', width=3)))
            fig_total.update_layout(title="Cumulative Daily Water Demand (New Future Projects Only)", yaxis_title="Daily Flow (m³/day)", barmode='group', xaxis_type='category')
            st.plotly_chart(fig_total, use_container_width=True)

        with tab3:
            df_agg_type = df_results.groupby(['Year', 'Type'])[['Average Daily Demand (m³/day)', 'Peak Daily Demand (m³/day)']].sum().reset_index()
            if not df_agg_type.empty:
                fig_type = px.bar(df_agg_type, x="Year", y="Average Daily Demand (m³/day)", color="Type", 
                                  title="New Average Daily Demand by Asset Type", barmode="stack", text_auto='.1f')
                fig_type.update_layout(xaxis_type='category')
                st.plotly_chart(fig_type, use_container_width=True)

        st.divider()

        # --- Export Functionality ---
        st.header("📥 Export Projections")
        col_export1, col_export2 = st.columns(2)

        csv_data = df_results.to_csv(index=False).encode('utf-8')
        col_export1.download_button("📄 Download Individual Projects (CSV)", data=csv_data, file_name="Individual_Project_Demands_MethodB.csv", mime="text/csv", use_container_width=True)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Updated Export to only export the New Cumulative Totals
            df_yearly_new[['Year', 'Cumulative New Avg Daily Demand (m³/day)', 'Cumulative New Peak Daily Demand (m³/day)']].to_excel(writer, index=False, sheet_name='Cumulative Totals (New)')
            df_results.to_excel(writer, index=False, sheet_name='Individual Demands')
            edited_baseline.to_excel(writer, index=False, sheet_name='Baseline Inputs')
        excel_data = excel_buffer.getvalue()

        col_export2.download_button("📊 Download Full Report (Excel)", data=excel_data, file_name="Complete_Water_Demand_Report_MethodB.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)

    else:
        st.info("Add projects to the Future Data Input table to generate projections.")
