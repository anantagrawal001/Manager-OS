"""Typed project tools. Separate working directories and dependencies, no shell strings."""
import hashlib
import ast
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import zipfile

import psutil


class ProjectTools:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.control = self.root / '.manager'
        self.control.mkdir(exist_ok=True)
        self.server = None
        self.server_log = None
        self.url = None
        self.processes = set()
        self.guard = threading.Lock()
        self.cancelled = False
        manifest = self.control/'written-files.json'
        self.written = set(json.loads(manifest.read_text(encoding='utf-8'))) if manifest.exists() else set()

    def path(self, name):
        if not isinstance(name, str) or not name or '\x00' in name:
            raise ValueError('A relative project path is required')
        value = PurePosixPath(name.replace('\\', '/'))
        if value.is_absolute() or '..' in value.parts or ':' in name:
            raise ValueError('Path must remain inside this project')
        if any(part.startswith('.') and part not in {'.gitignore', '.env.example'} for part in value.parts):
            raise ValueError('Runtime and control directories are not editable')
        if any(part.lower() in {'node_modules', '__pycache__'} or part.rstrip(' .') != part or
               re.fullmatch(r'(?i)(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', part) for part in value.parts):
            raise ValueError('Unsupported project path')
        target = (self.root / str(value)).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError('Path escapes the project')
        return target

    def files(self):
        result = []
        for base, directories, files in os.walk(self.root):
            directories[:] = [d for d in directories if d not in {'.venv', '.manager', 'node_modules', '__pycache__', '.git'} and not (Path(base)/d).is_symlink()]
            for name in files:
                path = Path(base)/name
                if path.is_symlink() or not path.resolve().is_relative_to(self.root):
                    continue
                result.append({'path': path.relative_to(self.root).as_posix(), 'bytes': path.stat().st_size})
                if len(result) >= 300:
                    return result
        return result

    def write(self, name, content):
        if not isinstance(content, str) or len(content) > 120000:
            raise ValueError('File content must be text, at most 120000 characters')
        path = self.path(name)
        if path.exists():
            digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
            previous = self.control/'revisions'/digest/path.relative_to(self.root)
            previous.parent.mkdir(parents=True, exist_ok=True)
            if not previous.exists():
                shutil.copy2(path, previous)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        self.written.add(path.relative_to(self.root).as_posix())
        (self.control/'written-files.json').write_text(json.dumps(sorted(self.written)), encoding='utf-8')
        return {'written': path.relative_to(self.root).as_posix(), 'bytes': path.stat().st_size}

    def read(self, name):
        return {'path': name, 'content': self.path(name).read_text(encoding='utf-8')[:50000]}

    def fingerprint(self):
        digest = hashlib.sha256()
        for item in sorted(self.files(), key=lambda f: f['path']):
            if item['path'] not in self.written and item['path'] not in {'package-lock.json', 'package.json'}:
                continue
            # Runtime data and reports are not source changes.
            if Path(item['path']).suffix.lower() not in {'.py', '.js', '.mjs', '.cjs', '.ts', '.tsx', '.jsx', '.html', '.css', '.svg', '.json', '.toml', '.yaml', '.yml', '.lock'} and Path(item['path']).name != 'requirements.txt':
                continue
            digest.update(item['path'].encode())
            digest.update((self.root/item['path']).read_bytes())
        return digest.hexdigest()

    def environment(self, port=None):
        names = ['PATH', 'SYSTEMROOT', 'WINDIR', 'PATHEXT', 'COMSPEC', 'TEMP', 'TMP']
        env = {name: os.environ[name] for name in names if name in os.environ}
        home = self.control/'home'
        home.mkdir(exist_ok=True)
        env.update({'HOME': str(home), 'USERPROFILE': str(home), 'PYTHONUTF8': '1',
                    'PYTHONUNBUFFERED': '1', 'PYTHONNOUSERSITE': '1',
                    'HOST': '127.0.0.1', 'MANAGER_PROJECT_ROOT': str(self.root)})
        if port is not None:
            env['PORT'] = str(port)
        return env

    def python(self):
        executable = self.root/'.venv'/('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
        if not executable.exists():
            result = self.run_process([sys.executable, '-m', 'venv', str(self.root/'.venv')], timeout=90)
            if result['exit_code'] != 0:
                raise RuntimeError('Project Python environment could not be created: ' + result['output'][-1500:])
        return str(executable)

    def command(self, runtime, args):
        if not isinstance(args, list) or not args or not all(isinstance(arg, str) and len(arg) < 2000 for arg in args):
            raise ValueError('args must be a nonempty list of arguments, not a shell command')
        if runtime == 'python':
            if args[0] == '-m':
                if len(args) < 2 or args[1] not in {'unittest', 'pytest', 'py_compile', 'compileall', 'uvicorn', 'http.server'}:
                    raise ValueError('Supported Python modules: unittest, pytest, py_compile, compileall, uvicorn, http.server')
            elif args[0].endswith('.py'):
                if not self.path(args[0]).is_file():
                    raise ValueError('Python entry point is missing')
            else:
                raise ValueError('Use a project Python file or supported module')
            executable = [self.python()]
        elif runtime == 'node':
            node = shutil.which('node')
            if not node:
                raise ValueError('Node.js is not installed')
            if args[0] not in {'--test', '--check'} and not self.path(args[0]).is_file():
                raise ValueError('Node entry point is missing')
            executable = [node]
        elif runtime == 'npm':
            node = shutil.which('node')
            cli = Path(node).parent/'node_modules/npm/bin/npm-cli.js' if node else Path('missing')
            if not node or not cli.exists():
                raise ValueError('npm is not installed in the supported Node location')
            if args[0] not in {'test', 'run', 'exec'}:
                raise ValueError('Use npm test or npm run for project scripts')
            if args[0] == 'exec':
                raise ValueError('Use an installed package through a named package.json script')
            executable = [node, str(cli)]
        else:
            raise ValueError('Available runtimes are python, node and npm')
        for argument in args:
            if '..' in PurePosixPath(argument.replace('\\', '/')).parts or re.match(r'^[A-Za-z]:[\\/]|^/', argument):
                raise ValueError('Command arguments cannot point outside this project')
        return executable + args

    def stop_process(self, process):
        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except psutil.NoSuchProcess:
                    pass
            parent.terminate()
            _, alive = psutil.wait_procs(children + [parent], timeout=3)
            for item in alive:
                try:
                    item.kill()
                except psutil.NoSuchProcess:
                    pass
        except psutil.NoSuchProcess:
            pass
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)

    def run_process(self, command, timeout=90, port=None):
        if self.cancelled:
            raise RuntimeError('Project work was cancelled')
        # CWD and environment separation are not an OS security sandbox.
        log = self.control/('command-' + str(time.time_ns()) + '.log')
        with log.open('wb') as output:
            process = subprocess.Popen(command, cwd=self.root, env=self.environment(port), stdin=subprocess.DEVNULL,
                stdout=output, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            with self.guard:
                self.processes.add(process)
            try:
                process.wait(timeout=timeout)
                timed_out = False
            except subprocess.TimeoutExpired:
                self.stop_process(process)
                timed_out = True
            finally:
                with self.guard:
                    self.processes.discard(process)
        with log.open('rb') as stream:
            stream.seek(max(0, log.stat().st_size - 24000))
            text = stream.read().decode('utf-8', errors='replace')
        return {'exit_code': process.returncode if not timed_out else -1, 'timed_out': timed_out, 'output': text}

    def placeholder_tests(self):
        placeholders = []
        for item in self.files():
            path = Path(item['path'])
            if not (path.name.startswith('test_') and path.suffix == '.py'):
                continue
            try:
                tree = ast.parse((self.root/path).read_text(encoding='utf-8'))
            except SyntaxError:
                continue  # Let the actual runner report the precise syntax error.
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                    body = [statement for statement in node.body if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str))]
                    if not body or all(isinstance(statement, ast.Pass) for statement in body):
                        placeholders.append(item['path'] + ':' + node.name)
        return placeholders

    def http_test(self, args):
        if not self.url or not self.server or self.server.poll() is not None:
            raise ValueError('Start the project server before http_test')
        path = args.get('path', '/')
        if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or '://' in path:
            raise ValueError('HTTP checks must use a path on the running project')
        import httpx
        files = None
        if args.get('file'):
            document = self.path(args['file'])
            files = {args.get('field', 'file'): (document.name, document.read_bytes())}
        with httpx.Client(timeout=60, follow_redirects=False) as client:
            response = client.request(args.get('method', 'GET'), self.url + path,
                json=args.get('json'), data=args.get('form'), files=files)
        assertions = 0
        if 'status' in args:
            if response.status_code != int(args['status']):
                raise ValueError(f'Expected HTTP {args["status"]}, got {response.status_code}: {response.text[:1200]}')
            assertions += 1
        for fragment in args.get('contains', []):
            if str(fragment) not in response.text:
                raise ValueError('Expected response text was absent: ' + str(fragment)[:200])
            assertions += 1
        if args.get('content_type'):
            if args['content_type'] not in response.headers.get('content-type', ''):
                raise ValueError('Unexpected response content type')
            assertions += 1
        if args.get('starts_with'):
            if not response.content.startswith(args['starts_with'].encode('utf-8')):
                raise ValueError('Response did not have the expected file signature')
            assertions += 1
        return {'passed': assertions > 0, 'assertions': assertions, 'status': response.status_code,
                'content_type': response.headers.get('content-type'), 'bytes': len(response.content)}

    def package_info(self, runtime, name):
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.@/-]{1,100}', name):
            raise ValueError('Invalid package name')
        if runtime == 'python':
            url = 'https://pypi.org/pypi/' + urllib.parse.quote(name, safe='') + '/json'
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.load(response)['info']
            return {'name': data['name'], 'version': data['version'], 'summary': data['summary'],
                    'requires_python': data.get('requires_python'), 'project_urls': data.get('project_urls'), 'source': url}
        if runtime == 'node':
            url = 'https://registry.npmjs.org/' + urllib.parse.quote(name, safe='') + '/latest'
            with urllib.request.urlopen(url, timeout=15) as response:
                data = json.load(response)
            return {'name': data['name'], 'version': data['version'], 'description': data.get('description'),
                    'engines': data.get('engines'), 'source': url}
        raise ValueError('Package runtime must be python or node')

    def install(self, runtime, packages):
        if not isinstance(packages, list) or not 1 <= len(packages) <= 20:
            raise ValueError('Provide 1–20 package requirements')
        if runtime == 'python':
            if not all(isinstance(p, str) and re.fullmatch(r'[A-Za-z0-9_.-]+(?:\[[A-Za-z0-9_,.-]+\])?(?:==[A-Za-z0-9_.+-]+)?', p) for p in packages):
                raise ValueError('Use package names with optional ==version; no shell commands or URLs')
            result = self.run_process([self.python(), '-m', 'pip', 'install', '--disable-pip-version-check'] + packages, timeout=180)
        elif runtime == 'node':
            if not all(isinstance(p, str) and re.fullmatch(r'(?:@[A-Za-z0-9_.-]+/)?[A-Za-z0-9_.-]+(?:@[A-Za-z0-9_.^~+-]+)?', p) for p in packages):
                raise ValueError('Use npm package names with optional versions')
            node = shutil.which('node')
            if not node:
                raise ValueError('Node is not installed')
            cli = Path(node).parent/'node_modules/npm/bin/npm-cli.js'
            result = self.run_process([node, str(cli), 'install', '--ignore-scripts', '--no-audit', '--no-fund'] + packages, timeout=180)
        else:
            raise ValueError('Package runtime must be python or node')
        return result

    def start_server(self, runtime, args):
        self.stop_server()
        with socket.socket() as connection:
            connection.bind(('127.0.0.1', 0))
            port = connection.getsockname()[1]
        if runtime == 'static':
            command = [sys.executable, '-m', 'http.server', str(port), '--bind', '127.0.0.1']
        else:
            args = [arg.replace('{port}', str(port)) for arg in args]
            command = self.command(runtime, args)
        self.server_log = (self.control/'server.log').open('wb')
        self.server = subprocess.Popen(command, cwd=self.root, env=self.environment(port), stdin=subprocess.DEVNULL,
            stdout=self.server_log, stderr=subprocess.STDOUT, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        self.url = f'http://127.0.0.1:{port}'
        for _ in range(100):
            if self.server.poll() is not None:
                self.server_log.flush()
                raise RuntimeError('Server exited: ' + (self.control/'server.log').read_text(encoding='utf-8', errors='replace')[-5000:])
            with socket.socket() as probe:
                if probe.connect_ex(('127.0.0.1', port)) == 0:
                    return {'url': self.url, 'running': True}
            time.sleep(.1)
        self.stop_server()
        raise RuntimeError('Server did not listen within 10 seconds. Bind HOST=127.0.0.1 and read the PORT environment variable.')

    def stop_server(self):
        if self.server is not None:
            self.stop_process(self.server)
            self.server = None
        if self.server_log:
            self.server_log.close()
            self.server_log = None
        self.url = None

    def browser_test(self, steps):
        if not self.url or not self.server or self.server.poll() is not None:
            raise ValueError('Start the project server before browser_test')
        if not isinstance(steps, list) or not 1 <= len(steps) <= 50:
            raise ValueError('Provide 1–50 browser steps')
        from playwright.sync_api import sync_playwright
        assertions = 0
        errors = []
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(channel='chrome', headless=True)
            except Exception:
                browser = playwright.chromium.launch(headless=True)
            try:
                page = browser.new_page(viewport={'width': 1440, 'height': 1000}, accept_downloads=True)
                origin = self.url
                page.route('**/*', lambda route: route.continue_() if route.request.url.startswith(origin + '/') else route.abort())
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(origin, wait_until='domcontentloaded')
                page.set_default_timeout(7000)
                for step in steps:
                    action = step.get('action')
                    selector = step.get('selector', '')
                    if action == 'fill':
                        page.locator(selector).fill(str(step.get('value', '')))
                    elif action == 'click':
                        page.locator(selector).click()
                    elif action == 'select':
                        page.locator(selector).select_option(str(step.get('value', '')))
                    elif action == 'press':
                        page.locator(selector).press(str(step.get('key', 'Enter')))
                    elif action == 'upload':
                        page.locator(selector).set_input_files(str(self.path(step['path'])))
                    elif action == 'assert_text':
                        from playwright.sync_api import expect
                        expect(page.locator(selector or 'body')).to_contain_text(str(step['text']))
                        assertions += 1
                    elif action == 'assert_visible':
                        page.locator(selector).wait_for(state='visible')
                        assertions += 1
                    elif action == 'assert_download':
                        with page.expect_download() as download_info:
                            page.locator(selector).click()
                        download = download_info.value
                        saved = download.path()
                        if not saved or Path(saved).stat().st_size == 0:
                            raise ValueError('The download is empty')
                        assertions += 1
                    elif action == 'reload':
                        page.reload(wait_until='domcontentloaded')
                    else:
                        raise ValueError('Unsupported browser action: ' + str(action))
                page.screenshot(path=str(self.control/'preview.png'), full_page=True)
                if errors:
                    raise ValueError('Browser JavaScript errors: ' + '; '.join(errors)[:2000])
                return {'passed': assertions > 0, 'assertions': assertions, 'console_errors': errors, 'screenshot': '.manager/preview.png'}
            finally:
                browser.close()

    def archive(self, destination):
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
            for item in self.files():
                if item['path'] not in self.written and item['path'] not in {'package-lock.json', 'package.json'}:
                    continue
                if item['path'].endswith(('.db', '.sqlite', '.log')) or Path(item['path']).name == '.env':
                    continue
                archive.write(self.root/item['path'], item['path'])
        return str(destination)

    def close(self):
        self.cancelled = True
        with self.guard:
            processes = list(self.processes)
        for process in processes:
            self.stop_process(process)
        self.stop_server()
