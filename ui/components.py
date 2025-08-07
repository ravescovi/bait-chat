"""
Reusable UI components for Streamlit application
Modular components for displaying devices, plans, queues, and scan results
"""

import streamlit as st
from typing import Dict, Any, List, Optional
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import json


class DeviceListComponent:
    """Component for displaying device information"""
    
    def __init__(self, devices: List[Dict[str, Any]]):
        self.devices = devices
    
    def render(self):
        """Render device list"""
        if not self.devices:
            st.warning("No devices found")
            return
        
        # Group devices by type
        motors = [d for d in self.devices if d.get("type") == "motor"]
        detectors = [d for d in self.devices if d.get("type") == "detector"]
        others = [d for d in self.devices if d.get("type") not in ["motor", "detector"]]
        
        # Display in columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("🔧 Motors")
            for motor in motors:
                with st.expander(motor["name"]):
                    st.write(f"**Description:** {motor.get('description', 'N/A')}")
                    st.write(f"**Readable:** {'✅' if motor.get('is_readable') else '❌'}")
                    st.write(f"**Movable:** {'✅' if motor.get('is_movable') else '❌'}")
                    
                    # Show metadata if available
                    if motor.get("metadata"):
                        st.json(motor["metadata"])
        
        with col2:
            st.subheader("📊 Detectors")
            for detector in detectors:
                with st.expander(detector["name"]):
                    st.write(f"**Description:** {detector.get('description', 'N/A')}")
                    st.write(f"**Readable:** {'✅' if detector.get('is_readable') else '❌'}")
                    
                    if detector.get("metadata"):
                        st.json(detector["metadata"])
        
        with col3:
            st.subheader("🔌 Other Devices")
            for device in others:
                with st.expander(device["name"]):
                    st.write(f"**Type:** {device.get('type', 'unknown')}")
                    st.write(f"**Description:** {device.get('description', 'N/A')}")
                    
                    if device.get("metadata"):
                        st.json(device["metadata"])


class PlanViewerComponent:
    """Component for displaying scan plan information"""
    
    def __init__(self, plans: List[Dict[str, Any]]):
        self.plans = plans
    
    def render(self):
        """Render plan viewer"""
        if not self.plans:
            st.warning("No plans found")
            return
        
        st.subheader("📋 Available Scan Plans")
        
        # Create tabs for different plan categories
        tabs = st.tabs(["All Plans", "Basic Scans", "Advanced", "Custom"])
        
        with tabs[0]:
            # Display all plans in a table
            plan_data = []
            for plan in self.plans:
                plan_data.append({
                    "Name": plan["name"],
                    "Description": plan.get("description", "")[:100] + "...",
                    "Parameters": len(plan.get("parameters", [])),
                    "Generator": "✅" if plan.get("is_generator") else "❌"
                })
            
            df = pd.DataFrame(plan_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with tabs[1]:
            # Basic scan plans
            basic_plans = [p for p in self.plans if p["name"] in ["scan", "count", "list_scan"]]
            self._render_plan_cards(basic_plans)
        
        with tabs[2]:
            # Advanced plans
            advanced_plans = [p for p in self.plans if "grid" in p["name"] or "fly" in p["name"]]
            self._render_plan_cards(advanced_plans)
        
        with tabs[3]:
            # Custom plans
            custom_plans = [p for p in self.plans if p["name"] not in ["scan", "count", "list_scan"] 
                          and "grid" not in p["name"] and "fly" not in p["name"]]
            self._render_plan_cards(custom_plans)
    
    def _render_plan_cards(self, plans: List[Dict[str, Any]]):
        """Render plan cards"""
        for plan in plans:
            with st.expander(f"**{plan['name']}**"):
                st.write(plan.get("description", "No description available"))
                
                # Show parameters
                if plan.get("parameters"):
                    st.write("**Parameters:**")
                    for param in plan["parameters"]:
                        st.write(f"- `{param.get('name', '')}` ({param.get('type', '')}):")
                        st.write(f"  {param.get('description', '')}")
                        if not param.get("required", True):
                            st.write(f"  *Optional, default: {param.get('default')}*")
                
                # Show enhanced description if available
                if plan.get("enhanced_description"):
                    st.info(plan["enhanced_description"])
                
                # Example usage
                st.code(self._generate_example(plan), language="python")
    
    def _generate_example(self, plan: Dict[str, Any]) -> str:
        """Generate example usage for a plan"""
        name = plan["name"]
        params = plan.get("parameters", [])
        
        if name == "scan":
            return "scan([pilatus], motor_x, 0, 5, 51)"
        elif name == "count":
            return "count([pilatus, i0], num=10, delay=1)"
        elif name == "list_scan":
            return "list_scan([pilatus], motor_x, [0, 1, 2.5, 4, 5])"
        else:
            param_names = [p.get("name", "...") for p in params[:3]]
            return f"{name}({', '.join(param_names)})"


class QueueStatusComponent:
    """Component for displaying queue status"""
    
    def __init__(self, queue_data: Optional[Dict[str, Any]] = None):
        self.queue_data = queue_data or {}
    
    def render(self):
        """Render queue status"""
        # Phase 1: Show placeholder
        # Phase 1.5: Show actual queue
        
        if not self.queue_data:
            st.info("Queue management available in Phase 1.5")
            st.caption("• Submit plans via natural language")
            st.caption("• View and manage queue")
            st.caption("• Pause/resume operations")
            return
        
        # When queue data is available (Phase 1.5)
        queue_size = self.queue_data.get("queue_size", 0)
        running = self.queue_data.get("running", False)
        
        # Status indicator
        if running:
            st.success(f"🟢 Running - {queue_size} items in queue")
        else:
            st.info(f"⚪ Idle - {queue_size} items in queue")
        
        # Running item
        if self.queue_data.get("running_item"):
            st.write("**Currently Running:**")
            item = self.queue_data["running_item"]
            st.write(f"• {item.get('name', 'Unknown')}")
        
        # Queue items
        if self.queue_data.get("plan_queue"):
            st.write("**Queue:**")
            for i, item in enumerate(self.queue_data["plan_queue"][:5], 1):
                st.write(f"{i}. {item.get('name', 'Unknown')}")
            
            if queue_size > 5:
                st.caption(f"... and {queue_size - 5} more")


class ScanResultComponent:
    """Component for displaying scan results"""
    
    def __init__(self, scan_data: Dict[str, Any]):
        self.scan_data = scan_data
    
    def render(self):
        """Render scan results"""
        st.subheader("📈 Scan Information")
        
        # Basic information
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Scan ID", self.scan_data.get("uid", "N/A"))
            st.metric("Plan", self.scan_data.get("plan_name", "N/A"))
        
        with col2:
            st.metric("Status", self.scan_data.get("exit_status", "N/A"))
            st.metric("Duration", f"{self.scan_data.get('duration', 0):.1f} s")
        
        with col3:
            timestamp = self.scan_data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            st.metric("Time", timestamp.strftime("%H:%M:%S") if timestamp else "N/A")
            st.metric("Points", self.scan_data.get("num_points", 0))
        
        # Plan arguments
        if self.scan_data.get("plan_args"):
            with st.expander("Plan Arguments"):
                st.json(self.scan_data["plan_args"])
        
        # Metadata
        if self.scan_data.get("metadata"):
            with st.expander("Metadata"):
                metadata = self.scan_data["metadata"]
                for key, value in metadata.items():
                    st.write(f"**{key}:** {value}")
        
        # Statistics
        if self.scan_data.get("statistics"):
            stats = self.scan_data["statistics"]
            st.subheader("Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Max", f"{stats.get('max_counts', 0):.0f}")
            with col2:
                st.metric("Min", f"{stats.get('min_counts', 0):.0f}")
            with col3:
                st.metric("Mean", f"{stats.get('mean_counts', 0):.0f}")
            with col4:
                st.metric("Total", f"{stats.get('total_counts', 0):.0f}")
        
        # Plot placeholder
        st.subheader("Data Visualization")
        self._render_plot()
    
    def _render_plot(self):
        """Render a placeholder plot"""
        # In production, would fetch actual scan data
        import numpy as np
        
        # Generate sample data
        x = np.linspace(0, 5, 51)
        y = 1000 * np.exp(-(x - 2.5)**2 / 0.5) + 100 * np.random.random(51)
        
        # Create plot
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode='lines+markers',
            name='Detector Counts',
            line=dict(color='blue', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title=f"Scan: {self.scan_data.get('plan_name', 'Unknown')}",
            xaxis_title="Motor Position (mm)",
            yaxis_title="Counts",
            hovermode='x unified',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)


class VoiceInputComponent:
    """Component for voice input (optional feature)"""
    
    def __init__(self):
        self.audio_data = None
    
    def render(self) -> Optional[str]:
        """
        Render voice input button
        Returns transcribed text if available
        """
        # This is a placeholder for voice input
        # In production, would use WebRTC or MediaRecorder API
        
        if st.button("🎤", help="Voice Input"):
            st.info("Voice input will be available with Whisper integration")
            # In production:
            # 1. Capture audio from browser
            # 2. Send to backend for transcription
            # 3. Return transcribed text
            return None
        
        return None


class StatusIndicatorComponent:
    """Component for showing system status"""
    
    def __init__(self, services: Dict[str, bool]):
        self.services = services
    
    def render(self):
        """Render status indicators"""
        cols = st.columns(len(self.services))
        
        for i, (service, status) in enumerate(self.services.items()):
            with cols[i]:
                if status:
                    st.success(f"✅ {service}")
                else:
                    st.error(f"❌ {service}")


class SearchResultsComponent:
    """Component for displaying search results"""
    
    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
    
    def render(self):
        """Render search results"""
        if not self.results:
            st.info("No results found")
            return
        
        st.subheader(f"Found {len(self.results)} results")
        
        for i, result in enumerate(self.results, 1):
            with st.expander(f"{i}. {result.get('source', 'Unknown source')}"):
                st.write(result.get("content", ""))
                
                # Show metadata
                if result.get("metadata"):
                    st.caption("Metadata:")
                    for key, value in result["metadata"].items():
                        st.caption(f"• {key}: {value}")
                
                # Show relevance score
                score = result.get("score", 0)
                st.progress(score, text=f"Relevance: {score:.0%}")


class PlanBuilderComponent:
    """Component for building plans interactively (Phase 2)"""
    
    def render(self) -> Optional[Dict[str, Any]]:
        """Render plan builder interface"""
        st.subheader("🔧 Plan Builder")
        
        # Plan type selection
        plan_type = st.selectbox(
            "Plan Type",
            ["scan", "count", "list_scan", "grid_scan"],
            help="Select the type of scan to create"
        )
        
        plan_dict = {"name": plan_type}
        
        if plan_type == "scan":
            col1, col2 = st.columns(2)
            with col1:
                motor = st.selectbox("Motor", ["motor_x", "motor_y", "motor_z"])
                start = st.number_input("Start Position (mm)", value=0.0)
                stop = st.number_input("Stop Position (mm)", value=5.0)
            
            with col2:
                detector = st.multiselect("Detectors", ["pilatus", "i0", "diode"], default=["pilatus"])
                num_points = st.number_input("Number of Points", min_value=2, value=51)
            
            plan_dict.update({
                "motor": motor,
                "start": start,
                "stop": stop,
                "detectors": detector,
                "num": num_points
            })
        
        elif plan_type == "count":
            detector = st.multiselect("Detectors", ["pilatus", "i0", "diode"], default=["pilatus", "i0"])
            num = st.number_input("Number of Counts", min_value=1, value=10)
            delay = st.number_input("Delay (seconds)", min_value=0.0, value=1.0)
            
            plan_dict.update({
                "detectors": detector,
                "num": num,
                "delay": delay
            })
        
        # Show generated plan
        st.code(json.dumps(plan_dict, indent=2), language="json")
        
        if st.button("Submit Plan", type="primary"):
            return plan_dict
        
        return None