"""
MANAGER OS — Agent Activity Tracker
FILE: core/activity_tracker.py
CREATED: 2026-06-06 | Claude Sonnet 4.6
PURPOSE: Log agent activities for welcome status updates.
"""

import os
import json
from datetime import datetime
from loguru import logger

TRACKER_FILE = os.path.abspath("./logs/agent_activities.json")

def log_activity(agent_name: str, activity_text: str):
    """Log an activity message for a specific agent."""
    try:
        os.makedirs(os.path.dirname(TRACKER_FILE), exist_ok=True)
        activities = []
        if os.path.exists(TRACKER_FILE):
            try:
                with open(TRACKER_FILE, "r") as f:
                    activities = json.load(f)
            except Exception:
                activities = []
                
        activities.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "activity": activity_text
        })
        
        # Keep only the last 200 activities to prevent disk bloat
        if len(activities) > 200:
            activities = activities[-200:]
            
        with open(TRACKER_FILE, "w") as f:
            json.dump(activities, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to log activity for agent '{agent_name}': {e}")

def get_recent_activities(limit: int = 20) -> list:
    """Retrieve the recent list of logged activities."""
    if not os.path.exists(TRACKER_FILE):
        return []
    try:
        with open(TRACKER_FILE, "r") as f:
            activities = json.load(f)
        return activities[-limit:]
    except Exception:
        return []
