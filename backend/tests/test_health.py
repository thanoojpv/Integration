from app import db
from datetime import datetime, timedelta, timezone
from app.auth import create_password_hash, make_token
from app.models import (
    Batch,
    Course,
    Certificate,
    Enrollment,
    Learner,
    Lesson,
    LessonProgress,
    LessonResource,
    Module,
    Question,
    Quiz,
    QuizAttempt,
    Trainer,
    User,
)


def test_health(client):
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.get_json()

    assert data["status"] == "ok"


def test_my_learning_requires_authentication(client):
    response = client.get("/api/my-learning")

    assert response.status_code in (401, 403)


def test_my_learning_rejects_wrong_role(client, app):
    with app.app_context():
        user = User(
            name="Test Trainer",
            email="trainer-test@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

    

        token = make_token(user)

    response = client.get(
        "/api/my-learning",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == (
        "You do not have permission for this action"
    )


def test_my_learning_allows_learner(client, app):
    with app.app_context():
        user = User(
            name="Test Learner",
            email="learner-test@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        token = make_token(user)

    response = client.get(
        "/api/my-learning",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["courses"] == []
    assert "pagination" in data
    assert data["pagination"]["total"] == 0


def test_inactive_user_cannot_use_existing_token(client, app):
    with app.app_context():
        user = User(
            name="Suspended Learner",
            email="suspended-test@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        # Create the token while the user is active.
        token = make_token(user)

        # Suspend the user after the token has already been issued.
        user.status = "inactive"
        db.session.commit()

    # Try to use the old token after the account was suspended.
    response = client.get(
        "/api/learner/leaderboard",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == "Your account is inactive"


def test_uploaded_files_require_authentication(client, app):
    response = client.get(
        "/api/files/test-file.pdf"
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"] == (
        "Authorization token is required"
    )


def test_non_enrolled_learner_cannot_access_lesson_file(
    client,
    app,
    tmp_path,
):
    with app.app_context():
        # Create learner user
        user = User(
            name="File Test Learner",
            email="file-test-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)

        # Create trainer
        trainer_user = User(
            name="File Test Trainer",
            email="file-test-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        # Create course
        course = Course(
            id="file-security-course",
            trainer_id=trainer.id,
            title="File Security Test Course",
            level="Beginner",
            description="Security test course",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        # Create module
        module = Module(
            course_id=course.id,
            title="Security Module",
            order_no=1,
        )

        db.session.add(module)
        db.session.commit()

        # Create lesson
        lesson = Lesson(
            id="file-security-lesson",
            module_id=module.id,
            title="Security Test Lesson",
            content="Test lesson",
            order_no=1,
        )

        db.session.add(lesson)
        db.session.commit()

        # Create a real temporary uploaded file
        upload_dir = tmp_path / "uploads" / "pdfs"

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = upload_dir / "secret.pdf"

        file_path.write_bytes(
            b"private course file"
        )

        resource = LessonResource(
            lesson_id=lesson.id,
            resource_type="pdf",
            file_name="secret.pdf",
            file_path=str(file_path),
            title="Secret PDF",
        )

        db.session.add(resource)
        db.session.commit()

        token = make_token(user)

        filename = str(
            file_path.relative_to(
                tmp_path / "uploads"
            )
        )

    # The test application's upload folder must point
    # to the temporary upload directory.
    with app.app_context():
        original_upload_folder = (
            app.config["UPLOAD_FOLDER"]
        )

        app.config["UPLOAD_FOLDER"] = str(
            tmp_path / "uploads"
        )

        try:
            response = client.get(
                f"/api/files/{filename}",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
        finally:
            app.config["UPLOAD_FOLDER"] = (
                original_upload_folder
            )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == (
        "You are not enrolled in this course"
    )


def test_enrolled_learner_can_access_lesson_file(
    client,
    app,
    tmp_path,
):
    with app.app_context():
        # Create learner user
        user = User(
            name="Enrolled File Learner",
            email="enrolled-file-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        # Create trainer user
        trainer_user = User(
            name="File Access Trainer",
            email="file-access-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        # Create course
        course = Course(
            id="enrolled-file-course",
            trainer_id=trainer.id,
            title="Enrolled File Test Course",
            level="Beginner",
            description="File access test course",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        # Create active enrollment
        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        # Create module
        module = Module(
            course_id=course.id,
            title="File Module",
            order_no=1,
        )

        db.session.add(module)
        db.session.commit()

        # Create lesson
        lesson = Lesson(
            id="enrolled-file-lesson",
            module_id=module.id,
            title="File Access Lesson",
            content="Test lesson",
            order_no=1,
        )

        db.session.add(lesson)
        db.session.commit()

        # Create temporary PDF
        upload_dir = tmp_path / "uploads" / "pdfs"

        upload_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        file_path = upload_dir / "course.pdf"

        file_path.write_bytes(
            b"private course content"
        )

        resource = LessonResource(
            lesson_id=lesson.id,
            resource_type="pdf",
            file_name="course.pdf",
            file_path=str(file_path),
            title="Course PDF",
        )

        db.session.add(resource)
        db.session.commit()

        token = make_token(user)

        filename = str(
            file_path.relative_to(
                tmp_path / "uploads"
            )
        )

        original_upload_folder = (
            app.config["UPLOAD_FOLDER"]
        )

        app.config["UPLOAD_FOLDER"] = str(
            tmp_path / "uploads"
        )

        try:
            response = client.get(
                f"/api/files/{filename}",
                headers={
                    "Authorization": f"Bearer {token}",
                },
            )
        finally:
            app.config["UPLOAD_FOLDER"] = (
                original_upload_folder
            )

    assert response.status_code == 200
    assert response.data == (
        b"private course content"
    )


def test_non_enrolled_learner_cannot_update_lesson_progress(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Progress Test Learner",
            email="progress-test-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)

        trainer_user = User(
            name="Progress Test Trainer",
            email="progress-test-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course = Course(
            id="progress-security-course",
            trainer_id=trainer.id,
            title="Progress Security Course",
            level="Beginner",
            description="Progress security test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        module = Module(
            course_id=course.id,
            title="Progress Module",
            order_no=1,
        )

        db.session.add(module)
        db.session.commit()

        lesson = Lesson(
            id="progress-security-lesson",
            module_id=module.id,
            title="Progress Security Lesson",
            content="Test lesson",
            order_no=1,
        )

        db.session.add(lesson)
        db.session.commit()

        token = make_token(user)

        learner_id = learner.id
        lesson_id = lesson.id

    response = client.post(
        "/api/learner/lessons/progress-security-lesson/progress",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "completed": True,
        },
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == (
        "You are not enrolled in this course"
    )

    with app.app_context():
        progress = LessonProgress.query.filter_by(
            learner_id=learner_id,
            lesson_id=lesson_id,
        ).first()

        assert progress is None


def test_quiz_attempt_limit_is_enforced(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Quiz Limit Learner",
            email="quiz-limit-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)

        trainer_user = User(
            name="Quiz Limit Trainer",
            email="quiz-limit-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course = Course(
            id="quiz-limit-course",
            trainer_id=trainer.id,
            title="Quiz Limit Course",
            level="Beginner",
            description="Quiz attempt limit test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        quiz = Quiz(
            course_id=course.id,
            title="Attempt Limit Quiz",
            description="Attempt limit test",
            total_marks=1,
            max_attempts=1,
            duration_minutes=30,
        )

        db.session.add(quiz)
        db.session.commit()

        question = Question(
            quiz_id=quiz.id,
            question_text="What is 2 + 2?",
            option_a="3",
            option_b="4",
            option_c="5",
            option_d="6",
            correct_answer="B",
            marks=1,
        )

        db.session.add(question)
        db.session.commit()

        attempt = QuizAttempt(
            quiz_id=quiz.id,
            learner_id=learner.id,
            score=1,
            total=1,
            attempted_at=datetime.now(timezone.utc),
        )

        db.session.add(attempt)
        db.session.commit()

        token = make_token(user)

        quiz_id = quiz.id
        question_id = question.id

    response = client.post(
        f"/api/learner/exams/{quiz_id}/submit",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "answers": {
                str(question_id): "B",
            }
        },
    )

    assert response.status_code == 403

    data = response.get_json()

    assert data["error"] == (
        "Maximum quiz attempts reached"
    )

    assert data["max_attempts"] == 1
    assert data["attempts_used"] == 1

def test_quiz_submission_completes_existing_attempt(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Quiz Submit Learner",
            email="quiz-submit-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        trainer_user = User(
            name="Quiz Submit Trainer",
            email="quiz-submit-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course = Course(
            id="quiz-submit-course",
            trainer_id=trainer.id,
            title="Quiz Submit Course",
            level="Beginner",
            description="Quiz submission test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        quiz = Quiz(
            course_id=course.id,
            title="Submission Quiz",
            description="Submission test",
            total_marks=1,
            max_attempts=1,
            duration_minutes=30,
        )

        db.session.add(quiz)
        db.session.commit()

        question = Question(
            quiz_id=quiz.id,
            question_text="What is 2 + 2?",
            option_a="3",
            option_b="4",
            option_c="5",
            option_d="6",
            correct_answer="B",
            marks=1,
        )

        db.session.add(question)
        db.session.commit()

        user_id = user.id
        learner_id = learner.id
        quiz_id = quiz.id
        question_id = question.id

        token = make_token(user)

    # Opening the exam starts the server-side attempt.
    response = client.get(
        f"/api/learner/exams/{quiz_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    exam_data = response.get_json()

    assert exam_data["exam"]["attempt_id"] is not None
    assert exam_data["exam"]["duration_minutes"] == 30

    attempt_id = exam_data["exam"]["attempt_id"]

    with app.app_context():
        attempts_before_submit = QuizAttempt.query.filter_by(
            quiz_id=quiz_id,
            learner_id=learner_id,
        ).all()

        assert len(attempts_before_submit) == 1
        assert attempts_before_submit[0].id == attempt_id
        assert attempts_before_submit[0].attempted_at is None

    # Submit the quiz.
    response = client.post(
        f"/api/learner/exams/{quiz_id}/submit",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "answers": {
                str(question_id): "B",
            }
        },
    )

    assert response.status_code == 200

    with app.app_context():
        attempts_after_submit = QuizAttempt.query.filter_by(
            quiz_id=quiz_id,
            learner_id=learner_id,
        ).all()

        # Submission must update the existing attempt,
        # not create a second attempt.
        assert len(attempts_after_submit) == 1

        completed_attempt = attempts_after_submit[0]

        assert completed_attempt.id == attempt_id
        assert completed_attempt.score == 1
        assert completed_attempt.total == 1
        assert completed_attempt.attempted_at is not None

def test_learning_time_rejects_excessive_duration(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Learning Time Learner",
            email="learning-time-limit@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        token = make_token(user)

    response = client.post(
        "/api/learner/learning-time",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "duration_seconds": 3601,
        },
    )

    assert response.status_code == 400
    assert "3600" in response.get_json()["error"]

def test_learning_time_requires_active_enrollment(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Learning Time Enrollment Learner",
            email="learning-time-enrollment@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)

        trainer_user = User(
            name="Learning Time Trainer",
            email="learning-time-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course = Course(
            id="learning-time-course",
            trainer_id=trainer.id,
            title="Learning Time Course",
            level="Beginner",
            description="Learning time enrollment test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        token = make_token(user)
        course_id = course.id

    response = client.post(
        "/api/learner/learning-time",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "course_id": course_id,
            "duration_seconds": 300,
        },
    )

    assert response.status_code == 403
    assert response.get_json()["error"] == (
        "Active course enrollment required"
    )

def test_learning_time_rejects_lesson_from_wrong_course(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Learning Time Lesson Learner",
            email="learning-time-lesson@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)

        trainer_user = User(
            name="Learning Time Lesson Trainer",
            email="learning-time-lesson-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course_one = Course(
            id="learning-time-course-one",
            trainer_id=trainer.id,
            title="Learning Time Course One",
            level="Beginner",
            description="First course",
            published=True,
        )

        course_two = Course(
            id="learning-time-course-two",
            trainer_id=trainer.id,
            title="Learning Time Course Two",
            level="Beginner",
            description="Second course",
            published=True,
        )

        db.session.add_all([
            course_one,
            course_two,
        ])
        db.session.commit()

        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course_one.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        module = Module(
            course_id=course_two.id,
            title="Wrong Course Module",
            order_no=1,
        )

        db.session.add(module)
        db.session.commit()

        lesson = Lesson(
            id="learning-time-lesson-one",
            module_id=module.id,
            title="Wrong Course Lesson",
            order_no=1,
        )

        db.session.add(lesson)
        db.session.commit()
        
        token = make_token(user)

        course_one_id = course_one.id
        lesson_id = lesson.id

    response = client.post(
        "/api/learner/learning-time",
        headers={
            "Authorization": f"Bearer {token}",
        },
        json={
            "course_id": course_one.id,
            "lesson_id": lesson.id,
            "duration_seconds": 300,
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == (
        "Lesson not found for this course"
    )

def test_certificate_verification_uses_secure_id_and_minimal_public_data(
    client,
    app,
):
    with app.app_context():
        user = User(
            name="Certificate Learner",
            email="certificate-test@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

        learner = Learner(
            user_id=user.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        trainer_user = User(
            name="Certificate Trainer",
            email="certificate-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        course = Course(
            id="certificate-security-course",
            trainer_id=trainer.id,
            title="Certificate Security Course",
            level="Beginner",
            description="Certificate security test",
        )

        db.session.add(course)
        db.session.commit()

        now = datetime.now(timezone.utc)

        certificate = Certificate(
            certificate_id="CERT-TestSecureRandomValue123456",
            learner_id=learner.id,
            course_id=course.id,
            start_date=now,
            end_date=now,
            status="valid",
        )

        db.session.add(certificate)
        db.session.commit()

        certificate_id = certificate.certificate_id

        # The certificate ID must not use the old predictable format.
        assert certificate_id != (
            f"CERT-{now.year}-"
            f"{learner.id:04d}-"
            f"{course.id}"
        )

        # The certificate ID must not contain the course ID.
        assert course.id not in certificate_id

    response = client.get(
        f"/api/certificates/{certificate_id}"
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["valid"] is True

    certificate_data = data["certificate"]

    assert certificate_data["certificate_id"] == certificate_id
    assert certificate_data["course_title"] == (
        "Certificate Security Course"
    )

    # Public verification must not expose the learner's name.
    assert "learner_name" not in certificate_data

def test_login_locks_account_after_five_failed_attempts(client, app):
    with app.app_context():
        user = User(
            name="Lockout Test User",
            email="lockout-test@example.com",
            password_hash=create_password_hash(
                "CorrectPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

    login_url = "/api/auth/login"

    # First four failed attempts.
    for _ in range(4):
        response = client.post(
            login_url,
            json={
                "email": "lockout-test@example.com",
                "password": "WrongPassword123!",
            },
        )

        assert response.status_code == 401

    with app.app_context():
        user = User.query.filter_by(
            email="lockout-test@example.com"
        ).first()

        assert user.failed_login_attempts == 4
        assert user.locked_until is None

    # Fifth failed attempt should lock the account.
    response = client.post(
        login_url,
        json={
            "email": "lockout-test@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401

    with app.app_context():
        user = User.query.filter_by(
            email="lockout-test@example.com"
        ).first()

        assert user.failed_login_attempts == 5
        assert user.locked_until is not None


def test_locked_account_rejects_correct_password(client, app):
    with app.app_context():
        user = User(
            name="Already Locked User",
            email="locked-test@example.com",
            password_hash=create_password_hash(
                "CorrectPassword123!"
            ),
            role="learner",
            status="active",
            failed_login_attempts=5,
            locked_until=datetime.now(timezone.utc)
            + timedelta(minutes=15),
        )

        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "locked-test@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 401

    data = response.get_json()

    assert data["error"] == "Invalid email or password"


def test_successful_login_resets_failed_attempts(client, app):
    with app.app_context():
        user = User(
            name="Reset Counter User",
            email="reset-counter@example.com",
            password_hash=create_password_hash(
                "CorrectPassword123!"
            ),
            role="learner",
            status="active",
            failed_login_attempts=3,
        )

        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "reset-counter@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(
            email="reset-counter@example.com"
        ).first()

        assert user.failed_login_attempts == 0
        assert user.locked_until is None


def test_expired_lock_allows_login(client, app):
    with app.app_context():
        user = User(
            name="Expired Lock User",
            email="expired-lock@example.com",
            password_hash=create_password_hash(
                "CorrectPassword123!"
            ),
            role="learner",
            status="active",
            failed_login_attempts=5,
            locked_until=datetime.now(timezone.utc)
            - timedelta(minutes=1),
        )

        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/api/auth/login",
        json={
            "email": "expired-lock@example.com",
            "password": "CorrectPassword123!",
        },
    )

    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(
            email="expired-lock@example.com"
        ).first()

        assert user.failed_login_attempts == 0
        assert user.locked_until is None

def test_login_rate_limit(client, app):
    with app.app_context():
        user = User(
            name="Rate Limit User",
            email="rate-limit@example.com",
            password_hash=create_password_hash(
                "CorrectPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add(user)
        db.session.commit()

    responses = []

    for _ in range(11):
        response = client.post(
            "/api/auth/login",
            json={
                "email": "rate-limit@example.com",
                "password": "WrongPassword123!",
            },
        )

        responses.append(response)

    assert all(
        response.status_code == 401
        for response in responses[:10]
    )

    assert responses[10].status_code == 429

def test_admin_can_add_learner_to_batch(client, app):
    with app.app_context():
        # Admin
        admin_user = User(
            name="Batch Admin",
            email="batch-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        # Trainer
        trainer_user = User(
            name="Batch Trainer",
            email="batch-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        # Learner
        learner_user = User(
            name="Batch Learner",
            email="batch-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        learner = Learner(
            user_id=learner_user.id,
            status="active",
        )

        db.session.add_all([
            trainer,
            learner,
        ])
        db.session.commit()

        course = Course(
            id="batch-test-course",
            trainer_id=trainer.id,
            title="Batch Test Course",
            level="Beginner",
            description="Batch assignment test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        batch = Batch(
            name="Batch Test 1",
            course_id=course.id,
            trainer_id=trainer.id,
            start_date=datetime(2026, 10, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            status="active",
        )

        db.session.add(batch)

        enrollment = Enrollment(
            learner_id=learner.id,
            course_id=course.id,
            status="active",
        )

        db.session.add(enrollment)
        db.session.commit()

        token = make_token(admin_user)

        learner_id = learner.id
        batch_id = batch.id

    response = client.post(
        f"/api/admin/batches/{batch_id}/learners",
        json={
            "learner_id": learner_id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Learner added to batch successfully"
    )

    assert data["learner"]["id"] == learner_id
    assert data["learner"]["batch_id"] == batch_id

    with app.app_context():
        updated_learner = db.session.get(
            Learner,
            learner_id,
        )

        assert updated_learner.batch_id == batch_id


def test_admin_cannot_add_non_enrolled_learner_to_batch(
    client,
    app,
):
    with app.app_context():
        admin_user = User(
            name="Enrollment Admin",
            email="enrollment-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        trainer_user = User(
            name="Enrollment Trainer",
            email="enrollment-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        learner_user = User(
            name="Non Enrolled Learner",
            email="non-enrolled@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        learner = Learner(
            user_id=learner_user.id,
            status="active",
        )

        db.session.add_all([
            trainer,
            learner,
        ])
        db.session.commit()

        course = Course(
            id="non-enrolled-course",
            trainer_id=trainer.id,
            title="Non Enrolled Course",
            level="Beginner",
            description="Test course",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        batch = Batch(
            name="Enrollment Batch",
            course_id=course.id,
            trainer_id=trainer.id,
            status="active",
        )

        db.session.add(batch)
        db.session.commit()

        token = make_token(admin_user)

        batch_id = batch.id
        learner_id = learner.id

    response = client.post(
        f"/api/admin/batches/{batch_id}/learners",
        json={
            "learner_id": learner_id,
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["error"] == (
        "Learner must be actively enrolled in the batch course"
    )


def test_admin_can_view_batch_roster(client, app):
    with app.app_context():
        admin_user = User(
            name="Roster Admin",
            email="roster-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        trainer_user = User(
            name="Roster Trainer",
            email="roster-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        learner_user = User(
            name="Roster Learner",
            email="roster-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        learner = Learner(
            user_id=learner_user.id,
            status="active",
        )

        db.session.add_all([
            trainer,
            learner,
        ])
        db.session.commit()

        course = Course(
            id="roster-test-course",
            trainer_id=trainer.id,
            title="Roster Test Course",
            level="Beginner",
            description="Roster test",
            published=True,
        )

        db.session.add(course)
        db.session.commit()

        batch = Batch(
            name="Roster Batch",
            course_id=course.id,
            trainer_id=trainer.id,
            status="active",
        )

        db.session.add(batch)
        db.session.flush()

        learner.batch_id = batch.id

        db.session.commit()

        token = make_token(admin_user)

        batch_id = batch.id
        learner_id = learner.id

    response = client.get(
        f"/api/admin/batches/{batch_id}/learners",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["id"] == batch_id
    assert data["total"] == 1

    assert data["learners"][0]["id"] == learner_id
    assert data["learners"][0]["name"] == "Roster Learner"

def test_trainer_can_view_batch_attendance(client, app):
    from app import db
    from app.auth import make_token
    from app.models import User, Trainer, Batch, Learner

    trainer_user = User(
    name="Attendance Trainer",
        email="attendance_trainer@example.com",
        password_hash=create_password_hash(
            "password"
        ),
        role="trainer",
        status="active",
    )
    db.session.add(trainer_user)
    db.session.flush()

    trainer = Trainer(
        user_id=trainer_user.id,
        status="active",
    )
    db.session.add(trainer)
    db.session.flush()

    batch = Batch(
        name="Attendance Batch",
        trainer_id=trainer.id,
        status="active",
    )
    db.session.add(batch)
    db.session.flush()

    learner_user = User(
        name="Attendance Learner",
        email="attendance_learner@example.com",
        password_hash=create_password_hash(
            "password"
        ),
        role="learner",
        status="active",
    )
    db.session.add(learner_user)
    db.session.flush()

    learner = Learner(
        user_id=learner_user.id,
        batch_id=batch.id,
        status="active",
    )
    db.session.add(learner)

    db.session.commit()

    token = make_token(trainer_user)

    response = client.get(
        f"/api/trainer/batches/{batch.id}/attendance?date=2026-10-03",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["batch"]["id"] == batch.id
    assert data["batch"]["name"] == "Attendance Batch"
    assert data["date"] == "2026-10-03"
    assert data["total"] == 1

    assert data["learners"][0]["learner_id"] == learner.id
    assert data["learners"][0]["name"] == "Attendance Learner"
    assert data["learners"][0]["status"] is None

def test_trainer_can_mark_batch_attendance(client, app):
    from app import db
    from app.auth import make_token
    from app.models import (
        User,
        Trainer,
        Batch,
        Learner,
        Attendance,
    )

    trainer_user = User(
        name="Attendance Marker",
        email="attendance_marker@example.com",
        password_hash=create_password_hash(
            "password"
        ),
        role="trainer",
        status="active",
    )
    db.session.add(trainer_user)
    db.session.flush()

    trainer = Trainer(
        user_id=trainer_user.id,
        status="active",
    )
    db.session.add(trainer)
    db.session.flush()

    batch = Batch(
        name="Attendance Marking Batch",
        trainer_id=trainer.id,
        status="active",
    )
    db.session.add(batch)
    db.session.flush()

    learner_user_1 = User(
        name="Present Learner",
        email="present_learner@example.com",
        password_hash=create_password_hash(
            "password"
        ),
        role="learner",
        status="active",
    )
    learner_user_2 = User(
        name="Late Learner",
        email="late_learner@example.com",
        password_hash=create_password_hash(
            "password"
        ),
        role="learner",
        status="active",
    )

    db.session.add_all([
        learner_user_1,
        learner_user_2,
    ])
    db.session.flush()

    learner_1 = Learner(
        user_id=learner_user_1.id,
        batch_id=batch.id,
        status="active",
    )
    learner_2 = Learner(
        user_id=learner_user_2.id,
        batch_id=batch.id,
        status="active",
    )

    db.session.add_all([
        learner_1,
        learner_2,
    ])
    db.session.commit()

    token = make_token(trainer_user)

    response = client.post(
        f"/api/trainer/batches/{batch.id}/attendance",
        json={
            "date": "2026-10-03",
            "attendance": [
                {
                    "learner_id": learner_1.id,
                    "status": "present",
                },
                {
                    "learner_id": learner_2.id,
                    "status": "late",
                },
            ],
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Attendance saved successfully"
    )
    assert data["batch_id"] == batch.id
    assert data["date"] == "2026-10-03"
    assert len(data["attendance"]) == 2

    record_1 = Attendance.query.filter_by(
        learner_id=learner_1.id,
        batch_id=batch.id,
        date="2026-10-03",
    ).first()

    record_2 = Attendance.query.filter_by(
        learner_id=learner_2.id,
        batch_id=batch.id,
        date="2026-10-03",
    ).first()

    assert record_1 is not None
    assert record_1.status == "present"
    assert record_1.marked_by == trainer_user.id

    assert record_2 is not None
    assert record_2.status == "late"
    assert record_2.marked_by == trainer_user.id

def test_trainer_cannot_mark_attendance_for_another_trainers_batch(
    client,
    app,
):
    from app import db
    from app.auth import make_token
    from app.models import User, Trainer, Batch, Learner

    trainer_user_1 = User(
        name="Trainer One",
        email="trainer_one_attendance@example.com",
        password_hash=create_password_hash("password"),
        role="trainer",
        status="active",
    )

    trainer_user_2 = User(
        name="Trainer Two",
        email="trainer_two_attendance@example.com",
        password_hash=create_password_hash("password"),
        role="trainer",
        status="active",
    )

    db.session.add_all([
        trainer_user_1,
        trainer_user_2,
    ])
    db.session.flush()

    trainer_1 = Trainer(
        user_id=trainer_user_1.id,
        status="active",
    )

    trainer_2 = Trainer(
        user_id=trainer_user_2.id,
        status="active",
    )

    db.session.add_all([
        trainer_1,
        trainer_2,
    ])
    db.session.flush()

    batch = Batch(
        name="Trainer Two Batch",
        trainer_id=trainer_2.id,
        status="active",
    )

    db.session.add(batch)
    db.session.flush()

    learner_user = User(
        name="Protected Learner",
        email="protected_learner@example.com",
        password_hash=create_password_hash("password"),
        role="learner",
        status="active",
    )

    db.session.add(learner_user)
    db.session.flush()

    learner = Learner(
        user_id=learner_user.id,
        batch_id=batch.id,
        status="active",
    )

    db.session.add(learner)
    db.session.commit()

    token = make_token(trainer_user_1)

    response = client.post(
        f"/api/trainer/batches/{batch.id}/attendance",
        json={
            "date": "2026-10-03",
            "attendance": [
                {
                    "learner_id": learner.id,
                    "status": "present",
                }
            ],
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 404
    assert response.get_json()["error"] == "Batch not found"

def test_admin_can_view_attendance_and_summary(client, app):
    from app.models import Attendance
    with app.app_context():
        admin_user = User(
            name="Attendance Admin",
            email="attendance-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        trainer_user = User(
            name="Attendance Trainer Admin Test",
            email="attendance-trainer-admin-test@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        learner_user = User(
            name="Attendance Summary Learner",
            email="attendance-summary-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        batch = Batch(
            name="Attendance Admin Batch",
            trainer_id=trainer.id,
            start_date=datetime(2026, 10, 1).date(),
            end_date=datetime(2026, 12, 31).date(),
            status="active",
        )

        db.session.add(batch)
        db.session.commit()

        learner = Learner(
            user_id=learner_user.id,
            batch_id=batch.id,
            status="active",
        )

        db.session.add(learner)
        db.session.commit()

        attendance_records = [
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 1).date(),
                status="present",
                marked_by=trainer_user.id,
            ),
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 2).date(),
                status="late",
                marked_by=trainer_user.id,
            ),
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 3).date(),
                status="absent",
                marked_by=trainer_user.id,
            ),
        ]

        db.session.add_all(attendance_records)
        db.session.commit()

        token = make_token(admin_user)

        batch_id = batch.id
        learner_id = learner.id

    response = client.get(
        f"/api/admin/attendance?batch_id={batch_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["pagination"]["total"] == 3
    assert len(data["attendance"]) == 3

    response = client.get(
        f"/api/admin/attendance/summary?batch_id={batch_id}",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["total"] == 1

    summary = data["learners"][0]

    assert summary["learner_id"] == learner_id
    assert summary["total"] == 3
    assert summary["present"] == 1
    assert summary["late"] == 1
    assert summary["absent"] == 1
    assert summary["attendance_percentage"] == 66.67

def test_admin_can_edit_attendance(client, app):
    from app.models import Attendance

    with app.app_context():
        admin_user = User(
            name="Attendance Edit Admin",
            email="attendance-edit-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        trainer_user = User(
            name="Attendance Edit Trainer",
            email="attendance-edit-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        learner_user = User(
            name="Attendance Edit Learner",
            email="attendance-edit-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )
        db.session.add(trainer)
        db.session.commit()

        batch = Batch(
            name="Attendance Edit Batch",
            trainer_id=trainer.id,
            status="active",
        )
        db.session.add(batch)
        db.session.commit()

        learner = Learner(
            user_id=learner_user.id,
            batch_id=batch.id,
            status="active",
        )
        db.session.add(learner)
        db.session.commit()

        attendance = Attendance(
            learner_id=learner.id,
            batch_id=batch.id,
            date=datetime(2026, 10, 3).date(),
            status="present",
            marked_by=trainer_user.id,
        )

        db.session.add(attendance)
        db.session.commit()

        attendance_id = attendance.id

        token = make_token(admin_user)

    response = client.put(
        f"/api/admin/attendance/{attendance_id}",
        json={
            "status": "absent",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Attendance updated successfully"
    )

    assert data["attendance"]["id"] == attendance_id
    assert data["attendance"]["status"] == "absent"
    assert data["attendance"]["marked_by"] == admin_user.id

    with app.app_context():
        updated = db.session.get(
            Attendance,
            attendance_id,
        )

        assert updated is not None
        assert updated.status == "absent"
        assert updated.marked_by == admin_user.id

def test_admin_can_edit_attendance(client, app):
    from app.models import Attendance

    with app.app_context():
        admin_user = User(
            name="Attendance Edit Admin",
            email="attendance-edit-admin@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="admin",
            status="active",
        )

        trainer_user = User(
            name="Attendance Edit Trainer",
            email="attendance-edit-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        learner_user = User(
            name="Attendance Edit Learner",
            email="attendance-edit-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        db.session.add_all([
            admin_user,
            trainer_user,
            learner_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )
        db.session.add(trainer)
        db.session.commit()

        batch = Batch(
            name="Attendance Edit Batch",
            trainer_id=trainer.id,
            status="active",
        )
        db.session.add(batch)
        db.session.commit()

        learner = Learner(
            user_id=learner_user.id,
            batch_id=batch.id,
            status="active",
        )
        db.session.add(learner)
        db.session.commit()

        attendance = Attendance(
            learner_id=learner.id,
            batch_id=batch.id,
            date=datetime(2026, 10, 3).date(),
            status="present",
            marked_by=trainer_user.id,
        )

        db.session.add(attendance)
        db.session.commit()

        attendance_id = attendance.id

        token = make_token(admin_user)

    response = client.put(
        f"/api/admin/attendance/{attendance_id}",
        json={
            "status": "absent",
        },
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["message"] == (
        "Attendance updated successfully"
    )

    assert data["attendance"]["id"] == attendance_id
    assert data["attendance"]["status"] == "absent"
    assert data["attendance"]["marked_by"] == admin_user.id

    with app.app_context():
        updated = db.session.get(
            Attendance,
            attendance_id,
        )

        assert updated is not None
        assert updated.status == "absent"
        assert updated.marked_by == admin_user.id

def test_learner_can_view_own_attendance_history(client, app):
    from app.models import Attendance

    with app.app_context():
        learner_user = User(
            name="Attendance History Learner",
            email="attendance-history-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        other_learner_user = User(
            name="Other Attendance Learner",
            email="other-attendance-learner@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="learner",
            status="active",
        )

        trainer_user = User(
            name="Attendance History Trainer",
            email="attendance-history-trainer@example.com",
            password_hash=create_password_hash(
                "TestPassword123!"
            ),
            role="trainer",
            status="active",
        )

        db.session.add_all([
            learner_user,
            other_learner_user,
            trainer_user,
        ])
        db.session.commit()

        trainer = Trainer(
            user_id=trainer_user.id,
            status="active",
        )

        db.session.add(trainer)
        db.session.commit()

        batch = Batch(
            name="Attendance History Batch",
            trainer_id=trainer.id,
            status="active",
        )

        other_batch = Batch(
            name="Other Attendance Batch",
            trainer_id=trainer.id,
            status="active",
        )

        db.session.add_all([
            batch,
            other_batch,
        ])
        db.session.commit()

        learner = Learner(
            user_id=learner_user.id,
            batch_id=batch.id,
            status="active",
        )

        other_learner = Learner(
            user_id=other_learner_user.id,
            batch_id=other_batch.id,
            status="active",
        )

        db.session.add_all([
            learner,
            other_learner,
        ])
        db.session.commit()

        db.session.add_all([
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 1).date(),
                status="present",
                marked_by=trainer_user.id,
            ),
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 2).date(),
                status="late",
                marked_by=trainer_user.id,
            ),
            Attendance(
                learner_id=learner.id,
                batch_id=batch.id,
                date=datetime(2026, 10, 3).date(),
                status="absent",
                marked_by=trainer_user.id,
            ),
            Attendance(
                learner_id=other_learner.id,
                batch_id=other_batch.id,
                date=datetime(2026, 10, 4).date(),
                status="present",
                marked_by=trainer_user.id,
            ),
        ])

        db.session.commit()

        learner_id = learner.id
        other_learner_id = other_learner.id

        token = make_token(learner_user)

    response = client.get(
        "/api/learner/attendance",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["summary"]["total"] == 3
    assert data["summary"]["present"] == 1
    assert data["summary"]["late"] == 1
    assert data["summary"]["absent"] == 1
    assert data["summary"]["attendance_percentage"] == 66.67

    assert len(data["history"]) == 3

    returned_ids = {
        record["id"]
        for record in data["history"]
    }

    with app.app_context():
        own_ids = {
            record.id
            for record in Attendance.query.filter_by(
                learner_id=learner_id
            ).all()
        }

        other_ids = {
            record.id
            for record in Attendance.query.filter_by(
                learner_id=other_learner_id
            ).all()
        }

    assert returned_ids == own_ids
    assert returned_ids.isdisjoint(other_ids)