# Nena AI — Master Demo Video Prompt & Recording Script
**Target Duration:** 2 minutes 45 seconds – 3 minutes  
**Audience:** Institutional Healthcare Donors, Ministry of Health Officials, Clinic Networks, Hackathon/Pitch Judges, Health-Tech Investors  
**Tone:** Confident, mission-driven, authoritative, technically rigorous (Zero-Trust, Kenyan digital health context)  
**Presenter / Voiceover Persona:** Cynthia Moraa (Co-Founder & Lead Engineer) or Professional African Tech Voiceover  

---

## 🎬 1. AI Video Generator Master Prompt (For InVideo, HeyGen, Synthesia, or ElevenLabs)

> **Copy & Paste Prompt:**
> "Create a 3-minute, high-energy, institutional product demonstration video for 'Nena AI', a Kenyan digital health financing platform. The video showcases a unified healthcare subsidy exchange connecting community clinics directly with NGO funders. The visual style features a crisp, modern SaaS aesthetic with Trust Blue (#0A3D91) and Health Teal (#00C49A) branding, live UI screen recordings, animated Zero-Trust architectural flows, and Kenyan primary healthcare context. The narrator speaks with a warm, articulate Kenyan/African English accent, delivering an authoritative technical pitch explaining how Nena AI eliminates patient out-of-pocket costs (KES 0 copay), enforces a 4-Stage Zero-Trust verification engine, prevents subsidy fraud via heuristic anomaly scoring, updates an append-only SHA-256 financial ledger, and settles instantly via simulated M-Pesa Daraja B2C. Include on-screen text callouts for key metrics: 'KES 0 Patient Copay', '342ms Settlement Latency', 'SHA-256 Chained Ledger', 'Offline-First IndexedDB Vault'."

---

## ⏱️ 2. Detailed Scene-by-Scene Director's Cut & Screenplay

```
Total Run Time: 02:45
Resolution: 1080p 60fps (1920x1080)
Theme: Light mode, high-contrast, professional SaaS
Screen: http://localhost:5173
```

---

### **ACT I: The Crisis & The Solution (0:00 – 0:35)**

#### **Scene 1: The Problem at the Primary Care Level (0:00 – 0:18)**
- **Visual:**
  - B-Roll or high-res graphic of a bustling Kenyan community health centre (Nairobi / Kisumu).
  - Split-screen infographic showing two pain points:
    1. *Clinics:* Red invoice stacks marked "60–90 Day Subsidy Delays".
    2. *Patients:* A mother reaching into an empty purse marked "Out-of-pocket barrier: KES 1,200".
- **Voiceover (VO):**
  > *"In Kenya, independent primary care clinics are the frontline of healthcare. Yet, millions of mothers and children risk being turned away because manual subsidy reconciliations take up to ninety days. Clinics face crippling cash flow gaps, while institutional donors lack verifiable, real-time proof of where their funding goes."*

#### **Scene 2: Introducing Nena AI (0:18 – 0:35)**
- **Visual:**
  - Dynamic transition to the **Nena AI** logo and web portal at `http://localhost:5173`.
  - Camera glides across the clean top banner: "Zero-Trust Healthcare Subsidy Routing Ledger".
  - On-screen badge animates: **"Patient Copay: KES 0 Guaranteed"**.
- **Voiceover (VO):**
  > *"Enter Nena AI: a Kenyan digital health financing platform and Zero-Trust Subsidy Routing Ledger. We connect independent clinics directly with institutional funders, verifying care encounters in real time, settling payments instantly via M-Pesa, and ensuring vulnerable patients pay zero shillings out-of-pocket."*

---

### **ACT II: Point-of-Care Clinic Flow & Consent (0:35 – 1:25)**

#### **Scene 3: Patient Check-In & Voucher Selection (0:35 – 0:55)**
- **Screen Action:**
  - Show the **Clinic Portal** tab.
  - Cursor clicks on the top-right role switcher showing `Nurse Jane (Mwangaza Community Clinic)`.
  - Point to the hardware attestation badge: `Mwangaza Demo Tablet` • `DEMO-DEVICE-FINGERPRINT-001` (Active).
  - Cursor clicks on the preset card for **Amina Mwangi (DEMO-PATIENT-001)**.
  - Notice the form automatically populates with `MATERNAL_CARE`, `KES 1,200`, and clinical antenatal notes.
- **Voiceover (VO):**
  > *"Let's see this live from the perspective of Nurse Jane at Mwangaza Community Clinic in Nairobi. A registered tablet hardware fingerprint authenticates the facility. When expectant mother Amina arrives, her voucher is looked up through an HMAC-pseudonymized identifier, ensuring her national ID is never exposed."*

#### **Scene 4: The 4-Stage Zero-Trust Engine & Patient Consent OTP (0:55 – 1:25)**
- **Screen Action:**
  - Cursor clicks the large blue button: **"Authorize Claim & Verify Consent (KES 0 Copay)"**.
  - A modal pops up: **"Stage 2: Patient Consent Verification"** with a 300-second live countdown timer.
  - Highlight the mock SMS notification banner on screen: *"Nena AI: Your verification code is 123456"*.
  - Cursor clicks **"Auto-fill Valid OTP (123456)"**, then clicks **"Confirm Consent & Authorize"**.
  - Immediate visual feedback: Green checkmark animation with:
    - *"Four-Stage Verification Passed & Subsidy Settled!"*
    - *"M-Pesa Receipt: MPESA-SIM-B2C-..."*
  - The clinic settlement wallet updates from KES 14,800 to KES 16,000.
- **Voiceover (VO):**
  > *"Before a single shilling moves, the encounter must clear Nena AI's Four-Stage Zero-Trust engine: Identity, Patient Consent, Program Policy, and Heuristic Anomaly Scoring. The patient receives an immediate SMS verification code. Once verified, patient consent is cryptographically bound, the subsidy is authorized in under 350 milliseconds, and an automated M-Pesa B2C payment is dispatched directly to the clinic's digital wallet."*

---

### **ACT III: Offline-First Reliability & Anomaly Detection (1:25 – 2:05)**

#### **Scene 5: IndexedDB Offline Vault (1:25 – 1:45)**
- **Screen Action:**
  - In the top navbar, click the **"Online"** toggle. It immediately flips to **"Offline"** in amber (`WifiOff` icon).
  - Fill another demo voucher (**Baby Ethan - DEMO-PATIENT-002**) and click **"Queue Claim in Offline Vault (IndexedDB)"**.
  - Notice the **"1 Queued"** badge pulsing in the navbar.
  - Click the **"Online"** toggle back on. Click **"Sync Now"** in the IndexedDB drawer.
  - Show the queue synchronizing smoothly and settling with the backend.
- **Voiceover (VO):**
  > *"Kenyan primary care doesn't stop when power or mobile connectivity drops. Built as an offline-first PWA, Nena AI uses an encrypted IndexedDB vault to capture encounters offline. The moment connectivity restores, claims are securely replayed and validated server-side without data loss or duplicate risks."*

#### **Scene 6: Anomaly Engine Flagging Suspicious Claims (1:45 – 2:05)**
- **Screen Action:**
  - Switch to the **Zero-Trust Audit** tab using the navbar.
  - Show the **"Suspicious Claims Awaiting Human Adjudication"** table.
  - Click **"Inspect Claim"** on a flagged encounter.
  - The **Four-Stage Claim Inspector Modal** appears, showing Stage 1–3 Passed, and Stage 4 flagged with `BILLING_SPIKE (Weight: 35)` and `OFF_HOURS_CLAIM (Weight: 25)`.
- **Voiceover (VO):**
  > *"To protect institutional capital, Stage 4 evaluates every claim against our explainable anomaly detection model. Any claim exhibiting frequency clustering, billing anomalies, or off-hours spikes is immediately held in a manual audit queue with full algorithmic explainability for human review."*

---

### **ACT IV: Institutional Funder Dashboard & Cryptographic Ledger (2:05 – 2:45)**

#### **Scene 7: NGO Funder Dashboard & Policy Rule Editor (2:05 – 2:25)**
- **Screen Action:**
  - Switch to the **NGO Dashboard** tab.
  - Show the top KPI cards:
    - *Total Allocated:* KES 5,000,000
    - *Subsidies Authorized:* KES 1,842,400
    - *Average Settlement Latency:* 342 ms
  - Hover over the **Recharts Regional Disbursement Bar Chart** (Nairobi vs. Kisumu vs. Mombasa).
  - Click **"Configure Policy Rules"** on *AfyaMama Maternal Subsidy*, change visit cap to `1,500`, and save.
- **Voiceover (VO):**
  > *"For donor organizations like AfyaBridge Foundation, the NGO Dashboard provides unprecedented governance. Donors see live capital pool utilization, real-time geographic disbursements across Kenyan counties, and can dynamically adjust policy rules—like regional boundaries and visit caps—with instant enforcement."*

#### **Scene 8: Cryptographic Chain Verification & Closing (2:25 – 2:45)**
- **Screen Action:**
  - Scroll to the bottom table: **"Live Immutable Financial Ledger"**. Highlight the SHA-256 hash chaining columns (`Prev Hash` linking to `Tx Hash`).
  - Switch to **Zero-Trust Audit** tab and click the prominent green button: **"Verify Cryptographic Chain"**.
  - Show the instant banner: **"CHAIN VALID (UNBROKEN) — All Transactions Verified with 0 Inconsistencies"**.
  - Fade in closing slide with Nena AI logo and call-to-action:
    - *Nena AI — Healthcare Subsidy Routing Ledger*
    - *Email:* founders@nena.health
    - *Website:* https://nena.health
- **Voiceover (VO):**
  > *"Every single transaction is chained in an immutable append-only ledger. With one click, auditors verify SHA-256 integrity from genesis to current head—guaranteeing zero tampering. Nena AI: empowering clinics, reassuring donors, and delivering free healthcare to those who need it most. Thank you."*

---

## 📋 3. Recording Checklist & Settings

| Item | Recommended Setting |
| :--- | :--- |
| **Screen Resolution** | 1920 x 1080 (1080p Full HD) |
| **Browser** | Chrome / Edge with zoom at 100% |
| **URL** | `http://localhost:5173` |
| **Backend State** | Healthy on `http://localhost:8000/api/v1/health` |
| **Audio** | Clear microphone, pop filter, zero background noise |
| **Demo Data** | Fresh seed data with Mwangaza Community Clinic and AfyaBridge Foundation |
| **Mouse Cursor** | Smooth movements, pause 1 second before clicking buttons for visual clarity |
