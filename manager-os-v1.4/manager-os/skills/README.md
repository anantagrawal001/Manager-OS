# MANAGER OS — Skills / Plugin System

## How to Add a New Skill

Adding a new capability to Manager OS takes 3 steps:

### Step 1 — Create the agent file
```
agents/your_skill_agent.py
```

```python
from agents.base_agent import BaseAgent

class YourSkillAgent(BaseAgent):
    async def execute(self, request: str, context: dict) -> str:
        # Your skill logic here
        return "Result"
    
    async def get_status(self) -> dict:
        return {"healthy": True, "state": "running"}
```

### Step 2 — Register in main.py
In `main.py`, add to the agents dict:
```python
agents = {
    ...
    "your_skill": YourSkillAgent(config, router, firewall),
}
```

### Step 3 — Add intent keywords in manager.py
In `core/manager.py`, add to `INTENT_MAP`:
```python
INTENT_MAP = {
    ...
    "your_skill": ["keyword1", "keyword2", "trigger phrase"],
}
```

That's it. Nothing else breaks. The modular architecture handles the rest.

## Installed Skills

See `skills/registry/installed_skills.json` for a full list of added skills.

## Notes

- Every skill inherits privacy firewall automatically
- Health agent monitors all skills automatically
- New skills suggested by Growth Agent weekly
- Manager presents new skill proposals to Sir for approval
