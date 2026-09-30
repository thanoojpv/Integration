from flask import (
    Blueprint,
    request,
    jsonify,
    send_from_directory,
    current_app,
)

import os
import shutil
import secrets
import random
import json
import uuid
from datetime import datetime, timedelta, timezone

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
    LessonResource,
    Wishlist,
    Discussion,
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

    module_result = []

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
                    "type": resource.resource_type,
                    "fileName": resource.file_name,
                    "title": resource.title or resource.file_name,
                    "url": "/api/files/" + os.path.relpath(
                         resource.file_path,
                        current_app.config["UPLOAD_FOLDER"],
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
            "course_id": module.course_id,
            "title": module.title,
            "description": getattr(
                module,
                "description",
                "",
            ),
            "lessons": lesson_result,
        })

    return jsonify({
        "course":
            course_json(
                course,
                progress,
            ),
        "modules":
            module_result,
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
            "error":
                "Trainer profile not found"
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
            "error":
                "Course ID is required"
        }), 400

    if not title:
        return jsonify({
            "error":
                "Course title is required"
        }), 400

    if Course.query.get(course_id):
        return jsonify({
            "error":
                "Course ID already exists"
        }), 409

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

@api.post(
    "/courses/<course_id>/enroll"
)
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

    enrollment = (
        Enrollment.query
        .filter_by(
            learner_id=learner.id,
            course_id=course.id,
        )
        .first()
    )

    if enrollment:
        if enrollment.status != "active":
            enrollment.status = "active"
            db.session.commit()

        return jsonify({
            "message":
                "Already enrolled in this course",
            "enrollment": {
                "id": enrollment.id,
                "course_id": enrollment.course_id,
                "progress":
                    enrollment.progress or 0,
                "status":
                    enrollment.status,
            },
        })

    enrollment = Enrollment(
        learner_id=learner.id,
        course_id=course.id,
        progress=0,
        status="active",
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({
        "message":
            "Course enrolled successfully",
        "enrollment": {
            "id": enrollment.id,
            "course_id": enrollment.course_id,
            "progress": 0,
            "status": enrollment.status,
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

    lesson = db.session.get(
        Lesson,
        lesson_id
    )

    if not lesson:
        return jsonify({
            "error": "Lesson not found"
        }), 404

    # --------------------------------------------------------
    # Find the course through the lesson's module
    # --------------------------------------------------------

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
        item.id
        for item in course_lessons
    ]

    if lesson_ids:
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
            (completed_count / len(lesson_ids)) * 100
        )

    else:
        percentage = 0

    enrollment.progress = percentage

    # --------------------------------------------------------
    # Course completion
    # --------------------------------------------------------

    if percentage >= 100:
        enrollment.status = "completed"

        # ----------------------------------------------------
        # Generate certificate automatically
        # ----------------------------------------------------

        existing_certificate = (
            Certificate.query
            .filter_by(
                learner_id=learner.id,
                course_id=course.id
            )
            .first()
        )

        if not existing_certificate:

            now = datetime.now(
                timezone.utc
            )

            certificate_id = f"CERT-{secrets.token_urlsafe(24)}"

            certificate = Certificate(
                certificate_id=certificate_id,
                learner_id=learner.id,
                course_id=course.id,
                start_date=(
                    enrollment.enrolled_at
                    or now
                ),
                end_date=now,
                status="valid"
            )

            db.session.add(
                certificate
            )

    db.session.commit()

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

    quiz = Quiz.query.get(
        Quiz,
        exam_id
    )

    if not quiz:
        return jsonify({
            "error": "Exam not found"
        }), 404

    # --------------------------------------------------------
    # Make sure learner is enrolled in this exam's course
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
    # QUIZ ATTEMPT / SERVER-SIDE TIMER
    # --------------------------------------------------------

    max_attempts = int(quiz.max_attempts or 1)

    # Find the learner's current unfinished attempt.
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

    # Count all attempts, including an unfinished attempt.
    attempt_count = QuizAttempt.query.filter_by(
        quiz_id=quiz.id,
        learner_id=learner.id
    ).count()

    # If there is no active attempt, this is a new attempt.
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

    # --------------------------------------------------------
    # SERVER-CONTROLLED EXPIRY
    # --------------------------------------------------------

    now = datetime.now(timezone.utc)

    started_at = active_attempt.started_at

    # Handle databases that return a naive datetime.
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

    # If an unfinished attempt has already expired,
    # do not allow the learner to continue it.
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

    # --------------------------------------------------------
    # Get the learner's latest attempt
    # --------------------------------------------------------

    attempt = QuizAttempt.query.filter_by(
        quiz_id=quiz.id,
        learner_id=learner.id
    ).order_by(
        QuizAttempt.id.desc()
    ).first()

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
                int(answer.marks_awarded or 0)
                if answer
                else 0
            )
        })

    # --------------------------------------------------------
    # Calculate percentage
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

        course = Course.query.get(
            enrollment.course_id
        )

        result.append({
            "id": enrollment.id,
            "learner_id": enrollment.learner_id,
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
            "course_id": enrollment.course_id,
            "course_title": (
                course.title
                if course
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
            ),
        })

    return jsonify({
        "enrollments": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev,
        },
    })


@api.post("/admin/enrollments")
@role_required("admin")
def admin_create_enrollment(user):
    data = request.get_json(silent=True) or {}

    learner_id = data.get(
        "learner_id"
    )

    course_id = data.get(
        "course_id"
    )

    if not learner_id or not course_id:
        return jsonify({
            "error": "learner_id and course_id are required"
        }), 400

    learner = Learner.query.get(
        learner_id
    )

    if not learner:
        return jsonify({
            "error": "Learner not found"
        }), 404

    course = Course.query.get(
        course_id
    )

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

    enrollment = Enrollment(
        learner_id=learner_id,
        course_id=course_id,
        progress=0,
        status="active"
    )

    db.session.add(enrollment)
    db.session.commit()

    return jsonify({
        "message": "Learner enrolled successfully",
        "enrollment": {
            "id": enrollment.id,
            "learner_id": enrollment.learner_id,
            "course_id": enrollment.course_id,
            "progress": enrollment.progress,
            "status": enrollment.status,
            "enrolled_at": (
                enrollment.enrolled_at.isoformat()
                if enrollment.enrolled_at
                else None
            )
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
        .order_by(
            Batch.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False,
        )
    )

    result = []

    for batch in pagination.items:
        result.append({
            "id": batch.id,
            "name": getattr(
                batch,
                "name",
                None,
            ),
            "status": getattr(
                batch,
                "status",
                None,
            ),
            "created_at": (
                batch.created_at.isoformat()
                if getattr(
                    batch,
                    "created_at",
                    None,
                )
                else None
            ),
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
    })


@api.post("/admin/batches")
@role_required("admin")
def admin_create_batch(user):
    data = request.get_json(silent=True) or {}

    name = str(
        data.get("name", "")
    ).strip()

    if not name:
        return jsonify({
            "error": "Batch name is required"
        }), 400

    batch_data = {
        "name": name
    }

    if hasattr(Batch, "status"):
        batch_data["status"] = data.get(
            "status",
            "active"
        )

    batch = Batch(
        **batch_data
    )

    db.session.add(batch)
    db.session.commit()

    return jsonify({
        "message": "Batch created successfully",
        "batch": {
            "id": batch.id,
            "name": getattr(
                batch,
                "name",
                None
            ),
            "status": getattr(
                batch,
                "status",
                None
            )
        }
    }), 201


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


# ============================================================
# DISCUSSIONS
# ============================================================

@api.get("/courses/<string:course_id>/discussions")
@token_required
def get_course_discussions(
    user,
    course_id
):
    course = Course.query.get(
        course_id
    )

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
        Discussion.query
        .join(
            Lesson,
            Discussion.lesson_id == Lesson.id
        )
        .join(
            Module,
            Lesson.module_id == Module.id
        )
        .filter(
            Module.course_id == course_id
        )
        .order_by(
            Discussion.id.desc()
        )
        .paginate(
            page=page,
            per_page=limit,
            error_out=False
        )
    )

    discussions = pagination.items

    result = []

    for discussion in discussions:
        discussion_user = User.query.get(
            discussion.user_id
        )

        result.append({
            "id": discussion.id,
            "course_id": discussion.course_id,
            "user_id": discussion.user_id,
            "user_name": (
                discussion_user.name
                if discussion_user
                else None
            ),
            "message": getattr(
                discussion,
                "message",
                getattr(
                    discussion,
                    "content",
                    ""
                )
            ),
            "created_at": (
                discussion.created_at.isoformat()
                if getattr(
                    discussion,
                    "created_at",
                    None
                )
                else None
            )
        })

    return jsonify({
        "discussions": result,
        "pagination": {
            "page": pagination.page,
            "limit": pagination.per_page,
            "total": pagination.total,
            "pages": pagination.pages,
            "has_next": pagination.has_next,
            "has_previous": pagination.has_prev
        }
    })


@api.post("/courses/<string:course_id>/discussions")
@token_required
def create_course_discussion(
    user,
    course_id
):
    course = Course.query.get(
        course_id
    )

    if not course:
        return jsonify({
            "error": "Course not found"
        }), 404

    data = request.get_json(silent=True) or {}

    message = data.get(
        "message"
    )

    if message is None:
        message = data.get(
            "content",
            ""
        )

    message = str(
        message
    ).strip()

    if not message:
        return jsonify({
            "error": "Message is required"
        }), 400

    discussion_data = {
        "course_id": course_id,
        "user_id": user.id
    }

    # --------------------------------------------------------
    # Support whichever text field exists in the model.
    # --------------------------------------------------------

    if hasattr(Discussion, "message"):
        discussion_data["message"] = message
    elif hasattr(Discussion, "content"):
        discussion_data["content"] = message
    else:
        return jsonify({
            "error": "Discussion model does not contain a message field"
        }), 500

    discussion = Discussion(
        **discussion_data
    )

    db.session.add(discussion)
    db.session.commit()

    return jsonify({
        "message": "Discussion posted successfully",
        "discussion": {
            "id": discussion.id,
            "course_id": discussion.course_id,
            "user_id": discussion.user_id,
            "user_name": user.name,
            "message": message,
            "created_at": (
                discussion.created_at.isoformat()
                if getattr(
                    discussion,
                    "created_at",
                    None
                )
                else None
            )
        }
    }), 201


# ============================================================
# END OF PART 6
# ============================================================
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
