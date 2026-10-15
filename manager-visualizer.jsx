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
  dim: "#1e2530",
  muted: "#3a4555",
};

const domains = [
  {
    id: "core", label: "MANAGER CORE", icon: "⬡", color: C.cyan,
    tasks: [
      "Realistic Iron Man FRIDAY-style voice interaction",
      "Always works under you — never over you",
      "One ask → full plan → execution → delivery",
      "Zero limitations — always finds a way",
      "Auto-selects best AI per task (quality + cost)",
      "Seamless AI switch on rate limit — zero interruption",
      "Multiple API keys per provider — rotates proactively",
      "Tracks key usage — switches before limit hits",
      "Effectively unlimited free usage via key rotation",
      "Modular plugin architecture — add/remove domains freely",
      "Nothing breaks when adding or removing a capability",
      "Self-growing — adds new skills after your confirmation",
      "Regular scan for new tools & AI models in market",
      "Available worldwide via private encrypted network",
    ],
  },
  {
    id: "workflow", label: "WORKFLOW ENGINE", icon: "⬢", color: C.gold,
    tasks: [
      "Plan → Pick Tools → Execute → Review → Polish → Deliver",
      "Breaks every request into precise subtasks",
      "Assigns best tool/AI to each subtask",
      "Monitors tool execution constantly — live review",
      "If output wrong → re-evaluates → re-routes → loops",
      "Never delivers raw output — always polished first",
      "Adds Manager's own perspective to every output",
      "Output is presentable, cinematic, easy to understand",
      "Parallel agents work simultaneously for speed",
      "Every created project looks like a super polished product",
    ],
  },
  {
    id: "trading", label: "TRADING & FINANCE", icon: "◈", color: C.green,
    tasks: [
      "Live candlestick reading — all patterns, all timeframes",
      "News & sentiment scanning → trade signal generation",
      "FII/DII, Open Interest, Volume & order flow analysis",
      "Demat account direct integration — autonomous orders",
      "1000-year trader logic — multi-signal confirmation only",
      "Knows when NOT to trade — equally important",
      "Portfolio tracking: stocks, ETFs, gold, silver, crypto",
      "Gold & jewelry inventory with live pricing + OCR bills",
      "Capital protection first — consistent net profit goal",
      "Self-improving strategy learned from every trade",
      "NSE/BSE primary — crypto & global markets expanding",
      "Never acts on single signal — always cross-confirms",
    ],
  },
  {
    id: "career", label: "CAREER & JOBS", icon: "◉", color: C.orange,
    tasks: [
      "24/7 job portal scanning — LinkedIn, Naukri, Indeed, Wellfound",
      "Resume remastered per every single application",
      "ATS optimized with full keyword matching per JD",
      "Cold emails to hiring managers, founders, recruiters",
      "Application status tracking & auto follow-ups",
      "Interview coaching per specific company & role",
      "Mock interviews with live scoring & feedback",
      "Google XYZ formula: accomplished X, measured by Y, by doing Z",
      "Diagnose → Score → Rewrite → Prep — full loop",
      "Teaches until you are ready to crack that exact interview",
    ],
  },
  {
    id: "comms", label: "COMMUNICATION", icon: "◎", color: C.pink,
    tasks: [
      "Takes calls on your behalf when unavailable",
      "Speaks as your personal manager — Anant's office",
      "Post-call full summary: who, what, importance, action needed",
      "WhatsApp, email management & smart replies",
      "Cold outreach campaigns with tracking & follow-ups",
      "DM management across all platforms — never misses",
      "Context-aware responses — never sounds generic or robotic",
    ],
  },
  {
    id: "social", label: "SOCIAL MEDIA & BRAND", icon: "◆", color: C.purple,
    tasks: [
      "Instagram (personal + professional) fully managed",
      "Facebook, Twitter/X, LinkedIn — all platforms covered",
      "Reels created autonomously: concept → script → visual → post",
      "Posted at peak engagement times — data driven",
      "Hashtag research & captions crafted per post",
      "Daily follower, reach & engagement analytics report",
      "Weekly growth strategy adjusted by real performance data",
      "Brand outreach initiated when account reaches eligibility",
      "Negotiates brand deals, manages deliverables, tracks payments",
      "Scales: micro brands → mid brands → major brand partnerships",
    ],
  },
  {
    id: "builder", label: "PROJECT BUILDER", icon: "◇", color: C.gold,
    tasks: [
      "Idea → production-ready app in any language, any framework",
      "Full UI, backend, database, deployment — end to end",
      "n8n automation workflows & API pipeline creation",
      "Modular plugin domains — plug in, plug out, no breakage",
      "GitHub-like: branches, commits, rollback per code block",
      "Nothing ever deleted — only commented with reason & date",
      "Structure file updated on every single change — append only",
      "Emergent AI, Codex, Claude, Gemini — best model per task",
      "Multi-agent developer team orchestration",
      "Free tier maximized — premium quality at zero cost",
    ],
  },
  {
    id: "creative", label: "CREATIVE STUDIO", icon: "◐", color: C.amber,
    tasks: [
      "Images: posters, logos, thumbnails, artwork — any style",
      "Video & reel production — full pipeline",
      "Literature, scripts, captions, copy — all formats",
      "Brand identity & visual design systems",
      "Content calendar planning & autonomous execution",
      "Multi-model pipeline for maximum output quality",
      "Everything produced looks cinematic & super polished",
    ],
  },
  {
    id: "security", label: "PRIVACY & SECURITY", icon: "◑", color: C.red,
    tasks: [
      "Biometric / passphrase identity verification — only Anant",
      "Data invisible to all outsiders — looks like empty space",
      "API providers cannot see or log your data — blocked",
      "No company can train models on your data — hard blocked",
      "Private encrypted tunnel — worldwide access, zero exposure",
      "Even on full breach — attacker sees absolutely nothing",
      "Multiple API keys stored encrypted — invisible externally",
    ],
  },
];

const workflowSteps = [
  { id: "01", label: "USER REQUEST", desc: "Voice or text — natural language", color: C.cyan },
  { id: "02", label: "MANAGER PLANS", desc: "Breaks into subtasks, picks strategy", color: C.gold },
  { id: "03", label: "PICKS TOOLS", desc: "Best AI + service per subtask", color: C.purple },
  { id: "04", label: "PARALLEL EXECUTE", desc: "Agents work simultaneously", color: C.green },
  { id: "05", label: "LIVE REVIEW", desc: "Manager monitors every output", color: C.orange },
  { id: "06", label: "CORRECT?", desc: "YES → polish  |  NO → re-route", color: C.amber },
  { id: "07", label: "POLISH", desc: "Refined + Manager perspective added", color: C.pink },
  { id: "08", label: "DELIVERED", desc: "Cinematic, clear, presentable", color: C.cyan },
];

const aiModels = [
  { name: "Claude", specialty: "Reasoning & code", color: C.orange },
  { name: "GPT-4o", specialty: "Writing & analysis", color: C.green },
  { name: "Gemini", specialty: "Research & multimodal", color: C.cyan },
  { name: "Codex", specialty: "Code generation", color: C.gold },
  { name: "DALL-E 3", specialty: "Image creation", color: C.purple },
  { name: "Runway ML", specialty: "Video generation", color: C.pink },
  { name: "Llama 3", specialty: "Local offline LLM", color: C.red },
  { name: "Mistral", specialty: "Fast local model", color: C.amber },
  { name: "Perplexity", specialty: "Live web research", color: C.cyan },
  { name: "Flux", specialty: "Alt image gen", color: C.green },
  { name: "Emergent AI", specialty: "App building", color: C.gold },
  { name: "Kimi K2", specialty: "Free reasoning", color: C.purple },
];

const phases = [
  { n: "01", label: "CORE + VOICE + IDENTITY", color: C.cyan },
  { n: "02", label: "TRADING + FINANCE ENGINE", color: C.green },
  { n: "03", label: "CAREER + COMMUNICATION", color: C.orange },
  { n: "04", label: "SOCIAL + CREATIVE STUDIO", color: C.purple },
  { n: "05", label: "FULL INTEGRATION + SELF-GROWTH", color: C.gold },
];

const securityRules = [
  "Only Anant can access — identity always verified",
  "Data appears as empty space to any outsider or hacker",
  "API providers cannot see, log or use your data",
  "No third-party model training on your data — hard blocked",
  "Multiple API keys encrypted and rotated silently",
  "Private encrypted tunnel — works globally, zero exposure",
];

const totalCaps = domains.reduce((a, d) => a + d.tasks.length, 0);

export default function ManagerOS() {
  const [selected, setSelected] = useState(null);
  const [activeStep, setActiveStep] = useState(0);
  const [clock, setClock] = useState("");
  const [tab, setTab] = useState("domains");

  useEffect(() => {
    const i = setInterval(() => setActiveStep(s => (s + 1) % workflowSteps.length), 800);
    return () => clearInterval(i);
  }, []);

  useEffect(() => {
    const i = setInterval(() => setClock(new Date().toLocaleTimeString("en-IN", { hour12: false })), 1000);
    return () => clearInterval(i);
  }, []);

  const sel = domains.find(d => d.id === selected);

  return (
    <div style={{ minHeight: "100vh", background: C.bg, fontFamily: "monospace", color: C.white, overflowX: "hidden", position: "relative" }}>

      {/* Grid */}
      <div style={{ position: "fixed", inset: 0, pointerEvents: "none", zIndex: 0,
        backgroundImage: `linear-gradient(${C.cyan}08 1px,transparent 1px),linear-gradient(90deg,${C.cyan}08 1px,transparent 1px)`,
        backgroundSize: "44px 44px" }} />

      {/* Glow center */}
      <div style={{ position: "fixed", top: "40%", left: "50%", transform: "translate(-50%,-50%)", width: 700, height: 700,
        background: `radial-gradient(circle,${C.cyan}06 0%,transparent 70%)`, pointerEvents: "none", zIndex: 0 }} />

      {/* Corner marks */}
      {[["top","left"],["top","right"],["bottom","left"],["bottom","right"]].map(([v,h]) => (
        <div key={v+h} style={{ position:"fixed", [v]:20, [h]:20, width:32, height:32, zIndex:0, pointerEvents:"none",
          borderTop: v==="top" ? `1px solid ${C.cyan}30` : "none",
          borderBottom: v==="bottom" ? `1px solid ${C.cyan}30` : "none",
          borderLeft: h==="left" ? `1px solid ${C.cyan}30` : "none",
          borderRight: h==="right" ? `1px solid ${C.cyan}30` : "none" }} />
      ))}

      <div style={{ position: "relative", zIndex: 1, maxWidth: 1200, margin: "0 auto", padding: "32px 20px 72px" }}>

        {/* STATUS BAR */}
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:52, flexWrap:"wrap", gap:10 }}>
          <div style={{ display:"flex", alignItems:"center", gap:10 }}>
            <span style={{ width:8, height:8, borderRadius:"50%", background:C.green, boxShadow:`0 0 10px ${C.green}`, display:"inline-block", animation:"blink 1.4s infinite" }} />
            <span style={{ fontSize:9, letterSpacing:4, color:C.green }}>ALL SYSTEMS ONLINE</span>
          </div>
          <div style={{ fontSize:9, letterSpacing:3, color:C.muted }}>
            {clock} IST &nbsp;·&nbsp; ACCESS: ANANT ONLY &nbsp;·&nbsp; NETWORK: ENCRYPTED PRIVATE
          </div>
        </div>

        {/* HERO */}
        <div style={{ textAlign:"center", marginBottom:72 }}>
          <div style={{ fontSize:9, letterSpacing:8, color:C.cyan, opacity:0.5, marginBottom:16 }}>
            CLASSIFIED — PERSONAL AI OPERATING SYSTEM
          </div>
          <h1 style={{ fontSize:"clamp(60px,13vw,128px)", fontWeight:900, letterSpacing:-5, lineHeight:1, margin:0,
            background:`linear-gradient(135deg,#fff 0%,${C.cyan} 45%,#fff 75%,${C.cyan} 100%)`,
            WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent", backgroundClip:"text",
            backgroundSize:"300% 300%", animation:"shimmer 5s infinite linear" }}>
            MANAGER
          </h1>
          <div style={{ fontSize:10, letterSpacing:6, color:C.muted, marginTop:10 }}>
            BUILT EXCLUSIVELY FOR ANANT
          </div>

          {/* Stat pills */}
          <div style={{ display:"flex", justifyContent:"center", gap:12, marginTop:36, flexWrap:"wrap" }}>
            {[
              { v: domains.length, l: "DOMAINS" },
              { v: `${totalCaps}+`, l: "CAPABILITIES" },
              { v: `${aiModels.length}+`, l: "AI MODELS" },
              { v: "∞", l: "API KEYS" },
              { v: "5", l: "PHASES" },
              { v: "GLOBAL", l: "ACCESS" },
            ].map(s => (
              <div key={s.l} style={{ background:`${C.cyan}06`, border:`1px solid ${C.cyan}18`, borderRadius:100, padding:"10px 20px", textAlign:"center" }}>
                <div style={{ fontSize:20, fontWeight:900, color:C.cyan, lineHeight:1 }}>{s.v}</div>
                <div style={{ fontSize:8, letterSpacing:3, color:C.muted, marginTop:3 }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* TAB NAV */}
        <div style={{ display:"flex", gap:4, marginBottom:32, borderBottom:`1px solid ${C.dim}`, paddingBottom:0, overflowX:"auto" }}>
          {[
            { id:"domains", label:"CAPABILITY DOMAINS" },
            { id:"workflow", label:"WORKFLOW ENGINE" },
            { id:"ai", label:"AI ROUTING MATRIX" },
            { id:"security", label:"SECURITY" },
            { id:"phases", label:"BUILD PHASES" },
          ].map(t => (
            <button key={t.id} onClick={() => { setTab(t.id); setSelected(null); }}
              style={{ background:"none", border:"none", cursor:"pointer", padding:"10px 16px", whiteSpace:"nowrap",
                fontSize:9, letterSpacing:3, fontFamily:"monospace",
                color: tab===t.id ? C.cyan : C.muted,
                borderBottom: tab===t.id ? `2px solid ${C.cyan}` : "2px solid transparent",
                transition:"all 0.2s" }}>
              {t.label}
            </button>
          ))}
        </div>

        {/* TAB: DOMAINS */}
        {tab === "domains" && (
          <div>
            <div style={{ fontSize:9, letterSpacing:3, color:C.muted, marginBottom:20 }}>
              TAP ANY DOMAIN TO EXPAND ALL CAPABILITIES
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(280px,1fr))", gap:12 }}>
              {domains.map(d => {
                const open = selected === d.id;
                return (
                  <div key={d.id} onClick={() => setSelected(open ? null : d.id)}
                    style={{ background: open ? `${d.color}08` : `${C.white}03`,
                      border:`1px solid ${open ? d.color+"44" : C.dim}`,
                      borderRadius:12, padding:20, cursor:"pointer",
                      transition:"all 0.25s", boxShadow: open ? `0 0 28px ${d.color}18` : "none",
                      transform: open ? "translateY(-2px)" : "none" }}>
                    <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:10 }}>
                        <span style={{ fontSize:18, color:d.color }}>{d.icon}</span>
                        <span style={{ fontSize:9, fontWeight:700, letterSpacing:2, color: open ? d.color : C.muted }}>{d.label}</span>
                      </div>
                      <span style={{ fontSize:9, color:d.color, opacity:0.6 }}>{d.tasks.length}</span>
                    </div>
                    {!open && (
                      <div style={{ fontSize:9, color:C.muted, letterSpacing:1 }}>{d.tasks.length} CAPABILITIES — TAP TO EXPAND</div>
                    )}
                    {open && (
                      <div style={{ borderTop:`1px solid ${d.color}18`, paddingTop:14 }}>
                        {d.tasks.map((task,i) => (
                          <div key={i} style={{ display:"flex", gap:8, marginBottom:9, animation:`fadeIn 0.15s ease ${i*0.03}s both` }}>
                            <span style={{ color:d.color, fontSize:7, marginTop:4, flexShrink:0 }}>▶</span>
                            <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.6 }}>{task}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB: WORKFLOW */}
        {tab === "workflow" && (
          <div>
            <div style={{ fontSize:9, letterSpacing:3, color:C.muted, marginBottom:28 }}>
              MANAGER'S INTERNAL THINKING & EXECUTION LOOP — RUNS ON EVERY REQUEST
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(220px,1fr))", gap:10, marginBottom:40 }}>
              {workflowSteps.map((step,i) => {
                const active = activeStep === i;
                return (
                  <div key={step.id} style={{ background: active ? `${step.color}10` : `${C.white}02`,
                    border:`1px solid ${active ? step.color+"50" : C.dim}`,
                    borderRadius:10, padding:18, transition:"all 0.3s",
                    transform: active ? "scale(1.04)" : "scale(1)",
                    boxShadow: active ? `0 0 24px ${step.color}20` : "none" }}>
                    <div style={{ fontSize:36, fontWeight:900, color: active ? step.color : C.dim, lineHeight:1, marginBottom:10, transition:"color 0.3s" }}>
                      {step.id}
                    </div>
                    <div style={{ fontSize:9, fontWeight:700, letterSpacing:2, color: active ? step.color : C.muted, marginBottom:6 }}>
                      {step.label}
                    </div>
                    <div style={{ fontSize:9, color: active ? "#99aabb" : C.muted, lineHeight:1.6 }}>{step.desc}</div>
                  </div>
                );
              })}
            </div>

            {/* Code rules */}
            <div style={{ background:`${C.gold}06`, border:`1px solid ${C.gold}20`, borderRadius:12, padding:24 }}>
              <div style={{ fontSize:9, letterSpacing:4, color:C.gold, marginBottom:18 }}>CODE & STRUCTURE RULES — NON-NEGOTIABLE</div>
              {[
                "Nothing ever deleted — only commented out with reason + date",
                "Every comment includes: reason why, date, capability source",
                "Capability unused? → discussion first → only then consider deletion",
                "GitHub-like structure: branches, commits, rollback per code block",
                "Structure file updated on every single change — append only, never replaced",
                "Any AI reads structure file → understands full context → continues work",
                "Modular domains — add or remove any capability without breaking anything",
                "Every project created looks super polished — cinematic production quality",
              ].map((r,i) => (
                <div key={i} style={{ display:"flex", gap:10, marginBottom:10 }}>
                  <span style={{ color:C.gold, fontSize:8, marginTop:3, flexShrink:0 }}>◆</span>
                  <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.6 }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: AI ROUTING */}
        {tab === "ai" && (
          <div>
            <div style={{ fontSize:9, letterSpacing:3, color:C.muted, marginBottom:28 }}>
              MANAGER AUTO-SELECTS BEST AI PER TASK — QUALITY + COST EFFICIENCY COMBINED
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(180px,1fr))", gap:10, marginBottom:36 }}>
              {aiModels.map(ai => (
                <div key={ai.name} style={{ background:`${ai.color}06`, border:`1px solid ${ai.color}20`, borderRadius:10, padding:16,
                  transition:"all 0.2s", cursor:"default" }}>
                  <div style={{ fontSize:13, fontWeight:700, color:C.white, marginBottom:6 }}>{ai.name}</div>
                  <div style={{ fontSize:9, color:ai.color, opacity:0.8, letterSpacing:1 }}>{ai.specialty}</div>
                </div>
              ))}
            </div>

            {/* Multi-key system */}
            <div style={{ background:`${C.cyan}05`, border:`1px solid ${C.cyan}20`, borderRadius:12, padding:24, marginBottom:20 }}>
              <div style={{ fontSize:9, letterSpacing:4, color:C.cyan, marginBottom:18 }}>MULTI-API KEY ROTATION SYSTEM</div>
              {[
                "Multiple API keys per provider — Anthropic 1 → 2 → 3 → unlimited rotation",
                "Proactive rotation — switches before limit is reached, never waits for failure",
                "Tracks usage per key in real-time — knows which is close to limit",
                "Same system for OpenAI, Gemini, Groq, Replicate, any provider",
                "Keys stored encrypted — invisible to any outside observer",
                "Free tier accounts multiplied — effectively unlimited free usage",
                "Add new API keys anytime — Manager registers and adds to rotation pool",
                "Zero interruption — user never notices a key switch happened",
              ].map((r,i) => (
                <div key={i} style={{ display:"flex", gap:10, marginBottom:10 }}>
                  <span style={{ color:C.cyan, fontSize:8, marginTop:3, flexShrink:0 }}>▶</span>
                  <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.6 }}>{r}</span>
                </div>
              ))}
            </div>

            <div style={{ background:`${C.dim}`, border:`1px solid ${C.muted}30`, borderRadius:10, padding:16 }}>
              <div style={{ fontSize:9, color:C.muted, letterSpacing:3, marginBottom:10 }}>ROUTING LOGIC</div>
              <div style={{ fontSize:10, color:"#667788", lineHeight:2, fontFamily:"monospace" }}>
                IF task = code → Claude / Codex → if limit → next key → next model<br/>
                IF task = image → DALL-E / Flux / Midjourney → rotate on limit<br/>
                IF task = research → Perplexity / Gemini → rotate on limit<br/>
                IF task = video → Runway / Kling → rotate on limit<br/>
                IF task = local → Llama / Mistral → runs on your RTX 5060<br/>
                IF any model fails → full context preserved → next model picks up
              </div>
            </div>
          </div>
        )}

        {/* TAB: SECURITY */}
        {tab === "security" && (
          <div>
            <div style={{ fontSize:9, letterSpacing:3, color:C.muted, marginBottom:28 }}>
              ZERO TRUST — ZERO EXPOSURE — ZERO COMPROMISE
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(280px,1fr))", gap:12, marginBottom:36 }}>
              {securityRules.map((r,i) => (
                <div key={i} style={{ background:`${C.red}06`, border:`1px solid ${C.red}20`, borderRadius:10, padding:18,
                  display:"flex", gap:12, alignItems:"flex-start" }}>
                  <span style={{ color:C.red, fontSize:16, marginTop:2, flexShrink:0 }}>■</span>
                  <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.7 }}>{r}</span>
                </div>
              ))}
            </div>

            <div style={{ background:`${C.red}04`, border:`1px solid ${C.red}15`, borderRadius:12, padding:24 }}>
              <div style={{ fontSize:9, letterSpacing:4, color:C.red, marginBottom:16 }}>HARD RULES — CANNOT BE OVERRIDDEN BY ANYONE</div>
              {[
                "Not even API providers (Anthropic, OpenAI, Google) can see your data",
                "Not even a hacker who gets inside the system can see anything",
                "Not even other company model training pipelines touch your data",
                "Not even future updates can loosen these security constraints",
                "Only one person has access — Anant — verified every single session",
              ].map((r,i) => (
                <div key={i} style={{ display:"flex", gap:10, marginBottom:10 }}>
                  <span style={{ color:C.red, fontSize:8, marginTop:3 }}>▶</span>
                  <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.6 }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB: PHASES */}
        {tab === "phases" && (
          <div>
            <div style={{ fontSize:9, letterSpacing:3, color:C.muted, marginBottom:28 }}>
              STRUCTURED BUILD ROADMAP — PHASE BY PHASE EXECUTION
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:16, marginBottom:40 }}>
              {phases.map((p,i) => (
                <div key={p.n} style={{ background:`${p.color}06`, border:`1px solid ${p.color}20`, borderRadius:12,
                  padding:"20px 24px", display:"flex", alignItems:"center", gap:24, flexWrap:"wrap" }}>
                  <div style={{ fontSize:52, fontWeight:900, color:p.color, opacity:0.25, lineHeight:1, minWidth:80 }}>
                    {p.n}
                  </div>
                  <div style={{ flex:1 }}>
                    <div style={{ fontSize:11, fontWeight:700, letterSpacing:3, color:p.color, marginBottom:6 }}>{p.label}</div>
                    <div style={{ fontSize:9, color:C.muted, letterSpacing:2 }}>PHASE {p.n} — PLANNED</div>
                  </div>
                  <div style={{ width:80, height:4, background:C.dim, borderRadius:4, overflow:"hidden" }}>
                    <div style={{ width:"0%", height:"100%", background:p.color, borderRadius:4 }} />
                  </div>
                </div>
              ))}
            </div>

            {/* Structure file */}
            <div style={{ background:`${C.amber}06`, border:`1px solid ${C.amber}20`, borderRadius:12, padding:24 }}>
              <div style={{ fontSize:9, letterSpacing:4, color:C.amber, marginBottom:18 }}>MASTER STRUCTURE FILE — THE LIVING LOG</div>
              {[
                "Contains: project vision, end goal, full structure, all modifications",
                "Append only — nothing ever deleted or replaced",
                "Every change logged: what changed, why, date, who/what triggered it",
                "GitHub-like: every code block change visible, rollback available",
                "Any AI reads this one file → knows everything → continues seamlessly",
                "Auto-requirements: any change → dependencies installed automatically",
                "User max effort: download code → run .bat → log in if needed",
                "Even API key fetching: Manager surfs website, copies key — you just log in",
                "File itself states: THIS FILE IS APPEND ONLY — DO NOT REPLACE OR DELETE",
              ].map((r,i) => (
                <div key={i} style={{ display:"flex", gap:10, marginBottom:10 }}>
                  <span style={{ color:C.amber, fontSize:8, marginTop:3 }}>◆</span>
                  <span style={{ fontSize:10, color:"#99aabb", lineHeight:1.6 }}>{r}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* BOTTOM STATUS */}
        <div style={{ textAlign:"center", marginTop:64 }}>
          <div style={{ display:"inline-flex", alignItems:"center", gap:10,
            background:`${C.cyan}06`, border:`1px solid ${C.cyan}18`,
            borderRadius:100, padding:"12px 28px" }}>
            <span style={{ width:6, height:6, borderRadius:"50%", background:C.cyan,
              boxShadow:`0 0 10px ${C.cyan}`, display:"inline-block", animation:"blink 1.2s infinite" }} />
            <span style={{ fontSize:9, letterSpacing:4, color:C.cyan }}>
              ALL 10 SETS STORED — AWAITING BUILD COMMAND
            </span>
          </div>
        </div>

      </div>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.15} }
        @keyframes shimmer { 0%{background-position:0% 50%} 100%{background-position:300% 50%} }
        @keyframes fadeIn { from{opacity:0;transform:translateX(-6px)} to{opacity:1;transform:translateX(0)} }
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; height:4px; }
        ::-webkit-scrollbar-track { background:transparent; }
        ::-webkit-scrollbar-thumb { background:${C.cyan}30; border-radius:4px; }
      `}</style>
    </div>
  );
}
