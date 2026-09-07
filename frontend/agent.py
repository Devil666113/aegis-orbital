import os
from langchain.agents import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# 1. Define the Tools for the AI
@tool
def get_threat_telemetry(satellite_name: str) -> str:
    """Use this to check the current collision risk and Time of Closest Approach (TCA) for a specific satellite."""
    # In a full production environment, this would query your SATELLITES or PERSISTENT_DEBRIS lists.
    # For now, we return a simulated tactical read-out.
    return f"Threat detected for {satellite_name}. Distance: 2.5km. TCA: 45 seconds. Relative Velocity: 14 km/s."

@tool
def execute_orbital_burn(satellite_name: str, maneuver_type: str) -> str:
    """Executes an orbital maneuver. Types must be 'prograde', 'retrograde', or 'plane'."""
    # This simulates hooking into your MANEUVER_STATE logic.
    return f"Burn executed: {maneuver_type} on {satellite_name}."

# 2. Initialize the LLM (Make sure your GOOGLE_API_KEY environment variable is set)
# We use temperature=0 because we want tactical precision, not creative hallucination.
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)

tools = [get_threat_telemetry, execute_orbital_burn]

# 3. Create the System Prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are the AEGIS Tactical AI. You monitor satellite telemetry and recommend or execute evasion maneuvers to prevent Kessler Syndrome cascades. Be concise, analytical, and militaristic in your responses."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),
])

# 4. Build the Agent
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 5. Create the function that app.py will actually call
def ask_aegis_agent(query: str):
    response = agent_executor.invoke({"input": query})
    return response["output"]