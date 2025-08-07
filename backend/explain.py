"""
Plan explanation service using LLM
Translates Bluesky plan source code to plain English explanations
"""

import logging
from typing import Optional, Dict, Any
import re
import ast
from config.settings import settings
from local_llm import local_llm_service

# In production, these would be actual imports
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)


class PlanExplainer:
    """Service for explaining Bluesky scan plans in plain language"""
    
    def __init__(self):
        self.llm = None
        self._initialize_llm()
    
    def _initialize_llm(self):
        """Initialize the LLM for plan explanation"""
        try:
            if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
                # Local LLM service will be initialized separately
                self.llm = None
                logger.info("Using local LLM service for plan explanation")
            else:
                # In production, initialize cloud LLM
                # self.llm = ChatOpenAI(
                #     model=settings.LLM_MODEL,
                #     temperature=0.3,
                #     api_key=settings.OPENAI_API_KEY
                # )
                logger.info("LLM initialized for plan explanation")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
    
    async def explain(
        self, 
        plan_source: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate plain English explanation of a scan plan
        
        Args:
            plan_source: Python source code of the plan
            context: Additional context about devices, sample, etc.
        
        Returns:
            Human-readable explanation of what the plan does
        """
        try:
            # Parse the plan source to extract key information
            plan_info = self._parse_plan_source(plan_source)
            
            # Build explanation prompt
            prompt = self._build_explanation_prompt(plan_info, context)
            
            # Generate explanation using LLM
            if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
                # Use local LLM service
                explanation = await self._generate_local_explanation(prompt, plan_info, context)
            elif self.llm:
                # In production, use cloud LLM
                # response = await self.llm.ainvoke(prompt)
                # explanation = response.content
                explanation = self._generate_template_explanation(plan_info, context)
            else:
                # Fallback to template-based explanation
                explanation = self._generate_template_explanation(plan_info, context)
            
            logger.info(f"Generated explanation for plan: {plan_info.get('name', 'unknown')}")
            return explanation
            
        except Exception as e:
            logger.error(f"Error explaining plan: {e}")
            return "Unable to generate explanation for this plan."
    
    def _parse_plan_source(self, source: str) -> Dict[str, Any]:
        """
        Parse Python source code to extract plan information
        """
        info = {
            "name": "unknown",
            "parameters": [],
            "docstring": "",
            "yields": [],
            "devices": [],
            "movements": []
        }
        
        try:
            # Parse the source code
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                # Extract function definition
                if isinstance(node, ast.FunctionDef):
                    info["name"] = node.name
                    info["parameters"] = [arg.arg for arg in node.args.args]
                    
                    # Extract docstring
                    if ast.get_docstring(node):
                        info["docstring"] = ast.get_docstring(node)
                
                # Look for yield statements (plan commands)
                if isinstance(node, ast.Yield):
                    info["yields"].append(ast.unparse(node.value) if hasattr(ast, 'unparse') else str(node.value))
                
                # Look for device references
                if isinstance(node, ast.Name):
                    # Common device patterns
                    if any(pattern in node.id.lower() for pattern in ['motor', 'detector', 'pilatus', 'sample']):
                        if node.id not in info["devices"]:
                            info["devices"].append(node.id)
            
            # Extract movement patterns from source
            movement_patterns = [
                r'mv\((.*?)\)',  # mv(motor, position)
                r'scan\((.*?)\)',  # scan(detectors, motor, start, stop, num)
                r'count\((.*?)\)',  # count(detectors, num)
                r'list_scan\((.*?)\)',  # list_scan(detectors, motor, positions)
            ]
            
            for pattern in movement_patterns:
                matches = re.findall(pattern, source)
                info["movements"].extend(matches)
                
        except Exception as e:
            logger.warning(f"Failed to parse plan source: {e}")
        
        return info
    
    def _build_explanation_prompt(
        self, 
        plan_info: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for LLM to generate explanation
        """
        prompt = f"""
You are a beamline scientist assistant. Explain the following Bluesky scan plan in simple, clear language
that a scientist can understand. Focus on what the plan does, not how it's implemented.

Plan Name: {plan_info['name']}
Parameters: {', '.join(plan_info['parameters'])}
Docstring: {plan_info.get('docstring', 'No description available')}

The plan uses these devices: {', '.join(plan_info.get('devices', ['unknown']))}
"""
        
        if context:
            prompt += f"\nAdditional Context: {context}"
        
        prompt += """

Please provide:
1. A brief summary of what this plan does
2. What parameters it requires and what they mean
3. What kind of data it will collect
4. Typical use cases for this plan

Keep the explanation concise and scientific but accessible.
"""
        
        return prompt
    
    async def _generate_local_explanation(
        self, 
        prompt: str, 
        plan_info: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate explanation using local LLM service"""
        try:
            # Use chat format for better results
            messages = [
                {
                    "role": "system", 
                    "content": "You are a helpful beamline scientist assistant. Explain scan plans in clear, simple language that scientists can understand. Focus on what the plan does and what kind of data it collects."
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
            
            # Try chat completion first, fall back to text completion
            try:
                explanation = await local_llm_service.generate_chat(
                    messages, 
                    temperature=0.3,
                    max_tokens=1000
                )
            except Exception:
                # Fallback to simple text completion
                explanation = await local_llm_service.generate_text(
                    prompt, 
                    temperature=0.3,
                    max_tokens=1000
                )
            
            if explanation and len(explanation) > 50:
                return explanation
            else:
                # Fallback to template if LLM response is poor
                logger.warning("Local LLM response was poor, falling back to template")
                return self._generate_template_explanation(plan_info, context)
                
        except Exception as e:
            logger.error(f"Error with local LLM explanation: {e}")
            # Fallback to template explanation
            return self._generate_template_explanation(plan_info, context)
    
    def _generate_template_explanation(
        self, 
        plan_info: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Generate template-based explanation when LLM is not available
        """
        name = plan_info.get('name', 'unknown')
        params = plan_info.get('parameters', [])
        devices = plan_info.get('devices', [])
        docstring = plan_info.get('docstring', '')
        
        # Build explanation based on common plan types
        if 'scan' in name.lower():
            explanation = self._explain_scan_plan(name, params, devices, docstring)
        elif 'count' in name.lower():
            explanation = self._explain_count_plan(name, params, devices, docstring)
        elif 'list' in name.lower():
            explanation = self._explain_list_scan(name, params, devices, docstring)
        else:
            explanation = self._explain_generic_plan(name, params, devices, docstring)
        
        # Add context if provided
        if context:
            if 'sample' in context:
                explanation += f"\n\nThis will be performed on sample: {context['sample']}"
            if 'energy' in context:
                explanation += f"\nBeam energy: {context['energy']} keV"
        
        return explanation
    
    def _explain_scan_plan(
        self, 
        name: str, 
        params: list, 
        devices: list, 
        docstring: str
    ) -> str:
        """Generate explanation for scan-type plans"""
        
        explanation = f"**{name.replace('_', ' ').title()} Plan**\n\n"
        
        if docstring:
            explanation += f"{docstring}\n\n"
        else:
            explanation += "This plan performs a continuous scan by moving a motor through a range of positions while collecting data.\n\n"
        
        explanation += "**How it works:**\n"
        explanation += "1. The motor moves from a starting position to an ending position\n"
        explanation += "2. Data is collected at regular intervals during the movement\n"
        explanation += "3. Detectors record measurements at each position\n\n"
        
        if params:
            explanation += "**Parameters needed:**\n"
            param_descriptions = {
                'detectors': '- Detectors: Instruments that collect data (e.g., Pilatus detector for X-ray images)',
                'motor': '- Motor: The device being moved (e.g., sample stage, goniometer)',
                'start': '- Start position: Where the scan begins (in mm or degrees)',
                'stop': '- Stop position: Where the scan ends',
                'num': '- Number of points: How many measurements to take',
                'time': '- Exposure time: How long to collect data at each point (seconds)'
            }
            
            for param in params:
                if param in param_descriptions:
                    explanation += f"{param_descriptions[param]}\n"
                else:
                    explanation += f"- {param}: Configuration parameter\n"
        
        explanation += "\n**Typical use:** Mapping sample properties as a function of position, such as absorption scans or diffraction patterns across a sample."
        
        return explanation
    
    def _explain_count_plan(
        self, 
        name: str, 
        params: list, 
        devices: list, 
        docstring: str
    ) -> str:
        """Generate explanation for count-type plans"""
        
        explanation = f"**{name.replace('_', ' ').title()} Plan**\n\n"
        
        if docstring:
            explanation += f"{docstring}\n\n"
        else:
            explanation += "This plan takes repeated measurements at a fixed position.\n\n"
        
        explanation += "**How it works:**\n"
        explanation += "1. All motors remain at their current positions\n"
        explanation += "2. Detectors collect data for a specified time or number of readings\n"
        explanation += "3. Results are averaged or summed to improve statistics\n\n"
        
        if params:
            explanation += "**Parameters needed:**\n"
            if 'detectors' in params:
                explanation += "- Detectors: Which instruments to read from\n"
            if 'num' in params:
                explanation += "- Number of counts: How many readings to take\n"
            if 'delay' in params or 'time' in params:
                explanation += "- Time/Delay: Duration of each measurement or time between measurements\n"
        
        explanation += "\n**Typical use:** Collecting statistics at a single point, measuring beam intensity, or checking detector response."
        
        return explanation
    
    def _explain_list_scan(
        self, 
        name: str, 
        params: list, 
        devices: list, 
        docstring: str
    ) -> str:
        """Generate explanation for list scan plans"""
        
        explanation = f"**{name.replace('_', ' ').title()} Plan**\n\n"
        
        if docstring:
            explanation += f"{docstring}\n\n"
        else:
            explanation += "This plan moves to specific positions from a list and collects data at each point.\n\n"
        
        explanation += "**How it works:**\n"
        explanation += "1. The motor moves to each position in a predefined list\n"
        explanation += "2. At each position, the system waits for stability\n"
        explanation += "3. Data is collected from all specified detectors\n"
        explanation += "4. The process repeats for all positions in the list\n\n"
        
        if params:
            explanation += "**Parameters needed:**\n"
            explanation += "- Detectors: Instruments for data collection\n"
            explanation += "- Motor: The device to move\n"
            explanation += "- Position list: Specific positions to visit (e.g., [0, 1.5, 3.2, 5.0] mm)\n"
        
        explanation += "\n**Typical use:** Measuring at specific points of interest, returning to previously identified features, or non-uniform sampling."
        
        return explanation
    
    def _explain_generic_plan(
        self, 
        name: str, 
        params: list, 
        devices: list, 
        docstring: str
    ) -> str:
        """Generate generic explanation for unknown plan types"""
        
        explanation = f"**{name.replace('_', ' ').title()} Plan**\n\n"
        
        if docstring:
            explanation += f"{docstring}\n\n"
        else:
            explanation += "This is a custom measurement plan.\n\n"
        
        if params:
            explanation += "**Parameters:**\n"
            for param in params:
                explanation += f"- {param}\n"
            explanation += "\n"
        
        if devices:
            explanation += f"**Devices used:** {', '.join(devices)}\n\n"
        
        explanation += "For more details about this plan, please consult the beamline documentation or contact beamline staff."
        
        return explanation