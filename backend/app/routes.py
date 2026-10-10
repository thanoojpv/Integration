from flask import (
    Blueprint,
    request,
    jsonify,
    send_file,
    send_from_directory,
    current_app,
)
import csv
import os
import shutil
import secrets
import random
import json
import uuid
import hmac
import hashlib
import razorpay
from datetime import datetime, timedelta, timezone
from io import BytesIO

import qrcode

from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)

from werkzeug.utils import secure_filename

from . import db ,limiter

from .models import (
    User,
    Trainer,
    Learner,
    LearningTime,
    Batch,
    Course,
    CourseDocument,
    Module,
    Lesson,
    Enrollment,
    Assignment,
    AssignmentSubmission,
    Quiz,
    Question,
    QuizAttempt,
    QuizAnswer,
    CodingExam,
    CodingQuestion,
    CodingTestCase,
    CodingSubmission,
    Certificate,
    CodingExamSession,
    CodingExamMonitoringEvent,
    CodingExamScreenshot,
    Attendance,
    Payment,
    Invoice,
    LessonProgress,
    LessonNote,
    LessonResource,
    Wishlist,
    Discussion,
    MixedExam,
    MixedExamSection,
    QuestionBank,
    QuestionBankItem,
    MixedExamQuestion,
    MixedExamInvite,
    MixedExamAttempt,
    MixedExamAnswer,
    CalendarEvent,
    Notification,
    AuditLog,
)
from .code_runner.runner import run_code

from .auth import (
    make_token,
    login_user,
    create_password_hash,
    token_required,
    role_required,
)


api = Blueprint("api", __name__)


# =========================================================
# PROJECT / UPLOAD CONFIGURATION
# =========================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
    )
)

UPLOAD_ROOT = os.path.join(
    PROJECT_ROOT,
    "uploads",
)

VIDEO_UPLOAD_ROOT = os.path.join(
    UPLOAD_ROOT,
    "videos",
)

PDF_UPLOAD_ROOT = os.path.join(
    UPLOAD_ROOT,
    "documents",
)

COURSE_DOCUMENT_ROOT = os.path.join(
    UPLOAD_ROOT,
    "course_documents",
)

os.makedirs(
    VIDEO_UPLOAD_ROOT,
    exist_ok=True,
)

os.makedirs(
    PDF_UPLOAD_ROOT,
    exist_ok=True,
)

os.makedirs(
    COURSE_DOCUMENT_ROOT,
    exist_ok=True,
)


ALLOWED_VIDEO_EXTENSIONS = {
    "mp4",
    "webm",
    "mov",
    "avi",
    "mkv",
}

ALLOWED_DOCUMENT_EXTENSIONS = {
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "txt",
}


# =========================================================
# BASIC HELPERS
# =========================================================

def create_audit_log(
    user,
    action,
    entity_type,
    entity_id=None,
    description="",
):
    audit_log = AuditLog(
        user_id=user.id if user else None,
        action=action,
        entity_type=entity_type,
        entity_id=str(entity_id) if entity_id is not None else None,
        description=description,
        ip_address=request.remote_addr,
    )

    db.session.add(audit_log)

def allowed_extension(filename, allowed):
    return bool(
        filename
        and "."
        in filename
        and filename.rsplit(
            ".",
            1,
        )[1].lower()
        in allowed
    )


def user_json(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "mobile": user.mobile,
        "role": user.role,
        "status": user.status,
        "created_at": (
            user.created_at.isoformat()
            if user.created_at
            else None
        ),
    }


def trainer_json(trainer):
    return {
        "id": trainer.id,
        "user_id": trainer.user_id,
        "name": (
            trainer.user.name
            if trainer.user
            else None
        ),
        "email": (
            trainer.user.email
            if trainer.user
            else None
        ),
        "mobile": (
            trainer.user.mobile
            if trainer.user
            else None
        ),
        "specialization": trainer.specialization,
        "experience": trainer.experience,
        "bio": trainer.bio,
        "status": trainer.status,
    }


def learner_json(learner):
    return {
        "id": learner.id,
        "user_id": learner.user_id,
        "name": (
            learner.user.name
            if learner.user
            else None
        ),
        "email": (
            learner.user.email
            if learner.user
            else None
        ),
        "mobile": (
            learner.user.mobile
            if learner.user
            else None
        ),
        "education": learner.education,
        "batch_id": learner.batch_id,
        "status": learner.status,
    }


def parse_datetime(value):
    if not value:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(
            str(value).replace(
                "Z",
                "+00:00",
            )
        )
    except (
        ValueError,
        TypeError,
    ):
        return None


# =========================================================
# RESOURCE HELPERS
# =========================================================

def resource_url(
    lesson_id,
    resource_type,
    filename,
):
    return (
        f"/api/lessons/"
        f"{lesson_id}/resources/"
        f"{resource_type}/"
        f"{filename}"
    )


def resource_folder(
    lesson_id,
    resource_type,
):
    root = (
        VIDEO_UPLOAD_ROOT
        if resource_type == "video"
        else PDF_UPLOAD_ROOT
    )

    folder = os.path.join(
        root,
        secure_filename(
            str(lesson_id)
        ),
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )

    return folder


def lesson_resource_list(lesson_id):
    resources = []

    for resource_type, root in [
        ("video", VIDEO_UPLOAD_ROOT),
        ("pdf", PDF_UPLOAD_ROOT),
    ]:
        folder = os.path.join(
            root,
            secure_filename(
                str(lesson_id)
            ),
        )

        if not os.path.isdir(folder):
            continue

        for filename in sorted(
            os.listdir(folder)
        ):
            file_path = os.path.join(
                folder,
                filename,
            )

            if not os.path.isfile(file_path):
                continue

            resources.append({
                "type": resource_type,
                "fileName": filename,
                "url": resource_url(
                    lesson_id,
                    resource_type,
                    filename,
                ),
            })

    return resources


def course_document_folder(course_id):
    folder = os.path.join(
        COURSE_DOCUMENT_ROOT,
        secure_filename(
            str(course_id)
        ),
    )

    os.makedirs(
        folder,
        exist_ok=True,
    )

    return folder


def course_document_url(
    course_id,
    filename,
):
    return (
        f"/api/courses/"
        f"{course_id}/documents/"
        f"{filename}"
    )


# =========================================================
# COURSE JSON
# =========================================================

def course_json(
    course,
    progress=0,
):
    lesson_count = (
        Lesson.query
        .join(
            Module,
            Lesson.module_id == Module.id,
        )
        .filter(
            Module.course_id == course.id,
        )
        .count()
    )

    completed_lessons = (
        round(
            lesson_count
            * progress
            / 100
        )
        if lesson_count
        else 0
    )

    return {
        "id": course.id,
        "title": course.title,
        "trainer_id": course.trainer_id,
        "trainer": (
            course.trainer.user.name
            if course.trainer
            and course.trainer.user
            else None
        ),
        "level": course.level,
        "description": course.description,
        "thumbnail": course.thumbnail,
        "published": course.published,

        "course_fee": float(
            course.course_fee or 0
        ),
        "progress": progress,
        "totalLessons": lesson_count,
        "lessons": (
            f"{completed_lessons}/"
            f"{lesson_count} Lessons"
            if lesson_count
            else "0/0 Lessons"
        ),
    }


# =========================================================
# LEARNING TIME
# =========================================================

def calculate_learning_time(learner_id):
    rows = (
        db.session.query(
            Lesson.id,
            Lesson.duration
        )
        .join(
            LessonProgress,
            LessonProgress.lesson_id == Lesson.id
        )
        .join(
            Module,
            Lesson.module_id == Module.id
        )
        .join(
            Enrollment,
            db.and_(
                Enrollment.course_id == Module.course_id,
                Enrollment.learner_id == learner_id,
                Enrollment.status == "active",
            )
        )
        .filter(
            LessonProgress.learner_id == learner_id,
            LessonProgress.completed.is_(True),
        )
        .distinct()
        .all()
    )

    total_seconds = 0

    for lesson_id, duration in rows:
        if not duration:
            continue

        try:
            parts = [
                int(value)
                for value in str(duration).split(":")
            ]

            if len(parts) == 2:
                minutes, seconds = parts
                total_seconds += (
                    minutes * 60
                    + seconds
                )

            elif len(parts) == 3:
                hours, minutes, seconds = parts
                total_seconds += (
                    hours * 3600
                    + minutes * 60
                    + seconds
                )

        except (ValueError, TypeError):
            continue

    total_minutes = total_seconds // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60

    return {
        "hours": hours,
        "minutes": minutes,
        "totalMinutes": total_minutes,
        "formatted": f"{hours}h {minutes}m",
    }


# =========================================================
# ASSIGNMENT JSON
# =========================================================

def assignment_json(assignment):
    return {
        "id": assignment.id,
        "course_id": assignment.course_id,
        "title": assignment.title,
        "description": getattr(
            assignment,
            "description",
            "",
        ),
        "due_date": (
            assignment.due_date.isoformat()
            if getattr(
                assignment,
                "due_date",
                None,
            )
            else None
        ),
    }


# =========================================================
# QUIZ JSON
# =========================================================

def quiz_json(quiz):
    question_count = (
        Question.query
        .filter_by(
            quiz_id=quiz.id,
        )
        .count()
    )

    total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    Question.marks
                ),
                0,
            )
        )
        .filter(
            Question.quiz_id == quiz.id
        )
        .scalar()
        or 0
    )

    return {
        "id": quiz.id,
        "course_id": quiz.course_id,
        "title": quiz.title,
        "description": quiz.description,
        "total_marks": int(total_marks),
        "question_count": question_count,
    }


# =========================================================
# HEALTH
# =========================================================

@api.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Devsprint LMS Backend",
        "timestamp": (
            datetime.now(timezone.utc).isoformat()
            + "Z"
        ),
    })


# =========================================================
# AUTH - REGISTER
# =========================================================

@api.post("/auth/register")
def register():
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get(
        "password",
        "",
    )

    mobile = str(
        data.get("mobile", "")
    ).strip()

    if not name or not email or not password:
        return jsonify({
            "error":
                "Name, email and password are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error":
                "Password must be at least 8 characters"
        }), 400

    if User.query.filter_by(
        email=email
    ).first():
        return jsonify({
            "error":
                "Email already registered"
        }), 409

    user = User(
        name=name,
        email=email,
        mobile=mobile,
        password_hash=
            create_password_hash(
                password
            ),
        role="learner",
        status="active",
    )

    db.session.add(user)
    db.session.flush()

    learner = Learner(
        user_id=user.id,
        education=data.get(
            "education",
            "",
        ),
        batch_id=data.get(
            "batch_id"
        ),
        status="active",
    )

    db.session.add(learner)
    db.session.commit()

    return jsonify({
        "message":
            "Registration successful",
        "user":
            user_json(user),
        "token":
            make_token(user),
    }), 201


# =========================================================
# AUTH - LOGIN
# =========================================================

@api.post("/auth/login")
@limiter.limit("10 per minute")
def login():
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get(
        "password",
        "",
    )

    user = login_user(
        email,
        password,
    )

    if not user:
        return jsonify({
            "error":
                "Invalid email or password"
        }), 401

    if user.status != "active":
        return jsonify({
            "error":
                "Your account is inactive"
        }), 403

    requested_role = data.get("role")

    if (
        requested_role
        and requested_role != user.role
    ):
        return jsonify({
            "error":
                f"This account is registered as {user.role}"
        }), 403

    return jsonify({
        "message":
            "Login successful",
        "user":
            user_json(user),
        "token":
            make_token(user),
    })


# =========================================================
# AUTH - CURRENT USER
# =========================================================

@api.get("/auth/me")
@token_required
def me(user):
    return jsonify({
        "user":
            user_json(user)
    })


# =========================================================
# ADMIN - DASHBOARD
# =========================================================

@api.get("/admin/dashboard")
@role_required("admin")
def admin_dashboard(user):
    return jsonify({
        "user":
            user_json(user),
        "stats": {
            "totalUsers":
                User.query.count(),
            "totalTrainers":
                Trainer.query.count(),
            "totalLearners":
                Learner.query.count(),
            "totalAdmins":
                User.query.filter_by(
                    role="admin"
                ).count(),
            "activeUsers":
                User.query.filter_by(
                    status="active"
                ).count(),
            "totalCourses":
                Course.query.count(),
            "totalBatches":
                Batch.query.count(),
            "totalCertificates":
                Certificate.query.count(),
            "totalPayments":
                Payment.query.count(),
        },
    })

# =========================================================
# ADMIN - REPORTS & ANALYTICS
# =========================================================

@api.get("/admin/reports/overview")
@role_required("admin")
def admin_reports_overview(user):

    # -----------------------------------------------------
    # USER STATISTICS
    # -----------------------------------------------------

    total_users = User.query.count()

    total_learners = Learner.query.count()

    total_trainers = Trainer.query.count()

    active_users = User.query.filter_by(
        status="active"
    ).count()

    inactive_users = User.query.filter_by(
        status="inactive"
    ).count()

    # -----------------------------------------------------
    # COURSE STATISTICS
    # -----------------------------------------------------

    total_courses = Course.query.count()

    published_courses = Course.query.filter_by(
        published=True
    ).count()

    unpublished_courses = Course.query.filter_by(
        published=False
    ).count()

    # -----------------------------------------------------
    # ENROLLMENT STATISTICS
    # -----------------------------------------------------

    total_enrollments = Enrollment.query.count()

    active_enrollments = Enrollment.query.filter_by(
        status="active"
    ).count()

    payment_pending_enrollments = (
        Enrollment.query
        .filter_by(status="payment_pending")
        .count()
    )

    # -----------------------------------------------------
    # PAYMENT STATISTICS
    # -----------------------------------------------------

    total_payments = Payment.query.count()

    paid_payments = Payment.query.filter_by(
        status="paid"
    ).count()

    pending_payments = Payment.query.filter_by(
        status="pending"
    ).count()

    failed_payments = Payment.query.filter_by(
        status="failed"
    ).count()

    # -----------------------------------------------------
    # REVENUE
    # -----------------------------------------------------

    total_revenue = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter(
            Payment.status == "paid"
        )
        .scalar()
    )

    pending_revenue = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter(
            Payment.status == "pending"
        )
        .scalar()
    )

    # -----------------------------------------------------
    # INVOICE STATISTICS
    # -----------------------------------------------------

    total_invoices = Invoice.query.count()

    paid_invoices = Invoice.query.filter_by(
        status="paid"
    ).count()

    unpaid_invoices = Invoice.query.filter_by(
        status="unpaid"
    ).count()

    # -----------------------------------------------------
    # CERTIFICATE STATISTICS
    # -----------------------------------------------------

    total_certificates = Certificate.query.count()

    valid_certificates = Certificate.query.filter_by(
        status="valid"
    ).count()

    # -----------------------------------------------------
    # ENROLLMENT PROGRESS
    # -----------------------------------------------------

    average_progress = (
        db.session.query(
            db.func.coalesce(
                db.func.avg(
                    Enrollment.progress
                ),
                0
            )
        )
        .scalar()
    )

    completed_enrollments = (
        Enrollment.query
        .filter(
            Enrollment.progress >= 100
        )
        .count()
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return jsonify({

        "users": {
            "total": total_users,
            "learners": total_learners,
            "trainers": total_trainers,
            "active": active_users,
            "inactive": inactive_users,
        },

        "courses": {
            "total": total_courses,
            "published": published_courses,
            "unpublished": unpublished_courses,
        },

        "enrollments": {
            "total": total_enrollments,
            "active": active_enrollments,
            "payment_pending":
                payment_pending_enrollments,
            "completed":
                completed_enrollments,
        },

        "payments": {
            "total": total_payments,
            "paid": paid_payments,
            "pending": pending_payments,
            "failed": failed_payments,
        },

        "revenue": {
            "total_paid":
                float(total_revenue or 0),
            "pending":
                float(pending_revenue or 0),
        },

        "invoices": {
            "total": total_invoices,
            "paid": paid_invoices,
            "unpaid": unpaid_invoices,
        },

        "certificates": {
            "total": total_certificates,
            "valid": valid_certificates,
        },

        "progress": {
            "average":
                round(
                    float(
                        average_progress or 0
                    ),
                    2
                ),
            "completed_enrollments":
                completed_enrollments,
        },

    }), 200

# =========================================================
# ADMIN - USERS
# =========================================================

@api.get("/admin/users")
@role_required("admin")
def admin_users(user):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(int(request.args.get("limit", 20)), 1),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        User.query
        .order_by(
            User.created_at.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    return jsonify({
        "users": [
            user_json(item)
            for item in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    })


@api.put("/admin/users/<int:user_id>/status")
@role_required("admin")
def admin_update_user_status(
    user,
    user_id,
):
    target = User.query.get_or_404(
        user_id
    )

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    status = data.get("status")

    if status not in (
        "active",
        "inactive",
    ):
        return jsonify({
            "error":
                "Status must be active or inactive"
        }), 400

    target.status = status
    db.session.commit()

    return jsonify({
        "message":
            "User status updated",
        "user":
            user_json(target),
    })


@api.delete("/admin/users/<int:user_id>")
@role_required("admin")
def admin_delete_user(
    user,
    user_id,
):
    target = User.query.get_or_404(
        user_id
    )

    if target.id == user.id:
        return jsonify({
            "error":
                "Admin cannot delete their own account"
        }), 400

    target.status = "inactive"
    db.session.commit()

    return jsonify({
        "message":
            "User deactivated successfully",
        "user":
            user_json(target),
    })


# =========================================================
# ADMIN - CREATE TRAINER
# =========================================================

@api.post("/admin/trainers")
@role_required("admin")
def admin_create_trainer(user):
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get(
        "password",
        "",
    )

    if (
        not name
        or not email
        or len(password) < 8
    ):
        return jsonify({
            "error":
                "Name, email and password of at least 8 characters are required"
        }), 400

    if User.query.filter_by(
        email=email
    ).first():
        return jsonify({
            "error":
                "An account with this email already exists"
        }), 409

    trainer_user = User(
        name=name,
        email=email,
        mobile=data.get(
            "mobile",
            "",
        ),
        role="trainer",
        status="active",
        password_hash=
            create_password_hash(
                password
            ),
    )

    db.session.add(trainer_user)
    db.session.flush()

    try:
        experience = int(
            data.get(
                "experience",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        experience = 0

    trainer = Trainer(
        user_id=trainer_user.id,
        specialization=data.get(
            "specialization",
            "",
        ),
        experience=experience,
        bio=data.get(
            "bio",
            "",
        ),
        status="active",
    )

    db.session.add(trainer)
    db.session.commit()

    return jsonify({
        "message":
            "Trainer created successfully",
        "trainer":
            trainer_json(trainer),
    }), 201


# =========================================================
# ADMIN - TRAINERS
# =========================================================

@api.get("/admin/trainers")
@role_required("admin")
def admin_trainers(user):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(int(request.args.get("limit", 20)), 1),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Trainer.query
        .order_by(Trainer.id.asc())
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    return jsonify({
        "trainers": [
            trainer_json(item)
            for item in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    })


@api.get("/admin/trainers/<int:trainer_id>")
@role_required("admin")
def admin_get_trainer(
    user,
    trainer_id,
):
    trainer = Trainer.query.get_or_404(
        trainer_id
    )

    return jsonify({
        "trainer":
            trainer_json(trainer)
    })


@api.put("/admin/trainers/<int:trainer_id>")
@role_required("admin")
def admin_update_trainer(
    user,
    trainer_id,
):
    trainer = Trainer.query.get_or_404(
        trainer_id
    )

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "name" in data:
        trainer.user.name = data["name"]

    if "email" in data:
        trainer.user.email = (
            str(data["email"])
            .strip()
            .lower()
        )

    if "mobile" in data:
        trainer.user.mobile = data["mobile"]

    if "specialization" in data:
        trainer.specialization = (
            data["specialization"]
        )

    if "experience" in data:
        try:
            trainer.experience = int(
                data["experience"]
            )
        except (
            TypeError,
            ValueError,
        ):
            trainer.experience = 0

    if "bio" in data:
        trainer.bio = data["bio"]

    if "status" in data:
        trainer.status = data["status"]

    db.session.commit()

    return jsonify({
        "message":
            "Trainer updated successfully",
        "trainer":
            trainer_json(trainer),
    })


@api.delete("/admin/trainers/<int:trainer_id>")
@role_required("admin")
def admin_delete_trainer(
    user,
    trainer_id,
):
    trainer = Trainer.query.get_or_404(
        trainer_id
    )

    trainer.status = "inactive"

    if trainer.user:
        trainer.user.status = "inactive"

    db.session.commit()

    return jsonify({
        "message":
            "Trainer deactivated successfully"
    })


# =========================================================
# ADMIN - CREATE LEARNER
# =========================================================

@api.post("/admin/learners")
@role_required("admin")
def admin_create_learner(user):
    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    name = str(
        data.get("name", "")
    ).strip()

    email = str(
        data.get("email", "")
    ).strip().lower()

    password = data.get(
        "password",
        "",
    )

    if (
        not name
        or not email
        or len(password) < 8
    ):
        return jsonify({
            "error":
                "Name, email and password of at least 8 characters are required"
        }), 400

    if User.query.filter_by(
        email=email
    ).first():
        return jsonify({
            "error":
                "An account with this email already exists"
        }), 409

    learner_user = User(
        name=name,
        email=email,
        mobile=data.get(
            "mobile",
            "",
        ),
        role="learner",
        status="active",
        password_hash=
            create_password_hash(
                password
            ),
    )

    db.session.add(learner_user)
    db.session.flush()

    learner = Learner(
        user_id=learner_user.id,
        education=data.get(
            "education",
            "",
        ),
        batch_id=data.get(
            "batch_id"
        ),
        status="active",
    )

    db.session.add(learner)
    db.session.commit()

    return jsonify({
        "message":
            "Learner created successfully",
        "learner":
            learner_json(learner),
    }), 201

# =========================================================
# ADMIN - CSV TEMPLATE FOR LEARNER IMPORT
# =========================================================

@api.get("/admin/learners/import-csv/template")
@role_required("admin")
def admin_learners_csv_template(user):
    output = BytesIO()

    content = (
        "name,email,password,mobile,education\n"
        "John Doe,john@example.com,Welcome123,+919999999999,B.Tech\n"
    )

    output.write(content.encode("utf-8"))
    output.seek(0)

    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name="learner_import_template.csv",
    )

# =========================================================
# ADMIN - BULK IMPORT LEARNERS FROM CSV
# =========================================================

@api.post("/admin/learners/import-csv")
@role_required("admin")
def admin_import_learners_csv(user):
    if "file" not in request.files:
        return jsonify({
            "error": "CSV file is required"
        }), 400

    file = request.files["file"]

    if not file.filename:
        return jsonify({
            "error": "CSV file is required"
        }), 400

    if not file.filename.lower().endswith(".csv"):
        return jsonify({
            "error": "Only CSV files are allowed"
        }), 400

    try:
        content = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return jsonify({
            "error": "CSV file must use UTF-8 encoding"
        }), 400

    reader = csv.DictReader(content.splitlines())

    required_columns = {
        "name",
        "email",
        "password",
    }

    if not reader.fieldnames:
        return jsonify({
            "error": "CSV file must contain a header row"
        }), 400

    columns = {
        column.strip().lower()
        for column in reader.fieldnames
        if column
    }

    missing_columns = required_columns - columns

    if missing_columns:
        return jsonify({
            "error": (
                "Missing required columns: "
                + ", ".join(sorted(missing_columns))
            )
        }), 400

    created = []
    skipped = []
    errors = []

    for row_number, row in enumerate(reader, start=2):
        name = str(
            row.get("name", "")
        ).strip()

        email = str(
            row.get("email", "")
        ).strip().lower()

        password = str(
            row.get("password", "")
        )

        mobile = str(
            row.get("mobile", "")
        ).strip()

        education = str(
            row.get("education", "")
        ).strip()

        if not name:
            errors.append({
                "row": row_number,
                "error": "Name is required"
            })
            continue

        if not email:
            errors.append({
                "row": row_number,
                "error": "Email is required"
            })
            continue

        if not password or len(password) < 8:
            errors.append({
                "row": row_number,
                "error": (
                    "Password must be at least 8 characters"
                )
            })
            continue

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            skipped.append({
                "row": row_number,
                "email": email,
                "reason": "Email already exists"
            })
            continue

        try:
            with db.session.begin_nested():
                learner_user = User(
                    name=name,
                    email=email,
                    mobile=mobile,
                    role="learner",
                    status="active",
                    password_hash=create_password_hash(
                        password
                    ),
                )

                db.session.add(learner_user)
                db.session.flush()

                learner = Learner(
                    user_id=learner_user.id,
                    education=education,
                    status="active",
                )

                db.session.add(learner)
                db.session.flush()

                created.append({
                    "row": row_number,
                    "name": name,
                    "email": email,
                    "learner_id": learner.id,
                })

        except Exception as exc:
            errors.append({
                "row": row_number,
                "email": email,
                "error": str(exc),
            })
    current_app.logger.warning(
        "AUDIT DEBUG: user=%s created=%s skipped=%s errors=%s",
        user.id,
        len(created),
        len(skipped),
        len(errors),
    )
    create_audit_log(
        user=user,
        action="CSV_IMPORT",
        entity_type="Learner",
        description=(
            f"Imported learners from CSV: "
            f"{len(created)} created, "
            f"{len(skipped)} skipped, "
            f"{len(errors)} errors"
        ),
    )

    db.session.commit()

    return jsonify({
        "message": "CSV import completed",
        "summary": {
            "created": len(created),
            "skipped": len(skipped),
            "errors": len(errors),
            "total_rows": (
                len(created)
                + len(skipped)
                + len(errors)
            ),
        },
        "created": created,
        "skipped": skipped,
        "errors": errors,
    }), 200

# =========================================================
# ADMIN - AUDIT LOGS
# =========================================================

@api.get("/admin/audit-logs")
@role_required("admin")
def admin_audit_logs(user):
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    page = max(page, 1)
    per_page = min(max(per_page, 1), 100)

    pagination = (
        AuditLog.query
        .order_by(AuditLog.created_at.desc())
        .paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
    )

    logs = []

    for log in pagination.items:
        logs.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": log.user.name if log.user else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "description": log.description,
            "ip_address": log.ip_address,
            "created_at": (
                log.created_at.isoformat()
                if log.created_at
                else None
            ),
        })

    return jsonify({
        "audit_logs": logs,
        "pagination": {
            "page": pagination.page,
            "per_page": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_prev": pagination.has_prev,
        },
    }), 200


# =========================================================
# ADMIN - LEARNERS
# =========================================================

@api.get("/admin/learners")
@role_required("admin")
def admin_learners(user):
    try:
        page = max(int(request.args.get("page", 1)), 1)
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(int(request.args.get("limit", 20)), 1),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Learner.query
        .order_by(Learner.id.asc())
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    return jsonify({
        "learners": [
            learner_json(item)
            for item in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    })


@api.put("/admin/learners/<int:learner_id>")
@role_required("admin")
def admin_update_learner(
    user,
    learner_id,
):
    learner = Learner.query.get_or_404(
        learner_id
    )

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "name" in data:
        learner.user.name = data["name"]

    if "email" in data:
        learner.user.email = (
            str(data["email"])
            .strip()
            .lower()
        )

    if "mobile" in data:
        learner.user.mobile = data["mobile"]

    if "education" in data:
        learner.education = data["education"]

    if "batch_id" in data:
        learner.batch_id = data["batch_id"]

    if "status" in data:
        learner.status = data["status"]

    db.session.commit()

    return jsonify({
        "message":
            "Learner updated successfully",
        "learner":
            learner_json(learner),
    })


# =========================================================
# ADMIN - COURSES
# =========================================================

@api.get("/admin/courses")
@role_required("admin")
def admin_courses(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Course.query
        .order_by(
            Course.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    courses = pagination.items
    

    return jsonify({
    "courses": [
        course_json(course)
        for course in courses
    ],
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})

# =========================================================
# ADMIN - ACTIVATE / DEACTIVATE COURSE
# =========================================================

@api.patch("/admin/courses/<string:course_id>/status")
@role_required("admin")
def admin_update_course_status(
    user,
    course_id,
):
    course = Course.query.get_or_404(
        course_id
    )

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "published" not in data:
        return jsonify({
            "error":
                "published is required"
        }), 400

    published = data["published"]

    if not isinstance(
        published,
        bool
    ):
        return jsonify({
            "error":
                "published must be true or false"
        }), 400

    course.published = published

    db.session.commit()

    return jsonify({
        "message":
            (
                "Course activated successfully"
                if published
                else
                "Course deactivated successfully"
            ),
        "course":
            course_json(course),
    })

@api.put("/admin/courses/<string:course_id>/price")
@role_required("admin")
def admin_update_course_price(user, course_id):
    course = Course.query.get_or_404(course_id)

    data = request.get_json(silent=True) or {}

    if "course_fee" not in data:
        return jsonify({
            "error": "course_fee is required"
        }), 400

    try:
        course_fee = float(data["course_fee"])
    except (TypeError, ValueError):
        return jsonify({
            "error": "course_fee must be a valid number"
        }), 400

    if course_fee < 0:
        return jsonify({
            "error": "course_fee cannot be negative"
        }), 400

    course.course_fee = course_fee

    db.session.commit()

    return jsonify({
        "message": "Course price updated successfully",
        "course": course_json(course)
    }), 200

# =========================================================
# ADMIN - DELETE ENTIRE COURSE
# =========================================================

@api.delete("/admin/courses/<string:course_id>")
@role_required("admin")
def admin_delete_course(
    user,
    course_id,
):
    course = Course.query.get_or_404(
        course_id
    )

    try:
        # -------------------------------------------------
        # Find all modules and lessons
        # -------------------------------------------------

        modules = Module.query.filter_by(
            course_id=course.id
        ).all()

        lesson_ids = []

        for module in modules:

            lessons = Lesson.query.filter_by(
                module_id=module.id
            ).all()

            lesson_ids.extend(
                lesson.id
                for lesson in lessons
            )

        # -------------------------------------------------
        # Delete lesson-level records
        # -------------------------------------------------

        if lesson_ids:

            LessonProgress.query.filter(
                LessonProgress.lesson_id.in_(
                    lesson_ids
                )
            ).delete(
                synchronize_session=False
            )

            Discussion.query.filter(
                Discussion.lesson_id.in_(
                    lesson_ids
                )
            ).delete(
                synchronize_session=False
            )

            lesson_resources = (
                LessonResource.query
                .filter(
                    LessonResource.lesson_id.in_(
                        lesson_ids
                    )
                )
                .all()
            )

            # Delete physical lesson files.
            for resource in lesson_resources:

                if resource.file_path:
                    try:
                        if os.path.isfile(
                            resource.file_path
                        ):
                            os.remove(
                                resource.file_path
                            )
                    except OSError:
                        current_app.logger.warning(
                            "Unable to delete lesson resource file: %s",
                            resource.file_path,
                        )

            LessonResource.query.filter(
                LessonResource.lesson_id.in_(
                    lesson_ids
                )
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # Delete assignment submissions
        # -------------------------------------------------

        assignments = Assignment.query.filter_by(
            course_id=course.id
        ).all()

        assignment_ids = [
            assignment.id
            for assignment in assignments
        ]

        if assignment_ids:

            AssignmentSubmission.query.filter(
                AssignmentSubmission.assignment_id.in_(
                    assignment_ids
                )
            ).delete(
                synchronize_session=False
            )

            Assignment.query.filter(
                Assignment.id.in_(
                    assignment_ids
                )
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # Delete quiz answers / attempts / questions
        # -------------------------------------------------

        quizzes = Quiz.query.filter_by(
            course_id=course.id
        ).all()

        quiz_ids = [
            quiz.id
            for quiz in quizzes
        ]

        if quiz_ids:

            attempts = QuizAttempt.query.filter(
                QuizAttempt.quiz_id.in_(
                    quiz_ids
                )
            ).all()

            attempt_ids = [
                attempt.id
                for attempt in attempts
            ]

            if attempt_ids:

                QuizAnswer.query.filter(
                    QuizAnswer.attempt_id.in_(
                        attempt_ids
                    )
                ).delete(
                    synchronize_session=False
                )

                QuizAttempt.query.filter(
                    QuizAttempt.id.in_(
                        attempt_ids
                    )
                ).delete(
                    synchronize_session=False
                )

            Question.query.filter(
                Question.quiz_id.in_(
                    quiz_ids
                )
            ).delete(
                synchronize_session=False
            )

            Quiz.query.filter(
                Quiz.id.in_(
                    quiz_ids
                )
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # Delete coding exams and their children
        # -------------------------------------------------

        coding_exams = CodingExam.query.filter_by(
            course_id=course.id
        ).all()

        coding_exam_ids = [
            exam.id
            for exam in coding_exams
        ]

        if coding_exam_ids:

            coding_questions = (
                CodingQuestion.query
                .filter(
                    CodingQuestion.exam_id.in_(
                        coding_exam_ids
                    )
                )
                .all()
            )

            coding_question_ids = [
                question.id
                for question in coding_questions
            ]

            # Test cases depend on coding questions.
            if coding_question_ids:

                CodingTestCase.query.filter(
                    CodingTestCase.question_id.in_(
                        coding_question_ids
                    )
                ).delete(
                    synchronize_session=False
                )

            # Submissions depend on both exams
            # and questions.
            CodingSubmission.query.filter(
                CodingSubmission.exam_id.in_(
                    coding_exam_ids
                )
            ).delete(
                synchronize_session=False
            )

            CodingQuestion.query.filter(
                CodingQuestion.exam_id.in_(
                    coding_exam_ids
                )
            ).delete(
                synchronize_session=False
            )

            # Sessions depend on coding exams.
            sessions = (
                CodingExamSession.query
                .filter(
                    CodingExamSession.exam_id.in_(
                        coding_exam_ids
                    )
                )
                .all()
            )

            session_ids = [
                session.id
                for session in sessions
            ]

            if session_ids:

                CodingExamMonitoringEvent.query.filter(
                    CodingExamMonitoringEvent.session_id.in_(
                        session_ids
                    )
                ).delete(
                    synchronize_session=False
                )

                screenshots = (
                    CodingExamScreenshot.query
                    .filter(
                        CodingExamScreenshot.session_id.in_(
                            session_ids
                        )
                    )
                    .all()
                )

                for screenshot in screenshots:

                    if screenshot.file_path:
                        try:
                            if os.path.isfile(
                                screenshot.file_path
                            ):
                                os.remove(
                                    screenshot.file_path
                                )
                        except OSError:
                            current_app.logger.warning(
                                "Unable to delete coding screenshot: %s",
                                screenshot.file_path,
                            )

                CodingExamScreenshot.query.filter(
                    CodingExamScreenshot.session_id.in_(
                        session_ids
                    )
                ).delete(
                    synchronize_session=False
                )

                CodingExamSession.query.filter(
                    CodingExamSession.id.in_(
                        session_ids
                    )
                ).delete(
                    synchronize_session=False
                )

            CodingExam.query.filter(
                CodingExam.id.in_(
                    coding_exam_ids
                )
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # Delete course-level records
        # -------------------------------------------------

        Enrollment.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        Certificate.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        Wishlist.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        # Delete learning-time records linked directly to the course
        LearningTime.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        # Also delete learning-time records linked through
        # lessons belonging to this course.
        if lesson_ids:
            LearningTime.query.filter(
                LearningTime.lesson_id.in_(lesson_ids)
            ).delete(
                synchronize_session=False
            )

        # -------------------------------------------------
        # Delete course documents from database
        # and filesystem
        # -------------------------------------------------

        documents = CourseDocument.query.filter_by(
            course_id=course.id
        ).all()

        for document in documents:

            if document.file_path:
                try:
                    if os.path.isfile(
                        document.file_path
                    ):
                        os.remove(
                            document.file_path
                        )
                except OSError:
                    current_app.logger.warning(
                        "Unable to delete course document: %s",
                        document.file_path,
                    )

        CourseDocument.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # Delete physical course folders
        # -------------------------------------------------

        course_document_path = (
            os.path.join(
                COURSE_DOCUMENT_ROOT,
                secure_filename(
                    str(course.id)
                ),
            )
        )

        if os.path.isdir(
            course_document_path
        ):
            shutil.rmtree(
                course_document_path,
                ignore_errors=True
            )

        for lesson_id in lesson_ids:

            for root in (
                VIDEO_UPLOAD_ROOT,
                PDF_UPLOAD_ROOT,
            ):

                lesson_folder = os.path.join(
                    root,
                    secure_filename(
                        str(lesson_id)
                    ),
                )

                if os.path.isdir(
                    lesson_folder
                ):
                    shutil.rmtree(
                        lesson_folder,
                        ignore_errors=True
                    )

        # -------------------------------------------------
        # Delete lessons and modules
        # -------------------------------------------------

        if lesson_ids:

            Lesson.query.filter(
                Lesson.id.in_(
                    lesson_ids
                )
            ).delete(
                synchronize_session=False
            )

        Module.query.filter_by(
            course_id=course.id
        ).delete(
            synchronize_session=False
        )

        # -------------------------------------------------
        # Finally delete the course itself
        # -------------------------------------------------

        db.session.delete(course)

        db.session.commit()

        return jsonify({
            "message":
                "Course and all related data deleted successfully"
        })

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to delete course %s",
            course_id
        )

        return jsonify({
            "error":
                "Unable to delete course"
        }), 500
    
# =========================================================
# PUBLIC / LEARNER - LIST PUBLISHED COURSES
# =========================================================

@api.get("/courses")
@token_required
def courses(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Course.query
        .filter_by(
            published=True
        )
        .order_by(
            Course.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    published_courses = pagination.items

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    result = []

    for course in published_courses:
        progress = 0

        if learner:
            enrollment = (
                Enrollment.query
                .filter_by(
                    learner_id=learner.id,
                    course_id=course.id,
                    status="active",
                )
                .first()
            )

            if enrollment:
                progress = (
                    enrollment.progress
                    or 0
                )

        result.append(
            course_json(
                course,
                progress,
            )
        )

    return jsonify({
    "courses": [
        course_json(course)
        for course in published_courses
    ],
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


# =========================================================
# COURSE DETAILS
# =========================================================

@api.get("/courses/<course_id>")
@token_required
def course_details(
    user,
    course_id,
):
    course = Course.query.get_or_404(
        course_id
    )

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    progress = 0
    enrollment = None
    access_granted = True
    payment_required = False
    paid_amount = 0
    pending_amount = 0

    # -----------------------------------------------------
    # LEARNER ACCESS CHECK
    # -----------------------------------------------------

    if user.role == "learner":

        if not learner:
            return jsonify({
                "error": "Learner profile not found"
            }), 404

        enrollment = (
            Enrollment.query
            .filter_by(
                learner_id=learner.id,
                course_id=course.id,
            )
            .first()
        )

        course_fee = float(
            course.course_fee or 0
        )

        # -------------------------------------------------
        # Calculate paid amount
        # -------------------------------------------------

        if enrollment:

            paid_amount = (
                db.session.query(
                    db.func.coalesce(
                        db.func.sum(
                            Payment.amount
                        ),
                        0
                    )
                )
                .filter(
                    Payment.enrollment_id
                    == enrollment.id,
                    Payment.status == "paid"
                )
                .scalar()
                or 0
            )

            paid_amount = float(
                paid_amount
            )

        # -------------------------------------------------
        # FREE COURSE
        # -------------------------------------------------

        if course_fee <= 0:

            payment_required = False

            if enrollment:
                access_granted = (
                    enrollment.status == "active"
                )
                progress = (
                    enrollment.progress or 0
                )
            else:
                access_granted = False

        # -------------------------------------------------
        # PAID COURSE
        # -------------------------------------------------

        else:

            pending_amount = max(
                course_fee - paid_amount,
                0
            )

            if enrollment:
                progress = (
                    enrollment.progress or 0
                )

            # Full payment + active enrollment
            if (
                enrollment
                and enrollment.status == "active"
                and paid_amount >= course_fee
            ):
                access_granted = True
                payment_required = False

            else:
                access_granted = False
                payment_required = True

    # -----------------------------------------------------
    # Load course content only when access is granted
    # -----------------------------------------------------

    module_result = []

    if access_granted:

        modules = (
            Module.query
            .filter_by(
                course_id=course.id
            )
            .order_by(
                Module.id.asc()
            )
            .all()
        )

        for module in modules:

            lessons = (
                Lesson.query
                .filter_by(
                    module_id=module.id
                )
                .order_by(
                    Lesson.id.asc()
                )
                .all()
            )

            lesson_result = []

            for lesson in lessons:

                completed = False

                if learner:

                    progress_row = (
                        LessonProgress.query
                        .filter_by(
                            learner_id=learner.id,
                            lesson_id=lesson.id,
                        )
                        .first()
                    )

                    if progress_row:
                        completed = bool(
                            progress_row.completed
                        )

                resources = (
                    LessonResource.query
                    .filter_by(
                        lesson_id=lesson.id
                    )
                    .order_by(
                        LessonResource.id.asc()
                    )
                    .all()
                )

                resource_result = []

                for resource in resources:

                    resource_result.append({
                        "id": resource.id,
                        "type":
                            resource.resource_type,
                        "fileName":
                            resource.file_name,
                        "title":
                            resource.title
                            or resource.file_name,
                        "url":
                            "/api/files/"
                            + os.path.relpath(
                                resource.file_path,
                                current_app.config[
                                    "UPLOAD_FOLDER"
                                ],
                            ).replace(
                                os.sep,
                                "/",
                            ),
                    })

                lesson_result.append({
                    "id": lesson.id,
                    "title": lesson.title,
                    "description": getattr(
                        lesson,
                        "description",
                        "",
                    ),
                    "duration": lesson.duration,
                    "video_url": lesson.video_url,
                    "pdf_url": lesson.pdf_url,
                    "completed": completed,
                    "resources": resource_result,
                })

            module_result.append({
                "id": module.id,
                "course_id":
                    module.course_id,
                "title": module.title,
                "description": getattr(
                    module,
                    "description",
                    "",
                ),
                "lessons": lesson_result,
            })

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({
        "course": course_json(
            course,
            progress,
        ),

        "modules": module_result,

        "access_granted":
            access_granted,

        "payment_required":
            payment_required,

        "enrollment_status": (
            enrollment.status
            if enrollment
            else None
        ),

        "paid_amount":
            paid_amount,

        "pending_amount":
            pending_amount,
    })


# =========================================================
# TRAINER - LIST OWN COURSES
# =========================================================

@api.get("/trainer/courses")
@role_required("trainer")
def trainer_courses(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    try:
        page = max(
        int(request.args.get("page", 1)),
        1
    )
    except (TypeError, ValueError):
            page = 1

    try:
            limit = min(
                max(
                    int(request.args.get("limit", 20)),
                    1
                ),
                100
            )
    except (TypeError, ValueError):
            limit = 20

    pagination = (
            Course.query
            .filter_by(
                trainer_id=trainer.id
            )
            .order_by(
                Course.created_at.desc()
            )
            .paginate(
                page=page,
                per_page=limit,
                error_out=False
            )
        )

    courses = pagination.items

    return jsonify({
    "courses": [
        course_json(course)
        for course in courses
    ],
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


# =========================================================
# TRAINER - CREATE COURSE
# =========================================================

@api.post("/trainer/courses")
@role_required("trainer")
def trainer_create_course(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    course_id = (
        data.get("id")
        or data.get("course_id")
    )

    title = str(
        data.get(
            "title",
            "",
        )
    ).strip()

    if not course_id:
        return jsonify({
            "error": "Course ID is required"
        }), 400

    if not title:
        return jsonify({
            "error": "Course title is required"
        }), 400

    if Course.query.get(course_id):
        return jsonify({
            "error": "Course ID already exists"
        }), 409

    # -----------------------------------------------------
    # Validate course fee
    # -----------------------------------------------------

    course_fee = data.get(
        "course_fee",
        0
    )

    try:
        course_fee = float(course_fee)
    except (TypeError, ValueError):
        return jsonify({
            "error": "course_fee must be a valid number"
        }), 400

    if course_fee < 0:
        return jsonify({
            "error": "course_fee cannot be negative"
        }), 400

    course = Course(
        id=course_id,
        title=title,
        trainer_id=trainer.id,
        level=data.get(
            "level",
            "",
        ),
        description=data.get(
            "description",
            "",
        ),
        thumbnail=data.get(
            "thumbnail",
            "",
        ),
        course_fee=course_fee,
        published=False,
    )

    db.session.add(course)
    db.session.commit()

    return jsonify({
        "message":
            "Course created successfully",
        "course":
            course_json(course),
    }), 201

# =========================================================
# CALENDAR - DATETIME HELPERS
# =========================================================

def calendar_datetime_iso(value):
    if not value:
        return None

    if value.tzinfo is None:
        value = value.replace(
            tzinfo=timezone.utc
        )

    return value.astimezone(
        timezone.utc
    ).isoformat()

# =========================================================
# CALENDAR - LEARNER
# =========================================================

@api.get("/learner/calendar")
@role_required("learner")
def learner_calendar(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    active_course_ids = [
        enrollment.course_id
        for enrollment in enrollments
        if enrollment.status == "active"
    ]

    if not active_course_ids:
        return jsonify({
            "events": []
        }), 200

    now = datetime.now(timezone.utc)

    events = (
        CalendarEvent.query
        .filter(
            CalendarEvent.course_id.in_(active_course_ids),
            CalendarEvent.start_at >= now
        )
        .order_by(
            CalendarEvent.start_at.asc()
        )
        .all()
    )

    result = []

    for event in events:
        course = Course.query.get(
            event.course_id
        )

        result.append({
            "id": event.id,
            "course_id": event.course_id,
            "course_title": (
                course.title
                if course
                else event.course_id
            ),
            "title": event.title,
            "description": event.description or "",
            "event_type": event.event_type,
            "start_at": calendar_datetime_iso(
                event.start_at
            ),
            "end_at": calendar_datetime_iso(
                event.end_at
            ),
            "meeting_url": event.meeting_url or ""
        })

    return jsonify({
        "events": result
    }), 200

# =========================================================
# CALENDAR - TRAINER LIST EVENTS
# =========================================================

@api.get("/trainer/calendar/events")
@role_required("trainer")
def trainer_calendar_events(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    events = (
        CalendarEvent.query
        .filter_by(
            trainer_id=trainer.id
        )
        .order_by(
            CalendarEvent.start_at.asc()
        )
        .all()
    )

    result = []

    for event in events:
        course = Course.query.get(
            event.course_id
        )

        result.append({
            "id": event.id,
            "course_id": event.course_id,
            "course_title": (
                course.title
                if course
                else event.course_id
            ),
            "title": event.title,
            "description": event.description or "",
            "event_type": event.event_type,
            "start_at": calendar_datetime_iso(
                event.start_at
            ),
            "end_at": calendar_datetime_iso(
                event.end_at
            ),
            "meeting_url": event.meeting_url or ""
        })

    return jsonify({
        "events": result
    }), 200

# =========================================================
# CALENDAR - TRAINER CREATE EVENT
# =========================================================

@api.post("/trainer/calendar/events")
@role_required("trainer")
def trainer_create_calendar_event(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    course_id = str(
        data.get("course_id", "")
    ).strip()

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    event_type = str(
        data.get(
            "event_type",
            "live_class"
        )
    ).strip()

    start_at_value = data.get(
        "start_at"
    )

    end_at_value = data.get(
        "end_at"
    )

    meeting_url = str(
        data.get("meeting_url", "")
    ).strip()

    if not course_id:
        return jsonify({
            "error": "Course ID is required"
        }), 400

    if not title:
        return jsonify({
            "error": "Event title is required"
        }), 400

    if not start_at_value:
        return jsonify({
            "error": "Start date and time are required"
        }), 400

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found or does not belong to this trainer"
        }), 404

    try:
        start_at = datetime.fromisoformat(
            str(start_at_value).replace(
                "Z",
                "+00:00"
            )
        )

        if start_at.tzinfo is None:
            start_at = start_at.replace(
                tzinfo=timezone.utc
            )
        else:
            start_at = start_at.astimezone(
                timezone.utc
            )

    except ValueError:
        return jsonify({
            "error": "Invalid start_at format"
        }), 400

    end_at = None

    if end_at_value:
        try:
            end_at = datetime.fromisoformat(
                str(end_at_value).replace(
                    "Z",
                    "+00:00"
                )
            )

            if end_at.tzinfo is None:
                end_at = end_at.replace(
                    tzinfo=timezone.utc
                )
            else:
                end_at = end_at.astimezone(
                    timezone.utc
                )

        except ValueError:
            return jsonify({
                "error": "Invalid end_at format"
            }), 400

    if end_at and end_at <= start_at:
        return jsonify({
            "error": "End time must be after start time"
        }), 400

    allowed_event_types = {
        "live_class",
        "exam",
        "assignment",
        "other"
    }

    if event_type not in allowed_event_types:
        return jsonify({
            "error": "Invalid event type"
        }), 400

    event = CalendarEvent(
        course_id=course.id,
        trainer_id=trainer.id,
        title=title,
        description=description,
        event_type=event_type,
        start_at=start_at,
        end_at=end_at,
        meeting_url=meeting_url
    )

    db.session.add(event)
    db.session.commit()

    return jsonify({
        "message": "Calendar event created successfully",
        "event": {
            "id": event.id,
            "course_id": event.course_id,
            "title": event.title,
            "description": event.description or "",
            "event_type": event.event_type,
            "start_at": calendar_datetime_iso(
                event.start_at
            ),
            "end_at": calendar_datetime_iso(
                event.end_at
            ),
            "meeting_url": event.meeting_url or ""
        }
    }), 201


# =========================================================
# CALENDAR - TRAINER UPDATE EVENT
# =========================================================

@api.put("/trainer/calendar/events/<int:event_id>")
@role_required("trainer")
def trainer_update_calendar_event(
    user,
    event_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    event = CalendarEvent.query.filter_by(
        id=event_id,
        trainer_id=trainer.id
    ).first()

    if not event:
        return jsonify({
            "error": "Calendar event not found"
        }), 404

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "title" in data:
        title = str(
            data.get("title", "")
        ).strip()

        if not title:
            return jsonify({
                "error": "Event title cannot be empty"
            }), 400

        event.title = title

    if "description" in data:
        event.description = str(
            data.get("description", "")
        ).strip()

    if "meeting_url" in data:
        event.meeting_url = str(
            data.get("meeting_url", "")
        ).strip()

    if "event_type" in data:
        event_type = str(
            data.get("event_type", "")
        ).strip()

        allowed_event_types = {
            "live_class",
            "exam",
            "assignment",
            "other"
        }

        if event_type not in allowed_event_types:
            return jsonify({
                "error": "Invalid event type"
            }), 400

        event.event_type = event_type

    if "start_at" in data:
        try:
            start_at = datetime.fromisoformat(
                str(data["start_at"]).replace(
                    "Z",
                    "+00:00"
                )
            )

            if start_at.tzinfo is None:
                start_at = start_at.replace(
                    tzinfo=timezone.utc
                )
            else:
                start_at = start_at.astimezone(
                    timezone.utc
                )

            event.start_at = start_at

        except ValueError:
            return jsonify({
                "error": "Invalid start_at format"
            }), 400

    if "end_at" in data:
        if data["end_at"]:
            try:
                end_at = datetime.fromisoformat(
                    str(data["end_at"]).replace(
                        "Z",
                        "+00:00"
                    )
                )

                if end_at.tzinfo is None:
                    end_at = end_at.replace(
                        tzinfo=timezone.utc
                    )
                else:
                    end_at = end_at.astimezone(
                        timezone.utc
                    )

                event.end_at = end_at

            except ValueError:
                return jsonify({
                    "error": "Invalid end_at format"
                }), 400
        else:
            event.end_at = None

    if (
        event.end_at
        and event.end_at <= event.start_at
    ):
        return jsonify({
            "error": "End time must be after start time"
        }), 400

    event.updated_at = datetime.now(
        timezone.utc
    )

    db.session.commit()

    return jsonify({
        "message": "Calendar event updated successfully",
        "event": {
            "id": event.id,
            "course_id": event.course_id,
            "title": event.title,
            "description": event.description or "",
            "event_type": event.event_type,
            "start_at": calendar_datetime_iso(
                event.start_at
            ),
            "end_at": calendar_datetime_iso(
                event.end_at
            ),
            "meeting_url": event.meeting_url or ""
        }
    }), 200


# =========================================================
# CALENDAR - TRAINER DELETE EVENT
# =========================================================

@api.delete("/trainer/calendar/events/<int:event_id>")
@role_required("trainer")
def trainer_delete_calendar_event(
    user,
    event_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    event = CalendarEvent.query.filter_by(
        id=event_id,
        trainer_id=trainer.id
    ).first()

    if not event:
        return jsonify({
            "error": "Calendar event not found"
        }), 404

    db.session.delete(event)
    db.session.commit()

    return jsonify({
        "message": "Calendar event deleted successfully"
    }), 200


# =========================================================
# TRAINER - UPDATE COURSE
# =========================================================

@api.put("/trainer/courses/<course_id>")
@role_required("trainer")
def trainer_update_course(
    user,
    course_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    course = Course.query.get_or_404(
        course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this course"
        }), 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "title" in data:
        course.title = str(
            data["title"]
        ).strip()

    if "level" in data:
        course.level = data["level"]

    if "description" in data:
        course.description = data["description"]

    if "thumbnail" in data:
        course.thumbnail = data["thumbnail"]

    if "published" in data:
        course.published = bool(
            data["published"]
        )

    # -----------------------------------------------------
    # Update course fee
    # -----------------------------------------------------

    if "course_fee" in data:
        try:
            course_fee = float(
                data["course_fee"]
            )
        except (TypeError, ValueError):
            return jsonify({
                "error":
                    "course_fee must be a valid number"
            }), 400

        if course_fee < 0:
            return jsonify({
                "error":
                    "course_fee cannot be negative"
            }), 400

        course.course_fee = course_fee

    db.session.commit()

    return jsonify({
        "message":
            "Course updated successfully",
        "course":
            course_json(course),
    })


# =========================================================
# TRAINER - DELETE / UNPUBLISH COURSE
# =========================================================

@api.delete("/trainer/courses/<course_id>")
@role_required("trainer")
def trainer_delete_course(
    user,
    course_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    course = Course.query.get_or_404(
        course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this course"
        }), 403

    course.published = False
    db.session.commit()

    return jsonify({
        "message":
            "Course unpublished successfully"
    })


# =========================================================
# TRAINER - PUBLISH COURSE
# =========================================================

@api.post(
    "/trainer/courses/<course_id>/publish"
)
@role_required("trainer")
def trainer_publish_course(
    user,
    course_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    course = Course.query.get_or_404(
        course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this course"
        }), 403

    course.published = True
    db.session.commit()

    return jsonify({
        "message":
            "Course published successfully",
        "course":
            course_json(course),
    })


# =========================================================
# TRAINER - UNPUBLISH COURSE
# =========================================================

@api.post(
    "/trainer/courses/<course_id>/unpublish"
)
@role_required("trainer")
def trainer_unpublish_course(
    user,
    course_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    course = Course.query.get_or_404(
        course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this course"
        }), 403

    course.published = False
    db.session.commit()

    return jsonify({
        "message":
            "Course unpublished successfully",
        "course":
            course_json(course),
    })


# =========================================================
# TRAINER - CREATE MODULE
# =========================================================

@api.post(
    "/trainer/courses/<course_id>/modules"
)
@role_required("trainer")
def trainer_create_module(
    user,
    course_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    course = Course.query.get_or_404(
        course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this course"
        }), 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    title = str(
        data.get(
            "title",
            "",
        )
    ).strip()

    if not title:
        return jsonify({
            "error":
                "Module title is required"
        }), 400

    last_module = (
    Module.query
    .filter_by(course_id=course.id)
    .order_by(Module.order_no.desc())
    .first()
    )

    next_order_no = (
    (last_module.order_no or 0) + 1
    if last_module
    else 1
    )

    module = Module(
    course_id=course.id,
    title=title,
    order_no=next_order_no,
    )

    db.session.add(module)
    db.session.commit()

    return jsonify({
        "message":
            "Module created successfully",
        "module": {
            "id": module.id,
            "course_id": module.course_id,
            "title": module.title,
            "description": getattr(
                module,
                "description",
                "",
            ),
        },
    }), 201


# =========================================================
# TRAINER - UPDATE MODULE
# =========================================================

@api.put(
    "/trainer/modules/<int:module_id>"
)
@role_required("trainer")
def trainer_update_module(
    user,
    module_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    module = Module.query.get_or_404(
        module_id
    )

    course = Course.query.get_or_404(
        module.course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this module"
        }), 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    if "title" in data:
        module.title = str(
            data["title"]
        ).strip()


    db.session.commit()

    return jsonify({
        "message":
            "Module updated successfully",
        "module": {
            "id": module.id,
            "course_id": module.course_id,
            "title": module.title,
            "description": getattr(
                module,
                "description",
                "",
            ),
        },
    })


# =========================================================
# TRAINER - CREATE LESSON
# =========================================================

@api.post(
    "/trainer/modules/<int:module_id>/lessons"
)
@role_required("trainer")
def trainer_create_lesson(
    user,
    module_id,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error":
                "Trainer profile not found"
        }), 404

    module = Module.query.get_or_404(
        module_id
    )

    course = Course.query.get_or_404(
        module.course_id
    )

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You do not own this module"
        }), 403

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    # -----------------------------------------------------
    # LESSON ID
    # -----------------------------------------------------

    lesson_id = str(
        data.get(
            "id",
            data.get(
                "lesson_id",
                ""
            )
        )
    ).strip()

    if not lesson_id:
        return jsonify({
            "error":
                "Lesson ID is required"
        }), 400

    # -----------------------------------------------------
    # LESSON TITLE
    # -----------------------------------------------------

    title = str(
        data.get(
            "title",
            ""
        )
    ).strip()

    if not title:
        return jsonify({
            "error":
                "Lesson title is required"
        }), 400

    # -----------------------------------------------------
    # CHECK DUPLICATE LESSON ID
    # -----------------------------------------------------

    if Lesson.query.get(lesson_id):
        return jsonify({
            "error":
                "Lesson ID already exists"
        }), 409

    # -----------------------------------------------------
    # LESSON CONTENT
    # -----------------------------------------------------

    content = data.get(
        "content",
        data.get(
            "description",
            ""
        )
    )

    # -----------------------------------------------------
    # ORDER NUMBER
    # -----------------------------------------------------

    last_lesson = (
        Lesson.query
        .filter_by(
            module_id=module.id
        )
        .order_by(
            Lesson.order_no.desc()
        )
        .first()
    )

    next_order_no = (
        (last_lesson.order_no + 1)
        if last_lesson
        else 1
    )

    # -----------------------------------------------------
    # CREATE LESSON
    # -----------------------------------------------------

    lesson = Lesson(
        id=lesson_id,
        module_id=module.id,
        title=title,
        content=content,
        duration=data.get(
            "duration",
            "00:00"
        ),
        video_url=data.get(
            "video_url",
            ""
        ),
        pdf_url=data.get(
            "pdf_url",
            ""
        ),
        order_no=next_order_no,
    )

    db.session.add(lesson)
    db.session.commit()

    return jsonify({
        "message":
            "Lesson created successfully",

        "lesson": {
            "id": lesson.id,
            "module_id": lesson.module_id,
            "title": lesson.title,
            "description": lesson.content or "",
            "content": lesson.content or "",
            "duration": lesson.duration,
            "video_url": lesson.video_url,
            "pdf_url": lesson.pdf_url,
            "order_no": lesson.order_no,
        },
    }), 201


# =========================================================
# LEARNER - ENROLL
# =========================================================

@api.post("/courses/<course_id>/enroll")
@role_required("learner")
def enroll_course(
    user,
    course_id,
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error":
                "Learner profile not found"
        }), 404

    course = Course.query.get(
        course_id
    )

    if not course:
        return jsonify({
            "error":
                "Course not found"
        }), 404

    # -----------------------------------------------------
    # Only published courses can be enrolled in
    # -----------------------------------------------------

    if not course.published:
        return jsonify({
            "error":
                "This course is not available for enrollment"
        }), 400

    # -----------------------------------------------------
    # Check existing enrollment
    # -----------------------------------------------------

    enrollment = (
        Enrollment.query
        .filter_by(
            learner_id=learner.id,
            course_id=course.id,
        )
        .first()
    )

    if enrollment:

        # Keep the enrollment fee synchronized
        # with the course fee only when no payment
        # has been recorded yet.
        paid_amount = (
            db.session.query(
                db.func.coalesce(
                    db.func.sum(Payment.amount),
                    0
                )
            )
            .filter(
                Payment.enrollment_id == enrollment.id,
                Payment.status == "paid"
            )
            .scalar()
            or 0
        )

        if float(paid_amount) <= 0:
            enrollment.course_fee = (
                course.course_fee or 0
            )

        # Already fully active
        if enrollment.status == "active":
            db.session.commit()

            return jsonify({
                "message":
                    "Already enrolled in this course",
                "enrollment": {
                    "id": enrollment.id,
                    "course_id":
                        enrollment.course_id,
                    "course_fee":
                        float(
                            enrollment.course_fee or 0
                        ),
                    "progress":
                        enrollment.progress or 0,
                    "status":
                        enrollment.status,
                    "paid_amount":
                        float(paid_amount),
                    "pending_amount":
                        max(
                            float(
                                enrollment.course_fee or 0
                            ) - float(paid_amount),
                            0
                        ),
                },
            }), 200

        # Existing payment-pending enrollment
        db.session.commit()

        return jsonify({
            "message":
                "Enrollment already exists. Payment is required.",
            "enrollment": {
                "id": enrollment.id,
                "course_id":
                    enrollment.course_id,
                "course_fee":
                    float(
                        enrollment.course_fee or 0
                    ),
                "progress":
                    enrollment.progress or 0,
                "status":
                    enrollment.status,
                "paid_amount":
                    float(paid_amount),
                "pending_amount":
                    max(
                        float(
                            enrollment.course_fee or 0
                        ) - float(paid_amount),
                        0
                    ),
            },
        }), 200

    # -----------------------------------------------------
    # Copy the course fee into the enrollment
    # -----------------------------------------------------

    course_fee = float(
        course.course_fee or 0
    )

    # -----------------------------------------------------
    # Free course
    # -----------------------------------------------------

    if course_fee <= 0:

        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course.id,
            course_fee=0,
            progress=0,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        return jsonify({
            "message":
                "Course enrolled successfully",
            "enrollment": {
                "id":
                    enrollment.id,
                "course_id":
                    enrollment.course_id,
                "course_fee":
                    0,
                "progress":
                    0,
                "status":
                    enrollment.status,
                "paid_amount":
                    0,
                "pending_amount":
                    0,
            },
        }), 201

    # -----------------------------------------------------
    # Paid course
    # -----------------------------------------------------
    # Create the enrollment but DO NOT activate it.
    # Payment must be recorded before access is granted.

    enrollment = Enrollment(
        learner_id=learner.id,
        course_id=course.id,
        course_fee=course_fee,
        progress=0,
        status="payment_pending",
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({
        "message":
            "Enrollment created. Payment is required before course access.",
        "enrollment": {
            "id":
                enrollment.id,
            "course_id":
                enrollment.course_id,
            "course_fee":
                course_fee,
            "progress":
                0,
            "status":
                enrollment.status,
            "paid_amount":
                0,
            "pending_amount":
                course_fee,
        },
    }), 201


# =========================================================
# LEARNER - MY LEARNING
# =========================================================

@api.get("/my-learning")
@role_required("learner")
def my_learning(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error":
                "Learner profile not found"
        }), 404

    try:
     page = max(
        int(request.args.get("page", 1)),
        1
    )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
        max(
            int(request.args.get("limit", 20)),
            1
        ),
        100
    )
    except (TypeError, ValueError):
         limit = 20

    pagination = (
        Enrollment.query
        .filter_by(
            learner_id=learner.id
        )
        .order_by(
            Enrollment.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
)

    enrollments = pagination.items

    result = []

    for enrollment in enrollments:
        course = Course.query.get(
            enrollment.course_id
        )

        if not course:
            continue

        result.append({
            **course_json(
                course,
                enrollment.progress or 0,
            ),
            "enrollment": {
                "id": enrollment.id,
                "status": enrollment.status,
                "progress":
                    enrollment.progress or 0,
                "enrolled_at": (
                    enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at
                    else None
                ),
            },
        })

    return jsonify({
    "courses": result,
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


# =========================================================
# LEARNER - WISHLIST
# =========================================================

@api.get("/wishlist")
@role_required("learner")
def get_wishlist(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error":
                "Learner profile not found"
        }), 404

    try:
        page = max(
        int(request.args.get("page", 1)),
        1
    )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Wishlist.query
        .filter_by(
            learner_id=learner.id
        )
        .order_by(
            Wishlist.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    items = pagination.items

    result = []

    for item in items:
        course = Course.query.get(
            item.course_id
        )

        if course:
            result.append(
                course_json(course)
            )

    return jsonify({
    "wishlist": result,
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


@api.put(
    "/courses/<course_id>/wishlist"
)
@role_required("learner")
def toggle_wishlist(
    user,
    course_id,
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error":
                "Learner profile not found"
        }), 404

    course = Course.query.get(
        course_id
    )

    if not course:
        return jsonify({
            "error":
                "Course not found"
        }), 404

    existing = (
        Wishlist.query
        .filter_by(
            learner_id=learner.id,
            course_id=course.id,
        )
        .first()
    )

    if existing:
        db.session.delete(existing)
        wishlisted = False
    else:
        db.session.add(
            Wishlist(
                learner_id=learner.id,
                course_id=course.id,
            )
        )
        wishlisted = True

    db.session.commit()

    return jsonify({
        "message":
            "Wishlist updated",
        "wishlisted":
            wishlisted,
    })


# =========================================================
# LEARNER DASHBOARD
# =========================================================

@api.get("/dashboard")
@role_required("learner")
def learner_dashboard(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error":
                "Learner profile not found"
        }), 404

    enrollments = (
        Enrollment.query
        .filter_by(
            learner_id=learner.id
        )
        .all()
    )

    courses_result = []

    for enrollment in enrollments:
        course = Course.query.get(
            enrollment.course_id
        )

        if not course:
            continue

        courses_result.append(
            course_json(
                course,
                enrollment.progress or 0,
            )
        )

    certificate_count = (
        Certificate.query
        .filter_by(
            learner_id=learner.id
        )
        .count()
    )

    assignment_count = (
        AssignmentSubmission.query
        .filter_by(
            learner_id=learner.id
        )
        .count()
    )

    assessment_count = (
        QuizAttempt.query
        .filter_by(
            learner_id=learner.id
        )
        .count()
    )

    return jsonify({
        "user":
            user_json(user),
        "stats": {
            "coursesEnrolled":
                len(enrollments),
            "certificates":
                certificate_count,
            "assignments":
                assignment_count,
            "assessments":
                assessment_count,
            "learningTime":
                calculate_learning_time(
                    learner.id
                ),
        },
        "courses":
            courses_result,
    })
# ============================================================
# LEARNER PROGRESS
# ============================================================

@api.get("/learner/lessons/<string:lesson_id>/progress")
@role_required("learner")
def get_lesson_progress(user, lesson_id):
    learner = Learner.query.filter_by(user_id=user.id).first()

    if not learner:
        return jsonify({"error": "Learner profile not found"}), 404

    progress = LessonProgress.query.filter_by(
        learner_id=learner.id,
        lesson_id=lesson_id
    ).first()

    return jsonify({
        "lesson_id": lesson_id,
        "completed": bool(progress.completed) if progress else False
    })


@api.post("/learner/lessons/<string:lesson_id>/progress")
@role_required("learner")
def update_lesson_progress(user, lesson_id):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # Find lesson
    # --------------------------------------------------------

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    # --------------------------------------------------------
    # Find module
    # --------------------------------------------------------

    module = db.session.get(
        Module,
        lesson.module_id
    )

    if not module:
        return jsonify({
            "error": "Module not found"
        }), 404

    # --------------------------------------------------------
    # Find course
    # --------------------------------------------------------

    course = db.session.get(
        Course,
        module.course_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # --------------------------------------------------------
    # SECURITY: learner must be actively enrolled
    # --------------------------------------------------------

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=course.id,
        status="active"
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    # --------------------------------------------------------
    # Update lesson progress
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    completed = bool(
        data.get(
            "completed",
            False
        )
    )

    progress = LessonProgress.query.filter_by(
        learner_id=learner.id,
        lesson_id=lesson_id
    ).first()

    if not progress:
        progress = LessonProgress(
            learner_id=learner.id,
            lesson_id=lesson_id,
            completed=completed
        )

        db.session.add(progress)

    else:
        progress.completed = completed

    # --------------------------------------------------------
    # Recalculate course progress
    # --------------------------------------------------------

    total_lessons = (
        Lesson.query
        .join(
            Module,
            Lesson.module_id == Module.id
        )
        .filter(
            Module.course_id == course.id
        )
        .count()
    )

    completed_count = (
        LessonProgress.query
        .join(
            Lesson,
            LessonProgress.lesson_id == Lesson.id
        )
        .join(
            Module,
            Lesson.module_id == Module.id
        )
        .filter(
            LessonProgress.learner_id == learner.id,
            LessonProgress.completed.is_(True),
            Module.course_id == course.id
        )
        .count()
    )

    percentage = (
        int(
            (completed_count / total_lessons) * 100
        )
        if total_lessons
        else 0
    )

    enrollment.progress = percentage

    certificate = (
        Certificate.query
        .filter_by(
            learner_id=learner.id,
            course_id=course.id
        )
        .first()
    )

    # --------------------------------------------------------
    # Course completion + certificate
    # --------------------------------------------------------

    if percentage >= 100:
        enrollment.status = "completed"

        if not certificate:
            now = datetime.now(
                timezone.utc
            )

            certificate = Certificate(
                certificate_id=(
                    f"CERT-{secrets.token_urlsafe(24)}"
                ),
                learner_id=learner.id,
                course_id=course.id,
                start_date=(
                    enrollment.enrolled_at
                    or now
                ),
                end_date=now,
                status="valid"
            )

            db.session.add(certificate)

    db.session.commit()

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    response = {
        "message": "Progress updated",
        "completed": completed,
        "courseProgress": percentage,
        "enrollmentStatus": enrollment.status
    }

    if certificate:
        response["certificate"] = {
            "certificate_id": certificate.certificate_id,
            "course_title": course.title,
            "start_date": (
                certificate.start_date.isoformat()
                if certificate.start_date
                else None
            ),
            "end_date": (
                certificate.end_date.isoformat()
                if certificate.end_date
                else None
            ),
            "status": certificate.status
        }

    return jsonify(response)

# ============================================================
# LEARNER LESSON NOTES
# ============================================================

@api.get("/learner/lessons/<string:lesson_id>/notes")
@role_required("learner")
def get_lesson_notes(user, lesson_id):
    # Find the learner profile.
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # Find the lesson.
    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    # Find the module and associated course.
    module = db.session.get(
        Module,
        lesson.module_id
    )

    if not module:
        return jsonify({
            "error": "Module not found"
        }), 404

    course = db.session.get(
        Course,
        module.course_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # Require active enrollment.
    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=course.id,
        status="active"
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    # Retrieve only this learner's note.
    note = LessonNote.query.filter_by(
        learner_id=learner.id,
        lesson_id=lesson_id
    ).first()

    return jsonify({
        "lesson_id": lesson_id,
        "content": note.content if note else "",
        "created_at": (
            note.created_at.isoformat()
            if note and note.created_at
            else None
        ),
        "updated_at": (
            note.updated_at.isoformat()
            if note and note.updated_at
            else None
        )
    }), 200


@api.put("/learner/lessons/<string:lesson_id>/notes")
@role_required("learner")
def save_lesson_notes(user, lesson_id):
    # Find the learner profile.
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # Find the lesson.
    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    # Find the module and associated course.
    module = db.session.get(
        Module,
        lesson.module_id
    )

    if not module:
        return jsonify({
            "error": "Module not found"
        }), 404

    course = db.session.get(
        Course,
        module.course_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # Require active enrollment.
    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=course.id,
        status="active"
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    # Validate the request body.
    data = request.get_json(
        silent=True
    ) or {}

    if "content" not in data:
        return jsonify({
            "error": "content is required"
        }), 400

    content = data["content"]

    if not isinstance(content, str):
        return jsonify({
            "error": "content must be a string"
        }), 400

    if len(content) > 50000:
        return jsonify({
            "error": "Notes cannot exceed 50000 characters"
        }), 400

    # Retrieve this learner's existing note.
    note = LessonNote.query.filter_by(
        learner_id=learner.id,
        lesson_id=lesson_id
    ).first()

    if note:
        # Update the existing note.
        note.content = content
        note.updated_at = datetime.now(
            timezone.utc
        )

    else:
        # Create a new note.
        note = LessonNote(
            learner_id=learner.id,
            lesson_id=lesson_id,
            content=content
        )

        db.session.add(note)

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Failed to save lesson notes"
        )

        return jsonify({
            "error": "Unable to save lesson notes"
        }), 500

    return jsonify({
        "message": "Lesson notes saved successfully",
        "lesson_id": lesson_id,
        "content": note.content,
        "created_at": (
            note.created_at.isoformat()
            if note.created_at
            else None
        ),
        "updated_at": (
            note.updated_at.isoformat()
            if note.updated_at
            else None
        )
    }), 200


@api.get("/learner/courses/<string:course_id>/progress")
@role_required("learner")
def get_course_progress(user, course_id):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    course = Course.query.get(course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    course_lessons = (
        Lesson.query
        .join(
            Module,
            Lesson.module_id == Module.id
        )
        .filter(
            Module.course_id == course.id
        )
        .all()
    )

    lesson_ids = [
        lesson.id
        for lesson in course_lessons
    ]

    total_lessons = len(lesson_ids)

    if total_lessons == 0:
        percentage = 0
        completed_count = 0
    else:
        completed_count = (
            LessonProgress.query
            .filter(
                LessonProgress.learner_id == learner.id,
                LessonProgress.lesson_id.in_(lesson_ids),
                LessonProgress.completed.is_(True)
            )
            .count()
        )

        percentage = int(
            (completed_count / total_lessons) * 100
        )

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=course.id
    ).first()

    return jsonify({
        "course_id": course.id,
        "completed_lessons": completed_count,
        "total_lessons": total_lessons,
        "progress": percentage,
        "enrolled": enrollment is not None,
        "status": enrollment.status if enrollment else None
    }), 200

# ============================================================
# LEARNER — ATTENDANCE
# ============================================================

@api.get("/learner/attendance")
@role_required("learner")
def learner_attendance(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    records = (
        Attendance.query
        .filter_by(
            learner_id=learner.id
        )
        .order_by(
            Attendance.date.desc(),
            Attendance.id.desc()
        )
        .all()
    )

    total = len(records)

    present = sum(
        1
        for record in records
        if record.status == "present"
    )

    late = sum(
        1
        for record in records
        if record.status == "late"
    )

    absent = sum(
        1
        for record in records
        if record.status == "absent"
    )

    attended = present + late

    percentage = (
        round(
            (attended / total) * 100,
            2
        )
        if total
        else 0
    )

    history = []

    for record in records:
        batch = db.session.get(
            Batch,
            record.batch_id
        )

        history.append({
            "id": record.id,
            "date": (
                record.date.isoformat()
                if record.date
                else None
            ),
            "batch_id": record.batch_id,
            "batch_name": (
                batch.name
                if batch
                else None
            ),
            "status": record.status
        })

    return jsonify({
        "summary": {
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_percentage": percentage
        },
        "history": history
    }), 200

# ============================================================
# LEARNER - LEADERBOARD
# ============================================================

@api.get("/learner/leaderboard")
@role_required("learner")
def learner_leaderboard(user):

    learners = Learner.query.all()

    leaderboard = []

    for learner in learners:

        if not learner.user:
            continue

        # Get this learner's enrollments
        enrollments = Enrollment.query.filter(
            Enrollment.learner_id == learner.id,
            Enrollment.status.in_(["active", "completed"])
        ).all()

        course_ids = [
            enrollment.course_id
            for enrollment in enrollments
        ]

        # No courses
        if not course_ids:
            leaderboard.append({
                "learner_id": learner.id,
                "user_id": learner.user_id,
                "name": learner.user.name,
                "email": learner.user.email,
                "courses": 0,
                "completedLessons": 0,
                "progress": 0
            })
            continue

        # All lessons belonging to enrolled courses
        course_lessons = (
            Lesson.query
            .join(
                Module,
                Lesson.module_id == Module.id
            )
            .filter(
                Module.course_id.in_(course_ids)
            )
            .all()
        )

        total_lessons = len(course_lessons)

        lesson_ids = [
            lesson.id
            for lesson in course_lessons
        ]

        # Completed lessons for this learner
        completed_lessons = 0

        if lesson_ids:
            completed_lessons = (
                LessonProgress.query
                .filter(
                    LessonProgress.learner_id == learner.id,
                    LessonProgress.lesson_id.in_(lesson_ids),
                    LessonProgress.completed.is_(True)
                )
                .count()
            )

        # Overall progress
        progress = (
            int(
                (completed_lessons / total_lessons) * 100
            )
            if total_lessons
            else 0
        )

        leaderboard.append({
            "learner_id": learner.id,
            "user_id": learner.user_id,
            "name": learner.user.name,
            "email": learner.user.email,
            "courses": len(course_ids),
            "completedLessons": completed_lessons,
            "progress": progress
        })

    # Highest progress first.
    # If progress is equal, completed lessons are used as the
    # second sorting value.
    leaderboard.sort(
        key=lambda item: (
            item["progress"],
            item["completedLessons"]
        ),
        reverse=True
    )

    # Add rank
    for index, learner_data in enumerate(
        leaderboard,
        start=1
    ):
        learner_data["rank"] = index

    return jsonify({
        "leaderboard": leaderboard
    }), 200

# ============================================================
# LEARNING TIME
# ============================================================

@api.get("/learner/learning-time")
@role_required("learner")
def learner_learning_time(user):
    learner = Learner.query.filter_by(user_id=user.id).first()

    if not learner:
        return jsonify({"error": "Learner profile not found"}), 404

    records = LearningTime.query.filter_by(
        learner_id=learner.id
    ).order_by(
        LearningTime.id.desc()
    ).all()

    total_seconds = 0

    for record in records:
        total_seconds += int(
            getattr(record, "duration_seconds", 0) or 0
        )

    return jsonify({
        "total_seconds": total_seconds,
        "total_minutes": round(total_seconds / 60, 2),
        "records": [
            {
                "id": record.id,
                "course_id": getattr(record, "course_id", None),
                "lesson_id": getattr(record, "lesson_id", None),
                "duration_seconds": getattr(
                    record,
                    "duration_seconds",
                    0
                ),
                "created_at": (
                    record.created_at.isoformat()
                    if getattr(record, "created_at", None)
                    else None
                )
            }
            for record in records
        ]
    })


@api.post("/learner/learning-time")
@role_required("learner")
def record_learning_time(user):
    learner = Learner.query.filter_by(user_id=user.id).first()

    if not learner:
        return jsonify({"error": "Learner profile not found"}), 404

    data = request.get_json(silent=True) or {}

    course_id = data.get("course_id")
    lesson_id = data.get("lesson_id")

    try:
        duration_seconds = int(
            data.get("duration_seconds", 0)
        )
    except (TypeError, ValueError):
        return jsonify({
            "error": "duration_seconds must be a valid integer"
        }), 400

    # Prevent clients from submitting an unreasonably large
    # amount of learning time in a single record.
    MAX_LEARNING_TIME_SECONDS = 60 * 60  # 1 hour

    if duration_seconds <= 0:
        return jsonify({
            "error": "duration_seconds must be greater than 0"
        }), 400

    if duration_seconds > MAX_LEARNING_TIME_SECONDS:
        return jsonify({
            "error": "duration_seconds cannot exceed 3600 seconds"
        }), 400

    # A learning-time record must belong to an active enrollment.
    if course_id:
        enrollment = Enrollment.query.filter_by(
            learner_id=learner.id,
            course_id=course_id,
            status="active"
        ).first()

        if not enrollment:
            return jsonify({
                "error": "Active course enrollment required"
            }), 403

    # If a lesson is supplied, make sure it belongs to the
    # specified course.
    if lesson_id:
        lesson = db.session.get(Lesson, lesson_id)

        if not lesson:
            return jsonify({
                "error": "Lesson not found"
            }), 404

        module = db.session.get(Module, lesson.module_id)

        if not module or module.course_id != course_id:
            return jsonify({
                "error": "Lesson not found for this course"
            }), 404

    record = LearningTime(
        learner_id=learner.id,
        course_id=course_id,
        lesson_id=lesson_id,
        duration_seconds=duration_seconds
    )

    db.session.add(record)
    db.session.commit()

    return jsonify({
        "message": "Learning time recorded",
        "duration_seconds": duration_seconds
    }), 201


# ============================================================
# ============================================================
# LEADERBOARD
# ============================================================

@api.get("/leaderboard")
@token_required
def leaderboard(user):

    learners = Learner.query.all()

    result = []

    for learner in learners:

        # Make sure learner has a user
        if not learner.user:
            continue

        # ----------------------------------------------------
        # GET ACTIVE / COMPLETED ENROLLMENTS
        # ----------------------------------------------------

        enrollments = Enrollment.query.filter(
            Enrollment.learner_id == learner.id,
            Enrollment.status.in_(["active", "completed"])
        ).all()

        course_ids = [
            enrollment.course_id
            for enrollment in enrollments
        ]

        # ----------------------------------------------------
        # NO ENROLLED COURSES
        # ----------------------------------------------------

        if not course_ids:

            result.append({
                "learner_id": learner.id,
                "user_id": learner.user_id,
                "name": learner.user.name,
                "email": learner.user.email,
                "courses": 0,
                "completedLessons": 0,
                "progress": 0
            })

            continue

        # ----------------------------------------------------
        # GET ALL LESSONS FROM ENROLLED COURSES
        # ----------------------------------------------------

        course_lessons = (
            Lesson.query
            .join(
                Module,
                Lesson.module_id == Module.id
            )
            .filter(
                Module.course_id.in_(course_ids)
            )
            .all()
        )

        total_lessons = len(course_lessons)

        # ----------------------------------------------------
        # GET LESSON IDS
        # ----------------------------------------------------

        lesson_ids = [
            lesson.id
            for lesson in course_lessons
        ]

        # ----------------------------------------------------
        # COUNT COMPLETED LESSONS
        # ----------------------------------------------------

        completed_lessons = 0

        if lesson_ids:

            completed_lessons = (
                LessonProgress.query
                .filter(
                    LessonProgress.learner_id == learner.id,
                    LessonProgress.lesson_id.in_(lesson_ids),
                    LessonProgress.completed == True
                )
                .count()
            )

        # ----------------------------------------------------
        # CALCULATE OVERALL PROGRESS
        # ----------------------------------------------------

        if total_lessons > 0:

            progress = int(
                (completed_lessons / total_lessons) * 100
            )

        else:

            progress = 0

        # ----------------------------------------------------
        # ADD LEARNER TO LEADERBOARD
        # ----------------------------------------------------

        result.append({
            "learner_id": learner.id,
            "user_id": learner.user_id,
            "name": learner.user.name,
            "email": learner.user.email,
            "courses": len(course_ids),
            "completedLessons": completed_lessons,
            "progress": progress
        })

    # --------------------------------------------------------
    # SORT LEADERBOARD
    # --------------------------------------------------------

    result.sort(
        key=lambda item: (
            item["progress"],
            item["completedLessons"]
        ),
        reverse=True
    )

    # --------------------------------------------------------
    # ADD RANK
    # --------------------------------------------------------

    for index, item in enumerate(result, start=1):

        item["rank"] = index

    return jsonify({
        "leaderboard": result
    }), 200


# ============================================================
# CERTIFICATES
# ============================================================

@api.get("/learner/certificates")
@role_required("learner")
def learner_certificates(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Certificate.query
        .filter_by(
            learner_id=learner.id
        )
        .order_by(
            Certificate.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    certificates = pagination.items

    result = []

    for certificate in certificates:
        course = Course.query.get(
            certificate.course_id
        )

        result.append({
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "course_id": certificate.course_id,
            "course_title": (
                course.title
                if course
                else None
            ),
            "start_date": (
                certificate.start_date.isoformat()
                if certificate.start_date
                else None
            ),
            "end_date": (
                certificate.end_date.isoformat()
                if certificate.end_date
                else None
            ),
            "created_at": (
                certificate.created_at.isoformat()
                if certificate.created_at
                else None
            ),
            "status": certificate.status
        })

    return jsonify({
        "certificates": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.get("/learner/certificates/<int:certificate_id>")
@role_required("learner")
def learner_certificate_detail(
    user,
    certificate_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    certificate = Certificate.query.filter_by(
        id=certificate_id,
        learner_id=learner.id
    ).first()

    if not certificate:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    course = Course.query.get(
        certificate.course_id
    )

    learner_user = User.query.get(
        learner.user_id
    )

    return jsonify({
        "id": certificate.id,
        "certificate_id": certificate.certificate_id,
        "learner_id": learner.id,
        "learner_name": (
            user.name
            if user
            else None
        ),
        "course_id": certificate.course_id,
        "course_title": (
            course.title
            if course
            else None
        ),
        "start_date": (
            certificate.start_date.isoformat()
            if certificate.start_date
            else None
        ),
        "end_date": (
            certificate.end_date.isoformat()
            if certificate.end_date
            else None
        ),
        "created_at": (
            certificate.created_at.isoformat()
            if certificate.created_at
            else None
        ),
        "status": certificate.status
    })

@api.get("/learner/certificates/<int:certificate_id>/pdf")
@role_required("learner")
def learner_certificate_pdf(user, certificate_id):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    certificate = Certificate.query.filter_by(
        id=certificate_id,
        learner_id=learner.id
    ).first()

    if not certificate:
        return jsonify({
            "error": "Certificate not found"
        }), 404

    course = db.session.get(
        Course,
        certificate.course_id
    )

    learner_user = db.session.get(
        User,
        learner.user_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    if not learner_user:
        return jsonify({
            "error": "Learner user not found"
        }), 404

    # ---------------------------------------------------------
    # PUBLIC VERIFICATION URL
    # ---------------------------------------------------------

    frontend_origin = current_app.config.get(
        "FRONTEND_ORIGIN",
        "http://localhost:5173"
    ).rstrip("/")

    verification_url = (
        f"{frontend_origin}/verify/"
        f"{certificate.certificate_id}"
    )

    # ---------------------------------------------------------
    # QR CODE
    # ---------------------------------------------------------

    qr = qrcode.QRCode(
        version=1,
        box_size=8,
        border=4,
    )

    qr.add_data(verification_url)
    qr.make(fit=True)

    qr_image = qr.make_image(
        fill_color="black",
        back_color="white"
    )

    qr_buffer = BytesIO()
    qr_image.save(
        qr_buffer,
        format="PNG"
    )
    qr_buffer.seek(0)

    # ---------------------------------------------------------
    # PDF BUFFER
    # ---------------------------------------------------------

    pdf_buffer = BytesIO()

    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(A4),
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "CertificateTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=30,
        leading=36,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceAfter=8 * mm,
    )

    subtitle_style = ParagraphStyle(
        "CertificateSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=14,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#4B5563"),
    )

    learner_style = ParagraphStyle(
        "LearnerName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#111827"),
        spaceBefore=5 * mm,
        spaceAfter=5 * mm,
    )

    course_style = ParagraphStyle(
        "CourseName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=26,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=8 * mm,
    )

    detail_style = ParagraphStyle(
        "CertificateDetails",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#374151"),
    )

    story = []

    story.append(
        Paragraph(
            "CERTIFICATE OF COMPLETION",
            title_style
        )
    )

    story.append(
        Paragraph(
            "This certificate is proudly presented to",
            subtitle_style
        )
    )

    story.append(
        Paragraph(
            learner_user.name,
            learner_style
        )
    )

    story.append(
        Paragraph(
            f"for successfully completing the course<br/>"
            f"<b>{course.title}</b>",
            course_style
        )
    )

    start_date = (
        certificate.start_date.strftime("%d %B %Y")
        if certificate.start_date
        else "—"
    )

    end_date = (
        certificate.end_date.strftime("%d %B %Y")
        if certificate.end_date
        else "—"
    )

    issued_date = (
        certificate.created_at.strftime("%d %B %Y")
        if certificate.created_at
        else "—"
    )

    details = [
        [
            Paragraph(
                f"<b>Certificate ID:</b><br/>"
                f"{certificate.certificate_id}",
                detail_style
            ),
            Paragraph(
                f"<b>Course Period:</b><br/>"
                f"{start_date} — {end_date}",
                detail_style
            ),
            Paragraph(
                f"<b>Issued:</b><br/>"
                f"{issued_date}",
                detail_style
            ),
        ]
    ]

    details_table = Table(
        details,
        colWidths=[
            75 * mm,
            75 * mm,
            55 * mm,
        ],
    )

    details_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.5,
                colors.HexColor("#D1D5DB")
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.25,
                colors.HexColor("#E5E7EB")
            ),
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                colors.HexColor("#F9FAFB")
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
        ])
    )

    story.append(
        details_table
    )

    story.append(
        Spacer(
            1,
            8 * mm
        )
    )

    qr_image_for_pdf = Image(
        qr_buffer,
        width=32 * mm,
        height=32 * mm,
    )

    verification_text = Paragraph(
        "<b>Verify this certificate</b><br/>"
        "Scan the QR code or use the certificate ID "
        "on the public verification page.",
        detail_style
    )

    verification_table = Table(
        [[qr_image_for_pdf, verification_text]],
        colWidths=[
            40 * mm,
            100 * mm,
        ],
    )

    verification_table.setStyle(
        TableStyle([
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "ALIGN",
                (0, 0),
                (0, 0),
                "CENTER"
            ),
        ])
    )

    story.append(
        verification_table
    )

    story.append(
        Spacer(
            1,
            5 * mm
        )
    )

    status_text = (
        "VALID"
        if certificate.status == "valid"
        else certificate.status.upper()
    )

    status_style = ParagraphStyle(
        "CertificateStatus",
        parent=detail_style,
        fontName="Helvetica-Bold",
        fontSize=11,
        alignment=TA_CENTER,
        textColor=(
            colors.HexColor("#166534")
            if certificate.status == "valid"
            else colors.HexColor("#991B1B")
        ),
    )

    story.append(
        Paragraph(
            f"Certificate Status: {status_text}",
            status_style
        )
    )

    document.build(story)

    pdf_buffer.seek(0)

    filename = (
        f"certificate-{certificate.certificate_id}.pdf"
    )

    from flask import send_file

    return send_file(
        pdf_buffer,
        mimetype="application/pdf",
        as_attachment=True,
        download_name=filename,
    )

@api.get("/certificates/<string:certificate_number>")
def verify_certificate(certificate_number):
    certificate = Certificate.query.filter_by(
        certificate_id=certificate_number
    ).first()

    if not certificate:
        return jsonify({
            "valid": False,
            "error": "Certificate not found"
        }), 404

    course = db.session.get(
        Course,
        certificate.course_id
    )

    return jsonify({
        "valid": certificate.status == "valid",
        "certificate": {
            "certificate_id": certificate.certificate_id,
            "course_title": (
                course.title
                if course
                else None
            ),
            "start_date": (
                certificate.start_date.isoformat()
                if certificate.start_date
                else None
            ),
            "end_date": (
                certificate.end_date.isoformat()
                if certificate.end_date
                else None
            ),
            "status": certificate.status
        }
    })


# ============================================================
# TRAINER — COURSE LEARNERS
# ============================================================

@api.get("/trainer/courses/<string:course_id>/learners")
@role_required("trainer")
def trainer_course_learners(user, course_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    try:
        page = max(
        int(request.args.get("page", 1)),
        1
    )
    except (TypeError, ValueError):
         page = 1

    try:
        limit = min(
        max(
            int(request.args.get("limit", 20)),
            1
        ),
        100
    )
    except (TypeError, ValueError):
     limit = 20

    pagination = (
         Enrollment.query
        .filter_by(
            course_id=course_id
        )
        .order_by(
            Enrollment.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
)

    enrollments = pagination.items

    result = []

    for enrollment in enrollments:
        learner = Learner.query.get(
            enrollment.learner_id
        )

        if not learner:
            continue

        learner_user = User.query.get(
            learner.user_id
        )

        result.append({
            "enrollment_id": enrollment.id,
            "learner_id": learner.id,
            "name": (
                learner_user.name
                if learner_user
                else None
            ),
            "email": (
                learner_user.email
                if learner_user
                else None
            ),
            "mobile": (
                learner_user.mobile
                if learner_user
                else None
            ),
            "progress": int(
                enrollment.progress or 0
            ),
            "status": enrollment.status,
            "enrolled_at": (
                enrollment.enrolled_at.isoformat()
                if enrollment.enrolled_at
                else None
            )
        })

    return jsonify({
    "course": course_json(course),
    "learners": result,
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})

# ============================================================
# TRAINER ANALYTICS
# ============================================================

@api.get("/trainer/analytics")
@role_required("trainer")
def trainer_analytics(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    # --------------------------------------------------------
    # Get all courses owned by this trainer
    # --------------------------------------------------------

    courses = Course.query.filter_by(
        trainer_id=trainer.id
    ).all()

    course_ids = [
        course.id
        for course in courses
    ]

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_courses = len(courses)

    total_learners = (
        db.session.query(
            db.func.count(
                db.distinct(Enrollment.learner_id)
            )
        )
        .filter(
            Enrollment.course_id.in_(course_ids)
        )
        .scalar()
        if course_ids
        else 0
    )

    total_assignments = (
        Assignment.query
        .filter(
            Assignment.course_id.in_(course_ids)
        )
        .count()
        if course_ids
        else 0
    )

    total_quizzes = (
        Quiz.query
        .filter(
            Quiz.course_id.in_(course_ids)
        )
        .count()
        if course_ids
        else 0
    )

    # --------------------------------------------------------
    # LESSON DROP-OFF ANALYTICS
    # --------------------------------------------------------

    lesson_dropoff = []

    if course_ids:

        modules = Module.query.filter(
            Module.course_id.in_(course_ids)
        ).all()

        module_map = {
            module.id: module
            for module in modules
        }

        module_ids = [
            module.id
            for module in modules
        ]

        lessons = (
            Lesson.query
            .filter(
                Lesson.module_id.in_(module_ids)
            )
            .order_by(
                Lesson.order_no.asc()
            )
            .all()
            if module_ids
            else []
        )

        for lesson in lessons:

            module = module_map.get(
                lesson.module_id
            )

            if not module:
                continue

            course = next(
                (
                    c for c in courses
                    if c.id == module.course_id
                ),
                None
            )

            if not course:
                continue

            progress_rows = (
                LessonProgress.query
                .filter_by(
                    lesson_id=lesson.id
                )
                .all()
            )

            started_count = len(
                progress_rows
            )

            completed_count = sum(
                1
                for row in progress_rows
                if row.completed
            )

            dropoff_count = max(
                started_count - completed_count,
                0
            )

            dropoff_percentage = (
                round(
                    (
                        dropoff_count
                        /
                        started_count
                    ) * 100,
                    2
                )
                if started_count
                else 0
            )

            lesson_dropoff.append({

                "lesson_id": lesson.id,

                "lesson_title": lesson.title,

                "course_id": course.id,

                "course_title": course.title,

                "duration": lesson.duration,

                "started": started_count,

                "completed": completed_count,

                "dropoff": dropoff_count,

                "dropoff_percentage":
                    dropoff_percentage
            })

    # --------------------------------------------------------
    # QUIZ QUESTION ANALYTICS
    # --------------------------------------------------------

    quiz_questions = []

    if course_ids:

        quizzes = Quiz.query.filter(
            Quiz.course_id.in_(course_ids)
        ).all()

        quiz_map = {
            quiz.id: quiz
            for quiz in quizzes
        }

        quiz_ids = [
            quiz.id
            for quiz in quizzes
        ]

        questions = (
            Question.query
            .filter(
                Question.quiz_id.in_(quiz_ids)
            )
            .order_by(
                Question.id.asc()
            )
            .all()
            if quiz_ids
            else []
        )

        for question in questions:

            quiz = quiz_map.get(
                question.quiz_id
            )

            if not quiz:
                continue

            answers = (
                QuizAnswer.query
                .filter_by(
                    question_id=question.id
                )
                .all()
            )

            answered_count = sum(
                1
                for answer in answers
                if answer.selected_answer
                is not None
            )

            correct_count = sum(
                1
                for answer in answers
                if answer.is_correct
            )

            wrong_count = sum(
                1
                for answer in answers
                if (
                    answer.selected_answer
                    is not None
                    and not answer.is_correct
                )
            )

            wrong_percentage = (
                round(
                    (
                        wrong_count
                        /
                        answered_count
                    ) * 100,
                    2
                )
                if answered_count
                else 0
            )

            quiz_questions.append({

                "question_id":
                    question.id,

                "quiz_id":
                    quiz.id,

                "quiz_title":
                    quiz.title,

                "course_id":
                    quiz.course_id,

                "question":
                    question.question_text,

                "attempts":
                    answered_count,

                "correct":
                    correct_count,

                "wrong":
                    wrong_count,

                "wrong_percentage":
                    wrong_percentage
            })

    # --------------------------------------------------------
    # ASSIGNMENT ANALYTICS
    # --------------------------------------------------------

    assignments = []

    if course_ids:

        assignment_rows = (
            Assignment.query
            .filter(
                Assignment.course_id.in_(course_ids)
            )
            .order_by(
                Assignment.id.desc()
            )
            .all()
        )

        for assignment in assignment_rows:

            enrollments = (
                Enrollment.query
                .filter_by(
                    course_id=assignment.course_id
                )
                .all()
            )

            enrolled_count = len(
                enrollments
            )

            on_time_count = 0
            late_count = 0
            missing_count = 0
            no_due_date_count = 0

            for enrollment in enrollments:

                submission = (
                    AssignmentSubmission.query
                    .filter_by(
                        assignment_id=assignment.id,
                        learner_id=(
                            enrollment.learner_id
                        )
                    )
                    .first()
                )

                if (
                    not assignment.due_date
                ):
                    if (
                        submission
                        and submission.submitted_at
                    ):
                        no_due_date_count += 1

                    continue

                if (
                    submission
                    and submission.submitted_at
                ):

                    submitted_at = (
                        submission.submitted_at
                    )

                    due_date = (
                        assignment.due_date
                    )

                    # Handle timezone differences
                    if (
                        submitted_at.tzinfo
                        is None
                    ):
                        submitted_at = (
                            submitted_at.replace(
                                tzinfo=timezone.utc
                            )
                        )

                    if (
                        due_date.tzinfo
                        is None
                    ):
                        due_date = (
                            due_date.replace(
                                tzinfo=timezone.utc
                            )
                        )

                    if submitted_at <= due_date:
                        on_time_count += 1
                    else:
                        late_count += 1

                else:

                    now = datetime.now(
                        timezone.utc
                    )

                    due_date = (
                        assignment.due_date
                    )

                    if (
                        due_date.tzinfo
                        is None
                    ):
                        due_date = (
                            due_date.replace(
                                tzinfo=timezone.utc
                            )
                        )

                    if now > due_date:
                        missing_count += 1

            assignments.append({

                "assignment_id":
                    assignment.id,

                "title":
                    assignment.title,

                "course_id":
                    assignment.course_id,

                "due_date": (
                    assignment.due_date.isoformat()
                    if assignment.due_date
                    else None
                ),

                "enrolled":
                    enrolled_count,

                "on_time":
                    on_time_count,

                "late":
                    late_count,

                "missing":
                    missing_count,

                "no_due_date":
                    no_due_date_count
            })

    # --------------------------------------------------------
    # Sort lesson drop-off by highest drop-off
    # --------------------------------------------------------

    lesson_dropoff.sort(
        key=lambda item:
            item["dropoff_percentage"],
        reverse=True
    )

    # --------------------------------------------------------
    # Sort quiz questions by highest wrong percentage
    # --------------------------------------------------------

    quiz_questions.sort(
        key=lambda item:
            item["wrong_percentage"],
        reverse=True
    )

    # --------------------------------------------------------
    # SUMMARY COUNTS
    # --------------------------------------------------------

    total_lesson_started = sum(
        item["started"]
        for item in lesson_dropoff
    )

    total_lesson_completed = sum(
        item["completed"]
        for item in lesson_dropoff
    )

    total_lesson_dropoff = sum(
        item["dropoff"]
        for item in lesson_dropoff
    )

    total_on_time = sum(
        item["on_time"]
        for item in assignments
    )

    total_late = sum(
        item["late"]
        for item in assignments
    )

    total_missing = sum(
        item["missing"]
        for item in assignments
    )

    return jsonify({

        "summary": {

            "courses":
                total_courses,

            "learners":
                total_learners,

            "assignments":
                total_assignments,

            "quizzes":
                total_quizzes,

            "lesson_started":
                total_lesson_started,

            "lesson_completed":
                total_lesson_completed,

            "lesson_dropoff":
                total_lesson_dropoff,

            "assignment_on_time":
                total_on_time,

            "assignment_late":
                total_late,

            "assignment_missing":
                total_missing
        },

        "lesson_dropoff":
            lesson_dropoff,

        "quiz_questions":
            quiz_questions,

        "assignments":
            assignments

    }), 200


# ============================================================
# TRAINER — ALL STUDENTS
# ============================================================

@api.get("/trainer/students")
@role_required("trainer")
def trainer_students(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    # --------------------------------------------------------
    # QUERY PARAMETERS
    # --------------------------------------------------------

    search = (
        request.args.get("search", "")
        .strip()
        .lower()
    )

    needs_attention_param = (
        request.args.get(
            "needs_attention",
            ""
        )
        .strip()
        .lower()
    )

    # --------------------------------------------------------
    # GET TRAINER'S COURSES
    # --------------------------------------------------------

    courses = Course.query.filter_by(
        trainer_id=trainer.id
    ).all()

    course_ids = [
        course.id
        for course in courses
    ]

    course_map = {
        course.id: course
        for course in courses
    }

    if not course_ids:
        return jsonify({
            "students": [],
            "total": 0
        }), 200

    # --------------------------------------------------------
    # GET ENROLLMENTS
    # --------------------------------------------------------

    enrollments = (
        Enrollment.query
        .filter(
            Enrollment.course_id.in_(
                course_ids
            )
        )
        .order_by(
            Enrollment.id.desc()
        )
        .all()
    )

    students = []

    # --------------------------------------------------------
    # BUILD STUDENT DATA
    # --------------------------------------------------------

    for enrollment in enrollments:

        learner = Learner.query.get(
            enrollment.learner_id
        )

        if not learner:
            continue

        learner_user = User.query.get(
            learner.user_id
        )

        if not learner_user:
            continue

        course = course_map.get(
            enrollment.course_id
        )

        if not course:
            continue

        # ----------------------------------------------------
        # SEARCH
        # ----------------------------------------------------

        searchable_text = (
            f"{learner_user.name or ''} "
            f"{learner_user.email or ''}"
        ).lower()

        if search and search not in searchable_text:
            continue

        # ----------------------------------------------------
        # LAST ACTIVE
        # ----------------------------------------------------

        last_active = None

        last_progress = (
            db.session.query(LessonProgress)
            .join(
                Lesson,
                Lesson.id == LessonProgress.lesson_id
            )
            .join(
                Module,
                Module.id == Lesson.module_id
            )
            .filter(
                LessonProgress.learner_id == learner.id,
                Module.course_id == course.id
            )
            .order_by(
                LessonProgress.updated_at.desc()
            )
            .first()
        )

        if last_progress:
            last_active = last_progress.updated_at

        # ----------------------------------------------------
        # QUIZ SCORE
        # ----------------------------------------------------

        quiz_ids = [
            quiz.id
            for quiz in Quiz.query.filter_by(
                course_id=course.id
            ).all()
        ]

        score_percentage = None

        if quiz_ids:

            attempts = (
                QuizAttempt.query
                .filter(
                    QuizAttempt.learner_id
                    == learner.id,

                    QuizAttempt.quiz_id.in_(
                        quiz_ids
                    ),

                    QuizAttempt.attempted_at
                    != None
                )
                .order_by(
                    QuizAttempt.attempted_at.desc()
                )
                .all()
            )

            if attempts:

                total_score = 0
                total_possible = 0

                for attempt in attempts:

                    total_score += (
                        attempt.score or 0
                    )

                    total_possible += (
                        attempt.total or 0
                    )

                if total_possible > 0:

                    score_percentage = round(
                        (
                            total_score
                            / total_possible
                        ) * 100,
                        2
                    )

        # ----------------------------------------------------
        # NEEDS ATTENTION
        # ----------------------------------------------------

        progress_value = int(
            enrollment.progress or 0
        )

        needs_attention = False

        # Low progress
        if progress_value < 40:
            needs_attention = True

        # No recent activity
        if last_active is None:
            needs_attention = True

        # Low quiz score
        if (
            score_percentage is not None
            and score_percentage < 50
        ):
            needs_attention = True

        # ----------------------------------------------------
        # FILTER
        # ----------------------------------------------------

        if needs_attention_param in (
            "true",
            "1",
            "yes"
        ):
            if not needs_attention:
                continue

        elif needs_attention_param in (
            "false",
            "0",
            "no"
        ):
            if needs_attention:
                continue

        # ----------------------------------------------------
        # RESULT
        # ----------------------------------------------------

        students.append({

            "learner_id":
                learner.id,

            "enrollment_id":
                enrollment.id,

            "name":
                learner_user.name,

            "email":
                learner_user.email,

            "mobile":
                learner_user.mobile,

            "course_id":
                course.id,

            "course_title":
                course.title,

            "progress":
                progress_value,

            "score":
                score_percentage,

            "last_active":
                (
                    last_active.isoformat()
                    if last_active
                    else None
                ),

            "status":
                enrollment.status,

            "enrolled_at":
                (
                    enrollment.enrolled_at.isoformat()
                    if enrollment.enrolled_at
                    else None
                ),

            "needs_attention":
                needs_attention
        })

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({

        "students": students,

        "total": len(students)

    }), 200

# ============================================================
# TRAINER — ATTENDANCE
# ============================================================

@api.get("/trainer/batches")
@role_required("trainer")
def trainer_batches(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    batches = (
        Batch.query
        .filter_by(trainer_id=trainer.id)
        .order_by(Batch.id.desc())
        .all()
    )

    result = []

    for batch in batches:
        learner_count = Learner.query.filter_by(
            batch_id=batch.id
        ).count()

        course = (
            db.session.get(Course, batch.course_id)
            if batch.course_id
            else None
        )

        result.append({
            "id": batch.id,
            "name": batch.name,
            "course_id": batch.course_id,
            "course_title": (
                course.title
                if course
                else None
            ),
            "start_date": (
                batch.start_date.isoformat()
                if batch.start_date
                else None
            ),
            "end_date": (
                batch.end_date.isoformat()
                if batch.end_date
                else None
            ),
            "status": batch.status,
            "learner_count": learner_count
        })

    return jsonify({
        "batches": result,
        "total": len(result)
    }), 200


@api.get("/trainer/batches/<int:batch_id>/attendance")
@role_required("trainer")
def trainer_batch_attendance(user, batch_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    batch = Batch.query.filter_by(
        id=batch_id,
        trainer_id=trainer.id
    ).first()

    if not batch:
        return jsonify({
            "error": "Batch not found"
        }), 404

    date_value = request.args.get("date")

    if not date_value:
        return jsonify({
            "error": "Date is required"
        }), 400

    try:
        attendance_date = datetime.strptime(
            date_value,
            "%Y-%m-%d"
        ).date()
    except (TypeError, ValueError):
        return jsonify({
            "error": "Date must use YYYY-MM-DD format"
        }), 400

    learners = (
        Learner.query
        .filter_by(batch_id=batch.id)
        .order_by(Learner.id.asc())
        .all()
    )

    attendance_records = Attendance.query.filter_by(
        batch_id=batch.id,
        date=attendance_date
    ).all()

    attendance_by_learner = {
        record.learner_id: record
        for record in attendance_records
    }

    result = []

    for learner in learners:
        record = attendance_by_learner.get(
            learner.id
        )

        result.append({
            "learner_id": learner.id,
            "name": (
                learner.user.name
                if learner.user
                else None
            ),
            "email": (
                learner.user.email
                if learner.user
                else None
            ),
            "status": (
                record.status
                if record
                else None
            ),
            "attendance_id": (
                record.id
                if record
                else None
            )
        })

    return jsonify({
        "batch": {
            "id": batch.id,
            "name": batch.name
        },
        "date": attendance_date.isoformat(),
        "learners": result,
        "total": len(result)
    }), 200


@api.post("/trainer/batches/<int:batch_id>/attendance")
@role_required("trainer")
def trainer_mark_batch_attendance(user, batch_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    batch = Batch.query.filter_by(
        id=batch_id,
        trainer_id=trainer.id
    ).first()

    if not batch:
        return jsonify({
            "error": "Batch not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    date_value = data.get("date")
    records = data.get("attendance")

    if not date_value:
        return jsonify({
            "error": "Date is required"
        }), 400

    if not isinstance(records, list):
        return jsonify({
            "error": "attendance must be a list"
        }), 400

    try:
        attendance_date = datetime.strptime(
            str(date_value),
            "%Y-%m-%d"
        ).date()
    except (TypeError, ValueError):
        return jsonify({
            "error": "Date must use YYYY-MM-DD format"
        }), 400

    valid_statuses = {
        "present",
        "absent",
        "late"
    }

    learner_ids = {
        learner.id
        for learner in Learner.query.filter_by(
            batch_id=batch.id
        ).all()
    }

    updated = []

    for item in records:
        if not isinstance(item, dict):
            return jsonify({
                "error": "Each attendance record must be an object"
            }), 400

        learner_id = item.get("learner_id")
        status = str(
            item.get("status", "")
        ).strip().lower()

        if learner_id is None:
            return jsonify({
                "error": "learner_id is required"
            }), 400

        try:
            learner_id = int(learner_id)
        except (TypeError, ValueError):
            return jsonify({
                "error": "learner_id must be an integer"
            }), 400

        if learner_id not in learner_ids:
            return jsonify({
                "error": (
                    f"Learner {learner_id} "
                    "does not belong to this batch"
                )
            }), 400

        if status not in valid_statuses:
            return jsonify({
                "error": (
                    "Status must be present, absent, or late"
                )
            }), 400

        record = Attendance.query.filter_by(
            learner_id=learner_id,
            batch_id=batch.id,
            date=attendance_date
        ).first()

        if record:
            record.status = status
            record.marked_by = user.id
        else:
            record = Attendance(
                learner_id=learner_id,
                batch_id=batch.id,
                date=attendance_date,
                status=status,
                marked_by=user.id
            )
            db.session.add(record)

        updated.append({
            "learner_id": learner_id,
            "status": status
        })

    db.session.commit()

    return jsonify({
        "message": "Attendance saved successfully",
        "batch_id": batch.id,
        "date": attendance_date.isoformat(),
        "attendance": updated
    }), 200


# ============================================================
# TRAINER — LEARNER PROGRESS
# ============================================================

@api.get(
    "/trainer/courses/<string:course_id>/learners/<int:learner_id>/progress"
)
@role_required("trainer")
def trainer_learner_progress(
    user,
    course_id,
    learner_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    learner = Learner.query.get(
        learner_id
    )

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner_id,
        course_id=course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "Learner is not enrolled in this course"
        }), 404

    lessons = Lesson.query.filter_by(
        course_id=course_id
    ).all()

    lesson_ids = [
        lesson.id
        for lesson in lessons
    ]

    progress_records = []

    if lesson_ids:
        progress_records = LessonProgress.query.filter(
            LessonProgress.learner_id == learner_id,
            LessonProgress.lesson_id.in_(lesson_ids)
        ).all()

    progress_map = {
        record.lesson_id: bool(record.completed)
        for record in progress_records
    }

    learner_user = User.query.get(
        learner.user_id
    )

    return jsonify({
        "learner": {
            "id": learner.id,
            "name": (
                learner_user.name
                if learner_user
                else None
            ),
            "email": (
                learner_user.email
                if learner_user
                else None
            )
        },
        "course": course_json(course),
        "progress": int(
            enrollment.progress or 0
        ),
        "status": enrollment.status,
        "lessons": [
            {
                "id": lesson.id,
                "title": lesson.title,
                "completed": progress_map.get(
                    lesson.id,
                    False
                )
            }
            for lesson in lessons
        ]
    })
# ============================================================
# ASSIGNMENTS
# ============================================================

@api.post("/trainer/courses/<string:course_id>/assignments")
@role_required("trainer")
def trainer_create_assignment(user, course_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    due_date = parse_datetime(
        data.get("due_date")
    )

    if not title:
        return jsonify({
            "error": "Assignment title is required"
        }), 400

    assignment = Assignment(
        course_id=course_id,
        trainer_id=trainer.id,
        title=title,
        description=description,
        due_date=due_date
    )

    db.session.add(assignment)
    db.session.commit()

    return jsonify({
        "message": "Assignment created successfully",
        "assignment": assignment_json(assignment)
    }), 201


@api.get("/trainer/courses/<string:course_id>/assignments")
@role_required("trainer")
def trainer_assignments(user, course_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Assignment.query
        .filter_by(
            course_id=course_id
        )
        .order_by(
            Assignment.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
)

    assignments = pagination.items

    return jsonify({
    "assignments": [
        assignment_json(assignment)
        for assignment in assignments
    ],
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


@api.get("/trainer/assignments/<int:assignment_id>")
@role_required("trainer")
def trainer_assignment_detail(
    user,
    assignment_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    assignment = Assignment.query.get(
        assignment_id
    )

    if not assignment:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    course = Course.query.filter_by(
        id=assignment.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        AssignmentSubmission.query
        .filter_by(
            assignment_id=assignment.id
        )
        .order_by(
            AssignmentSubmission.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
)

    submissions = pagination.items

    result = []

    for submission in submissions:
        learner = Learner.query.get(
            submission.learner_id
        )

        learner_user = (
            User.query.get(learner.user_id)
            if learner
            else None
        )

        result.append({
            "id": submission.id,
            "learner_id": submission.learner_id,
            "learner_name": (
                user.name
                if user
                else None
            ),
            "learner_email": (
                user.email
                if user
                else None
            ),
            "content": submission.submission,
            "submission": submission.submission,
            "submitted_at": (
                submission.submitted_at.isoformat()
                if submission.submitted_at
                else None
            ),
            "score": submission.grade,
            "grade": submission.grade,
            "feedback": submission.feedback
        })

    return jsonify({
    "assignment": assignment_json(
        assignment
    ),
    "submissions": result,
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})


@api.delete("/trainer/assignments/<int:assignment_id>")
@role_required("trainer")
def trainer_delete_assignment(
    user,
    assignment_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    assignment = Assignment.query.get(
        assignment_id
    )

    if not assignment:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    course = Course.query.filter_by(
        id=assignment.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(assignment)
    db.session.commit()

    return jsonify({
        "message": "Assignment deleted successfully"
    })


# ------------------------------------------------------------
# LEARNER ASSIGNMENTS
# ------------------------------------------------------------

@api.get("/learner/courses/<string:course_id>/assignments")
@role_required("learner")
def learner_course_assignments(
    user,
    course_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Assignment.query
        .filter_by(
            course_id=course_id
        )
        .order_by(
            Assignment.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
)

    assignments = pagination.items
    result = []

    for assignment in assignments:
        item = assignment_json(
            assignment
        )

        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.id,
            learner_id=learner.id
        ).first()

        item["submitted"] = bool(
            submission
            and submission.submitted_at
        )

        item["submission"] = (
            submission.submission
            if submission
            else None
        )

        item["content"] = (
            submission.submission
            if submission
            else None
        )

        item["submitted_at"] = (
            submission.submitted_at.isoformat()
            if submission
            and submission.submitted_at
            else None
        )

        item["grade"] = (
            submission.grade
            if submission
            else None
        )

        item["score"] = (
            submission.grade
            if submission
            else None
        )

        item["feedback"] = (
            submission.feedback
            if submission
            else None
        )

        result.append(item)

    return jsonify({
    "assignments": result,
    "pagination": {
        "page": pagination.page,
        "limit": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
        "has_next": pagination.has_next,
        "has_previous": pagination.has_prev
    }
})

@api.get("/learner/assignments/<int:assignment_id>")
@role_required("learner")
def learner_assignment_detail(
    user,
    assignment_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    assignment = Assignment.query.get(
        assignment_id
    )

    if not assignment:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=assignment.course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        learner_id=learner.id
    ).first()

    response = assignment_json(
        assignment
    )

    response["submitted"] = bool(
        submission
        and submission.submitted_at
    )

    response["submission"] = (
        submission.submission
        if submission
        else None
    )

    response["content"] = (
        submission.submission
        if submission
        else None
    )

    response["submitted_at"] = (
        submission.submitted_at.isoformat()
        if submission
        and submission.submitted_at
        else None
    )

    response["grade"] = (
        submission.grade
        if submission
        else None
    )

    response["score"] = (
        submission.grade
        if submission
        else None
    )

    response["feedback"] = (
        submission.feedback
        if submission
        else None
    )

    return jsonify(response)


@api.post("/learner/assignments/<int:assignment_id>/submit")
@role_required("learner")
def learner_submit_assignment(
    user,
    assignment_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    assignment = Assignment.query.get(
        assignment_id
    )

    if not assignment:
        return jsonify({
            "error": "Assignment not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=assignment.course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    data = request.get_json(silent=True) or {}

    submission_text = data.get(
        "submission"
    )

    if submission_text is None:
        submission_text = data.get(
            "content",
            ""
        )

    submission_text = str(
        submission_text
    ).strip()

    if not submission_text:
        return jsonify({
            "error": "Submission content is required"
        }), 400

    submission = AssignmentSubmission.query.filter_by(
        assignment_id=assignment.id,
        learner_id=learner.id
    ).first()

    if not submission:
        submission = AssignmentSubmission(
            assignment_id=assignment.id,
            learner_id=learner.id
        )
        db.session.add(submission)

    submission.submission = submission_text
    submission.submitted_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({
        "message": "Assignment submitted successfully",
        "submission": {
            "id": submission.id,
            "assignment_id": submission.assignment_id,
            "learner_id": submission.learner_id,
            "submission": submission.submission,
            "content": submission.submission,
            "submitted_at": (
                submission.submitted_at.isoformat()
                if submission.submitted_at
                else None
            ),
            "grade": submission.grade,
            "score": submission.grade,
            "feedback": submission.feedback
        }
    })

# ============================================================
# QUESTION BANK
# ============================================================

@api.post("/trainer/question-banks")
@role_required("trainer")
def create_question_bank(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Question bank title is required"
        }), 400

    bank = QuestionBank(
        trainer_id=trainer.id,
        title=title,
        description=description
    )

    db.session.add(bank)
    db.session.commit()

    return jsonify({
        "message": "Question bank created successfully",
        "bank": {
            "id": bank.id,
            "trainer_id": bank.trainer_id,
            "title": bank.title,
            "description": bank.description,
            "created_at": (
                bank.created_at.isoformat()
                if bank.created_at
                else None
            )
        }
    }), 201


@api.get("/trainer/question-banks")
@role_required("trainer")
def get_question_banks(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    banks = (
        QuestionBank.query
        .filter_by(
            trainer_id=trainer.id
        )
        .order_by(
            QuestionBank.id.desc()
        )
        .all()
    )

    return jsonify({
        "banks": [
            {
                "id": bank.id,
                "title": bank.title,
                "description": bank.description,
                "created_at": (
                    bank.created_at.isoformat()
                    if bank.created_at
                    else None
                )
            }
            for bank in banks
        ]
    }), 200


@api.get("/trainer/question-banks/<int:bank_id>")
@role_required("trainer")
def get_question_bank(user, bank_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question bank not found"
        }), 404

    questions = (
        QuestionBankItem.query
        .filter_by(
            bank_id=bank.id
        )
        .order_by(
            QuestionBankItem.id.asc()
        )
        .all()
    )

    return jsonify({
        "bank": {
            "id": bank.id,
            "title": bank.title,
            "description": bank.description,
            "created_at": (
                bank.created_at.isoformat()
                if bank.created_at
                else None
            ),
            "questions": [
                {
                    "id": question.id,
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                    "option_a": question.option_a,
                    "option_b": question.option_b,
                    "option_c": question.option_c,
                    "option_d": question.option_d,
                    "correct_answer": question.correct_answer,
                    "coding_description": question.coding_description,
                    "starter_code": question.starter_code,
                    "language": question.language,
                    "difficulty": question.difficulty,
                    "marks": question.marks,
                    "created_at": (
                        question.created_at.isoformat()
                        if question.created_at
                        else None
                    )
                }
                for question in questions
            ]
        }
    }), 200


@api.put("/trainer/question-banks/<int:bank_id>")
@role_required("trainer")
def update_question_bank(user, bank_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question bank not found"
        }), 404

    data = request.get_json(silent=True) or {}

    if "title" in data:
        title = str(
            data.get("title", "")
        ).strip()

        if not title:
            return jsonify({
                "error": "Question bank title is required"
            }), 400

        bank.title = title

    if "description" in data:
        bank.description = str(
            data.get("description", "")
        ).strip()

    db.session.commit()

    return jsonify({
        "message": "Question bank updated successfully"
    }), 200


@api.delete("/trainer/question-banks/<int:bank_id>")
@role_required("trainer")
def delete_question_bank(user, bank_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question bank not found"
        }), 404

    QuestionBankItem.query.filter_by(
        bank_id=bank.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(bank)
    db.session.commit()

    return jsonify({
        "message": "Question bank deleted successfully"
    }), 200


# ============================================================
# QUESTION BANK ITEMS
# ============================================================

@api.post("/trainer/question-banks/<int:bank_id>/questions")
@role_required("trainer")
def create_question_bank_item(user, bank_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question bank not found"
        }), 404

    data = request.get_json(silent=True) or {}

    question_type = str(
        data.get("question_type", "")
    ).strip().lower()

    question_text = str(
        data.get("question_text", "")
    ).strip()

    if question_type not in (
        "mcq",
        "coding"
    ):
        return jsonify({
            "error": "question_type must be mcq or coding"
        }), 400

    if not question_text:
        return jsonify({
            "error": "question_text is required"
        }), 400

    question = QuestionBankItem(
        bank_id=bank.id,
        question_type=question_type,
        question_text=question_text,
        option_a=data.get("option_a"),
        option_b=data.get("option_b"),
        option_c=data.get("option_c"),
        option_d=data.get("option_d"),
        correct_answer=data.get("correct_answer"),
        coding_description=data.get(
            "coding_description",
            ""
        ),
        starter_code=data.get(
            "starter_code",
            ""
        ),
        language=data.get(
            "language",
            "python"
        ),
        difficulty=data.get(
            "difficulty",
            "medium"
        ),
        marks=int(
            data.get("marks", 1)
        )
    )

    if question_type == "mcq":
        if not question.correct_answer:
            return jsonify({
                "error": "correct_answer is required for MCQ"
            }), 400

    if question_type == "coding":
        question.coding_description = (
            str(
                data.get(
                    "coding_description",
                    ""
                )
            ).strip()
        )

        if not question.coding_description:
            return jsonify({
                "error": (
                    "coding_description is required "
                    "for coding questions"
                )
            }), 400

    db.session.add(question)
    db.session.commit()

    return jsonify({
        "message": "Question added to question bank",
        "question": {
            "id": question.id,
            "bank_id": question.bank_id,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "marks": question.marks
        }
    }), 201


@api.get(
    "/trainer/question-banks/<int:bank_id>/questions"
)
@role_required("trainer")
def get_question_bank_items(user, bank_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question bank not found"
        }), 404

    questions = (
        QuestionBankItem.query
        .filter_by(
            bank_id=bank.id
        )
        .order_by(
            QuestionBankItem.id.asc()
        )
        .all()
    )

    return jsonify({
        "questions": [
            {
                "id": question.id,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "correct_answer": question.correct_answer,
                "coding_description": question.coding_description,
                "starter_code": question.starter_code,
                "language": question.language,
                "difficulty": question.difficulty,
                "marks": question.marks
            }
            for question in questions
        ]
    }), 200


@api.put(
    "/trainer/question-bank-questions/<int:question_id>"
)
@role_required("trainer")
def update_question_bank_item(user, question_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = db.session.get(
        QuestionBankItem,
        question_id
    )

    if not question:
        return jsonify({
            "error": "Question not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=question.bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question not found"
        }), 404

    data = request.get_json(silent=True) or {}

    if "question_type" in data:
        question_type = str(
            data.get("question_type", "")
        ).strip().lower()

        if question_type not in (
            "mcq",
            "coding"
        ):
            return jsonify({
                "error": (
                    "question_type must be "
                    "mcq or coding"
                )
            }), 400

        question.question_type = question_type

    if "question_text" in data:
        question.question_text = str(
            data.get("question_text", "")
        ).strip()

    for field in (
        "option_a",
        "option_b",
        "option_c",
        "option_d",
        "correct_answer",
        "coding_description",
        "starter_code",
        "language",
        "difficulty"
    ):
        if field in data:
            setattr(
                question,
                field,
                data.get(field)
            )

    if "marks" in data:
        try:
            question.marks = int(
                data.get("marks")
            )
        except (
            TypeError,
            ValueError
        ):
            return jsonify({
                "error": "marks must be an integer"
            }), 400

    if (
        question.question_type == "mcq"
        and not question.correct_answer
    ):
        return jsonify({
            "error": (
                "correct_answer is required "
                "for MCQ"
            )
        }), 400

    if (
        question.question_type == "coding"
        and not str(
            question.coding_description or ""
        ).strip()
    ):
        return jsonify({
            "error": (
                "coding_description is required "
                "for coding questions"
            )
        }), 400

    db.session.commit()

    return jsonify({
        "message": "Question updated successfully"
    }), 200


@api.delete(
    "/trainer/question-bank-questions/<int:question_id>"
)
@role_required("trainer")
def delete_question_bank_item(user, question_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = db.session.get(
        QuestionBankItem,
        question_id
    )

    if not question:
        return jsonify({
            "error": "Question not found"
        }), 404

    bank = QuestionBank.query.filter_by(
        id=question.bank_id,
        trainer_id=trainer.id
    ).first()

    if not bank:
        return jsonify({
            "error": "Question not found"
        }), 404

    db.session.delete(question)
    db.session.commit()

    return jsonify({
        "message": "Question deleted successfully"
    }), 200

# ============================================================
# MIXED EXAMS
# ============================================================

@api.post("/trainer/mixed-exams")
@role_required("trainer")
def create_mixed_exam(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    course_id = str(
        data.get("course_id", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Exam title is required"
        }), 400

    if not course_id:
        return jsonify({
            "error": "course_id is required"
        }), 400

    course = Course.query.filter_by(
        id=course_id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    try:
        duration_minutes = int(
            data.get("duration_minutes", 60)
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "duration_minutes must be an integer"
        }), 400

    if duration_minutes <= 0:
        return jsonify({
            "error": "duration_minutes must be greater than 0"
        }), 400

    exam = MixedExam(
        title=title,
        description=description,
        course_id=course_id,
        trainer_id=trainer.id,
        duration_minutes=duration_minutes,
        total_marks=0,
        status="draft"
    )

    db.session.add(exam)
    db.session.commit()

    return jsonify({
        "message": "Mixed exam created successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration_minutes": exam.duration_minutes,
            "total_marks": exam.total_marks,
            "status": exam.status,
            "created_at": (
                exam.created_at.isoformat()
                if exam.created_at
                else None
            )
        }
    }), 201

# ============================================================
# UPDATE MIXED EXAM STATUS
# ============================================================

@api.put("/trainer/mixed-exams/<int:exam_id>/status")
@role_required("trainer")
def update_mixed_exam_status(user, exam_id):

    exam = MixedExam.query.filter_by(
        id=exam_id
    ).first()

    if not exam:
        return jsonify({
            "error": "Mixed exam not found"
        }), 404

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    if exam.trainer_id != trainer.id:
        return jsonify({
            "error": "You do not have permission to update this exam"
        }), 403

    data = request.get_json(silent=True) or {}

    status = str(
        data.get("status", "")
    ).strip().lower()

    allowed_statuses = {
        "draft",
        "published",
        "closed"
    }

    if status not in allowed_statuses:
        return jsonify({
            "error": (
                "Invalid status. "
                "Allowed values are: draft, published, closed"
            )
        }), 400

    exam.status = status

    db.session.commit()

    return jsonify({
        "message": "Mixed exam status updated successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "status": exam.status
        }
    }), 200

@api.get("/trainer/mixed-exams")
@role_required("trainer")
def get_mixed_exams(user):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exams = (
        MixedExam.query
        .filter_by(
            trainer_id=trainer.id
        )
        .order_by(
            MixedExam.id.desc()
        )
        .all()
    )

    return jsonify({
        "exams": [
            {
                "id": exam.id,
                "title": exam.title,
                "description": exam.description,
                "course_id": exam.course_id,
                "duration_minutes": exam.duration_minutes,
                "total_marks": exam.total_marks,
                "status": exam.status,
                "created_at": (
                    exam.created_at.isoformat()
                    if exam.created_at
                    else None
                )
            }
            for exam in exams
        ]
    }), 200

@api.post("/trainer/mixed-exams/<int:exam_id>/sections")
@role_required("trainer")
def create_mixed_exam_section(user, exam_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = MixedExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Mixed exam not found"
        }), 404

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    section_type = str(
        data.get("section_type", "")
    ).strip().lower()

    if not title:
        return jsonify({
            "error": "Section title is required"
        }), 400

    if section_type not in (
        "mcq",
        "coding"
    ):
        return jsonify({
            "error": "section_type must be mcq or coding"
        }), 400

    try:
        order_index = int(
            data.get("order_index", 0)
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "order_index must be an integer"
        }), 400

    section = MixedExamSection(
        exam_id=exam.id,
        title=title,
        section_type=section_type,
        order_index=order_index,
        marks=0
    )

    db.session.add(section)
    db.session.commit()

    return jsonify({
        "message": "Mixed exam section created successfully",
        "section": {
            "id": section.id,
            "exam_id": section.exam_id,
            "title": section.title,
            "section_type": section.section_type,
            "order_index": section.order_index,
            "marks": section.marks
        }
    }), 201

@api.post("/trainer/mixed-exam-sections/<int:section_id>/questions")
@role_required("trainer")
def add_mixed_exam_question(user, section_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    section = db.session.get(
        MixedExamSection,
        section_id
    )

    if not section:
        return jsonify({
            "error": "Mixed exam section not found"
        }), 404

    exam = MixedExam.query.filter_by(
        id=section.exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Mixed exam not found"
        }), 404

    data = request.get_json(silent=True) or {}

    try:
        question_bank_item_id = int(
            data.get("question_bank_item_id")
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "question_bank_item_id must be an integer"
        }), 400

    question = db.session.get(
        QuestionBankItem,
        question_bank_item_id
    )

    if not question:
        return jsonify({
            "error": "Question bank question not found"
        }), 404

    bank = db.session.get(
        QuestionBank,
        question.bank_id
    )

    if not bank or bank.trainer_id != trainer.id:
        return jsonify({
            "error": "You do not have access to this question"
        }), 403

    if question.question_type != section.section_type:
        return jsonify({
            "error": (
                "Question type does not match "
                "the section type"
            )
        }), 400

    try:
        order_index = int(
            data.get("order_index", 0)
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "order_index must be an integer"
        }), 400

    mixed_question = MixedExamQuestion(
        section_id=section.id,
        question_type=question.question_type,
        question_bank_item_id=question.id,
        question_text=question.question_text,
        option_a=question.option_a,
        option_b=question.option_b,
        option_c=question.option_c,
        option_d=question.option_d,
        correct_answer=question.correct_answer,
        coding_description=question.coding_description,
        starter_code=question.starter_code,
        language=question.language,
        marks=question.marks,
        order_index=order_index
    )

    db.session.add(mixed_question)

    db.session.flush()

    section.marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    MixedExamQuestion.marks
                ),
                0
            )
        )
        .filter(
            MixedExamQuestion.section_id == section.id
        )
        .scalar()
        or 0
    )

    db.session.flush()

    exam.total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    MixedExamQuestion.marks
                ),
                0
            )
        )
        .join(
            MixedExamSection,
            MixedExamQuestion.section_id ==
            MixedExamSection.id
        )
        .filter(
            MixedExamSection.exam_id == exam.id
        )
        .scalar()
        or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Question added to mixed exam",
        "question": {
            "id": mixed_question.id,
            "section_id": mixed_question.section_id,
            "question_bank_item_id": (
                mixed_question.question_bank_item_id
            ),
            "question_type": mixed_question.question_type,
            "question_text": mixed_question.question_text,
            "marks": mixed_question.marks,
            "order_index": mixed_question.order_index
        },
        "section": {
            "id": section.id,
            "marks": section.marks
        },
        "exam": {
            "id": exam.id,
            "total_marks": exam.total_marks
        }
    }), 201

@api.get("/trainer/mixed-exams/<int:exam_id>")
@role_required("trainer")
def get_mixed_exam(user, exam_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = MixedExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Mixed exam not found"
        }), 404

    sections = (
        MixedExamSection.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            MixedExamSection.order_index.asc(),
            MixedExamSection.id.asc()
        )
        .all()
    )

    section_data = []

    for section in sections:

        questions = (
            MixedExamQuestion.query
            .filter_by(
                section_id=section.id
            )
            .order_by(
                MixedExamQuestion.order_index.asc(),
                MixedExamQuestion.id.asc()
            )
            .all()
        )

        section_data.append({
            "id": section.id,
            "title": section.title,
            "section_type": section.section_type,
            "order_index": section.order_index,
            "marks": section.marks,
            "questions": [
                {
                    "id": question.id,
                    "question_bank_item_id": (
                        question.question_bank_item_id
                    ),
                    "question_type": question.question_type,
                    "question_text": question.question_text,
                    "option_a": question.option_a,
                    "option_b": question.option_b,
                    "option_c": question.option_c,
                    "option_d": question.option_d,
                    "coding_description": (
                        question.coding_description
                    ),
                    "starter_code": question.starter_code,
                    "language": question.language,
                    "marks": question.marks,
                    "order_index": question.order_index
                }
                for question in questions
            ]
        })

    return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration_minutes": exam.duration_minutes,
            "total_marks": exam.total_marks,
            "status": exam.status,
            "created_at": (
                exam.created_at.isoformat()
                if exam.created_at
                else None
            ),
            "sections": section_data
        }
    }), 200

# ============================================================
# MIXED EXAM INVITES
# ============================================================

@api.post("/trainer/mixed-exams/<int:exam_id>/invites")
@role_required("trainer")
def create_mixed_exam_invite(user, exam_id):

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = MixedExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Mixed exam not found"
        }), 404

    data = request.get_json(silent=True) or {}

    candidate_name = str(
        data.get("candidate_name", "")
    ).strip()

    candidate_email = str(
        data.get("candidate_email", "")
    ).strip()

    try:
        max_attempts = int(
            data.get("max_attempts", 1)
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "max_attempts must be an integer"
        }), 400

    if max_attempts <= 0:
        return jsonify({
            "error": "max_attempts must be greater than 0"
        }), 400

    expires_at = None

    if data.get("expires_at"):
        try:
            expires_at = datetime.fromisoformat(
                str(data.get("expires_at")).replace(
                    "Z",
                    "+00:00"
                )
            )

            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(
                    tzinfo=timezone.utc
                )

        except ValueError:
            return jsonify({
                "error": (
                    "expires_at must be a valid "
                    "ISO datetime"
                )
            }), 400

    invite_code = secrets.token_urlsafe(32)

    invite = MixedExamInvite(
        exam_id=exam.id,
        invite_code=invite_code,
        candidate_name=candidate_name or None,
        candidate_email=candidate_email or None,
        expires_at=expires_at,
        max_attempts=max_attempts,
        is_active=True
    )

    db.session.add(invite)
    db.session.commit()

    return jsonify({
        "message": "Mixed exam invite created successfully",
        "invite": {
            "id": invite.id,
            "exam_id": invite.exam_id,
            "invite_code": invite.invite_code,
            "candidate_name": invite.candidate_name,
            "candidate_email": invite.candidate_email,
            "expires_at": (
                invite.expires_at.isoformat()
                if invite.expires_at
                else None
            ),
            "max_attempts": invite.max_attempts,
            "is_active": invite.is_active,
            "created_at": (
                invite.created_at.isoformat()
                if invite.created_at
                else None
            )
        }
    }), 201

@api.get("/mixed-exam/invites/<string:invite_code>")
def get_public_mixed_exam_invite(invite_code):

    invite = MixedExamInvite.query.filter_by(
        invite_code=invite_code,
        is_active=True
    ).first()

    if not invite:
        return jsonify({
            "error": "Invalid or inactive invite"
        }), 404

    if invite.expires_at:
        current_time = datetime.now(timezone.utc)

        expires_at = invite.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= current_time:
            return jsonify({
                "error": "This invite has expired"
            }), 410

    exam = db.session.get(
        MixedExam,
        invite.exam_id
    )

    if not exam:
        return jsonify({
            "error": "Exam not found"
        }), 404

    sections = (
        MixedExamSection.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            MixedExamSection.order_index.asc(),
            MixedExamSection.id.asc()
        )
        .all()
    )

    section_data = []

    for section in sections:

        questions = (
            MixedExamQuestion.query
            .filter_by(
                section_id=section.id
            )
            .order_by(
                MixedExamQuestion.order_index.asc(),
                MixedExamQuestion.id.asc()
            )
            .all()
        )

        question_data = []

        for question in questions:

            item = {
                "id": question.id,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "marks": question.marks,
                "order_index": question.order_index
            }

            if question.question_type == "mcq":
                item.update({
                    "option_a": question.option_a,
                    "option_b": question.option_b,
                    "option_c": question.option_c,
                    "option_d": question.option_d
                })

            elif question.question_type == "coding":
                item.update({
                    "coding_description": (
                        question.coding_description
                    ),
                    "starter_code": question.starter_code,
                    "language": question.language
                })

            question_data.append(item)

        section_data.append({
            "id": section.id,
            "title": section.title,
            "section_type": section.section_type,
            "order_index": section.order_index,
            "marks": section.marks,
            "questions": question_data
        })

    return jsonify({
        "invite": {
            "id": invite.id,
            "candidate_name": invite.candidate_name,
            "candidate_email": invite.candidate_email,
            "max_attempts": invite.max_attempts,
            "expires_at": (
                invite.expires_at.isoformat()
                if invite.expires_at
                else None
            )
        },
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "duration_minutes": exam.duration_minutes,
            "total_marks": exam.total_marks,
            "sections": section_data
        }
    }), 200

@api.post("/mixed-exam/invites/<string:invite_code>/start")
def start_public_mixed_exam(user=None, invite_code=None):

    invite = MixedExamInvite.query.filter_by(
        invite_code=invite_code,
        is_active=True
    ).first()

    if not invite:
        return jsonify({
            "error": "Invalid or inactive invite"
        }), 404

    if invite.expires_at:
        current_time = datetime.now(timezone.utc)

        expires_at = invite.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= current_time:
            return jsonify({
                "error": "This invite has expired"
            }), 410

    exam = db.session.get(
        MixedExam,
        invite.exam_id
    )

    if not exam:
        return jsonify({
            "error": "Exam not found"
        }), 404

    data = request.get_json(silent=True) or {}

    candidate_name = str(
        data.get(
            "candidate_name",
            invite.candidate_name or ""
        )
    ).strip()

    candidate_email = str(
        data.get(
            "candidate_email",
            invite.candidate_email or ""
        )
    ).strip()

    if not candidate_name:
        return jsonify({
            "error": "candidate_name is required"
        }), 400

    if not candidate_email:
        return jsonify({
            "error": "candidate_email is required"
        }), 400

    existing_attempts = MixedExamAttempt.query.filter_by(
        invite_id=invite.id
    ).count()

    if existing_attempts >= invite.max_attempts:
        return jsonify({
            "error": "Maximum attempts reached for this invite"
        }), 403

    attempt = MixedExamAttempt(
        exam_id=exam.id,
        invite_id=invite.id,
        candidate_name=candidate_name,
        candidate_email=candidate_email,
        status="in_progress",
        score=0,
        total_marks=exam.total_marks
    )

    db.session.add(attempt)
    db.session.commit()

    return jsonify({
        "message": "Mixed exam started successfully",
        "attempt": {
            "id": attempt.id,
            "exam_id": attempt.exam_id,
            "invite_id": attempt.invite_id,
            "candidate_name": attempt.candidate_name,
            "candidate_email": attempt.candidate_email,
            "status": attempt.status,
            "started_at": (
                attempt.started_at.isoformat()
                if attempt.started_at
                else None
            ),
            "total_marks": attempt.total_marks,
            "duration_minutes": exam.duration_minutes
        }
    }), 201

# ============================================================
# MIXED EXAM ANSWERS
# ============================================================

@api.post("/mixed-exam/attempts/<int:attempt_id>/answers")
def save_mixed_exam_answer(attempt_id):

    attempt = db.session.get(
        MixedExamAttempt,
        attempt_id
    )

    if not attempt:
        return jsonify({
            "error": "Exam attempt not found"
        }), 404

    if attempt.status != "in_progress":
        return jsonify({
            "error": "This exam attempt is no longer active"
        }), 403

    data = request.get_json(silent=True) or {}

    try:
        question_id = int(
            data.get("question_id")
        )
    except (
        TypeError,
        ValueError
    ):
        return jsonify({
            "error": "question_id must be an integer"
        }), 400

    question = MixedExamQuestion.query.filter_by(
        id=question_id
    ).first()

    if not question:
        return jsonify({
            "error": "Mixed exam question not found"
        }), 404

    section = db.session.get(
        MixedExamSection,
        question.section_id
    )

    if not section:
        return jsonify({
            "error": "Exam section not found"
        }), 404

    if section.exam_id != attempt.exam_id:
        return jsonify({
            "error": "Question does not belong to this exam"
        }), 403

    answer = MixedExamAnswer.query.filter_by(
        attempt_id=attempt.id,
        question_id=question.id
    ).first()

    if not answer:
        answer = MixedExamAnswer(
            attempt_id=attempt.id,
            question_id=question.id
        )

        db.session.add(answer)

    if question.question_type == "mcq":

        selected_answer = str(
            data.get(
                "selected_answer",
                ""
            )
        ).strip().upper()

        if selected_answer not in (
            "A",
            "B",
            "C",
            "D"
        ):
            return jsonify({
                "error": (
                    "selected_answer must be "
                    "A, B, C or D"
                )
            }), 400

        answer.selected_answer = selected_answer
        answer.source_code = None
        answer.language = None

        answer.is_correct = (
            selected_answer ==
            str(
                question.correct_answer or ""
            ).strip().upper()
        )

        answer.marks_awarded = (
            question.marks
            if answer.is_correct
            else 0
        )

    elif question.question_type == "coding":

        source_code = str(
            data.get(
                "source_code",
                ""
            )
        )

        language = str(
            data.get(
                "language",
                question.language or "python"
            )
        ).strip()

        if not source_code.strip():
            return jsonify({
                "error": "source_code is required"
            }), 400

        answer.source_code = source_code
        answer.language = language
        answer.selected_answer = None

        # Coding questions are not scored here.
        # They will be evaluated through the
        # coding execution system during submission.
        answer.is_correct = None
        answer.marks_awarded = 0

    else:

        return jsonify({
            "error": "Unsupported question type"
        }), 400

    answer.submitted_at = datetime.now(
        timezone.utc
    )

    db.session.commit()

    return jsonify({
        "message": "Answer saved successfully",
        "answer": {
            "id": answer.id,
            "attempt_id": answer.attempt_id,
            "question_id": answer.question_id,
            "question_type": question.question_type,
            "marks_awarded": answer.marks_awarded
        }
    }), 200

# ============================================================
# PUBLIC MIXED EXAM - SUBMIT ATTEMPT
# ============================================================

@api.post("/mixed-exam/attempts/<int:attempt_id>/submit")
def submit_mixed_exam_attempt(attempt_id):

    attempt = MixedExamAttempt.query.get_or_404(
        attempt_id
    )

    # --------------------------------------------------------
    # Prevent submitting an already submitted attempt
    # --------------------------------------------------------

    if attempt.status == "submitted":
        return jsonify({
            "error": "This exam has already been submitted."
        }), 400

    if attempt.status != "in_progress":
        return jsonify({
            "error": "This exam attempt is no longer active."
        }), 400

    exam = MixedExam.query.get_or_404(
        attempt.exam_id
    )

    # --------------------------------------------------------
    # Check time limit
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    started_at = attempt.started_at

    if started_at is not None:

        # Make old naive datetime values timezone-aware.
        if started_at.tzinfo is None:
            started_at = started_at.replace(
                tzinfo=timezone.utc
            )

        elapsed_seconds = (
            now - started_at
        ).total_seconds()

        allowed_seconds = (
            int(exam.duration_minutes or 60)
            * 60
        )

        # We allow submission when time has expired.
        # The attempt is still submitted normally.
        time_expired = (
            elapsed_seconds >= allowed_seconds
        )

    else:
        time_expired = False

    # --------------------------------------------------------
    # Get all exam questions
    # --------------------------------------------------------

    sections = MixedExamSection.query.filter_by(
        exam_id=exam.id
    ).order_by(
        MixedExamSection.order_index.asc()
    ).all()

    question_ids = []

    for section in sections:

        section_questions = (
            MixedExamQuestion.query
            .filter_by(section_id=section.id)
            .order_by(
                MixedExamQuestion.order_index.asc()
            )
            .all()
        )

        for question in section_questions:
            question_ids.append(
                question.id
            )

    # --------------------------------------------------------
    # Get saved answers
    # --------------------------------------------------------

    saved_answers = (
        MixedExamAnswer.query
        .filter_by(
            attempt_id=attempt.id
        )
        .all()
    )

    answer_by_question = {
        answer.question_id: answer
        for answer in saved_answers
    }

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    score = 0
    total_marks = 0
    coding_pending = 0

    for question_id in question_ids:

        question = MixedExamQuestion.query.get(
            question_id
        )

        if not question:
            continue

        total_marks += int(
            question.marks or 0
        )

        answer = answer_by_question.get(
            question.id
        )

        # ----------------------------------------------------
        # MCQ
        # ----------------------------------------------------

        if question.question_type == "mcq":

            if answer:

                selected = (
                    answer.selected_answer or ""
                ).upper()

                correct = (
                    question.correct_answer or ""
                ).upper()

                if (
                    selected
                    and correct
                    and selected == correct
                ):

                    answer.is_correct = True

                    answer.marks_awarded = int(
                        question.marks or 0
                    )

                    score += int(
                        question.marks or 0
                    )

                else:

                    answer.is_correct = False
                    answer.marks_awarded = 0

            else:

                # No answer
                pass

        # ----------------------------------------------------
        # CODING
        # ----------------------------------------------------

        elif question.question_type == "coding":

            if answer:

                # Coding execution/scoring will be added
                # later using the coding runner.
                answer.is_correct = None
                answer.marks_awarded = 0

            coding_pending += 1

    # --------------------------------------------------------
    # Update attempt
    # --------------------------------------------------------

    attempt.status = "submitted"

    attempt.submitted_at = now

    attempt.score = score

    attempt.total_marks = total_marks

    db.session.commit()

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({
        "message": "Exam submitted successfully.",
        "attempt": {
            "id": attempt.id,
            "exam_id": attempt.exam_id,
            "candidate_name": attempt.candidate_name,
            "candidate_email": attempt.candidate_email,
            "status": attempt.status,
            "score": attempt.score,
            "total_marks": attempt.total_marks,
            "submitted_at": (
                attempt.submitted_at.isoformat()
                if attempt.submitted_at
                else None
            ),
        },
        "coding_pending": coding_pending,
        "time_expired": time_expired,
    })


# ============================================================
# EXAMS / QUIZZES
# ============================================================

@api.post("/trainer/courses/<string:course_id>/quizzes")
@role_required("trainer")
def trainer_create_quiz(user, course_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    data = request.get_json(silent=True) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Exam title is required"
        }), 400

    quiz = Quiz(
        course_id=course_id,
        title=title,
        description=description,
        total_marks=0
    )

    db.session.add(quiz)
    db.session.commit()

    return jsonify({
        "message": "Exam created successfully",
        "exam": quiz_json(quiz)
    }), 201


@api.get("/trainer/courses/<string:course_id>/quizzes")
@role_required("trainer")
def trainer_course_quizzes(user, course_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Quiz.query
        .filter_by(
            course_id=course_id
        )
        .order_by(
            Quiz.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    return jsonify({
        "exams": [
            quiz_json(quiz)
            for quiz in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.get("/trainer/quizzes/<int:quiz_id>")
@role_required("trainer")
def trainer_quiz_detail(
    user,
    quiz_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = db.session.get(
        Quiz,
        exam_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    return jsonify(
        quiz_json(quiz)
    )


@api.delete("/trainer/quizzes/<int:quiz_id>")
@role_required("trainer")
def trainer_delete_quiz(
    user,
    quiz_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = Quiz.query.get(
        quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    Question.query.filter_by(
        quiz_id=quiz.id
    ).delete(
        synchronize_session=False
    )

    QuizAttempt.query.filter_by(
        quiz_id=quiz.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(quiz)
    db.session.commit()

    return jsonify({
        "message": "Exam deleted successfully"
    })


# ============================================================
# TRAINER — EXAM QUESTIONS
# ============================================================

@api.post("/trainer/quizzes/<int:quiz_id>/questions")
@role_required("trainer")
def trainer_add_question(
    user,
    quiz_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = Quiz.query.get(
        quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    data = request.get_json(silent=True) or {}

    question_text = str(
        data.get("question_text", "")
    ).strip()

    option_a = str(
        data.get("option_a", "")
    ).strip()

    option_b = str(
        data.get("option_b", "")
    ).strip()

    option_c = str(
        data.get("option_c", "")
    ).strip()

    option_d = str(
        data.get("option_d", "")
    ).strip()

    correct_answer = str(
        data.get("correct_answer", "")
    ).strip().upper()

    try:
        marks = int(
            data.get("marks", 1)
        )
    except (TypeError, ValueError):
        marks = 1

    if marks <= 0:
        marks = 1

    if not question_text:
        return jsonify({
            "error": "Question text is required"
        }), 400

    if not option_a:
        return jsonify({
            "error": "Option A is required"
        }), 400

    if not option_b:
        return jsonify({
            "error": "Option B is required"
        }), 400

    if not option_c:
        return jsonify({
            "error": "Option C is required"
        }), 400

    if not option_d:
        return jsonify({
            "error": "Option D is required"
        }), 400

    if correct_answer not in {
        "A",
        "B",
        "C",
        "D"
    }:
        return jsonify({
            "error": "correct_answer must be A, B, C or D"
        }), 400

    question = Question(
        quiz_id=quiz.id,
        question_text=question_text,
        option_a=option_a,
        option_b=option_b,
        option_c=option_c,
        option_d=option_d,
        correct_answer=correct_answer,
        marks=marks
    )

    db.session.add(question)

    quiz.total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Question.marks),
                0
            )
        )
        .filter(
            Question.quiz_id == quiz.id
        )
        .scalar()
        or 0
    ) + marks

    db.session.commit()

    return jsonify({
        "message": "Question added successfully",
        "question": {
            "id": question.id,
            "quiz_id": question.quiz_id,
            "question_text": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_answer,
            "marks": question.marks,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d
            }
        }
    }), 201


@api.get("/trainer/quizzes/<int:quiz_id>/questions")
@role_required("trainer")
def trainer_quiz_questions(
    user,
    quiz_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = Quiz.query.get(
        quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Question.query
        .filter_by(
            quiz_id=quiz.id
        )
        .order_by(
            Question.id.asc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    return jsonify({
        "questions": [
            {
                "id": question.id,
                "quiz_id": question.quiz_id,
                "question_text": question.question_text,
                "question": question.question_text,
                "option_a": question.option_a,
                "option_b": question.option_b,
                "option_c": question.option_c,
                "option_d": question.option_d,
                "options": {
                    "A": question.option_a,
                    "B": question.option_b,
                    "C": question.option_c,
                    "D": question.option_d
                },
                "correct_answer": question.correct_answer,
                "marks": question.marks
            }
            for question in pagination.items
        ],
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })

# ============================================================
# TRAINER — UPDATE EXAM QUESTION
# ============================================================

@api.put("/trainer/questions/<int:question_id>")
@role_required("trainer")
def trainer_update_question(
    user,
    question_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = Question.query.get(
        question_id
    )

    if not question:
        return jsonify({
            "error": "Question not found"
        }), 404

    quiz = Quiz.query.get(
        question.quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Question not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    question_text = str(
        data.get(
            "question_text",
            question.question_text
        )
    ).strip()

    option_a = str(
        data.get(
            "option_a",
            question.option_a
        )
    ).strip()

    option_b = str(
        data.get(
            "option_b",
            question.option_b
        )
    ).strip()

    option_c = str(
        data.get(
            "option_c",
            question.option_c
        )
    ).strip()

    option_d = str(
        data.get(
            "option_d",
            question.option_d
        )
    ).strip()

    correct_answer = str(
        data.get(
            "correct_answer",
            question.correct_answer
        )
    ).strip().upper()

    try:
        marks = int(
            data.get(
                "marks",
                question.marks or 1
            )
        )
    except (TypeError, ValueError):
        marks = 1

    if not question_text:
        return jsonify({
            "error": "Question text is required"
        }), 400

    if not option_a:
        return jsonify({
            "error": "Option A is required"
        }), 400

    if not option_b:
        return jsonify({
            "error": "Option B is required"
        }), 400

    if not option_c:
        return jsonify({
            "error": "Option C is required"
        }), 400

    if not option_d:
        return jsonify({
            "error": "Option D is required"
        }), 400

    if correct_answer not in {
        "A",
        "B",
        "C",
        "D"
    }:
        return jsonify({
            "error": "correct_answer must be A, B, C or D"
        }), 400

    if marks <= 0:
        marks = 1

    question.question_text = question_text
    question.option_a = option_a
    question.option_b = option_b
    question.option_c = option_c
    question.option_d = option_d
    question.correct_answer = correct_answer
    question.marks = marks

    # Recalculate total marks
    quiz.total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Question.marks),
                0
            )
        )
        .filter(
            Question.quiz_id == quiz.id
        )
        .scalar()
        or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Question updated successfully",
        "question": {
            "id": question.id,
            "quiz_id": question.quiz_id,
            "question_text": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_answer,
            "marks": question.marks,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d
            }
        }
    })


@api.delete("/trainer/questions/<int:question_id>")
@role_required("trainer")
def trainer_delete_question(
    user,
    question_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = Question.query.get(
        question_id
    )

    if not question:
        return jsonify({
            "error": "Question not found"
        }), 404

    quiz = Quiz.query.get(
        question.quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Question not found"
        }), 404

    db.session.delete(question)

    db.session.flush()

    quiz.total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(Question.marks),
                0
            )
        )
        .filter(
            Question.quiz_id == quiz.id
        )
        .scalar()
        or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Question deleted successfully"
    })
# ============================================================
# LEARNER — EXAMS
# ============================================================

@api.get("/learner/exams")
@role_required("learner")
def learner_exams(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    course_ids = [
        enrollment.course_id
        for enrollment in enrollments
    ]

    if not course_ids:
        return jsonify({
            "exams": []
        })

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Quiz.query
        .join(
            Question,
            Question.quiz_id == Quiz.id
        )
        .filter(
            Quiz.course_id.in_(course_ids)
        )
        .distinct()
        .order_by(
            Quiz.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )
    

    quizzes = pagination.items

    exams = []

    for quiz in quizzes:
        # ----------------------------------------------------
        # Do not show empty exams to learners.
        # Trainers can still see empty exams.
        # ----------------------------------------------------
        question_count = Question.query.filter_by(
            quiz_id=quiz.id
        ).count()

        course = db.session.get(
            Course,
            quiz.course_id
        )

        item = quiz_json(quiz)

        item["course_title"] = (
            course.title
            if course
            else None
        )

        item["question_count"] = question_count

        # ----------------------------------------------------
        # Check whether learner already attempted this exam
        # ----------------------------------------------------
        attempt = QuizAttempt.query.filter_by(
            quiz_id=quiz.id,
            learner_id=learner.id
        ).order_by(
            QuizAttempt.id.desc()
        ).first()

        item["attempted"] = bool(attempt)

        if attempt:
            item["latest_attempt"] = {
                "id": attempt.id,
                "score": attempt.score,
                "total": attempt.total,
                "attempted_at": (
                    attempt.attempted_at.isoformat()
                    if attempt.attempted_at
                    else None
                )
            }
        else:
            item["latest_attempt"] = None

        exams.append(item)

    return jsonify({
        "exams": exams,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.get("/learner/exams/<int:exam_id>")
@role_required("learner")
def learner_exam_detail(
    user,
    exam_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    quiz = db.session.get(
        Quiz,
        exam_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=quiz.course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

        # --------------------------------------------------------
    # QUIZ ATTEMPT / SERVER-SIDE TIMER
    # --------------------------------------------------------

    max_attempts = int(quiz.max_attempts or 1)

    active_attempt = (
        QuizAttempt.query
        .filter_by(
            quiz_id=quiz.id,
            learner_id=learner.id,
            attempted_at=None
        )
        .order_by(QuizAttempt.id.desc())
        .first()
    )

    attempt_count = QuizAttempt.query.filter_by(
        quiz_id=quiz.id,
        learner_id=learner.id
    ).count()

    if not active_attempt:

        if attempt_count >= max_attempts:
            return jsonify({
                "error": "Maximum quiz attempts reached",
                "max_attempts": max_attempts,
                "attempts_used": attempt_count
            }), 403

        active_attempt = QuizAttempt(
            quiz_id=quiz.id,
            learner_id=learner.id,
            started_at=datetime.now(timezone.utc),
            attempted_at=None,
            score=0,
            total=0
        )

        db.session.add(active_attempt)
        db.session.commit()

        attempt_count += 1

    now = datetime.now(timezone.utc)

    started_at = active_attempt.started_at

    if started_at.tzinfo is None:
        started_at = started_at.replace(
            tzinfo=timezone.utc
        )

    expires_at = (
        started_at +
        timedelta(
            minutes=int(
                quiz.duration_minutes or 30
            )
        )
    )

    if now >= expires_at:
        return jsonify({
            "error": "Quiz time limit exceeded",
            "duration_minutes": int(
                quiz.duration_minutes or 30
            ),
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "attempt_id": active_attempt.id
        }), 403

    questions = Question.query.filter_by(
        quiz_id=quiz.id
    ).order_by(
        Question.id.asc()
    ).all()

    if not questions:
        return jsonify({
            "error": "This exam does not have any questions yet"
        }), 400

    course = db.session.get(
        Course,
        quiz.course_id
    )

    # --------------------------------------------------------
    # Build learner-safe questions.
    #
    # IMPORTANT:
    # correct_answer is intentionally NOT returned.
    # --------------------------------------------------------

    question_list = []

    for question in questions:
        question_list.append({
            "id": question.id,
            "quiz_id": question.quiz_id,
            "question_id": question.id,
            "question_text": question.question_text,
            "question": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "options": {
                "A": question.option_a,
                "B": question.option_b,
                "C": question.option_c,
                "D": question.option_d
            },
            "marks": question.marks
        })

    return jsonify({
        "exam": {
            "id": quiz.id,
            "quiz_id": quiz.id,
            "course_id": quiz.course_id,
            "course_title": (
                course.title
                if course
                else None
            ),
            "title": quiz.title,
            "description": quiz.description,
            "total_marks": sum(
                int(question.marks or 0)
                for question in questions
            ),
            "question_count": len(questions),
            "max_attempts": max_attempts,
            "attempts_used": attempt_count,
            "attempts_remaining": max(
                0,
                max_attempts - attempt_count
            ),
            "duration_minutes": int(
                quiz.duration_minutes or 30
            ),
            "attempt_id": active_attempt.id,
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat()
        },
        "questions": question_list
    })


# ============================================================
# LEARNER — SUBMIT EXAM
# ============================================================

@api.post("/learner/exams/<int:exam_id>/submit")
@role_required("learner")
def learner_submit_exam(
    user,
    exam_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    quiz = db.session.get(
        Quiz,
        exam_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=quiz.course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

        # --------------------------------------------------------
    # SERVER-SIDE QUIZ TIMER
    # --------------------------------------------------------

    max_attempts = int(quiz.max_attempts or 1)

    active_attempt = (
        QuizAttempt.query
        .filter_by(
            quiz_id=quiz.id,
            learner_id=learner.id,
            attempted_at=None
        )
        .order_by(QuizAttempt.id.desc())
        .first()
    )

    attempt_count = QuizAttempt.query.filter_by(
        quiz_id=quiz.id,
        learner_id=learner.id
    ).count()

    if not active_attempt:
        if attempt_count >= max_attempts:
            return jsonify({
                "error": "Maximum quiz attempts reached",
                "max_attempts": max_attempts,
                "attempts_used": attempt_count
            }), 403

        return jsonify({
            "error": "No active quiz attempt. Please start the quiz first."
        }), 400

    now = datetime.now(timezone.utc)

    started_at = active_attempt.started_at

    # Some databases may return a naive datetime.
    if started_at.tzinfo is None:
        started_at = started_at.replace(
            tzinfo=timezone.utc
        )

    expires_at = (
        started_at +
        timedelta(
            minutes=int(
                quiz.duration_minutes or 30
            )
        )
    )

    if now >= expires_at:
        return jsonify({
            "error": "Quiz time limit exceeded",
            "duration_minutes": int(
                quiz.duration_minutes or 30
            ),
            "started_at": started_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "attempt_id": active_attempt.id
        }), 403

    questions = Question.query.filter_by(
        quiz_id=quiz.id
    ).order_by(
        Question.id.asc()
    ).all()

    if not questions:
        return jsonify({
            "error": "This exam does not have any questions"
        }), 400

    data = request.get_json(silent=True) or {}

    answers = data.get("answers", {})

    # --------------------------------------------------------
    # Accept a few frontend formats safely.
    # --------------------------------------------------------

    if not isinstance(answers, dict):
        return jsonify({
            "error": "answers must be an object"
        }), 400

    # --------------------------------------------------------
    # Normalize all submitted answers FIRST.
    #
    # This fixes the previous bug where only the last answer
    # was processed.
    # --------------------------------------------------------

    submitted_answers = {}

    for question_id, selected_answer in answers.items():

        if selected_answer is None:
            continue

        answer = str(
            selected_answer
        ).strip().upper()

        if answer in {
            "A",
            "B",
            "C",
            "D"
        }:
            submitted_answers[
                str(question_id)
            ] = answer

    # --------------------------------------------------------
    # Calculate score
    # --------------------------------------------------------

    score = 0
    total = 0
    correct_count = 0

    question_results = []

    for question in questions:

        marks = int(
            question.marks or 0
        )

        total += marks

        selected_answer = submitted_answers.get(
            str(question.id)
        )

        correct_answer = str(
            question.correct_answer or ""
        ).strip().upper()

        is_correct = (
            selected_answer is not None
            and selected_answer == correct_answer
        )

        if is_correct:
            score += marks
            correct_count += 1

        question_results.append({
            "question_id": question.id,
            "selected_answer": selected_answer,
            "correct": is_correct,
            "marks": marks
        })

        # --------------------------------------------------------
    # Complete the active attempt
    # --------------------------------------------------------

    attempt = active_attempt

    attempt.score = score
    attempt.total = total
    attempt.attempted_at = datetime.now(timezone.utc)

    db.session.flush()

# --------------------------------------------------------
# Store every submitted answer
# --------------------------------------------------------

    for question in questions:

        selected_answer = submitted_answers.get(
            str(question.id)
        )

        correct_answer = str(
            question.correct_answer or ""
        ).strip().upper()

        is_correct = (
            selected_answer is not None
            and selected_answer == correct_answer
        )

        marks_awarded = (
            int(question.marks or 0)
            if is_correct
            else 0
        )

        answer_record = QuizAnswer(
            attempt_id=attempt.id,
            question_id=question.id,
            selected_answer=selected_answer,
            is_correct=is_correct,
            marks_awarded=marks_awarded
        )

        db.session.add(answer_record)

    db.session.commit()

    percentage = (

        round(

            (score / total) * 100,

            2

        )

        if total > 0

        else 0

    )

    return jsonify({

        "message": "Exam submitted successfully",

        "attempt": {

            "id": attempt.id,

            "exam_id": quiz.id,

            "score": score,

            "total": total,

            "percentage": percentage,

            "correct_count": correct_count,

            "question_count": len(questions),

            "question_results": question_results

        }

    }), 200


# ============================================================
# LEARNER — QUIZ ATTEMPTS
# ============================================================

@api.get("/learner/quiz-attempts")
@role_required("learner")
def learner_quiz_attempts(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        QuizAttempt.query
        .filter_by(
            learner_id=learner.id
        )
        .order_by(
            QuizAttempt.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    attempts = pagination.items

    result = []

    for attempt in attempts:
        quiz = Quiz.query.get(
            attempt.quiz_id
        )

        if not quiz:
            continue

        course = Course.query.get(
            quiz.course_id
        )

        percentage = (
            round(
                (
                    int(attempt.score or 0)
                    / int(attempt.total or 1)
                ) * 100,
                2
            )
            if attempt.total
            else 0
        )

        result.append({
    "id": attempt.id,
    "attempt_id": attempt.id,
    "learner_id": attempt.learner_id,

    "learner_name": (
        user.name
        if user
        else None
    ),

    "learner_email": (
        user.email
        if user
        else None
    ),

    "score": int(
        attempt.score or 0
    ),

    "total": int(
        attempt.total or 0
    ),

    "percentage": percentage,

    "status": "completed",

    "attempted_at": (
        attempt.attempted_at.isoformat()
        if attempt.attempted_at
        else None
    )
})

        return jsonify({
        "attempts": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })
# ============================================================
# LEARNER — VIEW OWN EXAM RESULT
# ============================================================

@api.get("/learner/exams/<int:exam_id>/result")
@role_required("learner")
def learner_exam_result(user, exam_id):

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # Find exam
    # --------------------------------------------------------

    quiz = db.session.get(
        Quiz,
        exam_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    # --------------------------------------------------------
    # SECURITY: learner must be enrolled
    # --------------------------------------------------------

    enrollment = Enrollment.query.filter_by(
        learner_id=learner.id,
        course_id=quiz.course_id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "You are not enrolled in this course"
        }), 403

    # --------------------------------------------------------
    # View Result must NEVER create a new attempt.
    # Find the learner's latest existing attempt.
    # --------------------------------------------------------

    attempt = (
        QuizAttempt.query
        .filter_by(
            quiz_id=quiz.id,
            learner_id=learner.id
        )
        .order_by(
            QuizAttempt.id.desc()
        )
        .first()
    )

    if not attempt:
        return jsonify({
            "error": "No attempt found"
        }), 404

    # --------------------------------------------------------
    # Get saved answers
    # --------------------------------------------------------

    answers = QuizAnswer.query.filter_by(
        attempt_id=attempt.id
    ).all()

    answer_map = {
        answer.question_id: answer
        for answer in answers
    }

    # --------------------------------------------------------
    # Get all questions
    # --------------------------------------------------------

    questions = (
        Question.query
        .filter_by(
            quiz_id=quiz.id
        )
        .order_by(
            Question.id.asc()
        )
        .all()
    )

    question_results = []

    for question in questions:

        answer = answer_map.get(
            question.id
        )

        question_results.append({

            "question_id": question.id,

            "question_text": question.question_text,

            "option_a": question.option_a,

            "option_b": question.option_b,

            "option_c": question.option_c,

            "option_d": question.option_d,

            "correct_answer": (
                str(
                    question.correct_answer or ""
                ).strip().upper()
            ),

            "selected_answer": (
                answer.selected_answer
                if answer
                else None
            ),

            "is_correct": (
                bool(answer.is_correct)
                if answer
                else False
            ),

            "marks": int(
                question.marks or 0
            ),

            "marks_awarded": (
                int(
                    answer.marks_awarded or 0
                )
                if answer
                else 0
            )
        })

    # --------------------------------------------------------
    # Calculate result statistics
    # --------------------------------------------------------

    percentage = (
        round(
            (
                int(attempt.score or 0)
                /
                int(attempt.total or 1)
            ) * 100,
            2
        )
        if attempt.total
        else 0
    )

    correct_count = sum(
        1
        for item in question_results
        if item["is_correct"]
    )

    answered_count = sum(
        1
        for item in question_results
        if item["selected_answer"] is not None
    )

    wrong_count = sum(
        1
        for item in question_results
        if (
            item["selected_answer"] is not None
            and not item["is_correct"]
        )
    )

    unanswered_count = sum(
        1
        for item in question_results
        if item["selected_answer"] is None
    )

    # --------------------------------------------------------
    # Return saved result
    # --------------------------------------------------------

    return jsonify({

        "exam": {
            "id": quiz.id,
            "title": quiz.title,
            "description": quiz.description,
            "course_id": quiz.course_id,
            "total_marks": int(
                attempt.total or 0
            ),
            "question_count": len(
                question_results
            )
        },

        "attempt": {
            "id": attempt.id,
            "score": int(
                attempt.score or 0
            ),
            "total": int(
                attempt.total or 0
            ),
            "percentage": percentage,

            "correct_count": correct_count,

            "wrong_count": wrong_count,

            "answered_count": answered_count,

            "unanswered_count": unanswered_count,

            "attempted_at": (
                attempt.attempted_at.isoformat()
                if attempt.attempted_at
                else None
            )
        },

        "questions": question_results

    }), 200


# ============================================================
# TRAINER — VIEW COMPLETE LEARNER EXAM RESULT
# ============================================================

@api.get(
    "/trainer/quizzes/<int:quiz_id>/attempts/<int:attempt_id>"
)
@role_required("trainer")
def trainer_quiz_attempt_detail(
    user,
    quiz_id,
    attempt_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = Quiz.query.get(
        quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    attempt = QuizAttempt.query.filter_by(
        id=attempt_id,
        quiz_id=quiz_id
    ).first()

    if not attempt:
        return jsonify({
            "error": "Attempt not found"
        }), 404

    learner = Learner.query.get(
        attempt.learner_id
    )

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    learner_user = User.query.get(
        learner.user_id
    )

    answers = QuizAnswer.query.filter_by(
        attempt_id=attempt.id
    ).all()

    answer_map = {
        answer.question_id: answer
        for answer in answers
    }

    questions = Question.query.filter_by(
        quiz_id=quiz.id
    ).order_by(
        Question.id.asc()
    ).all()

    question_results = []

    for question in questions:

        answer = answer_map.get(
            question.id
        )

        question_results.append({
            "question_id": question.id,
            "question_text": question.question_text,
            "option_a": question.option_a,
            "option_b": question.option_b,
            "option_c": question.option_c,
            "option_d": question.option_d,
            "correct_answer": question.correct_answer,
            "selected_answer": (
                answer.selected_answer
                if answer
                else None
            ),
            "is_correct": (
                answer.is_correct
                if answer
                else False
            ),
            "marks": int(
                question.marks or 0
            ),
            "marks_awarded": (
                int(answer.marks_awarded or 0)
                if answer
                else 0
            )
        })

    percentage = (
        round(
            (
                int(attempt.score or 0)
                /
                int(attempt.total or 1)
            ) * 100,
            2
        )
        if attempt.total
        else 0
    )

    return jsonify({
        "exam": {
            "id": quiz.id,
            "title": quiz.title,
            "course_id": quiz.course_id
        },
        "learner": {
            "id": learner.id,
            "name": (
                learner_user.name
                if learner_user
                else None
            ),
            "email": (
                learner_user.email
                if learner_user
                else None
            )
        },
        "attempt": {
            "id": attempt.id,
            "score": int(
                attempt.score or 0
            ),
            "total": int(
                attempt.total or 0
            ),
            "percentage": percentage,
            "attempted_at": (
                attempt.attempted_at.isoformat()
                if attempt.attempted_at
                else None
            )
        },
        "questions": question_results
    })

# ============================================================
# TRAINER — EXAM ATTEMPTS
# ============================================================

@api.get("/trainer/quizzes/<int:quiz_id>/attempts")
@role_required("trainer")
def trainer_quiz_attempts(
    user,
    quiz_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    quiz = Quiz.query.get(
        quiz_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    course = Course.query.filter_by(
        id=quiz.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Exam not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        QuizAttempt.query
        .filter_by(
            quiz_id=quiz.id
        )
        .order_by(
            QuizAttempt.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    attempts = pagination.items

    result = []

    for attempt in attempts:
        learner = Learner.query.get(
            attempt.learner_id
        )

        learner_user = (
            User.query.get(
                learner.user_id
            )
            if learner
            else None
        )

        percentage = (
            round(
                (
                    int(attempt.score or 0)
                    / int(attempt.total or 1)
                ) * 100,
                2
            )
            if attempt.total
            else 0
        )

        result.append({
            "id": attempt.id,
            "attempt_id": attempt.id,
            "learner_id": attempt.learner_id,
            "learner_name": (
                user.name
                if user
                else None
            ),
            
            "learner_email": (
                user.email
                if user
                else None
            ),
            "score": attempt.score,
            "total": attempt.total,
            "percentage": percentage,
            "attempted_at": (
                attempt.attempted_at.isoformat()
                if attempt.attempted_at
                else None
            )
        })

        return jsonify({
        "exam": quiz_json(quiz),
        "attempts": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


# ============================================================
# END OF PART 5
# ============================================================
# ============================================================
# FILE UPLOAD HELPERS
# ============================================================

def save_uploaded_file(file, folder):
    """
    Save an uploaded file inside the configured upload folder.
    Returns the relative saved path.
    """

    if not file or not file.filename:
        return None

    filename = secure_filename(file.filename)

    if not filename:
        return None

    os.makedirs(folder, exist_ok=True)

    unique_name = (
        f"{uuid.uuid4().hex}_"
        f"{filename}"
    )

    path = os.path.join(
        folder,
        unique_name
    )

    file.save(path)

    return path

# ============================================================
# TRAINER — UPDATE LESSON DURATION
# ============================================================

@api.put("/trainer/lessons/<string:lesson_id>/duration")
@role_required("trainer")
def trainer_update_lesson_duration(
    user,
    lesson_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    module = Module.query.get(
        lesson.module_id
    )

    if not module:
        return jsonify({
            "error": "Module not found"
        }), 404

    course = Course.query.filter_by(
        id=module.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "You do not own this lesson"
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    duration = data.get(
        "duration"
    )

    if not duration:
        return jsonify({
            "error": "Duration is required"
        }), 400

    lesson.duration = str(
        duration
    )

    db.session.commit()

    return jsonify({
        "message": "Lesson duration updated successfully",
        "lesson_id": lesson.id,
        "duration": lesson.duration
    })

# ============================================================
# TRAINER — LESSON VIDEO UPLOAD
# ============================================================

@api.post("/trainer/lessons/<string:lesson_id>/video")
@role_required("trainer")
def trainer_upload_lesson_video(
    user,
    lesson_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    module = Module.query.get(
    lesson.module_id
    )

    if not module:
        return jsonify({
        "error": "Module not found"
    }), 404

    course = Course.query.filter_by(
    id=module.course_id,
    trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    video = request.files.get(
        "video"
    )

    if not video:
        return jsonify({
            "error": "Video file is required"
        }), 400

    upload_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "videos"
    )

    saved_path = save_uploaded_file(
        video,
        upload_folder
    )

    if not saved_path:
        return jsonify({
            "error": "Invalid video file"
        }), 400

    lesson.video_url = (
        "/" + saved_path.replace(
            os.sep,
            "/"
        )
    )

    video_resource = LessonResource(
        lesson_id=lesson.id,
        resource_type="video",
        file_name=video.filename,
        file_path=saved_path,
        title=video.filename,
    )

    db.session.add(video_resource)

    db.session.commit()

    return jsonify({
        "message": "Video uploaded successfully",
        "video_url": lesson.video_url
    })


# ============================================================
# TRAINER — LESSON PDF UPLOAD
# ============================================================

@api.post("/trainer/lessons/<string:lesson_id>/pdf")
@role_required("trainer")
def trainer_upload_lesson_pdf(
    user,
    lesson_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    module = Module.query.get(
    lesson.module_id
)

    if not module:
        return jsonify({
        "error": "Module not found"
    }), 404

    course = Course.query.filter_by(
    id=module.course_id,
    trainer_id=trainer.id
    ).first()   

    if not course:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    pdf = request.files.get(
        "pdf"
    )

    if not pdf:
        return jsonify({
            "error": "PDF file is required"
        }), 400

    upload_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "pdfs"
    )

    saved_path = save_uploaded_file(
        pdf,
        upload_folder
    )

    if not saved_path:
        return jsonify({
            "error": "Invalid PDF file"
        }), 400

    lesson.pdf_url = (
        "/" + saved_path.replace(
            os.sep,
            "/"
        )
    )

    pdf_resource = LessonResource(
        lesson_id=lesson.id,
        resource_type="pdf",
        file_name=pdf.filename,
        file_path=saved_path,
        title=pdf.filename,
    )

    db.session.add(pdf_resource)

    db.session.commit()

    return jsonify({
        "message": "PDF uploaded successfully",
        "pdf_url": lesson.pdf_url
    })


# ============================================================
# TRAINER — COURSE RESOURCE UPLOAD
# ============================================================

@api.post("/trainer/courses/<string:course_id>/resources")
@role_required("trainer")
def trainer_upload_course_resource(
    user,
    course_id
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    resource = request.files.get(
        "file"
    )

    if not resource:
        resource = request.files.get(
            "resource"
        )

    if not resource:
        return jsonify({
            "error": "Resource file is required"
        }), 400

    upload_folder = os.path.join(
        current_app.config["UPLOAD_FOLDER"],
        "resources"
    )

    saved_path = save_uploaded_file(
        resource,
        upload_folder
    )

    if not saved_path:
        return jsonify({
            "error": "Invalid resource file"
        }), 400

    return jsonify({
        "message": "Resource uploaded successfully",
        "resource": {
            "name": resource.filename,
            "url": "/" + saved_path.replace(
                os.sep,
                "/"
            )
        }
    }), 201

# ============================================================
# TRAINER — DELETE LESSON RESOURCE
# ============================================================

@api.delete(
    "/trainer/lessons/<string:lesson_id>/resources/<string:resource_type>/<path:file_name>"
)
@role_required("trainer")
def trainer_delete_lesson_resource(
    user,
    lesson_id,
    resource_type,
    file_name,
):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    module = Module.query.get(
        lesson.module_id
    )

    if not module:
        return jsonify({
            "error": "Module not found"
        }), 404

    course = Course.query.filter_by(
        id=module.course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "You do not own this lesson"
        }), 403

    resource = (
        LessonResource.query
        .filter_by(
            lesson_id=lesson.id,
            resource_type=resource_type,
            file_name=file_name,
        )
        .first()
    )

    if not resource:
        return jsonify({
            "error": "Resource not found"
        }), 404

    file_path = resource.file_path

    # Delete the physical file
    if file_path and os.path.isfile(file_path):
        os.remove(file_path)

    # Clear the legacy lesson URL if this resource
    # is the currently stored PDF/video.
    if resource_type == "pdf":
        expected_url = (
            "/" + file_path.replace(
                os.sep,
                "/"
            )
        )

        if lesson.pdf_url == expected_url:
            lesson.pdf_url = None

    elif resource_type == "video":
        expected_url = (
            "/" + file_path.replace(
                os.sep,
                "/"
            )
        )

        if lesson.video_url == expected_url:
            lesson.video_url = None

    db.session.delete(resource)

    db.session.commit()

    return jsonify({
        "message": "Resource deleted successfully",
        "resource": {
            "id": resource.id,
            "type": resource_type,
            "fileName": file_name,
        }
    })

# ============================================================
# SERVE UPLOADED FILES
# ============================================================

@api.get("/files/<path:filename>")
@token_required
def serve_uploaded_file(user, filename):
    upload_folder = os.path.abspath(
        current_app.config["UPLOAD_FOLDER"]
    )

    requested_path = os.path.abspath(
        os.path.join(
            upload_folder,
            filename
        )
    )

    # Prevent path traversal outside the upload directory.
    if not requested_path.startswith(
        upload_folder + os.sep
    ):
        return jsonify({
            "error": "Invalid file path"
        }), 400

    if not os.path.isfile(requested_path):
        return jsonify({
            "error": "File not found"
        }), 404

    # -----------------------------------------------------
    # ADMIN / TRAINER ACCESS
    # -----------------------------------------------------

    if user.role in ("admin", "trainer"):
        return send_from_directory(
            upload_folder,
            filename
        )

    # -----------------------------------------------------
    # LEARNER ACCESS
    # -----------------------------------------------------

    if user.role != "learner":
        return jsonify({
            "error": "You do not have permission to access this file"
        }), 403

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    normalized_requested = os.path.normcase(
        os.path.normpath(requested_path)
    )

    # Find the lesson resource matching this physical file.
    resource = LessonResource.query.filter(
        LessonResource.file_path.isnot(None)
    ).all()

    matching_resource = None

    for item in resource:
        stored_path = os.path.abspath(
            os.path.normpath(item.file_path)
        )

        if os.path.normcase(stored_path) == normalized_requested:
            matching_resource = item
            break

    if matching_resource:
        lesson = db.session.get(
            Lesson,
            matching_resource.lesson_id
        )

        if not lesson:
            return jsonify({
                "error": "Lesson not found"
            }), 404

        module = db.session.get(
            Module,
            lesson.module_id
        )

        if not module:
            return jsonify({
                "error": "Module not found"
            }), 404

        enrollment = Enrollment.query.filter_by(
            learner_id=learner.id,
            course_id=module.course_id,
            status="active"
        ).first()

        if not enrollment:
            return jsonify({
                "error": "You are not enrolled in this course"
            }), 403

        return send_from_directory(
            upload_folder,
            filename
        )

    # -----------------------------------------------------
    # LEGACY LESSON VIDEO/PDF ACCESS
    # -----------------------------------------------------

    lesson = None

    lessons = Lesson.query.all()

    for item in lessons:
        if item.video_url == "/" + filename:
            lesson = item
            break

        if item.pdf_url == "/" + filename:
            lesson = item
            break

    if lesson:
        module = db.session.get(
            Module,
            lesson.module_id
        )

        if not module:
            return jsonify({
                "error": "Module not found"
            }), 404

        enrollment = Enrollment.query.filter_by(
            learner_id=learner.id,
            course_id=module.course_id,
            status="active"
        ).first()

        if not enrollment:
            return jsonify({
                "error": "You are not enrolled in this course"
            }), 403

        return send_from_directory(
            upload_folder,
            filename
        )

    return jsonify({
        "error": "File access is not authorized"
    }), 403


# ============================================================
# ADMIN — ENROLLMENTS
# ============================================================

@api.get("/admin/enrollments")
@role_required("admin")
def admin_enrollments(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1,
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1,
            ),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Enrollment.query
        .order_by(
            Enrollment.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    result = []

    for enrollment in pagination.items:

        # -------------------------------------------------
        # Learner
        # -------------------------------------------------

        learner = Learner.query.get(
            enrollment.learner_id
        )

        learner_user = (
            User.query.get(
                learner.user_id
            )
            if learner
            else None
        )

        # -------------------------------------------------
        # Course
        # -------------------------------------------------

        course = Course.query.get(
            enrollment.course_id
        )

        # -------------------------------------------------
        # Payment summary
        # -------------------------------------------------

        paid_amount = (
            db.session.query(
                db.func.coalesce(
                    db.func.sum(Payment.amount),
                    0
                )
            )
            .filter(
                Payment.enrollment_id == enrollment.id,
                Payment.status == "paid"
            )
            .scalar()
            or 0
        )

        course_fee = float(
            enrollment.course_fee
            if enrollment.course_fee is not None
            else (
                course.course_fee
                if course
                else 0
            )
        )

        paid_amount = float(
            paid_amount
        )

        pending_amount = max(
            course_fee - paid_amount,
            0
        )

        result.append({
            "id": enrollment.id,

            "learner_id":
                enrollment.learner_id,

            "learner_name": (
                learner_user.name
                if learner_user
                else None
            ),

            "learner_email": (
                learner_user.email
                if learner_user
                else None
            ),

            "course_id":
                enrollment.course_id,

            "course_title": (
                course.title
                if course
                else None
            ),

            "course_fee":
                course_fee,

            "paid_amount":
                paid_amount,

            "pending_amount":
                pending_amount,

            "progress": int(
                enrollment.progress or 0
            ),

            "status":
                enrollment.status,

            "enrolled_at": (
                enrollment.enrolled_at.isoformat()
                if enrollment.enrolled_at
                else None
            ),
        })

    return jsonify({
        "enrollments": result,

        "pagination": {
            "page":
                pagination.page,

            "limit":
                pagination.per_page,

            "total":
                pagination.total,

            "pages":
                pagination.pages,

            "has_next":
                pagination.has_next,

            "has_previous":
                pagination.has_prev,
        },
    })

@api.post("/admin/enrollments")
@role_required("admin")
def admin_create_enrollment(user):
    data = request.get_json(silent=True) or {}

    learner_id = data.get("learner_id")
    course_id = data.get("course_id")

    if not learner_id or not course_id:
        return jsonify({
            "error": "learner_id and course_id are required"
        }), 400

    learner = Learner.query.get(learner_id)

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    course = Course.query.get(course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    existing = Enrollment.query.filter_by(
        learner_id=learner_id,
        course_id=course_id
    ).first()

    if existing:
        return jsonify({
            "error": "Learner is already enrolled in this course"
        }), 409

    course_fee = float(
        course.course_fee or 0
    )

    # Free courses can be activated immediately.
    if course_fee <= 0:
        enrollment_status = "active"
    else:
        # Paid courses require payment.
        enrollment_status = "payment_pending"

    enrollment = Enrollment(
        learner_id=learner.id,
        course_id=course.id,
        course_fee=course_fee,
        progress=0,
        status=enrollment_status
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({
        "message": (
            "Learner enrolled successfully"
            if enrollment_status == "active"
            else "Enrollment created. Payment is required."
        ),
        "enrollment": {
            "id": enrollment.id,
            "learner_id": enrollment.learner_id,
            "course_id": enrollment.course_id,
            "course_fee": course_fee,
            "progress": enrollment.progress,
            "status": enrollment.status,
            "paid_amount": 0,
            "pending_amount": course_fee
        }
    }), 201


@api.delete("/admin/enrollments/<int:enrollment_id>")
@role_required("admin")
def admin_delete_enrollment(
    user,
    enrollment_id
):
    enrollment = Enrollment.query.get(
        enrollment_id
    )

    if not enrollment:
        return jsonify({
            "error": "Enrollment not found"
        }), 404

    db.session.delete(enrollment)
    db.session.commit()

    return jsonify({
        "message": "Enrollment deleted successfully"
    })

# =========================================================
# ADMIN — PAYMENTS
# =========================================================

@api.post("/admin/payments")
@role_required("admin")
def admin_create_payment(user):
    data = request.get_json(silent=True) or {}

    learner_id = data.get("learner_id")
    enrollment_id = data.get("enrollment_id")
    amount = data.get("amount")
    payment_method = data.get("payment_method")
    status = data.get("status", "paid")

    # -----------------------------------------------------
    # Validate required fields
    # -----------------------------------------------------

    if not learner_id:
        return jsonify({
            "error": "learner_id is required"
        }), 400

    if not enrollment_id:
        return jsonify({
            "error": "enrollment_id is required"
        }), 400

    if amount is None:
        return jsonify({
            "error": "amount is required"
        }), 400

    # -----------------------------------------------------
    # Validate amount
    # -----------------------------------------------------

    try:
        amount = float(amount)
    except (TypeError, ValueError):
        return jsonify({
            "error": "amount must be a valid number"
        }), 400

    if amount <= 0:
        return jsonify({
            "error": "Payment amount must be greater than 0"
        }), 400

    # -----------------------------------------------------
    # Validate payment status
    # -----------------------------------------------------

    allowed_statuses = {
        "paid",
        "pending",
        "failed"
    }

    status = str(status).lower()

    if status not in allowed_statuses:
        return jsonify({
            "error": (
                "Invalid payment status. "
                "Use paid, pending, or failed."
            )
        }), 400

    # -----------------------------------------------------
    # Find learner
    # -----------------------------------------------------

    learner = Learner.query.get(learner_id)

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    # -----------------------------------------------------
    # Find enrollment
    # -----------------------------------------------------

    enrollment = Enrollment.query.get(enrollment_id)

    if not enrollment:
        return jsonify({
            "error": "Enrollment not found"
        }), 404

    # -----------------------------------------------------
    # Security: enrollment must belong to learner
    # -----------------------------------------------------

    if enrollment.learner_id != learner.id:
        return jsonify({
            "error": (
                "Enrollment does not belong to "
                "this learner"
            )
        }), 400

    # -----------------------------------------------------
    # Get course
    # -----------------------------------------------------

    course = Course.query.get(enrollment.course_id)

    if not course:
        return jsonify({
            "error": "Course associated with enrollment not found"
        }), 404

    # -----------------------------------------------------
    # Make sure enrollment has the course fee
    # -----------------------------------------------------

    if enrollment.course_fee is None:
        enrollment.course_fee = course.course_fee or 0

    course_fee = float(enrollment.course_fee or 0)

    # -----------------------------------------------------
    # Calculate already paid amount
    # -----------------------------------------------------

    paid_payments = Payment.query.filter_by(
        enrollment_id=enrollment.id,
        status="paid"
    ).all()

    already_paid = sum(
        float(payment.amount or 0)
        for payment in paid_payments
    )

    # -----------------------------------------------------
    # Calculate pending amount before this payment
    # -----------------------------------------------------

    pending_before = max(
        course_fee - already_paid,
        0
    )

    # -----------------------------------------------------
    # Only successful payments reduce the balance
    # -----------------------------------------------------

    if status == "paid":

        if pending_before <= 0:
            return jsonify({
                "error": "This enrollment is already fully paid"
            }), 400

        if amount > pending_before:
            return jsonify({
                "error": "Payment amount exceeds pending balance",
                "course_fee": course_fee,
                "already_paid": already_paid,
                "pending_amount": pending_before,
                "maximum_payment": pending_before
            }), 400

    # -----------------------------------------------------
    # Create payment
    # -----------------------------------------------------

    payment = Payment(
        learner_id=learner.id,
        enrollment_id=enrollment.id,
        amount=amount,
        payment_method=payment_method,
        status=status
    )

    db.session.add(payment)

    # -----------------------------------------------------
    # Create invoice for the payment
    # -----------------------------------------------------

    invoice_number = (
        f"INV-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
        f"-{learner.id}-{enrollment.id}"
    )

    # Prevent an extremely unlikely duplicate invoice number
    existing_invoice = Invoice.query.filter_by(
        invoice_number=invoice_number
    ).first()

    if existing_invoice:
        invoice_number = (
            f"INV-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
            f"-{learner.id}-{enrollment.id}-{uuid.uuid4().hex[:6].upper()}"
        )

    invoice_status = (
        "paid"
        if status == "paid"
        else "unpaid"
    )

    invoice = Invoice(
        learner_id=learner.id,
        invoice_number=invoice_number,
        amount=amount,
        status=invoice_status
    )

    db.session.add(invoice)

    # -----------------------------------------------------
    # Calculate new balance
    # -----------------------------------------------------

    if status == "paid":
        new_paid = already_paid + amount
    else:
        new_paid = already_paid

    pending_after = max(
        course_fee - new_paid,
        0
    )

    # -----------------------------------------------------
    # Activate enrollment after full payment
    # -----------------------------------------------------

    if (
        status == "paid"
        and course_fee > 0
        and pending_after <= 0
    ):
        enrollment.status = "active"

    db.session.commit()

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({
        "message": "Payment recorded successfully",

        "payment": {
            "id": payment.id,
            "learner_id": payment.learner_id,
            "enrollment_id": payment.enrollment_id,
            "amount": payment.amount,
            "payment_method": payment.payment_method,
            "status": payment.status,
            "payment_date": (
                payment.payment_date.isoformat()
                if payment.payment_date
                else None
            )
        },

        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": invoice.amount,
            "status": invoice.status,
            "invoice_date": (
                invoice.invoice_date.isoformat()
                if invoice.invoice_date
                else None
            )
        },

        "summary": {
            "course_fee": course_fee,
            "already_paid": already_paid,
            "current_payment": (
                amount
                if status == "paid"
                else 0
            ),
            "total_paid": new_paid,
            "pending_amount": pending_after,
            "enrollment_status": enrollment.status
        }
    }), 201

@api.get("/admin/payments")
@role_required("admin")
def admin_get_payments(user):
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    query = (
        Payment.query
        .order_by(Payment.payment_date.desc())
    )

    pagination = query.paginate(
        page=page,
        per_page=limit,
        error_out=False
    )
    total_money_collected = float(
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter(Payment.status == "paid")
        .scalar()
        or 0
    )

    payments = []

    for payment in pagination.items:
        learner = Learner.query.get(payment.learner_id)

        enrollment = None
        course = None

        if payment.enrollment_id:
            enrollment = Enrollment.query.get(payment.enrollment_id)

            if enrollment:
                course = Course.query.get(enrollment.course_id)

        payments.append({
            "id": payment.id,
            "learner_id": payment.learner_id,
            "learner_name": (
                learner.user.name
                if learner and learner.user
                else None
            ),
            "learner_email": (
                learner.user.email
                if learner and learner.user
                else None
            ),
            "enrollment_id": payment.enrollment_id,
            "course_id": (
                course.id
                if course
                else None
            ),
            "course_title": (
                course.title
                if course
                else None
            ),
            "amount": float(payment.amount or 0),
            "payment_method": payment.payment_method,
            "status": payment.status,
            "payment_date": (
                payment.payment_date.isoformat()
                if payment.payment_date
                else None
            )
        })

    return jsonify({
        "payments": payments,
        "total_money_collected": total_money_collected,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200


@api.get("/admin/invoices")
@role_required("admin")
def admin_get_invoices(user):
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    query = (
        Invoice.query
        .order_by(Invoice.invoice_date.desc())
    )

    pagination = query.paginate(
        page=page,
        per_page=limit,
        error_out=False
    )

    invoices = []

    for invoice in pagination.items:
        learner = Learner.query.get(invoice.learner_id)

        invoices.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "learner_id": invoice.learner_id,
            "learner_name": (
                learner.user.name
                if learner and learner.user
                else None
            ),
            "learner_email": (
                learner.user.email
                if learner and learner.user
                else None
            ),
            "amount": float(invoice.amount or 0),
            "invoice_date": (
                invoice.invoice_date.isoformat()
                if invoice.invoice_date
                else None
            ),
            "status": invoice.status
        })

    return jsonify({
        "invoices": invoices,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200

# =========================================================
# LEARNER - PAYMENT HISTORY
# =========================================================

@api.get("/learner/payments")
@role_required("learner")
def learner_get_payments(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    query = (
        Payment.query
        .filter_by(learner_id=learner.id)
        .order_by(Payment.payment_date.desc())
    )

    pagination = query.paginate(
        page=page,
        per_page=limit,
        error_out=False
    )

    payments = []

    for payment in pagination.items:
        enrollment = Enrollment.query.get(
            payment.enrollment_id
        )

        course = (
            Course.query.get(enrollment.course_id)
            if enrollment
            else None
        )

        payments.append({
            "id": payment.id,
            "enrollment_id": payment.enrollment_id,
            "course_id": course.id if course else None,
            "course_title": course.title if course else None,
            "amount": float(payment.amount or 0),
            "payment_method": payment.payment_method,
            "status": payment.status,
            "payment_date": (
                payment.payment_date.isoformat()
                if payment.payment_date
                else None
            ),
        })

    total_paid = float(
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter_by(
            learner_id=learner.id,
            status="paid"
        )
        .scalar()
        or 0
    )

    payment_count = Payment.query.filter_by(
        learner_id=learner.id,
        status="paid"
    ).count()

    return jsonify({
        "payments": payments,
        "summary": {
            "total_paid": total_paid,
            "payment_count": payment_count
        },
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200

# =========================================================
# LEARNER - CREATE PAYMENT (DISABLED)
# =========================================================

@api.post("/learner/payments")
@role_required("learner")
def learner_create_payment(user):
    return jsonify({
        "error": (
            "Direct payment recording is disabled. "
            "Please use Razorpay Checkout to complete payment."
        ),
        "code": "RAZORPAY_CHECKOUT_REQUIRED"
    }), 410

# =========================================================
# LEARNER - RAZORPAY PAYMENT
# =========================================================

def get_razorpay_client():
    """Create a Razorpay client using backend-only credentials."""

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise RuntimeError(
            "Razorpay credentials are not configured."
        )

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


@api.post("/learner/payments/razorpay/order")
@role_required("learner")
def learner_create_razorpay_order(user):
    data = request.get_json(silent=True) or {}
    enrollment_id = data.get("enrollment_id")

    if not enrollment_id:
        return jsonify({
            "error": "enrollment_id is required"
        }), 400

    try:
        enrollment_id = int(enrollment_id)
    except (TypeError, ValueError):
        return jsonify({
            "error": "Invalid enrollment_id"
        }), 400

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollment = Enrollment.query.filter_by(
        id=enrollment_id,
        learner_id=learner.id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "Enrollment not found"
        }), 404

    course = Course.query.get(enrollment.course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    course_fee = float(
        enrollment.course_fee
        if enrollment.course_fee is not None
        else course.course_fee or 0
    )

    if course_fee <= 0:
        return jsonify({
            "error": "This course does not require payment"
        }), 400

    already_paid = float(
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter(
            Payment.enrollment_id == enrollment.id,
            Payment.status == "paid"
        )
        .scalar()
        or 0
    )

    pending_amount = round(
        max(course_fee - already_paid, 0),
        2
    )

    if pending_amount <= 0:
        enrollment.status = "active"
        db.session.commit()

        return jsonify({
            "error": "This course is already fully paid"
        }), 400

        # Reuse an existing pending Razorpay order for this enrollment.
    existing_payment = Payment.query.filter(
        Payment.enrollment_id == enrollment.id,
        Payment.learner_id == learner.id,
        Payment.payment_method == "razorpay",
        Payment.status == "pending",
        Payment.razorpay_order_id.isnot(None),
    ).order_by(Payment.id.desc()).first()

    if existing_payment:
        try:
            client = get_razorpay_client()
            existing_order = client.order.fetch(
                existing_payment.razorpay_order_id
            )

            if (
                existing_order.get("status") == "created"
                and int(existing_order.get("amount", -1))
                == int(round(float(existing_payment.amount) * 100))
                and existing_order.get("currency") == "INR"
            ):
                return jsonify({
                    "message": "Existing Razorpay order reused",
                    "key_id": os.getenv("RAZORPAY_KEY_ID"),
                    "order_id": existing_order["id"],
                    "amount": existing_order["amount"],
                    "currency": existing_order["currency"],
                    "payment_id": existing_payment.id,
                    "course_name": course.title,
                }), 200

        except Exception:
            current_app.logger.exception(
                "Unable to check existing Razorpay order"
            )

            return jsonify({
                "error": (
                    "Unable to check the existing payment order. "
                    "Please try again."
                )
            }), 502

    # Create the Razorpay order for the server-calculated balance.
    try:
        client = get_razorpay_client()

        order = client.order.create({
            "amount": int(round(pending_amount * 100)),
            "currency": "INR",
            "receipt": f"enr_{enrollment.id}_{uuid.uuid4().hex[:12]}",
            "notes": {
                "learner_id": str(learner.id),
                "enrollment_id": str(enrollment.id),
                "course_id": str(course.id),
            },
        })

    except Exception:
        current_app.logger.exception(
            "Unable to create Razorpay order"
        )

        return jsonify({
            "error": "Unable to create payment order. Please try again."
        }), 502

    # Save the order as pending before opening Checkout.
    payment = Payment(
        learner_id=learner.id,
        enrollment_id=enrollment.id,
        amount=pending_amount,
        payment_method="razorpay",
        status="pending",
        razorpay_order_id=order["id"],
    )

    try:
        db.session.add(payment)
        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Unable to save Razorpay order"
        )

        return jsonify({
            "error": "Unable to save payment order"
        }), 500

    return jsonify({
        "message": "Razorpay order created",
        "key_id": os.getenv("RAZORPAY_KEY_ID"),
        "order_id": order["id"],
        "amount": order["amount"],
        "currency": order["currency"],
        "payment_id": payment.id,
        "course_name": course.title,
    }), 201


@api.post("/learner/payments/razorpay/verify")
@role_required("learner")
def learner_verify_razorpay_payment(user):
    data = request.get_json(silent=True) or {}

    order_id = data.get("razorpay_order_id")
    payment_id = data.get("razorpay_payment_id")
    signature = data.get("razorpay_signature")

    if not all([order_id, payment_id, signature]):
        return jsonify({
            "error": (
                "razorpay_order_id, razorpay_payment_id, "
                "and razorpay_signature are required"
            )
        }), 400

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    payment = Payment.query.filter_by(
        learner_id=learner.id,
        razorpay_order_id=order_id
    ).first()

    if not payment:
        return jsonify({
            "error": "Payment order not found"
        }), 404

    # Idempotency: repeated verification of the same payment
    # must not create another payment or invoice.
    if payment.status == "paid":
        if payment.razorpay_payment_id == payment_id:
            enrollment = Enrollment.query.get(
                payment.enrollment_id
            )

            return jsonify({
                "message": "Payment already verified",
                "status": "paid",
                "enrollment_status": (
                    enrollment.status if enrollment else None
                ),
            }), 200

        return jsonify({
            "error": "This order has already been paid"
        }), 409

    try:
        client = get_razorpay_client()

        # Verify Razorpay's HMAC-SHA256 checkout signature.
        key_secret = os.getenv("RAZORPAY_KEY_SECRET")

        expected_signature = hmac.new(
            key_secret.encode("utf-8"),
            f"{order_id}|{payment_id}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(
            expected_signature,
            str(signature),
        ):
            return jsonify({
                "error": "Invalid payment signature"
            }), 400
        # Verify the order details directly with Razorpay.
        gateway_order = client.order.fetch(order_id)

        expected_amount = int(
            round(float(payment.amount) * 100)
        )

        if int(gateway_order.get("amount", -1)) != expected_amount:
            return jsonify({
                "error": "Razorpay order amount does not match"
            }), 400

        if gateway_order.get("currency") != "INR":
            return jsonify({
                "error": "Razorpay order currency does not match"
            }), 400
        
        # Fetch payment details from Razorpay itself.
        gateway_payment = client.payment.fetch(payment_id)

        if gateway_payment.get("order_id") != order_id:
            return jsonify({
                "error": "Payment does not match this order"
            }), 400

        if gateway_payment.get("status") != "captured":
            return jsonify({
                "error": (
                    "Payment has not been captured yet. "
                    "Please wait and try again."
                )
            }), 409

        expected_amount = int(round(float(payment.amount) * 100))

        if int(gateway_payment.get("amount", -1)) != expected_amount:
            return jsonify({
                "error": "Payment amount does not match the order"
            }), 400

        if gateway_payment.get("currency") != "INR":
            return jsonify({
                "error": "Unexpected payment currency"
            }), 400

        if gateway_payment.get("id") != payment_id:
            return jsonify({
                "error": "Payment identifier mismatch"
            }), 400

    except Exception:
        current_app.logger.exception(
            "Razorpay payment verification failed"
        )

        return jsonify({
            "error": (
                "Unable to verify payment with Razorpay. "
                "Please retry verification."
            )
        }), 502

    enrollment = Enrollment.query.filter_by(
        id=payment.enrollment_id,
        learner_id=learner.id
    ).first()

    if not enrollment:
        return jsonify({
            "error": "Enrollment not found"
        }), 404

    course = Course.query.get(enrollment.course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # Prevent the same Razorpay transaction being reused.
    duplicate_payment = Payment.query.filter(
        Payment.razorpay_payment_id == payment_id,
        Payment.id != payment.id
    ).first()

    if duplicate_payment:
        return jsonify({
            "error": "This Razorpay payment has already been processed"
        }), 409

    # Record the verified payment.
    payment.razorpay_payment_id = payment_id
    payment.payment_method = "razorpay"
    payment.status = "paid"
    payment.payment_date = datetime.now(timezone.utc)

    # Create an invoice only after successful verification.
    invoice_number = (
        f"INV-{datetime.now(timezone.utc):%Y%m%d%H%M%S}"
        f"-{learner.id}-{enrollment.id}-{uuid.uuid4().hex[:6].upper()}"
    )

    invoice = Invoice(
        learner_id=learner.id,
        invoice_number=invoice_number,
        amount=float(payment.amount),
        status="paid",
    )

    db.session.add(invoice)

    # Calculate the total paid amount, including this payment.
    new_paid = float(
        db.session.query(
            db.func.coalesce(
                db.func.sum(Payment.amount),
                0
            )
        )
        .filter(
            Payment.enrollment_id == enrollment.id,
            Payment.status == "paid",
        )
        .scalar()
        or 0
    )

    course_fee = float(
        enrollment.course_fee
        if enrollment.course_fee is not None
        else course.course_fee or 0
    )

    pending_after = max(
        round(course_fee - new_paid, 2),
        0
    )

    if pending_after <= 0:
        enrollment.status = "active"
    else:
        enrollment.status = "payment_pending"

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()

        current_app.logger.exception(
            "Unable to save verified Razorpay payment"
        )

        return jsonify({
            "error": (
                "Payment was verified, but saving the result failed. "
                "Please retry verification or contact support."
            )
        }), 500

    return jsonify({
        "message": "Payment verified successfully",
        "payment": {
            "id": payment.id,
            "razorpay_order_id": payment.razorpay_order_id,
            "razorpay_payment_id": payment.razorpay_payment_id,
            "amount": float(payment.amount),
            "status": payment.status,
        },
        "invoice": {
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": float(invoice.amount),
            "status": invoice.status,
        },
        "summary": {
            "course_fee": course_fee,
            "total_paid": new_paid,
            "pending_amount": pending_after,
            "enrollment_status": enrollment.status,
            "access_granted": enrollment.status == "active",
        },
    }), 200

@api.get("/learner/invoices")
@role_required("learner")
def learner_get_invoices(user):
    learner = Learner.query.filter_by(user_id=user.id).first()

    if not learner:
        return jsonify({"message": "Learner profile not found"}), 404

    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 20, type=int)

    page = max(page, 1)
    limit = min(max(limit, 1), 100)

    query = (
        Invoice.query
        .filter_by(learner_id=learner.id)
        .order_by(Invoice.invoice_date.desc())
    )

    pagination = query.paginate(
        page=page,
        per_page=limit,
        error_out=False
    )

    invoices = []

    for invoice in pagination.items:
        invoices.append({
            "id": invoice.id,
            "invoice_number": invoice.invoice_number,
            "amount": float(invoice.amount or 0),
            "invoice_date": (
                invoice.invoice_date.isoformat()
                if invoice.invoice_date
                else None
            ),
            "status": invoice.status
        })

    return jsonify({
        "invoices": invoices,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "pages": pagination.pages,
            "total": pagination.total,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200

@api.get("/learner/invoices/<int:invoice_id>/pdf")
@role_required("learner")
def learner_download_invoice_pdf(user, invoice_id):
    learner = Learner.query.filter_by(user_id=user.id).first()

    if not learner:
        return jsonify({
            "message": "Learner profile not found"
        }), 404

    invoice = Invoice.query.filter_by(
        id=invoice_id,
        learner_id=learner.id
    ).first()

    if not invoice:
        return jsonify({
            "message": "Invoice not found"
        }), 404

    try:
        from io import BytesIO
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_CENTER
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle
        )
        from reportlab.lib import colors

        buffer = BytesIO()

        font_path = "/System/Library/Fonts/NotoSansKannada.ttc"

        pdfmetrics.registerFont(
            TTFont(
                "RupeeFont",
                font_path,
                subfontIndex=0
            )
        )

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        title_style.alignment = TA_CENTER

        story = []

        story.append(
            Paragraph("DEVSPRINT LMS", title_style)
        )

        story.append(
            Paragraph("INVOICE", styles["Heading2"])
        )

        story.append(Spacer(1, 20))

        learner_name = (
            learner.user.name
            if learner.user
            else "Learner"
        )

        learner_email = (
            learner.user.email
            if learner.user
            else ""
        )

        invoice_date = (
            invoice.invoice_date.strftime("%d %B %Y")
            if invoice.invoice_date
            else ""
        )

        invoice_details = [
            ["Invoice Number", invoice.invoice_number],
            ["Invoice Date", invoice_date],
            ["Learner", learner_name],
            ["Email", learner_email],
            [
                "Amount",
                Paragraph(
                    f'<font name="RupeeFont">₹</font>'
                    f'{float(invoice.amount or 0):,.2f}',
                    styles["Normal"]
                )
            ],
            ["Status", str(invoice.status).upper()],
        ]

        table = Table(
            invoice_details,
            colWidths=[150, 330]
        )

        table.setStyle(
            TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),                
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 8),
            ])
        )

        story.append(table)

        story.append(Spacer(1, 30))

        story.append(
            Paragraph(
                "Thank you for using DevSprint LMS.",
                styles["Normal"]
            )
        )

        doc.build(story)

        buffer.seek(0)

        from flask import send_file

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"{invoice.invoice_number}.pdf"
        )

    except ImportError:
        return jsonify({
            "message": "PDF generation is not available. "
                       "Please install reportlab."
        }), 500

    except Exception:
        return jsonify({
            "message": "Failed to generate invoice PDF"
        }), 500

# ============================================================
# ADMIN — INVOICE PDF
# ============================================================

@api.get("/admin/invoices/<int:invoice_id>/pdf")
@role_required("admin")
def admin_download_invoice_pdf(user, invoice_id):

    invoice = Invoice.query.get(invoice_id)

    if not invoice:
        return jsonify({
            "message": "Invoice not found"
        }), 404

    learner = Learner.query.get(invoice.learner_id)

    if not learner:
        return jsonify({
            "message": "Learner not found"
        }), 404

    try:
        from io import BytesIO

        from reportlab.lib.pagesizes import A4

        from reportlab.lib.styles import (
            getSampleStyleSheet
        )

        from reportlab.lib.enums import TA_CENTER

        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle
        )

        from reportlab.lib import colors

        buffer = BytesIO()

        # ----------------------------------------------------
        # RUPEE FONT
        # ----------------------------------------------------

        font_path = (
            "/System/Library/Fonts/"
            "NotoSansKannada.ttc"
        )

        pdfmetrics.registerFont(
            TTFont(
                "RupeeFont",
                font_path,
                subfontIndex=0
            )
        )

        # ----------------------------------------------------
        # PDF DOCUMENT
        # ----------------------------------------------------

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]

        title_style.alignment = TA_CENTER

        story = []

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        story.append(
            Paragraph(
                "DEVSPRINT LMS",
                title_style
            )
        )

        story.append(
            Paragraph(
                "INVOICE",
                styles["Heading2"]
            )
        )

        story.append(
            Spacer(1, 20)
        )

        # ----------------------------------------------------
        # LEARNER DETAILS
        # ----------------------------------------------------

        learner_name = (
            learner.user.name
            if learner.user
            else "Learner"
        )

        learner_email = (
            learner.user.email
            if learner.user
            else ""
        )

        # ----------------------------------------------------
        # INVOICE DATE
        # ----------------------------------------------------

        invoice_date = (
            invoice.invoice_date.strftime(
                "%d %B %Y"
            )
            if invoice.invoice_date
            else ""
        )

        # ----------------------------------------------------
        # INVOICE DETAILS
        # ----------------------------------------------------

        invoice_details = [

            [
                "Invoice Number",
                invoice.invoice_number
            ],

            [
                "Invoice Date",
                invoice_date
            ],

            [
                "Learner",
                learner_name
            ],

            [
                "Email",
                learner_email
            ],

            [
                "Amount",
                Paragraph(
                    f'<font name="RupeeFont">₹</font>'
                    f'{float(invoice.amount or 0):,.2f}',
                    styles["Normal"]
                )
            ],

            [
                "Status",
                str(
                    invoice.status
                ).upper()
            ],

        ]

        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        table = Table(
            invoice_details,
            colWidths=[
                150,
                330
            ]
        )

        table.setStyle(
            TableStyle([

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, -1),
                    "Helvetica"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

            ])
        )

        story.append(table)

        story.append(
            Spacer(1, 30)
        )

        # ----------------------------------------------------
        # FOOTER MESSAGE
        # ----------------------------------------------------

        story.append(
            Paragraph(
                "Thank you for using DevSprint LMS.",
                styles["Normal"]
            )
        )

        # ----------------------------------------------------
        # BUILD PDF
        # ----------------------------------------------------

        doc.build(story)

        buffer.seek(0)

        from flask import send_file

        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=(
                f"{invoice.invoice_number}.pdf"
            )
        )

    except ImportError:

        return jsonify({
            "message":
                "PDF generation is not available. "
                "Please install reportlab."
        }), 500

    except Exception:

        return jsonify({
            "message":
                "Failed to generate invoice PDF"
        }), 500

# ============================================================
# ADMIN — ATTENDANCE
# ============================================================

@api.get("/admin/attendance")
@role_required("admin")
def admin_attendance(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1,
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1,
            ),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    batch_id = request.args.get("batch_id")
    date_value = request.args.get("date")
    learner_id = request.args.get("learner_id")

    query = Attendance.query

    if batch_id:
        try:
            batch_id = int(batch_id)
        except (TypeError, ValueError):
            return jsonify({
                "error": "batch_id must be an integer"
            }), 400

        query = query.filter(
            Attendance.batch_id == batch_id
        )

    if learner_id:
        try:
            learner_id = int(learner_id)
        except (TypeError, ValueError):
            return jsonify({
                "error": "learner_id must be an integer"
            }), 400

        query = query.filter(
            Attendance.learner_id == learner_id
        )

    if date_value:
        try:
            attendance_date = datetime.strptime(
                date_value,
                "%Y-%m-%d",
            ).date()
        except (TypeError, ValueError):
            return jsonify({
                "error": "Date must use YYYY-MM-DD format"
            }), 400

        query = query.filter(
            Attendance.date == attendance_date
        )

    pagination = (
        query
        .order_by(
            Attendance.date.desc(),
            Attendance.id.desc(),
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    result = []

    for record in pagination.items:
        learner = db.session.get(
            Learner,
            record.learner_id,
        )

        batch = db.session.get(
            Batch,
            record.batch_id,
        )

        learner_user = (
            db.session.get(
                User,
                learner.user_id,
            )
            if learner
            else None
        )

        trainer = (
            db.session.get(
                Trainer,
                batch.trainer_id,
            )
            if batch and batch.trainer_id
            else None
        )

        trainer_user = (
            db.session.get(
                User,
                trainer.user_id,
            )
            if trainer
            else None
        )

        result.append({
            "id": record.id,
            "learner_id": record.learner_id,
            "learner_name": (
                learner_user.name
                if learner_user
                else None
            ),
            "learner_email": (
                learner_user.email
                if learner_user
                else None
            ),
            "batch_id": record.batch_id,
            "batch_name": (
                batch.name
                if batch
                else None
            ),
            "trainer_id": (
                trainer.id
                if trainer
                else None
            ),
            "trainer_name": (
                trainer_user.name
                if trainer_user
                else None
            ),
            "date": (
                record.date.isoformat()
                if record.date
                else None
            ),
            "status": record.status,
            "marked_by": record.marked_by,
        })

    return jsonify({
        "attendance": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    }), 200


@api.get("/admin/attendance/summary")
@role_required("admin")
def admin_attendance_summary(user):
    batch_id = request.args.get("batch_id")

    query = Learner.query

    if batch_id:
        try:
            batch_id = int(batch_id)
        except (TypeError, ValueError):
            return jsonify({
                "error": "batch_id must be an integer"
            }), 400

        query = query.filter(
            Learner.batch_id == batch_id
        )

    learners = (
        query
        .filter(
            Learner.batch_id.isnot(None)
        )
        .order_by(Learner.id.asc())
        .all()
    )

    result = []

    for learner in learners:
        records = Attendance.query.filter_by(
            learner_id=learner.id,
            batch_id=learner.batch_id,
        ).all()

        total = len(records)

        present = sum(
            1
            for record in records
            if record.status == "present"
        )

        late = sum(
            1
            for record in records
            if record.status == "late"
        )

        absent = sum(
            1
            for record in records
            if record.status == "absent"
        )

        attended = present + late

        percentage = (
            round(
                (attended / total) * 100,
                2,
            )
            if total
            else 0
        )

        result.append({
            "learner_id": learner.id,
            "learner_name": (
                learner.user.name
                if learner.user
                else None
            ),
            "batch_id": learner.batch_id,
            "total": total,
            "present": present,
            "late": late,
            "absent": absent,
            "attendance_percentage": percentage,
        })

    return jsonify({
        "learners": result,
        "total": len(result),
    }), 200


@api.put("/admin/attendance/<int:attendance_id>")
@role_required("admin")
def admin_update_attendance(
    user,
    attendance_id,
):
    record = db.session.get(
        Attendance,
        attendance_id,
    )

    if not record:
        return jsonify({
            "error": "Attendance record not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    status = str(
        data.get("status", "")
    ).strip().lower()

    if status not in {
        "present",
        "absent",
        "late",
    }:
        return jsonify({
            "error": (
                "Status must be present, absent, or late"
            )
        }), 400

    record.status = status
    record.marked_by = user.id

    db.session.commit()

    return jsonify({
        "message": "Attendance updated successfully",
        "attendance": {
            "id": record.id,
            "learner_id": record.learner_id,
            "batch_id": record.batch_id,
            "date": (
                record.date.isoformat()
                if record.date
                else None
            ),
            "status": record.status,
            "marked_by": record.marked_by,
        },
    }), 200




# ============================================================
# ADMIN — CERTIFICATES
# ============================================================

@api.get("/admin/certificates")
@role_required("admin")
def admin_certificates(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1,
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1,
            ),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Certificate.query
        .order_by(
            Certificate.created_at.desc(),
            Certificate.id.desc(),
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    result = []

    for certificate in pagination.items:
        learner = certificate.learner
        course = certificate.course

        learner_user = None

        if learner:
            learner_user = User.query.get(
                learner.user_id
            )

        learner_name = None
        learner_email = None

        if learner_user:
            learner_name = (
                getattr(
                    learner_user,
                    "name",
                    None,
                )
                or getattr(
                    learner_user,
                    "full_name",
                    None,
                )
                or getattr(
                    learner_user,
                    "username",
                    None,
                )
            )

            learner_email = getattr(
                learner_user,
                "email",
                None,
            )

        result.append({
            "id": certificate.id,
            "certificate_id": certificate.certificate_id,
            "learner_id": certificate.learner_id,
            "learner_name": learner_name,
            "learner_email": learner_email,
            "course_id": certificate.course_id,
            "course_name": (
                course.title
                if course
                else None
            ),
            "start_date": (
                certificate.start_date.isoformat()
                if certificate.start_date
                else None
            ),
            "end_date": (
                certificate.end_date.isoformat()
                if certificate.end_date
                else None
            ),
            "created_at": (
                certificate.created_at.isoformat()
                if certificate.created_at
                else None
            ),
            "status": certificate.status,
        })

    return jsonify({
        "certificates": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    }), 200

# ============================================================
# ADMIN — BATCHES
# ============================================================
@api.post("/admin/batches")
@role_required("admin")
def admin_create_batch(user):
    data = request.get_json(silent=True) or {}

    name = str(data.get("name", "")).strip()
    course_id = str(data.get("course_id", "")).strip()
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    trainer_id = data.get("trainer_id")
    status = str(
        data.get("status", "active")
    ).strip().lower()

    if not name:
        return jsonify({
            "error": "Batch name is required"
        }), 400

    if not course_id:
        return jsonify({
            "error": "Course is required"
        }), 400

    if not trainer_id:
        return jsonify({
            "error": "Trainer is required"
        }), 400

    course = db.session.get(
        Course,
        course_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    trainer = db.session.get(
        Trainer,
        trainer_id
    )

    if not trainer:
        return jsonify({
            "error": "Trainer not found"
        }), 404

    if not start_date:
        return jsonify({
            "error": "Start date is required"
        }), 400

    if not end_date:
        return jsonify({
            "error": "End date is required"
        }), 400

    try:
        parsed_start_date = datetime.strptime(
            str(start_date),
            "%Y-%m-%d"
        ).date()

        parsed_end_date = datetime.strptime(
            str(end_date),
            "%Y-%m-%d"
        ).date()

    except (
        TypeError,
        ValueError,
    ):
        return jsonify({
            "error": "Dates must use YYYY-MM-DD format"
        }), 400

    if parsed_end_date < parsed_start_date:
        return jsonify({
            "error": "End date cannot be before start date"
        }), 400

    if status not in {
        "active",
        "inactive",
    }:
        return jsonify({
            "error": "Status must be active or inactive"
        }), 400

    batch = Batch(
        name=name,
        course_id=course.id,
        trainer_id=trainer.id,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        status=status,
    )

    db.session.add(batch)
    db.session.commit()

    return jsonify({
        "message": "Batch created successfully",
        "batch": {
            "id": batch.id,
            "name": batch.name,
            "course_id": batch.course_id,
            "course_title": course.title,
            "trainer_id": batch.trainer_id,
            "trainer_name": (
                trainer.user.name
                if trainer.user
                else None
            ),
            "start_date": (
                batch.start_date.isoformat()
                if batch.start_date
                else None
            ),
            "end_date": (
                batch.end_date.isoformat()
                if batch.end_date
                else None
            ),
            "status": batch.status,
        },
    }), 201


@api.get("/admin/batches")
@role_required("admin")
def admin_batches(user):
    try:
        page = max(
            int(request.args.get("page", 1)),
            1,
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1,
            ),
            100,
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        Batch.query
        .order_by(Batch.id.desc())
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    result = []

    for batch in pagination.items:
        course = (
            db.session.get(
                Course,
                batch.course_id
            )
            if batch.course_id
            else None
        )

        trainer = (
            db.session.get(
                Trainer,
                batch.trainer_id
            )
            if batch.trainer_id
            else None
        )

        learner_count = Learner.query.filter_by(
            batch_id=batch.id
        ).count()

        trainer_name = None

        if trainer and trainer.user:
            trainer_name = trainer.user.name

        result.append({
            "id": batch.id,
            "name": batch.name,
            "course_id": batch.course_id,
            "course_title": (
                course.title
                if course
                else None
            ),
            "trainer_id": batch.trainer_id,
            "trainer_name": trainer_name,
            "start_date": (
                batch.start_date.isoformat()
                if batch.start_date
                else None
            ),
            "end_date": (
                batch.end_date.isoformat()
                if batch.end_date
                else None
            ),
            "status": batch.status,
            "learner_count": learner_count,
        })

    return jsonify({
        "batches": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    }), 200



@api.get("/admin/batches/<int:batch_id>/learners")
@role_required("admin")
def admin_batch_learners(user, batch_id):
    batch = db.session.get(Batch, batch_id)

    if not batch:
        return jsonify({
            "error": "Batch not found"
        }), 404

    learners = (
        Learner.query
        .filter_by(batch_id=batch.id)
        .order_by(Learner.id.asc())
        .all()
    )

    return jsonify({
        "batch": {
            "id": batch.id,
            "name": batch.name,
            "course_id": batch.course_id,
        },
        "learners": [
            {
                "id": learner.id,
                "name": (
                    learner.user.name
                    if learner.user
                    else None
                ),
                "email": (
                    learner.user.email
                    if learner.user
                    else None
                ),
                "mobile": (
                    learner.user.mobile
                    if learner.user
                    else None
                ),
                "education": learner.education,
                "batch_id": learner.batch_id,
                "status": learner.status,
            }
            for learner in learners
        ],
        "total": len(learners),
    }), 200


@api.post("/admin/batches/<int:batch_id>/learners")
@role_required("admin")
def admin_add_batch_learner(user, batch_id):
    batch = db.session.get(Batch, batch_id)

    if not batch:
        return jsonify({
            "error": "Batch not found"
        }), 404

    if not batch.course_id:
        return jsonify({
            "error": "This batch is not linked to a course"
        }), 400

    data = request.get_json(silent=True) or {}

    learner_id = data.get("learner_id")

    if learner_id is None:
        return jsonify({
            "error": "learner_id is required"
        }), 400

    try:
        learner_id = int(learner_id)
    except (TypeError, ValueError):
        return jsonify({
            "error": "learner_id must be an integer"
        }), 400

    learner = db.session.get(Learner, learner_id)

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    if learner.status != "active":
        return jsonify({
            "error": "Only active learners can be assigned to a batch"
        }), 400

    if learner.batch_id == batch.id:
        return jsonify({
            "error": "Learner is already assigned to this batch"
        }), 409

    if learner.batch_id is not None:
        return jsonify({
            "error": "Learner is already assigned to another batch"
        }), 409

    enrollment = (
        Enrollment.query
        .filter_by(
            learner_id=learner.id,
            course_id=batch.course_id,
            status="active",
        )
        .first()
    )

    if not enrollment:
        return jsonify({
            "error": "Learner must be actively enrolled in the batch course"
        }), 400

    learner.batch_id = batch.id

    db.session.commit()

    return jsonify({
        "message": "Learner added to batch successfully",
        "learner": learner_json(learner),
    }), 200


@api.delete("/admin/batches/<int:batch_id>")
@role_required("admin")
def admin_delete_batch(
    user,
    batch_id
):
    batch = Batch.query.get(
        batch_id
    )

    if not batch:
        return jsonify({
            "error": "Batch not found"
        }), 404

    # --------------------------------------------------------
    # Do not delete a batch if learners are still attached.
    # --------------------------------------------------------

    learners = Learner.query.filter_by(
        batch_id=batch.id
    ).all()

    if learners:
        return jsonify({
            "error": "Cannot delete a batch while learners are assigned to it"
        }), 409

    db.session.delete(batch)
    db.session.commit()

    return jsonify({
        "message": "Batch deleted successfully"
    })


# =========================================================
# DISCUSSION / COMMUNITY
# =========================================================

@api.get("/courses/<course_id>/discussions")
@token_required
def course_discussions(user, course_id):

    # -----------------------------------------------------
    # Check course
    # -----------------------------------------------------

    course = Course.query.get(course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # -----------------------------------------------------
    # Get all modules belonging to this course
    # -----------------------------------------------------

    modules = (
        Module.query
        .filter_by(course_id=course.id)
        .order_by(Module.order_no.asc())
        .all()
    )

    lesson_ids = []

    lesson_details = {}

    for module in modules:

        lessons = (
            Lesson.query
            .filter_by(module_id=module.id)
            .order_by(Lesson.order_no.asc())
            .all()
        )

        for lesson in lessons:

            lesson_ids.append(lesson.id)

            lesson_details[lesson.id] = {
                "id": lesson.id,
                "title": lesson.title,
                "module_id": module.id,
                "module_title": module.title,
            }

    # -----------------------------------------------------
    # No lessons
    # -----------------------------------------------------

    if not lesson_ids:
        return jsonify({
            "course": {
                "id": course.id,
                "title": course.title
            },
            "discussions": [],
            "lessons": []
        })

    # -----------------------------------------------------
    # Get discussions for all lessons in this course
    # -----------------------------------------------------

    rows = (
        Discussion.query
        .filter(
            Discussion.lesson_id.in_(lesson_ids)
        )
        .order_by(
            Discussion.created_at.desc()
        )
        .all()
    )

    result = []

    for discussion in rows:

        discussion_user = User.query.get(
            discussion.user_id
        )

        lesson_info = lesson_details.get(
            discussion.lesson_id,
            {}
        )

        result.append({
            "id": discussion.id,
            "lesson_id": discussion.lesson_id,
            "lesson_title": lesson_info.get(
                "title"
            ),
            "module_title": lesson_info.get(
                "module_title"
            ),
            "message": discussion.message,
            "user": (
                discussion_user.name
                if discussion_user
                else "Learner"
            ),
            "user_id": discussion.user_id,
            "createdAt": (
                discussion.created_at.isoformat()
                if discussion.created_at
                else None
            )
        })

    # -----------------------------------------------------
    # Return course discussions
    # -----------------------------------------------------

    return jsonify({
        "course": {
            "id": course.id,
            "title": course.title
        },
        "lessons": list(
            lesson_details.values()
        ),
        "discussions": result
    })


# =========================================================
# CREATE COURSE DISCUSSION
# =========================================================

@api.post("/courses/<course_id>/discussions")
@token_required
def create_course_discussion(user, course_id):

    # -----------------------------------------------------
    # Check course
    # -----------------------------------------------------

    course = Course.query.get(course_id)

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    # -----------------------------------------------------
    # Read request data
    # -----------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    lesson_id = str(
        data.get("lesson_id", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    # -----------------------------------------------------
    # Validate lesson
    # -----------------------------------------------------

    if not lesson_id:

        return jsonify({
            "error": "Lesson is required"
        }), 400

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:

        return jsonify({
            "error": "Lesson not found"
        }), 404

    # -----------------------------------------------------
    # Make sure lesson belongs to this course
    # -----------------------------------------------------

    module = Module.query.get(
        lesson.module_id
    )

    if not module:

        return jsonify({
            "error": "Lesson module not found"
        }), 404

    if module.course_id != course.id:

        return jsonify({
            "error": "Lesson does not belong to this course"
        }), 400

    # -----------------------------------------------------
    # Validate message
    # -----------------------------------------------------

    if not message:

        return jsonify({
            "error": "Message is required"
        }), 400

    if len(message) > 5000:

        return jsonify({
            "error": "Message cannot exceed 5000 characters"
        }), 400

    # -----------------------------------------------------
    # Learner enrollment security
    # -----------------------------------------------------

    if user.role == "learner":

        learner = Learner.query.filter_by(
            user_id=user.id
        ).first()

        if not learner:

            return jsonify({
                "error": "Learner profile not found"
            }), 404

        enrollment = Enrollment.query.filter_by(
            learner_id=learner.id,
            course_id=course.id
        ).first()

        if not enrollment:

            return jsonify({
                "error": "You are not enrolled in this course"
            }), 403

        if enrollment.status != "active":

            return jsonify({
                "error": "Your enrollment is not active"
            }), 403

    # -----------------------------------------------------
    # Create discussion
    # -----------------------------------------------------

    row = Discussion(
        user_id=user.id,
        lesson_id=lesson.id,
        message=message
    )

    db.session.add(row)

    db.session.commit()

    # -----------------------------------------------------
    # Response
    # -----------------------------------------------------

    return jsonify({
        "message": "Discussion posted successfully",
        "discussion": {
            "id": row.id,
            "lesson_id": row.lesson_id,
            "lesson_title": lesson.title,
            "module_title": module.title,
            "message": row.message,
            "user": user.name,
            "user_id": user.id,
            "createdAt": (
                row.created_at.isoformat()
                if row.created_at
                else None
            )
        }
    }), 201


# =========================================================
# LESSON DISCUSSIONS
# =========================================================

@api.get("/lessons/<lesson_id>/discussions")
@token_required
def discussions(user, lesson_id):

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:

        return jsonify({
            "error": "Lesson not found"
        }), 404

    rows = (
        Discussion.query
        .filter_by(
            lesson_id=lesson.id
        )
        .order_by(
            Discussion.created_at.asc()
        )
        .all()
    )

    result = []

    for discussion in rows:

        discussion_user = User.query.get(
            discussion.user_id
        )

        result.append({
            "id": discussion.id,
            "lesson_id": discussion.lesson_id,
            "message": discussion.message,
            "user": (
                discussion_user.name
                if discussion_user
                else "Learner"
            ),
            "user_id": discussion.user_id,
            "createdAt": (
                discussion.created_at.isoformat()
                if discussion.created_at
                else None
            )
        })

    return jsonify({
        "lesson": {
            "id": lesson.id,
            "title": lesson.title
        },
        "discussions": result
    })


# =========================================================
# CREATE LESSON DISCUSSION
# =========================================================

@api.post("/lessons/<lesson_id>/discussions")
@token_required
def create_discussion(user, lesson_id):

    lesson = Lesson.query.get(
        lesson_id
    )

    if not lesson:

        return jsonify({
            "error": "Lesson not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    message = str(
        data.get("message", "")
    ).strip()

    if not message:

        return jsonify({
            "error": "Message is required"
        }), 400

    if len(message) > 5000:

        return jsonify({
            "error": "Message cannot exceed 5000 characters"
        }), 400

    row = Discussion(
        user_id=user.id,
        lesson_id=lesson.id,
        message=message
    )

    db.session.add(row)

    db.session.commit()

    return jsonify({
        "message": "Discussion posted",
        "discussion": {
            "id": row.id,
            "lesson_id": row.lesson_id,
            "message": row.message,
            "user": user.name,
            "user_id": user.id,
            "createdAt": (
                row.created_at.isoformat()
                if row.created_at
                else None
            )
        }
    }), 201



# ============================================================
# NOTIFICATIONS
# ============================================================

@api.get("/notifications")
@token_required
def get_notifications(user):
    notifications = (
        Notification.query
        .filter_by(user_id=user.id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return jsonify({
        "notifications": [
            {
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "is_read": notification.is_read,
                "link": notification.link,
                "created_at": (
                    notification.created_at.isoformat()
                    if notification.created_at
                    else None
                ),
                "read_at": (
                    notification.read_at.isoformat()
                    if notification.read_at
                    else None
                )
            }
            for notification in notifications
        ]
    }), 200


@api.get("/notifications/unread-count")
@token_required
def get_unread_notification_count(user):
    count = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).count()

    return jsonify({
        "unread_count": count
    }), 200


@api.put("/notifications/<int:notification_id>/read")
@token_required
def mark_notification_as_read(user, notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user.id
    ).first()

    if not notification:
        return jsonify({
            "error": "Notification not found"
        }), 404

    notification.is_read = True
    notification.read_at = datetime.now(timezone.utc)

    db.session.commit()

    return jsonify({
        "message": "Notification marked as read",
        "notification": {
            "id": notification.id,
            "is_read": notification.is_read,
            "read_at": (
                notification.read_at.isoformat()
                if notification.read_at
                else None
            )
        }
    }), 200


@api.put("/notifications/read-all")
@token_required
def mark_all_notifications_as_read(user):
    notifications = Notification.query.filter_by(
        user_id=user.id,
        is_read=False
    ).all()

    read_time = datetime.now(timezone.utc)

    for notification in notifications:
        notification.is_read = True
        notification.read_at = read_time

    db.session.commit()

    return jsonify({
        "message": "All notifications marked as read",
        "updated_count": len(notifications)
    }), 200

@api.delete("/notifications/<int:notification_id>")
@token_required
def delete_notification(user, notification_id):
    notification = Notification.query.filter_by(
        id=notification_id,
        user_id=user.id
    ).first()

    if not notification:
        return jsonify({
            "error": "Notification not found"
        }), 404

    db.session.delete(notification)
    db.session.commit()

    return jsonify({
        "message": "Notification deleted successfully",
        "notification_id": notification_id
    }), 200

@api.delete("/notifications")
@token_required
def delete_all_notifications(user):
    notifications = Notification.query.filter_by(
        user_id=user.id
    ).all()

    deleted_count = len(notifications)

    for notification in notifications:
        db.session.delete(notification)

    db.session.commit()

    return jsonify({
        "message": "All notifications deleted successfully",
        "deleted_count": deleted_count
    }), 200

# ============================================================
# PROFILE
# ============================================================

@api.get("/profile")
@token_required
def get_profile(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    return jsonify({
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role,
            "status": user.status
        },
        "learner": (
            {
                "id": learner.id,
                "education": learner.education,
                "batch_id": learner.batch_id,
                "status": learner.status
            }
            if learner
            else None
        ),
        "trainer": (
            {
                "id": trainer.id,
                "specialization": getattr(
                    trainer,
                    "specialization",
                    None
                ),
                "experience": getattr(
                    trainer,
                    "experience",
                    None
                ),
                "status": getattr(
                    trainer,
                    "status",
                    None
                )
            }
            if trainer
            else None
        )
    })


@api.put("/profile")
@token_required
def update_profile(user):
    data = request.get_json(silent=True) or {}

    if "name" in data:
        name = str(
            data.get("name", "")
        ).strip()

        if name:
            user.name = name

    if "mobile" in data:
        user.mobile = str(
            data.get("mobile", "")
        ).strip()

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if learner and "education" in data:
        learner.education = str(
            data.get("education", "")
        ).strip()

    db.session.commit()

    return jsonify({
        "message": "Profile updated successfully",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "mobile": user.mobile,
            "role": user.role,
            "status": user.status
        }
    })


# ============================================================
# CHANGE PASSWORD
# ============================================================

@api.post("/auth/change-password")
@token_required
def change_password(user):
    data = request.get_json(silent=True) or {}

    current_password = data.get(
        "current_password",
        ""
    )

    new_password = data.get(
        "new_password",
        ""
    )

    if not current_password:
        return jsonify({
            "error": "Current password is required"
        }), 400

    if not new_password:
        return jsonify({
            "error": "New password is required"
        }), 400

    if len(new_password) < 8:
        return jsonify({
            "error": "New password must be at least 8 characters"
        }), 400

    if not check_password_hash(
        user.password_hash,
        current_password
    ):
        return jsonify({
            "error": "Current password is incorrect"
        }), 401

    user.password_hash = create_password_hash(
        new_password
    )

    db.session.commit()

    return jsonify({
        "message": "Password changed successfully"
    })


# ============================================================
# ADMIN — LIST LEARNERS
# ============================================================
# ============================================================
# TRAINER — CODING EXAMS
# ============================================================

@api.get("/trainer/coding-exams")
@role_required("trainer")
def trainer_coding_exams(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingExam.query
        .filter_by(
            trainer_id=trainer.id
        )
        .order_by(
            CodingExam.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    exams = pagination.items

    result = []

    for exam in exams:
        question_count = CodingQuestion.query.filter_by(
            exam_id=exam.id
        ).count()

        result.append({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status,
            "question_count": question_count,
            "created_at": (
                exam.created_at.isoformat()
                if exam.created_at
                else None
            ),
            "updated_at": (
                exam.updated_at.isoformat()
                if exam.updated_at
                else None
            )
        })

        return jsonify({
        "exams": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.post("/trainer/coding-exams")
@role_required("trainer")
def trainer_create_coding_exam(user):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    course_id = str(
        data.get("course_id", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Exam title is required"
        }), 400

    if not course_id:
        return jsonify({
            "error": "Course ID is required"
        }), 400

    course = Course.query.filter_by(
        id=course_id,
        trainer_id=trainer.id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found or does not belong to you"
        }), 404

    try:
        duration = int(
            data.get("duration", 60)
        )
    except (TypeError, ValueError):
        duration = 60

    if duration <= 0:
        return jsonify({
            "error": "Duration must be greater than 0"
        }), 400

    exam = CodingExam(
        title=title,
        description=description,
        course_id=course.id,
        trainer_id=trainer.id,
        duration=duration,
        total_marks=0,
        status="draft"
    )

    db.session.add(exam)
    db.session.commit()

    return jsonify({
        "message": "Coding exam created successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status,
            "question_count": 0
        }
    }), 201


@api.get("/trainer/coding-exams/<int:exam_id>")
@role_required("trainer")
def trainer_get_coding_exam(user, exam_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingQuestion.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            CodingQuestion.order_index.asc(),
            CodingQuestion.id.asc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    questions = pagination.items

    question_list = []

    for question in questions:
        test_cases = CodingTestCase.query.filter_by(
            question_id=question.id
        ).order_by(
            CodingTestCase.order_index.asc(),
            CodingTestCase.id.asc()
        ).all()

        question_list.append({
            "id": question.id,
            "title": question.title,
            "description": question.description,
            "difficulty": question.difficulty,
            "points": question.points,
            "input_format": question.input_format,
            "output_format": question.output_format,
            "constraints": question.constraints,
            "starter_code": question.starter_code,
            "language": question.language,
            "order_index": question.order_index,
            "test_cases": [
                {
                    "id": test_case.id,
                    "input_data": test_case.input_data,
                    "expected_output": test_case.expected_output,
                    "is_sample": test_case.is_sample,
                    "order_index": test_case.order_index
                }
                for test_case in test_cases
            ]
        })

    return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status,
            "created_at": (
                exam.created_at.isoformat()
                if exam.created_at
                else None
            ),
            "updated_at": (
                exam.updated_at.isoformat()
                if exam.updated_at
                else None
            )
        },
        "questions": question_list
    })


@api.put("/trainer/coding-exams/<int:exam_id>")
@role_required("trainer")
def trainer_update_coding_exam(user, exam_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    if "title" in data:
        title = str(
            data.get("title", "")
        ).strip()

        if not title:
            return jsonify({
                "error": "Exam title cannot be empty"
            }), 400

        exam.title = title

    if "description" in data:
        exam.description = str(
            data.get("description", "")
        ).strip()

    if "duration" in data:
        try:
            duration = int(
                data.get("duration")
            )
        except (TypeError, ValueError):
            return jsonify({
                "error": "Duration must be a valid number"
            }), 400

        if duration <= 0:
            return jsonify({
                "error": "Duration must be greater than 0"
            }), 400

        exam.duration = duration

    if "status" in data:
        status = str(
            data.get("status", "")
        ).strip().lower()

        if status not in {
            "draft",
            "published"
        }:
            return jsonify({
                "error": "Status must be draft or published"
            }), 400

        exam.status = status

    if "course_id" in data:
        course_id = str(
            data.get("course_id", "")
        ).strip()

        course = Course.query.filter_by(
            id=course_id,
            trainer_id=trainer.id
        ).first()

        if not course:
            return jsonify({
                "error": "Course not found or does not belong to you"
            }), 404

        exam.course_id = course.id

    db.session.commit()

    return jsonify({
        "message": "Coding exam updated successfully",
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "trainer_id": exam.trainer_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status
        }
    })


@api.delete("/trainer/coding-exams/<int:exam_id>")
@role_required("trainer")
def trainer_delete_coding_exam(user, exam_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    questions = CodingQuestion.query.filter_by(
        exam_id=exam.id
    ).all()

    for question in questions:
        CodingTestCase.query.filter_by(
            question_id=question.id
        ).delete(
            synchronize_session=False
        )

        CodingSubmission.query.filter_by(
            question_id=question.id
        ).delete(
            synchronize_session=False
        )

        db.session.delete(question)

    CodingSubmission.query.filter_by(
        exam_id=exam.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(exam)
    db.session.commit()

    return jsonify({
        "message": "Coding exam deleted successfully"
    })

# ============================================================
# TRAINER — CODING QUESTIONS
# ============================================================

@api.get("/trainer/coding-exams/<int:exam_id>/questions")
@role_required("trainer")
def trainer_coding_questions(user, exam_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingQuestion.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            CodingQuestion.order_index.asc(),
            CodingQuestion.id.asc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    questions = pagination.items

    result = []

    for question in questions:
        test_cases = CodingTestCase.query.filter_by(
            question_id=question.id
        ).order_by(
            CodingTestCase.order_index.asc(),
            CodingTestCase.id.asc()
        ).all()

        result.append({
            "id": question.id,
            "exam_id": question.exam_id,
            "title": question.title,
            "description": question.description,
            "difficulty": question.difficulty,
            "points": question.points,
            "input_format": question.input_format,
            "output_format": question.output_format,
            "constraints": question.constraints,
            "starter_code": question.starter_code,
            "language": question.language,
            "order_index": question.order_index,
            "test_cases": [
                {
                    "id": test_case.id,
                    "input_data": test_case.input_data,
                    "expected_output": test_case.expected_output,
                    "is_sample": test_case.is_sample,
                    "order_index": test_case.order_index
                }
                for test_case in test_cases
            ]
        })

        return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status
        },
        "questions": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.post("/trainer/coding-exams/<int:exam_id>/questions")
@role_required("trainer")
def trainer_create_coding_question(user, exam_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    data = request.get_json(
        silent=True
    ) or {}

    title = str(
        data.get("title", "")
    ).strip()

    description = str(
        data.get("description", "")
    ).strip()

    if not title:
        return jsonify({
            "error": "Question title is required"
        }), 400

    if not description:
        return jsonify({
            "error": "Question description is required"
        }), 400

    try:
        points = int(
            data.get("points", 10)
        )
    except (TypeError, ValueError):
        points = 10

    if points <= 0:
        return jsonify({
            "error": "Points must be greater than 0"
        }), 400

    difficulty = str(
        data.get("difficulty", "medium")
    ).strip().lower()

    if difficulty not in {
        "easy",
        "medium",
        "hard"
    }:
        return jsonify({
            "error": "Difficulty must be easy, medium or hard"
        }), 400

    language = str(
        data.get("language", "python")
    ).strip().lower()

    allowed_languages = {
        "python",
        "javascript",
        "java",
        "cpp",
        "c"
    }

    if language not in allowed_languages:
        return jsonify({
            "error": "Unsupported programming language"
        }), 400

    try:
        order_index = int(
            data.get(
                "order_index",
                CodingQuestion.query.filter_by(
                    exam_id=exam.id
                ).count()
            )
        )
    except (TypeError, ValueError):
        order_index = CodingQuestion.query.filter_by(
            exam_id=exam.id
        ).count()

    question = CodingQuestion(
        exam_id=exam.id,
        title=title,
        description=description,
        difficulty=difficulty,
        points=points,
        input_format=str(
            data.get("input_format", "")
        ).strip(),
        output_format=str(
            data.get("output_format", "")
        ).strip(),
        constraints=str(
            data.get("constraints", "")
        ).strip(),
        starter_code=str(
            data.get("starter_code", "")
        ),
        language=language,
        order_index=order_index
    )

    db.session.add(question)
    db.session.flush()

    test_cases = data.get(
        "test_cases",
        []
    )

    if not isinstance(test_cases, list):
        test_cases = []

    for index, item in enumerate(test_cases):

        if not isinstance(item, dict):
            continue

        expected_output = str(
            item.get(
                "expected_output",
                ""
            )
        ).strip()

        if not expected_output:
            continue

        test_case = CodingTestCase(
            question_id=question.id,
            input_data=str(
                item.get(
                    "input_data",
                    ""
                )
            ),
            expected_output=expected_output,
            is_sample=bool(
                item.get(
                    "is_sample",
                    False
                )
            ),
            order_index=index
        )

        db.session.add(test_case)

    total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    CodingQuestion.points
                ),
                0
            )
        )
        .filter(
            CodingQuestion.exam_id == exam.id
        )
        .scalar()
    )

    exam.total_marks = int(
        total_marks or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Coding question created successfully",
        "question": {
            "id": question.id,
            "exam_id": question.exam_id,
            "title": question.title,
            "description": question.description,
            "difficulty": question.difficulty,
            "points": question.points,
            "input_format": question.input_format,
            "output_format": question.output_format,
            "constraints": question.constraints,
            "starter_code": question.starter_code,
            "language": question.language,
            "order_index": question.order_index,
            "test_cases": [
                {
                    "id": test_case.id,
                    "input_data": test_case.input_data,
                    "expected_output": test_case.expected_output,
                    "is_sample": test_case.is_sample,
                    "order_index": test_case.order_index
                }
                for test_case in CodingTestCase.query.filter_by(
                    question_id=question.id
                ).order_by(
                    CodingTestCase.order_index.asc()
                ).all()
            ]
        }
    }), 201


@api.put("/trainer/coding-questions/<int:question_id>")
@role_required("trainer")
def trainer_update_coding_question(user, question_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = CodingQuestion.query.get(
        question_id
    )

    if not question:
        return jsonify({
            "error": "Coding question not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=question.exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "You do not have access to this question"
        }), 403

    data = request.get_json(
        silent=True
    ) or {}

    if "title" in data:
        title = str(
            data.get("title", "")
        ).strip()

        if not title:
            return jsonify({
                "error": "Question title cannot be empty"
            }), 400

        question.title = title

    if "description" in data:
        description = str(
            data.get("description", "")
        ).strip()

        if not description:
            return jsonify({
                "error": "Question description cannot be empty"
            }), 400

        question.description = description

    if "difficulty" in data:
        difficulty = str(
            data.get("difficulty", "")
        ).strip().lower()

        if difficulty not in {
            "easy",
            "medium",
            "hard"
        }:
            return jsonify({
                "error": "Invalid difficulty"
            }), 400

        question.difficulty = difficulty

    if "points" in data:
        try:
            points = int(
                data.get("points")
            )
        except (TypeError, ValueError):
            return jsonify({
                "error": "Points must be a valid number"
            }), 400

        if points <= 0:
            return jsonify({
                "error": "Points must be greater than 0"
            }), 400

        question.points = points

    if "input_format" in data:
        question.input_format = str(
            data.get("input_format", "")
        ).strip()

    if "output_format" in data:
        question.output_format = str(
            data.get("output_format", "")
        ).strip()

    if "constraints" in data:
        question.constraints = str(
            data.get("constraints", "")
        ).strip()

    if "starter_code" in data:
        question.starter_code = str(
            data.get("starter_code", "")
        )

    if "language" in data:
        language = str(
            data.get("language", "")
        ).strip().lower()

        if language not in {
            "python",
            "javascript",
            "java",
            "cpp",
            "c"
        }:
            return jsonify({
                "error": "Unsupported programming language"
            }), 400

        question.language = language

    if "order_index" in data:
        try:
            question.order_index = int(
                data.get("order_index")
            )
        except (TypeError, ValueError):
            return jsonify({
                "error": "Order index must be a number"
            }), 400

    if "test_cases" in data:

        test_cases = data.get(
            "test_cases"
        )

        if not isinstance(test_cases, list):
            return jsonify({
                "error": "test_cases must be an array"
            }), 400

        CodingTestCase.query.filter_by(
            question_id=question.id
        ).delete(
            synchronize_session=False
        )

        for index, item in enumerate(test_cases):

            if not isinstance(item, dict):
                continue

            expected_output = str(
                item.get(
                    "expected_output",
                    ""
                )
            ).strip()

            if not expected_output:
                continue

            test_case = CodingTestCase(
                question_id=question.id,
                input_data=str(
                    item.get(
                        "input_data",
                        ""
                    )
                ),
                expected_output=expected_output,
                is_sample=bool(
                    item.get(
                        "is_sample",
                        False
                    )
                ),
                order_index=index
            )

            db.session.add(test_case)

    total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    CodingQuestion.points
                ),
                0
            )
        )
        .filter(
            CodingQuestion.exam_id == exam.id
        )
        .scalar()
    )

    exam.total_marks = int(
        total_marks or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Coding question updated successfully"
    })


@api.delete("/trainer/coding-questions/<int:question_id>")
@role_required("trainer")
def trainer_delete_coding_question(user, question_id):
    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    question = CodingQuestion.query.get(
        question_id
    )

    if not question:
        return jsonify({
            "error": "Coding question not found"
        }), 404

    exam = CodingExam.query.filter_by(
        id=question.exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "You do not have access to this question"
        }), 403

    CodingTestCase.query.filter_by(
        question_id=question.id
    ).delete(
        synchronize_session=False
    )

    CodingSubmission.query.filter_by(
        question_id=question.id
    ).delete(
        synchronize_session=False
    )

    db.session.delete(question)

    db.session.flush()

    total_marks = (
        db.session.query(
            db.func.coalesce(
                db.func.sum(
                    CodingQuestion.points
                ),
                0
            )
        )
        .filter(
            CodingQuestion.exam_id == exam.id
        )
        .scalar()
    )

    exam.total_marks = int(
        total_marks or 0
    )

    db.session.commit()

    return jsonify({
        "message": "Coding question deleted successfully"
    })

# ============================================================
# LEARNER — CODING EXAMS
# ============================================================

@api.get("/learner/coding-exams")
@role_required("learner")
def learner_coding_exams(user):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    enrolled_course_ids = {
        enrollment.course_id
        for enrollment in enrollments
    }

    if not enrolled_course_ids:
        return jsonify({
            "exams": []
        })

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingExam.query
        .filter(
            CodingExam.course_id.in_(
                enrolled_course_ids
            ),
            CodingExam.status == "published"
        )
        .order_by(
            CodingExam.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    exams = pagination.items

    result = []

    for exam in exams:
        question_count = CodingQuestion.query.filter_by(
            exam_id=exam.id
        ).count()

        result.append({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "question_count": question_count,
            "status": exam.status,
            "created_at": (
                exam.created_at.isoformat()
                if exam.created_at
                else None
            ),
        })

        return jsonify({
        "exams": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })
# =========================================================
# LEARNER - CODING EXAM HISTORY
# =========================================================

@api.get("/learner/coding-exams/<int:exam_id>")
@role_required("learner")
def learner_get_coding_exam(user, exam_id):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    enrolled_course_ids = {
        enrollment.course_id
        for enrollment in enrollments
    }

    exam = CodingExam.query.filter(
        CodingExam.id == exam_id,
        CodingExam.status == "published",
        CodingExam.course_id.in_(
            enrolled_course_ids
        )
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found or you are not enrolled in this course"
        }), 404

    questions = CodingQuestion.query.filter_by(
        exam_id=exam.id
    ).order_by(
        CodingQuestion.order_index.asc(),
        CodingQuestion.id.asc()
    ).all()

    question_list = []

    for question in questions:

        test_cases = CodingTestCase.query.filter_by(
            question_id=question.id
        ).order_by(
            CodingTestCase.order_index.asc(),
            CodingTestCase.id.asc()
        ).all()

        visible_test_cases = []

        for test_case in test_cases:

            item = {
                "id": test_case.id,
                "input_data": test_case.input_data,
                "is_sample": bool(
                    test_case.is_sample
                ),
                "order_index": test_case.order_index
            }

            # Only sample test cases expose
            # their expected output to learners.
            if test_case.is_sample:
                item["expected_output"] = (
                    test_case.expected_output
                )

            visible_test_cases.append(item)

        question_list.append({
            "id": question.id,
            "exam_id": question.exam_id,
            "title": question.title,
            "description": question.description,
            "difficulty": question.difficulty,
            "points": question.points,
            "input_format": question.input_format,
            "output_format": question.output_format,
            "constraints": question.constraints,
            "starter_code": question.starter_code,
            "language": question.language,
            "order_index": question.order_index,
            "test_cases": visible_test_cases
        })

    return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status
        },
        "questions": question_list
    })

@api.get("/learner/coding-exams/history")
@role_required("learner")
def learner_coding_exam_history(user):

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    enrolled_course_ids = {
        enrollment.course_id
        for enrollment in enrollments
    }

    if not enrolled_course_ids:
        return jsonify({
            "exams": []
        }), 200

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingExam.query
        .filter(
            CodingExam.course_id.in_(enrolled_course_ids),
            CodingExam.status == "published"
        )
        .order_by(
            CodingExam.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    exams = pagination.items

    exam_history = []

    for exam in exams:

        questions = CodingQuestion.query.filter_by(
            exam_id=exam.id
        ).order_by(
            CodingQuestion.order_index.asc(),
            CodingQuestion.id.asc()
        ).all()

        if not questions:
            continue

        question_ids = {
            question.id
            for question in questions
        }

        submissions = CodingSubmission.query.filter(
            CodingSubmission.exam_id == exam.id,
            CodingSubmission.learner_id == learner.id,
            CodingSubmission.question_id.in_(question_ids)
        ).order_by(
            CodingSubmission.submitted_at.desc(),
            CodingSubmission.id.desc()
        ).all()

        # Keep only the latest submission for each question
        latest_submissions = {}

        for submission in submissions:
            if submission.question_id not in latest_submissions:
                latest_submissions[
                    submission.question_id
                ] = submission

        total_questions = len(questions)

        answered_questions = len(
            latest_submissions
        )

        total_marks = sum(
            int(question.points or 0)
            for question in questions
        )

        score = sum(
            int(submission.score or 0)
            for submission in latest_submissions.values()
        )

        percentage = (
            round(
                (score / total_marks) * 100,
                2
            )
            if total_marks > 0
            else 0
        )

        attempted = answered_questions > 0

        completed = (
            total_questions > 0
            and answered_questions >= total_questions
        )

        if not attempted:
            status = "not_attempted"

        elif not completed:
            status = "in_progress"

        elif score >= total_marks:
            status = "passed"

        else:
            status = "failed"

        last_submitted_at = None

        if latest_submissions:

            submitted_dates = [
                submission.submitted_at
                for submission in latest_submissions.values()
                if submission.submitted_at
            ]

            if submitted_dates:
                last_submitted_at = max(
                    submitted_dates
                ).isoformat()

        exam_history.append({
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "course_id": exam.course_id,
            "duration": exam.duration,
            "total_marks": total_marks,

            "attempted": attempted,
            "completed": completed,

            "status": status,

            "score": score,
            "percentage": percentage,

            "total_questions": total_questions,
            "answered_questions": answered_questions,

            "last_submitted_at": last_submitted_at
        })

        return jsonify({
        "exams": exam_history,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200

# ============================================================
# LEARNER — CODING EXAM MONITORING SESSION
# ============================================================

@api.post("/learner/coding-exams/<int:exam_id>/session/start")
@role_required("learner")
def start_coding_exam_monitoring_session(user, exam_id):

    # --------------------------------------------------------
    # FIND LEARNER
    # --------------------------------------------------------

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND ENROLLED COURSE
    # --------------------------------------------------------

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    enrolled_course_ids = {
        enrollment.course_id
        for enrollment in enrollments
    }

    # --------------------------------------------------------
    # FIND PUBLISHED EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter(
        CodingExam.id == exam_id,
        CodingExam.status == "published",
        CodingExam.course_id.in_(enrolled_course_ids)
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found or you are not enrolled in this course"
        }), 404

    # --------------------------------------------------------
    # READ CAMERA / MICROPHONE STATUS
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    camera_enabled = bool(
        data.get("camera_enabled", False)
    )

    microphone_enabled = bool(
        data.get("microphone_enabled", False)
    )

    # Both devices are required for the monitored exam.
    if not camera_enabled:
        return jsonify({
            "error": "Camera permission is required before starting the exam"
        }), 400

    if not microphone_enabled:
        return jsonify({
            "error": "Microphone permission is required before starting the exam"
        }), 400

    # --------------------------------------------------------
    # CLOSE ANY PREVIOUS ACTIVE SESSION
    # --------------------------------------------------------

    previous_sessions = CodingExamSession.query.filter_by(
        exam_id=exam.id,
        learner_id=learner.id,
        status="active"
    ).all()

    for previous_session in previous_sessions:
        previous_session.status = "abandoned"
        previous_session.ended_at = datetime.now(timezone.utc)

    # --------------------------------------------------------
    # CREATE NEW MONITORING SESSION
    # --------------------------------------------------------

    session = CodingExamSession(
        exam_id=exam.id,
        learner_id=learner.id,
        started_at=datetime.now(timezone.utc),
        status="active",
        camera_enabled=camera_enabled,
        microphone_enabled=microphone_enabled,
        warning_count=0
    )

    db.session.add(session)
    db.session.flush()

    # --------------------------------------------------------
    # RECORD SESSION START EVENT
    # --------------------------------------------------------

    start_event = CodingExamMonitoringEvent(
        session_id=session.id,
        event_type="session_started",
        message="Coding exam monitoring session started",
        metadata_json='{"camera_enabled":true,"microphone_enabled":true}'
    )

    db.session.add(start_event)

    db.session.commit()

    return jsonify({
        "message": "Monitoring session started",
        "session": {
            "id": session.id,
            "exam_id": session.exam_id,
            "learner_id": session.learner_id,
            "started_at": (
                session.started_at.isoformat()
                if session.started_at
                else None
            ),
            "status": session.status,
            "camera_enabled": session.camera_enabled,
            "microphone_enabled": session.microphone_enabled,
            "warning_count": session.warning_count
        }
    }), 201

# ============================================================
# LEARNER CODING EXAM MONITORING EVENT
# ============================================================

@api.post(
    "/learner/coding-exams/<int:exam_id>/session/<int:session_id>/event"
)
@role_required("learner")
def record_coding_exam_monitoring_event(
    user,
    exam_id,
    session_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND MONITORING SESSION
    # --------------------------------------------------------

    session = CodingExamSession.query.filter_by(
        id=session_id,
        exam_id=exam_id,
        learner_id=learner.id
    ).first()

    if not session:
        return jsonify({
            "error": "Monitoring session not found"
        }), 404

    if session.status not in [
        "active",
        "flagged"
    ]:
        return jsonify({
            "error": "Monitoring session is no longer active"
        }), 400

    # --------------------------------------------------------
    # READ EVENT DATA
    # --------------------------------------------------------

    data = request.get_json(
        silent=True
    ) or {}

    event_type = str(
        data.get("event_type", "")
    ).strip()

    message = str(
        data.get("message", "")
    ).strip()

    metadata = data.get(
        "metadata",
        {}
    )

    # --------------------------------------------------------
    # ALLOWED MONITORING EVENTS
    # --------------------------------------------------------

    allowed_event_types = {
        "face_not_detected",
        "face_detected",
        "camera_disabled",
        "microphone_disabled",
        "monitoring_error",
        "tab_visibility_changed",
        "session_warning"
    }

    if event_type not in allowed_event_types:
        return jsonify({
            "error": "Invalid monitoring event type"
        }), 400

    # --------------------------------------------------------
    # CONVERT METADATA TO JSON
    # --------------------------------------------------------

    try:
        metadata_json = json.dumps(
            metadata
        )
    except (TypeError, ValueError):
        metadata_json = "{}"

    # --------------------------------------------------------
    # WARNING HANDLING
    # --------------------------------------------------------

    warning_count = (
        session.warning_count or 0
    )

    is_warning_event = (
        event_type == "face_not_detected"
    )

    if is_warning_event:

        # Never allow more than 3 warnings.
        if warning_count >= 3:
            return jsonify({
                "message":
                    "Maximum warning count already reached.",
                "warning_count": 3,
                "flagged": True
            }), 200

        warning_count += 1

        session.warning_count = (
            warning_count
        )

        # ----------------------------------------------------
        # THIRD WARNING
        # ----------------------------------------------------

        if warning_count >= 3:
            session.status = "flagged"

    # --------------------------------------------------------
    # CREATE MONITORING EVENT
    # --------------------------------------------------------

    monitoring_event = (
        CodingExamMonitoringEvent(
            session_id=session.id,
            event_type=event_type,
            message=message,
            event_time=datetime.now(timezone.utc),
            metadata_json=metadata_json
        )
    )

    db.session.add(
        monitoring_event
    )

    db.session.commit()

    return jsonify({
        "message":
            "Monitoring event recorded",

        "event": {
            "id":
                monitoring_event.id,

            "session_id":
                monitoring_event.session_id,

            "event_type":
                monitoring_event.event_type,

            "message":
                monitoring_event.message,

            "event_time":
                monitoring_event.event_time.isoformat()
                if monitoring_event.event_time
                else None
        },

        "warning_count":
            min(
                session.warning_count or 0,
                3
            ),

        "flagged":
            session.status == "flagged"
    }), 201

# ============================================================
# LEARNER CODING EXAM MONITORING SCREENSHOT
# ============================================================

@api.post(
    "/learner/coding-exams/<int:exam_id>/session/<int:session_id>/screenshot"
)
@role_required("learner")
def upload_coding_exam_monitoring_screenshot(
    user,
    exam_id,
    session_id
):
    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND MONITORING SESSION
    # --------------------------------------------------------

    session = CodingExamSession.query.filter_by(
        id=session_id,
        exam_id=exam_id,
        learner_id=learner.id
    ).first()

    if not session:
        return jsonify({
            "error": "Monitoring session not found"
        }), 404

    if session.status not in [
        "active",
        "flagged"
    ]:
        return jsonify({
            "error": "Monitoring session is no longer active"
        }), 400

    # --------------------------------------------------------
    # CHECK FILE
    # --------------------------------------------------------

    if "screenshot" not in request.files:
        return jsonify({
            "error": "Screenshot file is required"
        }), 400

    screenshot_file = request.files[
        "screenshot"
    ]

    if not screenshot_file:
        return jsonify({
            "error": "Invalid screenshot file"
        }), 400

    if not screenshot_file.filename:
        return jsonify({
            "error": "Screenshot filename is missing"
        }), 400

    # --------------------------------------------------------
    # CHECK MIME TYPE
    # --------------------------------------------------------

    allowed_types = {
        "image/jpeg",
        "image/png"
    }

    if screenshot_file.mimetype not in allowed_types:
        return jsonify({
            "error":
                "Only JPEG and PNG screenshots are allowed"
        }), 400

    # --------------------------------------------------------
    # LIMIT SCREENSHOT SIZE
    # --------------------------------------------------------

    screenshot_file.seek(
        0,
        os.SEEK_END
    )

    file_size = screenshot_file.tell()

    screenshot_file.seek(0)

    max_size = 2 * 1024 * 1024

    if file_size > max_size:
        return jsonify({
            "error":
                "Screenshot must be smaller than 2 MB"
        }), 400

    # --------------------------------------------------------
    # CREATE STORAGE DIRECTORY
    # --------------------------------------------------------

    upload_root = os.path.join(
        current_app.root_path,
        "uploads",
        "coding_exam_monitoring"
    )

    session_directory = os.path.join(
        upload_root,
        str(exam_id),
        str(learner.id),
        str(session.id)
    )

    os.makedirs(
        session_directory,
        exist_ok=True
    )

    # --------------------------------------------------------
    # CREATE SAFE FILE NAME
    # --------------------------------------------------------

    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    extension = ".jpg"

    if screenshot_file.mimetype == "image/png":
        extension = ".png"

    filename = (
        f"screenshot_{timestamp}{extension}"
    )

    filename = secure_filename(
        filename
    )

    file_path = os.path.join(
        session_directory,
        filename
    )

    # --------------------------------------------------------
    # SAVE FILE
    # --------------------------------------------------------

    screenshot_file.save(
        file_path
    )

    # --------------------------------------------------------
    # SAVE DATABASE RECORD
    # --------------------------------------------------------

    screenshot_record = CodingExamScreenshot(
        session_id=session.id,
        file_path=file_path,
        captured_at=datetime.now(timezone.utc)
    )

    db.session.add(
        screenshot_record
    )

    # Also create a monitoring event.
    screenshot_event = (
        CodingExamMonitoringEvent(
            session_id=session.id,
            event_type="screenshot_captured",
            message=
                "Random monitoring screenshot captured.",
            event_time=datetime.now(timezone.utc),
            metadata_json=json.dumps({
                "screenshot_id":
                    screenshot_record.id
            })
        )
    )

    db.session.add(
        screenshot_event
    )

    db.session.commit()

    return jsonify({
        "message":
            "Monitoring screenshot stored",

        "screenshot": {
            "id":
                screenshot_record.id,

            "session_id":
                screenshot_record.session_id,

            "captured_at":
                screenshot_record.captured_at.isoformat()
                if screenshot_record.captured_at
                else None
        }
    }), 201


# ============================================================
# LEARNER — RUN CODING CODE
# ============================================================

@api.post("/learner/coding-exams/run-code")
@role_required("learner")
def learner_run_coding_code(user):

    data = request.get_json(
        silent=True
    ) or {}

    code = data.get("code", "")

    input_data = data.get(
        "input_data",
        ""
    )
    language = data.get("language", "python")

    language = data.get(
        "language",
        "python"
    )

    # --------------------------------------------------------
    # VALIDATE CODE
    # --------------------------------------------------------

    if not isinstance(code, str):
        return jsonify({
            "error": "Code must be text"
        }), 400

    if not code.strip():
        return jsonify({
            "status": "empty",
            "stdout": "",
            "stderr": "No code was provided.",
            "execution_time": 0
        }), 400

    # --------------------------------------------------------
    # VALIDATE INPUT
    # --------------------------------------------------------

    if not isinstance(input_data, str):
        input_data = str(input_data)

    # --------------------------------------------------------
    # VALIDATE LANGUAGE
    # --------------------------------------------------------

    if not isinstance(language, str):
        return jsonify({
            "error": "Programming language must be text"
        }), 400

    language = language.strip()

    if not language:
        language = "python"

    # --------------------------------------------------------
    # RUN CODE IN DOCKER
    # --------------------------------------------------------

    result = run_code(
        code=code,
        language=language,
        input_data=input_data
    )

    # --------------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------------

    return jsonify({
        "status": result.get(
            "status",
            "error"
        ),

        "stdout": result.get(
            "stdout",
            ""
        ),

        "stderr": result.get(
            "stderr",
            ""
        ),

        "execution_time": result.get(
            "execution_time",
            0
        )
    })

# ============================================================
# LEARNER — SUBMIT CODING QUESTION
# ============================================================

@api.post("/learner/coding-exams/submit-code")
@role_required("learner")
def learner_submit_coding_code(user):
    data = request.get_json(silent=True) or {}

    exam_id = data.get("exam_id")
    question_id = data.get("question_id")
    language = data.get("language", "python")
    source_code = data.get("code", "")

    # --------------------------------------------------------
    # VALIDATION
    # --------------------------------------------------------

    if not exam_id:
        return jsonify({
            "error": "Exam ID is required"
        }), 400

    if not question_id:
        return jsonify({
            "error": "Question ID is required"
        }), 400

    if not isinstance(source_code, str):
        return jsonify({
            "error": "Code must be text"
        }), 400

    if not source_code.strip():
        return jsonify({
            "error": "Code cannot be empty"
        }), 400

    # --------------------------------------------------------
    # LEARNER
    # --------------------------------------------------------

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter_by(
        id=exam_id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    # --------------------------------------------------------
    # QUESTION
    # --------------------------------------------------------

    question = CodingQuestion.query.filter_by(
        id=question_id,
        exam_id=exam.id
    ).first()

    if not question:
        return jsonify({
            "error": "Coding question not found"
        }), 404

    # --------------------------------------------------------
    # CHECK LANGUAGE
    # --------------------------------------------------------

    #if language != "python":
        return jsonify({
            "error": (
                "Python code execution is currently "
                "supported. Other languages will be "
                "added separately."
            )
        }), 400#

    # --------------------------------------------------------
    # GET ALL TEST CASES
    #
    # IMPORTANT:
    # This includes both sample and hidden test cases.
    # Hidden expected outputs NEVER go to the frontend.
    # --------------------------------------------------------

    test_cases = CodingTestCase.query.filter_by(
        question_id=question.id
    ).order_by(
        CodingTestCase.order_index.asc(),
        CodingTestCase.id.asc()
    ).all()

    if not test_cases:
        return jsonify({
            "error": "No test cases are configured for this question"
        }), 400

    # --------------------------------------------------------
    # EXECUTE ALL TEST CASES
    # --------------------------------------------------------

    passed_tests = 0
    total_tests = len(test_cases)

    total_execution_time = 0.0

    test_results = []

    for index, test_case in enumerate(test_cases):

        input_data = test_case.input_data or ""
        expected_output = (
            test_case.expected_output or ""
        )

        # ----------------------------------------------------
        # RUN CODE IN DOCKER
        # ----------------------------------------------------

        result = run_code(
        code=source_code,
        language=language,
        input_data=input_data
        )
        

        status = result.get(
            "status",
            "error"
        )

        stdout = result.get(
            "stdout",
            ""
        )

        stderr = result.get(
            "stderr",
            ""
        )

        execution_time = float(
            result.get(
                "execution_time",
                0
            ) or 0
        )

        total_execution_time += (
            execution_time
        )

        # ----------------------------------------------------
        # NORMALIZE OUTPUT
        #
        # Ignore trailing spaces/newlines when comparing.
        # ----------------------------------------------------

        actual_normalized = (
            stdout.strip()
        )

        expected_normalized = (
            expected_output.strip()
        )

        passed = (
            status == "success"
            and
            actual_normalized ==
            expected_normalized
        )

        if passed:
            passed_tests += 1

        # ----------------------------------------------------
        # RESULT FOR FRONTEND
        #
        # NEVER expose expected output for hidden tests.
        # ----------------------------------------------------

        test_result = {
            "test_case": index + 1,
            "is_sample": bool(
                test_case.is_sample
            ),
            "status": (
                "passed"
                if passed
                else "failed"
            ),
            "execution_status": status,
            "execution_time": execution_time,
        }

        # ----------------------------------------------------
        # SAMPLE TEST CASE
        #
        # We can show actual output.
        # ----------------------------------------------------

        if test_case.is_sample:
            test_result["input"] = (
                input_data
            )

            test_result["expected_output"] = (
                expected_output
            )

            test_result["actual_output"] = (
                stdout
            )

            if stderr:
                test_result["error"] = stderr

        # ----------------------------------------------------
        # HIDDEN TEST CASE
        #
        # Do NOT expose expected output.
        # ----------------------------------------------------

        else:
            test_result["input"] = (
                None
            )

            test_result["expected_output"] = (
                None
            )

            test_result["actual_output"] = (
                None
            )

            if stderr:
                test_result["error"] = stderr

        test_results.append(
            test_result
        )

        # ----------------------------------------------------
        # STOP AFTER TIME LIMIT / RUNTIME ERROR
        #
        # The remaining tests are marked failed.
        # ----------------------------------------------------

        if status in (
            "time_limit_exceeded",
            "runtime_error"
        ):
            remaining_tests = (
                test_cases[index + 1:]
            )

            for remaining_index, _ in enumerate(
                remaining_tests,
                start=index + 2
            ):
                test_results.append({
                    "test_case": remaining_index,
                    "is_sample": False,
                    "status": "not_run",
                    "execution_status": "not_run",
                    "execution_time": 0,
                    "input": None,
                    "expected_output": None,
                    "actual_output": None,
                })

            break

    # --------------------------------------------------------
    # SCORE
    # --------------------------------------------------------

    score = int(
        round(
            (
                passed_tests /
                total_tests
            ) * question.points
        )
    )

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    if passed_tests == total_tests:
        submission_status = "accepted"

    elif passed_tests > 0:
        submission_status = "partial"

    else:
        submission_status = "failed"

    # --------------------------------------------------------
    # SAVE SUBMISSION
    # --------------------------------------------------------

    submission = CodingSubmission(
        exam_id=exam.id,
        question_id=question.id,
        learner_id=learner.id,
        language=language,
        source_code=source_code,
        status=submission_status,
        score=score,
        total_tests=total_tests,
        passed_tests=passed_tests,
        execution_time=total_execution_time,
    )

    db.session.add(submission)
    db.session.commit()

    # --------------------------------------------------------
    # RESPONSE
    # --------------------------------------------------------

    return jsonify({
        "message": "Code evaluated successfully",

        "submission": {
            "id": submission.id,
            "status": submission.status,
            "score": submission.score,
            "total_tests": submission.total_tests,
            "passed_tests": submission.passed_tests,
            "execution_time": (
                submission.execution_time
            ),
            "submitted_at": (
                submission.submitted_at.isoformat()
                if submission.submitted_at
                else None
            ),
        },

        "results": test_results,
    }), 200

# ============================================================
# TRAINER — CODING EXAM SUBMISSIONS
# ============================================================

@api.get("/trainer/coding-exams/<int:exam_id>/submissions")
@role_required("trainer")
def trainer_coding_exam_submissions(user, exam_id):

    # --------------------------------------------------------
    # FIND TRAINER
    # --------------------------------------------------------

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter_by(
        id=exam_id,
        trainer_id=trainer.id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    # --------------------------------------------------------
    # GET QUESTIONS
    # --------------------------------------------------------

    questions = CodingQuestion.query.filter_by(
        exam_id=exam.id
    ).order_by(
        CodingQuestion.order_index.asc(),
        CodingQuestion.id.asc()
    ).all()

    question_map = {
        question.id: question
        for question in questions
    }

    # --------------------------------------------------------
    # GET SUBMISSIONS
    # --------------------------------------------------------

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingSubmission.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            CodingSubmission.submitted_at.desc(),
            CodingSubmission.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    submissions = pagination.items

    # --------------------------------------------------------
    # BUILD RESPONSE
    # --------------------------------------------------------

    result = []

    for submission in submissions:

        question = question_map.get(
            submission.question_id
        )

        learner = Learner.query.get(
            submission.learner_id
        )

        learner_name = "Unknown Learner"
        learner_email = ""

        if learner:
            learner_user = User.query.get(
                learner.user_id
            )

            if learner_user:
                learner_name = (
                    getattr(
                        learner_user,
                        "name",
                        None
                    )
                    or getattr(
                        learner_user,
                        "full_name",
                        None
                    )
                    or getattr(
                        learner_user,
                        "username",
                        None
                    )
                    or "Unknown Learner"
                )

                learner_email = (
                    getattr(
                        learner_user,
                        "email",
                        ""
                    )
                    or ""
                )

        result.append({
            "id": submission.id,

            "exam_id": submission.exam_id,

            "question_id": (
                submission.question_id
            ),

            "question_title": (
                question.title
                if question
                else "Unknown Question"
            ),

            "learner_id": (
                submission.learner_id
            ),

            "learner_name": learner_name,

            "learner_email": learner_email,

            "language": submission.language,

            "status": submission.status,

            "score": submission.score,

            "total_tests": (
                submission.total_tests
            ),

            "passed_tests": (
                submission.passed_tests
            ),

            "execution_time": (
                submission.execution_time
            ),

            "submitted_at": (
                submission.submitted_at.isoformat()
                if submission.submitted_at
                else None
            )
        })

    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    total_submissions = (
        CodingSubmission.query
        .filter_by(
            exam_id=exam.id
        )
        .count()
    )

    accepted_count = (
        CodingSubmission.query
        .filter_by(
            exam_id=exam.id,
            status="accepted"
        )
        .count()
    )

    partial_count = (
        CodingSubmission.query
        .filter_by(
            exam_id=exam.id,
            status="partial"
        )
        .count()
    )

    failed_count = (
        CodingSubmission.query
        .filter_by(
            exam_id=exam.id,
            status="failed"
        )
        .count()
    )

    return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "course_id": exam.course_id,
            "duration": exam.duration,
            "total_marks": exam.total_marks,
            "status": exam.status
        },

        "summary": {
            "total_submissions": (
                total_submissions
            ),
            "accepted": accepted_count,
            "partial": partial_count,
            "failed": failed_count
        },

        "submissions": result,

        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    }), 200

# ============================================================
# TRAINER CODING EXAM MONITORING
# ============================================================

@api.get(
    "/trainer/coding-exams/<int:exam_id>/monitoring"
)
@role_required("trainer")
def trainer_coding_exam_monitoring(
    user,
    exam_id
):
    # --------------------------------------------------------
    # FIND TRAINER
    # --------------------------------------------------------

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter_by(
        id=exam_id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    # --------------------------------------------------------
    # VERIFY TRAINER OWNS THE COURSE
    # --------------------------------------------------------

    course = Course.query.filter_by(
        id=exam.course_id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You are not authorized to view this exam"
        }), 403

    # --------------------------------------------------------
    # GET MONITORING SESSIONS
    # --------------------------------------------------------

    try:
        page = max(
            int(request.args.get("page", 1)),
            1
        )
    except (TypeError, ValueError):
        page = 1

    try:
        limit = min(
            max(
                int(request.args.get("limit", 20)),
                1
            ),
            100
        )
    except (TypeError, ValueError):
        limit = 20

    pagination = (
        CodingExamSession.query
        .filter_by(
            exam_id=exam.id
        )
        .order_by(
            CodingExamSession.started_at.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    sessions = pagination.items

    result = []

    for session in sessions:

        learner = Learner.query.filter_by(
            id=session.learner_id
        ).first()

        user_record = None

        if learner:
            user_record = User.query.filter_by(
                id=learner.user_id
            ).first()

        # ----------------------------------------------------
        # EVENTS
        # ----------------------------------------------------

        events = (
            CodingExamMonitoringEvent.query
            .filter_by(
                session_id=session.id
            )
            .order_by(
                CodingExamMonitoringEvent.event_time.asc()
            )
            .all()
        )

        event_data = []

        for event in events:
            try:
                metadata = (
                    json.loads(
                        event.metadata_json or "{}"
                    )
                )
            except (
                TypeError,
                ValueError
            ):
                metadata = {}

            event_data.append({
                "id":
                    event.id,

                "event_type":
                    event.event_type,

                "message":
                    event.message,

                "event_time":
                    event.event_time.isoformat()
                    if event.event_time
                    else None,

                "metadata":
                    metadata
            })

        # ----------------------------------------------------
        # SCREENSHOTS
        # ----------------------------------------------------

        screenshots = (
            CodingExamScreenshot.query
            .filter_by(
                session_id=session.id
            )
            .order_by(
                CodingExamScreenshot.captured_at.asc()
            )
            .all()
        )

        screenshot_data = []

        for screenshot in screenshots:
            screenshot_data.append({
                "id":
                    screenshot.id,

                "captured_at":
                    screenshot.captured_at.isoformat()
                    if screenshot.captured_at
                    else None,

                "url":
                    f"/api/trainer/coding-exams/"
                    f"{exam.id}/monitoring/"
                    f"screenshots/"
                    f"{screenshot.id}"
            })

        # ----------------------------------------------------
        # SESSION DATA
        # ----------------------------------------------------

        result.append({
            "session": {
                "id":
                    session.id,

                "exam_id":
                    session.exam_id,

                "learner_id":
                    session.learner_id,

                "started_at":
                    session.started_at.isoformat()
                    if session.started_at
                    else None,

                "ended_at":
                    session.ended_at.isoformat()
                    if session.ended_at
                    else None,

                "status":
                    session.status,

                "camera_enabled":
                    session.camera_enabled,

                "microphone_enabled":
                    session.microphone_enabled,

                "warning_count":
                    min(
                        session.warning_count or 0,
                        3
                    )
            },

            "learner": {
                "id":
                    learner.id
                    if learner
                    else None,

                "name":
                    (
                        user_record.name
                        if user_record
                        and hasattr(
                            user_record,
                            "name"
                        )
                        else None
                    ),

                "email":
                    (
                        user_record.email
                        if user_record
                        else None
                    )
            },

            "events":
                event_data,

            "screenshots":
                screenshot_data
        })

    return jsonify({
        "exam": {
            "id":
                exam.id,

            "title":
                exam.title
        },

        "sessions":
            result,

        "pagination": {
            "page":
                pagination.page,

            "limit":
                pagination.per_page,

            "total":
                pagination.total,

            "pages":
                pagination.pages,

            "has_next":
                pagination.has_next,

            "has_previous":
                pagination.has_prev
        }
    }), 200

# ============================================================
# TRAINER CODING EXAM MONITORING SCREENSHOT VIEW
# ============================================================

@api.get(
    "/trainer/coding-exams/<int:exam_id>/monitoring/screenshots/<int:screenshot_id>"
)
@role_required("trainer")
def trainer_coding_exam_monitoring_screenshot(
    user,
    exam_id,
    screenshot_id
):
    # --------------------------------------------------------
    # FIND TRAINER
    # --------------------------------------------------------

    trainer = Trainer.query.filter_by(
        user_id=user.id
    ).first()

    if not trainer:
        return jsonify({
            "error": "Trainer profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter_by(
        id=exam_id
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found"
        }), 404

    # --------------------------------------------------------
    # VERIFY TRAINER OWNS THE COURSE
    # --------------------------------------------------------

    course = Course.query.filter_by(
        id=exam.course_id
    ).first()

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    if course.trainer_id != trainer.id:
        return jsonify({
            "error":
                "You are not authorized to view this screenshot"
        }), 403

    # --------------------------------------------------------
    # FIND SCREENSHOT
    # --------------------------------------------------------

    screenshot = CodingExamScreenshot.query.filter_by(
        id=screenshot_id
    ).first()

    if not screenshot:
        return jsonify({
            "error": "Screenshot not found"
        }), 404

    # --------------------------------------------------------
    # VERIFY SCREENSHOT BELONGS TO THIS EXAM
    # --------------------------------------------------------

    session = CodingExamSession.query.filter_by(
        id=screenshot.session_id,
        exam_id=exam.id
    ).first()

    if not session:
        return jsonify({
            "error":
                "Screenshot does not belong to this exam"
        }), 404

    # --------------------------------------------------------
    # VERIFY FILE EXISTS
    # --------------------------------------------------------

    if not os.path.isfile(
        screenshot.file_path
    ):
        return jsonify({
            "error":
                "Screenshot file no longer exists"
        }), 404

    # --------------------------------------------------------
    # RETURN IMAGE
    # --------------------------------------------------------

    mime_type = "image/jpeg"

    if screenshot.file_path.lower().endswith(
    ".png"
    ):
        mime_type = "image/png"

    return send_file(
    screenshot.file_path,
    mimetype=mime_type,
    as_attachment=False
)

# ============================================================
# LEARNER — CODING EXAM RESULT
# ============================================================

@api.get("/learner/coding-exams/<int:exam_id>/result")
@role_required("learner")
def learner_coding_exam_result(user, exam_id):

    # --------------------------------------------------------
    # FIND LEARNER
    # --------------------------------------------------------

    learner = Learner.query.filter_by(
        user_id=user.id
    ).first()

    if not learner:
        return jsonify({
            "error": "Learner profile not found"
        }), 404

    # --------------------------------------------------------
    # FIND ENROLLED COURSE
    # --------------------------------------------------------

    enrollments = Enrollment.query.filter_by(
        learner_id=learner.id
    ).all()

    enrolled_course_ids = {
        enrollment.course_id
        for enrollment in enrollments
    }

    # --------------------------------------------------------
    # FIND EXAM
    # --------------------------------------------------------

    exam = CodingExam.query.filter(
        CodingExam.id == exam_id,
        CodingExam.status == "published",
        CodingExam.course_id.in_(enrolled_course_ids)
    ).first()

    if not exam:
        return jsonify({
            "error": "Coding exam not found or you are not enrolled in this course"
        }), 404

    # --------------------------------------------------------
    # GET ALL QUESTIONS
    # --------------------------------------------------------

    questions = CodingQuestion.query.filter_by(
        exam_id=exam.id
    ).order_by(
        CodingQuestion.order_index.asc(),
        CodingQuestion.id.asc()
    ).all()

    question_ids = {
        question.id
        for question in questions
    }

    # --------------------------------------------------------
    # GET LEARNER SUBMISSIONS
    # --------------------------------------------------------

    submissions = CodingSubmission.query.filter(
        CodingSubmission.exam_id == exam.id,
        CodingSubmission.learner_id == learner.id,
        CodingSubmission.question_id.in_(question_ids)
    ).order_by(
        CodingSubmission.submitted_at.desc(),
        CodingSubmission.id.desc()
    ).all()

    # --------------------------------------------------------
    # USE LATEST SUBMISSION FOR EACH QUESTION
    # --------------------------------------------------------

    latest_submissions = {}

    for submission in submissions:

        if submission.question_id not in latest_submissions:
            latest_submissions[
                submission.question_id
            ] = submission

    # --------------------------------------------------------
    # CALCULATE RESULT
    # --------------------------------------------------------

    total_questions = len(questions)

    answered_questions = len(
        latest_submissions
    )

    total_marks = sum(
        int(question.points or 0)
        for question in questions
    )

    score = sum(
        int(submission.score or 0)
        for submission in latest_submissions.values()
    )

    passed_tests = sum(
        int(submission.passed_tests or 0)
        for submission in latest_submissions.values()
    )

    total_tests = sum(
        int(submission.total_tests or 0)
        for submission in latest_submissions.values()
    )

    accepted_questions = sum(
        1
        for submission in latest_submissions.values()
        if submission.status == "accepted"
    )

    partial_questions = sum(
        1
        for submission in latest_submissions.values()
        if submission.status == "partial"
    )

    failed_questions = sum(
        1
        for submission in latest_submissions.values()
        if submission.status == "failed"
    )

    completed = (
        total_questions > 0
        and answered_questions >= total_questions
    )

        # --------------------------------------------------------
    # QUESTION RESULTS
    # --------------------------------------------------------

    question_results = []

    for question in questions:

        submission = latest_submissions.get(
            question.id
        )

        question_results.append({

            # ------------------------------------------------
            # QUESTION INFORMATION
            # ------------------------------------------------

            "question_id": question.id,

            "question_title": question.title,

            "question_description": (
                question.description
                if question.description
                else ""
            ),

            "difficulty": (
                question.difficulty
                if question.difficulty
                else "medium"
            ),

            "points": (
                int(question.points or 0)
            ),

            # ------------------------------------------------
            # SUBMISSION INFORMATION
            # ------------------------------------------------

            "submitted": (
                submission is not None
            ),

            "status": (
                submission.status
                if submission
                else "not_submitted"
            ),

            "score": (
                int(submission.score or 0)
                if submission
                else 0
            ),

            # ------------------------------------------------
            # TEST RESULTS
            # ------------------------------------------------

            "passed_tests": (
                int(
                    submission.passed_tests or 0
                )
                if submission
                else 0
            ),

            "total_tests": (
                int(
                    submission.total_tests or 0
                )
                if submission
                else 0
            ),

            # ------------------------------------------------
            # CODE INFORMATION
            # ------------------------------------------------

            "language": (
                submission.language
                if submission
                else question.language
            ),

            "source_code": (
                submission.source_code
                if submission
                else ""
            ),

            # ------------------------------------------------
            # EXECUTION INFORMATION
            # ------------------------------------------------

            "execution_time": (
                submission.execution_time
                if submission
                else 0
            ),

            # ------------------------------------------------
            # SUBMISSION TIME
            # ------------------------------------------------

            "submitted_at": (
                submission.submitted_at.isoformat()
                if submission
                and submission.submitted_at
                else None
            )
        })

        # --------------------------------------------------------
    # COMPLETION TIME
    # --------------------------------------------------------

    completed_at = None

    if latest_submissions:
        submitted_dates = [
            submission.submitted_at
            for submission in latest_submissions.values()
            if submission.submitted_at
        ]

        if submitted_dates:
            completed_at = max(
                submitted_dates
            ).isoformat()

    # --------------------------------------------------------
    # RETURN FINAL RESULT
    # --------------------------------------------------------

    return jsonify({
        "exam": {
            "id": exam.id,
            "title": exam.title,
            "description": exam.description,
            "duration": exam.duration,
            "total_marks": total_marks,
            "status": exam.status
        },

        "completed": completed,

        "completed_at": completed_at,

        "result": {
            "score": score,
            "total_marks": total_marks,

            "percentage": (
                round(
                    (score / total_marks) * 100,
                    2
                )
                if total_marks > 0
                else 0
            ),

            "total_questions": total_questions,
            "answered_questions": answered_questions,

            "accepted_questions": accepted_questions,
            "partial_questions": partial_questions,
            "failed_questions": failed_questions,

            "passed_tests": passed_tests,
            "total_tests": total_tests
        },

        "questions": question_results
    }), 200


# FINAL BLUEPRINT REGISTRATION
# ============================================================

def register_routes(app):
    """
    Register the API blueprint.

    This function is optional if your app/__init__.py already
    imports and registers the blueprint directly.
    """
    app.register_blueprint(
        api,
        url_prefix="/api"
    )


# ============================================================
# END OF routes.py
# ============================================================
