from datetime import datetime, timezone
from . import db


# =========================================================
# USER
# =========================================================

class User(db.Model):
    __tablename__ = "user"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(255),
        unique=True,
        nullable=False,
        index=True
    )

    mobile = db.Column(
        db.String(30)
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # admin / trainer / learner
    role = db.Column(
        db.String(30),
        nullable=False,
        default="learner"
    )

    # active / inactive
    status = db.Column(
        db.String(20),
        nullable=False,
        default="active"
    )
    failed_login_attempts = db.Column(
        db.Integer,
        nullable=False,
        default=0
    )

    locked_until = db.Column(
        db.DateTime,
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# TRAINER
# =========================================================

class Trainer(db.Model):
    __tablename__ = "trainer"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    specialization = db.Column(
        db.String(150)
    )

    experience = db.Column(
        db.Integer,
        default=0
    )

    bio = db.Column(
        db.Text,
        default=""
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "trainer_profile",
            uselist=False
        )
    )


# =========================================================
# BATCH
# =========================================================

class Batch(db.Model):
    __tablename__ = "batch"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    start_date = db.Column(
        db.Date
    )

    end_date = db.Column(
        db.Date
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey("trainer.id")
    )

    status = db.Column(
        db.String(20),
        default="active"
    )


# =========================================================
# LEARNER
# =========================================================

class Learner(db.Model):
    __tablename__ = "learner"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        unique=True,
        nullable=False
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("batch.id")
    )

    education = db.Column(
        db.String(200)
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "learner_profile",
            uselist=False
        )
    )


# =========================================================
# COURSE
# =========================================================

class Course(db.Model):
    __tablename__ = "course"

    id = db.Column(
        db.String(80),
        primary_key=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey("trainer.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    level = db.Column(
        db.String(50),
        nullable=False,
        default="Beginner"
    )

    description = db.Column(
        db.Text,
        default=""
    )

    thumbnail = db.Column(
        db.Text,
        default=""
    )

    published = db.Column(
        db.Boolean,
        default=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    trainer = db.relationship(
        "Trainer",
        backref="courses"
    )


# =========================================================
# MODULE
# =========================================================

class Module(db.Model):
    __tablename__ = "module"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    order_no = db.Column(
        db.Integer,
        nullable=False
    )


# =========================================================
# LESSON
# =========================================================

class Lesson(db.Model):
    __tablename__ = "lesson"

    id = db.Column(
        db.String(80),
        primary_key=True
    )

    module_id = db.Column(
        db.Integer,
        db.ForeignKey("module.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    content = db.Column(
        db.Text,
        default=""
    )

    # -----------------------------------------------------
    # LEGACY VIDEO
    # -----------------------------------------------------

    video_url = db.Column(
        db.Text,
        default=""
    )

    # -----------------------------------------------------
    # LEGACY PDF
    # -----------------------------------------------------

    pdf_url = db.Column(
        db.Text,
        default=""
    )

    # -----------------------------------------------------
    # LESSON DURATION
    # -----------------------------------------------------

    duration = db.Column(
        db.String(20),
        default="00:00"
    )

    order_no = db.Column(
        db.Integer,
        nullable=False
    )

    # Multiple uploaded resources
    resources = db.relationship(
        "LessonResource",
        backref="lesson",
        lazy=True,
        cascade="all, delete-orphan"
    )


# =========================================================
# LESSON RESOURCE
# =========================================================

class LessonResource(db.Model):
    __tablename__ = "lesson_resource"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Which lesson this file belongs to
    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=False,
        index=True
    )

    # video / pdf
    resource_type = db.Column(
        db.String(20),
        nullable=False
    )

    # Original file name
    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    # Actual file location
    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    # Optional title displayed in frontend
    title = db.Column(
        db.String(200),
        default=""
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# ENROLLMENT
# =========================================================

class Enrollment(db.Model):
    __tablename__ = "enrollment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    progress = db.Column(
        db.Integer,
        default=0
    )

    status = db.Column(
        db.String(20),
        default="active"
    )

    enrolled_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "learner_id",
            "course_id",
            name="uq_enrollment"
        ),
    )


# =========================================================
# LESSON PROGRESS
# =========================================================

class LessonProgress(db.Model):
    __tablename__ = "lesson_progress"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=False
    )

    completed = db.Column(
        db.Boolean,
        default=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "learner_id",
            "lesson_id",
            name="uq_lesson_progress"
        ),
    )


# =========================================================
# ASSIGNMENT
# =========================================================

class Assignment(db.Model):
    __tablename__ = "assignment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey("trainer.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    due_date = db.Column(
        db.DateTime
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# ASSIGNMENT SUBMISSION
# =========================================================

class AssignmentSubmission(db.Model):
    __tablename__ = "assignment_submission"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    assignment_id = db.Column(
        db.Integer,
        db.ForeignKey("assignment.id"),
        nullable=False
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    submission = db.Column(
        db.Text,
        default=""
    )

    submitted_at = db.Column(
        db.DateTime
    )

    grade = db.Column(
        db.Integer
    )

    feedback = db.Column(
        db.Text,
        default=""
    )


# =========================================================
# QUIZ
# =========================================================

class Quiz(db.Model):
    __tablename__ = "quiz"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    total_marks = db.Column(
        db.Integer,
        default=0
    )

    max_attempts = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    duration_minutes = db.Column(
        db.Integer,
        default=30,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

class QuizAnswer(db.Model):
    __tablename__ = "quiz_answer"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz_attempt.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("question.id"),
        nullable=False
    )

    selected_answer = db.Column(
        db.String(10),
        nullable=True
    )

    is_correct = db.Column(
        db.Boolean,
        default=False
    )

    marks_awarded = db.Column(
        db.Integer,
        default=0
    )

    attempt = db.relationship(
        "QuizAttempt",
        backref=db.backref(
            "answers",
            lazy=True,
            cascade="all, delete-orphan"
        )
    )

    question = db.relationship(
        "Question",
        backref=db.backref(
            "submitted_answers",
            lazy=True
        )
    )

# =========================================================
# QUESTION
# =========================================================

class Question(db.Model):
    __tablename__ = "question"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz.id"),
        nullable=False
    )

    question_text = db.Column(
        db.Text,
        nullable=False
    )

    option_a = db.Column(
        db.String(500)
    )

    option_b = db.Column(
        db.String(500)
    )

    option_c = db.Column(
        db.String(500)
    )

    option_d = db.Column(
        db.String(500)
    )

    correct_answer = db.Column(
        db.String(10)
    )

    marks = db.Column(
        db.Integer,
        default=1
    )


# =========================================================
# QUIZ ATTEMPT
# =========================================================

class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempt"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    quiz_id = db.Column(
        db.Integer,
        db.ForeignKey("quiz.id"),
        nullable=False
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    total = db.Column(
        db.Integer,
        default=0
    )

    started_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    attempted_at = db.Column(
        db.DateTime,
        nullable=True
    )

# =========================================================
# CERTIFICATE
# =========================================================

class Certificate(db.Model):
    __tablename__ = "certificate"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    certificate_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False,
        index=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    start_date = db.Column(
        db.DateTime,
        nullable=False
    )

    end_date = db.Column(
        db.DateTime,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    status = db.Column(
        db.String(20),
        default="valid"
    )

    learner = db.relationship(
        "Learner",
        backref=db.backref(
            "certificates",
            lazy=True
        )
    )

    course = db.relationship(
        "Course",
        backref=db.backref(
            "certificates",
            lazy=True
        )
    )


# =========================================================
# ATTENDANCE
# =========================================================

class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    batch_id = db.Column(
        db.Integer,
        db.ForeignKey("batch.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        nullable=False
    )

    marked_by = db.Column(
        db.Integer,
        db.ForeignKey("user.id")
    )


# =========================================================
# PAYMENT
# =========================================================

class Payment(db.Model):
    __tablename__ = "payment"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    payment_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    payment_method = db.Column(
        db.String(50)
    )

    status = db.Column(
        db.String(20),
        default="pending"
    )


# =========================================================
# INVOICE
# =========================================================

class Invoice(db.Model):
    __tablename__ = "invoice"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    invoice_number = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    amount = db.Column(
        db.Float,
        nullable=False
    )

    invoice_date = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    status = db.Column(
        db.String(20),
        default="unpaid"
    )


# =========================================================
# DISCUSSION / COMMUNITY
# =========================================================

class Discussion(db.Model):
    __tablename__ = "discussion"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# WISHLIST
# =========================================================

class Wishlist(db.Model):
    __tablename__ = "wishlist"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        db.UniqueConstraint(
            "learner_id",
            "course_id",
            name="uq_wishlist"
        ),
    )


# =========================================================
# COURSE DOCUMENT
# =========================================================

class CourseDocument(db.Model):
    __tablename__ = "course_document"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    file_name = db.Column(
        db.String(255),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    uploaded_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    course = db.relationship(
        "Course",
        backref="documents"
    )

# ============================================================
# CODING EXAM MODELS
# ============================================================

class CodingExam(db.Model):
    __tablename__ = "coding_exam"

    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey("trainer.id"),
        nullable=False
    )

    duration = db.Column(db.Integer, default=60)
    total_marks = db.Column(db.Integer, default=0)

    status = db.Column(
        db.String(20),
        default="draft"
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class CodingQuestion(db.Model):
    __tablename__ = "coding_question"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_exam.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    difficulty = db.Column(
        db.String(20),
        default="medium"
    )

    points = db.Column(
        db.Integer,
        default=10
    )

    input_format = db.Column(
        db.Text,
        default=""
    )

    output_format = db.Column(
        db.Text,
        default=""
    )

    constraints = db.Column(
        db.Text,
        default=""
    )

    starter_code = db.Column(
        db.Text,
        default=""
    )

    language = db.Column(
        db.String(30),
        default="python"
    )

    order_index = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )


class CodingTestCase(db.Model):
    __tablename__ = "coding_test_case"

    id = db.Column(db.Integer, primary_key=True)

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_question.id"),
        nullable=False
    )

    input_data = db.Column(
        db.Text,
        default=""
    )

    expected_output = db.Column(
        db.Text,
        nullable=False
    )

    is_sample = db.Column(
        db.Boolean,
        default=False
    )

    order_index = db.Column(
        db.Integer,
        default=0
    )


class CodingSubmission(db.Model):
    __tablename__ = "coding_submission"

    id = db.Column(db.Integer, primary_key=True)

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_exam.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_question.id"),
        nullable=False
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    language = db.Column(
        db.String(30),
        nullable=False
    )

    source_code = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(30),
        default="submitted"
    )

    score = db.Column(
        db.Integer,
        default=0
    )

    total_tests = db.Column(
        db.Integer,
        default=0
    )

    passed_tests = db.Column(
        db.Integer,
        default=0
    )

    execution_time = db.Column(
        db.Float,
        default=0
    )

    submitted_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

# ============================================================
# CODING EXAM PROCTORING / MONITORING MODELS
# ============================================================

class CodingExamSession(db.Model):
    __tablename__ = "coding_exam_session"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_exam.id"),
        nullable=False
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False
    )

    started_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    ended_at = db.Column(
        db.DateTime,
        nullable=True
    )

    status = db.Column(
        db.String(30),
        default="active",
        nullable=False
    )

    camera_enabled = db.Column(
        db.Boolean,
        default=False
    )

    microphone_enabled = db.Column(
        db.Boolean,
        default=False
    )

    warning_count = db.Column(
        db.Integer,
        default=0
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


class CodingExamMonitoringEvent(db.Model):
    __tablename__ = "coding_exam_monitoring_event"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_exam_session.id"),
        nullable=False
    )

    event_type = db.Column(
        db.String(50),
        nullable=False
    )

    message = db.Column(
        db.Text,
        default=""
    )

    event_time = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    metadata_json = db.Column(
        db.Text,
        default=""
    )


class CodingExamScreenshot(db.Model):
    __tablename__ = "coding_exam_screenshot"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    session_id = db.Column(
        db.Integer,
        db.ForeignKey("coding_exam_session.id"),
        nullable=False
    )

    file_path = db.Column(
        db.String(500),
        nullable=False
    )

    captured_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

# ============================================================
# LEARNING TIME
# ============================================================

class LearningTime(db.Model):
    __tablename__ = "learning_time"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    learner_id = db.Column(
        db.Integer,
        db.ForeignKey("learner.id"),
        nullable=False,
        index=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=True,
        index=True
    )

    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=True,
        index=True
    )

    duration_seconds = db.Column(
        db.Integer,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )