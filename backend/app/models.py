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

    role = db.Column(
        db.String(30),
        nullable=False,
        default="learner"
    )

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

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=True
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

    course_fee = db.Column(
        db.Float,
        nullable=False,
        default=0
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
# AUDIT LOG
# =========================================================

class AuditLog(db.Model):
    __tablename__ = "audit_log"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        index=True
    )

    action = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    entity_type = db.Column(
        db.String(100),
        nullable=False,
        index=True
    )

    entity_id = db.Column(
        db.String(100),
        nullable=True
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    ip_address = db.Column(
        db.String(45),
        nullable=True
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "audit_logs",
            lazy=True
        )
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

    video_url = db.Column(
        db.Text,
        default=""
    )

    pdf_url = db.Column(
        db.Text,
        default=""
    )

    duration = db.Column(
        db.String(20),
        default="00:00"
    )

    order_no = db.Column(
        db.Integer,
        nullable=False
    )

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

    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=False,
        index=True
    )

    resource_type = db.Column(
        db.String(20),
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

    course_fee = db.Column(
        db.Float,
        nullable=False,
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
# =========================================================
# LESSON NOTES
# =========================================================

class LessonNote(db.Model):
    __tablename__ = "lesson_note"

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

    lesson_id = db.Column(
        db.String(80),
        db.ForeignKey("lesson.id"),
        nullable=False,
        index=True
    )

    content = db.Column(
        db.Text,
        nullable=False,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    __table_args__ = (
        db.UniqueConstraint(
            "learner_id",
            "lesson_id",
            name="uq_lesson_note"
        ),
    )


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
# QUIZ ANSWER
# =========================================================

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

    enrollment_id = db.Column(
        db.Integer,
        db.ForeignKey("enrollment.id"),
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

    # Razorpay transaction identifiers
    # Nullable to preserve existing payment records.

    razorpay_order_id = db.Column(
        db.String(100),
        unique=True,
        nullable=True,
        index=True
    )

    razorpay_payment_id = db.Column(
        db.String(100),
        unique=True,
        nullable=True,
        index=True
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


# =========================================================
# CODING EXAM
# =========================================================

class CodingExam(db.Model):
    __tablename__ = "coding_exam"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
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

    duration = db.Column(
        db.Integer,
        default=60
    )

    total_marks = db.Column(
        db.Integer,
        default=0
    )

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


# =========================================================
# CODING QUESTION
# =========================================================

class CodingQuestion(db.Model):
    __tablename__ = "coding_question"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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


# =========================================================
# CODING TEST CASE
# =========================================================

class CodingTestCase(db.Model):
    __tablename__ = "coding_test_case"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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


# =========================================================
# CODING SUBMISSION
# =========================================================

class CodingSubmission(db.Model):
    __tablename__ = "coding_submission"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

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


# =========================================================
# CODING EXAM SESSION
# =========================================================

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


# =========================================================
# CODING EXAM MONITORING EVENT
# =========================================================

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


# =========================================================
# CODING EXAM SCREENSHOT
# =========================================================

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


# =========================================================
# LEARNING TIME
# =========================================================

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


# =========================================================
# MIXED EXAMS / QUESTION BANK / INVITES
# =========================================================

class MixedExam(db.Model):
    __tablename__ = "mixed_exam"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
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

    duration_minutes = db.Column(
        db.Integer,
        default=60,
        nullable=False
    )

    total_marks = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="draft",
        nullable=False
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


# =========================================================
# MIXED EXAM SECTION
# =========================================================

class MixedExamSection(db.Model):
    __tablename__ = "mixed_exam_section"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam.id"),
        nullable=False
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    section_type = db.Column(
        db.String(20),
        nullable=False
    )

    order_index = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    marks = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )


# =========================================================
# QUESTION BANK
# =========================================================

class QuestionBank(db.Model):
    __tablename__ = "question_bank"

    id = db.Column(
        db.Integer,
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

    description = db.Column(
        db.Text,
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# QUESTION BANK ITEM
# =========================================================

class QuestionBankItem(db.Model):
    __tablename__ = "question_bank_item"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    bank_id = db.Column(
        db.Integer,
        db.ForeignKey("question_bank.id"),
        nullable=False
    )

    question_type = db.Column(
        db.String(20),
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

    coding_description = db.Column(
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

    difficulty = db.Column(
        db.String(20),
        default="medium"
    )

    marks = db.Column(
        db.Integer,
        default=1
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# MIXED EXAM QUESTION
# =========================================================

class MixedExamQuestion(db.Model):
    __tablename__ = "mixed_exam_question"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    section_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam_section.id"),
        nullable=False
    )

    question_type = db.Column(
        db.String(20),
        nullable=False
    )

    question_bank_item_id = db.Column(
        db.Integer,
        db.ForeignKey("question_bank_item.id"),
        nullable=True
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

    coding_description = db.Column(
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

    marks = db.Column(
        db.Integer,
        default=1
    )

    order_index = db.Column(
        db.Integer,
        default=0
    )


# =========================================================
# MIXED EXAM INVITE
# =========================================================

class MixedExamInvite(db.Model):
    __tablename__ = "mixed_exam_invite"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam.id"),
        nullable=False
    )

    invite_code = db.Column(
        db.String(80),
        unique=True,
        nullable=False,
        index=True
    )

    candidate_name = db.Column(
        db.String(200)
    )

    candidate_email = db.Column(
        db.String(255)
    )

    expires_at = db.Column(
        db.DateTime
    )

    max_attempts = db.Column(
        db.Integer,
        default=1,
        nullable=False
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )


# =========================================================
# MIXED EXAM ATTEMPT
# =========================================================

class MixedExamAttempt(db.Model):
    __tablename__ = "mixed_exam_attempt"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    exam_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam.id"),
        nullable=False
    )

    invite_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam_invite.id"),
        nullable=False
    )

    candidate_name = db.Column(
        db.String(200)
    )

    candidate_email = db.Column(
        db.String(255)
    )

    status = db.Column(
        db.String(20),
        default="in_progress",
        nullable=False
    )

    started_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

    submitted_at = db.Column(
        db.DateTime
    )

    score = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    total_marks = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )


# =========================================================
# MIXED EXAM ANSWER
# =========================================================

class MixedExamAnswer(db.Model):
    __tablename__ = "mixed_exam_answer"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    attempt_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam_attempt.id"),
        nullable=False
    )

    question_id = db.Column(
        db.Integer,
        db.ForeignKey("mixed_exam_question.id"),
        nullable=False
    )

    selected_answer = db.Column(
        db.String(10)
    )

    source_code = db.Column(
        db.Text
    )

    language = db.Column(
        db.String(30)
    )

    is_correct = db.Column(
        db.Boolean
    )

    marks_awarded = db.Column(
        db.Integer,
        default=0,
        nullable=False
    )

    submitted_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc)
    )

# =========================================================
# CALENDAR EVENT
# =========================================================

class CalendarEvent(db.Model):
    __tablename__ = "calendar_event"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    course_id = db.Column(
        db.String(80),
        db.ForeignKey("course.id"),
        nullable=False,
        index=True
    )

    trainer_id = db.Column(
        db.Integer,
        db.ForeignKey("trainer.id"),
        nullable=True,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        default=""
    )

    event_type = db.Column(
        db.String(30),
        nullable=False,
        default="live_class"
    )

    start_at = db.Column(
        db.DateTime,
        nullable=False
    )

    end_at = db.Column(
        db.DateTime,
        nullable=True
    )

    meeting_url = db.Column(
        db.Text,
        default=""
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

    course = db.relationship(
        "Course",
        backref="calendar_events"
    )

    trainer = db.relationship(
        "Trainer",
        backref="calendar_events"
    )

# =========================================================
# NOTIFICATION
# =========================================================

class Notification(db.Model):
    __tablename__ = "notification"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False,
        index=True
    )

    title = db.Column(
        db.String(200),
        nullable=False
    )

    message = db.Column(
        db.Text,
        nullable=False
    )

    notification_type = db.Column(
        db.String(50),
        nullable=False,
        default="general"
    )

    is_read = db.Column(
        db.Boolean,
        default=False,
        nullable=False
    )

    link = db.Column(
        db.String(500),
        default=""
    )

    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    read_at = db.Column(
        db.DateTime,
        nullable=True
    )

    user = db.relationship(
        "User",
        backref="notifications"
    )