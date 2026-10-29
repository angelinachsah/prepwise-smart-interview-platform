# Software Requirements Specification

**Project:** Prepwise — Smart Interview Preparation Platform  
**Version:** 1.0  
**Date:** 2026-10-29  
**Status:** Implementation baseline for an academic microproject

## 1. Introduction

### 1.1 Purpose
This specification defines testable requirements for a local web platform that consolidates interview preparation activities and tracks student progress.

### 1.2 Scope
Prepwise provides student and administrator accounts; a categorized question bank; timed mock assessments; safe sample-based coding practice; HR answer drafting; progress summaries; rule-based recommendations; and administrator content creation and result viewing.

### 1.3 Objectives
1. Provide a single usable preparation workspace.
2. Record practice and test outcomes in SQLite.
3. Give students feedback tied to their stored activity.
4. Allow authorized admins to maintain shared question and test content.

### 1.4 Intended audience
Students, project evaluators, instructors, and developers maintaining a small Flask demonstration.

### 1.5 Definitions
- **Attempt:** One student's run of a configured mock test.
- **Sample check:** A comparison between a student's manually entered observed output and the displayed sample output. It does not execute or verify submitted code.
- **Recommendation:** A stored suggestion generated from measured activity using fixed score bands.
- **RBAC:** Role-based access control.

## 2. Overall product description

### 2.1 Product perspective
The application is a standalone Flask server-rendered web app. SQLite persists user, content, practice, attempt, and recommendation records. Chart.js renders client-side charts from server-computed data.

### 2.2 User classes
- **Student:** Creates an account, practices questions and assessments, saves HR drafts, and views own progress/results.
- **Admin:** Creates questions and tests and views platform student accounts and submitted test summaries.

### 2.3 Operating environment
Python 3.12+, a modern browser, Flask development server, SQLite, and internet access for CDN-hosted Chart.js/fonts. The app is designed for local Windows, Linux, and macOS demonstrations.

### 2.4 Assumptions and dependencies
The operator installs packages from `requirements.txt`, sets a private secret, and configures a first admin through environment variables or the documented local-only demo seed. Users have JavaScript enabled for charts, test navigation, countdown display, and HR single-question navigation; server forms remain present without those enhancements.

### 2.5 Constraints
- No unrestricted execution of submitted code.
- No external AI API or machine-learning claims.
- SQLite is a demonstration database; migrations and multi-worker deployment are not part of this version.
- The timer uses server start timestamps; a browser refresh preserves the server-side attempt but not unsubmitted browser selections.

## 3. Functional requirements

| ID | Requirement | Acceptance evidence |
|---|---|---|
| FR-001 | The system shall register a student with a unique, valid email and confirmed password. | Registration tests and duplicate-email rejection. |
| FR-002 | The system shall enforce an 8–128 character password containing uppercase, lowercase, and a digit and store only a password hash. | Registration and password-change tests; hash verification. |
| FR-003 | The system shall authenticate users and support logout. | Login/logout tests and protected dashboard redirect. |
| FR-004 | The system shall enforce student/admin authorization on server routes. | Student receives 403 for admin route; admin can load it. |
| FR-005 | The system shall let a student update name, preferred role, and education. | Profile update test. |
| FR-006 | The system shall let students change a password after verifying the current password. | Password-change test. |
| FR-007 | The system shall list questions with keyword, category, difficulty filters, and pagination. | Question route and filter test. |
| FR-008 | The system shall display question details, explanations, practice recording, and bookmarks. | Detail and bookmark test. |
| FR-009 | The system shall allow a student to start a published test with server-recorded start time. | Test-start flow. |
| FR-010 | The system shall omit answer keys from the taking-test response and calculate scores on the server. | Response inspection and scoring test. |
| FR-011 | The system shall validate test answer IDs/options, prevent repeated submission, and restrict result access to the owner or admin. | Invalid-ID, result access, and submission-state tests. |
| FR-012 | The system shall automatically submit an in-progress attempt after its configured duration. | Server deadline behavior; browser countdown mirrors remaining time. |
| FR-013 | The system shall provide coding problem statements, sample cases, hints, and safe sample-output comparison without executing code. | Coding route and sample-check test. |
| FR-014 | The system shall save a student's HR draft and practice flag. | HR persistence test. |
| FR-015 | The system shall show database-backed question, test, coding, and HR activity. | Dashboard/progress queries and empty states. |
| FR-016 | The system shall generate recommendations from measured category scores and avoid inventing scores for new users. | Recommendation rules and onboarding state. |
| FR-017 | The system shall allow an admin to create, edit, and conditionally delete interview questions. | Admin question routes; historical/test-linked content is locked. |
| FR-018 | The system shall allow an admin to create and configure tests from category-consistent MCQs and a valid duration. | Admin test creation and configuration routes. |
| FR-019 | The system shall allow admins to view student accounts/results and enable or disable student accounts. | Admin dashboard and account-toggle route. |
| FR-020 | The system shall persist data in SQLite across server restarts. | Database file and ORM persistence; local manual case TC-038. |
| FR-021 | The system shall provide keyboard-usable forms, labels, responsive layouts, and reduced-motion behavior. | HTML labels, responsive CSS, `prefers-reduced-motion` rule. |
| FR-022 | The system shall protect state-changing forms with CSRF validation. | Flask-WTF global CSRF configuration. |
| FR-023 | The system shall allow admins to add, rename, and conditionally remove categories. | Admin category routes; categories used by content cannot be deleted. |
| FR-024 | The system shall allow admins to add and conditionally remove coding and HR content. | Admin creation/deletion routes; content with submissions/drafts is protected. |

## 4. Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-001 Security | Passwords are hashed; secrets are environment-configured; inputs are validated server-side; ORM queries are used. |
| NFR-002 Security | CSRF is enabled; cookies are HttpOnly and SameSite=Lax; secure cookies can be enabled for HTTPS. |
| NFR-003 Security | Correct answers are withheld during tests; scoring is server-side; result ownership is checked. |
| NFR-004 Safety | The server never executes submitted code; sample comparison is clearly labelled and not represented as full acceptance. |
| NFR-005 Performance | Ordinary local requests should complete within two seconds for a small demo database, excluding package installation and browser CDN loading. |
| NFR-006 Usability | Navigation, forms, feedback, and empty states use consistent terms and responsive presentation. |
| NFR-007 Accessibility | Inputs have labels; controls have accessible names; semantic sections are used; reduced-motion preferences are respected. |
| NFR-008 Reliability | Missing records return a not-found page; invalid roles and identifiers do not expose private content. |
| NFR-009 Maintainability | Routes, models, templates, assets, tests, and documentation are separated into dedicated files/directories. |

## 5. External interface requirements

### 5.1 User interface
The browser UI uses a responsive SaaS-style dashboard, a desktop sidebar, a mobile navigation toggle, semantic forms, charts, status badges, confirmation dialogs, and toast messages.

### 5.2 Software interfaces
Flask handles HTTP and sessions; SQLAlchemy maps application models to SQLite; Flask-Login handles sessions; Flask-WTF supplies CSRF protection; Chart.js renders analytics.

### 5.3 Communication interfaces
The local development server uses HTTP on `127.0.0.1:5000`. HTTPS is expected to be terminated by an external deployment layer before setting secure cookies.

## 6. Data requirements

| Entity | Important fields and relationships |
|---|---|
| User | Name, unique email, password hash, role, role/education preferences, status, creation time. Owns attempts, bookmarks, practice, activity, and recommendations. |
| Category | Unique name and description; groups questions/tests. |
| Question | Category, text, type, difficulty, optional MCQ options/key, explanation, tags. |
| Bookmark | User/question pair; unique constraint prevents duplicates. |
| QuestionAttempt | User/question, optional correctness for discussion prompts, timestamp. |
| MockTest | Title, description, category, duration, pass percentage, published flag. |
| TestQuestion | Test/question/marks association; unique test/question pair. |
| TestAttempt | User/test, start/submission timestamps, score, percentage, state, elapsed time. |
| AttemptAnswer | Attempt/question, selected option, correctness, awarded marks; unique attempt/question pair. |
| CodingProblem | Prompt, formats, samples, constraints, hints, explanation, stored case data. |
| CodingSubmission | User/problem, code, sample-check state, counts, timestamp. |
| HRQuestion | Prompt, example structure, tips, category. |
| HRPractice | User/question pair, draft, practice flag, update timestamp. |
| Recommendation | User/category, title, explanation, priority, action, completion, timestamp. |
| ActivityLog | User, activity type, optional reference/score, timestamp. |

## 7. Use cases

### UC-01 Register and practice
**Actor:** Student. **Precondition:** No account for the email. **Flow:** Student submits account details; server validates and hashes password; session is created; dashboard is shown. Student selects a question and records an answer. **Postcondition:** Account and practice record persist.

### UC-02 Take mock test
**Actor:** Student. **Precondition:** Authenticated; published test has MCQs. **Flow:** Server creates an in-progress attempt; browser receives question text/options without answer key and displays remaining time; student submits; server validates IDs and options, calculates score, stores answers and result, refreshes recommendations, and displays private review. **Postcondition:** Attempt is submitted once and result is persisted.

### UC-03 Practice coding sample
**Actor:** Student. **Flow:** Student reads problem, enters code and observed output; server compares only the entered output to the sample output and stores status. **Postcondition:** Sample match/mismatch is recorded with explicit limitation notice; code is not executed.

### UC-04 Manage question and test content
**Actor:** Admin. **Precondition:** Authenticated admin. **Flow:** Admin enters a question or test; server checks category, difficulty, options, duration, and test-question category; valid content persists. **Postcondition:** Student content pages can retrieve the new item.

## 8. Business rules
1. Only active accounts authenticate.
2. Only admins use `/admin` content-management routes.
3. Test result access is limited to the attempt owner or an admin.
4. Test scores are marks-awarded divided by configured total marks; unanswered questions receive zero.
5. Test score thresholds are High (<50%), Medium (50–69%), Low (70–84%), and maintain proficiency (≥85%).
6. Recommendation generation uses available saved activity; new users see onboarding suggestions instead of fabricated scores.
7. Coding sample match is not a claim that code passed hidden or full test cases.

## 9. Traceability

| Requirement | Primary implementation | Primary test/document |
|---|---|---|
| FR-001–006 | `app.py` auth/profile routes, `models.py` User | `tests/test_app.py`, TC-001–008 |
| FR-007–008 | `app.py` question routes | `tests/test_app.py`, TC-009–013 |
| FR-009–012 | test routes and attempt models | `tests/test_app.py`, TC-014–022 |
| FR-013 | coding route and CodingSubmission | `tests/test_app.py`, TC-023–025 |
| FR-014 | HR route and HRPractice | `tests/test_app.py`, TC-026 |
| FR-015–016 | dashboard/progress/recommendation logic | `tests/test_app.py`, TC-027–030 |
| FR-017–019 | admin routes/dashboard | `tests/test_app.py`, TC-031–037 |
| FR-020 | SQLAlchemy SQLite persistence | TC-038 |
| FR-021–022 | templates, assets, global CSRF | manual inspection and TC-039–042 |
| FR-023–024 | admin category/content routes | admin feature tests/manual verification |

## 10. UML diagram guide

The PlantUML sources in `docs/diagrams/` describe the implemented role and data relationships:

- **Use case:** separates student preparation tasks from administrator content and account-management actions.
- **Class:** documents the SQLAlchemy entities, their links, and the sample-only coding limitation.
- **Sequence:** traces an owner-authenticated test attempt from start through server-side scoring, persistence, and result review.
- **Activity:** shows the preparation choices, test timeout branch, activity update, and recommendations/onboarding decision.
- **State machine:** records valid attempt states and the server deadline/submission/evaluation transitions.

## 11. Acceptance criteria
- Automated tests pass using the documented pytest command.
- Seed initializes ten categories, at least 60 distinct interview questions, five tests, 15 coding problems, and 20 HR prompts.
- Registration/login, role checks, bookmarks, test grading/results, coding sample checks, HR drafts, analytics, and admin content creation work against SQLite.
- Correct test answers are not present in the taking-test response.
- Submitted code is never executed.
- Five PlantUML source diagrams and this SRS are included.

## 12. Risks and limitations
- This is a local educational demo, not a production-ready public service.
- Browser choices are not persisted until test submission; a refresh retains server timer state but can lose unsent answers.
- SQLite schema changes require a reset in this version; Alembic migrations are not configured.
- The client-side chart and fonts use CDN resources.
- Recommendation scores are simple rules and do not account for statistical confidence or recency weighting.
- Coding and HR content can be added and conditionally deleted; dedicated edit forms for those two content types are not included. Questions/tests with attempt history are protected from destructive edits.

## 13. References
- Flask documentation: https://flask.palletsprojects.com/
- Flask-SQLAlchemy documentation: https://flask-sqlalchemy.palletsprojects.com/
- Flask-Login documentation: https://flask-login.readthedocs.io/
- OWASP CSRF Prevention Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html
