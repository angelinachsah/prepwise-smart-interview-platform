# Software Test Case Catalog

**Project:** Prepwise — Smart Interview Preparation Platform  
**Version:** 1.0  
**Execution status:** Initial manual cases are Pending. Automated tests are run separately and report genuine observed outcomes.

Status values below are deliberately `Pending` until a corresponding manual test is executed. “Actual result” must be updated only with observed evidence.

| ID | Requirement | Objective | Preconditions | Steps | Input / test data | Expected result | Actual result | Status | Remarks |
|---|---|---|---|---|---|---|---|---|---|
| TC-001 | FR-001 | Register a valid student | Seeded app; unused email | Open Register; submit form | Valid name, unused email, strong matching password | Account created and dashboard opens | `test_registration_password_rules_and_duplicate_email` passed | Pass | Automated |
| TC-002 | FR-001 | Reject duplicate email | Existing student | Register with same email | `student@test.local` | Duplicate-account message; no second account | `test_registration_password_rules_and_duplicate_email` passed | Pass | Automated |
| TC-003 | FR-001 | Reject malformed email | App running | Register | `not-an-email` | Validation error; no account | Not Executed | Pending | Negative |
| TC-004 | FR-002 | Reject weak password | App running | Register | `abc123` | Password policy error | `test_registration_password_rules_and_duplicate_email` passed | Pass | Automated |
| TC-005 | FR-001 | Reject password mismatch | App running | Register | Two different strong values | Mismatch message; no account | `test_registration_password_rules_and_duplicate_email` passed | Pass | Automated |
| TC-006 | FR-001 | Require name and email | App running | Submit empty registration form | Empty required fields | Validation prevents account creation | Not Executed | Pending | Boundary |
| TC-007 | FR-003 | Login with valid credentials | Seeded student | Submit login form | Correct email/password | Dashboard loads | `test_login_logout_and_protected_dashboard` passed | Pass | Automated |
| TC-008 | FR-003 | Reject incorrect credentials | Seeded student | Submit login form | Correct email, incorrect password | Generic credential error | `test_login_logout_and_protected_dashboard` passed | Pass | Automated |
| TC-009 | FR-003 | Protect dashboard | Signed-out browser | Navigate to dashboard | No session | Redirect to login | `test_login_logout_and_protected_dashboard` passed | Pass | Automated |
| TC-010 | FR-004 | Deny student access to admin | Student session | Open `/admin` | Student role | HTTP 403 | `test_student_is_denied_admin_and_admin_can_open_dashboard` passed | Pass | Automated |
| TC-011 | FR-004 | Allow admin access | Admin session | Open `/admin` | Admin role | Admin workspace loads | `test_student_is_denied_admin_and_admin_can_open_dashboard` passed | Pass | Automated |
| TC-012 | FR-007 | Browse questions | Student session; seeded content | Open question list | No filter | Questions and categories display | `test_question_search_detail_and_bookmark` passed | Pass | Automated |
| TC-013 | FR-007 | Search/filter questions | Student session | Search, choose category/difficulty | Known term and category | Matching results only | Not Executed | Pending | Functional |
| TC-014 | FR-008 | Bookmark question | Student session | Open question; save bookmark | Existing question ID | Bookmark saved and shown | `test_question_search_detail_and_bookmark` passed | Pass | Automated |
| TC-015 | FR-008 | Reject unknown question | Student session | Open absent question ID | Very large ID | Not-found page | Not Executed | Pending | Negative |
| TC-016 | FR-009 | Start a published test | Student session; test has questions | Start test | Published test | Attempt starts and timer appears | `test_mock_test_scores_on_server_and_persists_result` passed | Pass | Automated |
| TC-017 | FR-010 | Hide correct answers in test | Student session; active attempt | Inspect taking-test response | Test with MCQs | Correct option is not sent to browser | `test_mock_test_scores_on_server_and_persists_result` passed | Pass | Automated |
| TC-018 | FR-010 | Score all-correct attempt | Active attempt | Submit every correct choice | All answer keys | Full marks and 100% | Not Executed | Pending | Boundary |
| TC-019 | FR-010 | Score zero-correct attempt | Active attempt | Submit incorrect choices | Valid options, all incorrect | Zero score and 0% | Not Executed | Pending | Boundary |
| TC-020 | FR-010 | Score unanswered attempt | Active attempt | Submit without choices | Empty answer fields | Zero marks; all items unanswered | Not Executed | Pending | Boundary |
| TC-021 | FR-011 | Reject invalid question ID | Active attempt | Submit unknown question field | `q_999999=A` | HTTP 400; result not altered | `test_test_submission_rejects_unknown_question_id` passed | Pass | Automated |
| TC-022 | FR-011 | Reject invalid answer choice | Active attempt | Submit malformed choice | `q_id=Z` | HTTP 400 | Not Executed | Pending | Negative |
| TC-023 | FR-011 | Protect another student's result | Attempt belongs to other user | Sign in as different student; open result | Foreign attempt ID | HTTP 404; no result details disclosed | `test_test_result_is_private` passed | Pass | Automated |
| TC-024 | FR-012 | Auto-submit at timer boundary | Active test near deadline | Wait until server deadline; reload | Deadline reached | Server submits and calculates result | `test_test_auto_submits_when_server_deadline_has_passed` passed | Pass | Automated |
| TC-025 | FR-013 | Record matching coding sample | Student session | Submit code and exact displayed output | Valid sample output | Sample-pass state stored with limitation notice | `test_coding_sample_check_never_claims_full_execution` passed | Pass | Automated |
| TC-026 | FR-013 | Reject mismatched coding sample | Student session | Submit code and different output | Wrong output | Sample-failed state; no acceptance claim | Not Executed | Pending | Negative |
| TC-027 | FR-013 | Ensure code is not executed | Student session | Submit code containing a side-effect expression | Harmless text such as print statement | Code is stored; no execution occurs | `test_coding_sample_check_never_claims_full_execution` passed; implementation contains no execution call | Pass | Automated/code inspection |
| TC-028 | FR-014 | Save HR draft | Student session | Enter answer and save | Draft text | Draft persists after reload | `test_hr_answer_is_saved_and_marked_practiced` passed | Pass | Automated |
| TC-029 | FR-014 | Reject oversized HR answer | Student session | Submit answer beyond limit | More than 5,000 characters | Validation error; prior answer retained | Not Executed | Pending | Boundary |
| TC-030 | FR-015 | View empty progress | New student | Open dashboard/progress | No attempts | Useful empty state; no fabricated score | Not Executed | Pending | Boundary |
| TC-031 | FR-016 | Generate high-priority advice | Student has measured score below 50% | Record weak practice/test; view recommendations | Score below threshold | High-priority category recommendation | `test_recommendations_use_real_score_and_empty_state_is_not_fabricated` passed | Pass | Automated |
| TC-032 | FR-016 | Refresh advice after activity | Student with a recommendation | Complete a new test/practice | New measured activity | Recommendation set reflects available new score | Not Executed | Pending | Integration |
| TC-033 | FR-017 | Admin creates a question | Admin session | Submit valid content form | Valid category/text/options | Question appears in student bank | `test_admin_can_create_question_and_test_validation` passed | Pass | Automated |
| TC-034 | FR-017 | Reject incomplete MCQ | Admin session | Submit MCQ without four choices/key | Missing option or key | Validation error; no partial question | Not Executed | Pending | Negative |
| TC-035 | FR-018 | Admin creates a test | Admin session; valid MCQs | Select category, questions, duration and pass mark | Duration 1–180; same-category questions | Published test can be started by student | `test_admin_can_create_question_and_test_validation` passed | Pass | Automated |
| TC-036 | FR-018 | Reject invalid test duration | Admin session | Submit out-of-range duration | `0` or `181` | Validation error; no test created | `test_admin_can_create_question_and_test_validation` passed | Pass | Automated |
| TC-037 | FR-019 | Admin views test results | Admin session; submitted attempt exists | Open admin workspace | Seed/test attempt | Student/test/percentage displayed | Not Executed | Pending | Integration |
| TC-038 | FR-020 | Persist database after restart | Local seeded database | Save content; restart app; query content | Existing database file | Data remains available | Not Executed | Pending | Reliability |
| TC-039 | FR-022 | Reject absent/invalid CSRF token | CSRF enabled; signed-out form | Submit POST without valid token | Missing token | HTTP 400; no state change | Not Executed | Pending | Security |
| TC-040 | NFR-006 | Handle missing database record | Student session | Request absent content ID | Nonexistent ID | Clear 404 response, no traceback | Not Executed | Pending | Error handling |
| TC-041 | NFR-007 | Check mobile layout | Browser at narrow viewport | Load landing/dashboard/question list | 375px viewport | Navigation and forms fit viewport | Not Executed | Pending | Usability |
| TC-042 | NFR-007 | Respect reduced motion | Browser prefers reduced motion | Load landing page | Reduced motion enabled | Non-essential motion is suppressed | Not Executed | Pending | Accessibility |
| TC-043 | FR-023 | Add and rename an unused category | Admin session | Create and rename a category | Unique category name | Category is saved with the updated name | `test_admin_category_and_question_management` passed | Pass | Automated |
| TC-044 | FR-019 | Disable an active student account | Admin and student sessions | Admin disables the student; student requests dashboard | Existing student session | Disabled account is no longer authenticated | `test_admin_disabling_account_invalidates_existing_session` passed | Pass | Automated |
| TC-045 | FR-017 | Edit and delete unused question content | Admin session; question has no history | Create, edit, and delete an unlinked question | Temporary descriptive question | Updated question persists; unused content can be deleted | `test_admin_category_and_question_management` passed | Pass | Automated |

## Automated test execution

Run `python -m pytest -q` from the project directory. The automated test file is `tests/test_app.py`; its fixture creates a temporary SQLite database for each test. The test run output, rather than the pending manual catalog rows, is the evidence for automated execution.

### Observed run

On 2026-10-29, the final full automated suite completed with **17 passed** in 37.28 seconds. Rows explicitly marked Automated above map to assertions in that run. Other manual-only cases remain `Not Executed` / `Pending`; no manual behavior is claimed.
