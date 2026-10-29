import re
from datetime import timedelta

import pytest

from app import create_app
from models import (
    Category, CodingProblem, MockTest, Question, TestAttempt as DBTestAttempt,
    User, db, utcnow,
)
from seed import seed_data


@pytest.fixture()
def app(tmp_path):
    database = tmp_path / "test.sqlite"
    application = create_app({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "test-key",
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{database.as_posix()}",
    })
    with application.app_context():
        db.drop_all()
        db.create_all()
        seed_data(admin_email="admin@test.local", admin_password="AdminTest123")
        student = User(
            full_name="Taylor Student", email="student@test.local",
            preferred_job_role="Engineer",
        )
        student.set_password("StudentTest123")
        db.session.add(student)
        db.session.commit()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login(client, email="student@test.local", password="StudentTest123"):
    return client.post("/login", data={"email": email, "password": password}, follow_redirects=True)


def test_landing_and_student_dashboard(client):
    assert client.get("/").status_code == 200
    login(client)
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Taylor" in response.data
    assert b"Your progress starts here" in response.data


def test_registration_password_rules_and_duplicate_email(client):
    weak = client.post("/register", data={
        "full_name": "New Student", "email": "new@test.local",
        "password": "short", "confirm_password": "short",
    })
    assert weak.status_code == 200
    assert b"8" in weak.data
    mismatch = client.post("/register", data={
        "full_name": "New Student", "email": "new@test.local",
        "password": "GoodPass123", "confirm_password": "OtherPass123",
    })
    assert b"do not match" in mismatch.data
    assert client.post("/register", data={
        "full_name": "New Student", "email": "student@test.local",
        "password": "GoodPass123", "confirm_password": "GoodPass123",
    }).status_code == 200
    created = client.post("/register", data={
        "full_name": "New Student", "email": "new@test.local",
        "password": "GoodPass123", "confirm_password": "GoodPass123",
    }, follow_redirects=True)
    assert created.status_code == 200
    assert b"Hey, New" in created.data


def test_login_logout_and_protected_dashboard(client):
    assert client.get("/dashboard").status_code == 302
    assert b"Taylor" in login(client).data
    assert client.post("/logout", follow_redirects=True).status_code == 200
    assert client.get("/dashboard").status_code == 302
    bad = client.post("/login", data={"email": "student@test.local", "password": "wrong"})
    assert b"incorrect" in bad.data


def test_student_is_denied_admin_and_admin_can_open_dashboard(client):
    login(client)
    assert client.get("/admin").status_code == 403
    client.post("/logout")
    login(client, "admin@test.local", "AdminTest123")
    assert client.get("/admin").status_code == 200
    assert b"Content studio" in client.get("/admin").data


def test_question_search_detail_and_bookmark(client, app):
    login(client)
    with app.app_context():
        question = Question.query.first()
        qid = question.id
        text = question.question_text[:12]
    assert client.get(f"/questions?q={text}").status_code == 200
    assert client.get(f"/questions/{qid}").status_code == 200
    saved = client.post(f"/questions/{qid}", data={"action": "bookmark"}, follow_redirects=True)
    assert saved.status_code == 200
    assert b"Remove bookmark" in saved.data


def test_mock_test_scores_on_server_and_persists_result(client, app):
    login(client)
    with app.app_context():
        test = MockTest.query.first()
        test_id = test.id
        question_rows = list(db.session.get(MockTest, test_id).category.questions[:6])
        correct = question_rows[0].correct_answer
        ids = [question.id for question in question_rows]
    started = client.post(f"/mock-tests/{test_id}/start")
    assert started.status_code == 302
    attempt_id = int(re.search(r"/test-attempts/(\d+)$", started.location).group(1))
    page = client.get(f"/test-attempts/{attempt_id}")
    assert page.status_code == 200
    assert b"Correct answer" not in page.data
    form = {f"q_{qid}": (correct if i == 0 else "") for i, qid in enumerate(ids)}
    response = client.post(f"/test-attempts/{attempt_id}", data=form)
    assert response.status_code == 302
    result = client.get(response.location)
    assert result.status_code == 200
    assert b"17%" in result.data or b"16%" in result.data
    with app.app_context():
        attempt = db.session.get(DBTestAttempt, attempt_id)
        assert attempt.status == "submitted"
        assert attempt.score == 1
        assert attempt.percentage > 0


def test_test_submission_rejects_unknown_question_id(client, app):
    login(client)
    with app.app_context():
        test_id = MockTest.query.first().id
    location = client.post(f"/mock-tests/{test_id}/start").location
    attempt_id = int(re.search(r"/test-attempts/(\d+)$", location).group(1))
    response = client.post(f"/test-attempts/{attempt_id}", data={"q_999999": "A"})
    assert response.status_code == 400


def test_test_auto_submits_when_server_deadline_has_passed(client, app):
    login(client)
    with app.app_context():
        test = MockTest.query.first()
        test_id = test.id
        duration = test.duration_minutes
    location = client.post(f"/mock-tests/{test_id}/start").location
    attempt_id = int(re.search(r"/test-attempts/(\d+)$", location).group(1))
    with app.app_context():
        attempt = db.session.get(DBTestAttempt, attempt_id)
        attempt.started_at = utcnow() - timedelta(minutes=duration + 1)
        db.session.commit()
    response = client.get(f"/test-attempts/{attempt_id}")
    assert response.status_code == 302
    assert f"/test-attempts/{attempt_id}/result" in response.location
    with app.app_context():
        assert db.session.get(DBTestAttempt, attempt_id).status == "submitted"


def test_test_result_is_private(client, app):
    login(client)
    with app.app_context():
        test_id = MockTest.query.first().id
    location = client.post(f"/mock-tests/{test_id}/start").location
    attempt_id = int(re.search(r"/test-attempts/(\d+)$", location).group(1))
    client.post(f"/test-attempts/{attempt_id}", data={})
    client.post("/logout")
    client.post("/register", data={
        "full_name": "Another Student", "email": "other@test.local",
        "password": "OtherPass123", "confirm_password": "OtherPass123",
    })
    assert client.get(f"/test-attempts/{attempt_id}/result").status_code == 404


def test_coding_sample_check_never_claims_full_execution(client, app):
    login(client)
    with app.app_context():
        problem_id = CodingProblem.query.first().id
        expected = db.session.get(CodingProblem, problem_id).sample_output
    result = client.post(f"/coding/{problem_id}", data={
        "code": "print('not executed')", "observed_output": expected,
    }, follow_redirects=True)
    assert result.status_code == 200
    assert b"not executed" in result.data
    assert b"code was not executed" in result.data
    with app.app_context():
        from models import CodingSubmission
        submission = CodingSubmission.query.first()
        assert submission.result_status == "sample_passed"


def test_hr_answer_is_saved_and_marked_practiced(client, app):
    login(client)
    with app.app_context():
        from models import HRQuestion, HRPractice
        question_id = HRQuestion.query.first().id
    response = client.post(f"/hr/{question_id}", data={
        "answer": "My role-focused introduction.", "practiced": "yes",
    }, follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        practice = HRPractice.query.first()
        assert practice.personal_answer == "My role-focused introduction."
        assert practice.is_practiced


def test_profile_can_be_updated_and_password_changed(client, app):
    login(client)
    response = client.post("/profile", data={
        "action": "profile", "full_name": "Taylor Updated",
        "preferred_job_role": "Backend Engineer", "education": "CS",
    }, follow_redirects=True)
    assert b"Profile updated" in response.data
    response = client.post("/profile", data={
        "action": "password", "current_password": "StudentTest123",
        "new_password": "ChangedPass123", "confirm_password": "ChangedPass123",
    }, follow_redirects=True)
    assert b"Password changed" in response.data
    with app.app_context():
        user = User.query.filter_by(email="student@test.local").first()
        assert user.check_password("ChangedPass123")


def test_admin_can_create_question_and_test_validation(client, app):
    login(client, "admin@test.local", "AdminTest123")
    with app.app_context():
        category_id = Category.query.filter_by(name="Python").first().id
        question_id = Question.query.filter_by(category_id=category_id).first().id
    added = client.post("/admin/questions", data={
        "question_text": "What does a generator yield?",
        "category_id": category_id, "question_type": "descriptive",
        "difficulty": "Beginner",
    }, follow_redirects=True)
    assert b"Question created" in added.data
    created_test = client.post("/admin/tests", data={
        "title": "Python Admin Quick Check", "category_id": category_id,
        "duration_minutes": "10", "passing_percentage": "50",
        "question_ids": [str(question_id)],
    }, follow_redirects=True)
    assert b"Mock test created" in created_test.data
    with app.app_context():
        before = MockTest.query.count()
    bad = client.post("/admin/tests", data={
        "title": "Bad duration", "category_id": category_id,
        "duration_minutes": "0", "passing_percentage": "50",
        "question_ids": [str(question_id)],
    }, follow_redirects=True)
    assert b"valid title, category, duration" in bad.data
    with app.app_context():
        assert MockTest.query.count() == before


def test_admin_category_and_question_management(client, app):
    login(client, "admin@test.local", "AdminTest123")
    category = client.post("/admin/categories", data={
        "name": "Interview Skills", "description": "Communication practice",
    }, follow_redirects=True)
    assert b"Category created" in category.data
    with app.app_context():
        category_id = Category.query.filter_by(name="Interview Skills").first().id
    edited = client.post(f"/admin/categories/{category_id}/edit", data={
        "name": "Career Skills", "description": "Career communication",
    }, follow_redirects=True)
    assert b"Category updated" in edited.data
    with app.app_context():
        category_id = Category.query.filter_by(name="Python").first().id
    client.post("/admin/questions", data={
        "question_text": "Temporary question for editing",
        "category_id": category_id, "question_type": "descriptive",
        "difficulty": "Beginner",
    })
    with app.app_context():
        question_id = Question.query.filter_by(
            question_text="Temporary question for editing"
        ).first().id
    updated = client.post(f"/admin/questions/{question_id}/edit", data={
        "question_text": "Edited temporary question",
        "category_id": category_id, "question_type": "descriptive",
        "difficulty": "Intermediate",
    }, follow_redirects=True)
    assert b"Question updated" in updated.data
    deleted = client.post(f"/admin/questions/{question_id}/delete", follow_redirects=True)
    assert b"Question deleted" in deleted.data


def test_admin_disabling_account_invalidates_existing_session(client, app):
    student_client = app.test_client()
    login(student_client)
    login(client, "admin@test.local", "AdminTest123")
    with app.app_context():
        student_id = User.query.filter_by(email="student@test.local").first().id
    response = client.post(f"/admin/users/{student_id}/toggle", follow_redirects=True)
    assert b"Account disabled" in response.data
    assert student_client.get("/dashboard").status_code == 302


def test_recommendations_use_real_score_and_empty_state_is_not_fabricated(client, app):
    login(client)
    empty = client.get("/recommendations")
    assert b"no measured scores" in empty.data.lower()
    with app.app_context():
        test = MockTest.query.first()
        test_id = test.id
    location = client.post(f"/mock-tests/{test_id}/start").location
    attempt_id = int(re.search(r"/test-attempts/(\d+)$", location).group(1))
    client.post(f"/test-attempts/{attempt_id}", data={})
    response = client.get("/recommendations")
    assert response.status_code == 200
    assert b"High priority" in response.data


def test_seed_content_meets_requested_minimums(app):
    with app.app_context():
        assert Category.query.count() >= 10
        assert Question.query.count() >= 60
        assert MockTest.query.count() >= 5
        assert CodingProblem.query.count() >= 15
        from models import HRQuestion
        assert HRQuestion.query.count() >= 20
