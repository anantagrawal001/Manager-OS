"""Deterministic command routing. Specific actions take precedence over topics."""
import re


def contains(text, phrase):
    return bool(re.search(r"(?<!\w)" + re.escape(phrase) + r"(?!\w)", text, re.I))


def classify(text, intent_map):
    lower = text.lower().strip()
    action_text = re.sub(r'^(?:(?:please|also|can you|could you|would you)\s+)+', '', lower)
    if re.match(r'^send\b', action_text):
        return 'communication'
    if re.match(r'^(?:continue|retry|cancel|stop|open|run) (?:the )?(?:project|build)\b|^(?:project|build) progress\b', lower):
        return 'builder'
    # A requested product owns its subject: a calendar app is a build, not a calendar action.
    direct_task = re.match(r'^(?:please\s+)?(?:add task|remind me|complete task|create file|write file|send message|send whatsapp)\b', lower)
    build_verb = re.search(r'\b(build|create|develop|implement|make|generate)\b', lower)
    product = re.search(r'\b(app|application|project|platform|website|api|backend|frontend|dashboard|extension|bot|system|tracker|optimizer|resume maker|software)\b', lower)
    if build_verb and product and not direct_task:
        return 'builder'
    if any(contains(lower, p) for p in ["what did i say", "do you remember", "when did i mention", "conversation history", "recall", "last time"]):
        return "conversation_memory"
    if any(contains(lower, p) for p in ["status", "which api", "which model", "what model", "providers", "agents", "are you working", "second laptop", "capabilities", "what can you"]):
        return "system"
    if any(contains(lower, p) for p in ["whatsapp", "send message", "send photo", "send image", "invite", "invitation", "simulate recruiter call", "incoming call"]):
        return "communication"
    if any(contains(lower, p) for p in ["add task", "list tasks", "show tasks", "my tasks", "complete task", "remind me", "reminder", "schedule", "calendar"]):
        return "life"
    if re.search(r'\b(resume|résumé|cv|curriculum vitae)\b', lower):
        return 'career'
    if re.search(r"\b(find|search|read|create|write|save|show|open)\s+(?:a\s+|the\s+)?file\b", lower):
        return "files"
    if re.search(r"\b(open|launch|start)\s+(?:the\s+)?(notepad|calc(?:ulator)?|chrome|explorer|paint|mspaint|word|excel|powerpoint|vscode|vs code)\b", lower):
        return "files"
    scores = {}
    for intent, keywords in intent_map.items():
        # These words alone are ordinary chat instructions, not external actions.
        keywords = [kw for kw in keywords if kw not in {'reply', 'message', 'dm', 'content', 'keyword', 'today', 'plan'}]
        hits = [kw for kw in keywords if contains(lower, kw)]
        if hits:
            scores[intent] = sum(1 + len(kw.split()) for kw in hits)
    return max(scores, key=scores.get) if scores else "conversation"
