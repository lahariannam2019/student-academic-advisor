# Student Academic Advisor

> A personalized, data-driven academic intelligence companion for college students that combines reliable deterministic calculations with server-side AI explanations.

```text
Student Academic Data → Deterministic Calculations → Priority Engine → Personalized Recommendations → AI Explanation
```

---

## 🚀 Key Features

1. **Dashboard ("Today" Page)**:
   - Personalized hero greeting highlighting the day's top focus area.
   - Status cards: Current CGPA, Overall Attendance Risk, Next Upcoming Exam countdown, Pending Assignments.
   - 3–5 daily study blocks with time duration, subject, and transparent rationale.
   - Workload capacity optimization alert if requested study effort exceeds available time.
   - Grounded daily AI strategy brief.

2. **Deterministic Academic Calculations**:
   - **Attendance Tracking**: Calculates exact percentage, safe missed class buffer, or exact consecutive classes needed to recover minimum policy (e.g. 75%).
   - **Marks & Performance**: Credit-weighted averages, historical trend detection, strong and weak subject classifications.
   - **GPA / CGPA & Feasibility**: Credit-weighted SGPA & cumulative CGPA with mathematical goal feasibility verification.

3. **Deterministic Priority Engine**:
   - Multi-factor scoring system combining exam proximity, attendance risk, marks decline, and assignment deadlines into a transparent 0–100 score with human-readable reasons.

4. **Daily Study Planner**:
   - Generates focused study blocks (Revision, Practice, Assignment, Exam Prep) adhering to student's daily available study hours.
   - Interactive actions: Mark Complete (with satisfying completion feedback), Skip, and Reschedule.

5. **Server-Side AI Academic Advisor**:
   - Integrated with Claude API server-side using the Anthropic SDK.
   - Uses strict anti-hallucination rules and receives a deterministic JSON context snapshot.
   - Never hallucinates grades, attendance, or dates.
   - Transparent "View Grounding Facts" inspector in every advisory chat turn.

6. **Actionable Analytics**:
   - CGPA growth trajectory across historical semesters.
   - Attendance safety margins visualization (safe buffers vs. critical warning zones).
   - Subject strength/attention breakdowns.

---

## 🛠 Tech Stack

- **Frontend**: React 19, Vite, TypeScript, Tailwind CSS, Lucide React icons, Recharts, React Router.
- **Backend**: Python 3.11, FastAPI, Pydantic V2, SQLAlchemy, Alembic, Uvicorn.
- **Database**: PostgreSQL (Supabase) + local SQLite development fallback.
- **Authentication**: Supabase Auth + Instant 1-Click Demo Evaluation Mode.
- **AI**: Claude 3.5 Sonnet (Server-side Anthropic SDK).

---

## 🏃 Quick Start

### 1. Automated Start (Windows)
Double-click `start.bat` or run:
```powershell
.\start.bat
```

### 2. Manual Start

#### Backend
```powershell
cd backend
.venv\Scripts\activate
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
API Documentation will be accessible at: `http://127.0.0.1:8000/api/docs`

#### Frontend
```powershell
cd frontend
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run backend test suite:
```powershell
cd backend
.venv\Scripts\pytest tests/ -v
```
All 18 tests cover calculations, database models, priority engine, planner capacity, health check, and API endpoints.

---

## 🔒 Security & Privacy

- All AI communications happen server-side; API keys are never exposed in frontend bundles.
- Password hashes and authentication handled securely via Supabase.
- Clean `.env.example` templates provided with placeholders only.
