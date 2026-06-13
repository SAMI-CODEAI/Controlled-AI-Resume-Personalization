from app.services.guardrail_validator import validate_resume

def test_guardrail_fix():
    authorized_terms = ["Python", "FastAPI", "Sami", "Neural Nexus", "Google"]
    
    # Test case 1: Name "Sami" should be allowed if in authorized_terms
    latex_sami = "\\textbf{Sami} is a software engineer."
    is_valid, violations = validate_resume(latex_sami, authorized_terms)
    print(f"Test 1 (Name Sami): {'Success' if is_valid else 'Failed: ' + str(violations)}")
    
    # Test case 2: True unauthorized skill should still be rejected
    latex_bad = "\\textbf{Underwater Basket Weaving} expert."
    is_valid, violations = validate_resume(latex_bad, authorized_terms)
    print(f"Test 2 (Bad Skill): {'Success' if not is_valid and 'underwater basket weaving' in violations else 'Failed'}")

if __name__ == "__main__":
    test_guardrail_fix()
