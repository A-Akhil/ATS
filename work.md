# High-level summary of the project

You will build a Django web application (SQLite for storage) that allows users to register, create a profile, generate a single-template ATS-friendly LaTeX resume (via Gemini), upload or reuse that resume to apply to any job description (JD) users paste, and receive an ATS-style match score computed locally using Sentence-BERT. Gemini will be used as a validator and to produce LaTeX resume output and natural-language improvement suggestions. The admin panel shows all users and logs, and can tune scoring weights (default: 35% education, 45% skills, 20% experience).

---

# Architecture & components (conceptual)

1. **Frontend (Django templates / simple SPA inside Django)**

   * Pages: Landing, Register, Login, User Dashboard (Profile & Resume Builder), Resume Preview (LaTeX rendered to PDF for download), Job Match page (paste JD / upload JD), Results page (score + breakdown + improvements), Admin Dashboard.

2. **Backend (Django)**

   * Django app handles authentication, profile CRUD, file storage (resumes uploaded), job descriptions, match requests, admin endpoints, and orchestrates calls to the NLP service(s) and Gemini API.

3. **NLP/Scoring Module (local Python service within Django project)**

   * Uses Sentence-BERT (or any sentence embedding model appropriate for CPU) to compute embeddings for resume sections and job description sections.
   * Implements rule-based parsers for education, skill extraction, and experience (regex + heuristics + spaCy).
   * Implements the composite scoring function and tuning via admin weights.
   * Stores the match breakdown and raw scoring artifacts for admin logging.

4. **Gemini API usage (external)**

   * Two main responsibilities:

     * Produce the LaTeX resume output, given a standard template and the user profile.
     * Validate and/or adjust BERT scores and produce human-language improvement suggestions.
   * Django will call Gemini via REST API (server-side), parse structured JSON responses.

5. **Database (SQLite)**

   * Stores users, profiles, resumes, job descriptions, matches, logs, and admin settings (weights). SQLite is fine for an academic project.


---

# Data model (entities & fields — conceptual)

Define these main entities. (No SQL code — design only.)

1. **User**

   * id
   * email
   * password_hash (and *you asked raw password* — see security note below)
   * full_name
   * phone (optional)
   * role (user / admin)
   * created_at
   * last_login

2. **Profile** (one-to-one with User)

   * user_id
   * summary / bio
   * education_entries: list of {degree, field, institution, start_year, end_year}
   * skills: list (free-text tokens)
   * experiences: list of {title, company, start, end, description, tech_stack}
   * certifications (optional)
   * projects (optional)
   * parsed_searchable_text (concatenated normalized text for matching)

3. **Resume** (generated or uploaded)

   * id
   * user_id
   * filename (if uploaded)
   * source_type: uploaded | generated
   * latex_source (if generated)
   * pdf_blob or file_path
   * parsed_text (raw extracted text)
   * parsed_sections (json: education, skills, experience)
   * created_at

4. **JobDescription**

   * id
   * user_id (who created/pasted the JD)
   * title
   * raw_text
   * parsed_sections (json)
   * requirements (deduced list)
   * created_at

5. **MatchAttempt**

   * id
   * user_id
   * resume_id
   * job_description_id
   * bert_scores: {education: float, skills: float, experience: float, final: float}
   * gemini_correction: optional {education, skills, experience, final, reason}
   * final_score (after optional Gemini correction)
   * breakdown_details: which skills matched, which keywords missing, experience gaps
   * suggestion_text (Gemini’s improvement sentence)
   * profession_match_flag (bool)
   * created_at

6. **AdminSettings**

   * id (singleton)
   * weight_education (default 0.35)
   * weight_skills (default 0.45)
   * weight_experience (default 0.20)
   * profession_similarity_thresholds: {cap_threshold, zero_threshold, partial_credit_score}
   * allowed_degree_equivalences (mapping if any)

7. **SystemLog**

   * id
   * user_id (action by)
   * action_type (login, generate_resume, match, admin_update, etc.)
   * raw_data (json snapshot)
   * created_at

---

# Authentication & account setup flow

1. **Registration**

   * New user signs up with email and password. After confirming password:

     * If they are a brand-new account, the system asks for “full details” needed to auto-generate a profile: full name, highest degree, major/field, institution, graduation year, list of skills (comma-separated), list of experiences (title, company, duration, short description).
     * The frontend should present an on-boarding multi-step form for these fields.

2. **Password handling (security note)**

   * You requested storing raw and hashed passwords for admin display. This is insecure. For academic demonstration, you may store hashed passwords and an optional dev-only plaintext field that is clearly flagged and protected (only for local demo). Ideally:

     * Store only password hashes in production-like setups.
     * If you must show raw text for the assignment, do it only in a dev environment with a clear comment and secure the admin page behind authentication and possibly restricted to the local machine. I will include a caution in your documentation.

3. **Auto-profile creation**

   * After onboarding, create the Profile record and generate parsed_searchable_text by concatenating normalized fields so matching is easier.

---

# Resume generation (LaTeX via Gemini) flow

1. **Template management**

   * Define a single LaTeX template with placeholders for: name, contact, education list, skills list, experiences, projects, certifications, and a short summary.
   * Store the template in the project (as a text resource) and expose it so Gemini can fill placeholders.

2. **Trigger generation**

   * When user chooses “Generate Resume”, send the user profile (structured JSON) + template to Gemini with a prompt instructing Gemini to produce LaTeX that:

     * Fills the template placeholders using the user’s data.
     * Produces ATS-friendly structure (clean headings, bullet lists, no fancy visuals that break text-parsing).
     * Returns only the LaTeX source in a structured JSON field.

3. **Post-processing**

   * Save the returned LaTeX source in the Resume record.
   * Optionally compile the LaTeX to PDF (use a command-line latex engine if available). Using "curl -F "file=@main.tex" http://localhost:8006/convert --output output.pdf"

   * Provide a download button that returns the PDF (if compiled).
   * also return the error of gemini if any found in latex with the latex code.

4. **UX**

   * Preview the LaTeX source on a page and show a download icon. Also allow regenerating if user edits profile fields.

---

# Resume / JD parsing and section extraction (BERT prep)

1. **Normalization**

   * Lowercasing, removing punctuation where necessary, expanding common abbreviations (e.g., “B.Tech” → “Bachelor of Technology”), and consistent tokenization.
   * Normalize skill names (e.g., "tf" -> "tensorflow") via a small alias map.

2. **Education extraction heuristics**

   * Look for lines containing known degree keywords (bachelor, master, B.Tech, M.Sc, MBBS, MD, B.Com, etc.), years, and institution names.
   * Determine degree level (bachelor, master, doctoral, diploma) and the field/major.

3. **Skill extraction**

   * From profile: split the provided skill list and normalize.
   * From resume text: extract candidate n-grams, detect known tech keywords, and merge with profile skills.

4. **Experience extraction**

   * Extract job titles, companies, durations, and text describing responsibilities.
   * Extract technologies/tools from experience descriptions.

5. **Profession detection**

   * Using embeddings or basic keyword taxonomy:

     * Build a small taxonomy of profession domains (software, data, healthcare, finance, legal, academia, etc.)
     * For a text (resume or JD), compute similarity between a domain’s representative keywords and the text; choose highest-scoring domain and a similarity score between 0 and 1.

---

# BERT-based scoring logic (detailed, but no code)

1. **Model selection**

   * Use a Sentence-BERT variant that's efficient on CPU (for example, a small or distilled model). The model should produce sentence or short-paragraph embeddings for:

     * Education strings
     * Skill tokens
     * Experience descriptions
     * Job requirement sentences

2. **Create canonical vectors**

   * For resume: create three canonical vectors

     * Education vector (embedding of concatenated education text)
     * Skills vector (embedding of concatenated skills)
     * Experience vector (embedding of concatenated experience text)
   * For job: create the corresponding vectors (requirements parsed to education requirement, skills required baseline, experience requirements)

3. **Compute similarities**

   * Compute cosine similarity between resume and job vectors for each of the three domains:

     * education_sim ∈ [0,1]
     * skills_sim ∈ [0,1]
     * experience_sim ∈ [0,1]

4. **Apply gating & partial credit rules**

   * Profession similarity (domain match) is computed first. If profession_similarity < zero_threshold (e.g., 0.2), set final_score = 0 and tag profession_mismatch.
   * If profession_similarity between zero_threshold and cap_threshold (e.g., 0.2–0.4), cap the final score to a partial-credit maximum (e.g., 30) to reflect transferable skills.
   * Education handling:

     * If job explicitly requires a specific degree or field and the education_sim is below a threshold, map education_sim to a lower weight or 0 depending on strictness. Use admin-configurable rules for strict degrees (MBBS, MD, law degrees, etc. — strictly required).
     * If degree is related (match via simple taxonomy or embedding similarity), give partial credit (e.g., scale education_sim by 0.4 to 0.8).

5. **Combine with admin weights**

   * Use the admin-configurable formula:

     * final_score_raw = weight_education * education_sim + weight_skills * skills_sim + weight_experience * experience_sim
     * Multiply by 100 → preliminary final_score_percent
   * Apply profession caps/zeroing rules described above.

6. **Record intermediate values**

   * Save per-skill match results, missing keywords, and exact similarity numbers in MatchAttempt for admin review and Gemini validation.

---

# Gemini validation & improvement suggestions

1. **When to call Gemini**

   * Call Gemini after BERT produces the preliminary score and breakdown.
   * Use Gemini for two related tasks:

     * Validate or correct the numeric scores (optional; you can accept or override BERT).
     * Produce concise improvement suggestions and explain reasoning in plain English.

2. **What to send to Gemini (prompt)**

   * Send structured JSON-like instructions:

     * Resume parsed sections (education text, skills list, experience summary)
     * Job parsed sections (required education text, required skills list, experience requirements)
     * BERT’s numeric scores and profession_similarity
     * Ask Gemini to either confirm, correct (with numbers between 0–1), or explain with a short paragraph. Also request a short one-sentence improvement and a LaTeX snippet if needed.
   * Ask for a strict JSON-only response in the format you expect (education_score, skills_score, experience_score, final_score, reason, suggestion).

3. **Use Gemini’s LaTeX output for resume generation**

   * Provide the user profile and the template—ask Gemini to fill the LaTeX template and return LaTeX code only.
   * Save LaTeX; optionally compile to PDF.

4. **Decision on final score**

   * Policy options:

     * Always accept Gemini-corrected final_score.
     * Or accept BERT’s final_score unless Gemini’s correction differs by more than a threshold (e.g., 10%), in which case override or log for manual review.
   * For your academic project choose a simple rule: accept Gemini’s correction when provided; store both the BERT and Gemini scores in MatchAttempt.

---

# Admin panel functionality (detailed)

1. **User management**

   * List all users, searchable by email or name.
   * Show profile details and resume(s). Show hashed password and (if you insist) plaintext dev password only when in dev mode with a big warning. Provide a toggle to show/hide plaintext (default hidden).

2. **Match logs**

   * Show MatchAttempt records with full payloads:

     * BERT scores, Gemini corrections, matched keywords, missing skills, profession similarity, timestamps, and the full JD text.
   * Allow export of match history as CSV.

3. **Audit & raw logs**

   * Store raw Gemini responses and BERT inputs/outputs for reproducibility and grading.
   * Admin can delete or export logs.

---

# UI/UX flow (user-facing)

1. **On first login**

   * Show onboarding form requesting essential profile details. Save to Profile.
   * Offer a button “Generate ATS Resume (LaTeX)” which calls Gemini and returns the LaTeX file for download. Display download icon.

2. **Profile & Resume**

   * User can edit profile fields and regenerate the resume.
   * Show preview and a “Regenerate LaTeX” button.

3. **Applying a job / Matching**

   * User can either:

     * Upload a resume file (PDF) or
     * Use existing generated profile-resume (recommended).
   * User pastes the JD or uploads the JD file.
   * User clicks “Check Match”.
   * System runs parsing → BERT scoring → Gemini validation → shows results.

4. **Results page**

   * Show:

     * Final ATS score (percentage)
     * Breakdown: education %, skills %, experience %
     * Profession match flag (if mismatch, show “Not a match: profession mismatch”)
     * List of matched skills and missing skills
     * One-line improvement suggestion from Gemini
     * Option to “Regenerate resume with changes” — link to profile editing.

---

# Admin UX

* Admin login goes to Admin Dashboard.
* Tabs: Users, Matches, Settings, Logs.
* Under Settings, provide sliders to change weights and thresholds and a “Recompute selected matches” button to re-run BERT scoring with new weights.

---

# Logging & storage policies (practical)

1. **Store raw_text snapshots**

   * For each uploaded resume and JD, store the raw text (for reproducibility and grading).
2. **Store parsed outputs**

   * Save parsed sections and embeddings (optionally hashed or truncated).
3. **Store Gemini responses**

   * Save the JSON returned by Gemini verbatim for audit.
4. **Retention**

   * For an academic project, keep everything; but document retention policy and caution about PII.

---


# Deployment & development environment

1. **Local development**

   * Install Django and necessary Python libraries (spaCy, sentence-transformers, requests or a Google client for Gemini).
   * Store Gemini API key in environment variables, not hard-coded. For academic demo, place a local .env file but keep it out of source control.

2. **Packaging**

   * Provide a README with instructions for:

     * Installing Python dependencies
     * Downloading the sentence-transformers model
     * Setting environment variables (API key)
     * Starting Django dev server
   * Provide a script for seeding the SQLite DB with one admin user and a couple of sample users for grading.

---

# UX edge cases & behavior rules (clear rules to implement)

1. **Profession completely different (e.g., MBBS vs Software)**

   * If profession_similarity < zero_threshold:

     * final_score = 0
     * Show clear message: “Profession mismatch — this resume is not for the given JD.” Include reason and the profession labels detected.

2. **Related profession (transferable skills)**

   * If zero_threshold ≤ profession_similarity < cap_threshold:

     * Compute final_score but cap at partial_credit_score (e.g., 30).
     * Show explanation: “Partial match due to transferable skills; consider highlighting X.”

3. **Education strictness**

   * If job explicitly requires a strict degree (admin-configured), and education does not match, reduce education_sim to 0 (or to a small value) depending on policy.

4. **Missing experience years**

   * If JD asks for X years and candidate has Y < X, compute experience_sim as Y/X capped at 1. Penalize modestly and show the gap.

5. **Skill exact vs semantic match**

   * Exact text match boosts score strongly; semantic embedding match gives partial credit. Show which skills were matched exactly vs semantically.

---

# Admin & grading requirements for academic submission

* Prepare a demo admin account.
* Provide seeded sample data for automated evaluation: several resumes and job descriptions (including examples with profession mismatches, partial matches, and full matches).
---

# Security & ethical cautions (important)

* **Passwords**: Storing raw plaintext passwords is insecure and unacceptable for real deployment. For an academic demo, if you must show plaintext for grading, restrict the system to a local environment and clearly label the danger in documentation. Prefer storing only secure hashed passwords.
* **PII**: Resumes contain personal data. Secure the admin dashboard and avoid exposing personally identifiable information without consent.
* **Gemini API Key**: Keep the key in environment variables and do not commit it. For assignments, you can provide a placeholder.
* **Model outputs**: LLMs can hallucinate. When using Gemini for corrections/suggestions, log and display the source of claims and avoid accepting suggestions blindly in critical contexts.

---

# Practical prompts to use with Gemini (text-only examples)

Use these templates when calling Gemini from Django. Obtain structured JSON responses from Gemini by instructing it explicitly.

1. **LaTeX Resume generation prompt (supply template & profile JSON)**

   * Ask Gemini: “Fill this LaTeX template using this user profile. Ensure output is a complete LaTeX document and nothing else; respond in JSON: { "latex": "<LaTeX source>" }.”

2. **Score validation & suggestion prompt (supply parsed sections + BERT scores)**

   * Ask Gemini: “Validate the numeric scores below that a BERT-based system generated for this resume vs job. Return JSON: {education_score, skills_score, experience_score, final_score, reason, suggestion} where scores are floats 0–1, final_score is your recommended final. Also return a one-line improvement suggestion.”

3. **Profession detection prompt (optional)**

   * Ask Gemini: “Given this text, determine the most likely profession domain (one of: Software, Data, Healthcare, Finance, Legal, Education, Other) and a confidence 0–1. Return JSON.”

---