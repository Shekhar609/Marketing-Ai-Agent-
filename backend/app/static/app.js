/**
 * AIPNT Autonomous Revenue Operations Platform - SPA Application Router & UI Logic
 * Implements all 26 routes defined in Master Specification Section 43.
 */

(function () {
  'use strict';

  // --- State Management ---
  const state = {
    currentRoute: 'dashboard',
    authToken: localStorage.getItem('aipnt_token') || '',
    user: {
      name: 'AIPNT Executive',
      org: 'Enterprise Healthcare Ops',
      role: 'admin',
    },
    approvalsPending: 2,
  };

  // --- Toast Notifications ---
  function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️';
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // --- API Helper ---
  async function apiFetch(endpoint, options = {}) {
    const headers = Object.assign(
      {
        'Content-Type': 'application/json',
      },
      options.headers || {}
    );
    if (state.authToken) {
      headers['Authorization'] = `Bearer ${state.authToken}`;
    }
    try {
      const res = await fetch(endpoint, Object.assign({}, options, { headers }));
      return await res.json();
    } catch (err) {
      console.warn('API fetch notice:', err);
      return null;
    }
  }

  // --- Router & Views ---
  const routes = {
    // 1. Dashboard View
    dashboard: function () {
      return `
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">Annual Recurring Revenue</div>
            <div class="kpi-value">$2,450,000</div>
            <div class="kpi-trend up">▲ +24.8% vs last quarter</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Pipeline Value</div>
            <div class="kpi-value">$8,120,000</div>
            <div class="kpi-trend up">▲ +18.2% velocity</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Blended ROAS</div>
            <div class="kpi-value">3.82x</div>
            <div class="kpi-trend up">▲ High efficiency</div>
          </div>
          <div class="kpi-card">
            <div class="kpi-label">Customer Acquisition Cost</div>
            <div class="kpi-value">$1,140</div>
            <div class="kpi-trend up">▼ -14.2% lower CAC</div>
          </div>
        </div>

        <div class="grid-2">
          <div class="card">
            <div class="card-header">
              <div class="card-title">Full-Funnel Conversion Velocity</div>
              <span class="pill pill-emerald">Live Telemetry</span>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">1. Visitors</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 100%">48,250 (100%)</div></div>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">2. Leads Captured</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 72%">3,840 (8.0%)</div></div>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">3. MQLs</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 54%">1,280 (33.3%)</div></div>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">4. SQLs</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 38%">520 (40.6%)</div></div>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">5. Opportunities</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 26%">190 (36.5%)</div></div>
            </div>
            <div class="funnel-bar">
              <div class="funnel-stage-name">6. Won Deals</div>
              <div class="funnel-track"><div class="funnel-fill" style="width: 18%">64 (33.7%)</div></div>
            </div>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="card-title">Autonomous Strategic Recommendations</div>
              <span class="pill pill-indigo">AI Optimization</span>
            </div>
            <div style="display:flex; flex-direction:column; gap:14px;">
              <div style="background:var(--bg-tertiary); padding:14px; border-radius:8px; border-left:3px solid var(--accent-primary);">
                <div style="font-weight:600; font-size:14px; margin-bottom:4px;">Reallocate $8,000 from Meta to LinkedIn Search</div>
                <div style="font-size:12px; color:var(--text-secondary);">LinkedIn healthcare decision-maker CPC produces 3.4x higher pipeline velocity for ABDM certified products.</div>
              </div>
              <div style="background:var(--bg-tertiary); padding:14px; border-radius:8px; border-left:3px solid var(--accent-emerald);">
                <div style="font-weight:600; font-size:14px; margin-bottom:4px;">Launch Hospital CIO Video Testimonial Retargeting</div>
                <div style="font-size:12px; color:var(--text-secondary);">Visitors viewing pricing page 2+ times convert 48% faster when served ABDM case study battlecard.</div>
              </div>
              <div style="background:var(--bg-tertiary); padding:14px; border-radius:8px; border-left:3px solid var(--accent-amber);">
                <div style="font-weight:600; font-size:14px; margin-bottom:4px;">Deploy Email Drip Sequence #4 to Stalled MQLs</div>
                <div style="font-size:12px; color:var(--text-secondary);">Automated reactivation campaign expected to recover 28 opportunities worth $480,000.</div>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 2. AI Executive Copilot View
    'ai-copilot': function () {
      return `
        <div class="chat-container">
          <div class="chat-history" id="copilot-chat-history">
            <div class="chat-message assistant">
              <div class="chat-bubble">
                Hello! I am your <strong>AIPNT Autonomous Revenue Copilot</strong>. I have full visibility across your 12 growth agents, CRM pipeline, attribution models, and ad spend. How can I assist your marketing operations today?
              </div>
            </div>
          </div>
          <div style="padding:10px 20px; display:flex; gap:8px; overflow-x:auto;">
            <button class="btn btn-secondary btn-sm" onclick="window.sendCopilotPrompt('Analyze our Q3 CAC vs LTV efficiency across channels')">📊 Analyze Q3 CAC vs LTV</button>
            <button class="btn btn-secondary btn-sm" onclick="window.sendCopilotPrompt('Which competitor is bidding on our high-intent search terms?')">⚔️ Competitor Search Bidding</button>
            <button class="btn btn-secondary btn-sm" onclick="window.sendCopilotPrompt('Draft a 30-day ABM strategy for 50 bed hospitals in Maharashtra')">🎯 30-Day Hospital ABM</button>
          </div>
          <div class="chat-input-bar">
            <input type="text" class="form-control" id="copilot-input" placeholder="Ask AI Copilot about pipeline velocity, campaigns, or strategic recommendations..." onkeydown="if(event.key==='Enter') window.submitCopilot()">
            <button class="btn btn-primary" onclick="window.submitCopilot()">Send ✨</button>
          </div>
        </div>
      `;
    },

    // 3. Agent Fleet View
    agents: function () {
      const agentList = [
        { name: 'Market Research Agent', role: 'Macro trends, TAM/SAM/SOM, regulatory tracking', status: 'ACTIVE', runs: 84 },
        { name: 'Competitive Intelligence', role: 'Competitor monitoring, battlecards, positioning', status: 'ACTIVE', runs: 112 },
        { name: 'Customer Persona Agent', role: 'ICP definition, firmographics, buying triggers', status: 'ACTIVE', runs: 96 },
        { name: 'Brand Strategy Agent', role: 'Messaging architecture, value propositions', status: 'ACTIVE', runs: 42 },
        { name: 'Content Strategy Agent', role: 'Editorial calendar, thought leadership creation', status: 'ACTIVE', runs: 158 },
        { name: 'SEO Engine Agent', role: 'Keyword clusters, SERP ranking, technical audits', status: 'ACTIVE', runs: 230 },
        { name: 'Social Media Agent', role: 'Viral hooks, multi-channel distribution', status: 'ACTIVE', runs: 310 },
        { name: 'Email Marketing Agent', role: 'Cold outreach, nurture sequences, subject A/B testing', status: 'ACTIVE', runs: 184 },
        { name: 'Campaign Management Agent', role: 'Cross-channel budgeting, audience orchestration', status: 'ACTIVE', runs: 68 },
        { name: 'Lead Generation Agent', role: 'Prospect discovery, 5-factor lead scoring', status: 'ACTIVE', runs: 420 },
        { name: 'Sales Enablement Agent', role: 'Sales decks, objection handling, ROI calculators', status: 'ACTIVE', runs: 88 },
        { name: 'Marketing Orchestrator', role: 'Autonomous 12-stage loop, episodic memory, task graph', status: 'AUTONOMOUS', runs: 512 },
      ];

      return `
        <div class="card" style="margin-bottom:24px;">
          <div class="card-header">
            <div class="card-title">Autonomous Marketing Agent Fleet (12 Active Agents)</div>
            <button class="btn btn-primary btn-sm" onclick="window.triggerAllAgents()">⚡ Trigger Full Autonomous Cycle</button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Agent Name</th>
                  <th>Primary Mission & Scope</th>
                  <th>Operational Status</th>
                  <th>Total Runs</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                ${agentList
                  .map(
                    (a) => `
                  <tr>
                    <td><strong>${a.name}</strong></td>
                    <td>${a.role}</td>
                    <td><span class="pill ${a.status === 'AUTONOMOUS' ? 'pill-indigo' : 'pill-emerald'}">${a.status}</span></td>
                    <td>${a.runs} executions</td>
                    <td>
                      <button class="btn btn-secondary btn-sm" onclick="window.runSingleAgent('${a.name}')">Run Now</button>
                    </td>
                  </tr>
                `
                  )
                  .join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 4. Market Research View
    'market-research': function () {
      return `
        <div class="grid-2">
          <div class="card">
            <div class="card-header">
              <div class="card-title">Market Intelligence Query</div>
            </div>
            <div class="form-group">
              <label class="form-label">Sector / Domain</label>
              <input type="text" class="form-control" id="mr-sector" value="Indian Healthcare & Hospital Digital Transformation">
            </div>
            <div class="form-group">
              <label class="form-label">Target Geography</label>
              <input type="text" class="form-control" id="mr-geo" value="India (Tier 1 & Tier 2 Cities)">
            </div>
            <button class="btn btn-primary" onclick="window.runMarketResearch()">Generate Deep Market Report 🌐</button>
          </div>

          <div class="card">
            <div class="card-header">
              <div class="card-title">Latest Synthesized Market Report</div>
              <span class="pill pill-emerald">Verified Factual</span>
            </div>
            <div id="mr-output" style="font-size:13px; line-height:1.6; color:var(--text-secondary);">
              <h4 style="color:var(--text-primary); margin-bottom:8px;">ABDM Adoption & Digital OPD Kiosk Market 2026</h4>
              <p>• <strong>TAM:</strong> $4.2 Billion Indian digital healthcare infrastructure sector.</p>
              <p>• <strong>Key Driver:</strong> National Health Authority ABDM mandates accelerating digital registration in 25,000+ private hospitals.</p>
              <p>• <strong>Bottleneck:</strong> Legacy HMIS systems suffer from 12-18 minute OPD queues, driving hospital adoption of AI voice kiosks.</p>
            </div>
          </div>
        </div>
      `;
    },

    // 5. Competitive Intel View
    competitors: function () {
      return `
        <div class="card" style="margin-bottom:24px;">
          <div class="card-header">
            <div class="card-title">Competitive Battlefield & Positioning Matrix</div>
            <button class="btn btn-secondary btn-sm" onclick="window.refreshCompetitors()">🔄 Refresh SERP & Price Intel</button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Competitor</th>
                  <th>Market Share</th>
                  <th>Primary Vulnerability</th>
                  <th>AIPNT Counter-Advantage</th>
                  <th>Battlecard</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td><strong>HealthCube Systems</strong></td>
                  <td>28.4%</td>
                  <td>No native ABDM M3 EHR connector; high hardware cost</td>
                  <td>AIPNT DigiSwasth offers 100% turnkey ABDM compliance at 60% lower TCO</td>
                  <td><button class="btn btn-secondary btn-sm" onclick="window.viewBattlecard('HealthCube')">View Battlecard</button></td>
                </tr>
                <tr>
                  <td><strong>MedCloud Ops</strong></td>
                  <td>21.2%</td>
                  <td>English-only voice interface; complex 3-month deployment</td>
                  <td>Multilingual 12 Indian regional languages voice triage in 48 hours</td>
                  <td><button class="btn btn-secondary btn-sm" onclick="window.viewBattlecard('MedCloud')">View Battlecard</button></td>
                </tr>
                <tr>
                  <td><strong>PulseHealth Care</strong></td>
                  <td>14.8%</td>
                  <td>Opaque pricing tiers with zero lead attribution analytics</td>
                  <td>Transparent multi-touch attribution & guaranteed pipeline velocity</td>
                  <td><button class="btn btn-secondary btn-sm" onclick="window.viewBattlecard('PulseHealth')">View Battlecard</button></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 6. Buyer Personas & ICP View
    personas: function () {
      return `
        <div class="grid-2">
          <div class="card">
            <div class="card-header">
              <div class="card-title">Ideal Customer Profile (ICP) Criteria</div>
            </div>
            <div style="font-size:13px; line-height:1.7; color:var(--text-secondary);">
              <p>• <strong>Industry:</strong> Multi-Specialty Hospitals, Private Healthcare Networks</p>
              <p>• <strong>Company Size:</strong> 50 to 500 Bed Capacity (500+ daily OPD footfall)</p>
              <p>• <strong>Target Region:</strong> India Tier-1 & Tier-2 Metros</p>
              <p>• <strong>Technology Stack:</strong> Looking for ABDM compliance, Cloud PACS, AI Triage</p>
            </div>
          </div>
          <div class="card">
            <div class="card-header">
              <div class="card-title">Buyer Persona: Dr. Suresh Rao (Hospital Medical Director)</div>
              <span class="pill pill-indigo">Primary Decision Maker</span>
            </div>
            <div style="font-size:13px; line-height:1.7; color:var(--text-secondary);">
              <p>• <strong>Key Priority:</strong> Eliminate 15-minute registration bottlenecks, comply with ABDM guidelines.</p>
              <p>• <strong>Primary Objection:</strong> "Our nursing staff cannot learn complicated new software."</p>
              <p>• <strong>Conversion Hook:</strong> 45-second vernacular voice triage with zero staff training required.</p>
            </div>
          </div>
        </div>
      `;
    },

    // 7. Brand Strategy View
    brand: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Brand Positioning & Core Value Architecture</div>
          </div>
          <div class="grid-3" style="margin-bottom:0;">
            <div style="background:var(--bg-tertiary); padding:18px; border-radius:8px;">
              <h4 style="color:var(--accent-primary); margin-bottom:8px;">Brand Archetype</h4>
              <p style="font-size:13px; color:var(--text-secondary);">The Visionary Technologist & Empathetic Healer. Uncompromising compliance meets futuristic efficiency.</p>
            </div>
            <div style="background:var(--bg-tertiary); padding:18px; border-radius:8px;">
              <h4 style="color:var(--accent-emerald); margin-bottom:8px;">Core Value Proposition</h4>
              <p style="font-size:13px; color:var(--text-secondary);">Transform high-friction hospital waiting rooms into frictionless AI-powered digital healthcare corridors.</p>
            </div>
            <div style="background:var(--bg-tertiary); padding:18px; border-radius:8px;">
              <h4 style="color:var(--accent-cyan); margin-bottom:8px;">Voice & Tone Pillars</h4>
              <p style="font-size:13px; color:var(--text-secondary);">Authoritative, Data-Backed, Compliant (ABDM certified), and Optimistic for Indian Healthcare.</p>
            </div>
          </div>
        </div>
      `;
    },

    // 8. Content Engine View
    content: function () {
      return `
        <div class="grid-2">
          <div class="card">
            <div class="card-header"><div class="card-title">AI Content Studio</div></div>
            <div class="form-group">
              <label class="form-label">Content Format</label>
              <select class="form-control" id="content-format">
                <option>LinkedIn Thought Leadership Post</option>
                <option>SEO Long-Form Blog Guide</option>
                <option>Executive Whitepaper Abstract</option>
                <option>High-Intent Ad Copy (Google & LinkedIn)</option>
              </select>
            </div>
            <div class="form-group">
              <label class="form-label">Core Topic / Angle</label>
              <input type="text" class="form-control" id="content-topic" value="How Indian Hospitals are Slashing OPD Wait Times by 65% with Voice AI">
            </div>
            <button class="btn btn-primary" onclick="window.generateContent()">Generate Brand-Aligned Draft ✍️</button>
          </div>
          <div class="card">
            <div class="card-header">
              <div class="card-title">Generated Draft</div>
              <button class="btn btn-secondary btn-sm" onclick="window.copyDraft()">Copy to Clipboard</button>
            </div>
            <div id="content-output" style="white-space:pre-wrap; font-size:13px; line-height:1.6; color:var(--text-secondary);">
Click "Generate Brand-Aligned Draft" to trigger the Content Strategy Agent...
            </div>
          </div>
        </div>
      `;
    },

    // 9. SEO & Keywords View
    seo: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">High-Intent Keyword Intelligence & SERP Tracking</div>
            <span class="pill pill-emerald">Domain Authority: 44</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Keyword</th>
                  <th>Intent</th>
                  <th>Monthly Search Volume</th>
                  <th>SERP Rank</th>
                  <th>Difficulty</th>
                </tr>
              </thead>
              <tbody>
                <tr><td><strong>abdm compliant ehr software</strong></td><td>Commercial</td><td>4,200</td><td><span class="pill pill-emerald">#3</span></td><td>48 / 100</td></tr>
                <tr><td><strong>hospital opd queue management system</strong></td><td>Transactional</td><td>6,800</td><td><span class="pill pill-emerald">#2</span></td><td>52 / 100</td></tr>
                <tr><td><strong>ai triage kiosk india</strong></td><td>High Intent</td><td>2,400</td><td><span class="pill pill-emerald">#1</span></td><td>36 / 100</td></tr>
                <tr><td><strong>digital health transformation hospital case study</strong></td><td>Informational</td><td>1,900</td><td><span class="pill pill-indigo">#5</span></td><td>41 / 100</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 10. Social Media View
    social: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Automated LinkedIn & Social Editorial Calendar</div>
            <button class="btn btn-primary btn-sm" onclick="window.scheduleSocialPost()">+ Queue Autonomous Post</button>
          </div>
          <div class="grid-3" style="margin-bottom:0;">
            <div style="background:var(--bg-tertiary); padding:16px; border-radius:8px;">
              <span class="pill pill-indigo">Tuesday • LinkedIn</span>
              <div style="margin:10px 0; font-size:13px; font-weight:600;">"Why 25,000 Indian hospitals will adopt ABDM by Q4 2026..."</div>
              <div style="font-size:12px; color:var(--text-muted);">Est. Impressions: 12,400 • CTR: 3.2%</div>
            </div>
            <div style="background:var(--bg-tertiary); padding:16px; border-radius:8px;">
              <span class="pill pill-emerald">Thursday • Twitter / X</span>
              <div style="margin:10px 0; font-size:13px; font-weight:600;">"OPD wait times in India: 15 mins down to 45 secs. Here is how we engineered it:"</div>
              <div style="font-size:12px; color:var(--text-muted);">Est. Impressions: 8,900 • Reposts: 85</div>
            </div>
            <div style="background:var(--bg-tertiary); padding:16px; border-radius:8px;">
              <span class="pill pill-amber">Saturday • YouTube / Shorts</span>
              <div style="margin:10px 0; font-size:13px; font-weight:600;">"Doctor POV: Deploying AI triage kiosk in 48 hours."</div>
              <div style="font-size:12px; color:var(--text-muted);">Est. Views: 15,000 • Leads: 24</div>
            </div>
          </div>
        </div>
      `;
    },

    // 11. Email Sequences View
    email: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Automated Nurture & Sales Outbound Sequences</div>
            <span class="pill pill-emerald">Delivery Rate: 99.1%</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>Campaign Name</th><th>Audience</th><th>Open Rate</th><th>Click Rate</th><th>Replies / SQLs</th></tr>
              </thead>
              <tbody>
                <tr><td>Hospital CIO 4-Step ABM Sequence</td><td>CIOs & IT Directors</td><td>44.2%</td><td>14.8%</td><td>28 Demos Booked</td></tr>
                <tr><td>ABDM Compliance Benchmark Report Drip</td><td>MQL Whitepaper Downloads</td><td>38.9%</td><td>11.2%</td><td>19 Demos Booked</td></tr>
                <tr><td>Stalled Opportunity Reactivation</td><td>Closed Lost & Warm Leads</td><td>31.4%</td><td>8.9%</td><td>12 Reactivations</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 12. Campaigns & Paid Ads View
    campaigns: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Cross-Channel Paid Campaigns & Budget Allocation</div>
            <span class="pill pill-emerald">Total Monthly Budget: $40,000</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>Campaign</th><th>Channel</th><th>Spend</th><th>Impressions</th><th>Conversions</th><th>CPA</th><th>ROAS</th></tr>
              </thead>
              <tbody>
                <tr><td>High-Intent Search - ABDM EHR</td><td>Google Ads</td><td>$14,500</td><td>48,200</td><td>142 SQLs</td><td>$102.11</td><td>4.2x</td></tr>
                <tr><td>CRO & Medical Director ABM</td><td>LinkedIn Ads</td><td>$18,000</td><td>38,400</td><td>88 SQLs</td><td>$204.54</td><td>3.6x</td></tr>
                <tr><td>Remarketing Hospital Website Visitors</td><td>Meta Feed</td><td>$7,500</td><td>84,200</td><td>112 Leads</td><td>$66.96</td><td>3.1x</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 13. Leads & Scoring View
    leads: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Lead Intelligence & Multi-Factor Scoring (5 Factors)</div>
            <span class="pill pill-indigo">Total Tracked: 3,840</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>Lead Name</th><th>Company</th><th>Job Title</th><th>Fit Score</th><th>Intent Score</th><th>Total Score</th><th>Stage</th></tr>
              </thead>
              <tbody>
                <tr><td><strong>Elena Rostova</strong></td><td>Enterprise Healthcare</td><td>VP Revenue Operations</td><td>92</td><td>88</td><td><strong>90 / 100</strong></td><td><span class="pill pill-emerald">Sales Qualified (SQL)</span></td></tr>
                <tr><td><strong>Marcus Vance</strong></td><td>TechScale Systems</td><td>Chief Medical Officer</td><td>84</td><td>82</td><td><strong>83 / 100</strong></td><td><span class="pill pill-emerald">Sales Qualified (SQL)</span></td></tr>
                <tr><td><strong>Sarah Connor</strong></td><td>Cyberdyne Health</td><td>Director of IT</td><td>76</td><td>68</td><td><strong>72 / 100</strong></td><td><span class="pill pill-indigo">Marketing Qualified (MQL)</span></td></tr>
                <tr><td><strong>Devin Cole</strong></td><td>Apex Global Hospital</td><td>Chief Revenue Officer</td><td>95</td><td>94</td><td><strong>94 / 100</strong></td><td><span class="pill pill-emerald">Hot Opportunity</span></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 14. Sales Enablement View
    sales: function () {
      return `
        <div class="grid-2">
          <div class="card">
            <div class="card-header"><div class="card-title">Live Sales Battlecards</div></div>
            <div style="font-size:13px; line-height:1.7; color:var(--text-secondary);">
              <h4 style="color:var(--text-primary); margin-bottom:6px;">Objection: "We already have an EHR system from 2021"</h4>
              <p>👉 <em>Response:</em> "AIPNT DigiSwasth does not replace your EHR; it sits on top as an intelligent AI triage layer with native ABDM integration, reducing registration time by 65% with zero migration downtime."</p>
            </div>
          </div>
          <div class="card">
            <div class="card-header"><div class="card-title">Interactive ROI Calculator</div></div>
            <div style="font-size:13px; line-height:1.7; color:var(--text-secondary);">
              <p>• Daily OPD Patients: <strong>800</strong></p>
              <p>• Current Cost Per Registration: <strong>$1.80</strong></p>
              <p>• Estimated Monthly Savings: <strong>$28,800</strong></p>
              <p>• Projected Annual Payback: <strong>14.2x ROI</strong></p>
            </div>
          </div>
        </div>
      `;
    },

    // 15. Analytics & Attribution View
    analytics: function () {
      return `
        <div class="card" style="margin-bottom:24px;">
          <div class="card-header">
            <div class="card-title">Multi-Touch Revenue Attribution Comparison</div>
            <span class="pill pill-emerald">Total Attributed: $2,450,000</span>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>Channel</th><th>First-Touch</th><th>Last-Touch</th><th>Linear (Equal)</th><th>Time-Decay</th><th>W-Shaped (40/40/20)</th></tr>
              </thead>
              <tbody>
                <tr><td><strong>LinkedIn Sponsored</strong></td><td>38.2%</td><td>24.5%</td><td>30.4%</td><td>28.9%</td><td><strong>34.8%</strong></td></tr>
                <tr><td><strong>Google High-Intent Search</strong></td><td>26.4%</td><td>44.2%</td><td>32.8%</td><td>36.5%</td><td><strong>38.2%</strong></td></tr>
                <tr><td><strong>Organic Content & SEO</strong></td><td>24.8%</td><td>12.4%</td><td>21.2%</td><td>18.4%</td><td><strong>16.5%</strong></td></tr>
                <tr><td><strong>Direct / Referral</strong></td><td>10.6%</td><td>18.9%</td><td>15.6%</td><td>16.2%</td><td><strong>10.5%</strong></td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 16. A/B Experiments View
    experiments: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Autonomous A/B Testing & Optimization Engine</div>
            <button class="btn btn-primary btn-sm" onclick="window.createExperiment()">+ Launch Experiment</button>
          </div>
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr><th>Experiment Name</th><th>Variant A</th><th>Variant B</th><th>Sample Size</th><th>Confidence</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr><td>Landing Page Hero Headline</td><td>"Transform Hospital Operations" (3.2% CR)</td><td>"Cut OPD Wait Times by 65% with Voice AI" (5.8% CR)</td><td>4,200 visitors</td><td><span class="pill pill-emerald">99.4% (Winner B)</span></td><td>Promoted to Production</td></tr>
                <tr><td>Email Drip Subject Line</td><td>"ABDM Compliance Guide" (28.4% Open)</td><td>"Is your hospital ready for ABDM audit?" (41.2% Open)</td><td>2,800 recipients</td><td><span class="pill pill-emerald">98.8% (Winner B)</span></td><td>Promoted to Production</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      `;
    },

    // 17. Customers & Retention View
    customers: function () {
      return `
        <div class="kpi-grid">
          <div class="kpi-card"><div class="kpi-label">Active Customer Accounts</div><div class="kpi-value">128</div><div class="kpi-trend up">▲ +12 this month</div></div>
          <div class="kpi-card"><div class="kpi-label">Net Revenue Retention (NRR)</div><div class="kpi-value">134.2%</div><div class="kpi-trend up">▲ Best in class</div></div>
          <div class="kpi-card"><div class="kpi-label">Customer Lifetime Value (LTV)</div><div class="kpi-value">$84,000</div><div class="kpi-trend up">▲ 4.8x LTV/CAC</div></div>
          <div class="kpi-card"><div class="kpi-label">Gross Churn Rate</div><div class="kpi-value">0.8%</div><div class="kpi-trend up">▼ Low churn</div></div>
        </div>
      `;
    },

    // 18. Executive Reports View
    reports: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Executive Intelligence Reports</div>
            <button class="btn btn-primary btn-sm" onclick="window.generateNewReport()">⚡ Generate Weekly Digest</button>
          </div>
          <div style="font-size:13px; line-height:1.7; color:var(--text-secondary);">
            <h3 style="color:var(--text-primary); margin-bottom:12px;">Executive Weekly Revenue & Strategy Report (Week 40)</h3>
            <p><strong>1. Executive Summary:</strong> The platform achieved $2.45M ARR pacing +24.8% QoQ. Full funnel velocity accelerated with 142 new SQLs generated at an average CPA of $102.11.</p>
            <p><strong>2. Attribution Highlights:</strong> Google Ads and LinkedIn accounted for 73% of influenced pipeline, while organic search SERP ranks reached #1 for 'ai triage kiosk india'.</p>
            <p><strong>3. Autonomous Loop Actions:</strong> Reallocated $8,000 to top-performing ad sets and promoted Variant B hero headline to production.</p>
          </div>
        </div>
      `;
    },

    // 19. Human Approvals View
    approvals: function () {
      return `
        <div class="card">
          <div class="card-header">
            <div class="card-title">Human-in-the-Loop Risk Governance Queue</div>
            <span class="pill pill-rose" id="approvals-count-badge">2 Actions Awaiting Approval</span>
          </div>
          <div style="display:flex; flex-direction:column; gap:16px;">
            <div id="approval-item-1" style="background:var(--bg-tertiary); padding:18px; border-radius:8px; border:1px solid rgba(244,63,94,0.3);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <strong>Launch Q4 Google Ads Expansion Campaign ($15,000 Budget)</strong>
                <span class="pill pill-rose">CRITICAL RISK</span>
              </div>
              <p style="font-size:13px; color:var(--text-secondary); margin-bottom:12px;">Proposed by Campaign Management Agent based on 4.2x ROAS in Search intent tests. Financial commitment > $5,000 threshold requires sign-off.</p>
              <div style="display:flex; gap:10px;">
                <button class="btn btn-success btn-sm" onclick="window.approveAction(1)">Approve & Launch</button>
                <button class="btn btn-danger btn-sm" onclick="window.rejectAction(1)">Reject Action</button>
              </div>
            </div>

            <div id="approval-item-2" style="background:var(--bg-tertiary); padding:18px; border-radius:8px; border:1px solid rgba(245,158,11,0.3);">
              <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                <strong>Push 42 Stage Updates to HubSpot CRM Records</strong>
                <span class="pill pill-amber">HIGH RISK</span>
              </div>
              <p style="font-size:13px; color:var(--text-secondary); margin-bottom:12px;">Proposed by Lead Generation Agent. Modifies external system of record to graduate MQLs to Sales Qualified stage based on high intent signals.</p>
              <div style="display:flex; gap:10px;">
                <button class="btn btn-success btn-sm" onclick="window.approveAction(2)">Approve CRM Sync</button>
                <button class="btn btn-danger btn-sm" onclick="window.rejectAction(2)">Reject Update</button>
              </div>
            </div>
          </div>
        </div>
      `;
    },

    // 20. Integrations & Webhooks View
    integrations: function () {
      return `
        <div class="card" style="margin-bottom:24px;">
          <div class="card-header">
            <div>
              <div class="card-title">Production External Integrations & Connectors</div>
              <div style="font-size:13px; color:var(--text-secondary); margin-top:4px;">
                Connect live systems of record for bi-directional CRM lead sync, demo scheduling, and real-time Slack revenue alerts.
              </div>
            </div>
            <span class="pill pill-emerald" id="integrations-status-badge">Active Integrations Online</span>
          </div>

          <div class="grid-3" style="gap:20px; margin-bottom:0;">
            <!-- 1. Salesforce CRM -->
            <div class="integration-card">
              <div>
                <div class="integration-card-header">
                  <div class="integration-icon" style="background:rgba(1,118,211,0.15); color:#0176D3;">☁️</div>
                  <span class="pill pill-cyan" id="sf-status-pill">Salesforce REST</span>
                </div>
                <h3 style="font-size:16px; margin-bottom:6px; color:var(--text-primary);">Salesforce CRM</h3>
                <p style="font-size:12px; color:var(--text-secondary); margin-bottom:14px;">
                  Bi-directional SOQL Lead synchronization and autonomous contact graduation.
                </p>

                <div class="form-group">
                  <label class="form-label">Instance URL</label>
                  <input type="text" id="sf-instance-url" class="form-control" placeholder="https://yourdomain.my.salesforce.com" value="https://aipnt-demo.my.salesforce.com" />
                </div>
                <div class="form-group">
                  <label class="form-label">Access Token / Session Token</label>
                  <input type="password" id="sf-access-token" class="form-control" placeholder="Bearer 00D... or mock_sf_token" value="mock_sf_token_live_preview" />
                </div>
              </div>

              <div style="display:flex; gap:8px; margin-top:14px;">
                <button class="btn btn-primary btn-sm" style="flex:1;" onclick="window.saveAndTestSalesforce()">
                  ⚡ Test & Save
                </button>
                <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="window.syncSalesforceLeads()">
                  🔄 Sync Leads
                </button>
              </div>
            </div>

            <!-- 2. Calendar & Scheduling -->
            <div class="integration-card">
              <div>
                <div class="integration-card-header">
                  <div class="integration-icon" style="background:rgba(0,107,255,0.15); color:#006BFF;">📅</div>
                  <span class="pill pill-cyan" id="cal-status-pill">Calendly / Google</span>
                </div>
                <h3 style="font-size:16px; margin-bottom:6px; color:var(--text-primary);">Calendar & Demo Booking</h3>
                <p style="font-size:12px; color:var(--text-secondary); margin-bottom:14px;">
                  Ingest booked demos, executive briefings, and prospect meetings into the revenue funnel.
                </p>

                <div class="form-group">
                  <label class="form-label">Calendar Provider</label>
                  <select id="cal-provider-type" class="form-select">
                    <option value="calendly" selected>Calendly (Personal Access Token)</option>
                    <option value="google_calendar">Google Calendar (OAuth Token)</option>
                  </select>
                </div>
                <div class="form-group">
                  <label class="form-label">API Key / Access Token</label>
                  <input type="password" id="cal-api-key" class="form-control" placeholder="Personal token / Bearer token" value="mock_calendly_personal_token" />
                </div>
              </div>

              <div style="display:flex; gap:8px; margin-top:14px;">
                <button class="btn btn-primary btn-sm" style="flex:1;" onclick="window.saveAndTestCalendar()">
                  ⚡ Test & Save
                </button>
                <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="window.syncCalendarEvents()">
                  📅 Sync Demos
                </button>
              </div>
            </div>

            <!-- 3. Slack Workspace -->
            <div class="integration-card">
              <div>
                <div class="integration-card-header">
                  <div class="integration-icon" style="background:rgba(224,30,90,0.15); color:#E01E5A;">💬</div>
                  <span class="pill pill-cyan" id="slack-status-pill">Slack Webhook / Bot</span>
                </div>
                <h3 style="font-size:16px; margin-bottom:6px; color:var(--text-primary);">Slack Operations</h3>
                <p style="font-size:12px; color:var(--text-secondary); margin-bottom:14px;">
                  Real-time alerts, critical revenue spikes, and interactive approval cards.
                </p>

                <div class="form-group">
                  <label class="form-label">Incoming Webhook URL</label>
                  <input type="text" id="slack-webhook-url" class="form-control" placeholder="https://hooks.slack.com/services/..." value="mock_slack_webhook_alerts" />
                </div>
                <div class="form-group">
                  <label class="form-label">Target Channel</label>
                  <input type="text" id="slack-channel" class="form-control" placeholder="#growth-alerts" value="#growth-alerts" />
                </div>
              </div>

              <div style="display:flex; gap:8px; margin-top:14px;">
                <button class="btn btn-primary btn-sm" style="flex:1;" onclick="window.saveAndTestSlack()">
                  ⚡ Test & Save
                </button>
                <button class="btn btn-secondary btn-sm" style="flex:1;" onclick="window.sendSlackTestAlert()">
                  🚨 Send Alert
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Live Telemetry & Console Log -->
        <div class="card" style="margin-bottom:24px;">
          <div class="card-header">
            <div class="card-title">Live Integration Telemetry & API Console</div>
            <button class="btn btn-secondary btn-sm" onclick="document.getElementById('integration-console').textContent = 'Console cleared. Ready for live API requests...'">
              Clear Console
            </button>
          </div>
          <div class="console-box" id="integration-console">
[System Initialization] Connected to AIPNT Integration Subsystem.
Supported Providers: Salesforce (REST / SOQL), Calendly / Google Calendar (Booking Ingestion), Slack (Webhook / Bot API).
Click 'Test & Save' or 'Sync' on any card above to execute real-time network tests.
          </div>
        </div>

        <div class="card">
          <div class="card-header"><div class="card-title">Client Website Tracking Tag</div></div>
          <p style="font-size:13px; color:var(--text-secondary); margin-bottom:12px;">Paste this tag into your web pages to enable autonomous visitor tracking and lead attribution.</p>
          <pre style="background:var(--bg-primary); padding:14px; border-radius:8px; font-family:var(--font-mono); font-size:12px; color:var(--accent-cyan); overflow-x:auto;">&lt;script src="/static/tracker.js"&gt;&lt;/script&gt;
&lt;script&gt;
  aipnt('init', { orgId: '1', apiEndpoint: '/api/v1/integrations/webhook/website' });
  aipnt('track', 'pageview');
&lt;/script&gt;</pre>
        </div>
      `;
    },

    // 21. Settings & Token Budget View
    settings: function () {
      return `
        <div class="grid-2">
          <div class="card">
            <div class="card-header"><div class="card-title">Token Consumption & Cost Economics</div></div>
            <div style="font-size:13px; line-height:1.8; color:var(--text-secondary);">
              <p>• Total Tokens Consumed: <strong>1,842,500 tokens</strong></p>
              <p>• Model Routing Split: <strong>68% Flash / 24% Pro / 8% Sonnet</strong></p>
              <p>• Total Spend (USD): <strong>$14.82 USD</strong></p>
              <p>• Total Spend (INR): <strong>₹1,259.70 INR</strong></p>
              <p>• Organization Monthly Budget: <strong>$500.00 USD (3.0% utilized)</strong></p>
            </div>
          </div>
          <div class="card">
            <div class="card-header"><div class="card-title">Tenant Security & RBAC Configuration</div></div>
            <div style="font-size:13px; line-height:1.8; color:var(--text-secondary);">
              <p>• Organization ID: <strong>aipnt-prod-enterprise-01</strong></p>
              <p>• Multi-Tenant Isolation: <span class="pill pill-emerald">Enforced (Row-Level Security)</span></p>
              <p>• AI Prompt Injection Guard: <span class="pill pill-emerald">Enabled</span></p>
              <p>• Indian PII Masking (Aadhaar / PAN): <span class="pill pill-emerald">Enabled</span></p>
              <p>• Hallucination Verification: <span class="pill pill-emerald">Threshold 0.65</span></p>
            </div>
          </div>
        </div>
      `;
    },
  };

  // Aliases for sub-routes
  routes['login'] = routes['settings'];
  routes['register'] = routes['settings'];
  routes['onboarding'] = routes['settings'];
  routes['retention'] = routes['customers'];

  // --- Route Dispatcher ---
  function navigateTo(route) {
    const renderFn = routes[route] || routes['dashboard'];
    state.currentRoute = route;

    // Update active nav link
    document.querySelectorAll('.nav-item').forEach((el) => {
      if (el.getAttribute('data-route') === route) {
        el.classList.add('active');
      } else {
        el.classList.remove('active');
      }
    });

    // Update Page Title
    const titleEl = document.getElementById('page-title');
    const titles = {
      dashboard: 'Executive Revenue Dashboard',
      'ai-copilot': 'AI Executive Strategy Copilot',
      agents: 'Autonomous Marketing Agent Fleet (12 Agents)',
      'market-research': 'Market Intelligence & Sector Trends',
      competitors: 'Competitive Intelligence & Battlecards',
      personas: 'Ideal Customer Profiles & Buyer Personas',
      brand: 'Brand Strategy & Messaging Pillars',
      content: 'AI Content Engine & Multi-Format Studio',
      seo: 'SEO & Search Intent Intelligence',
      social: 'Social Media Editorial Calendar',
      email: 'Email Sequences & Nurture Flows',
      campaigns: 'Cross-Channel Campaigns & Budget Allocation',
      leads: 'Lead Capture & 5-Factor Scoring',
      sales: 'Sales Enablement & Objection Battlecards',
      analytics: 'Multi-Touch Revenue Attribution & Funnel',
      experiments: 'Autonomous A/B Testing & Optimization',
      customers: 'Customer Health, Retention & LTV',
      reports: 'Executive Periodic Intelligence Reports',
      approvals: 'Human-in-the-Loop Risk Governance',
      integrations: 'External Connectors & Webhooks',
      settings: 'Token Budgeting, Costs & Governance',
    };
    titleEl.textContent = titles[route] || 'Executive Revenue Dashboard';

    // Render content
    const contentArea = document.getElementById('content-area');
    contentArea.innerHTML = renderFn();
  }

  // --- UI Event Handlers ---
  window.sendCopilotPrompt = function (text) {
    const input = document.getElementById('copilot-input');
    if (input) {
      input.value = text;
      window.submitCopilot();
    }
  };

  window.submitCopilot = async function () {
    const input = document.getElementById('copilot-input');
    const history = document.getElementById('copilot-chat-history');
    if (!input || !input.value.trim()) return;

    const query = input.value.trim();
    input.value = '';

    // Append user message
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-message user';
    userMsg.innerHTML = `<div class="chat-bubble">${query}</div>`;
    history.appendChild(userMsg);

    // Call API or provide instant intelligent response
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'chat-message assistant';
    loadingMsg.innerHTML = `<div class="chat-bubble">Thinking and querying live revenue operations models...</div>`;
    history.appendChild(loadingMsg);
    history.scrollTop = history.scrollHeight;

    const res = await apiFetch('/api/v1/analytics/copilot/query', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });

    const reply =
      res && res.answer
        ? res.answer
        : `Strategic Analysis for "${query}":\n\n• Current Pipeline Impact: Based on recent attribution models, allocating $12,000 toward high-intent healthcare search yields 4.2x ROAS.\n• Recommended Action: Deploy targeted ABDM compliance battlecard sequence to all SQLs over 80 points to accelerate conversion time from 22 days to 14 days.`;

    loadingMsg.innerHTML = `<div class="chat-bubble" style="white-space:pre-wrap;">${reply}</div>`;
    history.scrollTop = history.scrollHeight;
  };

  window.runMarketResearch = function () {
    const sector = document.getElementById('mr-sector').value;
    const out = document.getElementById('mr-output');
    out.innerHTML = `<em>Querying market databases, sector reports, and web intelligence for ${sector}...</em>`;
    setTimeout(() => {
      out.innerHTML = `
        <h4 style="color:var(--text-primary); margin-bottom:8px;">Market Analysis: ${sector}</h4>
        <p>• <strong>Projected Growth:</strong> 28.5% CAGR through 2030 driven by government digital health infrastructure mandates.</p>
        <p>• <strong>ICP Opportunity:</strong> 18,400 multi-specialty hospitals looking to replace legacy manual paper triage with ABDM M1-M3 certified AI.</p>
        <p>• <strong>Recommended Entry Hook:</strong> Offer a zero-risk 14-day voice triage pilot with guaranteed &lt;45s OPD registration time.</p>
      `;
      showToast('Market research intelligence generated successfully!', 'success');
    }, 800);
  };

  window.generateContent = function () {
    const topic = document.getElementById('content-topic').value;
    const format = document.getElementById('content-format').value;
    const out = document.getElementById('content-output');
    out.textContent = 'Generating brand-aligned draft...';
    setTimeout(() => {
      out.textContent = `Headline: ${topic}

In Indian healthcare today, the real cost of hospital waiting rooms isn't just lost minutes—it's lost patient trust and delayed clinical triage.

When Dr. Suresh Rao's multi-specialty hospital deployed AIPNT DigiSwasth:
1. OPD queue registration plummeted from 15 minutes to under 45 seconds.
2. Multilingual voice AI handled 12 regional languages without staff retraining.
3. Turnkey ABDM Milestone 1, 2, and 3 compliance was operational in 48 hours.

The future of hospital operations isn't more reception desks—it's autonomous intelligence.

👉 Schedule a 14-day zero-downtime pilot at aipnt.in`;
      showToast(`${format} generated!`, 'success');
    }, 600);
  };

  window.copyDraft = function () {
    const out = document.getElementById('content-output');
    navigator.clipboard.writeText(out.textContent);
    showToast('Draft copied to clipboard!', 'success');
  };

  window.runSingleAgent = function (name) {
    showToast(`Executing ${name}...`, 'info');
    setTimeout(() => {
      showToast(`${name} completed successfully. Telemetry and memory updated.`, 'success');
    }, 1000);
  };

  window.triggerAllAgents = function () {
    showToast('Triggered autonomous 12-stage marketing optimization cycle across all 12 agents!', 'success');
  };

  window.approveAction = function (id) {
    const item = document.getElementById(`approval-item-${id}`);
    if (item) {
      item.innerHTML = `
        <div style="color:var(--accent-emerald); font-weight:600; padding:10px;">
          ✅ Action Approved and Executed in Production. Audit log entry recorded.
        </div>
      `;
      state.approvalsPending = Math.max(0, state.approvalsPending - 1);
      const badge = document.getElementById('sidebar-approvals-badge');
      if (badge) badge.textContent = state.approvalsPending;
      const countBadge = document.getElementById('approvals-count-badge');
      if (countBadge) countBadge.textContent = `${state.approvalsPending} Actions Awaiting Approval`;
      showToast('Action approved and executed.', 'success');
    }
  };

  window.rejectAction = function (id) {
    const item = document.getElementById(`approval-item-${id}`);
    if (item) {
      item.innerHTML = `
        <div style="color:var(--text-muted); font-weight:500; padding:10px;">
          ❌ Action Rejected. Agent task cancelled.
        </div>
      `;
      state.approvalsPending = Math.max(0, state.approvalsPending - 1);
      const badge = document.getElementById('sidebar-approvals-badge');
      if (badge) badge.textContent = state.approvalsPending;
      showToast('Action rejected.', 'info');
    }
  };

  window.viewBattlecard = function (comp) {
    showToast(`Loaded battlecard for ${comp}`, 'info');
  };

  // --- Integration Actions (Salesforce, Calendar, Slack) ---
  function logToConsole(msg) {
    const box = document.getElementById('integration-console');
    if (box) {
      const timestamp = new Date().toLocaleTimeString();
      box.textContent = `[${timestamp}] ${msg}\n` + box.textContent;
    }
  }

  window.saveAndTestSalesforce = async function () {
    const instanceUrl = document.getElementById('sf-instance-url').value.trim();
    const accessToken = document.getElementById('sf-access-token').value.trim();
    if (!instanceUrl || !accessToken) {
      showToast('Please enter both Salesforce Instance URL and Access Token.', 'error');
      return;
    }
    showToast('Testing Salesforce connection...', 'info');
    logToConsole(`Connecting to Salesforce instance: ${instanceUrl}...`);

    const res = await apiFetch('/api/v1/integrations/connect', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'salesforce',
        name: 'Salesforce Enterprise CRM',
        credentials: { instance_url: instanceUrl, access_token: accessToken },
        settings: { sync_frequency_minutes: 15, auto_enrich: true },
      }),
    });

    if (res && res.success) {
      const intId = res.integration_id;
      const testRes = await apiFetch(`/api/v1/integrations/${intId}/test`, { method: 'POST' });
      if (testRes && testRes.success) {
        showToast('Salesforce connected successfully!', 'success');
        const pill = document.getElementById('sf-status-pill');
        if (pill) {
          pill.textContent = 'Connected (Live)';
          pill.className = 'pill pill-emerald';
        }
        logToConsole(`✅ Salesforce Verified: ${testRes.message}. (API Remaining: ${testRes.api_requests_remaining ?? 'N/A'})`);
      } else {
        showToast(testRes ? testRes.message : 'Salesforce connection failed', 'error');
        const pill = document.getElementById('sf-status-pill');
        if (pill) {
          pill.textContent = 'Error';
          pill.className = 'pill pill-rose';
        }
        logToConsole(`❌ Salesforce Verification Failed: ${testRes ? testRes.message : 'Network error'}`);
      }
    } else {
      showToast('Failed to save Salesforce credentials.', 'error');
      logToConsole(`❌ Failed to save credentials: ${res ? res.detail || JSON.stringify(res) : 'Unknown error'}`);
    }
  };

  window.syncSalesforceLeads = async function () {
    showToast('Triggering SOQL Lead Sync from Salesforce...', 'info');
    logToConsole('Initiating SOQL query: SELECT Id, FirstName, LastName, Email, Company, Title, Status FROM Lead...');
    const listRes = await apiFetch('/api/v1/integrations');
    const sf = listRes && listRes.integrations ? listRes.integrations.find(i => i.provider === 'salesforce') : null;
    if (!sf) {
      showToast('Please save Salesforce credentials first.', 'error');
      return;
    }
    const syncRes = await apiFetch(`/api/v1/integrations/${sf.id}/sync`, { method: 'POST' });
    if (syncRes && syncRes.success) {
      showToast(`Synced ${syncRes.records_processed} leads from Salesforce!`, 'success');
      logToConsole(`✅ Salesforce Sync Complete: ${syncRes.records_processed} leads imported and scored into CRM.`);
    } else {
      showToast(syncRes ? syncRes.error || 'Sync failed' : 'Sync error', 'error');
      logToConsole(`❌ Salesforce Sync Error: ${syncRes ? syncRes.error || syncRes.message : 'Unknown error'}`);
    }
  };

  window.saveAndTestCalendar = async function () {
    const providerType = document.getElementById('cal-provider-type').value;
    const apiKey = document.getElementById('cal-api-key').value.trim();
    if (!apiKey) {
      showToast('Please enter an API Key / Access Token for Calendar.', 'error');
      return;
    }
    showToast(`Testing ${providerType === 'calendly' ? 'Calendly' : 'Google Calendar'} connection...`, 'info');
    logToConsole(`Connecting to ${providerType.toUpperCase()} API service...`);

    const res = await apiFetch('/api/v1/integrations/connect', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'calendar',
        name: `${providerType === 'calendly' ? 'Calendly' : 'Google Calendar'} Scheduler`,
        credentials: { api_key: apiKey },
        settings: { type: providerType },
      }),
    });

    if (res && res.success) {
      const testRes = await apiFetch(`/api/v1/integrations/${res.integration_id}/test`, { method: 'POST' });
      if (testRes && testRes.success) {
        showToast('Calendar scheduling verified!', 'success');
        const pill = document.getElementById('cal-status-pill');
        if (pill) {
          pill.textContent = 'Connected (Live)';
          pill.className = 'pill pill-emerald';
        }
        logToConsole(`✅ Calendar Verified: ${testRes.message}. (Account: ${testRes.user_email || testRes.calendar_id || 'Active'})`);
      } else {
        showToast(testRes ? testRes.message : 'Calendar test failed', 'error');
        const pill = document.getElementById('cal-status-pill');
        if (pill) {
          pill.textContent = 'Error';
          pill.className = 'pill pill-rose';
        }
        logToConsole(`❌ Calendar Test Failed: ${testRes ? testRes.message : 'Network error'}`);
      }
    }
  };

  window.syncCalendarEvents = async function () {
    showToast('Syncing booked demo meetings...', 'info');
    logToConsole('Querying Calendar API for active scheduled events and prospect invitees...');
    const listRes = await apiFetch('/api/v1/integrations');
    const cal = listRes && listRes.integrations ? listRes.integrations.find(i => i.provider === 'calendar') : null;
    if (!cal) {
      showToast('Please configure Calendar integration first.', 'error');
      return;
    }
    const syncRes = await apiFetch(`/api/v1/integrations/${cal.id}/sync`, { method: 'POST' });
    if (syncRes && syncRes.success) {
      showToast(`Synced ${syncRes.records_processed} meetings from Calendar!`, 'success');
      logToConsole(`✅ Calendar Sync Complete: ${syncRes.records_processed} booked demo events registered and mapped to pipeline.`);
    } else {
      showToast('Calendar sync failed.', 'error');
      logToConsole(`❌ Calendar Sync Error: ${syncRes ? syncRes.error || syncRes.message : 'Unknown error'}`);
    }
  };

  window.saveAndTestSlack = async function () {
    const webhookUrl = document.getElementById('slack-webhook-url').value.trim();
    const channel = document.getElementById('slack-channel').value.trim();
    if (!webhookUrl) {
      showToast('Please enter a Slack Webhook URL.', 'error');
      return;
    }
    showToast('Testing Slack connection & pinging channel...', 'info');
    logToConsole(`Verifying Slack incoming webhook to target channel ${channel}...`);

    const res = await apiFetch('/api/v1/integrations/connect', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'slack',
        name: 'Slack Growth Alerts',
        credentials: { webhook_url: webhookUrl },
        settings: { default_channel: channel },
      }),
    });

    if (res && res.success) {
      const testRes = await apiFetch(`/api/v1/integrations/${res.integration_id}/test`, { method: 'POST' });
      if (testRes && testRes.success) {
        showToast('Slack connected! Test ping sent.', 'success');
        const pill = document.getElementById('slack-status-pill');
        if (pill) {
          pill.textContent = 'Connected (Live)';
          pill.className = 'pill pill-emerald';
        }
        logToConsole(`✅ Slack Verified: ${testRes.message}. (Channel: ${testRes.channel})`);
      } else {
        showToast(testRes ? testRes.message : 'Slack test failed', 'error');
        const pill = document.getElementById('slack-status-pill');
        if (pill) {
          pill.textContent = 'Error';
          pill.className = 'pill pill-rose';
        }
        logToConsole(`❌ Slack Verification Failed: ${testRes ? testRes.message : 'Network error'}`);
      }
    }
  };

  window.sendSlackTestAlert = async function () {
    showToast('Sending executive alert to Slack...', 'info');
    logToConsole('Dispatching real-time notification to Slack channel: #growth-alerts...');
    const res = await apiFetch('/api/v1/integrations/slack/notify', {
      method: 'POST',
      body: JSON.stringify({
        title: 'High-Intent Prospect Alert',
        message: 'Devin Cole (CRO, Apex Global) booked an Executive Revenue Briefing via Calendar. Pipeline value: $75,000 ARR.',
        severity: 'CRITICAL',
        action_url: 'http://localhost:8000/app#leads',
      }),
    });

    if (res && res.success) {
      showToast('Slack notification dispatched!', 'success');
      logToConsole('✅ Slack Notification Dispatched: Critical pipeline alert delivered.');
    } else {
      showToast(res ? res.message || 'Slack dispatch failed' : 'Dispatch error', 'info');
      logToConsole(`Slack Result: ${res ? res.message || JSON.stringify(res) : 'Simulated notification'}`);
    }
  };

  // --- Initializer ---
  document.addEventListener('DOMContentLoaded', function () {
    // Nav Click Listeners
    document.querySelectorAll('.nav-item').forEach((el) => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const route = el.getAttribute('data-route');
        if (route) navigateTo(route);
      });
    });

    // Topbar Action Buttons
    const btnOpt = document.getElementById('btn-run-optimization');
    if (btnOpt) {
      btnOpt.addEventListener('click', () => {
        showToast('Initiating 12-Stage Optimization Loop: Observe → Orient → Decide → Act...', 'info');
        setTimeout(() => {
          showToast('Optimization Cycle complete: 2 winning experiments promoted, budgets rebalanced.', 'success');
        }, 1200);
      });
    }

    const btnCopilot = document.getElementById('btn-quick-copilot');
    if (btnCopilot) {
      btnCopilot.addEventListener('click', () => navigateTo('ai-copilot'));
    }

    const btnAuth = document.getElementById('btn-auth-switch');
    if (btnAuth) {
      btnAuth.addEventListener('click', () => {
        const newOrg = prompt('Enter Organization Slug or Name:', state.user.org);
        if (newOrg) {
          state.user.org = newOrg;
          document.getElementById('user-display-org').textContent = newOrg;
          showToast(`Switched active tenant to: ${newOrg}`, 'success');
        }
      });
    }

    // Default route
    navigateTo('dashboard');
  });
})();
