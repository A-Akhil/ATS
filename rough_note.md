# Rough Notes - ATS Resume Checker Django Application

## Goals
- Build a Django web application with SQLite database
- Allow users to register, create profile, generate LaTeX resume via Gemini API
- Upload/paste job descriptions and get ATS match scores using Sentence-BERT
- Provide admin panel for user management, scoring weight tuning, and logs
- Use modern, eye-catching UI (not plain HTML/CSS)

## Observations
- Project is in `/home/akhil/Downloads/temp/ats-check/`
- Already has `work.md` with complete specifications
- Has `template.tex` (LaTeX template for resume)
- Has `latex-to-pdf/` folder with Docker setup for LaTeX compilation
- User wants eye-catching UI, not basic HTML/CSS

## Requirements Analysis from work.md
1. **Authentication**: User registration, login with email/password
2. **Profile Management**: Store education, skills, experience, projects, certifications
3. **Resume Generation**: Use Gemini API to generate LaTeX resume from profile
4. **Resume Compilation**: Use existing latex-to-pdf service at localhost:8006
5. **Job Matching**: Parse JD, compute BERT-based scores, validate with Gemini
6. **Scoring Logic**: 
   - 35% education, 45% skills, 20% experience (admin configurable)
   - Profession similarity gating (zero if mismatch)
   - Partial credit for transferable skills
7. **Admin Panel**: User management, match logs, weight configuration, audit logs
8. **Database**: SQLite with models for User, Profile, Resume, JobDescription, MatchAttempt, AdminSettings, SystemLog

## Tech Stack Decisions
- **Backend**: Django 5.0+
- **Database**: SQLite (default Django)
- **NLP**: sentence-transformers (BERT), spaCy for parsing
- **API**: Google Gemini API (gemini-1.5-flash)
- **UI Framework**: Tailwind CSS + Alpine.js for modern, interactive UI
- **Icons**: Heroicons or Lucide icons
- **LaTeX Compilation**: Existing service at localhost:8006

## Architecture Plan

### Django Project Structure
```
ats_checker/              # Django project
├── manage.py
├── requirements.txt
├── .env.example
├── ats_checker/          # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                 # Main app
│   ├── models.py         # All data models
│   ├── views.py          # Views/controllers
│   ├── forms.py          # Django forms
│   ├── urls.py           # URL routing
│   ├── admin.py          # Django admin customization
│   ├── services/         # Business logic
│   │   ├── nlp_service.py       # BERT scoring, parsing
│   │   ├── gemini_service.py    # Gemini API calls
│   │   ├── latex_service.py     # LaTeX generation
│   │   └── scoring_service.py   # Match scoring logic
│   ├── templates/        # HTML templates
│   │   ├── base.html
│   │   ├── landing.html
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── profile/
│   │   ├── resume/
│   │   ├── match/
│   │   └── admin_panel/
│   └── static/           # CSS, JS, assets
│       ├── css/
│       └── js/
└── media/                # User uploads
```

### Database Models
1. User (extend Django User)
2. Profile (one-to-one with User)
3. Resume
4. JobDescription
5. MatchAttempt
6. AdminSettings (singleton)
7. SystemLog

## UI Design Approach
- **Framework**: Tailwind CSS for modern, responsive design
- **Components**: Alpine.js for interactive components (modals, dropdowns, tabs)
- **Color Scheme**: Professional gradient-based design (blue/purple/teal theme)
- **Typography**: Modern fonts (Inter or similar)
- **Layout**: Clean, card-based design with smooth transitions
- **Icons**: Heroicons for consistent iconography
- **Forms**: Floating labels, validation feedback, multi-step wizards
- **Animations**: Subtle CSS transitions and hover effects

## Implementation Plan

### Phase 1: Project Setup
1. Create Django project structure
2. Configure settings (database, static files, media)
3. Set up requirements.txt with all dependencies
4. Create .env.example for API keys

### Phase 2: Models & Admin
1. Define all models (User, Profile, Resume, etc.)
2. Create migrations
3. Set up Django admin for model management
4. Create admin settings singleton

### Phase 3: Services Layer
1. NLP Service: BERT embeddings, parsing, scoring
2. Gemini Service: API calls for resume generation and validation
3. LaTeX Service: Template filling, compilation via localhost:8006
4. Scoring Service: Complete matching logic with profession gating

### Phase 4: Authentication & Onboarding
1. Registration with multi-step onboarding form
2. Login/logout
3. Profile creation and editing
4. Password hashing (Django default)

### Phase 5: Resume Generation
1. Profile to LaTeX via Gemini
2. LaTeX compilation to PDF
3. Download functionality
4. Preview and regenerate

### Phase 6: Job Matching
1. JD input (paste or upload)
2. Resume selection (generated or uploaded)
3. BERT-based scoring
4. Gemini validation
5. Results display with breakdown

### Phase 7: Admin Panel
1. User management dashboard
2. Match logs viewer
3. Weight configuration UI
4. System logs and audit trail

### Phase 8: UI Polish
1. Implement Tailwind CSS throughout
2. Add Alpine.js interactions
3. Responsive design
4. Loading states and error handling

## Assumptions
1. Gemini API key will be provided in .env file
2. latex-to-pdf service is already running on localhost:8006
3. sentence-transformers model will download automatically on first run
4. SQLite is sufficient for development and demo
5. User wants complete working code, not just templates

## TODO
- [ ] Create Django project structure
- [ ] Install and configure all dependencies
- [ ] Define all models
- [ ] Implement services layer
- [ ] Build authentication flow
- [ ] Create resume generation feature
- [ ] Build job matching feature
- [ ] Design admin panel
- [ ] Apply Tailwind CSS styling
- [ ] Test all features
- [ ] Create seed data script
- [ ] Write README with setup instructions

## Open Questions
- None at this time. Proceeding with implementation based on work.md specifications.

## Progress Log
- ✓ Created rough_note.md with complete analysis and plan
- ✓ Created Django project structure (ats_checker)
- ✓ Created core app with models
- ✓ Created all data models (User, Profile, Resume, JobDescription, MatchAttempt, AdminSettings, SystemLog)
- ✓ Created service layer:
  - gemini_service.py (using google-genai 1.47.0)
  - nlp_service.py (BERT-based scoring)
  - latex_service.py (PDF compilation)
  - scoring_service.py (complete matching logic)
- ✓ Updated requirements.txt with correct dependencies
- ✓ Configured settings.py with environment variables
- ✓ Created comprehensive views.py with all functionality
- ✓ Created forms.py for all input forms
- ✓ Created URL routing (core/urls.py and project urls.py)
- ✓ Created Django admin configuration
- ✓ Created base template with Tailwind CSS and Alpine.js
- ✓ Created landing page with modern gradient design
- ✓ Created authentication templates (login, register)
- ✓ Created onboarding flow template
- ✓ Created dashboard template with stats and quick actions
- ✓ Created placeholder templates for profile, resume, match, and admin
- ✓ Created comprehensive README.md
- ✓ Created .env file with configuration
- ✓ Created migrations and applied to database
- ✓ BERT model downloaded automatically (all-MiniLM-L6-v2)

## Current Issues Discovered (2025-01-18)

### Issue 1: Resume view template is blank ✓ FIXED
**Problem**: User clicks "Generate Resume" and after generation, gets redirected to resume_view but sees nothing
**Root Cause**: `/core/templates/resume/view.html` only has `{% extends 'base.html' %}` - no content
**Impact**: Cannot view generated resumes even though PDF is successfully created
**Fix Applied**: Created comprehensive resume view template with:
- PDF preview iframe (full page height)
- LaTeX source code display with syntax highlighting
- Action buttons: Download PDF, Download LaTeX, Regenerate, Match with Job
- Resume info sidebar: source type, filename, creation date, status
- Error display if LaTeX compilation failed
- Processing state for resumes still being generated
- Pro tips card
**Status**: ✓ FIXED

### Issue 2: No resume list view ✓ CLARIFIED
**Problem**: User wants to see list of all generated resumes (like in dashboard)
**Root Cause**: Misunderstanding - resume list already exists in generate_resume page, but view wasn't passing resumes context
**Current State**: 
- Dashboard shows recent resumes (working)
- Generate Resume page has "Your Resumes" section at bottom (now working)
- No separate dedicated "All Resumes" page (not needed)
**Fix Applied**: Updated `generate_resume()` view to pass `resumes` context so the resume list at bottom of page displays
**Status**: ✓ FIXED - No separate page needed, navigation link correctly goes to generate page which shows list

### Issue 3: Profile data missing after onboarding ⚠️ ACTIVE (2025-10-31)
**Observed**: Profile page shows "Not provided" for phone, location, LinkedIn, GitHub even after onboarding form submission.
**Initial Hypothesis (failed)**: Updating onboarding view alone would persist new fields.
**New Findings**:
- `Profile` model lacks fields for phone, city, state, linkedin, github (data never persisted).
- Model also missing JSONFields for publications, achievements, leadership.
- Onboarding view assigns to `profile.education` / `profile.experience`, but actual model fields are `education_entries` / `experiences`, so data is saved to non-persisted attributes.
**Plan**:
1. Inspect SQLite DB to confirm profile columns and current data (pending).
2. Update `Profile` model to add contact/info fields and JSON fields for optional sections.
3. Adjust onboarding view to write into correct field names (`education_entries`, `experiences`, etc.).
4. Create and apply migrations; ensure existing code reading from these fields updated accordingly.
5. Retest onboarding flow and profile display.
**Recent Progress**:
- Model updated with new contact/social fields + optional section JSONFields.
- Onboarding view aligned with new field names and responsibilities handling.
- Templates (`profile/onboarding.html`, `profile/profile.html`, `dashboard/dashboard.html`) refreshed to consume `education_entries` / `experiences` and new contact fields.
- Workspace search confirms no lingering references to deprecated `profile.education` / `profile.experience` attributes.
- Migration `core.0002` generated/applied to add new Profile columns.
- DB check (Oct 31, 2025) shows achievements/leadership persisted but publications empty → suggests form wiring/display gap.
- Observation: onboarding form does not pre-fill optional sections (publications, achievements, leadership) so revisits wipe data; profile view lacks sections to render these fields → user perceives data missing.
- Onboarding template updated to pre-populate publications/achievements/leadership inputs and correctly index new dynamic entries.
- Profile view now renders publications, achievements, and leadership sections so saved data is visible.
- Resume generation now passes contact/location plus publications, achievements, leadership to Gemini so LaTeX output can include optional sections.
- Gemini prompt updated to forbid renaming section headings (e.g., ensures "Projects" stays as-is instead of "Selected Projects").
- Match flow now logs GET/POST entry plus detailed NLP, scoring, and Gemini steps to trace performance bottlenecks.
- Pending: manual onboarding submission to confirm publications persist and appear; verify optional sections remain populated after revisiting form; re-generate resume to confirm optional data shows in LaTeX.
**Status**: Investigation in progress; migrations/testing outstanding.

## Task Notes (2025-11-04)

### Goals
- Fix the 404 when visiting `/admin/settings/` by moving the custom admin settings page away from Django's built-in admin namespace.
- Streamline the custom admin navigation so the user-facing links (Dashboard, Profile, Resume, Match Job) disappear on admin pages, leaving only the tooling relevant to admins (database visibility and scoring controls).
- Replace the blank admin settings template with a Tailwind-styled form so scoring parameters can be adjusted without resorting to Django admin.
- Build a custom data viewer within the admin panel so admins can browse core records without being redirected to Django's built-in interface.

### Observations
- `core/urls.py` still exposes `admin_settings` at `admin/settings/`, which collides with Django's admin catch-all; the new admin dashboard already lives under `/admin-panel/`.
- The shared navigation in `core/templates/base.html` renders the primary user links for every authenticated page; no flag exists to suppress it for admin-only screens.
- Both `admin_panel` and `admin_settings` views currently pass context without any signal to adjust the layout, so templates cannot change navigation behavior.
- Links inside `core/templates/admin_panel/dashboard.html` still target the old `admin_settings` path and should follow the revised route once it moves under `/admin-panel/`.
- `core/templates/admin_panel/settings.html` is empty, leaving `/admin-panel/settings/` blank even after routing was fixed.
- Admin dashboard quick actions still reference Django's built-in admin for data browsing, which the user specifically wants to avoid.

### Plan
1. Update `core/urls.py` so `admin_settings` lives at `admin-panel/settings/`, freeing the `/admin/` namespace for Django's built-in admin without clashes.
2. Inject a `hide_primary_nav` flag (or similar) from both admin views and teach `base.html` to skip rendering the standard Dashboard/Profile/Resume/Match Job links when the flag is present.
3. Provide a minimal admin-specific top bar when the primary nav is hidden so admins can still reach the dashboard and scoring settings quickly.
4. Replace all template references to the old settings URL with the new `admin-panel` variant and smoke test navigation after the change.
5. Implement a styled settings template that renders `AdminSettingsForm`, shows current weights, and surfaces validation errors inline.
6. Introduce an `admin_data` view and template that list recent Users, Resumes, Job Descriptions, and Match Attempts in Tailwind tables so admins can review database content without Django admin.
7. Update admin navigation and quick actions to link to the new data viewer instead of Django's built-in interface.

### Progress
- Re-pointed the custom admin settings route to `admin-panel/settings/`, eliminating the collision with Django's built-in admin URLs.
- Passed a `hide_primary_nav` flag plus active tab marker from both admin views and reworked `base.html` to render a slim admin navigation with direct links to the overview, scoring controls, and Django's data admin.
- Updated the admin dashboard hero buttons and quick actions so they now surface only the requested tools (custom data viewer and scoring configuration) and removed links to user-focused pages.
- Built a fully-styled scoring settings page that renders `AdminSettingsForm`, shows current thresholds, and provides inline validation feedback.
- Implemented a custom data viewer (`admin_panel/data.html`) plus supporting view and route, surfacing recent Users, Resumes, Job Descriptions, and Match Attempts within the Tailwind-styled admin experience.
- Applied Tailwind styling directly to `AdminSettingsForm` widgets so inputs align visually with the rest of the admin UI.
- Added vertical scrolling to each dataset table in the Platform Data Viewer so large collections remain manageable within the page.
- Added per-user "View Details" modals that surface the full profile (contact info, education, experience, projects, certifications, publications, achievements, leadership) without leaving the data viewer.
- Expanded job description cells to provide full text inside a scrollable container, preventing truncated qualification blurbs.
- Simplified the resume generation wizard by removing the unused template selection step so the flow now covers customization and generation only, aligning with the single available LaTeX template.

## Task Notes (2025-10-31) - Resume Upload Option for Matching

### Goals
- Allow users to run match analysis using an externally prepared resume PDF without having to generate one in the app first.

### Observations
- `match_job` currently requires an existing `Resume` record selected via dropdown; form lacks file upload handling.
- `ResumeUploadForm` already exists with PDF validation but is unused in the flow.
- `match/match.html` form lacks `enctype` for file uploads and Alpine state to toggle upload vs existing selection.
- `MatchAttempt` requires a `Resume` FK, so uploaded files should persist as `Resume` entries (source `uploaded`).
- PDF text extraction utilities (PyPDF2) are already imported in `core/views.py`, so reuse is practical.

### Plan
1. Update `match_job` view to accept either an existing resume selection or a freshly uploaded PDF using `ResumeUploadForm`.
2. If upload selected, extract text via `PyPDF2`, create a `Resume` record (`source_type='uploaded'`), store file, and parse sections before scoring.
3. Refresh `match/match.html` to add a toggle between "Use Saved Resume" and "Upload PDF", include the file input (with proper `enctype`), and adjust required attributes.
4. Pass an instance of `ResumeUploadForm` to the template for rendering, and surface validation/parse failures via Django messages.
5. Log the upload action and ensure match scoring proceeds with the newly created resume entry.

### Open Questions
- Should we expose uploaded resumes in the resume list UI? (Out of scope for now; can revisit after basic upload path is confirmed.)

### Progress
- Extended `match_job` to branch on resume source, validate uploads through `ResumeUploadForm`, extract PDF text, persist uploaded resumes, and reuse the scoring pipeline.
- Introduced a resume source toggle plus file input in `match/match.html`, updated form attributes for multipart posts, and surfaced guidance for upload requirements.

## Task Notes (2025-11-02)

### Goals
- Align profession mismatch messaging with latest user guidance so alerts only appear when the AI reviewer explicitly confirms a mismatch.
- Expand the AI review so candidates receive actionable guidance focused on improving their ATS score, without referencing underlying BERT computations.

### Observations
- `core/services/scoring_service.py` flags `profession_mismatch` before the Gemini review and keeps that flag for persistence even when the AI overrides the score.
- `core/templates/match/result.html` shows the mismatch banner whenever `profession_match_flag` is false, so users still see red warnings after an AI override.
- Gemini validation currently returns scores, reason, and suggestion but does not expose an explicit profession mismatch indicator.
- Latest POST attempt hit a ValueError because the JSON schema example inside the Gemini prompt uses literal braces within an f-string; Python interprets these as formatting tokens.
- Gemini’s current `suggestion` string is concise and occasionally references scoring; user wants a fuller review narrative focusing on resume improvements against the JD without mentioning BERT.
- The profession similarity figure (e.g., 0.10) comes straight from the Sentence-BERT comparison in `compute_profession_similarity`; even if the AI subsequently rules the role aligned, that initial metric still reflects how different the raw text embeddings appear.
- Admin account created via `createsuperuser` lacks an automatic `Profile`, causing `/dashboard/` (and other profile-dependent views) to crash with `User has no profile`.

### Assumptions
- Updating the Gemini prompt to include a `profession_mismatch` boolean and accompanying rationale will not break existing flows; older records without the new field must still render safely.
- Users prefer a softer note when the AI clears the mismatch rather than surfacing the original hard gate.

### Plan
1. Extend the Gemini validation prompt to request `profession_mismatch` and `profession_reason` fields while maintaining backward compatibility.
2. Adjust `compute_match_score` to track the initial gating flag separately, defer the final mismatch outcome to Gemini when available, and surface both states in `breakdown_details`.
3. Update the match result template to reference the final mismatch outcome and optionally display the AI rationale when it flags a mismatch.
4. Retest the match flow to ensure final scores, banners, and suggestions align with the AI reviewer’s guidance.
5. Escape literal braces in the Gemini JSON response example so the prompt renders correctly during f-string interpolation.
6. Update the Gemini prompt to produce a richer `review` field that avoids mentioning BERT values and focuses on tailored improvement guidance, then surface that review in the results page.
7. Introduce a reusable helper that guarantees a `Profile` exists for the current user (creating one on the fly when missing) and adopt it across dashboard/profile/resume/match views.

### Progress
- Updated Gemini validation prompt to capture `profession_mismatch` and `profession_reason`, ensuring the reviewer’s stance is explicit.
- Refactored `compute_match_score` to preserve the initial gate, honor the AI override, and record both initial and final mismatch states plus rationale for template use.
- Adjusted the match result template to display the AI-provided profession reason only when a mismatch persists.
- Escaped literal braces in the Gemini prompt so f-string interpolation no longer raises a ValueError during match analysis.
- Enhanced the Gemini prompt to request a multi-sentence resume review and a separate quick tip, ensured the scoring service stores this review as the main guidance, and updated the result template to surface the review and tip without mentioning BERT.
- Implemented a Tailwind-styled admin dashboard template that surfaces platform KPIs, recent matches, quick admin actions, latest users, and system logs, powered by the existing `admin_panel` view context.
- Updated routing so the custom admin dashboard lives at `/admin-panel/`, preventing clashes with Django’s built-in `/admin/` namespace.
- Added an `ensure_profile` helper in views to auto-create a profile when absent, preventing `RelatedObjectDoesNotExist` errors for admin or freshly migrated accounts.
- Updated the login flow to authenticate with the email-based username field, preserve `next` redirects (e.g., `/admin-panel/`), and keep the entered email populated when credentials fail.
- Granted Django superusers access to the custom admin dashboard and settings even if their `role` field remains at the default `user` value.

## Task Notes (2025-11-03)

### Goals
- Build a functional admin dashboard screen so admins can monitor users, recent matches, and key system metrics with the modern Tailwind/Alpine styling the user expects.

### Observations
- `core/views.py` already exposes an `admin_panel` view that gathers users, recent matches, logs, and settings, but the template `core/templates/admin_panel/dashboard.html` is empty.
- Shared components (navigation, base styling) already exist via `base.html`, and other pages leverage Tailwind cards and gradients for visual consistency.
- Admin-specific actions (weight tuning, viewing logs) should be surfaced, at least as quick links, even if the underlying forms already exist elsewhere (`admin_settings`).

### Assumptions
- The admin panel should focus on read-heavy cards (counts, recent activity, settings snapshot) and quick navigation; full CRUD tables can remain minimal for now.
- Tailwind and Alpine are available globally via `base.html`, so the dashboard can use them without additional imports.
- Metrics can be derived from the context provided by `admin_panel` (user count, recent matches, system logs) without extra queries.

### Plan
1. Design a three-section layout: KPI overview cards, activity tables (recent matches/users), and system insights (logs/settings).
2. Implement the Tailwind-based template in `admin_panel/dashboard.html`, adding conditional handling for empty datasets.
3. Ensure links point to existing routes like `admin_settings` and provide placeholders where functionality is planned.
4. Verify the template renders without errors and update navigation breadcrumbs if needed.

## Summary of All Fixes Applied (2025-01-18)

1. **Resume View Template** (core/templates/resume/view.html)
   - Was completely blank (only had base extends)
   - Created comprehensive view with PDF preview iframe, LaTeX source display, action buttons, info sidebar
   - Added error handling for failed compilations and processing states
   - User can now: view generated resume, download PDF/LaTeX, regenerate, match with job

2. **Resume List Context** (core/views.py - generate_resume)
   - View wasn't passing `resumes` context to template
   - Added: `resumes = Resume.objects.filter(user=request.user).order_by('-created_at')`
   - Resume list at bottom of generate page now displays correctly

3. **Profile Data Persistence** (core/views.py - onboarding)
   - View was only saving 4 field groups (summary, skills, education_entries, experiences)
   - Now saves ALL 15+ field groups including contact info, projects, certifications, optional sections
   - Fixed field name mapping: education_entries→education, experiences→experience
   - Fixed data parsing for multi-line responsibilities and comma-separated technologies

**User Testing Checklist:**
1. ✓ Fill onboarding form with all data → Check if it appears in profile page
2. ✓ Generate resume → Should redirect to resume view showing PDF preview
3. ✓ Click "Resume" in nav → Should show generate page with list of all resumes at bottom
4. ✓ Download PDF and LaTeX from resume view page

## Implementation Complete

The Django ATS Resume Checker application is now fully implemented with:

1. **Backend Architecture**:
   - Django 5.0 framework
   - SQLite database with 7 models
   - Service layer for business logic
   - Proper separation of concerns

2. **AI/ML Integration**:
   - Google Gemini API (google-genai 1.47.0) for resume generation and validation
   - Sentence-BERT for semantic matching
   - spaCy for NLP parsing
   - Custom scoring algorithm with profession gating

3. **Frontend**:
   - Modern UI with Tailwind CSS
   - Interactive components with Alpine.js
   - Responsive design
   - Gradient-based color scheme
   - Font Awesome icons

4. **Features Implemented**:
   - User authentication (register/login/logout)
   - Multi-step onboarding
   - Profile management
   - AI-powered LaTeX resume generation
   - Resume-JD matching with detailed scores
   - Admin panel for configuration
   - System logging

5. **Security**:
   - Django authentication system
   - CSRF protection
   - Environment variables for secrets
   - Optional plaintext password storage (dev only)

## Next Steps for User

1. Install dependencies: `pip install -r requirements.txt`
2. Add Gemini API key to `.env` file
3. Start LaTeX service on port 8006
4. Create superuser: `python manage.py createsuperuser`
5. Run server: `python manage.py runserver`
6. Access at http://localhost:8000

## Notes

- LaTeX service in `latex-to-pdf/` directory is already available
- `template.tex` file exists for LaTeX resume template
- Sentence-BERT model auto-downloaded on first run
- All templates use Tailwind CSS CDN (no build required)
- Admin settings singleton ensures single configuration instance

## Recent Updates (Oct 31, 2025)

### Completed Template Implementations

1. **profile.html** - Complete profile view page
   - Tabbed interface (Basic Info, Education, Experience, Skills & Projects)
   - Profile completion progress bar
   - Display all profile data with proper formatting
   - Quick action cards for Generate Resume, Match Job, Dashboard
   - Edit links to onboarding page
   - Uses Alpine.js for tab switching

2. **resume/generate.html** - Complete resume generation page
   - 3-step wizard: Template → Customize → Generate
   - Template selection (Professional, Academic)
   - Customization options (summary, target role, section toggles)
   - Step indicator with progress visualization
   - Loading state during generation
   - List of previously generated resumes with download links
   - Profile completeness warning

3. **match/match.html** - Complete job matching page
   - Dual input methods: Paste text or Job URL
   - Job description textarea with helpful placeholder
   - Optional fields: job title, company name
   - "How It Works" section explaining the matching process
   - Recent match history with color-coded scores
   - Profile completeness warning
   - Loading state during analysis

### Template Features
- All use Tailwind CSS for styling
- Alpine.js for interactive components (tabs, toggles, step wizards)
- Consistent color scheme (purple/indigo gradients)
- Responsive design (mobile-friendly)
- Font Awesome icons throughout
- Smooth transitions and hover effects
- Form validation feedback
- Loading states for async operations

### Integration Points
- All templates extend base.html
- Use Django template tags ({% url %}, {% if %}, {% for %})
- CSRF token included in all forms
- Proper context variable usage (profile, user, resumes, matches)
- Links to other pages (dashboard, onboarding, etc.)

### Bug Fixes (Oct 31, 2025 - Second Update)

1. **Fixed URL naming issues**:
   - Changed `'profile_view'` to `'profile'` in resume/generate.html
   - Changed `'profile_view'` to `'profile'` in match/match.html
   - URL pattern is named 'profile', not 'profile_view'

2. **Comprehensive Onboarding Form Update**:
   - Updated to collect ALL fields from template.tex
   - Added Contact Information section (name, phone, city, state, linkedin, github)
   - Enhanced Education section with GPA field
   - Made Work Experience completely optional (starts with 0 entries)
   - Added Projects section (optional)
   - Added Publications section (optional)
   - Added Achievements & Awards section (optional)
   - Added Certifications section (optional)
   - Added Extracurricular & Leadership section (optional)
   - Enhanced Technical Skills with categorization:
     * Core Concepts (optional)
     * Programming Languages (required)
     * Frameworks & Libraries (optional)

   ### Match Flow Alignment (Nov 2, 2025)
   - Identified mismatch between `match_job` POST expectations (`resume_id`, `jd_title`, `jd_text`) and `match/match.html` form (`job_description`, missing resume picker), explaining why POST branch never executed.
   - Updated `match_job` view to log incoming POST keys, validate request payload, and provide user-facing error messages when required fields are absent; also pass `profile`, `recent_matches`, and `total_matches` context so template warnings/history render with real data.
   - Added resume selector, required job title input, and renamed job description textarea (`jd_text`) in `match/match.html`; ensured helpful guidance while keeping Tailwind/Alpine styling intact.
   - Clarified that URL scraping is not yet implemented by enforcing pasted JD text and logging provided URLs for future wiring.

   ### Match Submit UX Bug (Oct 31, 2025)
   - Reported behavior: clicking "Analyze" does not fire POST; server logs show only GETs.
   - Observed form uses Alpine `analyzing` flag set on button click; when HTML validation fails (e.g., missing required fields or hidden `jd_text`), the click handler still disables the button, leaving no way to resubmit.
   - Hidden `jd_text` remains `required` even when URL tab selected, causing silent validation failure and reinforcing the stuck state.
   - Plan: move `analyzing` toggle to form `@submit` handler (runs only on valid submits), remove button `@click`, and bind `required` attribute of `jd_text` to `inputMethod === 'paste'` so URL mode no longer fails client-side while backend still enforces presence.

   ### Match Result Rendering Gap (Oct 31, 2025)
   - After successful match POST (MatchAttempt id 1), `/match/<id>/result/` renders but page is blank; template currently empty aside from `{% extends 'base.html' %}`.
   - Need to construct result view template leveraging existing `match` context: headline score, profession match warning (since gating zeroed score), breakdown tables, Gemini suggestions (`match.suggestion_text`), and links to rerun or go back.
   - Ensure template gracefully handles missing optional data (e.g., `gemini_correction` may be null) and surfaces logging-friendly details for debugging.
   - Plan: build structured Tailwind layout with summary card, weighted breakdown (education/skills/experience), gap lists from `match.breakdown_details`, show `match.job_description.raw_text` toggle, and action buttons for retry/download.
   - Implemented `match/result.html` with full score breakdown, profession fit, Gemini reason, matched/missing skill lists, suggestion card, job description toggle, resume links, and navigation buttons. Layout uses Tailwind utilities consistent with existing design and handles missing data via template fallbacks.

   ### Gemini Validation Always Runs (Oct 31, 2025)
   - Original scoring logic short-circuited on profession mismatch, returning before contacting Gemini; UI message misleadingly claimed API unreachable and user couldn't verify the decision.
   - Refactored `compute_match_score` to always compute section similarities and invoke Gemini. When mismatch occurs we still zero the final score per gating rules but preserve Gemini's response (reason/suggestion) for display.
   - Added mismatch-specific messaging and ensured fallback suggestion remains helpful if Gemini fails. Logs now show `[GEMINI]` entries even for mismatched roles.

   ### Gemini Override for Mismatch (Oct 31, 2025)
   - After enabling Gemini calls on mismatches, final score still locked to 0 even when Gemini returned 70; user wants Gemini to influence score despite mismatch.
   - Plan: allow Gemini's `final_score` to override the mismatch zeroing while capping via `partial_credit_cap`, keep `profession_match_flag` false, and surface caution messaging in result template.
   - Update breakdown metadata to indicate when Gemini override occurred so UI can flag the caution note.
   - Implemented override so AI review score becomes final (clamped 0-100) even when profession gate triggers, while still flagging mismatch in breakdown. Simplified UI to remove Gemini branding and caution copy—final score card now shows the AI-adjusted score directly, and recommendation section focuses on improvement steps only.
     * Tools & Platforms (optional)
   
3. **Form Features**:
   - All optional sections start with 0 entries
   - Users can add as many entries as needed
   - Remove buttons for all entries (except education which requires at least 1)
   - Clear labels indicating required (*) vs optional fields
   - Helpful placeholders showing expected format
   - Empty state messages when no entries added
   - Color-coded "Add" buttons for different sections
   - Responsive grid layouts
   - Better visual hierarchy with icons
   
4. **Data Collection Alignment with template.tex**:
   - Header: Name, City/State, Phone, Email, LinkedIn, GitHub ✓
   - Summary: Professional summary (optional, AI can generate) ✓
   - Experience: Company, Title, Dates, Responsibilities ✓
   - Technical Skills: Core Concepts, Programming, Frameworks, Tools ✓
   - Education: Degree, Major, Institution, Years, CGPA ✓
   - Publications: Title, Venue, Date, Description, DOI ✓
   - Achievements/Awards: Name, Organization, Level ✓
   - Extracurricular/Leadership: Role, Organization, Location, Description ✓
   - Projects: Implicit in original onboarding, now explicit ✓
   - Certifications: Name, Issuer, Year ✓

### User Feedback Implementation (Oct 31, 2025 - Third Update)

1. **Skills Section Simplified**:
   - Changed from categorized technical skills to single generic "Skills" field
   - Removed: Core Concepts, Programming Languages, Frameworks, Tools sections
   - Now: Single textarea for all skills (technical, soft skills, languages, etc.)
   - More inclusive for non-programmers (designers, managers, etc.)
   - Helpful placeholder examples for different professions

2. **Pre-fill Existing Data**:
   - All form fields now show existing profile data when editing
   - Contact Information: Pre-filled with user.get_full_name, profile.phone, city, state, linkedin, github
   - Professional Summary: Pre-filled with profile.summary
   - Skills: Pre-filled with profile.skills (comma-separated)
   - Education: Shows existing education entries, can add more
   - Experience: Shows existing work experience, can add more
   - Projects: Shows existing projects, can add more
   - Certifications: Shows existing certifications, can add more
   
3. **Dynamic Form Behavior**:
   - Existing entries are rendered from database
   - Alpine.js counters initialize with existing data count
   - "Add More" buttons create additional blank entries
   - Remove buttons work for all entries (except education must have 1+)
   - New entries get sequential numbering based on existing count
   - Form submission preserves both existing and new entries

4. **Implementation Details**:
   - Used Django template loops for existing data ({% for %})
   - Used Alpine.js templates for new dynamic entries
   - Counter arithmetic: `(newCount - existingCount)` for template x-for
   - Index calculation: `(i - 1 + existingCount)` for field names
   - Empty state handling: Shows blank form if no existing data
