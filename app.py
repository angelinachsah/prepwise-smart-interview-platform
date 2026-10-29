"""Flask application factory and HTTP routes."""
from datetime import date, timedelta, timezone
from functools import wraps
import json
import re

from flask import (
    Flask, abort, flash, redirect, render_template, request, url_for,
)
from flask_login import (
    LoginManager, current_user, login_required, login_user, logout_user,
)
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy import or_

from config import Config
from models import (
    ActivityLog, AttemptAnswer, Bookmark, Category, CodingProblem,
    CodingSubmission, HRPractice, HRQuestion, MockTest, Question,
    QuestionAttempt, Recommendation, TestAttempt, TestQuestion, User, db,
    utcnow,
)

login_manager = LoginManager()
csrf = CSRFProtect()
PASSWORD_PATTERN = re.compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).{8,128}$")
ANSWER_CHOICES = {"A", "B", "C", "D"}


@login_manager.user_loader
def load_user(user_id):
    user = db.session.get(User, int(user_id)) if str(user_id).isdigit() else None
    return user if user and user.is_active else None


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped(*args, **kwargs):
        if current_user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped


def log_activity(kind, reference_id=None, score=None):
    db.session.add(ActivityLog(
        user_id=current_user.id, activity_type=kind,
        reference_id=reference_id, score=score,
    ))


def _utc(value):
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def summarize_activity_streak(activity_dates, today=None):
    """Summarize distinct UTC activity dates and the trailing seven-day window."""
    today = today or utcnow().date()
    dates = set(activity_dates)
    active_today = today in dates

    cursor = today if active_today else today - timedelta(days=1)
    current_streak = 0
    while cursor in dates:
        current_streak += 1
        cursor -= timedelta(days=1)

    best_streak = 0
    running_streak = 0
    previous_day = None
    for activity_day in sorted(dates):
        if previous_day and activity_day == previous_day + timedelta(days=1):
            running_streak += 1
        else:
            running_streak = 1
        best_streak = max(best_streak, running_streak)
        previous_day = activity_day

    week_start = today - timedelta(days=6)
    week_days = [
        {
            "date": week_start + timedelta(days=offset),
            "active": week_start + timedelta(days=offset) in dates,
            "today": week_start + timedelta(days=offset) == today,
        }
        for offset in range(7)
    ]
    return {
        "current": current_streak,
        "best": best_streak,
        "active_today": active_today,
        "total_days": len(dates),
        "week_days": week_days,
    }


def _activity_streak(user_id):
    stored_dates = db.session.query(
        db.func.date(ActivityLog.created_at)
    ).filter_by(user_id=user_id).distinct().all()
    activity_dates = {
        date.fromisoformat(row[0]) for row in stored_dates if row[0]
    }
    return summarize_activity_streak(activity_dates)


def _get_attempt_or_404(attempt_id):
    attempt = db.session.get(TestAttempt, attempt_id)
    if not attempt or (attempt.user_id != current_user.id and current_user.role != "admin"):
        abort(404)
    return attempt


def _score_summary(user_id):
    stats = []
    for category in Category.query.order_by(Category.name).all():
        results = [
            row.is_correct for row in QuestionAttempt.query.join(
                Question, Question.id == QuestionAttempt.question_id
            ).filter(
                QuestionAttempt.user_id == user_id,
                Question.category_id == category.id,
                QuestionAttempt.is_correct.is_not(None),
            ).all()
        ]
        tests = TestAttempt.query.join(
            MockTest, TestAttempt.test_id == MockTest.id
        ).filter(
            TestAttempt.user_id == user_id,
            MockTest.category_id == category.id,
            TestAttempt.status == "submitted",
        ).order_by(TestAttempt.submitted_at.desc()).limit(3).all()
        if results:
            percentage = round(100 * sum(results) / len(results))
        elif tests:
            percentage = round(sum(t.percentage or 0 for t in tests) / len(tests))
        else:
            continue
        stats.append({"name": category.name, "score": percentage})
    submissions = CodingSubmission.query.filter_by(user_id=user_id).order_by(
        CodingSubmission.submitted_at.desc()
    ).all()
    latest_by_problem = {}
    for submission in submissions:
        latest_by_problem.setdefault(submission.problem_id, submission.result_status)
    if latest_by_problem:
        passed = sum(status == "sample_passed" for status in latest_by_problem.values())
        stats.append({
            "name": "Coding",
            "score": round(100 * passed / len(latest_by_problem)),
        })
    practiced_hr = HRPractice.query.filter_by(user_id=user_id, is_practiced=True).count()
    total_hr = HRQuestion.query.count()
    if practiced_hr and total_hr:
        stats.append({
            "name": "HR preparation",
            "score": round(100 * practiced_hr / total_hr),
        })
    return stats


def refresh_recommendations(user_id):
    Recommendation.query.filter_by(user_id=user_id, is_completed=False).delete()
    category_scores = _score_summary(user_id)
    for item in category_scores:
        score = item["score"]
        category = Category.query.filter_by(name=item["name"]).first()
        if score < 50:
            priority, title, action = "High", f"Prioritize {item['name']} revision", "Start a focused practice session"
            why = f"Your current measured score is {score}%, below the 50% target."
        elif score < 70:
            priority, title, action = "Medium", f"Build confidence in {item['name']}", "Practice more questions in this category"
            why = f"Your measured score is {score}%; more practice can strengthen the fundamentals."
        elif score < 85:
            priority, title, action = "Low", f"Keep progressing in {item['name']}", "Review missed questions and try another test"
            why = f"Your measured score is {score}%; targeted revision can improve consistency."
        else:
            priority, title, action = "Low", f"Maintain your {item['name']} proficiency", "Try advanced questions"
            why = f"Your measured score is {score}%, showing strong recent preparation."
        db.session.add(Recommendation(
            user_id=user_id, category_id=category.id if category else None,
            title=title, explanation=why, priority=priority,
            suggested_action=action,
        ))
    db.session.commit()


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_override:
        app.config.update(config_override)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please sign in to continue."
    login_manager.login_message_category = "info"

    @app.get("/")
    def landing():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        return render_template("landing.html")

    @app.route("/register", methods=["GET", "POST"])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            name = request.form.get("full_name", "").strip()
            email = request.form.get("email", "").strip().lower()
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            if not name or len(name) > 100 or not email or len(email) > 254:
                flash("Enter a name and a valid email address.", "error")
            elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
                flash("Enter a valid email address.", "error")
            elif not PASSWORD_PATTERN.fullmatch(password):
                flash("Use 8–128 characters with uppercase, lowercase, and a number.", "error")
            elif password != confirm:
                flash("Passwords do not match.", "error")
            elif User.query.filter_by(email=email).first():
                flash("An account already exists for that email.", "error")
            else:
                user = User(
                    full_name=name,
                    email=email,
                    preferred_job_role=request.form.get("preferred_job_role", "").strip()[:100],
                    education=request.form.get("education", "").strip()[:120],
                )
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Welcome! Your account is ready.", "success")
                return redirect(url_for("dashboard"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("dashboard"))
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=email).first()
            if user and user.is_active and user.check_password(request.form.get("password", "")):
                login_user(user)
                return redirect(url_for("admin_dashboard" if user.role == "admin" else "dashboard"))
            flash("Email or password is incorrect.", "error")
        return render_template("login.html")

    @app.post("/logout")
    @login_required
    def logout():
        logout_user()
        flash("You are signed out.", "info")
        return redirect(url_for("landing"))

    @app.get("/dashboard")
    @login_required
    def dashboard():
        user_id = current_user.id
        completed_tests = TestAttempt.query.filter_by(user_id=user_id, status="submitted").count()
        questions_attempted = QuestionAttempt.query.filter_by(user_id=user_id).count()
        solved = CodingSubmission.query.filter_by(user_id=user_id, result_status="sample_passed").with_entities(
            CodingSubmission.problem_id
        ).distinct().count()
        test_scores = [a.percentage for a in TestAttempt.query.filter_by(
            user_id=user_id, status="submitted"
        ).all() if a.percentage is not None]
        average_score = round(sum(test_scores) / len(test_scores)) if test_scores else None
        recent = ActivityLog.query.filter_by(user_id=user_id).order_by(ActivityLog.created_at.desc()).limit(6).all()
        category_scores = _score_summary(user_id)
        streak = _activity_streak(user_id)
        overall_progress = round(
            sum(item["score"] for item in category_scores) / len(category_scores)
        ) if category_scores else None
        return render_template(
            "dashboard.html", completed_tests=completed_tests,
            questions_attempted=questions_attempted, solved=solved,
            average_score=average_score, recent=recent,
            category_scores=category_scores,
            overall_progress=overall_progress,
            streak=streak,
            tests=MockTest.query.filter_by(is_published=True).limit(3).all(),
        )

    @app.get("/questions")
    @login_required
    def questions():
        query = Question.query.join(Category)
        search = request.args.get("q", "").strip()[:100]
        category_id = request.args.get("category", type=int)
        difficulty = request.args.get("difficulty", "")
        if search:
            query = query.filter(or_(
                Question.question_text.ilike(f"%{search}%"),
                Question.tags.ilike(f"%{search}%"),
            ))
        if category_id:
            query = query.filter(Question.category_id == category_id)
        if difficulty in {"Beginner", "Intermediate", "Advanced"}:
            query = query.filter(Question.difficulty == difficulty)
        page = request.args.get("page", 1, type=int)
        pagination = query.order_by(Question.id).paginate(
            page=max(page or 1, 1), per_page=app.config["ITEMS_PER_PAGE"], error_out=False
        )
        bookmarked = {b.question_id for b in Bookmark.query.filter_by(user_id=current_user.id).all()}
        return render_template(
            "questions.html", pagination=pagination,
            categories=Category.query.order_by(Category.name).all(),
            search=search, selected_category=category_id,
            difficulty=difficulty, bookmarked=bookmarked,
        )

    @app.route("/questions/<int:question_id>", methods=["GET", "POST"])
    @login_required
    def question_detail(question_id):
        question = db.get_or_404(Question, question_id)
        bookmark = Bookmark.query.filter_by(user_id=current_user.id, question_id=question.id).first()
        if request.method == "POST":
            action = request.form.get("action")
            if action == "bookmark":
                if bookmark:
                    db.session.delete(bookmark)
                else:
                    db.session.add(Bookmark(user_id=current_user.id, question_id=question.id))
                db.session.commit()
                return redirect(url_for("question_detail", question_id=question.id))
            if action == "complete":
                selected = request.form.get("answer", "").upper()
                correct = None
                if question.question_type == "mcq":
                    if selected not in ANSWER_CHOICES:
                        flash("Choose one of the listed answers.", "error")
                        return redirect(url_for("question_detail", question_id=question.id))
                    correct = selected == question.correct_answer
                db.session.add(QuestionAttempt(
                    user_id=current_user.id, question_id=question.id, is_correct=correct
                ))
                log_activity("question_practice", question.id, 100 if correct else (0 if correct is False else None))
                db.session.commit()
                refresh_recommendations(current_user.id)
                flash("Practice recorded." + (" Review the explanation below." if correct is False else ""), "success")
                return redirect(url_for("question_detail", question_id=question.id))
        return render_template("question_detail.html", question=question, bookmarked=bool(bookmark))

    @app.get("/mock-tests")
    @login_required
    def mock_tests():
        tests = MockTest.query.filter_by(is_published=True).order_by(MockTest.id).all()
        return render_template("mock_tests.html", tests=tests)

    @app.post("/mock-tests/<int:test_id>/start")
    @login_required
    def start_test(test_id):
        test = MockTest.query.filter_by(id=test_id, is_published=True).first_or_404()
        if test.duration_minutes < 1 or test.duration_minutes > 180:
            abort(400)
        if not TestQuestion.query.filter_by(test_id=test.id).first():
            flash("This test is not ready yet.", "error")
            return redirect(url_for("mock_tests"))
        attempt = TestAttempt(user_id=current_user.id, test_id=test.id)
        db.session.add(attempt)
        db.session.flush()
        log_activity("test_started", test.id)
        db.session.commit()
        return redirect(url_for("take_test", attempt_id=attempt.id))

    @app.route("/test-attempts/<int:attempt_id>", methods=["GET", "POST"])
    @login_required
    def take_test(attempt_id):
        attempt = _get_attempt_or_404(attempt_id)
        if attempt.status != "in_progress":
            return redirect(url_for("test_result", attempt_id=attempt.id))
        now = utcnow()
        deadline = _utc(attempt.started_at) + timedelta(minutes=attempt.test.duration_minutes)
        if request.method == "POST" or now >= deadline:
            if now >= deadline:
                flash("Time expired. Your test has been submitted automatically.", "info")
            allowed = {link.question_id: link for link in TestQuestion.query.filter_by(test_id=attempt.test_id).all()}
            answer_fields = [key for key in request.form if key.startswith("q_")]
            if any(not key.split("_", 1)[1].isdigit() for key in answer_fields):
                abort(400)
            submitted_ids = {int(key.split("_", 1)[1]) for key in answer_fields}
            if request.method == "POST" and submitted_ids - allowed.keys():
                abort(400)
            raw_score = 0
            max_score = sum(link.marks for link in allowed.values())
            for question_id, link in allowed.items():
                selected = request.form.get(f"q_{question_id}", "").upper()
                if selected and selected not in ANSWER_CHOICES:
                    abort(400)
                is_correct = selected == link.question.correct_answer and bool(selected)
                marks = link.marks if is_correct else 0
                raw_score += marks
                db.session.add(AttemptAnswer(
                    attempt_id=attempt.id, question_id=question_id,
                    selected_answer=selected or None, is_correct=is_correct,
                    marks_awarded=marks,
                ))
            attempt.status = "submitted"
            attempt.submitted_at = now
            attempt.score = raw_score
            attempt.percentage = round((raw_score / max_score) * 100, 2) if max_score else 0
            attempt.time_taken_seconds = max(0, min(int((now - _utc(attempt.started_at)).total_seconds()), attempt.test.duration_minutes * 60))
            log_activity("test_submitted", attempt.test_id, attempt.percentage)
            db.session.commit()
            refresh_recommendations(attempt.user_id)
            return redirect(url_for("test_result", attempt_id=attempt.id))
        links = TestQuestion.query.filter_by(test_id=attempt.test_id).all()
        questions_for_test = [link.question for link in links]
        existing_answers = {a.question_id: a.selected_answer for a in attempt.answers}
        remaining = max(0, int((deadline - now).total_seconds()))
        return render_template(
            "take_test.html", attempt=attempt, questions=questions_for_test,
            existing_answers=existing_answers, remaining_seconds=remaining,
        )

    @app.get("/test-attempts/<int:attempt_id>/result")
    @login_required
    def test_result(attempt_id):
        attempt = _get_attempt_or_404(attempt_id)
        if attempt.status == "in_progress":
            return redirect(url_for("take_test", attempt_id=attempt.id))
        answers = AttemptAnswer.query.filter_by(attempt_id=attempt.id).all()
        total = sum(link.marks for link in TestQuestion.query.filter_by(test_id=attempt.test_id).all())
        return render_template("test_result.html", attempt=attempt, answers=answers, total=total)

    @app.get("/coding")
    @login_required
    def coding():
        problems = CodingProblem.query.order_by(CodingProblem.id).all()
        solved = {
            row.problem_id for row in CodingSubmission.query.filter_by(
                user_id=current_user.id, result_status="sample_passed"
            ).all()
        }
        return render_template("coding.html", problems=problems, solved=solved)

    @app.route("/coding/<int:problem_id>", methods=["GET", "POST"])
    @login_required
    def coding_detail(problem_id):
        problem = db.get_or_404(CodingProblem, problem_id)
        if request.method == "POST":
            code = request.form.get("code", "")
            output = request.form.get("observed_output", "")
            try:
                sample_cases = json.loads(problem.test_cases_json)
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid coding problem test-case data for problem {problem.id}.") from error
            if not isinstance(sample_cases, list) or not sample_cases or any(
                not isinstance(case, dict) or not isinstance(case.get("output"), str)
                for case in sample_cases
            ):
                raise ValueError(f"Coding problem {problem.id} has no sample cases configured.")
            case_index = request.form.get("case_index", default="0")
            if not case_index.isdigit() or int(case_index) >= len(sample_cases):
                abort(400)
            if not code.strip() or len(code) > 20000:
                flash("Enter code (up to 20,000 characters) before checking the sample.", "error")
                return redirect(url_for("coding_detail", problem_id=problem.id))
            selected_case = sample_cases[int(case_index)]
            expected_output = str(selected_case.get("output", "")).strip()
            passed = output == expected_output
            submission = CodingSubmission(
                user_id=current_user.id, problem_id=problem.id,
                submitted_code=code, result_status="sample_passed" if passed else "sample_failed",
                test_cases_passed=1 if passed else 0, test_cases_total=1,
            )
            db.session.add(submission)
            log_activity(
                "coding_sample_passed" if passed else "coding_sample_attempt",
                problem.id, 100 if passed else 0,
            )
            db.session.commit()
            refresh_recommendations(current_user.id)
            flash(
                "Sample output matches. This is a sample check only; code was not executed." if passed
                else "Sample output does not match. Review the example and try again.",
                "success" if passed else "error",
            )
            return redirect(url_for("coding_detail", problem_id=problem.id))
        try:
            sample_cases = json.loads(problem.test_cases_json)
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid coding problem test-case data for problem {problem.id}.") from error
        if not isinstance(sample_cases, list) or any(
            not isinstance(case, dict)
            or not isinstance(case.get("input"), str)
            or not isinstance(case.get("output"), str)
            for case in sample_cases
        ):
            raise ValueError(f"Coding problem {problem.id} test cases have an invalid format.")
        return render_template("coding_detail.html", problem=problem, sample_cases=sample_cases)

    @app.get("/hr")
    @login_required
    def hr_practice():
        questions = HRQuestion.query.order_by(HRQuestion.id).all()
        practices = {p.hr_question_id: p for p in HRPractice.query.filter_by(user_id=current_user.id).all()}
        practiced = sum(1 for p in practices.values() if p.is_practiced)
        percentage = round(practiced * 100 / len(questions)) if questions else 0
        return render_template("hr.html", questions=questions, practices=practices, percentage=percentage)

    @app.post("/hr/<int:question_id>")
    @login_required
    def save_hr_answer(question_id):
        question = db.get_or_404(HRQuestion, question_id)
        answer = request.form.get("answer", "").strip()
        if len(answer) > 5000:
            flash("Answer must be 5,000 characters or fewer.", "error")
            return redirect(url_for("hr_practice"))
        practice = HRPractice.query.filter_by(
            user_id=current_user.id, hr_question_id=question.id
        ).first()
        if not practice:
            practice = HRPractice(user_id=current_user.id, hr_question_id=question.id)
            db.session.add(practice)
        practice.personal_answer = answer
        practice.is_practiced = request.form.get("practiced") == "yes"
        log_activity("hr_practice", question.id)
        db.session.commit()
        refresh_recommendations(current_user.id)
        flash("Your answer has been saved.", "success")
        return redirect(url_for("hr_practice"))

    @app.get("/progress")
    @login_required
    def progress():
        scores = _score_summary(current_user.id)
        attempts = TestAttempt.query.filter_by(
            user_id=current_user.id, status="submitted"
        ).order_by(TestAttempt.submitted_at.desc()).limit(10).all()
        question_count = QuestionAttempt.query.filter_by(user_id=current_user.id).count()
        coding_total = CodingSubmission.query.filter_by(user_id=current_user.id).count()
        return render_template(
            "progress.html", scores=scores, attempts=attempts,
            question_count=question_count, coding_total=coding_total,
            timeline=list(reversed(attempts)),
        )

    @app.get("/recommendations")
    @login_required
    def recommendations():
        items = Recommendation.query.filter_by(user_id=current_user.id).order_by(
            Recommendation.is_completed, Recommendation.created_at.desc()
        ).all()
        return render_template("recommendations.html", items=items, has_scores=bool(_score_summary(current_user.id)))

    @app.post("/recommendations/<int:recommendation_id>/complete")
    @login_required
    def complete_recommendation(recommendation_id):
        recommendation = Recommendation.query.filter_by(
            id=recommendation_id, user_id=current_user.id
        ).first_or_404()
        recommendation.is_completed = True
        db.session.commit()
        return redirect(url_for("recommendations"))

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            action = request.form.get("action")
            if action == "profile":
                name = request.form.get("full_name", "").strip()
                role = request.form.get("preferred_job_role", "").strip()
                education = request.form.get("education", "").strip()
                if not name or len(name) > 100 or len(role) > 100 or len(education) > 120:
                    flash("Check the required name and input lengths.", "error")
                else:
                    current_user.full_name = name
                    current_user.preferred_job_role = role
                    current_user.education = education
                    db.session.commit()
                    flash("Profile updated.", "success")
            elif action == "password":
                old = request.form.get("current_password", "")
                new = request.form.get("new_password", "")
                if not current_user.check_password(old):
                    flash("Current password is incorrect.", "error")
                elif not PASSWORD_PATTERN.fullmatch(new):
                    flash("Use 8–128 characters with uppercase, lowercase, and a number.", "error")
                elif new != request.form.get("confirm_password", ""):
                    flash("New passwords do not match.", "error")
                else:
                    current_user.set_password(new)
                    db.session.commit()
                    flash("Password changed successfully.", "success")
            return redirect(url_for("profile"))
        return render_template("profile.html")

    @app.get("/admin")
    @admin_required
    def admin_dashboard():
        return render_template(
            "admin_dashboard.html",
            student_count=User.query.filter_by(role="student").count(),
            question_count=Question.query.count(),
            test_count=MockTest.query.count(),
            result_count=TestAttempt.query.filter_by(status="submitted").count(),
            users=User.query.filter_by(role="student").order_by(User.created_at.desc()).limit(20).all(),
            attempts=TestAttempt.query.filter_by(status="submitted").order_by(
                TestAttempt.submitted_at.desc()
            ).limit(20).all(),
            categories=Category.query.order_by(Category.name).all(),
            questions=Question.query.order_by(Question.id.desc()).all(),
            tests=MockTest.query.order_by(MockTest.id.desc()).all(),
            coding_problems=CodingProblem.query.order_by(CodingProblem.id).all(),
            hr_questions=HRQuestion.query.order_by(HRQuestion.id).all(),
        )

    @app.post("/admin/categories")
    @admin_required
    def admin_add_category():
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        if not name or len(name) > 80 or len(description) > 240:
            flash("Enter a category name (up to 80 characters) and a description up to 240 characters.", "error")
        elif Category.query.filter(Category.name.ilike(name)).first():
            flash("A category with that name already exists.", "error")
        else:
            db.session.add(Category(name=name, description=description))
            db.session.commit()
            flash("Category created.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/categories/<int:category_id>/edit")
    @admin_required
    def admin_edit_category(category_id):
        category = db.get_or_404(Category, category_id)
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        duplicate = Category.query.filter(
            Category.name.ilike(name), Category.id != category.id
        ).first() if name else None
        if not name or len(name) > 80 or len(description) > 240 or duplicate:
            flash("Enter a unique category name (up to 80 characters) and description up to 240 characters.", "error")
        else:
            category.name = name
            category.description = description
            db.session.commit()
            flash("Category updated.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/categories/<int:category_id>/delete")
    @admin_required
    def admin_delete_category(category_id):
        category = db.get_or_404(Category, category_id)
        in_use = (
            Question.query.filter_by(category_id=category.id).first()
            or MockTest.query.filter_by(category_id=category.id).first()
            or Recommendation.query.filter_by(category_id=category.id).first()
        )
        if in_use:
            flash("This category is used by questions, tests, or recommendations and cannot be deleted.", "error")
        else:
            db.session.delete(category)
            db.session.commit()
            flash("Category deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/questions/<int:question_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_question(question_id):
        question = db.get_or_404(Question, question_id)
        linked = (
            TestQuestion.query.filter_by(question_id=question.id).first()
            or QuestionAttempt.query.filter_by(question_id=question.id).first()
            or AttemptAnswer.query.filter_by(question_id=question.id).first()
        )
        if linked:
            flash("Questions used by a test or saved practice history are locked to preserve past results.", "error")
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            text = request.form.get("question_text", "").strip()
            category_id = request.form.get("category_id", type=int)
            qtype = request.form.get("question_type", "descriptive")
            correct = request.form.get("correct_answer", "").upper() or None
            options = [
                request.form.get(f"option_{letter.lower()}", "").strip()[:300] or None
                for letter in "ABCD"
            ]
            if not text or len(text) > 2000 or not db.session.get(Category, category_id):
                flash("A question and valid category are required.", "error")
            elif qtype == "mcq" and (not all(options) or correct not in ANSWER_CHOICES):
                flash("MCQs need four options and a valid correct answer.", "error")
            else:
                question.question_text = text
                question.category_id = category_id
                question.question_type = "mcq" if qtype == "mcq" else "descriptive"
                question.difficulty = request.form.get("difficulty", "Beginner")
                if question.difficulty not in {"Beginner", "Intermediate", "Advanced"}:
                    question.difficulty = "Beginner"
                question.option_a, question.option_b, question.option_c, question.option_d = options
                question.correct_answer = correct if question.question_type == "mcq" else None
                question.explanation = request.form.get("explanation", "").strip()[:3000]
                db.session.commit()
                flash("Question updated.", "success")
                return redirect(url_for("admin_dashboard"))
        return render_template(
            "admin_edit_question.html", question=question,
            categories=Category.query.order_by(Category.name).all(),
        )

    @app.post("/admin/questions/<int:question_id>/delete")
    @admin_required
    def admin_delete_question(question_id):
        question = db.get_or_404(Question, question_id)
        linked = (
            TestQuestion.query.filter_by(question_id=question.id).first()
            or QuestionAttempt.query.filter_by(question_id=question.id).first()
            or AttemptAnswer.query.filter_by(question_id=question.id).first()
        )
        if linked:
            flash("This question is part of a test or saved practice history and cannot be deleted.", "error")
        else:
            db.session.delete(question)
            db.session.commit()
            flash("Question deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/questions")
    @admin_required
    def admin_add_question():
        text = request.form.get("question_text", "").strip()
        category_id = request.form.get("category_id", type=int)
        difficulty = request.form.get("difficulty", "Beginner")
        qtype = request.form.get("question_type", "descriptive")
        if not text or len(text) > 2000 or not db.session.get(Category, category_id):
            flash("A question and valid category are required.", "error")
            return redirect(url_for("admin_dashboard"))
        question = Question(
            question_text=text, category_id=category_id,
            difficulty=difficulty if difficulty in {"Beginner", "Intermediate", "Advanced"} else "Beginner",
            question_type="mcq" if qtype == "mcq" else "descriptive",
            option_a=request.form.get("option_a", "").strip()[:300] or None,
            option_b=request.form.get("option_b", "").strip()[:300] or None,
            option_c=request.form.get("option_c", "").strip()[:300] or None,
            option_d=request.form.get("option_d", "").strip()[:300] or None,
            correct_answer=request.form.get("correct_answer", "").upper() or None,
            explanation=request.form.get("explanation", "").strip()[:3000],
        )
        if question.question_type == "mcq" and (
            not all((question.option_a, question.option_b, question.option_c, question.option_d))
            or question.correct_answer not in ANSWER_CHOICES
        ):
            flash("MCQs need four options and a valid correct answer.", "error")
            return redirect(url_for("admin_dashboard"))
        db.session.add(question)
        db.session.commit()
        flash("Question created.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/tests")
    @admin_required
    def admin_add_test():
        title = request.form.get("title", "").strip()
        category_id = request.form.get("category_id", type=int)
        duration = request.form.get("duration_minutes", type=int)
        passing = request.form.get("passing_percentage", type=int)
        question_ids = request.form.getlist("question_ids", type=int)
        if (
            not title or len(title) > 120 or not db.session.get(Category, category_id)
            or not duration or not 1 <= duration <= 180
            or passing is None or not 0 <= passing <= 100
        ):
            flash("Enter a valid title, category, duration (1–180), and pass score (0–100).", "error")
            return redirect(url_for("admin_dashboard"))
        selected_questions = Question.query.filter(
            Question.id.in_(question_ids), Question.category_id == category_id,
            Question.question_type == "mcq",
        ).all()
        if not selected_questions or len(selected_questions) != len(set(question_ids)):
            flash("Select one or more valid multiple-choice questions from the category.", "error")
            return redirect(url_for("admin_dashboard"))
        test = MockTest(
            title=title, description=request.form.get("description", "").strip()[:2000],
            category_id=category_id, duration_minutes=duration,
            passing_percentage=passing,
        )
        db.session.add(test)
        db.session.flush()
        for question in selected_questions:
            db.session.add(TestQuestion(test_id=test.id, question_id=question.id))
        db.session.commit()
        flash("Mock test created and published.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.route("/admin/tests/<int:test_id>/edit", methods=["GET", "POST"])
    @admin_required
    def admin_edit_test(test_id):
        test = db.get_or_404(MockTest, test_id)
        if TestAttempt.query.filter_by(test_id=test.id).first():
            flash("A test with attempt history cannot be edited; create a new test instead.", "error")
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            duration = request.form.get("duration_minutes", type=int)
            passing = request.form.get("passing_percentage", type=int)
            if (
                not title or len(title) > 120 or len(description) > 2000
                or not duration or not 1 <= duration <= 180
                or passing is None or not 0 <= passing <= 100
            ):
                flash("Enter a valid title, duration (1–180), and pass score (0–100).", "error")
            else:
                test.title = title
                test.description = description
                test.duration_minutes = duration
                test.passing_percentage = passing
                test.is_published = request.form.get("is_published") == "yes"
                db.session.commit()
                flash("Mock test updated.", "success")
                return redirect(url_for("admin_dashboard"))
        return render_template("admin_edit_test.html", test=test)

    @app.post("/admin/tests/<int:test_id>/delete")
    @admin_required
    def admin_delete_test(test_id):
        test = db.get_or_404(MockTest, test_id)
        if TestAttempt.query.filter_by(test_id=test.id).first():
            flash("This test has attempt history and cannot be deleted.", "error")
        else:
            db.session.delete(test)
            db.session.commit()
            flash("Mock test deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/users/<int:user_id>/toggle")
    @admin_required
    def admin_toggle_user(user_id):
        user = db.get_or_404(User, user_id)
        if user.id == current_user.id:
            flash("You cannot disable your own administrator account.", "error")
        else:
            user.is_active = not user.is_active
            db.session.commit()
            flash("Account " + ("enabled." if user.is_active else "disabled."), "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/coding")
    @admin_required
    def admin_add_coding_problem():
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        sample_input = request.form.get("sample_input", "").strip()
        sample_output = request.form.get("sample_output", "").strip()
        fields = (
            (title, 120), (description, 3000),
            (sample_input, 2000), (sample_output, 2000),
        )
        if not all(value for value, _limit in fields) or any(
            len(value) > limit for value, limit in fields
        ):
            flash("Title, description, sample input, and sample output are required and must be within length limits.", "error")
        elif CodingProblem.query.filter_by(title=title).first():
            flash("A coding problem with that title already exists.", "error")
        else:
            db.session.add(CodingProblem(
                title=title, description=description,
                difficulty=request.form.get("difficulty", "Beginner"),
                sample_input=sample_input, sample_output=sample_output,
                input_format=request.form.get("input_format", "").strip()[:1000],
                output_format=request.form.get("output_format", "").strip()[:1000],
                constraints=request.form.get("constraints", "").strip()[:1000],
                hints=request.form.get("hints", "").strip()[:1000],
                solution_explanation=request.form.get("solution_explanation", "").strip()[:2000],
                test_cases_json=json.dumps([{
                    "input": sample_input,
                    "output": sample_output,
                }]),
            ))
            db.session.commit()
            flash("Coding problem created.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/hr")
    @admin_required
    def admin_add_hr_question():
        text = request.form.get("question_text", "").strip()
        example = request.form.get("example_answer", "").strip()
        tips = request.form.get("answer_tips", "").strip()
        category = request.form.get("category", "General").strip()
        if (
            not text or not example or not tips or len(text) > 300
            or len(example) > 3000 or len(tips) > 1000 or len(category) > 60
        ):
            flash("Enter a prompt, example, and tips within their length limits.", "error")
        elif HRQuestion.query.filter_by(question_text=text).first():
            flash("That HR question already exists.", "error")
        else:
            db.session.add(HRQuestion(
                question_text=text, example_answer=example,
                answer_tips=tips, category=category or "General",
            ))
            db.session.commit()
            flash("HR question created.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/coding/<int:problem_id>/delete")
    @admin_required
    def admin_delete_coding_problem(problem_id):
        problem = db.get_or_404(CodingProblem, problem_id)
        if CodingSubmission.query.filter_by(problem_id=problem.id).first():
            flash("This coding problem has student submissions and cannot be deleted.", "error")
        else:
            db.session.delete(problem)
            db.session.commit()
            flash("Coding problem deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.post("/admin/hr/<int:question_id>/delete")
    @admin_required
    def admin_delete_hr_question(question_id):
        question = db.get_or_404(HRQuestion, question_id)
        if HRPractice.query.filter_by(hr_question_id=question.id).first():
            flash("This HR question has saved student drafts and cannot be deleted.", "error")
        else:
            db.session.delete(question)
            db.session.commit()
            flash("HR question deleted.", "success")
        return redirect(url_for("admin_dashboard"))

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return render_template(
            "error.html", code=400, title="Session expired",
            message="Refresh the page and submit the form again.",
        ), 400

    @app.errorhandler(403)
    def forbidden(_error):
        return render_template("error.html", code=403, title="Access denied", message="You do not have permission to view this page."), 403

    @app.errorhandler(404)
    def not_found(_error):
        return render_template("error.html", code=404, title="Page not found", message="We could not find that page or record."), 404

    @app.errorhandler(500)
    def server_error(_error):
        db.session.rollback()
        return render_template("error.html", code=500, title="Something went wrong", message="The request could not be completed. Please try again."), 500

    with app.app_context():
        db.create_all()
    return app
