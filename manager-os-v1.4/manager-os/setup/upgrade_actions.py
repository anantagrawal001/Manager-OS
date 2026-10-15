from pathlib import Path
from setup.source_edit import replace_definition as replace

replace('agents/files_agent.py', 'FilesAgent._launch_app', '''    async def _launch_app(self, request, context):
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
                    with winreg.OpenKey(root, r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\' + mapping[name]) as key:
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
''')
# Fix raw string ending in slash in generated source by using an ordinary escaped prefix.
p = Path('agents/files_agent.py')
s = p.read_text(encoding='utf-8').replace("r'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\'", "'SOFTWARE\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\App Paths\\\\'")
p.write_text(s, encoding='utf-8')

replace('agents/files_agent.py', 'FilesAgent._find_file', '''    async def _find_file(self, request, context):
        import re
        query = re.sub(r'^(?:please )?(?:find|search(?: for)?|locate|where is)\\s+(?:the\\s+)?(?:files?\\s+)?', '', request.strip(), flags=re.I)
        query = query.strip(' "\\\'?')
        if not query:
            return 'Sir, give me a filename or part of one, for example "find file invoice.pdf".'
        results = await asyncio.to_thread(self._search_files, [query.lower()])
        self._last_results = results[:10]
        if not results:
            return f'Sir, no filenames matched "{query}" in your configured search folders.'
        return 'Found these files, Sir:\\n' + '\\n'.join(f"{i+1}. {r['path']}" for i, r in enumerate(self._last_results)) + '\\nUse "read file 1" to read the first result.'
''')
replace('agents/files_agent.py', 'FilesAgent._search_files', '''    def _search_files(self, keywords):
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
''')
replace('agents/files_agent.py', 'FilesAgent._read_file', '''    async def _read_file(self, request, context):
        import re
        hint = re.sub(r'^(?:please )?(?:read|open|show(?: me)?)\\s+(?:the\\s+)?(?:file\\s+)?', '', request.strip(), flags=re.I).strip(' "\\\'')
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
            return f'{path}\\n\\n' + content[:12000] + ('\\n[Preview limited to 12000 characters]' if len(content) > 12000 else '')
        except OSError as exc:
            return f'Sir, file read failed ({type(exc).__name__}).'
''')
replace('agents/files_agent.py', 'FilesAgent._create_file', '''    async def _create_file(self, request, context):
        import re
        match = re.search(r'(?:create|write|save)(?: a)? file (.+?) (?:with content|containing|with text) (.+)', request, re.I | re.S)
        if not match:
            return 'Sir, use: create file notes.txt with content Your text here. Files are saved in outputs unless you give an absolute path.'
        name, content = match[1].strip(' "\\\''), match[2]
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
''')

# Give every domain prompt a truthful execution contract, including direct router calls.
p = Path('core/router.py')
s = p.read_text(encoding='utf-8').replace("        opts = self.config.get('ai_router', {})", "        system = self.MANAGER_SYSTEM_PROMPT + '\\n\\n' + (system or '')\n        opts = self.config.get('ai_router', {})", 1)
p.write_text(s, encoding='utf-8')
p = Path('core/ollama_client.py')
s = p.read_text(encoding='utf-8').replace("'model': model, 'messages': chat, 'stream': False,", "'model': model, 'messages': chat, 'stream': False, 'think': False,")
p.write_text(s, encoding='utf-8')

# Preserve the call simulation, but report it as a simulation and never fabricate a caller.
p = Path('agents/communication_agent.py')
s = p.read_text(encoding='utf-8')
s = s.replace("Sir, I answered an incoming recruiter call.", "Sir, the recruiter call simulation completed. No telephone call was connected.")
s = s.replace('Recruiter details:', 'Simulation transcript:')
p.write_text(s, encoding='utf-8')

# Do not claim resume tailoring happened when no resume was read or written.
p = Path('agents/career_agent.py')
s = p.read_text(encoding='utf-8').replace('Tailoring resume (Google XYZ formula) for:', 'Inspecting job listing:')
s = s.replace('Never use vague language like', 'Never invent experience, qualifications or metrics. Use only details supplied by the user.\nNever use vague language like')
p.write_text(s, encoding='utf-8')
print('Local file actions updated')
