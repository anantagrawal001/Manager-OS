from pathlib import Path
p = Path('ui/dashboard.html')
s = p.read_text(encoding='utf-8')
def replace_js(start, end, replacement):
    global s
    left=s.index(start)
    right=s.index(end,left)
    old=s[left:right]
    s=s[:left] + '\n'.join('// Archived 2026-10-12: '+line for line in old.splitlines()) + '\n' + replacement + '\n' + s[right:]
replace_js("    window.addEventListener('load', () => {", '    // ─── AGENT LIST', "    window.addEventListener('load', () => initRuntime());")
replace_js('    function connectWS() {', '    // ─── SEND', '    function connectWS() { runtimeConnect(); }')
replace_js('    function send() {', "    document.getElementById('send').addEventListener", '    function send() { runtimeSend(); }')
s=s.replace('let continuousVoice = true', 'let continuousVoice = false')
s=s.replace('class="btn-icon active" id="continuous-voice" title="Continuous Conversation Mode: Active"', 'class="btn-icon" id="continuous-voice" title="Continuous Conversation Mode: Off"')
s=s.replace('title="Voice input"', 'title="Voice input (browser speech service; may use the internet)"')
s=s.replace('<span class="pill pill-secure">Secure</span>', '<span class="pill pill-secure">Local app</span>')
s=s.replace('<span class="pill pill-encrypted">Encrypted</span>', '<span class="pill pill-encrypted">Private vault</span>')
s=s.replace('<span class="pill pill-live">Live</span>', '<span class="pill pill-live">Personal workspace</span>')
s=s.replace('LAT 28.614N · LON 77.209E · ALT 220M', 'RUNNING ON THIS COMPUTER')
s=s.replace('All systems online, Sir.', 'Ready for your request, Sir.')
s=s.replace('Active Agents</div>', 'Available Agents</div>')
s=s.replace('Requests Today</div>', 'Requests This Session</div>')
s=s.replace('>Ollama</div>', '>Checking…</div>')
s=s.replace("document.getElementById('lat').textContent = '<5ms';", "document.getElementById('lat').textContent = `${Math.round(performance.now() - metricStart)}ms`;")
s=s.replace("    async function pollMetrics() {\n      try {", "    async function pollMetrics() {\n      const metricStart = performance.now();\n      try {")
s=s.replace("if (wp.length > 0) {", "if (wp.length > 0) {")
s=s.replace("document.getElementById('model').textContent = wp[0];", "document.getElementById('model').textContent = rt.last_model || wp[0];")
s=s.replace("        const calls = Object.values", "        if (!wp.length) { document.getElementById('model').textContent = 'Not connected'; document.getElementById('models-sub').textContent = 'Open Connections'; }\n        const calls = Object.values")
s=s.replace('agents active`', 'agents loaded`')
s=s.replace("ast.textContent = ok ? 'OK' : 'ERR'", "ast.textContent = ok ? 'READY' : 'ERR'")
s=s.replace('id="ast-${a.key}">OK', 'id="ast-${a.key}">CHECK')
# No microphone is started implicitly. Remove legacy global click-to-listen registration if present.
s=s.replace("          startClapDetection();", "          // Clap detection is opt-in only.")
toolbar='''<div class="runtime-toolbar"><button id="tasks-button">Tasks &amp; reminders</button><button id="connections-button">Connections</button><button id="speech-button">Speech: off</button><button id="logout-button">Lock</button></div>'''
s=s.replace('    <!-- MAIN -->', toolbar+'\n    <!-- MAIN -->')
s=s.replace('</body>', '  <script src="/client.js"></script>\n</body>')
css='''
    .runtime-toolbar {display:flex;gap:8px;padding:8px 24px;flex-wrap:wrap;grid-column:1/-1;}
    .runtime-toolbar button, #runtime-panel button {border:1px solid #294558;border-radius:7px;background:#102536;color:#b9e4ff;padding:8px 12px;cursor:pointer;}
    button:disabled {opacity:.45;cursor:wait;}
    #runtime-panel {position:fixed;inset:0;margin:auto;width:min(640px,94vw);max-height:85vh;overflow:auto;background:#08131d;color:#dfedfa;border:1px solid #31536b;border-radius:16px;padding:24px;font:14px/1.6 system-ui;}
    #runtime-panel::backdrop {background:rgba(0,0,0,.75);}
    #runtime-panel h2 {margin:0;font-size:20px;}
    .runtime-heading {display:flex;align-items:center;justify-content:space-between;}
    #runtime-panel form {display:grid;gap:12px;margin:16px 0;}
    #runtime-panel label {display:grid;gap:5px;}
    #runtime-panel input,#runtime-panel select {padding:10px;background:#122330;border:1px solid #31536b;color:white;border-radius:6px;width:100%;box-sizing:border-box;}
    .connection-row,.task-row {display:flex;gap:16px;justify-content:space-between;align-items:center;padding:12px 0;border-bottom:1px solid #233a4b;}
    .task-row small {display:block;color:#8db0c9;}
    #panel-message {color:#8fdbb5;}
'''
s=s.replace('  </style>', css+'\n  </style>')
p.write_text(s,encoding='utf-8')
p=Path('main.py')
s=p.read_text(encoding='utf-8')
pos=s.index('\ndef local_origins():')
s=s[:pos]+'''\n@app.get('/client.js')
async def client_script():
    return FileResponse(str(ui_dir / 'runtime.js'), media_type='application/javascript')
\n'''+s[pos:]
p.write_text(s,encoding='utf-8')
print('Dashboard runtime controls updated')
