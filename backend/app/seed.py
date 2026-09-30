import logging
from datetime import date

from . import db
from .models import (
    User,
    Trainer,
    Learner,
    Batch,
    Course,
    Module,
    Lesson,
    Enrollment,
    Assignment,
    Quiz,
    Question,
    Certificate,
    Attendance,
    Payment,
    Invoice,
)
from .auth import create_password_hash

logger = logging.getLogger(__name__)


def seed_database():

    # =========================================================
    # 1. ADMIN
    # =========================================================

    admin = User.query.filter_by(
        email="admin@devsprint.com"
    ).first()

    if not admin:
        admin = User(
            name="DevSprint HR Admin",
            email="admin@devsprint.com",
            mobile="9876543210",
            password_hash=create_password_hash("password123"),
            role="admin",
            status="active",
        )

        db.session.add(admin)
        db.session.flush()


    # =========================================================
    # 2. TRAINER USER
    # =========================================================

    trainer_user = User.query.filter_by(
        email="trainer@devsprint.com"
    ).first()

    if not trainer_user:
        trainer_user = User(
            name="DevSprint Trainer",
            email="trainer@devsprint.com",
            mobile="9876543211",
            password_hash=create_password_hash("password123"),
            role="trainer",
            status="active",
        )

        db.session.add(trainer_user)
        db.session.flush()


    trainer = Trainer.query.filter_by(
        user_id=trainer_user.id
    ).first()

    if not trainer:
        trainer = Trainer(
            user_id=trainer_user.id,
            specialization="Full Stack Development",
            experience=5,
            bio="Experienced trainer in Python, React, Node.js and REST APIs.",
            status="active",
        )

        db.session.add(trainer)
        db.session.flush()


    # =========================================================
    # 3. BATCH
    # =========================================================

    batch = Batch.query.filter_by(
        name="DevSprint Batch 2026"
    ).first()

    if not batch:
        batch = Batch(
            name="DevSprint Batch 2026",
            start_date=date(2026, 1, 10),
            end_date=date(2026, 12, 31),
            trainer_id=trainer.id,
            status="active",
        )

        db.session.add(batch)
        db.session.flush()


    # =========================================================
    # 4. LEARNER USER
    # =========================================================

    learner_user = User.query.filter_by(
        email="learner@devsprint.com"
    ).first()

    if not learner_user:
        learner_user = User(
            name="Sabeel Syed",
            email="learner@devsprint.com",
            mobile="9876543212",
            password_hash=create_password_hash("password123"),
            role="learner",
            status="active",
        )

        db.session.add(learner_user)
        db.session.flush()


    learner = Learner.query.filter_by(
        user_id=learner_user.id
    ).first()

    if not learner:
        learner = Learner(
            user_id=learner_user.id,
            batch_id=batch.id,
            education="B.Tech Computer Science",
            status="active",
        )

        db.session.add(learner)
        db.session.flush()


    # =========================================================
    # 5. COURSES
    # =========================================================

    courses_data = [

        # -----------------------------------------------------
        # 1. JAVA FUNDAMENTALS
        # -----------------------------------------------------

        {
            "id": "course-001",
            "title": "Java Fundamentals",
            "level": "Beginner",
            "description": "Learn Java programming from the basics and build a strong foundation in object-oriented programming.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Java Basics",
                    "lessons": [
                        {
                            "id": "les-101",
                            "title": "Introduction to Java",
                            "duration": "10:00",
                            "content": "Learn what Java is, where it is used, and how Java programs work."
                        },
                        {
                            "id": "les-102",
                            "title": "Variables and Data Types",
                            "duration": "15:00",
                            "content": "Learn Java variables, primitive data types, and type conversion."
                        },
                        {
                            "id": "les-103",
                            "title": "Operators",
                            "duration": "12:00",
                            "content": "Learn arithmetic, relational, logical, and assignment operators."
                        },
                    ],
                },
                {
                    "title": "Control Flow",
                    "lessons": [
                        {
                            "id": "les-104",
                            "title": "If Else Statements",
                            "duration": "14:00",
                            "content": "Learn how to make decisions using if, else if, and else."
                        },
                        {
                            "id": "les-105",
                            "title": "Loops",
                            "duration": "18:00",
                            "content": "Learn for, while, and do-while loops."
                        },
                        {
                            "id": "les-106",
                            "title": "Methods",
                            "duration": "16:00",
                            "content": "Learn how to create and use methods in Java."
                        },
                    ],
                },
                {
                    "title": "Object Oriented Programming",
                    "lessons": [
                        {
                            "id": "les-107",
                            "title": "Classes and Objects",
                            "duration": "20:00",
                            "content": "Understand classes, objects, constructors, and instance variables."
                        },
                        {
                            "id": "les-108",
                            "title": "Inheritance",
                            "duration": "18:00",
                            "content": "Learn how inheritance works in Java."
                        },
                        {
                            "id": "les-109",
                            "title": "Polymorphism",
                            "duration": "20:00",
                            "content": "Learn method overloading and method overriding."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 2. PYTHON
        # -----------------------------------------------------

        {
            "id": "course-python",
            "title": "Python Programming",
            "level": "Beginner",
            "description": "Learn Python programming from the basics through practical examples and mini projects.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Python Basics",
                    "lessons": [
                        {
                            "id": "py-101",
                            "title": "Introduction to Python",
                            "duration": "10:00",
                            "content": "Learn Python, its features, and common applications."
                        },
                        {
                            "id": "py-102",
                            "title": "Variables and Data Types",
                            "duration": "15:00",
                            "content": "Learn strings, numbers, booleans, and variables."
                        },
                        {
                            "id": "py-103",
                            "title": "Python Operators",
                            "duration": "12:00",
                            "content": "Learn arithmetic, comparison, logical, and assignment operators."
                        },
                    ],
                },
                {
                    "title": "Control Flow",
                    "lessons": [
                        {
                            "id": "py-104",
                            "title": "Conditional Statements",
                            "duration": "15:00",
                            "content": "Learn if, elif, and else statements."
                        },
                        {
                            "id": "py-105",
                            "title": "Loops in Python",
                            "duration": "18:00",
                            "content": "Learn for and while loops."
                        },
                        {
                            "id": "py-106",
                            "title": "Functions",
                            "duration": "20:00",
                            "content": "Learn how to define and call Python functions."
                        },
                    ],
                },
                {
                    "title": "Python Projects",
                    "lessons": [
                        {
                            "id": "py-107",
                            "title": "Working with Files",
                            "duration": "18:00",
                            "content": "Learn how to read and write files using Python."
                        },
                        {
                            "id": "py-108",
                            "title": "Exception Handling",
                            "duration": "15:00",
                            "content": "Learn how to handle errors using try and except."
                        },
                        {
                            "id": "py-109",
                            "title": "Mini Python Project",
                            "duration": "30:00",
                            "content": "Build a small practical Python application."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 3. WEB DEVELOPMENT
        # -----------------------------------------------------

        {
            "id": "course-web",
            "title": "Web Development",
            "level": "Beginner",
            "description": "Learn the fundamentals of modern web development using HTML, CSS, and JavaScript.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "HTML",
                    "lessons": [
                        {
                            "id": "web-101",
                            "title": "Introduction to HTML",
                            "duration": "12:00",
                            "content": "Learn the structure of HTML documents."
                        },
                        {
                            "id": "web-102",
                            "title": "HTML Elements",
                            "duration": "15:00",
                            "content": "Learn headings, paragraphs, links, images, and lists."
                        },
                        {
                            "id": "web-103",
                            "title": "HTML Forms",
                            "duration": "18:00",
                            "content": "Learn how to create forms and form controls."
                        },
                    ],
                },
                {
                    "title": "CSS",
                    "lessons": [
                        {
                            "id": "web-104",
                            "title": "CSS Basics",
                            "duration": "15:00",
                            "content": "Learn selectors, properties, and CSS rules."
                        },
                        {
                            "id": "web-105",
                            "title": "Flexbox",
                            "duration": "20:00",
                            "content": "Learn responsive layouts using Flexbox."
                        },
                        {
                            "id": "web-106",
                            "title": "CSS Grid",
                            "duration": "20:00",
                            "content": "Learn two-dimensional layouts using CSS Grid."
                        },
                    ],
                },
                {
                    "title": "JavaScript Basics",
                    "lessons": [
                        {
                            "id": "web-107",
                            "title": "JavaScript Introduction",
                            "duration": "15:00",
                            "content": "Learn the basics of JavaScript."
                        },
                        {
                            "id": "web-108",
                            "title": "DOM Manipulation",
                            "duration": "20:00",
                            "content": "Learn how JavaScript interacts with HTML."
                        },
                        {
                            "id": "web-109",
                            "title": "Web Project",
                            "duration": "30:00",
                            "content": "Build a small interactive web application."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 4. REACT
        # -----------------------------------------------------

        {
            "id": "course-react",
            "title": "React.js Development",
            "level": "Intermediate",
            "description": "Build modern interactive web applications using React, components, hooks, and routing.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "React Fundamentals",
                    "lessons": [
                        {
                            "id": "react-101",
                            "title": "Introduction to React",
                            "duration": "15:00",
                            "content": "Understand React and component-based development."
                        },
                        {
                            "id": "react-102",
                            "title": "Components and Props",
                            "duration": "20:00",
                            "content": "Learn React components and props."
                        },
                        {
                            "id": "react-103",
                            "title": "JSX",
                            "duration": "15:00",
                            "content": "Learn JSX syntax and expressions."
                        },
                    ],
                },
                {
                    "title": "React Hooks",
                    "lessons": [
                        {
                            "id": "react-104",
                            "title": "useState",
                            "duration": "20:00",
                            "content": "Learn state management with useState."
                        },
                        {
                            "id": "react-105",
                            "title": "useEffect",
                            "duration": "20:00",
                            "content": "Learn side effects and API calls using useEffect."
                        },
                        {
                            "id": "react-106",
                            "title": "Custom Hooks",
                            "duration": "18:00",
                            "content": "Learn how to create reusable custom hooks."
                        },
                    ],
                },
                {
                    "title": "React Applications",
                    "lessons": [
                        {
                            "id": "react-107",
                            "title": "React Router",
                            "duration": "20:00",
                            "content": "Learn client-side routing with React Router."
                        },
                        {
                            "id": "react-108",
                            "title": "API Integration",
                            "duration": "25:00",
                            "content": "Connect React applications to REST APIs."
                        },
                        {
                            "id": "react-109",
                            "title": "React Project",
                            "duration": "35:00",
                            "content": "Build a complete React application."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 5. NODE.JS
        # -----------------------------------------------------

        {
            "id": "course-node",
            "title": "Node.js & Express",
            "level": "Intermediate",
            "description": "Learn backend development using Node.js, Express, REST APIs, and authentication.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Node.js Basics",
                    "lessons": [
                        {
                            "id": "node-101",
                            "title": "Introduction to Node.js",
                            "duration": "15:00",
                            "content": "Learn Node.js and server-side JavaScript."
                        },
                        {
                            "id": "node-102",
                            "title": "Modules",
                            "duration": "18:00",
                            "content": "Learn CommonJS and Node.js modules."
                        },
                        {
                            "id": "node-103",
                            "title": "NPM",
                            "duration": "15:00",
                            "content": "Learn package management using npm."
                        },
                    ],
                },
                {
                    "title": "Express",
                    "lessons": [
                        {
                            "id": "node-104",
                            "title": "Express Basics",
                            "duration": "18:00",
                            "content": "Create web servers using Express."
                        },
                        {
                            "id": "node-105",
                            "title": "REST APIs",
                            "duration": "25:00",
                            "content": "Build RESTful API endpoints."
                        },
                        {
                            "id": "node-106",
                            "title": "Middleware",
                            "duration": "20:00",
                            "content": "Understand Express middleware."
                        },
                    ],
                },
                {
                    "title": "Authentication",
                    "lessons": [
                        {
                            "id": "node-107",
                            "title": "JWT Authentication",
                            "duration": "25:00",
                            "content": "Implement JWT based authentication."
                        },
                        {
                            "id": "node-108",
                            "title": "API Security",
                            "duration": "20:00",
                            "content": "Learn common API security practices."
                        },
                        {
                            "id": "node-109",
                            "title": "Backend Project",
                            "duration": "35:00",
                            "content": "Build a complete Express backend."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 6. MYSQL
        # -----------------------------------------------------

        {
            "id": "course-mysql",
            "title": "MySQL Database",
            "level": "Beginner",
            "description": "Learn relational databases, SQL queries, joins, and database design using MySQL.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Database Basics",
                    "lessons": [
                        {
                            "id": "mysql-101",
                            "title": "Introduction to Databases",
                            "duration": "12:00",
                            "content": "Learn relational databases and database concepts."
                        },
                        {
                            "id": "mysql-102",
                            "title": "Tables and Records",
                            "duration": "15:00",
                            "content": "Learn how tables and records are structured."
                        },
                        {
                            "id": "mysql-103",
                            "title": "Creating Databases",
                            "duration": "15:00",
                            "content": "Learn CREATE DATABASE and CREATE TABLE."
                        },
                    ],
                },
                {
                    "title": "SQL Queries",
                    "lessons": [
                        {
                            "id": "mysql-104",
                            "title": "SELECT Queries",
                            "duration": "18:00",
                            "content": "Learn how to retrieve data using SELECT."
                        },
                        {
                            "id": "mysql-105",
                            "title": "INSERT UPDATE DELETE",
                            "duration": "20:00",
                            "content": "Learn how to modify database records."
                        },
                        {
                            "id": "mysql-106",
                            "title": "Filtering and Sorting",
                            "duration": "18:00",
                            "content": "Learn WHERE, ORDER BY, and LIMIT."
                        },
                    ],
                },
                {
                    "title": "Advanced SQL",
                    "lessons": [
                        {
                            "id": "mysql-107",
                            "title": "Joins",
                            "duration": "25:00",
                            "content": "Learn INNER JOIN, LEFT JOIN, and related joins."
                        },
                        {
                            "id": "mysql-108",
                            "title": "Indexes",
                            "duration": "20:00",
                            "content": "Understand database indexes and performance."
                        },
                        {
                            "id": "mysql-109",
                            "title": "Database Project",
                            "duration": "30:00",
                            "content": "Design a small relational database."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 7. DATA SCIENCE
        # -----------------------------------------------------

        {
            "id": "course-datascience",
            "title": "Data Science with Python",
            "level": "Intermediate",
            "description": "Learn data analysis, visualization, and practical data science using Python.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Data Science Basics",
                    "lessons": [
                        {
                            "id": "ds-101",
                            "title": "Introduction to Data Science",
                            "duration": "15:00",
                            "content": "Learn what data science is and how it is used."
                        },
                        {
                            "id": "ds-102",
                            "title": "NumPy",
                            "duration": "20:00",
                            "content": "Learn numerical computing using NumPy."
                        },
                        {
                            "id": "ds-103",
                            "title": "Pandas",
                            "duration": "25:00",
                            "content": "Learn data manipulation using Pandas."
                        },
                    ],
                },
                {
                    "title": "Data Visualization",
                    "lessons": [
                        {
                            "id": "ds-104",
                            "title": "Matplotlib",
                            "duration": "20:00",
                            "content": "Create charts and visualizations using Matplotlib."
                        },
                        {
                            "id": "ds-105",
                            "title": "Data Cleaning",
                            "duration": "25:00",
                            "content": "Learn techniques for cleaning datasets."
                        },
                        {
                            "id": "ds-106",
                            "title": "Exploratory Data Analysis",
                            "duration": "30:00",
                            "content": "Perform exploratory analysis on real datasets."
                        },
                    ],
                },
                {
                    "title": "Data Science Project",
                    "lessons": [
                        {
                            "id": "ds-107",
                            "title": "Working with CSV Data",
                            "duration": "20:00",
                            "content": "Load and analyze CSV datasets."
                        },
                        {
                            "id": "ds-108",
                            "title": "Building Visual Reports",
                            "duration": "25:00",
                            "content": "Create meaningful visual reports."
                        },
                        {
                            "id": "ds-109",
                            "title": "Data Science Project",
                            "duration": "40:00",
                            "content": "Complete a practical data science project."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 8. MACHINE LEARNING
        # -----------------------------------------------------

        {
            "id": "course-ml",
            "title": "Machine Learning",
            "level": "Advanced",
            "description": "Learn machine learning fundamentals, algorithms, model evaluation, and practical projects.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "ML Fundamentals",
                    "lessons": [
                        {
                            "id": "ml-101",
                            "title": "Introduction to Machine Learning",
                            "duration": "20:00",
                            "content": "Understand machine learning and its applications."
                        },
                        {
                            "id": "ml-102",
                            "title": "Training Data",
                            "duration": "20:00",
                            "content": "Learn about datasets, features, and labels."
                        },
                        {
                            "id": "ml-103",
                            "title": "Model Evaluation",
                            "duration": "25:00",
                            "content": "Learn accuracy, precision, recall, and other metrics."
                        },
                    ],
                },
                {
                    "title": "ML Algorithms",
                    "lessons": [
                        {
                            "id": "ml-104",
                            "title": "Linear Regression",
                            "duration": "25:00",
                            "content": "Learn the basics of linear regression."
                        },
                        {
                            "id": "ml-105",
                            "title": "Decision Trees",
                            "duration": "25:00",
                            "content": "Understand decision tree models."
                        },
                        {
                            "id": "ml-106",
                            "title": "K-Means Clustering",
                            "duration": "25:00",
                            "content": "Learn basic unsupervised clustering."
                        },
                    ],
                },
                {
                    "title": "ML Project",
                    "lessons": [
                        {
                            "id": "ml-107",
                            "title": "Data Preprocessing",
                            "duration": "25:00",
                            "content": "Prepare data for machine learning models."
                        },
                        {
                            "id": "ml-108",
                            "title": "Model Training",
                            "duration": "30:00",
                            "content": "Train and evaluate a machine learning model."
                        },
                        {
                            "id": "ml-109",
                            "title": "Machine Learning Project",
                            "duration": "45:00",
                            "content": "Build a practical machine learning application."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 9. ADVANCED JAVASCRIPT
        # -----------------------------------------------------

        {
            "id": "course-js",
            "title": "Advanced JavaScript",
            "level": "Intermediate",
            "description": "Master modern JavaScript concepts including ES6, asynchronous programming, and advanced functions.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Modern JavaScript",
                    "lessons": [
                        {
                            "id": "js-101",
                            "title": "ES6 Features",
                            "duration": "20:00",
                            "content": "Learn let, const, arrow functions, and template literals."
                        },
                        {
                            "id": "js-102",
                            "title": "Destructuring",
                            "duration": "15:00",
                            "content": "Learn object and array destructuring."
                        },
                        {
                            "id": "js-103",
                            "title": "Spread and Rest",
                            "duration": "15:00",
                            "content": "Understand spread and rest operators."
                        },
                    ],
                },
                {
                    "title": "Advanced Functions",
                    "lessons": [
                        {
                            "id": "js-104",
                            "title": "Callbacks",
                            "duration": "18:00",
                            "content": "Understand callback functions."
                        },
                        {
                            "id": "js-105",
                            "title": "Promises",
                            "duration": "20:00",
                            "content": "Learn JavaScript promises."
                        },
                        {
                            "id": "js-106",
                            "title": "Async Await",
                            "duration": "20:00",
                            "content": "Learn asynchronous programming using async and await."
                        },
                    ],
                },
                {
                    "title": "JavaScript Applications",
                    "lessons": [
                        {
                            "id": "js-107",
                            "title": "Fetch API",
                            "duration": "20:00",
                            "content": "Learn how to communicate with APIs."
                        },
                        {
                            "id": "js-108",
                            "title": "Local Storage",
                            "duration": "15:00",
                            "content": "Learn browser local storage."
                        },
                        {
                            "id": "js-109",
                            "title": "JavaScript Project",
                            "duration": "35:00",
                            "content": "Build a practical JavaScript application."
                        },
                    ],
                },
            ],
        },


        # -----------------------------------------------------
        # 10. GIT AND GITHUB
        # -----------------------------------------------------

        {
            "id": "course-git",
            "title": "Git & GitHub",
            "level": "Beginner",
            "description": "Learn version control with Git and collaborate on software projects using GitHub.",
            "thumbnail": "",
            "modules": [
                {
                    "title": "Git Basics",
                    "lessons": [
                        {
                            "id": "git-101",
                            "title": "Introduction to Git",
                            "duration": "12:00",
                            "content": "Learn what Git is and why version control is important."
                        },
                        {
                            "id": "git-102",
                            "title": "Git Repository",
                            "duration": "15:00",
                            "content": "Learn how to create and manage Git repositories."
                        },
                        {
                            "id": "git-103",
                            "title": "Git Add Commit",
                            "duration": "15:00",
                            "content": "Learn how to stage and commit changes."
                        },
                    ],
                },
                {
                    "title": "Git Branching",
                    "lessons": [
                        {
                            "id": "git-104",
                            "title": "Branches",
                            "duration": "18:00",
                            "content": "Learn how to create and work with branches."
                        },
                        {
                            "id": "git-105",
                            "title": "Merge",
                            "duration": "18:00",
                            "content": "Learn how to merge branches."
                        },
                        {
                            "id": "git-106",
                            "title": "Merge Conflicts",
                            "duration": "20:00",
                            "content": "Learn how to resolve merge conflicts."
                        },
                    ],
                },
                {
                    "title": "GitHub",
                    "lessons": [
                        {
                            "id": "git-107",
                            "title": "GitHub Repositories",
                            "duration": "15:00",
                            "content": "Learn how to create and manage GitHub repositories."
                        },
                        {
                            "id": "git-108",
                            "title": "Push and Pull",
                            "duration": "18:00",
                            "content": "Learn how to push and pull code from GitHub."
                        },
                        {
                            "id": "git-109",
                            "title": "Team Collaboration",
                            "duration": "25:00",
                            "content": "Learn how developers collaborate using GitHub."
                        },
                    ],
                },
            ],
        },
    ]


    # =========================================================
    # CREATE COURSES + MODULES + LESSONS
    # =========================================================

    for course_data in courses_data:

        course = Course.query.filter_by(
            id=course_data["id"]
        ).first()

        if not course:

            course = Course(
                id=course_data["id"],
                trainer_id=trainer.id,
                title=course_data["title"],
                level=course_data["level"],
                description=course_data["description"],
                thumbnail=course_data["thumbnail"],
                published=True,
            )

            db.session.add(course)
            db.session.flush()

        else:

            # Keep existing course but update basic information
            course.trainer_id = trainer.id
            course.title = course_data["title"]
            course.level = course_data["level"]
            course.description = course_data["description"]
            course.thumbnail = course_data["thumbnail"]
            course.published = True

        # -----------------------------------------------------
        # MODULES
        # -----------------------------------------------------

        for module_index, module_data in enumerate(
            course_data["modules"],
            start=1
        ):

            module = Module.query.filter_by(
                course_id=course.id,
                order_no=module_index
            ).first()

            if not module:

                module = Module(
                    course_id=course.id,
                    title=module_data["title"],
                    order_no=module_index,
                )

                db.session.add(module)
                db.session.flush()

            else:

                module.title = module_data["title"]

            # -------------------------------------------------
            # LESSONS
            # -------------------------------------------------

            for lesson_index, lesson_data in enumerate(
                module_data["lessons"],
                start=1
            ):

                lesson = Lesson.query.filter_by(
                    id=lesson_data["id"]
                ).first()

                if not lesson:

                    lesson = Lesson(
                        id=lesson_data["id"],
                        module_id=module.id,
                        title=lesson_data["title"],
                        content=lesson_data["content"],
                        video_url="",
                        duration=lesson_data["duration"],
                        order_no=lesson_index,
                    )

                    db.session.add(lesson)

                else:

                    lesson.module_id = module.id
                    lesson.title = lesson_data["title"]
                    lesson.content = lesson_data["content"]
                    lesson.duration = lesson_data["duration"]
                    lesson.order_no = lesson_index


    db.session.flush()


    # =========================================================
    # 6. ENROLL LEARNER IN JAVA FUNDAMENTALS
    # =========================================================

    java_course = Course.query.filter_by(
        id="course-001"
    ).first()

    if java_course:

        enrollment = Enrollment.query.filter_by(
            learner_id=learner.id,
            course_id=java_course.id
        ).first()

        if not enrollment:

            enrollment = Enrollment(
                learner_id=learner.id,
                course_id=java_course.id,
                progress=0,
                status="active",
            )

            db.session.add(enrollment)


    # =========================================================
    # 7. ATTENDANCE
    # =========================================================

    attendance = Attendance.query.filter_by(
        learner_id=learner.id,
        batch_id=batch.id,
        date=date.today(),
    ).first()

    if not attendance:

        attendance = Attendance(
            learner_id=learner.id,
            batch_id=batch.id,
            date=date.today(),
            status="present",
            marked_by=admin.id,
        )

        db.session.add(attendance)


    # =========================================================
    # 8. PAYMENT
    # =========================================================

    if Payment.query.filter_by(
        learner_id=learner.id
    ).count() == 0:

        payment = Payment(
            learner_id=learner.id,
            amount=25000,
            payment_date=date.today(),
            payment_method="online",
            status="paid",
        )

        db.session.add(payment)


    # =========================================================
    # 9. INVOICE
    # =========================================================

    invoice = Invoice.query.filter_by(
        invoice_number="INV-2026-0001"
    ).first()

    if not invoice:

        invoice = Invoice(
            learner_id=learner.id,
            invoice_number="INV-2026-0001",
            amount=25000,
            invoice_date=date.today(),
            status="paid",
        )

        db.session.add(invoice)


    # =========================================================
    # SAVE EVERYTHING
    # =========================================================

    db.session.commit()

    logger.info("Database seed completed successfully.")
    logger.info("10 courses, modules and lessons are ready.")