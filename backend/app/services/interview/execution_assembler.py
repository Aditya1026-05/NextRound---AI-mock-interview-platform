from typing import Optional


class ExecutionAssembler:
    """Pure compilation component synthesizing language declarations, driver template, and solution code."""

    @staticmethod
    def assemble(
        candidate_code: str,
        driver_template: str,
        boilerplate_template: Optional[str] = None
    ) -> str:
        """Assembles standard library definitions, helper wrapper classes, and candidate solution code."""
        code_parts = []
        if boilerplate_template:
            code_parts.append(boilerplate_template.strip())

        placeholder = "{CANDIDATE_CODE}"
        if placeholder in driver_template:
            assembled_driver = driver_template.replace(placeholder, candidate_code)
            code_parts.append(assembled_driver)
        else:
            code_parts.append(candidate_code.strip())
            code_parts.append(driver_template.strip())

        return "\n\n".join(code_parts)
