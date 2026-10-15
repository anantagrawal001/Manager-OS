import { useState, useEffect } from "react";

const C = {
  bg: "#020406",
  cyan: "#00f5ff",
  gold: "#ffd60a",
  red: "#ff3b30",
  green: "#00ff88",
  purple: "#bf5af2",
  orange: "#ff6b35",
  pink: "#ff3d9a",
  amber: "#ff9f0a",
  white: "#f0f4f8",
  dim: "#0d1117",
  card: "#0a0f16",
  border: "#1a2332",
  muted: "#3a4a5a",
  text: "#8899aa",
};

const layers = [
  {
    id: "anant",
    label: "ANANT",
    sub: "Voice · Text · Command",
    color: C.gold,
    icon: "👤",
    desc: "Owner & only user. Interacts via voice or text from anywhere in the world.",
  },
  {
    id: "brain",
    label: "MANAGER BRAIN",
    sub: "Intent → Plan → Orchestrate → Review → Polish",
    color: C.cyan,
    icon: "🧠",
    desc: "The core intelligence. Understands requests, breaks into subtasks, routes to correct domains, reviews output, polishes before delivery.",
    children: ["Intent Parser", "Task Planner", "Orchestrator", "Reviewer", "Polisher"],
  },
  {
    id: "ai",
    label: "AI ROUTING LAYER",
    sub: "Best model per task · Multi-key rotation · Zero interruption",
    color: C.purple,
    icon: "⚡",
    desc: "Auto-selects best AI model per task. Manages multiple API keys per provider. Switches before limit hits. Context preserved always.",
    children: ["Claude", "GPT-4o", "Gemini", "Ollama Local", "DALL-E 3", "Runway ML"],
  },
  {
    id: "domains",
    label: "DOMAIN PLUGINS",
    sub: "Modular · Plug in/out · Zero breakage",
    color: C.green,
    icon: "🔌",
    desc: "Each domain is an independent plugin. Add or remove without breaking anything. All inherit from base_domain.py.",
    children: ["Trading", "Career", "Communication", "Social Media", "Builder", "Creative", "Files", "Security"],
  },
  {
    id: "infra",
    label: "INFRASTRUCTURE",
    sub: "FastAPI · SQLite · Tailscale · Encryption",
    color: C.orange,
    icon: "🖥️",
    desc: "The foundation. Private network, encrypted storage, background server on old laptop, always-on process management.",
    children: ["FastAPI Server", "SQLite + ChromaDB", "Tailscale VPN", "AES-256 Encryption", "Old Laptop Server", "n8n Workflows"],
  },
];

const domainCards = [
  { id: "trading", label: "TRADING & FINANCE", icon: "📈", color: C.green, phase: 2,
    caps: ["Candlestick analysis", "Sentiment engine", "Demat orders", "Portfolio tracker", "Gold inventory + OCR", "Risk management"] },
  { id: "career", label: "CAREER & JOBS", icon: "💼", color: C.orange, phase: 3,
    caps: ["24/7 job scanning", "Resume per application", "Cold emails", "Application tracker", "Interview coaching"] },
  { id: "comms", label: "COMMUNICATION", icon: "📞", color: C.pink, phase: 3,
    caps: ["Takes calls for Anant", "Post-call summary", "WhatsApp management", "Gmail management", "DM across platforms"] },
  { id: "social", label: "SOCIAL MEDIA", icon: "🚀", color: C.purple, phase: 4,
    caps: ["Instagram (personal + pro)", "Reel creation pipeline", "Peak-time posting", "Daily analytics", "Brand deal pipeline"] },
  { id: "builder", label: "PROJECT BUILDER", icon: "⚙️", color: C.gold, phase: 4,
    caps: ["Idea → production app", "Any language/framework", "n8n automations", "Full deployment pipeline"] },
  { id: "creative", label: "CREATIVE STUDIO", icon: "🎨", color: C.amber, phase: 4,
    caps: ["Images, logos, posters", "Video & reel production", "Scripts & copy", "Always cinematic quality"] },
  { id: "files", label: "FILE ACCESS", icon: "📁", color: C.cyan, phase: 1,
    caps: ["Read/write all laptop files", "Smart file organization", "Search across system", "Watch folder changes"] },
  { id: "security", label: "PRIVACY & SECURITY", icon: "🔐", color: C.red, phase: 1,
    caps: ["Only Anant verified", "Data invisible to all", "No provider data access", "AES-256 everywhere"] },
];

const aiMatrix = [
  { model: "Claude Sonnet", task: "Code & reasoning", cost: "Free tier", color: C.orange },
  { model: "GPT-4o", task: "Writing & analysis", cost: "Free tier", color: C.green },
  { model: "Gemini Pro", task: "Research & multimodal", cost: "Free", color: C.cyan },
  { model: "Ollama (local)", task: "Offline LLM", cost: "100% Free", color: C.purple },
  { model: "DALL-E 3", task: "Image generation", cost: "Free tier", color: C.pink },
  { model: "Runway ML", task: "Video generation", cost: "Free tier", color: C.amber },
  { model: "Perplexity", task: "Live research", cost: "Free tier", color: C.gold },
  { model: "Llama 3.1", task: "Local fast LLM", cost: "100% Free", color: C.red },
  { model: "Flux", task: "Alt image gen", cost: "Free", color: C.green },
  { model: "Kimi K2", task: "Free reasoning", cost: "Free", color: C.purple },
  { model: "Mistral 7B", task: "Local reasoning", cost: "100% Free", color: C.orange },
  { model: "Emergent AI", task: "App building", cost: "Free tier", color: C.cyan },
];

const phases = [
  { n: 1, label: "CORE + VOICE + IDENTITY + FILES", color: C.cyan,
    items: ["Wake word detection", "Speech-to-text (Whisper)", "Text-to-speech (Coqui)", "Intent parser", "Task planner", "AI router + multi-key", "Identity verification", "Memory system", "File access module", "Private network (Tailscale)", "FastAPI server", "setup.bat one-click install"] },
  { n: 2, label: "TRADING & FINANCE ENGINE", color: C.green,
    items: ["Live market data", "Candlestick analysis", "News sentiment", "Demat integration", "Order execution", "Portfolio tracker", "Gold/silver inventory", "Risk management"] },
  { n: 3, label: "CAREER + COMMUNICATION", color: C.orange,
    items: ["Job portal scanner", "Resume engine (ATS)", "Cold email system", "Application tracker", "Interview coach", "Call handler", "WhatsApp + Gmail", "DM management"] },
  { n: 4, label: "SOCIAL + CREATIVE + BUILDER", color: C.purple,
    items: ["Instagram management", "Reel creation pipeline", "Brand deal outreach", "Image/video generation", "Project generator", "n8n workflow builder", "Content calendar"] },
  { n: 5, label: "FULL INTEGRATION + SELF-GROWTH", color: C.gold,
    items: ["All domains interconnected", "Weekly new tool scanner", "Skill integration pipeline", "Old laptop as full server", "Complete worldwide access", "Cinematic dashboard live"] },
];

const folderTree = [
  { name: "MANAGER/", type: "root", color: C.cyan },
  { name: "  MANAGER_STRUCTURE.md", type: "critical", color: C.gold, note: "LIVING LOG — APPEND ONLY" },
  { name: "  setup.bat", type: "file", color: C.green, note: "ONE-CLICK SETUP" },
  { name: "  .env", type: "secure", color: C.red, note: "ENCRYPTED — NEVER COMMIT" },
  { name: "  core/", type: "folder", color: C.cyan },
  { name: "    voice/", type: "folder", color: C.muted },
  { name: "      stt.py  tts.py  wake_word.py", type: "files", color: C.text },
  { name: "    brain/", type: "folder", color: C.muted },
  { name: "      intent.py  planner.py  orchestrator.py  reviewer.py  polisher.py", type: "files", color: C.text },
  { name: "    identity/  memory/", type: "folders", color: C.muted },
  { name: "  ai_router/", type: "folder", color: C.purple },
  { name: "    selector.py  key_manager.py  context_bridge.py  usage_tracker.py", type: "files", color: C.text },
  { name: "    models/ (claude · openai · gemini · local · image · video)", type: "files", color: C.text },
  { name: "  domains/", type: "folder", color: C.green },
  { name: "    plugin_manager.py  base_domain.py", type: "files", color: C.text },
  { name: "    trading/  career/  communication/  social/", type: "folders", color: C.muted },
  { name: "    builder/  creative/  files/  security/", type: "folders", color: C.muted },
  { name: "  infrastructure/", type: "folder", color: C.orange },
  { name: "    server/  network/  storage/  old_laptop/", type: "folders", color: C.muted },
  { name: "  ui/", type: "folder", color: C.pink },
  { name: "    dashboard/ (React)  visualizer/", type: "folders", color: C.muted },
  { name: "  keys/", type: "secure", color: C.red, note: "AES-256 ENCRYPTED VAULT" },
  { name: "  logs/  tests/", type: "folders", color: C.muted },
];

function Tag({ label, color }) {
  return (
    <span style={{ fontSize: 8, letterSpacing: 2, color, border: `1px solid ${color}40`, borderRadius: 4, padding: "2px 6px" }}>
      {label}
    </span>
  );
}

function SectionHead({ label, color = C.cyan, sub }) {
  return (
    <div style={{ marginBottom: 28 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
        <span style={{ width: 5, height: 5, borderRadius: "50%", background: color, boxShadow: `0 0 8px ${color}`, display: "inline-block" }} />
        <span style={{ fontSize: 10, letterSpacing: 5, color, fontWeight: 700 }}>{label}</span>
        <div style={{ flex: 1, height: 1, background: `linear-gradient(to right,${color}30,transparent)` }} />
      </div>
      {sub && <div style={{ fontSize: 10, color: C.muted, letterSpacing: 1, marginLeft: 15 }}>{sub}</div>}
    </div>
  );
}

export default function ManagerArchitecture() {
  const [tab, setTab] = useState("architecture");
  const [expandedDomain, setExpandedDomain] = useState(null);
  const [expandedPhase, setExpandedPhase] = useState(null);
  const [expandedLayer, setExpandedLayer] = useState(null);
  const [clock, setClock] = useState("");
  const [pulse, setPulse] = useState(0);

  useEffect(() => {
    const i = setInterval(() => setClock(new Date().toLocaleTimeString("en-IN", { hour12: false })), 1000);
    return () => clearInterval(i);
  }, []);

  useEffect(() => {
    const i = setInterval(() => setPulse(p => (p + 1) % layers.length), 700);
    return () => clearInterval(i);
  }, []);

  const tabs = [
    { id: "architecture", label: "SYSTEM LAYERS" },
    { id: "domains", label: "DOMAIN PLUGINS" },
    { id: "ai", label: "AI MATRIX" },
    { id: "phases", label: "BUILD PHASES" },
    { id: "folder", label: "FOLDER STRUCTURE" },
  ];

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "'Courier New', monospace", color: C.white, position: "relative", overflowX: "hidden" }}>

      {/* Grid bg */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0,
        backgroundImage: `linear-gradient(${C.cyan}06 1px,transparent 1px),linear-gradient(90deg,${C.cyan}06 1px,transparent 1px)`,
        backgroundSize: "44px 44px" }} />

      {/* Corner brackets */}
      {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
        <div key={v+h} style={{ position:"fixed",[v]:16,[h]:16,width:28,height:28,zIndex:0,pointerEvents:"none",
          borderTop:v==="top"?`1px solid ${C.cyan}25`:"none", borderBottom:v==="bottom"?`1px solid ${C.cyan}25`:"none",
          borderLeft:h==="left"?`1px solid ${C.cyan}25`:"none", borderRight:h==="right"?`1px solid ${C.cyan}25`:"none" }} />
      ))}

      <div style={{ position: "relative", zIndex: 1, maxWidth: 1180, margin: "0 auto", padding: "28px 20px 72px" }}>

        {/* STATUS BAR */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:40, flexWrap:"wrap", gap:8 }}>
          <div style={{ display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ width:7,height:7,borderRadius:"50%",background:C.green,boxShadow:`0 0 10px ${C.green}`,display:"inline-block",animation:"blink 1.4s infinite" }} />
            <span style={{ fontSize:9,letterSpacing:4,color:C.green }}>ARCHITECTURE LOADED</span>
          </div>
          <div style={{ display:"flex", gap:16, flexWrap:"wrap" }}>
            <span style={{ fontSize:9,letterSpacing:2,color:C.muted }}>v0.1.0</span>
            <span style={{ fontSize:9,letterSpacing:2,color:C.muted }}>2026-05-22</span>
            <span style={{ fontSize:9,letterSpacing:2,color:C.muted }}>{clock} IST</span>
          </div>
        </div>

        {/* HERO */}
        <div style={{ textAlign:"center", marginBottom:52 }}>
          <div style={{ fontSize:9,letterSpacing:8,color:C.cyan,opacity:0.4,marginBottom:12 }}>
            PERSONAL AI OPERATING SYSTEM — CLASSIFIED
          </div>
          <h1 style={{ fontSize:"clamp(52px,10vw,100px)",fontWeight:900,letterSpacing:-4,margin:0,lineHeight:1,
            background:`linear-gradient(135deg,#fff 0%,${C.cyan} 40%,#fff 70%)`,
            WebkitBackgroundClip:"text",WebkitTextFillColor:"transparent",backgroundClip:"text",
            backgroundSize:"200%",animation:"shimmer 4s infinite linear" }}>
            MANAGER
          </h1>
          <div style={{ fontSize:10,color:C.muted,letterSpacing:5,marginTop:8 }}>ARCHITECTURE v0.1.0 — BUILT FOR ANANT</div>

          <div style={{ display:"flex",justifyContent:"center",gap:10,marginTop:28,flexWrap:"wrap" }}>
            {[["9","DOMAINS"],["80+","CAPABILITIES"],["12+","AI MODELS"],["5","PHASES"],["∞","API KEYS"],["GLOBAL","ACCESS"]].map(([v,l]) => (
              <div key={l} style={{ background:`${C.cyan}05`,border:`1px solid ${C.cyan}15`,borderRadius:100,padding:"8px 18px",textAlign:"center" }}>
                <div style={{ fontSize:18,fontWeight:900,color:C.cyan,lineHeight:1 }}>{v}</div>
                <div style={{ fontSize:7,letterSpacing:3,color:C.muted,marginTop:3 }}>{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* TABS */}
        <div style={{ display:"flex",gap:2,marginBottom:28,borderBottom:`1px solid ${C.border}`,overflowX:"auto",paddingBottom:0 }}>
          {tabs.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)} style={{
              background:"none",border:"none",cursor:"pointer",padding:"10px 14px",whiteSpace:"nowrap",
              fontSize:9,letterSpacing:3,fontFamily:"monospace",
              color:tab===t.id?C.cyan:C.muted,
              borderBottom:tab===t.id?`2px solid ${C.cyan}`:"2px solid transparent",
              transition:"all 0.2s"
            }}>{t.label}</button>
          ))}
        </div>

        {/* TAB: ARCHITECTURE */}
        {tab==="architecture" && (
          <div>
            <SectionHead label="LAYERED SYSTEM ARCHITECTURE" color={C.cyan} sub="Click any layer to see details — data flows top to bottom" />
            <div style={{ display:"flex",flexDirection:"column",gap:8 }}>
              {layers.map((layer,i) => {
                const open = expandedLayer===layer.id;
                const active = pulse===i;
                return (
                  <div key={layer.id} onClick={() => setExpandedLayer(open?null:layer.id)} style={{
                    background: open?`${layer.color}08`:active?`${layer.color}04`:C.card,
                    border:`1px solid ${open?layer.color+"50":active?layer.color+"25":C.border}`,
                    borderRadius:10,overflow:"hidden",cursor:"pointer",transition:"all 0.3s",
                    boxShadow:open?`0 0 28px ${layer.color}12`:"none"
                  }}>
                    <div style={{ padding:"16px 20px",display:"flex",alignItems:"center",gap:16,flexWrap:"wrap" }}>
                      {/* Layer number */}
                      <span style={{ fontSize:9,color:layer.color,opacity:0.4,minWidth:20 }}>
                        L{String(i+1).padStart(2,"0")}
                      </span>
                      {/* Icon */}
                      <span style={{ fontSize:20 }}>{layer.icon}</span>
                      {/* Label */}
                      <div style={{ flex:1,minWidth:120 }}>
                        <div style={{ fontSize:11,fontWeight:700,letterSpacing:2,color:active||open?layer.color:C.white }}>
                          {layer.label}
                        </div>
                        <div style={{ fontSize:9,color:C.muted,marginTop:3 }}>{layer.sub}</div>
                      </div>
                      {/* Children tags */}
                      {layer.children && (
                        <div style={{ display:"flex",gap:6,flexWrap:"wrap" }}>
                          {layer.children.map(c=>(
                            <Tag key={c} label={c} color={layer.color} />
                          ))}
                        </div>
                      )}
                      <span style={{ color:layer.color,fontSize:10,opacity:0.5 }}>{open?"▲":"▼"}</span>
                    </div>
                    {open && (
                      <div style={{ borderTop:`1px solid ${layer.color}15`,padding:"16px 20px",background:`${layer.color}04` }}>
                        <p style={{ fontSize:11,color:C.text,lineHeight:1.8,margin:0 }}>{layer.desc}</p>
                      </div>
                    )}
                    {/* Flow arrow */}
                    {i<layers.length-1 && (
                      <div style={{ textAlign:"center",padding:"2px 0",background:`${layer.color}08`,fontSize:10,color:layer.color,opacity:0.3 }}>
                        ↓
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            {/* Workflow loop */}
            <div style={{ marginTop:32,background:C.card,border:`1px solid ${C.border}`,borderRadius:12,padding:24 }}>
              <SectionHead label="MANAGER WORKFLOW LOOP" color={C.gold} />
              <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(140px,1fr))",gap:6 }}>
                {[
                  {n:"01",l:"REQUEST",d:"Voice or text",c:C.cyan},
                  {n:"02",l:"INTENT",d:"Understand ask",c:C.gold},
                  {n:"03",l:"PLAN",d:"Break subtasks",c:C.purple},
                  {n:"04",l:"ROUTE",d:"Pick AI + domain",c:C.green},
                  {n:"05",l:"EXECUTE",d:"Parallel agents",c:C.orange},
                  {n:"06",l:"REVIEW",d:"Correct output?",c:C.amber},
                  {n:"07",l:"POLISH",d:"Add perspective",c:C.pink},
                  {n:"08",l:"DELIVER",d:"Cinematic output",c:C.cyan},
                ].map(s=>(
                  <div key={s.n} style={{ background:`${s.c}08`,border:`1px solid ${s.c}25`,borderRadius:8,padding:14,textAlign:"center" }}>
                    <div style={{ fontSize:28,fontWeight:900,color:s.c,opacity:0.25,lineHeight:1 }}>{s.n}</div>
                    <div style={{ fontSize:9,fontWeight:700,letterSpacing:2,color:s.c,margin:"6px 0 4px" }}>{s.l}</div>
                    <div style={{ fontSize:8,color:C.muted }}>{s.d}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop:14,padding:14,background:`${C.red}06`,border:`1px solid ${C.red}20`,borderRadius:8 }}>
                <span style={{ fontSize:9,color:C.red,letterSpacing:2 }}>REVIEW LOOP: </span>
                <span style={{ fontSize:9,color:C.text }}>If output incorrect → re-evaluate request → re-route to tools → execute again → review again → loop until correct</span>
              </div>
            </div>

            {/* Key rotation */}
            <div style={{ marginTop:16,background:C.card,border:`1px solid ${C.purple}25`,borderRadius:12,padding:24 }}>
              <SectionHead label="MULTI-API KEY ROTATION" color={C.purple} />
              <div style={{ fontFamily:"monospace",fontSize:10,color:C.text,lineHeight:2 }}>
                <span style={{ color:C.purple }}>Anthropic Pool: </span> Key_1 (active) → Key_2 (standby) → Key_3 (standby) → ...<br/>
                <span style={{ color:C.green }}>OpenAI Pool: </span>&nbsp;&nbsp;&nbsp; Key_1 (active) → Key_2 (standby) → Key_3 (standby) → ...<br/>
                <span style={{ color:C.cyan }}>Gemini Pool: </span>&nbsp;&nbsp;&nbsp;&nbsp; Key_1 (active) → Key_2 (standby) → ...<br/>
                <div style={{ marginTop:10,padding:10,background:`${C.gold}08`,border:`1px solid ${C.gold}20`,borderRadius:6 }}>
                  <span style={{ color:C.gold,fontSize:9 }}>RULE: </span>
                  <span style={{ color:C.text,fontSize:9 }}>At 80% usage → proactive switch. Context preserved via context_bridge.py. Anant never notices. Free tier = effectively unlimited.</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB: DOMAINS */}
        {tab==="domains" && (
          <div>
            <SectionHead label="MODULAR DOMAIN PLUGINS" color={C.green} sub="Each domain is independent — add/remove without breaking anything" />
            <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))",gap:12 }}>
              {domainCards.map(d=>{
                const open=expandedDomain===d.id;
                return (
                  <div key={d.id} onClick={()=>setExpandedDomain(open?null:d.id)} style={{
                    background:open?`${d.color}08`:C.card,
                    border:`1px solid ${open?d.color+"50":C.border}`,
                    borderRadius:10,padding:18,cursor:"pointer",
                    transition:"all 0.25s",boxShadow:open?`0 0 24px ${d.color}15`:"none",
                    transform:open?"translateY(-2px)":"none"
                  }}>
                    <div style={{ display:"flex",alignItems:"center",justifyContent:"space-between",marginBottom:10 }}>
                      <div style={{ display:"flex",alignItems:"center",gap:10 }}>
                        <span style={{ fontSize:18 }}>{d.icon}</span>
                        <span style={{ fontSize:9,fontWeight:700,letterSpacing:2,color:open?d.color:C.white }}>{d.label}</span>
                      </div>
                      <Tag label={`PH${d.phase}`} color={d.color} />
                    </div>
                    {!open && <div style={{ fontSize:9,color:C.muted }}>Tap to expand capabilities</div>}
                    {open && (
                      <div style={{ borderTop:`1px solid ${d.color}18`,paddingTop:14 }}>
                        {d.caps.map((c,i)=>(
                          <div key={i} style={{ display:"flex",gap:8,marginBottom:8,animation:`fadeIn 0.12s ease ${i*0.03}s both` }}>
                            <span style={{ color:d.color,fontSize:7,marginTop:4,flexShrink:0 }}>▶</span>
                            <span style={{ fontSize:10,color:C.text,lineHeight:1.6 }}>{c}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div style={{ marginTop:20,background:C.card,border:`1px solid ${C.green}20`,borderRadius:10,padding:18 }}>
              <div style={{ fontSize:9,color:C.green,letterSpacing:3,marginBottom:10 }}>PLUGIN RULES</div>
              {["All domains inherit from base_domain.py",
                "Adding: create folder → register in plugin_manager.py → done",
                "Removing: comment out in plugin_manager.py with reason + date → done",
                "Zero other files touched on add or remove"].map((r,i)=>(
                <div key={i} style={{ display:"flex",gap:8,marginBottom:8 }}>
                  <span style={{ color:C.green,fontSize:7,marginTop:4 }}>◆</span>
                  <span style={{ fontSize:10,color:C.text }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: AI MATRIX */}
        {tab==="ai" && (
          <div>
            <SectionHead label="AI ROUTING MATRIX" color={C.purple} sub="Manager auto-selects — quality + cost efficiency — always free tier maximized" />
            <div style={{ display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(170px,1fr))",gap:10,marginBottom:24 }}>
              {aiMatrix.map(ai=>(
                <div key={ai.model} style={{ background:`${ai.color}06`,border:`1px solid ${ai.color}20`,borderRadius:10,padding:14 }}>
                  <div style={{ fontSize:12,fontWeight:700,color:C.white,marginBottom:4 }}>{ai.model}</div>
                  <div style={{ fontSize:9,color:ai.color,marginBottom:6,letterSpacing:1 }}>{ai.task}</div>
                  <Tag label={ai.cost} color={ai.color} />
                </div>
              ))}
            </div>
            <div style={{ background:C.card,border:`1px solid ${C.cyan}20`,borderRadius:12,padding:22 }}>
              <div style={{ fontSize:9,letterSpacing:3,color:C.cyan,marginBottom:14 }}>ROUTING DECISION TABLE</div>
              {[
                ["Code & Reasoning","Claude Sonnet","GPT-4o","Gemini Pro"],
                ["Writing & Analysis","GPT-4o","Claude","Gemini"],
                ["Live Research","Perplexity","Gemini","GPT-4o"],
                ["Image Generation","DALL-E 3","Flux","SD (local)"],
                ["Video Generation","Runway ML","Kling AI","—"],
                ["Local / Offline","Llama 3.1","Mistral 7B","Phi-3"],
                ["Fast & Free","Mistral (local)","Kimi K2","Gemini Flash"],
                ["App Building","Claude + Codex","GPT-4o","Emergent AI"],
              ].map(([task,...models],i)=>(
                <div key={i} style={{ display:"grid",gridTemplateColumns:"1.5fr 1fr 1fr 1fr",gap:8,marginBottom:8,
                  padding:"8px 0",borderBottom:`1px solid ${C.border}` }}>
                  <span style={{ fontSize:9,color:C.white }}>{task}</span>
                  {models.map((m,j)=>(
                    <span key={j} style={{ fontSize:9,color:j===0?C.cyan:C.muted }}>{m}</span>
                  ))}
                </div>
              ))}
              <div style={{ display:"grid",gridTemplateColumns:"1.5fr 1fr 1fr 1fr",gap:8,marginBottom:12 }}>
                {["TASK","PRIMARY","BACKUP 1","BACKUP 2"].map(h=>(
                  <span key={h} style={{ fontSize:7,letterSpacing:3,color:C.muted }}>{h}</span>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB: PHASES */}
        {tab==="phases" && (
          <div>
            <SectionHead label="BUILD PHASES — PHASE BY PHASE EXECUTION" color={C.gold} />
            <div style={{ display:"flex",flexDirection:"column",gap:12 }}>
              {phases.map(p=>{
                const open=expandedPhase===p.n;
                return (
                  <div key={p.n} onClick={()=>setExpandedPhase(open?null:p.n)} style={{
                    background:open?`${p.color}06`:C.card,
                    border:`1px solid ${open?p.color+"40":C.border}`,
                    borderRadius:10,cursor:"pointer",overflow:"hidden",transition:"all 0.25s"
                  }}>
                    <div style={{ padding:"18px 22px",display:"flex",alignItems:"center",gap:20,flexWrap:"wrap" }}>
                      <div style={{ fontSize:48,fontWeight:900,color:p.color,opacity:0.18,lineHeight:1,minWidth:60 }}>
                        0{p.n}
                      </div>
                      <div style={{ flex:1 }}>
                        <div style={{ fontSize:11,fontWeight:700,letterSpacing:2,color:open?p.color:C.white }}>{p.label}</div>
                        <div style={{ fontSize:9,color:C.muted,marginTop:4,letterSpacing:1 }}>
                          {p.items.length} DELIVERABLES · STATUS: PLANNED
                        </div>
                      </div>
                      <span style={{ color:p.color,opacity:0.5 }}>{open?"▲":"▼"}</span>
                    </div>
                    {open && (
                      <div style={{ borderTop:`1px solid ${p.color}15`,padding:"16px 22px",
                        display:"grid",gridTemplateColumns:"repeat(auto-fill,minmax(200px,1fr))",gap:8 }}>
                        {p.items.map((item,i)=>(
                          <div key={i} style={{ display:"flex",gap:8,alignItems:"flex-start",animation:`fadeIn 0.1s ease ${i*0.025}s both` }}>
                            <span style={{ color:p.color,fontSize:7,marginTop:4,flexShrink:0 }}>▶</span>
                            <span style={{ fontSize:10,color:C.text,lineHeight:1.5 }}>{item}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
            <div style={{ marginTop:20,background:C.card,border:`1px solid ${C.amber}20`,borderRadius:10,padding:20 }}>
              <div style={{ fontSize:9,letterSpacing:3,color:C.amber,marginBottom:12 }}>SETUP RULE — ANANT'S MAXIMUM EFFORT</div>
              {["Step 1: Download MANAGER project folder","Step 2: Run setup.bat — does everything automatically",
                "Step 3: Log in to any website if needed — Manager navigates, finds API key, copies it",
                "Step 4: Nothing else — Manager handles all config, all dependencies, always"].map((s,i)=>(
                <div key={i} style={{ display:"flex",gap:10,marginBottom:8 }}>
                  <span style={{ color:C.amber,fontSize:9,minWidth:16 }}>{i+1}.</span>
                  <span style={{ fontSize:10,color:C.text }}>{s}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: FOLDER */}
        {tab==="folder" && (
          <div>
            <SectionHead label="COMPLETE FOLDER ARCHITECTURE" color={C.orange} sub="Every file and folder — the exact structure that will be built" />
            <div style={{ background:C.dim,border:`1px solid ${C.border}`,borderRadius:12,padding:24,fontFamily:"monospace" }}>
              {folderTree.map((f,i)=>(
                <div key={i} style={{ display:"flex",alignItems:"center",gap:10,marginBottom:5,
                  padding:"2px 0",borderBottom:f.type==="root"?`1px solid ${C.border}`:"none" }}>
                  <span style={{ fontSize:10,color:f.color,lineHeight:1.8,flex:1,
                    fontWeight:f.type==="root"||f.type==="critical"?"700":"400" }}>
                    {f.name}
                  </span>
                  {f.note && <Tag label={f.note} color={f.color} />}
                </div>
              ))}
            </div>
            <div style={{ marginTop:16,background:C.card,border:`1px solid ${C.gold}20`,borderRadius:10,padding:18 }}>
              <div style={{ fontSize:9,letterSpacing:3,color:C.gold,marginBottom:12 }}>CODE RULES — NON-NEGOTIABLE</div>
              {["Nothing ever deleted — only commented with reason + date + source capability",
                "Comment format: # [YYYY-MM-DD] [REASON] [SOURCE FILE] [CAPABILITY]",
                "MANAGER_STRUCTURE.md updated after every meaningful change — append only",
                "Every project Manager creates looks cinematic and production-grade",
                "New domains: create folder → register in plugin_manager.py → done",
                "Git commit after every meaningful change with descriptive message"].map((r,i)=>(
                <div key={i} style={{ display:"flex",gap:8,marginBottom:8 }}>
                  <span style={{ color:C.gold,fontSize:7,marginTop:4,flexShrink:0 }}>◆</span>
                  <span style={{ fontSize:10,color:C.text,lineHeight:1.6 }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BOTTOM */}
        <div style={{ textAlign:"center",marginTop:56 }}>
          <div style={{ display:"inline-flex",alignItems:"center",gap:10,
            background:`${C.cyan}05`,border:`1px solid ${C.cyan}15`,borderRadius:100,padding:"12px 28px" }}>
            <span style={{ width:6,height:6,borderRadius:"50%",background:C.cyan,
              boxShadow:`0 0 10px ${C.cyan}`,display:"inline-block",animation:"blink 1.2s infinite" }} />
            <span style={{ fontSize:9,letterSpacing:4,color:C.cyan }}>ARCHITECTURE COMPLETE — READY TO BUILD PHASE 01</span>
          </div>
        </div>

      </div>

      <style>{`
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0.1}}
        @keyframes shimmer{0%{background-position:0% 50%}100%{background-position:300% 50%}}
        @keyframes fadeIn{from{opacity:0;transform:translateX(-6px)}to{opacity:1;transform:translateX(0)}}
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:3px;height:3px}
        ::-webkit-scrollbar-thumb{background:${C.cyan}25;border-radius:4px}
      `}</style>
    </div>
  );
}
