"""
MANAGER OS — Context Bridge
════════════════════════════
FILE: core/context_bridge.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: When AI model switches mid-task (e.g., Claude → GPT-4o),
         translates conversation history between provider formats.
         Task continues from EXACTLY where it left off. Full context preserved.
         Anant never knows a switch happened.

FORMATS HANDLED:
  Claude:  {"role": "user/assistant", "content": "..."}
  GPT-4o:  {"role": "system/user/assistant", "content": "..."}
  Gemini:  parts-based with history list
  Ollama:  single prompt string with conversation embedded

DO NOT DELETE ANY CODE — comment out with reason and date
"""

from typing import List, Dict, Optional, Any
from loguru import logger


class ContextBridge:
    """
    Translates conversation history between AI provider formats.
    Ensures seamless mid-task model switching with zero context loss.
    """

    @staticmethod
    def to_claude(
        messages: List[Dict],
        system: str = "",
    ) -> Dict:
        """
        Convert any message history to Claude format.
        Claude: system string separate, messages as user/assistant alternating.
        """
        claude_messages = []

        for msg in messages:
            role = msg.get("role", "user")

            # Skip system messages — they go in the system field
            if role == "system":
                continue

            # Normalize role
            if role in ("model", "assistant", "ai"):
                role = "assistant"
            else:
                role = "user"

            content = msg.get("content", "") or msg.get("parts", [""])[0]
            if isinstance(content, list):
                content = " ".join(str(c) for c in content)

            claude_messages.append({"role": role, "content": str(content)})

        # Ensure alternating user/assistant (Claude requires this)
        claude_messages = ContextBridge._ensure_alternating(claude_messages)

        return {
            "system": system,
            "messages": claude_messages
        }

    @staticmethod
    def to_openai(
        messages: List[Dict],
        system: str = "",
    ) -> List[Dict]:
        """
        Convert any message history to OpenAI GPT format.
        GPT: messages list starting with system role.
        """
        openai_messages = []

        if system:
            openai_messages.append({"role": "system", "content": system})

        for msg in messages:
            role = msg.get("role", "user")

            if role == "system":
                # Already added system at top
                continue

            if role in ("model", "ai"):
                role = "assistant"
            elif role not in ("user", "assistant"):
                role = "user"

            content = msg.get("content", "") or ""
            if isinstance(content, list):
                content = " ".join(str(c) for c in content)

            openai_messages.append({"role": role, "content": str(content)})

        return openai_messages

    @staticmethod
    def to_gemini(
        messages: List[Dict],
        system: str = "",
    ) -> Dict:
        """
        Convert any message history to Gemini format.
        Gemini: history as list of {role: user/model, parts: [text]}
        System instruction goes to GenerativeModel constructor.
        """
        history = []
        last_message = None

        for msg in messages[:-1]:  # All but last (last sent separately)
            role = msg.get("role", "user")

            if role == "system":
                continue

            if role in ("assistant", "ai"):
                role = "model"
            else:
                role = "user"

            content = msg.get("content", "")
            if isinstance(content, list):
                content = " ".join(str(c) for c in content)

            history.append({
                "role": role,
                "parts": [str(content)]
            })

        # Last message is sent as new input
        if messages:
            last = messages[-1]
            last_message = last.get("content", "")
            if isinstance(last_message, list):
                last_message = " ".join(str(c) for c in last_message)

        return {
            "system_instruction": system,
            "history": history,
            "last_message": last_message or ""
        }

    @staticmethod
    def to_ollama(
        messages: List[Dict],
        system: str = "",
        model: str = "llama3.1:8b"
    ) -> Dict:
        """
        Convert any message history to Ollama format.
        Ollama: single prompt string with conversation embedded.
        """
        parts = []

        if system:
            parts.append(f"System: {system}\n")

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if isinstance(content, list):
                content = " ".join(str(c) for c in content)

            if role == "system":
                parts.append(f"System: {content}")
            elif role in ("assistant", "ai", "model"):
                parts.append(f"Assistant: {content}")
            else:
                parts.append(f"User: {content}")

        parts.append("Assistant:")  # Signal model to continue
        prompt = "\n".join(parts)

        return {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

    @staticmethod
    def create_handoff_summary(
        original_request: str,
        work_completed: str,
        work_remaining: str,
        switching_from: str,
        switching_to: str
    ) -> str:
        """
        Create a context handoff summary when switching models mid-task.
        Injected as system context for the receiving model.
        """
        return f"""
CONTEXT HANDOFF — You are continuing a task that was started by {switching_from}.

ORIGINAL REQUEST FROM SIR:
{original_request}

WORK ALREADY COMPLETED:
{work_completed}

WORK STILL NEEDED:
{work_remaining}

IMPORTANT: Continue seamlessly from where the previous model left off.
Address Sir as "Sir". Maintain Manager OS personality.
Do NOT restart or repeat completed work. Continue from the remaining work only.
""".strip()

    @staticmethod
    def _ensure_alternating(messages: List[Dict]) -> List[Dict]:
        """
        Ensure messages alternate between user and assistant.
        Required by Claude API. Merges consecutive same-role messages.
        """
        if not messages:
            return messages

        result = []
        prev_role = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == prev_role:
                # Merge with previous message
                if result:
                    result[-1]["content"] += "\n" + content
            else:
                result.append({"role": role, "content": content})
                prev_role = role

        # Must start with user
        if result and result[0]["role"] != "user":
            result.insert(0, {"role": "user", "content": "[Context continues]"})

        return result

    @staticmethod
    def translate(
        messages: List[Dict],
        system: str,
        target_provider: str,
        model: str = None
    ) -> Any:
        """
        Main translation method — converts to target provider format.
        
        Usage:
            formatted = ContextBridge.translate(messages, system, "openai")
        """
        target = target_provider.lower()

        if target in ("anthropic", "claude"):
            return ContextBridge.to_claude(messages, system)

        elif target in ("openai", "gpt", "gpt4o", "gpt-4o"):
            return ContextBridge.to_openai(messages, system)

        elif target in ("google", "gemini"):
            return ContextBridge.to_gemini(messages, system)

        elif target in ("ollama", "llama", "mistral", "local"):
            return ContextBridge.to_ollama(
                messages, system,
                model=model or "llama3.1:8b"
            )

        else:
            logger.warning(f"Unknown target provider: {target} — defaulting to OpenAI format")
            return ContextBridge.to_openai(messages, system)
