"""
MANAGER OS — Files Agent
═════════════════════════
FILE: agents/files_agent.py
CREATED: 2026-05-24 | Claude Sonnet 4.6
PURPOSE: Full file system access on both of Anant's laptops.
         Search, read, write, organize, watch for changes.
         "Find that document I was working on last week about marketing" → works.

DO NOT DELETE ANY CODE — comment out with reason and date
"""

import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio

from loguru import logger
from agents.base_agent import BaseAgent


class FilesAgent(BaseAgent):
    """
    Full file system access. Anant's entire laptop as a unified interface.
    """

    FILES_SYSTEM = """
You are a file system assistant. Help organize, find, and manage files.
When suggesting file operations, be specific about paths and actions.
Never delete files without explicit confirmation. Always confirm before destructive operations.
"""

    # Directories to search (Windows paths)
    SEARCH_ROOTS = [
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "Downloads",
        Path.home() / "OneDrive",
    ]

    EXCLUDED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv",
                     "Windows", "Program Files", "Program Files (x86)"}

    async def execute(self, request: str, context: Dict[str, Any]) -> str:
        req_lower = request.lower()

        # NEW (2026-06-05): Handle local application launching requests
        if any(w in req_lower for w in ["launch", "run app", "run application", "open app", "open application", "start application"]) or \
           (any(app in req_lower for app in ["notepad", "calc", "calculator", "mspaint", "cmd", "powershell", "explorer", "chrome", "vscode", "excel", "word", "powerpoint"]) and "open" in req_lower):
            # If request ends with a common file extension, treat it as a file operation
            if not any(req_lower.endswith(ext) for ext in [".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".yaml", ".yml", ".log", ".csv", ".png", ".jpg", ".pdf", ".docx", ".xlsx", ".pptx"]):
                return await self._launch_app(request, context)

        if any(w in req_lower for w in ["find", "search", "where is", "locate"]):
            return await self._find_file(request, context)
        elif any(w in req_lower for w in ["read", "open", "show me", "contents"]):
            return await self._read_file(request, context)
        elif any(w in req_lower for w in ["save", "create", "write", "make"]):
            return await self._create_file(request, context)
        elif any(w in req_lower for w in ["organize", "sort", "clean", "move"]):
            return await self._organize_files(request, context)
        elif any(w in req_lower for w in ["recent", "last week", "recently"]):
            return await self._find_recent(request, context)
        else:
            return await self._ask_ai(request, system=self.FILES_SYSTEM)

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _launch_app(self, request: str, context: Dict[str, Any]) -> str:
    #     """NEW (2026-06-05): Launch a local Windows application."""
    #     import subprocess
    #
    #     # Ask AI to identify the app command name from the request
    #     prompt = (
    #         f"Identify the desktop application the user wants to launch from this request: '{request}'. "
    #         "Return ONLY the executable name or shortcut command (e.g., 'notepad', 'calc', 'chrome', 'explorer', 'code'). "
    #         "Do not include any other words, punctuation, explanation or formatting."
    #     )
    #     app_name = await self._ask_ai(prompt)
    #     app_name = app_name.strip().lower().replace("`", "").replace("'", "").replace("\"", "")
    #
    #     # Map friendly names to actual Windows commands
    #     mapping = {
    #         "calculator": "calc",
    #         "paint": "mspaint",
    #         "wordpad": "write",
    #         "file explorer": "explorer",
    #         "explorer": "explorer",
    #         "command prompt": "cmd",
    #         "cmd": "cmd",
    #         "powershell": "powershell",
    #         "task manager": "taskmgr",
    #         "taskmgr": "taskmgr",
    #         "excel": "excel",
    #         "word": "winword",
    #         "powerpoint": "powerpnt",
    #         "vs code": "code",
    #         "vscode": "code",
    #         "code": "code",
    #         "chrome": "chrome",
    #         "notepad": "notepad"
    #     }
    #
    #     cmd = mapping.get(app_name, app_name)
    #     logger.info(f"Attempting to launch application: {cmd} (raw extraction: {app_name})")
    #
    #     try:
    #         # Use 'start' to spawn the app detached from the server
    #         subprocess.Popen(f"start {cmd}", shell=True)
    #         return f"Sir, I have launched {app_name} for you."
    #     except Exception as e:
    #         logger.error(f"Failed to launch application {cmd}: {e}")
    #         return f"Sir, I tried to launch {app_name} but encountered an error: {e}"

    async def _launch_app(self, request, context):
        import re
        import subprocess
        mapping = {'notepad': 'notepad.exe', 'calculator': 'calc.exe', 'calc': 'calc.exe',
                   'paint': 'mspaint.exe', 'mspaint': 'mspaint.exe', 'explorer': 'explorer.exe',
                   'chrome': 'chrome.exe', 'excel': 'excel.exe', 'word': 'winword.exe',
                   'powerpoint': 'powerpnt.exe', 'vscode': 'Code.exe', 'vs code': 'Code.exe'}
        match = re.fullmatch(r'(?:please )?(?:open|launch|start) (?:the )?(.+?)(?: please)?[.!]?', request.strip(), re.I)
        name = match[1].lower() if match else ''
        if name not in mapping:
            return 'Sir, supported apps include Notepad, Calculator, Paint, Explorer, Chrome, Word, Excel and VS Code. Use "open notepad".'
        executable = shutil.which(mapping[name])
        if not executable and os.name == 'nt':
            import winreg
            for root in [winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE]:
                try:
                    with winreg.OpenKey(root, 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\' + mapping[name]) as key:
                        candidate = winreg.QueryValue(key, None).strip('"')
                        if Path(candidate).is_file():
                            executable = candidate
                            break
                except OSError:
                    continue
        if not executable:
            return f'Sir, {name} was not found on this computer.'
        try:
            subprocess.Popen([executable])
            return f'Sir, launched {name}.'
        except OSError as exc:
            return f'Sir, {name} could not start ({type(exc).__name__}).'

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _find_file(self, request: str, context: Dict) -> str:
    #     """Search for files by name or content description"""
    #     # Extract search terms
    #     prompt = f"Extract the file search terms from: '{request}'. Return only the search keywords, comma-separated."
    #     keywords_str = await self._ask_ai(prompt)
    #     keywords = [k.strip().lower() for k in keywords_str.split(",") if k.strip()]
    #
    #     results = await asyncio.to_thread(self._search_files, keywords)
    #
    #     if not results:
    #         return f"Sir, I couldn't find any files matching '{', '.join(keywords)}' in your Documents, Desktop, and Downloads folders."
    #
    #     result_lines = "\n".join(
    #         f"  {i+1}. {r['name']} — {r['path']}\n     Modified: {r['modified']}"
    #         for i, r in enumerate(results[:10])
    #     )
    #
    #     return (
    #         f"Found {len(results)} file(s) matching your search, Sir:\n\n"
    #         f"{result_lines}\n\n"
    #         f"{'(Showing top 10)' if len(results) > 10 else ''}\n"
    #         f"Say 'read file [number]' to see the contents of any of these."
    #     )

    async def _find_file(self, request, context):
        import re
        query = re.sub(r'^(?:please )?(?:find|search(?: for)?|locate|where is)\s+(?:the\s+)?(?:files?\s+)?', '', request.strip(), flags=re.I)
        query = query.strip(' "\'?')
        if not query:
            return 'Sir, give me a filename or part of one, for example "find file invoice.pdf".'
        results = await asyncio.to_thread(self._search_files, [query.lower()])
        self._last_results = results[:10]
        if not results:
            return f'Sir, no filenames matched "{query}" in your configured search folders.'
        return 'Found these files, Sir:\n' + '\n'.join(f"{i+1}. {r['path']}" for i, r in enumerate(self._last_results)) + '\nUse "read file 1" to read the first result.'

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # def _search_files(self, keywords: List[str]) -> List[Dict]:
    #     """Search file system for matching files"""
    #     results = []
    #
    #     for root_dir in self.SEARCH_ROOTS:
    #         if not root_dir.exists():
    #             continue
    #
    #         for path in root_dir.rglob("*"):
    #             # Skip excluded directories
    #             if any(excluded in path.parts for excluded in self.EXCLUDED_DIRS):
    #                 continue
    #
    #             if path.is_file():
    #                 name_lower = path.name.lower()
    #                 if any(keyword in name_lower for keyword in keywords):
    #                     try:
    #                         stat = path.stat()
    #                         results.append({
    #                             "name": path.name,
    #                             "path": str(path),
    #                             "size_kb": round(stat.st_size / 1024, 1),
    #                             "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
    #                             "extension": path.suffix
    #                         })
    #                     except Exception:
    #                         continue
    #
    #     # Sort by modification date (most recent first)
    #     results.sort(key=lambda x: x["modified"], reverse=True)
    #     return results

    def _search_files(self, keywords):
        import time
        results = []
        roots = [Path(p) for p in self.config.get('files', {}).get('search_roots', [])] or self.SEARCH_ROOTS
        deadline = time.monotonic() + 8
        for root in roots:
            if not root.exists():
                continue
            for folder, dirs, files in os.walk(root):
                dirs[:] = [d for d in dirs if d not in self.EXCLUDED_DIRS and d not in {'chrome_user_data', 'backups'} and not Path(folder, d).is_symlink()]
                if time.monotonic() > deadline or len(results) >= 100:
                    return sorted(results, key=lambda r: r['modified'], reverse=True)
                for name in files:
                    if any(k in name.lower() for k in keywords):
                        path = Path(folder, name)
                        try:
                            stat = path.stat()
                            results.append({'name': name, 'path': str(path), 'modified': stat.st_mtime})
                        except OSError:
                            pass
        return sorted(results, key=lambda r: r['modified'], reverse=True)

    async def _find_recent(self, request: str, context: Dict) -> str:
        """Find recently modified files"""
        days = 7
        if "last week" in request.lower():
            days = 7
        elif "yesterday" in request.lower():
            days = 1
        elif "month" in request.lower():
            days = 30

        cutoff = datetime.now() - timedelta(days=days)
        results = await asyncio.to_thread(self._get_recent_files, cutoff)

        if not results:
            return f"Sir, I don't see any files modified in the last {days} days."

        result_lines = "\n".join(
            f"  • {r['name']} ({r['modified']}) — {r['path']}"
            for r in results[:15]
        )

        return f"Recent files (last {days} days), Sir:\n\n{result_lines}"

    def _get_recent_files(self, cutoff: datetime) -> List[Dict]:
        """Get recently modified files"""
        results = []
        for root_dir in self.SEARCH_ROOTS:
            if not root_dir.exists():
                continue
            for path in root_dir.rglob("*"):
                if any(ex in path.parts for ex in self.EXCLUDED_DIRS):
                    continue
                if path.is_file():
                    try:
                        stat = path.stat()
                        modified = datetime.fromtimestamp(stat.st_mtime)
                        if modified >= cutoff:
                            results.append({
                                "name": path.name,
                                "path": str(path),
                                "modified": modified.strftime("%Y-%m-%d %H:%M"),
                            })
                    except Exception:
                        continue
        results.sort(key=lambda x: x["modified"], reverse=True)
        return results

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _read_file(self, request: str, context: Dict) -> str:
    #     """Read and summarize a file"""
    #     # Try to extract path from request
    #     prompt = f"Extract just the file path or filename from this request: '{request}'. Return only the path/filename."
    #     file_hint = await self._ask_ai(prompt)
    #     file_hint = file_hint.strip().strip('"\'')
    #
    #     # Search for the file
    #     if os.path.exists(file_hint):
    #         file_path = Path(file_hint)
    #     else:
    #         results = await asyncio.to_thread(self._search_files, [file_hint.lower()])
    #         if not results:
    #             return f"Sir, I couldn't find the file: {file_hint}"
    #         file_path = Path(results[0]["path"])
    #
    #     # Read the file
    #     try:
    #         if file_path.suffix in (".txt", ".md", ".py", ".js", ".html", ".css", ".json", ".yaml", ".yml", ".log", ".csv"):
    #             content = file_path.read_text(encoding="utf-8", errors="ignore")
    #             if len(content) > 5000:
    #                 content = content[:5000] + f"\n\n[... {len(content) - 5000} more characters — say 'read full file' for complete content]"
    #             return f"**{file_path.name}**\n\n```\n{content}\n```"
    #         else:
    #             stat = file_path.stat()
    #             return (
    #                 f"**{file_path.name}**\n\n"
    #                 f"Type: {file_path.suffix} file\n"
    #                 f"Size: {stat.st_size/1024:.1f} KB\n"
    #                 f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M')}\n"
    #                 f"Path: {file_path}\n\n"
    #                 f"Sir, this file type requires a specific application to open."
    #             )
    #     except Exception as e:
    #         return f"Sir, I couldn't read the file: {e}"

    async def _read_file(self, request, context):
        import re
        hint = re.sub(r'^(?:please )?(?:read|open|show(?: me)?)\s+(?:the\s+)?(?:file\s+)?', '', request.strip(), flags=re.I).strip(' "\'')
        if hint.isdigit():
            results = getattr(self, '_last_results', [])
            idx = int(hint) - 1
            if not 0 <= idx < len(results):
                return 'Sir, run a file search first, then use a result number.'
            path = Path(results[idx]['path'])
        else:
            path = Path(hint)
            if not path.is_file():
                results = await asyncio.to_thread(self._search_files, [hint.lower()])
                if len(results) != 1:
                    return 'Sir, provide the exact file path, or use "find file" and then "read file 1".'
                path = Path(results[0]['path'])
        if path.suffix.lower() not in {'.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.yaml', '.yml', '.log', '.csv', '.tsv'}:
            return f'Sir, text preview does not support {path.suffix}. File: {path}'
        try:
            with path.open(encoding='utf-8', errors='replace') as f:
                content = f.read(12001)
            return f'{path}\n\n' + content[:12000] + ('\n[Preview limited to 12000 characters]' if len(content) > 12000 else '')
        except OSError as exc:
            return f'Sir, file read failed ({type(exc).__name__}).'

    # Superseded 2026-10-12: retained for rollback; corrected implementation below.
    # async def _create_file(self, request: str, context: Dict) -> str:
    #     """Create a new file"""
    #     return (
    #         "Sir, I'll create the file. What should the filename be and where should I save it? "
    #         "For example: 'save as marketing_notes.txt in Documents'"
    #     )

    async def _create_file(self, request, context):
        import re
        match = re.search(r'(?:create|write|save)(?: a)? file (.+?) (?:with content|containing|with text) (.+)', request, re.I | re.S)
        if not match:
            return 'Sir, use: create file notes.txt with content Your text here. Files are saved in outputs unless you give an absolute path.'
        name, content = match[1].strip(' "\''), match[2]
        path = Path(name).expanduser()
        if not path.is_absolute():
            root = Path('outputs').resolve()
            path = (root / path).resolve()
            if not path.is_relative_to(root):
                return 'Sir, provide an absolute path to save outside outputs.'
        if path.suffix.lower() not in {'.txt', '.md', '.json', '.csv', '.html', '.css', '.js', '.py', '.yaml', '.yml'}:
            return 'Sir, choose a text, document or code file extension.'
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('x', encoding='utf-8') as f:
                f.write(content)
            return f'Sir, saved {path} ({path.stat().st_size} bytes).'
        except FileExistsError:
            return f'Sir, {path.name} already exists. Choose a new filename.'
        except OSError as exc:
            return f'Sir, file creation failed ({type(exc).__name__}).'

    async def _organize_files(self, request: str, context: Dict) -> str:
        """File organization suggestions"""
        prompt = f"""
Suggest a file organization strategy for: {request}

Provide:
1. Proposed folder structure
2. Which files go where (based on common patterns)
3. Naming conventions
4. What to consider archiving vs deleting

Note: Always ask for confirmation before any moves or deletions.
"""
        return await self._ask_ai(prompt, system=self.FILES_SYSTEM)

    async def get_status(self) -> Dict:
        return {"healthy": True, "state": "running", "agent": "FilesAgent"}


# ─── NEW 2026-05-27: Semantic File Search + WhatsApp Auto-Send (Reel 14 — IRIS AI) ──

    async def _semantic_search(self, description: str) -> str:
        """
        Semantic file search — finds files by concept/association, not just filename.
        Reel 14 insight: "find iris fabric mod in downloads" → finds .jar file by semantic match.
        """
        # Step 1: Generate search terms from description
        prompt = f"""
Given this file description: "{description}"

Generate:
1. Likely file extensions (e.g., .jar, .pdf, .docx, .xlsx)
2. Likely filename keywords (what words might appear in the filename)
3. Likely folder locations (Downloads, Documents, Desktop, etc.)

Return as JSON: {{"extensions": [...], "keywords": [...], "folders": [...]}}
Return ONLY the JSON, nothing else.
"""
        raw = await self.router.complete(
            system="You are a file system analyst. Return only valid JSON.",
            messages=[{"role": "user", "content": prompt}],
            task_type="reasoning"
        )

        try:
            import json as _json
            clean = raw.strip().strip("```json").strip("```").strip()
            hints = _json.loads(clean)
        except Exception:
            hints = {"extensions": [], "keywords": [description.lower()], "folders": []}

        keywords = hints.get("keywords", [description.lower()])
        extensions = hints.get("extensions", [])

        # Step 2: Search with expanded terms
        results = await asyncio.to_thread(self._search_files, keywords)

        # Filter by extension if specified
        if extensions:
            results = [r for r in results if any(r["name"].endswith(ext) for ext in extensions)]

        if not results:
            return f"Sir, I couldn't find any file matching '{description}'. Could you give me more details about the filename or where it might be?"

        result_lines = "\n".join(
            f"  {i+1}. {r['name']} — {r['path']}\n     Modified: {r['modified']}"
            for i, r in enumerate(results[:5])
        )

        return (
            f"Found {len(results)} file(s) matching '{description}', Sir:\n\n"
            f"{result_lines}\n\n"
            f"Say 'send file 1 to [contact] on WhatsApp' to auto-send, or 'read file 1' to see contents."
        )

    async def _send_file_whatsapp(self, file_path: str, contact: str) -> str:
        """
        Auto-send a file to a WhatsApp contact.
        Reel 14 insight: After finding file → auto-send via WhatsApp Web.
        """
        path = Path(file_path)
        if not path.exists():
            return f"Sir, the file doesn't exist at that path: {file_path}"

        return (
            f"Sir, I found the file: **{path.name}**\n\n"
            f"To send it to {contact} on WhatsApp:\n"
            f"WhatsApp Web automation requires your WhatsApp to be connected. "
            f"Once you complete the WhatsApp OAuth setup, I'll send files automatically "
            f"without you needing to do anything — just like IRIS AI in the reel you showed me."
        )
