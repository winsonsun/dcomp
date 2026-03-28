from pydantic import BaseModel
from typing import List, Dict

# --- 1. The Physics Registry (Q1) ---
class SystemPhysics(BaseModel):
    hard_limits: Dict[str, float]
    current_telemetry: Dict[str, float]

def fetch_q1_state(reactor_id: str) -> SystemPhysics:
    """Pulls live deterministic data from physical sensors or databases."""
    # Example DB/Sensor fetch
    return SystemPhysics(
        hard_limits={"max_temp_c": 800.0, "max_pressure_psi": 150.0},
        current_telemetry={"core_temp_c": 640.2, "pressure_psi": 110.5}
    )

# --- 2. The Society/Rules Registry (Q3) ---
class SystemRules(BaseModel):
    user_role: str
    active_sops: List[str]
    prohibited_actions: List[str]

def fetch_q3_state(user_id: str, current_task: str) -> SystemRules:
    """Pulls strict Role-Based Access Control (RBAC) and relevant SOPs."""
    return SystemRules(
        user_role="Level_2_Operator",
        active_sops=["SOP-101: Standard Pump Maintenance", "SOP-09: Mandatory Log Reporting"],
        prohibited_actions=["INITIATE_SHUTDOWN", "OVERRIDE_VALVE_LOCK"]
    )
