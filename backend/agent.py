"""
LangChain agent for natural language processing and tool orchestration
Handles NLP to plan translation and command routing
"""

import logging
from typing import Dict, Any, List, Optional
from config.settings import settings
from models import PlanSubmission, AgentResponse, NLPQuery
from local_llm import local_llm_service

# In production, these would be actual imports
# from langchain.agents import AgentExecutor, create_openai_tools_agent
# from langchain.tools import Tool, StructuredTool
# from langchain.chat_models import ChatOpenAI
# from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
# from langchain.memory import ConversationBufferMemory

logger = logging.getLogger(__name__)


class BaitChatAgent:
    """LangChain-based agent for handling natural language commands"""
    
    def __init__(self):
        self.llm = None
        self.tools = []
        self.agent = None
        self.agent_executor = None
        self.memory = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize the agent with tools and LLM"""
        try:
            # Initialize LLM based on provider
            if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
                # Local LLM will be used through local_llm_service
                self.llm = None
                logger.info("Using local LLM service for agent")
            else:
                # Initialize cloud LLM
                # self.llm = ChatOpenAI(
                #     model=settings.LLM_MODEL,
                #     temperature=0.7,
                #     api_key=settings.OPENAI_API_KEY
                # )
                pass
            
            # Initialize memory
            # self.memory = ConversationBufferMemory(
            #     memory_key="chat_history",
            #     return_messages=True
            # )
            
            # Create tools
            self._create_tools()
            
            # Create agent
            self._create_agent()
            
            self._initialized = True
            logger.info("BaitChat agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            self._initialized = False
    
    def _create_tools(self):
        """Create LangChain tools for agent"""
        
        # Device query tool
        device_tool = {
            "name": "list_devices",
            "description": "List available beamline devices (motors, detectors)",
            "func": self._list_devices
        }
        
        # Plan query tool
        plan_tool = {
            "name": "list_plans",
            "description": "List available scan plans",
            "func": self._list_plans
        }
        
        # Last scan tool
        scan_tool = {
            "name": "get_last_scan",
            "description": "Get information about the most recent scan",
            "func": self._get_last_scan
        }
        
        # Plan explanation tool
        explain_tool = {
            "name": "explain_plan",
            "description": "Explain what a scan plan does",
            "func": self._explain_plan
        }
        
        # Plan generation tool (Phase 1.5)
        generate_tool = {
            "name": "generate_plan",
            "description": "Generate a plan from natural language description",
            "func": self._generate_plan
        }
        
        # Queue management tools (Phase 1.5)
        queue_tool = {
            "name": "manage_queue",
            "description": "View or manage the scan queue",
            "func": self._manage_queue
        }
        
        # In production, convert to actual LangChain tools
        # self.tools = [
        #     Tool.from_function(
        #         func=tool["func"],
        #         name=tool["name"],
        #         description=tool["description"]
        #     )
        #     for tool in [device_tool, plan_tool, scan_tool, explain_tool, generate_tool, queue_tool]
        # ]
        
        # For development, store tool definitions
        self.tools = [device_tool, plan_tool, scan_tool, explain_tool, generate_tool, queue_tool]
    
    def _create_agent(self):
        """Create the LangChain agent"""
        
        # Define system prompt
        system_prompt = """You are a helpful beamline assistant for scientists using the APS beamline.
You help scientists run experiments, manage scan queues, and understand scan plans.

You have access to the following tools:
- list_devices: Show available motors and detectors
- list_plans: Show available scan plans
- get_last_scan: Get information about the most recent scan
- explain_plan: Explain what a scan plan does
- generate_plan: Create a scan plan from natural language
- manage_queue: View or manage the scan queue

When users ask questions, use the appropriate tools to help them.
Be concise but informative in your responses.
Always prioritize safety - if a request seems dangerous or unclear, ask for clarification.
"""
        
        # In production, create actual agent
        # prompt = ChatPromptTemplate.from_messages([
        #     ("system", system_prompt),
        #     MessagesPlaceholder(variable_name="chat_history"),
        #     ("human", "{input}"),
        #     MessagesPlaceholder(variable_name="agent_scratchpad"),
        # ])
        
        # self.agent = create_openai_tools_agent(
        #     llm=self.llm,
        #     tools=self.tools,
        #     prompt=prompt
        # )
        
        # self.agent_executor = AgentExecutor(
        #     agent=self.agent,
        #     tools=self.tools,
        #     memory=self.memory,
        #     verbose=True,
        #     handle_parsing_errors=True
        # )
        
        logger.info("Agent created with system prompt and tools")
    
    async def process_query(self, query: NLPQuery) -> AgentResponse:
        """
        Process a natural language query
        
        Args:
            query: Natural language query from user
        
        Returns:
            Agent response with answer and any actions taken
        """
        try:
            if not self._initialized:
                await self.initialize()
            
            # In production, use actual agent
            # result = await self.agent_executor.ainvoke({
            #     "input": query.query,
            #     "context": query.context
            # })
            
            # Use local LLM if configured, otherwise simulate
            if settings.LLM_PROVIDER in ["lmstudio", "ollama"]:
                response = await self._process_with_local_llm(query)
            else:
                # For development, simulate processing
                response = await self._simulate_agent_response(query)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing query: {e}")
            return AgentResponse(
                response="I encountered an error processing your request. Please try again.",
                confidence=0.0
            )
    
    async def _process_with_local_llm(self, query: NLPQuery) -> AgentResponse:
        """Process query using local LLM with tool integration"""
        
        try:
            # Build system prompt with available tools
            system_prompt = """You are a helpful beamline assistant for scientists using the APS beamline.
You help scientists run experiments, manage scan queues, and understand scan plans.

You have access to these tools:
- list_devices: Show available motors and detectors
- list_plans: Show available scan plans  
- get_last_scan: Get information about the most recent scan
- explain_plan: Explain what a scan plan does
- generate_plan: Create a scan plan from natural language
- manage_queue: View or manage the scan queue

When users ask questions, determine what action to take and provide helpful responses.
Be concise but informative. Always prioritize safety.

For each query, respond with:
1. What action you're taking (if any)
2. The relevant information or response

Examples:
User: "What motors can I use?"
Assistant: I'll list the available motors for you.
Action: list_devices
[Then provide the device information]

User: "Scan from 0 to 5 mm"  
Assistant: I'll create a scan plan for you.
Action: generate_plan
[Then provide the plan details]
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query.query}
            ]
            
            # Get LLM response
            llm_response = await local_llm_service.generate_chat(
                messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # Parse response and determine actions
            action_taken = self._parse_action_from_response(llm_response)
            
            # Execute the action if identified
            if action_taken:
                tool_result = await self._execute_tool_action(action_taken, query.query)
                final_response = f"{llm_response}\n\n{tool_result}"
                confidence = 0.8
            else:
                final_response = llm_response
                confidence = 0.6
            
            return AgentResponse(
                response=final_response,
                action_taken=action_taken,
                confidence=confidence
            )
            
        except Exception as e:
            logger.error(f"Error processing with local LLM: {e}")
            # Fallback to simulation
            return await self._simulate_agent_response(query)
    
    def _parse_action_from_response(self, response: str) -> Optional[str]:
        """Parse the action from LLM response"""
        response_lower = response.lower()
        
        if "list_devices" in response_lower or "available motors" in response_lower:
            return "list_devices"
        elif "list_plans" in response_lower or "available plans" in response_lower:
            return "list_plans"
        elif "last_scan" in response_lower or "recent scan" in response_lower:
            return "get_last_scan"
        elif "explain" in response_lower:
            return "explain_plan"
        elif "generate_plan" in response_lower or "create scan" in response_lower:
            return "generate_plan"
        elif "queue" in response_lower:
            return "manage_queue"
        
        return None
    
    async def _execute_tool_action(self, action: str, query: str) -> str:
        """Execute the identified tool action"""
        try:
            if action == "list_devices":
                return await self._list_devices()
            elif action == "list_plans":
                return await self._list_plans()
            elif action == "get_last_scan":
                return await self._get_last_scan()
            elif action == "explain_plan":
                return await self._explain_plan("scan")  # Default plan
            elif action == "generate_plan":
                plan = await self._generate_plan(query)
                return f"Generated plan: {plan.name} with args {plan.args}"
            elif action == "manage_queue":
                return await self._manage_queue()
            else:
                return "Action not implemented"
        except Exception as e:
            logger.error(f"Error executing tool action {action}: {e}")
            return f"Error executing {action}"
    
    async def _simulate_agent_response(self, query: NLPQuery) -> AgentResponse:
        """Simulate agent response for development"""
        
        query_lower = query.query.lower()
        
        # Check for device queries
        if any(word in query_lower for word in ["motor", "device", "detector", "hardware"]):
            devices = await self._list_devices()
            return AgentResponse(
                response=f"Available devices:\n{devices}",
                action_taken="list_devices",
                confidence=0.9
            )
        
        # Check for plan queries
        if any(word in query_lower for word in ["plan", "scan", "available"]):
            plans = await self._list_plans()
            return AgentResponse(
                response=f"Available scan plans:\n{plans}",
                action_taken="list_plans",
                confidence=0.9
            )
        
        # Check for last scan query
        if "last" in query_lower and "scan" in query_lower:
            scan_info = await self._get_last_scan()
            return AgentResponse(
                response=f"Last scan information:\n{scan_info}",
                action_taken="get_last_scan",
                confidence=0.95
            )
        
        # Check for explanation requests
        if "explain" in query_lower or "what does" in query_lower:
            explanation = await self._explain_plan("scan")
            return AgentResponse(
                response=explanation,
                action_taken="explain_plan",
                confidence=0.85
            )
        
        # Check for scan requests (Phase 1.5)
        if any(word in query_lower for word in ["run", "perform", "execute", "scan from"]):
            plan = await self._generate_plan(query.query)
            return AgentResponse(
                response="Generated scan plan. Ready to submit to queue.",
                action_taken="generate_plan",
                plan_generated=plan,
                confidence=0.75
            )
        
        # Default response
        return AgentResponse(
            response="I can help you with:\n- Listing available devices and plans\n- Checking the last scan\n- Explaining scan plans\n- Creating new scans",
            confidence=0.5
        )
    
    # Tool implementation methods
    
    async def _list_devices(self) -> str:
        """List available devices"""
        # In production, query actual QServer
        devices = [
            "Motors: motor_x, motor_y, motor_z, motor_theta",
            "Detectors: pilatus, i0, diode, scintillator",
            "Temperature: lakeshore, cryostream",
            "Sample environment: sample_stage, goniometer"
        ]
        return "\n".join(devices)
    
    async def _list_plans(self) -> str:
        """List available scan plans"""
        plans = [
            "scan: Continuous scan over a motor range",
            "count: Take repeated measurements at current position",
            "list_scan: Scan through a list of positions",
            "grid_scan: 2D grid scan with two motors",
            "fly_scan: High-speed continuous acquisition"
        ]
        return "\n".join(plans)
    
    async def _get_last_scan(self) -> str:
        """Get last scan information"""
        return """Scan ID: a1b2c3d4
Plan: scan
Motor: motor_x from 0.0 to 5.0 mm (51 points)
Detector: pilatus
Duration: 125.4 seconds
Status: completed
Max counts: 15234"""
    
    async def _explain_plan(self, plan_name: str) -> str:
        """Explain a scan plan"""
        explanations = {
            "scan": "The 'scan' plan moves a motor continuously from start to stop position while collecting detector data at regular intervals.",
            "count": "The 'count' plan takes repeated measurements at the current position to improve statistics.",
            "list_scan": "The 'list_scan' plan moves to specific positions from a list and collects data at each point."
        }
        return explanations.get(plan_name, "This plan performs a custom measurement sequence.")
    
    async def _generate_plan(self, query: str) -> PlanSubmission:
        """Generate a plan from natural language"""
        
        # Parse the query to extract parameters
        # This is simplified - in production, use NLP to extract entities
        
        plan = PlanSubmission(
            name="scan",
            args=[["pilatus"], "motor_x", 0.0, 5.0, 51],
            kwargs={},
            metadata={"generated_from": query}
        )
        
        return plan
    
    async def _manage_queue(self, action: str = "view") -> str:
        """Manage the scan queue"""
        if action == "view":
            return "Queue: 2 plans pending\n1. scan(motor_x, 0-5mm)\n2. count(pilatus, 10)"
        elif action == "clear":
            return "Queue cleared"
        else:
            return f"Queue action '{action}' performed"
    
    # NLP to plan translation methods
    
    def parse_scan_command(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language scan command to plan dictionary
        
        Examples:
        - "Scan motor_x from 0 to 5 mm with Pilatus"
        - "Take 10 counts with the detector"
        - "Move to positions [0, 1, 2, 3] and measure"
        """
        
        # In production, use more sophisticated NLP
        # For now, use simple pattern matching
        
        text_lower = text.lower()
        
        # Pattern: "scan [motor] from [start] to [stop]"
        if "scan" in text_lower and "from" in text_lower and "to" in text_lower:
            # Extract parameters
            return {
                "plan": "scan",
                "motor": "motor_x",  # Would extract from text
                "start": 0.0,
                "stop": 5.0,
                "num": 51,
                "detectors": ["pilatus"]
            }
        
        # Pattern: "take [n] counts"
        if "count" in text_lower:
            return {
                "plan": "count",
                "num": 10,
                "detectors": ["pilatus", "i0"]
            }
        
        # Pattern: "move to positions [list]"
        if "positions" in text_lower or "list" in text_lower:
            return {
                "plan": "list_scan",
                "motor": "motor_x",
                "positions": [0, 1, 2, 3, 4, 5],
                "detectors": ["pilatus"]
            }
        
        return None
    
    def validate_plan_safety(self, plan: Dict[str, Any]) -> bool:
        """
        Validate that a generated plan is safe to execute
        
        Checks:
        - Motor limits
        - Detector settings
        - Scan duration estimates
        """
        
        # Check motor limits
        if "motor" in plan:
            motor = plan["motor"]
            # In production, check actual motor limits
            limits = {"motor_x": (-10, 10), "motor_y": (-5, 5)}
            
            if motor in limits:
                min_limit, max_limit = limits[motor]
                if "start" in plan and "stop" in plan:
                    if plan["start"] < min_limit or plan["stop"] > max_limit:
                        logger.warning(f"Plan exceeds motor limits: {motor}")
                        return False
        
        # Check scan duration
        if "num" in plan:
            estimated_time = plan["num"] * 2  # 2 seconds per point estimate
            if estimated_time > 3600:  # 1 hour limit
                logger.warning(f"Plan duration too long: {estimated_time}s")
                return False
        
        return True