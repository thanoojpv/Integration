import logging
import os
import subprocess
import tempfile
import shutil

logger = logging.getLogger(__name__)

# ============================================================
# DOCKER CONFIGURATION
# ============================================================

# Resolve Docker from the system PATH.
# This works across macOS, Linux, CI, and containerized environments.
DOCKER_COMMAND = shutil.which("docker")

# Docker images
PYTHON_IMAGE = "python:3.12-alpine"
C_IMAGE = "gcc:14"
JAVA_IMAGE = "eclipse-temurin:21-jdk-alpine"
JAVASCRIPT_IMAGE = "node:22-alpine"

# Maximum execution time
TIME_LIMIT_SECONDS = 3

# Container resource limits
MEMORY_LIMIT = "128m"
CPU_LIMIT = "0.5"
PIDS_LIMIT = "64"


# ============================================================
# DOCKER AVAILABILITY
# ============================================================

def docker_available():
    """
    Check whether Docker is available.
    """

    if not DOCKER_COMMAND:
        return False

    try:
        result = subprocess.run(
            [
                DOCKER_COMMAND,
                "--version",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )

        return result.returncode == 0

    except Exception:
        return False


# ============================================================
# COMMON VALIDATION
# ============================================================

def validate_code_and_input(code, input_data=""):
    """
    Validate learner code and input.
    """

    if not isinstance(code, str):
        return {
            "valid": False,
            "result": {
                "status": "error",
                "stdout": "",
                "stderr": "Invalid code.",
                "execution_time": 0,
            },
        }

    if not code.strip():
        return {
            "valid": False,
            "result": {
                "status": "empty",
                "stdout": "",
                "stderr": "No code was provided.",
                "execution_time": 0,
            },
        }

    if not isinstance(input_data, str):
        input_data = str(input_data)

    if not docker_available():
        return {
            "valid": False,
            "result": {
                "status": "error",
                "stdout": "",
                "stderr": (
                    "Docker is not available. "
                    "Please make sure Docker Desktop is running."
                ),
                "execution_time": 0,
            },
        }

    return {
        "valid": True,
        "code": code,
        "input_data": input_data,
    }


# ============================================================
# COMMON DOCKER EXECUTION
# ============================================================

def run_docker_code(
    code,
    input_data,
    image,
    source_filename,
    command,
):
    """
    Run code inside an isolated Docker container.

    Security:
    - No network
    - Memory limit
    - CPU limit
    - Process limit
    - Read-only filesystem
    - Temporary writable /tmp
    - Dropped Linux capabilities
    - No privilege escalation
    - Hard execution timeout
    """

    validation = validate_code_and_input(
        code,
        input_data,
    )

    if not validation["valid"]:
        return validation["result"]

    temp_dir = tempfile.mkdtemp(
        prefix="lms_code_"
    )

    code_file = os.path.join(
        temp_dir,
        source_filename,
    )

    try:

        # ----------------------------------------------------
        # WRITE SOURCE CODE
        # ----------------------------------------------------

        with open(
            code_file,
            "w",
            encoding="utf-8",
        ) as file:
            file.write(code)

        # ----------------------------------------------------
        # DOCKER COMMAND
        # ----------------------------------------------------

        docker_command = [
            DOCKER_COMMAND,

            "run",

            "--rm",

            # Keep STDIN open
            "-i",

            # =================================================
            # NETWORK SECURITY
            # =================================================

            "--network",
            "none",

            # =================================================
            # RESOURCE LIMITS
            # =================================================

            "--memory",
            MEMORY_LIMIT,

            "--cpus",
            CPU_LIMIT,

            "--pids-limit",
            PIDS_LIMIT,

            # =================================================
            # FILESYSTEM SECURITY
            # =================================================

            "--read-only",

            # =================================================
            # LINUX SECURITY
            # =================================================

            "--cap-drop",
            "ALL",

            "--security-opt",
            "no-new-privileges",

            # =================================================
            # TEMPORARY WRITABLE FILESYSTEM
            # =================================================

            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=16m",

            # =================================================
            # COMPILATION DIRECTORY
            # =================================================

            "--tmpfs",
            "/build:rw,exec,nosuid,size=32m",

            # =================================================
            # MOUNT USER CODE
            # =================================================

            "--mount",
            (
                f"type=bind,"
                f"src={temp_dir},"
                f"dst=/runner,"
                f"readonly"
            ),

            # =================================================
            # IMAGE
            # =================================================

            image,

            # =================================================
            # EXECUTION COMMAND
            # =================================================

            *command,
        ]

        # ----------------------------------------------------
        # EXECUTE
        # ----------------------------------------------------

        try:

            completed = subprocess.run(
                docker_command,
                input=input_data,
                capture_output=True,
                text=True,
                timeout=TIME_LIMIT_SECONDS,
                check=False,
            )

        except subprocess.TimeoutExpired:

            return {
                "status": "time_limit_exceeded",
                "stdout": "",
                "stderr": (
                    "Time Limit Exceeded.\n"
                    f"Your program exceeded the "
                    f"{TIME_LIMIT_SECONDS} second limit."
                ),
                "execution_time": TIME_LIMIT_SECONDS,
            }

        # ----------------------------------------------------
        # OUTPUT
        # ----------------------------------------------------

        stdout = completed.stdout or ""
        stderr = completed.stderr or ""

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if completed.returncode == 0:

            return {
                "status": "success",
                "stdout": stdout,
                "stderr": stderr,
                "execution_time": 0,
            }

        # ----------------------------------------------------
        # COMPILATION / RUNTIME ERROR
        # ----------------------------------------------------

        return {
            "status": "runtime_error",
            "stdout": stdout,
            "stderr": stderr,
            "execution_time": 0,
        }

    except Exception as error:

        logger.exception("Code runner internal error")

        return {
            "status": "error",
            "stdout": "",
            "stderr": "Code execution could not be completed. Please try again.",
            "execution_time": 0,
        }

    finally:

        try:
            shutil.rmtree(
                temp_dir,
                ignore_errors=True,
            )
        except Exception:
            pass


# ============================================================
# PYTHON
# ============================================================

def run_python_code(code, input_data=""):
    """
    Execute Python code.
    """

    return run_docker_code(
        code=code,
        input_data=input_data,
        image=PYTHON_IMAGE,
        source_filename="code.py",
        command=[
            "python",
            "/runner/code.py",
        ],
    )


# ============================================================
# C
# ============================================================

def run_c_code(code, input_data=""):

    return run_docker_code(
        code=code,
        input_data=input_data,
        image=C_IMAGE,
        source_filename="main.c",
        command=[
            "sh",
            "-c",
            (
                "gcc /runner/main.c -O2 "
                "-o /build/main && "
                "/build/main"
            ),
        ],
    )

# ============================================================
# C++
# ============================================================

def run_cpp_code(code, input_data=""):

    return run_docker_code(
        code=code,
        input_data=input_data,
        image=C_IMAGE,
        source_filename="main.cpp",
        command=[
            "sh",
            "-c",
            (
                "g++ /runner/main.cpp -O2 "
                "-std=c++17 "
                "-o /build/main && "
                "/build/main"
            ),
        ],
    )


# ============================================================
# JAVA
# ============================================================

def run_java_code(code, input_data=""):

    return run_docker_code(
        code=code,
        input_data=input_data,
        image=JAVA_IMAGE,
        source_filename="Main.java",
        command=[
            "sh",
            "-c",
            (
                "cp /runner/Main.java /build/Main.java && "
                "javac /build/Main.java && "
                "java -cp /build Main"
            ),
        ],
    )


# ============================================================
# JAVASCRIPT
# ============================================================

def run_javascript_code(code, input_data=""):
    """
    Execute JavaScript using Node.js.
    """

    return run_docker_code(
        code=code,
        input_data=input_data,
        image=JAVASCRIPT_IMAGE,
        source_filename="main.js",
        command=[
            "node",
            "/runner/main.js",
        ],
    )


# ============================================================
# LANGUAGE DISPATCHER
# ============================================================

def run_code(
    code,
    language,
    input_data="",
):
    """
    Execute code according to the selected language.

    Supported:
        Python
        C
        C++
        Java
        JavaScript
    """

    if not isinstance(language, str):
        return {
            "status": "error",
            "stdout": "",
            "stderr": "Programming language was not specified.",
            "execution_time": 0,
        }

    normalized_language = (
        language
        .strip()
        .lower()
        .replace(" ", "")
        .replace("-", "")
        .replace("_", "")
        .replace("#", "sharp")
        .replace("++", "plusplus")
    )

    # --------------------------------------------------------
    # PYTHON
    # --------------------------------------------------------

    if normalized_language in (
        "python",
        "py",
    ):
        return run_python_code(
            code,
            input_data,
        )

    # --------------------------------------------------------
    # C
    # --------------------------------------------------------

    if normalized_language == "c":
        return run_c_code(
            code,
            input_data,
        )

    # --------------------------------------------------------
    # C++
    # --------------------------------------------------------

    if normalized_language in (
        "c++",
        "cplusplus",
        "cpp",
    ):
        return run_cpp_code(
            code,
            input_data,
        )

    # --------------------------------------------------------
    # JAVA
    # --------------------------------------------------------

    if normalized_language == "java":
        return run_java_code(
            code,
            input_data,
        )

    # --------------------------------------------------------
    # JAVASCRIPT
    # --------------------------------------------------------

    if normalized_language in (
        "javascript",
        "js",
        "node",
        "nodejs",
    ):
        return run_javascript_code(
            code,
            input_data,
        )

    # --------------------------------------------------------
    # UNSUPPORTED LANGUAGE
    # --------------------------------------------------------

    return {
        "status": "error",
        "stdout": "",
        "stderr": (
            f"Unsupported programming language: {language}. "
            "Supported languages are Python, C, C++, Java, "
            "and JavaScript."
        ),
        "execution_time": 0,
    }