import sys
import os

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.resume_generator import validate_latex_structure

def test_validate_latex_structure():
    # Test valid structure
    valid_latex = r"""
    \begin{itemize}
        \item Skill 1
        \item Skill 2
    \end{itemize}
    """
    assert validate_latex_structure(valid_latex) == []

    # Test missing end
    missing_end = r"""
    \begin{itemize}
        \item Skill 1
    """
    errors = validate_latex_structure(missing_end)
    assert any("never closed" in e for e in errors)
    assert "itemize" in errors[0]

    # Test mismatch
    mismatch = r"""
    \begin{itemize}
        \item Skill 1
    \end{enumerate}
    """
    errors = validate_latex_structure(mismatch)
    assert any("mismatch" in e for e in errors)

    # Test nested
    nested = r"""
    \begin{itemize}
        \item \begin{enumerate} \item nested \end{enumerate}
    \end{itemize}
    """
    assert validate_latex_structure(nested) == []

    # Test unbalanced nested
    unbalanced_nested = r"""
    \begin{itemize}
        \item \begin{enumerate} \item nested
    \end{itemize}
    """
    errors = validate_latex_structure(unbalanced_nested)
    assert len(errors) > 0

if __name__ == "__main__":
    try:
        test_validate_latex_structure()
        print("✅ LaTeX Validator tests passed!")
    except AssertionError as e:
        print(f"❌ LaTeX Validator tests failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
