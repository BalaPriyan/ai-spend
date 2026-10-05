"""
AI Spends Tracker & Analyzer - Streamlit Interactive Dashboard
A clean, executive analytics and cost optimization interface.
"""

import sys
import os
from datetime import datetime, date, time
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Ensure project root is in sys.path for clean backend module imports
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.config import DEFAULT_RATE_CARDS, DEFAULT_BUDGETS
from backend.database import SessionLocal, init_db, SpendEvent, ModelRateCard, Budget
from backend.seeder import seed_database, insert_single_event
from backend.pricing_engine import PricingEngine
from backend.analytics_engine import AnalyticsEngine
from backend.budget_service import BudgetService

# Configure page settings without emojis
st.set_page_config(
    page_title="AI Spends Tracker & Analyzer",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling for Sleek Dark Glassmorphism Theme
st.markdown("""
<style>
    /* Metric Card Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.01));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    }
    div[data-testid="stMetric"]:hover {
        border-color: rgba(59, 130, 246, 0.4);
        transform: translateY(-2px);
        transition: all 0.2s ease-in-out;
    }
    .metric-sub {
        font-size: 0.82rem;
        color: #94a3b8;
        margin-top: 4px;
    }
    .badge-ok {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .badge-warn {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }
    .badge-danger {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid rgba(239, 68, 68, 0.3);
    }
    .rec-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.7));
        border: 1px solid rgba(59, 130, 246, 0.25);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize database and seed sample data on first run
@st.cache_resource
def bootstrap_database():
    seed_database()
    return True

bootstrap_database()


# -------------------------------------------------------------
# Sidebar: Controls & Filters
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### AI Spends Tracker")
    st.caption("Centralized AI Token & Cost Intelligence")

    db = SessionLocal()
    try:
        projects = ["All"] + sorted([p[0] for p in db.query(SpendEvent.project_name).distinct().all()])
    finally:
        db.close()

    selected_project = st.selectbox("Project Workspace", projects, index=0)
    selected_env = st.selectbox("Environment", ["All", "production", "staging", "development"], index=0)
    time_window_days = st.slider("Time Range (Days)", min_value=7, max_value=30, value=30, step=1)

    st.markdown("---")
    st.markdown("#### Quick Simulation")
    if st.button("Inject 5 Simulated AI Calls", use_container_width=True):
        import random
        sim_models = ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash", "deepseek-chat"]
        for _ in range(5):
            m = random.choice(sim_models)
            insert_single_event(
                project_name=random.choice(["CustomerSupportBot", "DocSearchRAG", "CodeGenAssistant"]),
                environment="production",
                provider=DEFAULT_RATE_CARDS[m]["provider"],
                model_id=m,
                prompt_tokens=random.randint(600, 2800),
                completion_tokens=random.randint(150, 700),
                cached_tokens=random.choice([0, 500]),
                latency_ms=random.randint(280, 950),
                feature_tag="live_agent_chat"
            )
        st.success("Injected 5 events. Dashboard refreshed.")
        st.rerun()

    st.markdown("---")
    st.markdown("**System Status**: Active")
    st.markdown("**Storage Engine**: SQLite Embedded")
    st.markdown("**Reverse Proxy**: `/v1/chat/completions`")


# -------------------------------------------------------------
# Main Application Content
# -------------------------------------------------------------
st.title("AI Spends Tracker & Cost Analyzer")
st.markdown("Real-time token attribution, multi-model cost monitoring, and AI arbitrage engine.")

tab_overview, tab_data, tab_arbitrage, tab_models, tab_budgets, tab_proxy = st.tabs([
    "Spend Overview",
    "Data Management (Add & List)",
    "Cost Arbitrage & Savings",
    "Model Economics",
    "Budgets & Guardrails",
    "AI Proxy Simulator"
])

db = SessionLocal()

# -------------------------------------------------------------
# TAB 1: SPEND OVERVIEW
# -------------------------------------------------------------
with tab_overview:
    summary = AnalyticsEngine.get_summary(db, project_name=selected_project, environment=selected_env, days=time_window_days)
    
    # 4 Executive KPI Cards
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total AI Spend",
            value=f"${summary['total_spend_usd']:,.2f}",
            delta=f"{summary['total_requests']:,} calls"
        )
        st.markdown(f"<div class='metric-sub'>Avg Latency: <b>{summary['avg_latency_ms']:.0f} ms</b></div>", unsafe_allow_html=True)

    with col2:
        st.metric(
            label="Projected Monthly Run-Rate",
            value=f"${summary['projected_month_end_usd']:,.2f}",
            delta="30-day run rate"
        )
        st.markdown(f"<div class='metric-sub'>Active Models: <b>{summary['active_models_count']}</b> across <b>{summary['active_projects_count']}</b> projects</div>", unsafe_allow_html=True)

    with col3:
        st.metric(
            label="Total Tokens Consumed",
            value=f"{summary['total_tokens']:,}",
            delta=f"{summary['total_requests']:,} requests"
        )
        st.markdown("<div class='metric-sub'>Prompt, completion & reasoning</div>", unsafe_allow_html=True)

    with col4:
        st.metric(
            label="Cache Savings",
            value=f"${summary['cache_savings_usd']:,.2f}",
            delta=f"{summary['cache_hit_rate_pct']:.1f}% hit rate",
            delta_color="normal"
        )
        st.markdown("<div class='metric-sub'>Prompt prefix caching discount</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Time-Series Charts
    timeseries_data = AnalyticsEngine.get_timeseries(db, project_name=selected_project, environment=selected_env, days=time_window_days)
    df_ts = pd.DataFrame(timeseries_data)

    if not df_ts.empty:
        col_chart1, col_chart2 = st.columns([3, 2])
        
        with col_chart1:
            st.subheader("Daily AI Spend by Provider (USD)")
            fig_spend = px.bar(
                df_ts,
                x="date",
                y=["openai", "anthropic", "google", "deepseek", "other"],
                labels={"value": "Spend ($)", "date": "Date", "variable": "Provider"},
                title=f"Daily Spend Trajectory ({selected_project})",
                color_discrete_map={
                    "openai": "#10a37f",
                    "anthropic": "#d97706",
                    "google": "#3b82f6",
                    "deepseek": "#8b5cf6",
                    "other": "#6b7280"
                }
            )
            fig_spend.update_layout(
                barmode="stack",
                margin=dict(l=20, r=20, t=40, b=20),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_spend, use_container_width=True)

        with col_chart2:
            st.subheader("Daily Token Volume")
            fig_tokens = px.area(
                df_ts,
                x="date",
                y="tokens",
                labels={"tokens": "Tokens", "date": "Date"},
                title="Total Tokens Processed",
                color_discrete_sequence=["#38bdf8"]
            )
            fig_tokens.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_tokens, use_container_width=True)


# -------------------------------------------------------------
# TAB 2: DATA MANAGEMENT (ADD NEW DATA & LIST ALL DATA)
# -------------------------------------------------------------
with tab_data:
    st.subheader("Data Management")
    st.markdown("Inspect all recorded telemetry spend events or record new entries manually.")

    subtab_list, subtab_add = st.tabs(["List All Data", "Add New Data"])

    # --- Subtab: List All Data ---
    with subtab_list:
        col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 1])
        with col_f1:
            filter_proj = st.selectbox("Filter by Project", ["All"] + sorted([p[0] for p in db.query(SpendEvent.project_name).distinct().all()]), key="list_proj")
        with col_f2:
            filter_env = st.selectbox("Filter by Environment", ["All", "production", "staging", "development"], key="list_env")
        with col_f3:
            filter_model = st.selectbox("Filter by Model", ["All"] + sorted([m[0] for m in db.query(SpendEvent.model_id).distinct().all()]), key="list_model")
        with col_f4:
            row_limit = st.selectbox("Display Limit", [50, 100, 250, 500, "All"], index=1)

        # Build Query
        query = db.query(SpendEvent).order_by(SpendEvent.timestamp.desc())
        if filter_proj != "All":
            query = query.filter(SpendEvent.project_name == filter_proj)
        if filter_env != "All":
            query = query.filter(SpendEvent.environment == filter_env)
        if filter_model != "All":
            query = query.filter(SpendEvent.model_id == filter_model)

        total_matching = query.count()
        if row_limit != "All":
            events = query.limit(int(row_limit)).all()
        else:
            events = query.all()

        st.caption(f"Showing **{len(events)}** of **{total_matching}** total records.")

        if events:
            table_records = []
            for e in events:
                table_records.append({
                    "ID": e.id,
                    "Timestamp (UTC)": e.timestamp.strftime("%Y-%m-%d %H:%M:%S") if e.timestamp else "",
                    "Project": e.project_name,
                    "Environment": e.environment,
                    "Provider": e.provider,
                    "Model": e.model_id,
                    "Prompt Tokens": e.prompt_tokens or 0,
                    "Completion Tokens": e.completion_tokens or 0,
                    "Cached Tokens": e.cached_tokens or 0,
                    "Total Tokens": e.total_tokens or 0,
                    "Total Cost ($)": f"${(e.total_cost_usd or 0.0):.6f}",
                    "Latency (ms)": e.latency_ms or 0,
                    "Status": e.http_status_code or 200,
                    "Feature Tag": e.feature_tag or "general",
                    "User": e.user_identifier or "-"
                })
            df_table = pd.DataFrame(table_records)
            st.dataframe(df_table, use_container_width=True, hide_index=True)

            # Export to CSV
            csv_data = df_table.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download Filtered Data (CSV)",
                data=csv_data,
                file_name=f"ai_spends_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=False
            )
        else:
            st.info("No spend events found matching the specified filters.")

    # --- Subtab: Add New Data ---
    with subtab_add:
        st.markdown("#### Record New AI Spend Telemetry Event")
        st.markdown("Enter spend and token telemetry details. The pricing engine will calculate the exact cost per rate card.")

        with st.form("manual_add_event_form", clear_on_submit=False):
            c_a1, c_a2 = st.columns(2)
            with c_a1:
                # Project Name
                known_projs = sorted([p[0] for p in db.query(SpendEvent.project_name).distinct().all()])
                p_choice = st.selectbox("Select Existing Project", ["(Create New)"] + known_projs)
                if p_choice == "(Create New)":
                    new_proj_name = st.text_input("New Project Name", value="NewAiService")
                    final_project = new_proj_name.strip() if new_proj_name.strip() else "NewAiService"
                else:
                    final_project = p_choice

                new_env = st.selectbox("Environment", ["production", "staging", "development"], index=0)
                
                # Model selection
                available_models = list(DEFAULT_RATE_CARDS.keys())
                selected_model_id = st.selectbox("Model", available_models, index=0)
                selected_provider = DEFAULT_RATE_CARDS[selected_model_id]["provider"]
                st.caption(f"Provider: **{selected_provider.upper()}** | Tier: **{DEFAULT_RATE_CARDS[selected_model_id]['tier']}**")

                new_feature_tag = st.text_input("Feature Tag", value="customer_chat")
                new_user_id = st.text_input("User / Client Identifier (Optional)", value="user_demo")

            with c_a2:
                new_prompt_tokens = st.number_input("Prompt Tokens", min_value=0, max_value=1_000_000, value=1200, step=50)
                new_comp_tokens = st.number_input("Completion Tokens", min_value=0, max_value=500_000, value=300, step=50)
                new_cached_tokens = st.number_input("Cached Prompt Tokens", min_value=0, max_value=1_000_000, value=0, step=50)
                new_reasoning_tokens = st.number_input("Reasoning Tokens (Optional)", min_value=0, max_value=500_000, value=0, step=50)
                new_latency = st.number_input("Latency (ms)", min_value=0, max_value=60_000, value=450, step=25)
                
                col_d1, col_d2 = st.columns(2)
                with col_d1:
                    ev_date = st.date_input("Event Date", value=date.today())
                with col_d2:
                    ev_time = st.time_input("Event Time", value=datetime.utcnow().time())

            submit_new_event = st.form_submit_button("Save Spend Event", use_container_width=True)
            if submit_new_event:
                if not final_project:
                    st.error("Project name cannot be empty.")
                else:
                    event_dt = datetime.combine(ev_date, ev_time)
                    ev = insert_single_event(
                        project_name=final_project,
                        environment=new_env,
                        provider=selected_provider,
                        model_id=selected_model_id,
                        prompt_tokens=int(new_prompt_tokens),
                        completion_tokens=int(new_comp_tokens),
                        cached_tokens=int(new_cached_tokens),
                        reasoning_tokens=int(new_reasoning_tokens),
                        latency_ms=int(new_latency),
                        feature_tag=new_feature_tag.strip() or "general",
                        http_status_code=200,
                        user_identifier=new_user_id.strip() if new_user_id else None,
                        timestamp=event_dt
                    )
                    st.success(
                        f"Event #{ev.id} successfully recorded! "
                        f"Calculated Total Cost: ${ev.total_cost_usd:.6f} USD "
                        f"(Prompt: ${ev.prompt_cost_usd:.6f}, Comp: ${ev.completion_cost_usd:.6f})."
                    )
                    st.rerun()


# -------------------------------------------------------------
# TAB 3: ARBITRAGE & COST SAVINGS
# -------------------------------------------------------------
with tab_arbitrage:
    st.subheader("Intelligent Cost Arbitrage Recommendations")
    st.markdown("Our analyzer inspects your token profiles, model tiers, and latency metrics to flag immediate optimization targets.")

    recs = AnalyticsEngine.get_arbitrage_recommendations(db, days=time_window_days)
    total_potential_savings = sum(r["estimated_monthly_savings_usd"] for r in recs)

    col_sav1, col_sav2 = st.columns([1, 2])
    with col_sav1:
        st.metric(
            label="Total Potential Monthly Savings",
            value=f"${total_potential_savings:,.2f}/mo",
            delta=f"{len(recs)} optimization targets detected",
            delta_color="normal"
        )
    with col_sav2:
        st.info("Note: Over 65% of enterprise LLM spend typically goes to frontier models (GPT-4o / Claude 3.5 Sonnet) on queries that economy models (Gemini 1.5 Flash / Claude 3.5 Haiku) execute with comparable accuracy at 80% lower cost.")

    st.markdown("### Actionable Recommendations")
    if recs:
        for r in recs:
            with st.container():
                st.markdown(f"""
                <div class="rec-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="margin: 0; color: #60a5fa;">{r['title']}</h4>
                        <span class="badge-ok">Save ~${r['estimated_monthly_savings_usd']:,.2f}/mo (-{r['savings_percentage']}%)</span>
                    </div>
                    <p style="color: #cbd5e1; margin-bottom: 12px;">{r['description']}</p>
                    <div style="display: flex; gap: 24px; font-size: 0.85rem; color: #94a3b8;">
                        <div>Current: <b style="color: #f87171;">{r['current_model']}</b></div>
                        <div>Recommended: <b style="color: #34d399;">{r['suggested_model']}</b></div>
                        <div>Type: <b>{r['reasoning_type']}</b></div>
                        <div>Impact: <b>{r['impact_level']}</b></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No active arbitrage targets found for the selected time range. Your spend profile is well optimized.")


# -------------------------------------------------------------
# TAB 4: MODEL ECONOMICS
# -------------------------------------------------------------
with tab_models:
    st.subheader("Model Economics & Volume Breakdown")
    breakdown = AnalyticsEngine.get_model_breakdown(db, project_name=selected_project, days=time_window_days)
    
    if breakdown:
        df_models = pd.DataFrame(breakdown)
        
        col_m1, col_m2 = st.columns([3, 2])
        with col_m1:
            st.markdown("#### Performance & Spend Table")
            display_df = df_models[[
                "display_name", "provider", "tier", "request_count", 
                "total_tokens", "total_cost_usd", "percentage_of_total", "avg_latency_ms"
            ]].copy()
            display_df.columns = [
                "Model", "Provider", "Tier", "Requests", 
                "Tokens", "Spend ($)", "Share (%)", "Avg Latency (ms)"
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        with col_m2:
            st.markdown("#### Spend Distribution by Model")
            fig_pie = px.pie(
                df_models,
                values="total_cost_usd",
                names="display_name",
                hole=0.45,
                color_discrete_sequence=px.colors.qualitative.Prism
            )
            fig_pie.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")
    st.subheader("Active Model Rate Cards (USD per 1M Tokens)")
    rate_cards = db.query(ModelRateCard).all()
    if rate_cards:
        cards_data = [{
            "Model": c.display_name,
            "Model ID": c.model_id,
            "Provider": c.provider.upper(),
            "Tier": c.tier.capitalize(),
            "Prompt ($/1M)": f"${c.prompt_price_per_million:.2f}",
            "Completion ($/1M)": f"${c.completion_price_per_million:.2f}",
            "Cached Prompt ($/1M)": f"${c.cached_prompt_price_per_million:.4f}",
            "Reasoning ($/1M)": f"${c.reasoning_price_per_million:.2f}",
        } for c in rate_cards]
        st.dataframe(pd.DataFrame(cards_data), use_container_width=True, hide_index=True)


# -------------------------------------------------------------
# TAB 5: BUDGETS & GUARDRAILS
# -------------------------------------------------------------
with tab_budgets:
    st.subheader("Project Budgets & Threshold Guardrails")
    st.markdown("Track monthly spend quotas, automated warning thresholds, and hard throttle caps.")

    budgets = BudgetService.get_all_budgets(db)
    
    for b in budgets:
        col_b1, col_b2, col_b3 = st.columns([2, 3, 1])
        with col_b1:
            st.markdown(f"**{b['project_name']}**")
            badge_class = "badge-ok" if b['status'] == "NORMAL" else ("badge-warn" if b['status'] == "WARNING" else "badge-danger")
            st.markdown(f"<span class='{badge_class}'>{b['status']}</span> &nbsp; Limit: <b>${b['monthly_limit_usd']:,.2f}</b>", unsafe_allow_html=True)
            if b['hard_cap_enabled']:
                st.caption("[Hard Cap Enabled]")

        with col_b2:
            pct = min(100.0, b['percent_used']) / 100.0
            st.progress(pct)
            st.caption(f"Spent: ${b['current_spend_usd']:,.2f} of ${b['monthly_limit_usd']:,.2f} ({b['percent_used']}%)")

        with col_b3:
            st.metric(label="Current Usage", value=f"{b['percent_used']}%")

        st.markdown("<hr style='margin: 8px 0; opacity: 0.15;'/>", unsafe_allow_html=True)


# -------------------------------------------------------------
# TAB 6: AI REVERSE PROXY & SIMULATOR
# -------------------------------------------------------------
with tab_proxy:
    st.subheader("AI Reverse Proxy Simulator (/v1/chat/completions)")
    st.markdown("Test the transparent OpenAI-compatible proxy that automatically tracks token consumption and micro-cent expenditure.")

    with st.form("proxy_form"):
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            p_model = st.selectbox("Proxy Model Target", ["gpt-4o", "claude-3-5-sonnet", "gemini-1.5-flash", "deepseek-chat"])
            p_proj = st.selectbox("Attribution Project", ["ProxyGateway", "CustomerSupportBot", "DocSearchRAG", "CodeGenAssistant"])
        with col_p2:
            p_env = st.selectbox("Environment Target", ["production", "staging", "development"])
            p_feature = st.text_input("Feature Tag", value="proxy_interactive_chat")

        p_prompt = st.text_area("User Message", "Provide a summary of AI token economics and strategies for caching repeated system prompts.")
        
        p_submit = st.form_submit_button("Send Request via Proxy", use_container_width=True)
        if p_submit:
            card = PricingEngine.get_rate_card(db, p_model)
            est_prompt = max(12, len(p_prompt.split()) * 4 // 3)
            est_comp = 95
            est_cached = int(est_prompt * 0.5) if len(p_prompt) > 150 else 0
            
            ev = insert_single_event(
                project_name=p_proj,
                environment=p_env,
                provider=card["provider"],
                model_id=p_model,
                prompt_tokens=est_prompt,
                completion_tokens=est_comp,
                cached_tokens=est_cached,
                latency_ms=360,
                feature_tag=p_feature
            )
            st.markdown(f"**Proxy Response** (Model: `{p_model}`):")
            st.code(f"""{{
  "id": "chatcmpl-{ev.id}",
  "object": "chat.completion",
  "model": "{p_model}",
  "usage": {{
    "prompt_tokens": {est_prompt},
    "completion_tokens": {est_comp},
    "total_tokens": {est_prompt + est_comp},
    "cached_tokens": {est_cached}
  }},
  "_spend_metadata": {{
    "total_cost_usd": {ev.total_cost_usd:.6f},
    "prompt_cost_usd": {ev.prompt_cost_usd:.6f},
    "completion_cost_usd": {ev.completion_cost_usd:.6f},
    "latency_ms": 360
  }}
}}""", language="json")
            st.success(f"Tracked via AI Proxy! Cost: ${ev.total_cost_usd:.6f} USD recorded to database.")

db.close()
