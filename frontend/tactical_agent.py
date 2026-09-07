import os
import re
import math
import random

# Global flag to track if real LLM is usable
USE_REAL_LLM = False
agent_executor = None

def calculate_live_telemetry(satellite_name: str) -> str:
    """Calculates live telemetry using the Flask app state to retrieve actual collision risks."""
    try:
        import app
        from collision_detection import detect_collisions, predict_collision_point
        from risk_model import evaluate_collision_risk
        import time
        from datetime import datetime, timedelta
        from sgp4.api import jday

        if not app.SATELLITES:
            return f"No active satellites in registry."

        # Compute positions using current simulated time
        now_time = time.time()
        elapsed = now_time - app.REAL_START_TIME
        sim_now = app.SIM_START_TIME + timedelta(seconds=elapsed * app.TIME_WARP)
        jd, fr = jday(sim_now.year, sim_now.month, sim_now.day, sim_now.hour, sim_now.minute, sim_now.second + sim_now.microsecond / 1e6)

        pos = []
        for sat in app.SATELLITES:
            if sat.name in app.DESTROYED_SATELLITES:
                continue
            e, r, v = sat.satrec.sgp4(jd, fr)
            if e == 0:
                pos_obj = {
                    "name": sat.name,
                    "position": {"x": float(r[0]), "y": float(r[1]), "z": float(r[2])},
                    "velocity": {"vx": float(v[0]), "vy": float(v[1]), "vz": float(v[2])}
                }
                
                # Apply maneuver offsets
                if sat.name in app.MANEUVER_STATE:
                    offset = app.MANEUVER_STATE[sat.name]
                    dist = (pos_obj['position']['x']**2 + pos_obj['position']['y']**2 + pos_obj['position']['z']**2)**0.5
                    if dist > 0:
                        factor = (dist + offset) / dist
                        pos_obj['position']['x'] *= factor
                        pos_obj['position']['y'] *= factor
                        pos_obj['position']['z'] *= factor
                pos.append(pos_obj)

        # Include active persistent debris
        all_objects = pos + [d for d in app.PERSISTENT_DEBRIS if d['name'] not in app.DESTROYED_SATELLITES]

        # Find target object (case-insensitive strip)
        target_name_clean = satellite_name.strip().upper()
        target = next((obj for obj in all_objects if obj['name'].strip().upper() == target_name_clean), None)
        if not target:
            return f"Satellite '{satellite_name}' not found or is currently destroyed."

        # Detect collisions with threshold of 800.0 km (matches app.py)
        collisions = detect_collisions(all_objects, threshold_km=800.0)

        # Find threats involving our target satellite
        target_threats = []
        for c in collisions:
            if c['satellite_1'].strip().upper() == target_name_clean or c['satellite_2'].strip().upper() == target_name_clean:
                other_name = c['satellite_2'] if c['satellite_1'].strip().upper() == target_name_clean else c['satellite_1']
                other_obj = next((obj for obj in all_objects if obj['name'] == other_name), None)
                if other_obj:
                    risk = evaluate_collision_risk(target, other_obj, c['distance_km'])
                    try:
                        tca = predict_collision_point(target, other_obj, lookahead_sec=600)
                        risk['tca'] = round(tca) if tca else "IMMINENT"
                    except:
                        risk['tca'] = "IMMINENT"
                    target_threats.append(risk)

        if not target_threats:
            return f"No active threats detected for {target['name']}. Distance is clear. Orbit is stable."

        # Format details of the highest threat
        highest_threat = sorted(target_threats, key=lambda x: x['risk_score'], reverse=True)[0]
        other_sat = highest_threat['satellite_2']
        dist = highest_threat['distance_km']
        rel_vel = highest_threat['relative_velocity']
        risk_score = highest_threat['risk_score']
        tca = highest_threat['tca']

        return f"Threat detected for {target['name']}. Collision partner: {other_sat}. Distance: {dist:.2f} km. TCA: {tca} seconds. Relative Velocity: {rel_vel:.2f} km/s. Risk Score: {risk_score * 100:.1f}%."

    except Exception as ex:
        return f"Telemetry computation failed: {str(ex)}"

def apply_live_maneuver(satellite_name: str, maneuver_type: str) -> str:
    """Directly executes a maneuver on the live simulation state."""
    try:
        import app
        m_type = maneuver_type.lower().strip()
        if m_type not in ['prograde', 'retrograde', 'plane']:
            return f"Failed: Invalid maneuver type '{maneuver_type}'. Must be 'prograde', 'retrograde', or 'plane'."

        offset = 2000.0 if m_type == 'prograde' else -1200.0 if m_type == 'retrograde' else 2500.0
        # Clean name match
        import time
        target_name_clean = satellite_name.strip().upper()
        matched_name = None
        
        # Check SATELLITES
        for sat in app.SATELLITES:
            if sat.name.strip().upper() == target_name_clean:
                matched_name = sat.name
                break
                
        if not matched_name:
            # Check PERSISTENT_DEBRIS
            for d in app.PERSISTENT_DEBRIS:
                if d['name'].strip().upper() == target_name_clean:
                    matched_name = d['name']
                    break
                    
        if not matched_name:
            return f"Failed: Object '{satellite_name}' not found."

        app.MANEUVER_STATE[matched_name] = app.MANEUVER_STATE.get(matched_name, 0) + offset
        return f"Burn executed: {m_type} maneuver applied to {matched_name}. Orbit altered by {offset:.1f} meters."
    except Exception as ex:
        return f"Maneuver execution failed: {str(ex)}"

# Try to initialize the LangChain Google GenAI or OpenAI integration if key and libraries are present
try:
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = "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"

    openai_key = os.environ.get("OPENAI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

    if openai_key or google_key:
        from langchain_core.tools import tool
        from langchain_classic.agents import create_tool_calling_agent, AgentExecutor
        from langchain_core.prompts import ChatPromptTemplate

        # Define langchain tools
        @tool
        def get_threat_telemetry(satellite_name: str) -> str:
            """Use this to check the current collision risk and Time of Closest Approach (TCA) for a specific satellite."""
            return calculate_live_telemetry(satellite_name)

        @tool
        def execute_orbital_burn(satellite_name: str, maneuver_type: str) -> str:
            """Executes an orbital maneuver. Types must be 'prograde', 'retrograde', or 'plane'."""
            return apply_live_maneuver(satellite_name, maneuver_type)

        tools = [get_threat_telemetry, execute_orbital_burn]

        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are the AEGIS Tactical AI. You monitor satellite telemetry and recommend or execute evasion maneuvers to prevent Kessler Syndrome cascades. Be concise, analytical, and militaristic in your responses. Real-time telemetry tools are available, query them before recommending or executing maneuvers."),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        if openai_key:
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(model="gpt-4o", temperature=0)
            print("[AEGIS AI] LangChain OpenAI agent initialized successfully.")
        else:
            if "GEMINI_API_KEY" in os.environ and "GOOGLE_API_KEY" not in os.environ:
                os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
            from langchain_google_genai import ChatGoogleGenerativeAI
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", temperature=0)
            print("[AEGIS AI] LangChain Google GenAI agent initialized successfully.")

        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
        USE_REAL_LLM = True
except Exception as e:
    # We do not crash the app, but log and fall back to custom rule-based agent
    print(f"[AEGIS AI] LLM agent initialization failed: {e}")
    pass

def ask_aegis_agent(query: str) -> str:
    """Translates the query into a response. If LangChain is initialized, it calls the LLM,
    otherwise it uses the custom rule-based tactical engine."""
    global USE_REAL_LLM, agent_executor
    
    if USE_REAL_LLM and agent_executor:
        try:
            response = agent_executor.invoke({"input": query})
            return response["output"]
        except Exception as e:
            print(f"[AEGIS AI] Real LLM invocation failed: {e}. Falling back to Rule-based.")

    # --- Rule-Based Tactical Simulation Fallback ---
    # Extract satellite name from query. 
    # Example format: "Assess collision threats for STARLINK-1234 and recommend a maneuver."
    match = re.search(r"Assess collision threats for (.+?) and recommend", query, re.IGNORECASE)
    if not match:
        match = re.search(r"for\s+([A-Za-z0-9\-_\s]+?)(?:\s+and|\s*$)", query, re.IGNORECASE)
        
    satellite_name = match.group(1).strip() if match else "unknown satellite"
    
    # Calculate live telemetry
    telemetry = calculate_live_telemetry(satellite_name)
    
    if "Threat detected" in telemetry:
        # Parse details from telemetry string
        tca_match = re.search(r"TCA:\s*([0-9A-Za-z]+)\s*seconds", telemetry)
        dist_match = re.search(r"Distance:\s*([0-9\.]+)\s*km", telemetry)
        risk_match = re.search(r"Risk Score:\s*([0-9\.]+)%", telemetry)
        partner_match = re.search(r"Collision partner:\s*([A-Za-z0-9\-_\s]+)\.", telemetry)
        
        tca = tca_match.group(1) if tca_match else "unknown"
        dist = dist_match.group(1) if dist_match else "unknown"
        risk = risk_match.group(1) if risk_match else "unknown"
        partner = partner_match.group(1).strip() if partner_match else "orbital debris"
        
        # Formulate militaristic response
        return (
            f"AEGIS TACTICAL ALERT: High-risk orbital conjunction detected for {satellite_name}. "
            f"Conjunction Partner: {partner}. Current miss distance: {dist} km. "
            f"Time of Closest Approach (TCA): {tca} seconds. Risk Index: {risk}%. "
            f"RECOMMENDED EVASIVE ACTION: Execute a PROGRADE BURN immediately. "
            f"This tangential acceleration will raise the orbit of {satellite_name} by approximately 2000m, "
            f"effectively clearing the debris fragmentation envelope and preventing potential Kessler Syndrome cascade."
        )
    else:
        # Clean response
        # Extract name from telemetry if match
        clean_name = satellite_name
        name_match = re.search(r"for\s+(.+?)\.", telemetry)
        if name_match:
            clean_name = name_match.group(1)
            
        return (
            f"AEGIS MONITORING REPORT: Orbit analysis complete for {clean_name}. "
            f"No immediate threat targets detected within the active 600-second projection horizon. "
            f"Current tracking parameters indicate clear orbital corridor. "
            f"RECOMMENDATION: Maintain nominal operations. No evasive burns required."
        )
