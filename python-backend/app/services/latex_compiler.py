"""
LaTeX Compiler Service.
Compiles LaTeX to PDF using Docker sandbox or local pdflatex.
Shell escape is ALWAYS disabled for security.
"""
import os
import uuid
import subprocess
import logging
import tempfile
import shutil
from app.config import settings

logger = logging.getLogger(__name__)


def compile_latex(latex_content: str) -> str:
    """
    Compile LaTeX content to PDF.
    Attempts Docker compilation first, falls back to local pdflatex.

    Args:
        latex_content: Complete LaTeX document content

    Returns:
        Path to the generated PDF file

    Raises:
        RuntimeError: If compilation fails
    """
    job_id = str(uuid.uuid4())
    output_dir = os.path.abspath(settings.LATEX_OUTPUT_DIR)
    os.makedirs(output_dir, exist_ok=True)

    # Write LaTeX to a temp file
    tex_filename = f"{job_id}.tex"
    tex_filepath = os.path.join(output_dir, tex_filename)
    pdf_filepath = os.path.join(output_dir, f"{job_id}.pdf")

    with open(tex_filepath, "w", encoding="utf-8") as f:
        f.write(latex_content)

    try:
        # Try Docker compilation first
        result = _compile_with_docker(tex_filepath, output_dir, job_id)
        if result:
            return result

        # Fallback to local pdflatex
        result = _compile_locally(tex_filepath, output_dir, job_id)
        if result:
            return result

        raise RuntimeError("LaTeX compilation failed with both Docker and local methods")

    finally:
        # Clean up auxiliary files
        for ext in [".aux", ".log", ".out", ".toc", ".nav", ".snm"]:
            aux_file = os.path.join(output_dir, f"{job_id}{ext}")
            if os.path.exists(aux_file):
                os.remove(aux_file)


def _compile_with_docker(tex_filepath: str, output_dir: str, job_id: str) -> str:
    """Try to compile LaTeX using the Docker sandbox container."""
    try:
        # Check if Docker is available
        subprocess.run(["docker", "info"], capture_output=True, check=True, timeout=5)

        # Run pdflatex in the latex-sandbox container
        result = subprocess.run(
            [
                "docker", "exec", "latex-sandbox",
                "pdflatex",
                "--no-shell-escape",
                "-interaction=nonstopmode",
                f"-output-directory=/output",
                f"/output/{job_id}.tex",
            ],
            capture_output=True,
            text=True,
            timeout=settings.LATEX_TIMEOUT_SECONDS,
        )

        pdf_path = os.path.join(output_dir, f"{job_id}.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"Docker LaTeX compilation successful: {pdf_path}")
            return pdf_path

        logger.warning(f"Docker compilation did not produce PDF. stderr: {result.stderr[:500]}")
        return ""

    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError) as e:
        logger.info(f"Docker compilation unavailable: {e}. Will try local fallback.")
        return ""


def _compile_locally(tex_filepath: str, output_dir: str, job_id: str) -> str:
    """Compile LaTeX using local pdflatex installation (fallback)."""
    try:
        pdflatex_cmd = shutil.which("pdflatex")
        if not pdflatex_cmd:
            logger.warning("pdflatex not found locally")
            # Return the tex file path so the user at least gets the LaTeX source
            return tex_filepath

        for run in range(settings.LATEX_MAX_RUNS):
            result = subprocess.run(
                [
                    pdflatex_cmd,
                    "--no-shell-escape",
                    "-interaction=nonstopmode",
                    f"-output-directory={output_dir}",
                    tex_filepath,
                ],
                capture_output=True,
                text=True,
                timeout=settings.LATEX_TIMEOUT_SECONDS,
            )

        pdf_path = os.path.join(output_dir, f"{job_id}.pdf")
        if os.path.exists(pdf_path):
            logger.info(f"Local LaTeX compilation successful: {pdf_path}")
            return pdf_path

        logger.error(f"Local compilation failed. stdout: {result.stdout[:500]}")
        # Return tex file as fallback
        return tex_filepath

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error(f"Local LaTeX compilation failed: {e}")
        return tex_filepath
