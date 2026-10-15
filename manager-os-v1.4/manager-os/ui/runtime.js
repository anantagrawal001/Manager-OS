// Runtime controls: authenticated startup, connection recovery, saved tasks and keys.
let runtimeStarted = false;
let enrollmentRequired = false;
let awaitingReply = false;
let responseTimer = null;
let speakResponses = false;
let localRecording = null;

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {'Content-Type': 'application/json', Authorization: `Bearer ${_token}`, ...(options.headers || {})}
  });
  const data = await response.json();
  if (response.status === 401) { showLogin(); throw new Error('Please sign in again.'); }
  if (!response.ok) throw new Error(data.detail || 'Request failed');
  return data;
}

function showLogin() {
  continuousVoice = false;
  stopListening();
  if (localRecording) localRecording.stop(false);
  document.getElementById('runtime-panel')?.close();
  _token = '';
  sessionStorage.removeItem('mgr_token');
  document.getElementById('auth').classList.remove('hidden');
  document.getElementById('app').style.display = 'none';
  if (ws) { ws.onclose = null; ws.close(); }
  document.getElementById('auth-error').textContent = 'Your session ended. Sign in to continue.';
}

async function enterDashboard() {
  document.getElementById('auth').classList.add('hidden');
  document.getElementById('app').style.display = '';
  document.getElementById('auth-inp').value = '';
  if (!runtimeStarted) {
    mainOrb = new Orb(document.getElementById('orb'), 220, 1800);
    startClock();
    setInterval(() => { if (_token) pollMetrics(); }, 5000);
    setInterval(updateUptime, 1000);
    runtimeStarted = true;
  }
  const history = await api('/api/history?limit=60');
  document.getElementById('chat').replaceChildren();
  for (const item of history.history || []) addMsg(item.role === 'user' ? 'user' : 'mgr', item.content);
  document.getElementById('mem-count').textContent = (history.history || []).length;
  connectWS();
  pollMetrics();
}

async function initRuntime() {
  _token = sessionStorage.getItem('mgr_token') || '';
  authOrb = new Orb(document.getElementById('auth-orb'), 100, 400);
  buildAgentList();
  document.getElementById('auth-mic').hidden = true;
  document.getElementById('auth-sub-msg').textContent = 'Sign in with your existing passphrase, Sir.';
  const button = document.getElementById('auth-btn');
  const error = document.getElementById('auth-error');
  async function login() {
    if (button.disabled) return;
    button.disabled = true;
    error.textContent = '';
    try {
      const response = await fetch('/api/auth', {method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({passphrase: document.getElementById('auth-inp').value, enroll: enrollmentRequired})});
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Sign-in failed');
      if (!data.token) throw new Error('Server did not return a session.');
      _token = data.token;
      sessionStorage.setItem('mgr_token', _token);
      await enterDashboard();
    } catch (exc) { error.textContent = exc.message || 'Cannot reach Manager OS. Run startup.bat.'; }
    finally { button.disabled = false; }
  }
  button.addEventListener('click', login);
  document.getElementById('auth-inp').addEventListener('keydown', e => {if (e.key === 'Enter') login();});
  try {
    const response = await fetch('/api/auth/check', {headers: {Authorization: `Bearer ${_token}`}});
    if (!response.ok) throw new Error('Server unavailable');
    const state = await response.json();
    enrollmentRequired = state.enrollment_required;
    if (enrollmentRequired) {
      document.getElementById('auth-sub-msg').textContent = 'Create your private passphrase (at least 8 characters).';
      button.textContent = 'Create passphrase';
    }
    if (state.authenticated) await enterDashboard();
    else if (state.bypass) await login();
  } catch (exc) { error.textContent = 'Cannot reach Manager OS. Run startup.bat and refresh.'; }
}

function runtimeConnect() {
  if (!_token) return;
  if (ws) { ws.onclose = null; ws.close(); }
  ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws?token=${encodeURIComponent(_token)}`);
  ws.onopen = () => {
    document.querySelectorAll('.pill-online').forEach(el => el.textContent = '● Connected');
    document.getElementById('send').disabled = false;
  };
  ws.onmessage = event => {
    const data = JSON.parse(event.data);
    if (data.type === 'thinking') { showThinking(); mainOrb?.setState('thinking'); return; }
    if (data.type === 'response' || data.type === 'error') {
      removeThinking();
      awaitingReply = sending = false;
      clearTimeout(responseTimer);
      document.getElementById('send').disabled = false;
      mainOrb?.setState('idle');
      addMsg('mgr', data.content || 'No response received.');
      if (data.type === 'response') animCap(data.content);
      pollMetrics();
    } else if (data.type === 'alert') addMsg('mgr', data.content);
    else if (data.type === 'agent_hud') renderHUD(data.agents, data.recommendations || []);
    else if (data.type === 'speaking_state') {
      mainOrb?.setState(data.state === 'start' ? 'speaking' : 'idle');
      if (data.state === 'start') stopListening();
      else if (continuousVoice) startListening();
    }
  };
  ws.onclose = event => {
    document.querySelectorAll('.pill-online').forEach(el => el.textContent = '● Disconnected');
    document.getElementById('send').disabled = true;
    removeThinking();
    if (awaitingReply) addMsg('mgr', 'Connection interrupted. The action may still be running. Check history or status before repeating it.');
    awaitingReply = sending = false;
    clearTimeout(responseTimer);
    if (event.code === 4001 || event.code === 4003) showLogin();
    else if (_token) setTimeout(connectWS, 3000);
  };
  ws.onerror = () => ws.close();
}

function runtimeSend() {
  const input = document.getElementById('inp');
  const text = input.value.trim();
  if (awaitingReply || !text) return;
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    addMsg('mgr', 'Not connected yet. Your message is still in the input box.');
    return;
  }
  input.value = '';
  awaitingReply = sending = messageSent = true;
  accumulatedTranscript = '';
  isSilenceSend = false;
  clearTimeout(silenceTimer);
  stopListening();
  clearCap();
  addMsg('user', text);
  document.getElementById('send').disabled = true;
  ws.send(JSON.stringify({id: crypto.randomUUID(), type: 'text', content: text, speak: speakResponses}));
  responseTimer = setTimeout(() => {
    removeThinking();
    addMsg('mgr', 'This request is taking longer than expected. It may still be running; check status before repeating an action.');
  }, 110000);
}

function openPanel(title, html) {
  document.getElementById('runtime-panel')?.remove();
  const dialog = document.createElement('dialog');
  dialog.id = 'runtime-panel';
  dialog.innerHTML = `<div class="runtime-heading"><h2>${esc(title)}</h2><button id="close-panel" aria-label="Close panel">×</button></div>${html}<p id="panel-message" role="status"></p>`;
  document.body.appendChild(dialog);
  dialog.querySelector('#close-panel').onclick = () => dialog.close();
  dialog.showModal();
  return dialog;
}

async function showConnections() {
  const dialog = openPanel('Connections', `<p>Local AI is preferred. Cloud services need a valid key and available quota.</p>
    <div id="provider-list">Checking…</div><button id="check-providers">Check providers</button>
    <h3>Add or update an API key</h3><form id="key-form"><label>Provider <select id="key-provider">
    ${['groq','google','anthropic','openai','nvidia','cerebras','openrouter','deepseek'].map(p => `<option>${p}</option>`).join('')}
    </select></label><label>API key <input id="key-value" type="password" autocomplete="off" required minlength="8"></label>
    <button>Save key</button></form><p>WhatsApp and LinkedIn require sign-in in the automation browser. Live calls, broker orders and social publishing are not connected.</p>`);
  const render = state => {
    dialog.querySelector('#provider-list').innerHTML = Object.entries(state.providers || {}).map(([name, info]) =>
      `<div class="connection-row"><strong>${esc(name)}</strong><span>${esc(info.state.replaceAll('_',' '))}</span></div>`).join('');
    if (state.local_models?.length) dialog.querySelector('#provider-list').insertAdjacentHTML('beforeend', `<p>Installed chat models: ${esc(state.local_models.join(', '))}</p>`);
  };
  try { render(await api('/api/providers')); } catch (exc) { dialog.querySelector('#panel-message').textContent = exc.message; }
  dialog.querySelector('#check-providers').onclick = async event => {
    event.target.disabled = true;
    dialog.querySelector('#panel-message').textContent = 'Checking configured providers…';
    try {render(await api('/api/providers/check', {method:'POST'})); dialog.querySelector('#panel-message').textContent = 'Check complete.';}
    catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
    finally {event.target.disabled = false;}
  };
  dialog.querySelector('#key-form').onsubmit = async event => {
    event.preventDefault();
    try {
      await api('/api/key/add', {method:'POST', body:JSON.stringify({provider:dialog.querySelector('#key-provider').value, key:dialog.querySelector('#key-value').value})});
      dialog.querySelector('#key-value').value = '';
      dialog.querySelector('#panel-message').textContent = 'Key saved locally in the encrypted vault. Click Check providers to verify it.';
    } catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
  };
}

async function showTasks() {
  const dialog = openPanel('Tasks & reminders', `<p>Saved on this computer. Keep Manager OS running for reminder alerts.</p>
    <form id="task-form"><label>Task <input id="task-title" required maxlength="2000" placeholder="Prepare my resume"></label>
    <label>Reminder time (optional, local time) <input id="task-due" type="datetime-local"></label><button>Save task</button></form>
    <div id="task-list">Loading…</div>`);
  async function refresh() {
    const result = await api('/api/tasks');
    dialog.querySelector('#task-list').innerHTML = result.tasks.length ? result.tasks.map(t =>
      `<div class="task-row"><div><strong>#${t.id} ${esc(t.title)}</strong><small>${esc(t.due_at?.replace('T',' ') || 'No reminder time')}</small></div><button data-task="${t.id}">Complete</button></div>`).join('') : '<p>No open tasks.</p>';
    for (const button of dialog.querySelectorAll('[data-task]')) button.onclick = async () => {
      try {await api(`/api/tasks/${button.dataset.task}/complete`, {method:'POST'}); await refresh();}
      catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
    };
  }
  dialog.querySelector('#task-form').onsubmit = async event => {
    event.preventDefault();
    try {
      await api('/api/tasks', {method:'POST', body:JSON.stringify({title:dialog.querySelector('#task-title').value, due_at:dialog.querySelector('#task-due').value})});
      event.target.reset();
      dialog.querySelector('#panel-message').textContent = 'Task saved.';
      await refresh();
    } catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
  };
  try {await refresh();} catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
}

document.getElementById('connections-button').onclick = showConnections;
document.getElementById('tasks-button').onclick = showTasks;
document.getElementById('speech-button').onclick = event => {
  speakResponses = !speakResponses;
  event.target.textContent = speakResponses ? 'Speech: on' : 'Speech: off';
};
document.getElementById('logout-button').onclick = async () => {
  try { await api('/api/auth/logout', {method:'POST'}); } finally { showLogin(); }
};
document.getElementById('outputs-button').onclick = async () => {
  const dialog = openPanel('Outputs', '<p>Files created by Manager. Generated software is saved for review and is not executed automatically.</p><div id="output-list">Loading…</div>');
  try {
    const {files} = await api('/api/outputs');
    const list = dialog.querySelector('#output-list');
    list.replaceChildren();
    if (!files.length) list.textContent = 'No output files yet. Try “create file notes.txt with content Hello”.';
    for (const file of files) {
      const row = document.createElement('div');
      row.className = 'connection-row';
      const label = document.createElement('span');
      label.textContent = `${file.path} (${file.size} bytes)`;
      const button = document.createElement('button');
      button.textContent = 'Download';
      button.onclick = async () => {
        try {
          const response = await fetch(`/api/outputs/download?path=${encodeURIComponent(file.path)}`, {headers:{Authorization:`Bearer ${_token}`}});
          if (!response.ok) throw new Error('Download failed. Sign in again if your session expired.');
          const url = URL.createObjectURL(await response.blob());
          const link = document.createElement('a');
          link.href = url; link.download = file.path.split('/').pop(); link.click();
          setTimeout(() => URL.revokeObjectURL(url), 1000);
        } catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
      };
      row.append(label, button); list.append(row);
    }
  } catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
};

document.getElementById('local-mic-button').onclick = async () => {
  if (localRecording) {localRecording.stop(true); return;}
  const button = document.getElementById('local-mic-button');
  let stream = null, context = null;
  try {
    stream = await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true}});
    context = new AudioContext();
    const source = context.createMediaStreamSource(stream);
    const processor = context.createScriptProcessor(4096,1,1);
    const silent = context.createGain(); silent.gain.value = 0;
    const chunks = [];
    processor.onaudioprocess = event => chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    source.connect(processor); processor.connect(silent); silent.connect(context.destination);
    button.textContent = 'Stop recording';
    const timer = setTimeout(() => localRecording?.stop(true), 20000);
    let stopped = false;
    localRecording = {stop: async transcribe => {
      if (stopped) return; stopped = true;
      clearTimeout(timer); processor.disconnect(); source.disconnect();
      stream.getTracks().forEach(track => track.stop());
      const sampleRate = context.sampleRate;
      await context.close(); localRecording = null;
      button.textContent = 'Local mic';
      if (!transcribe || !_token) return;
      const sourceAudio = new Float32Array(chunks.reduce((n,c) => n+c.length,0));
      let offset = 0; for (const chunk of chunks) {sourceAudio.set(chunk,offset); offset += chunk.length;}
      const ratio = sampleRate/16000;
      const pcm = new Float32Array(Math.floor(sourceAudio.length/ratio));
      for (let i=0;i<pcm.length;i++) {
        const start=Math.floor(i*ratio), end=Math.min(Math.floor((i+1)*ratio),sourceAudio.length);
        let sum=0; for(let j=start;j<end;j++) sum+=sourceAudio[j];
        pcm[i]=sum/Math.max(1,end-start);
      }
      button.disabled=true; button.textContent='Transcribing…';
      try {
        const response=await fetch('/api/voice/transcribe',{method:'POST',headers:{Authorization:`Bearer ${_token}`,'Content-Type':'application/octet-stream'},body:pcm.buffer});
        const data=await response.json();
        if(!response.ok) throw new Error(data.detail || 'Local transcription failed');
        document.getElementById('inp').value=data.text || '';
        if (!data.text) addMsg('mgr','No speech detected. Please try again.');
        document.getElementById('inp').focus();
      } catch(exc) {addMsg('mgr',exc.message);}
      finally {button.disabled=false;button.textContent='Local mic';}
    }};
  } catch(exc) {
    stream?.getTracks().forEach(track=>track.stop());
    if(context) await context.close();
    button.textContent='Local mic';
    addMsg('mgr',`Microphone unavailable: ${exc.message}`);
  }
};

// Durable work is separate from simple reminders: real stages, saved outputs, recoverable failures.
const workButton = document.createElement('button');
workButton.id = 'work-button';
workButton.textContent = 'Work';
document.getElementById('tasks-button').before(workButton);
workButton.onclick = async () => {
  const dialog = openPanel('Work in progress', '<p>Project goals, resumes and document tasks run in the background. Projects include architecture, implementation, checks and repairs. Keep Manager running.</p><div id="work-list">Loading…</div><button id="work-refresh">Refresh</button><button id="work-outputs">Open outputs</button>');
  const refresh = async () => {
    try {
      const {workflows, focused_workflow_id} = await api('/api/workflows');
      const list = dialog.querySelector('#work-list');
      list.replaceChildren();
      if (!workflows.length) list.textContent = 'No work yet. Describe a project goal or document you want created.';
      for (const job of workflows) {
        const article = document.createElement('article');
        const title = document.createElement('h3');
        title.textContent = `${job.request} — ${job.status.replaceAll('_', ' ')}`;
        const steps = document.createElement('ol');
        for (const step of (job.steps || []).slice(-8)) {
          const item = document.createElement('li'); item.textContent = step; steps.append(item);
        }
        const detail = document.createElement('p');
        detail.textContent = job.question || job.error || `${job.outputs?.length || 0} saved files`;
        article.append(title, steps, detail);
        const focus = document.createElement('button');
        focus.textContent = job.id === focused_workflow_id ? 'Current task' : 'Use as current task';
        focus.disabled = job.id === focused_workflow_id;
        focus.onclick = async () => {
          focus.disabled = true;
          try {await api(`/api/workflows/${encodeURIComponent(job.id)}/focus`, {method:'POST'}); await refresh();}
          catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message; focus.disabled = false;}
        };
        article.append(focus);
        if (job.kind === 'project') {
          if (/^http:\/\/127\.0\.0\.1:\d+$/.test(job.preview_url || '')) {
            const link = document.createElement('a'); link.href = job.preview_url;
            link.target = '_blank'; link.rel = 'noopener'; link.textContent = 'Open project';
            article.append(link);
          }
          if (job.status === 'complete') {
            const launch = document.createElement('button'); launch.textContent = 'Start / restart project';
            launch.onclick = async () => {
              launch.disabled = true;
              try {await api(`/api/projects/${encodeURIComponent(job.id)}/open`, {method:'POST'}); await refresh();}
              catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
              finally {launch.disabled = false;}
            };
            article.append(launch);
          }
        }
        list.append(article);
      }
    } catch (exc) {dialog.querySelector('#panel-message').textContent = exc.message;}
  };
  dialog.querySelector('#work-refresh').onclick = refresh;
  dialog.querySelector('#work-outputs').onclick = () => {dialog.close(); document.getElementById('outputs-button').click();};
  const timer = setInterval(() => {if (dialog.open) refresh(); else clearInterval(timer);}, 3000);
  dialog.addEventListener('close', () => clearInterval(timer), {once:true});
  await refresh();
};
