#!/usr/bin/env python3
"""
bAIt-Chat Frontend - QServer-integrated Streamlit interface
"""

import json
import sys
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# Configure page
st.set_page_config(page_title="bAIt-Chat", page_icon="🔬", layout="wide")

# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "devices" not in st.session_state:
    st.session_state.devices = {}
if "plans" not in st.session_state:
    st.session_state.plans = {}


# Sidebar for configuration
st.sidebar.header("🔌 Connection Configuration")
model_address = st.sidebar.text_input(
    "Model Address", "http://localhost:1234", help="Enter the LLM model URL (LMStudio, Ollama, etc.)"
)
backend_url = st.sidebar.text_input("Backend URL", "http://localhost:8000")
qserver_url = st.sidebar.text_input(
    "QServer Address", "http://localhost:60610", help="Enter the QServer URL"
)

# QServer status section
st.sidebar.markdown("### 🖥️ QServer Status")
try:
    qserver_status_response = requests.get(f"{backend_url}/qserver/status", timeout=5)
    if qserver_status_response.status_code == 200:
        status_data = qserver_status_response.json()
        st.sidebar.success(f"✅ QServer: {status_data['manager_state']}")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.sidebar.metric("Devices", status_data.get("devices_in_queue", 0))
        with col2:
            st.sidebar.metric("Plans", status_data.get("plans_in_queue", 0))
    else:
        st.sidebar.error("❌ QServer not available")
except Exception as e:
    st.sidebar.warning(f"⚠️ QServer status unknown")

# Connection status and data fetching
if st.sidebar.button("Connect to QServer") or st.sidebar.button("🔄 Refresh Data"):
    with st.sidebar:
        with st.spinner("Connecting..."):
            # Test backend connection
            try:
                health_response = requests.get(f"{backend_url}/health", timeout=5)
                if health_response.status_code == 200:
                    st.success("✅ Backend connected")
                else:
                    st.error("❌ Backend not responding")
            except Exception as e:
                st.error(f"❌ Backend failed: {str(e)}")

            # Fetch devices from QServer via backend
            try:
                devices_response = requests.get(f"{backend_url}/devices", timeout=10)
                if devices_response.status_code == 200:
                    st.session_state.devices = devices_response.json().get("devices", {})
                    device_count = sum(
                        len(category) for category in st.session_state.devices.values()
                    )
                    st.success(f"✅ Loaded {device_count} devices")
                else:
                    st.warning("⚠️ Could not load devices")
                    st.session_state.devices = {}
            except Exception as e:
                st.warning(f"⚠️ Devices failed: {str(e)}")
                st.session_state.devices = {}

            # Fetch plans from QServer via backend
            try:
                plans_response = requests.get(f"{backend_url}/plans", timeout=10)
                if plans_response.status_code == 200:
                    plans_data = plans_response.json()
                    st.session_state.plans = plans_data.get("plans", {})
                    st.success(f"✅ Loaded {len(st.session_state.plans)} plans")
                else:
                    st.warning("⚠️ Could not load plans")
                    # Fallback to common plans
                    st.session_state.plans = {
                        "scan": {"description": "Continuous scan of a motor"},
                        "count": {"description": "Take measurements at current position"},
                        "list_scan": {"description": "Scan through a list of positions"},
                        "grid_scan": {"description": "2D grid scan with two motors"},
                        "rel_scan": {"description": "Relative scan from current position"},
                    }
            except Exception as e:
                st.warning(f"⚠️ Plans failed: {str(e)}")
                st.session_state.plans = {
                    "scan": {"description": "Continuous scan of a motor"},
                    "count": {"description": "Take measurements at current position"},
                    "list_scan": {"description": "Scan through a list of positions"},
                }

# Sidebar status
if st.session_state.devices or st.session_state.plans:
    st.sidebar.markdown("### 📊 Status")
    device_count = (
        sum(len(category) for category in st.session_state.devices.values())
        if st.session_state.devices
        else 0
    )
    plan_count = len(st.session_state.plans)
    st.sidebar.metric("Devices", device_count)
    st.sidebar.metric("Plans", plan_count)

# Main content - Tabbed interface
main_tab1, main_tab2 = st.tabs(["💬 Chat", "🔬 Instrument Info"])

with main_tab1:
    st.header("💬 AI Assistant Chat")
    
    # Display chat history
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask about beamline operations, scan plans, or devices..."):
        # Add user message to chat
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Use the new backend chat endpoint
                    response = requests.post(
                        f"{backend_url}/chat",
                        json={"message": prompt, "model_url": model_address},
                        timeout=30
                    )

                    if response.status_code == 200:
                        result = response.json()
                        ai_response = result.get("response", "I couldn't generate a response.")
                        st.write(ai_response)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": ai_response}
                        )
                    else:
                        error_msg = f"Chat API error: {response.status_code}"
                        if response.status_code == 500:
                            error_detail = response.json().get("detail", "Unknown server error")
                            error_msg += f" - {error_detail}"
                        st.error(error_msg)
                        st.session_state.chat_history.append(
                            {"role": "assistant", "content": error_msg}
                        )
                except Exception as e:
                    error_msg = f"Connection error: {str(e)}"
                    st.error(error_msg)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})

    # Clear chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()

with main_tab2:
    st.header("🔬 Instrument Information")
    
    # Create tabs for different aspects of introspection
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Status", "🔧 Devices", "📋 Plans", "📈 History"])

    with tab1:
        st.subheader("Instrument Status")
        if st.button("🔄 Refresh Status"):
            try:
                response = requests.get(f"{backend_url}/instrument/status", timeout=10)
                if response.status_code == 200:
                    status_data = response.json()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric(
                            "QServer State",
                            status_data["qserver_status"].get("manager_state", "Unknown"),
                        )
                        st.metric(
                            "Environment", "Open" if status_data.get("environment_info") else "Closed"
                        )

                    with col2:
                        st.metric("Instrument", status_data.get("instrument_name", "Unknown"))

                    # Show detailed QServer status
                    if "qserver_status" in status_data:
                        st.json(status_data["qserver_status"])
                else:
                    st.error("Could not fetch instrument status")
            except Exception as e:
                st.error(f"Error fetching status: {str(e)}")

    with tab2:
        st.subheader("Detailed Device Information")
        if st.button("🔄 Refresh Devices"):
            try:
                response = requests.get(f"{backend_url}/instrument/devices/detailed", timeout=10)
                if response.status_code == 200:
                    devices_data = response.json()

                    if "error" in devices_data:
                        st.error(devices_data["error"])
                    else:
                        devices = devices_data.get("devices", [])
                        categories = devices_data.get("categories", {})

                        # Show device summary
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Devices", devices_data.get("total_count", 0))
                        with col2:
                            st.metric("Motors", categories.get("motors", 0))
                        with col3:
                            st.metric("Detectors", categories.get("detectors", 0))

                        # Device details table
                        if devices:
                            device_df_data = []
                            for device in devices:
                                device_df_data.append(
                                {
                                    "Name": device["name"],
                                    "Category": device["category"],
                                    "Class": device["class"],
                                    "Description": device["description"],
                                    "Status": device.get("current_status", "unknown"),
                                }
                            )

                            st.dataframe(device_df_data, use_container_width=True)

                            # Expandable device details
                            for device in devices:
                                with st.expander(f"🔧 {device['name']} Details"):
                                    st.write(f"**Class:** {device['class']}")
                                    st.write(f"**Module:** {device['module']}")
                                    st.write(f"**Category:** {device['category']}")
                                    st.write(f"**Description:** {device['description']}")

                                    if device.get("read_attrs"):
                                        st.write(
                                            f"**Read Attributes:** {', '.join(device['read_attrs'])}"
                                        )
                                    if device.get("configuration_attrs"):
                                        st.write(
                                            f"**Config Attributes:** {', '.join(device['configuration_attrs'])}"
                                        )
                else:
                    st.error("Could not fetch device details")
            except Exception as e:
                st.error(f"Error fetching devices: {str(e)}")

    with tab3:
        st.subheader("Detailed Plan Information")

    # Add sub-tabs for better organization
    plan_tab1, plan_tab2, plan_tab3 = st.tabs(["📋 All Plans", "🎯 Recommendations", "📊 Analysis"])

    with plan_tab1:
        if st.button("🔄 Refresh Plans"):
            try:
                response = requests.get(f"{backend_url}/instrument/plans/detailed", timeout=10)
                if response.status_code == 200:
                    plans_data = response.json()

                    if "error" in plans_data:
                        st.error(plans_data["error"])
                    else:
                        plans = plans_data.get("plans", [])
                        categories = plans_data.get("categories", {})
                        analysis_summary = plans_data.get("analysis_summary", {})

                        # Show plan summary
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Total Plans", plans_data.get("total_count", 0))
                        with col2:
                            st.metric("Scan Plans", categories.get("scans", 0))
                        with col3:
                            st.metric(
                                "Low Complexity",
                                analysis_summary.get("complexity_breakdown", {}).get("low", 0),
                            )
                        with col4:
                            st.metric(
                                "High Complexity",
                                analysis_summary.get("complexity_breakdown", {}).get("high", 0),
                            )

                        # Filter controls
                        col1, col2 = st.columns(2)
                        with col1:
                            complexity_filter = st.selectbox(
                                "Filter by Complexity", ["All", "low", "medium", "high"]
                            )
                        with col2:
                            category_filter = st.selectbox(
                                "Filter by Category", ["All"] + list(categories.keys())
                            )

                        # Plan details
                        if plans:
                            filtered_plans = plans
                            if complexity_filter != "All":
                                filtered_plans = [
                                    p
                                    for p in filtered_plans
                                    if p.get("complexity") == complexity_filter
                                ]
                            if category_filter != "All":
                                filtered_plans = [
                                    p
                                    for p in filtered_plans
                                    if p.get("category") == category_filter
                                ]

                            for plan in filtered_plans:
                                complexity_color = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(
                                    plan.get("complexity", "low"), "⚪"
                                )
                                with st.expander(
                                    f"📋 {plan['name']} ({plan['category']}) {complexity_color}"
                                ):
                                    st.write(f"**Description:** {plan['description']}")
                                    st.write(f"**Module:** {plan['module']}")
                                    st.write(f"**Example Usage:** `{plan['example_usage']}`")
                                    st.write(
                                        f"**Complexity:** {plan.get('complexity', 'unknown')} | **Duration:** {plan.get('estimated_duration', 'unknown')}"
                                    )

                                    # Enhanced parameter display
                                    if plan.get("parameters"):
                                        st.write("**Parameters:**")
                                        param_df_data = []
                                        for param in plan["parameters"]:
                                            param_name = param.get("name", str(param))
                                            param_type = param.get("type", "Any")
                                            required = (
                                                "Yes" if param.get("required", False) else "No"
                                            )
                                            suggestions = ", ".join(
                                                str(s) for s in param.get("suggestions", [])[:3]
                                            )
                                            param_df_data.append(
                                                {
                                                    "Parameter": param_name,
                                                    "Type": param_type,
                                                    "Required": required,
                                                    "Suggestions": suggestions or "N/A",
                                                }
                                            )
                                        st.dataframe(param_df_data, use_container_width=True)

                                    # Prerequisites and use cases
                                    if plan.get("prerequisites"):
                                        st.write(
                                            f"**Prerequisites:** {', '.join(plan['prerequisites'])}"
                                        )

                                    if plan.get("common_use_cases"):
                                        st.write("**Common Use Cases:**")
                                        for use_case in plan["common_use_cases"][:3]:
                                            st.write(f"• {use_case}")

                                    if plan.get("related_plans"):
                                        st.write(
                                            f"**Related Plans:** {', '.join(plan['related_plans'][:3])}"
                                        )

                                    if plan.get("docstring"):
                                        st.write(f"**Documentation:** {plan['docstring']}")
                        else:
                            st.info("No plans match the selected filters")
                else:
                    st.error("Could not fetch plan details")
            except Exception as e:
                st.error(f"Error fetching plans: {str(e)}")

    with plan_tab2:
        st.subheader("Plan Recommendations")
        if st.button("🔄 Get Recommendations"):
            try:
                response = requests.get(
                    f"{backend_url}/instrument/plans/recommendations", timeout=10
                )
                if response.status_code == 200:
                    rec_data = response.json()

                    if "error" in rec_data:
                        st.error(rec_data["error"])
                    else:
                        recommendations = rec_data.get("recommendations", {})

                        # Device summary
                        device_summary = rec_data.get("available_devices_summary", {})
                        if device_summary:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Motors", device_summary.get("motors", 0))
                            with col2:
                                st.metric("Detectors", device_summary.get("detectors", 0))
                            with col3:
                                st.metric("Total Devices", device_summary.get("total", 0))

                        # Beginner recommendations
                        if recommendations.get("beginners"):
                            st.subheader("🟢 Beginner-Friendly Plans")
                            for rec in recommendations["beginners"]:
                                with st.expander(f"📋 {rec['name']} (Beginner)"):
                                    st.write(f"**Why:** {rec['reason']}")
                                    st.code(rec["example"])

                        # Common task recommendations
                        if recommendations.get("common_tasks"):
                            st.subheader("🟡 Common Task Plans")
                            for rec in recommendations["common_tasks"]:
                                with st.expander(f"📋 {rec['name']} (Intermediate)"):
                                    st.write(f"**Why:** {rec['reason']}")
                                    st.code(rec["example"])

                        # Advanced recommendations
                        if recommendations.get("advanced"):
                            st.subheader("🔴 Advanced Plans")
                            for rec in recommendations["advanced"]:
                                with st.expander(f"📋 {rec['name']} (Advanced)"):
                                    st.write(f"**Why:** {rec['reason']}")
                                    st.code(rec["example"])

                        # Device-based recommendations
                        if recommendations.get("by_device_type"):
                            st.subheader("🔧 Device-Specific Recommendations")
                            device_recs = recommendations["by_device_type"]

                            if device_recs.get("motors"):
                                st.write("**Motor-based Plans:**")
                                for rec in device_recs["motors"]:
                                    st.write(f"• **{rec['name']}**: {rec['description']}")
                                    st.code(rec["example"])

                            if device_recs.get("detectors"):
                                st.write("**Detector-based Plans:**")
                                for rec in device_recs["detectors"]:
                                    st.write(f"• **{rec['name']}**: {rec['description']}")
                                    st.code(rec["example"])
                else:
                    st.error("Could not fetch recommendations")
            except Exception as e:
                st.error(f"Error fetching recommendations: {str(e)}")

    with plan_tab3:
        st.subheader("Plan Analysis Summary")
        if st.button("🔄 Refresh Analysis"):
            try:
                response = requests.get(f"{backend_url}/instrument/plans/detailed", timeout=10)
                if response.status_code == 200:
                    plans_data = response.json()
                    analysis_summary = plans_data.get("analysis_summary", {})

                    if analysis_summary:
                        # Complexity breakdown chart
                        st.subheader("Complexity Distribution")
                        complexity_data = analysis_summary.get("complexity_breakdown", {})
                        if complexity_data:
                            st.bar_chart(complexity_data)

                        # Categories breakdown
                        st.subheader("Plan Categories")
                        categories_data = analysis_summary.get("categories_breakdown", {})
                        if categories_data:
                            st.bar_chart(categories_data)

                        # Recommendations
                        col1, col2 = st.columns(2)
                        with col1:
                            st.subheader("🔴 Most Complex Plans")
                            for plan_name in analysis_summary.get("most_complex_plans", []):
                                st.write(f"• {plan_name}")

                        with col2:
                            st.subheader("🟢 Recommended Starter Plans")
                            for plan_name in analysis_summary.get("recommended_starter_plans", []):
                                st.write(f"• {plan_name}")
                else:
                    st.error("Could not fetch analysis data")
            except Exception as e:
                st.error(f"Error fetching analysis: {str(e)}")

    with tab4:
        st.subheader("Scan History")
    if st.button("🔄 Refresh History"):
        try:
            response = requests.get(f"{backend_url}/instrument/history", timeout=10)
            if response.status_code == 200:
                history_data = response.json()

                if "error" in history_data:
                    st.warning(history_data["error"])
                else:
                    history = history_data.get("history", [])
                    summary = history_data.get("summary", {})

                    # Show summary metrics
                    if summary:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total Scans", summary.get("total_scans", 0))
                        with col2:
                            st.metric("Successful", summary.get("successful_scans", 0))
                        with col3:
                            st.metric("Failed", summary.get("failed_scans", 0))

                        # Most used plans
                        if summary.get("most_used_plans"):
                            st.write("**Most Used Plans:**")
                            for plan_name, count in summary["most_used_plans"]:
                                st.write(f"- {plan_name}: {count} times")

                    # Recent history
                    if history:
                        st.write("**Recent Scans:**")
                        history_df_data = []
                        for item in history[-10:]:  # Show last 10
                            history_df_data.append(
                                {
                                    "Plan": item.get("plan_name", "Unknown"),
                                    "Status": item.get("exit_status", "Unknown"),
                                    "Time": item.get("time_start", "Unknown"),
                                    "UID": (
                                        item.get("uid", "")[:8] + "..." if item.get("uid") else ""
                                    ),
                                }
                            )

                        st.dataframe(history_df_data, use_container_width=True)
            else:
                st.error("Could not fetch history")
        except Exception as e:
            st.error(f"Error fetching history: {str(e)}")

# Bottom section - Devices and Plans (keep existing for compatibility)
if st.session_state.devices or st.session_state.plans:
    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.header("🔧 Available Devices")
        if st.session_state.devices:
            for category, devices in st.session_state.devices.items():
                if devices:  # Only show categories that have devices
                    st.subheader(f"{category.title()}")
                    for name, info in devices.items():
                        description = info.get("description", "No description available")
                        st.write(f"**{name}**: {description}")
        else:
            st.info("Connect to QServer to load devices")

    with col2:
        st.header("📋 Available Plans")
        if st.session_state.plans:
            for plan_name, plan_info in st.session_state.plans.items():
                description = plan_info.get("description", "Scan plan")
                st.write(f"**{plan_name}**: {description}")
        else:
            st.info("Connect to QServer to load plans")

# Footer
st.markdown("---")
st.caption(
    "💡 **Tips:** Ask about specific devices, explain scan plans, or get help with beamline operations. Connect to QServer to load your beamline configuration."
)


def main():
    """Main entry point for the frontend"""
    pass  # Streamlit runs the script directly


if __name__ == "__main__":
    # This is handled by Streamlit CLI
    pass
