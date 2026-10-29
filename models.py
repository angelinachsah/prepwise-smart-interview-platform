from datetime import datetime, timezone

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    preferred_job_role = db.Column(db.String(100), default="")
    education = db.Column(db.String(120), default="")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    bookmarks = db.relationship("Bookmark", cascade="all, delete-orphan", backref="user")
    attempts = db.relationship("TestAttempt", cascade="all, delete-orphan", backref="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    description = db.Column(db.String(240), nullable=False, default="")
    questions = db.relationship("Question", backref="category", lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(20), nullable=False, default="descriptive")
    difficulty = db.Column(db.String(20), nullable=False, default="Beginner")
    option_a = db.Column(db.String(300))
    option_b = db.Column(db.String(300))
    option_c = db.Column(db.String(300))
    option_d = db.Column(db.String(300))
    correct_answer = db.Column(db.String(1))
    explanation = db.Column(db.Text, nullable=False, default="")
    tags = db.Column(db.String(240), nullable=False, default="")
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class Bookmark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    __table_args__ = (UniqueConstraint("user_id", "question_id", name="uq_bookmark_user_question"),)


class QuestionAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    is_correct = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class MockTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False, default="")
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=20)
    passing_percentage = db.Column(db.Integer, nullable=False, default=50)
    is_published = db.Column(db.Boolean, nullable=False, default=True)
    category = db.relationship("Category")
    question_links = db.relationship("TestQuestion", cascade="all, delete-orphan", backref="test")

    @property
    def question_count(self):
        return len(self.question_links)


class TestQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey("mock_test.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    marks = db.Column(db.Integer, nullable=False, default=1)
    question = db.relationship("Question")
    __table_args__ = (UniqueConstraint("test_id", "question_id", name="uq_test_question"),)


class TestAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = db.Column(db.Integer, db.ForeignKey("mock_test.id"), nullable=False)
    started_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    submitted_at = db.Column(db.DateTime(timezone=True))
    score = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default="in_progress")
    time_taken_seconds = db.Column(db.Integer)
    test = db.relationship("MockTest")
    answers = db.relationship("AttemptAnswer", cascade="all, delete-orphan", backref="attempt")


class AttemptAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("test_attempt.id", ondelete="CASCADE"), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey("question.id"), nullable=False)
    selected_answer = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    marks_awarded = db.Column(db.Integer, nullable=False, default=0)
    question = db.relationship("Question")
    __table_args__ = (UniqueConstraint("attempt_id", "question_id", name="uq_answer_attempt_question"),)


class CodingProblem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)
    difficulty = db.Column(db.String(20), nullable=False, default="Beginner")
    input_format = db.Column(db.Text, nullable=False, default="")
    output_format = db.Column(db.Text, nullable=False, default="")
    sample_input = db.Column(db.Text, nullable=False, default="")
    sample_output = db.Column(db.Text, nullable=False, default="")
    constraints = db.Column(db.Text, nullable=False, default="")
    hints = db.Column(db.Text, nullable=False, default="")
    solution_explanation = db.Column(db.Text, nullable=False, default="")
    test_cases_json = db.Column(db.Text, nullable=False, default="[]")


class CodingSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    problem_id = db.Column(db.Integer, db.ForeignKey("coding_problem.id", ondelete="CASCADE"), nullable=False)
    submitted_code = db.Column(db.Text, nullable=False)
    result_status = db.Column(db.String(30), nullable=False)
    test_cases_passed = db.Column(db.Integer, nullable=False, default=0)
    test_cases_total = db.Column(db.Integer, nullable=False, default=1)
    submitted_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)


class HRQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(300), unique=True, nullable=False)
    example_answer = db.Column(db.Text, nullable=False)
    answer_tips = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), nullable=False, default="General")


class HRPractice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    hr_question_id = db.Column(db.Integer, db.ForeignKey("hr_question.id", ondelete="CASCADE"), nullable=False)
    personal_answer = db.Column(db.Text, nullable=False, default="")
    is_practiced = db.Column(db.Boolean, nullable=False, default=False)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)
    question = db.relationship("HRQuestion")
    __table_args__ = (UniqueConstraint("user_id", "hr_question_id", name="uq_hr_user_question"),)


class Recommendation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"))
    title = db.Column(db.String(180), nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(20), nullable=False)
    suggested_action = db.Column(db.String(240), nullable=False)
    is_completed = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    category = db.relationship("Category")


class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    activity_type = db.Column(db.String(40), nullable=False)
    reference_id = db.Column(db.Integer)
    score = db.Column(db.Float)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
