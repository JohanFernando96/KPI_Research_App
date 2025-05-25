from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer


def validate_project_data(project_data):
    """
    Validate project data structure and values.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    # Required fields
    required_fields = ['project_type', 'project_timeline', 'project_team_size']
    for field in required_fields:
        if field not in project_data:
            errors.append(f"Missing required field: {field}")

    # Validate timeline
    if 'project_timeline' in project_data:
        try:
            timeline = int(project_data['project_timeline'])
            if timeline < 7:
                errors.append("Project timeline must be at least 7 days")
            elif timeline > 730:
                errors.append("Project timeline cannot exceed 730 days (2 years)")
        except (ValueError, TypeError):
            errors.append("Project timeline must be a valid number")

    # Validate team size
    if 'project_team_size' in project_data:
        try:
            team_size = int(project_data['project_team_size'])
            if team_size < 1:
                errors.append("Team size must be at least 1")
            elif team_size > 50:
                errors.append("Team size cannot exceed 50")
        except (ValueError, TypeError):
            errors.append("Team size must be a valid number")

    # Validate sprint count if provided
    if 'project_sprints' in project_data:
        try:
            sprints = int(project_data['project_sprints'])
            if sprints < 1:
                errors.append("Number of sprints must be at least 1")

            # Check sprint duration makes sense
            if 'project_timeline' in project_data:
                timeline = int(project_data['project_timeline'])
                avg_sprint_duration = timeline / sprints
                if avg_sprint_duration < 7:
                    errors.append("Average sprint duration is less than 7 days")
                elif avg_sprint_duration > 30:
                    errors.append("Average sprint duration exceeds 30 days")
        except (ValueError, TypeError):
            errors.append("Number of sprints must be a valid number")

    return len(errors) == 0, errors


def validate_team_composition(team_members, project_requirements):
    """
    Validate if team composition meets project requirements.

    Returns:
        tuple: (is_valid, issues)
    """
    issues = []

    if not team_members:
        issues.append("Team has no members")
        return False, issues

    # Check team size
    required_size = project_requirements.get('project_team_size', 5)
    if len(team_members) < required_size * 0.8:  # Allow 20% understaffing
        issues.append(f"Team significantly understaffed: {len(team_members)}/{required_size}")

    # Check required skills coverage
    required_skills = project_requirements.get('project_languages', [])
    if isinstance(required_skills, str):
        required_skills = [s.strip() for s in required_skills.split(',') if s.strip()]

    team_skills = set()
    for member in team_members:
        team_skills.update(member.get('Skills', []))

    missing_critical_skills = []
    skill_coverage = 0

    for required_skill in required_skills:
        found = False
        for team_skill in team_skills:
            if SkillMatcher.get_similarity(required_skill, team_skill) > 70:
                found = True
                skill_coverage += 1
                break

        if not found:
            missing_critical_skills.append(required_skill)

    coverage_percentage = (skill_coverage / len(required_skills) * 100) if required_skills else 100

    if coverage_percentage < 60:
        issues.append(f"Low skill coverage: {coverage_percentage:.0f}% (missing: {', '.join(missing_critical_skills)})")

    # Check experience balance
    experience_levels = []
    for member in team_members:
        exp_years = ExperienceAnalyzer.get_years_of_experience(member.get('Experience', []))
        exp_level = ExperienceAnalyzer.get_experience_level(exp_years)
        experience_levels.append(exp_level)

    # Count experience distribution
    exp_counts = {}
    for level in experience_levels:
        exp_counts[level] = exp_counts.get(level, 0) + 1

    # Check for problematic distributions
    total = len(experience_levels)
    if exp_counts.get('Junior', 0) > total * 0.6:
        issues.append("Team is too junior-heavy (>60% juniors)")

    if not any(level in ['Senior', 'Lead'] for level in experience_levels) and total > 3:
        issues.append("Team lacks senior technical leadership")

    # Check for minimum average experience if specified
    min_avg_experience = project_requirements.get('min_avg_experience', 0)
    if min_avg_experience > 0:
        total_exp = sum(
            ExperienceAnalyzer.get_years_of_experience(member.get('Experience', []))
            for member in team_members
        )
        avg_exp = total_exp / len(team_members)

        if avg_exp < min_avg_experience:
            issues.append(f"Insufficient average experience: {avg_exp:.1f}/{min_avg_experience} years")

    return len(issues) == 0, issues


def validate_kpi_structure(kpis):
    """
    Validate KPI structure and values.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    if not isinstance(kpis, dict):
        errors.append("KPIs must be a dictionary")
        return False, errors

    required_categories = ['productivity', 'code_quality', 'collaboration', 'adaptability']

    for category in required_categories:
        if category not in kpis:
            errors.append(f"Missing required KPI category: {category}")
            continue

        category_kpis = kpis[category]
        if not isinstance(category_kpis, dict):
            errors.append(f"KPI category '{category}' must be a dictionary")
            continue

        # Check each KPI in category
        for kpi_name, kpi_data in category_kpis.items():
            if not isinstance(kpi_data, dict):
                errors.append(f"KPI '{kpi_name}' in '{category}' must be a dictionary")
                continue

            # Check required fields
            required_fields = ['value', 'target', 'status']
            for field in required_fields:
                if field not in kpi_data:
                    errors.append(f"KPI '{kpi_name}' missing required field: {field}")

            # Validate status
            valid_statuses = ['On Track', 'At Risk', 'Below Target']
            if 'status' in kpi_data and kpi_data['status'] not in valid_statuses:
                errors.append(f"KPI '{kpi_name}' has invalid status: {kpi_data['status']}")

            # Validate value format
            if 'value' in kpi_data and 'target' in kpi_data:
                value_str = str(kpi_data['value'])
                target_str = str(kpi_data['target'])

                # Check if both have same format (percentage, units, etc.)
                value_has_percent = '%' in value_str
                target_has_percent = '%' in target_str

                if value_has_percent != target_has_percent:
                    errors.append(f"KPI '{kpi_name}' value and target have inconsistent formats")

    return len(errors) == 0, errors


def validate_employee_data(employee):
    """
    Validate employee/resume data structure.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    # Check required fields
    if 'Name' not in employee or not employee['Name']:
        errors.append("Employee must have a name")

    if 'Skills' not in employee:
        errors.append("Employee must have a skills list")
    elif not isinstance(employee['Skills'], list):
        errors.append("Skills must be a list")
    elif len(employee['Skills']) == 0:
        errors.append("Employee must have at least one skill")

    if 'Experience' not in employee:
        errors.append("Employee must have experience list")
    elif not isinstance(employee['Experience'], list):
        errors.append("Experience must be a list")

    # Validate experience entries
    if 'Experience' in employee and isinstance(employee['Experience'], list):
        for i, exp in enumerate(employee['Experience']):
            if not isinstance(exp, dict):
                errors.append(f"Experience entry {i} must be a dictionary")
                continue

            if 'Role' not in exp or not exp['Role']:
                errors.append(f"Experience entry {i} missing role")

            if 'Company' not in exp or not exp['Company']:
                errors.append(f"Experience entry {i} missing company")

    # Validate contact information if present
    if 'Contact Information' in employee:
        contact = employee['Contact Information']
        if not isinstance(contact, dict):
            errors.append("Contact Information must be a dictionary")
        else:
            if 'Email' in contact and contact['Email']:
                # Basic email validation
                if '@' not in contact['Email']:
                    errors.append("Invalid email format")

    return len(errors) == 0, errors


def validate_role_assignment(role_assignment, available_employees):
    """
    Validate role assignment data.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    if not isinstance(role_assignment, dict):
        errors.append("Role assignment must be a dictionary")
        return False, errors

    # Check required fields
    if 'employeeId' not in role_assignment:
        errors.append("Role assignment missing employeeId")

    if 'roleName' not in role_assignment:
        errors.append("Role assignment missing roleName")

    # Check if employee exists
    if 'employeeId' in role_assignment:
        employee_exists = any(
            str(emp.get('_id')) == role_assignment['employeeId']
            for emp in available_employees
        )
        if not employee_exists:
            errors.append(f"Employee {role_assignment['employeeId']} not found")

    return len(errors) == 0, errors


def validate_sprint_breakdown(sprint_breakdown, expected_sprints):
    """
    Validate sprint breakdown structure.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    if not isinstance(sprint_breakdown, dict):
        errors.append("Sprint breakdown must be a dictionary")
        return False, errors

    # Check sprint count
    sprint_keys = [key for key in sprint_breakdown.keys() if key.startswith('Sprint ')]
    if len(sprint_keys) != expected_sprints:
        errors.append(f"Expected {expected_sprints} sprints, found {len(sprint_keys)}")

    # Validate each sprint
    for i in range(1, expected_sprints + 1):
        sprint_key = f"Sprint {i}"
        if sprint_key not in sprint_breakdown:
            errors.append(f"Missing {sprint_key}")
            continue

        tasks = sprint_breakdown[sprint_key]
        if not isinstance(tasks, list):
            errors.append(f"{sprint_key} tasks must be a list")
        elif len(tasks) == 0:
            errors.append(f"{sprint_key} has no tasks")

    return len(errors) == 0, errors


def validate_chart_data(chart_data, chart_type):
    """
    Validate chart data structure based on chart type.

    Returns:
        tuple: (is_valid, errors)
    """
    errors = []

    if chart_type == 'gantt':
        if not isinstance(chart_data, list):
            errors.append("Gantt chart data must be a list")
            return False, errors

        for i, task in enumerate(chart_data):
            if not isinstance(task, dict):
                errors.append(f"Gantt task {i} must be a dictionary")
                continue

            required_fields = ['Task', 'Start', 'End']
            for field in required_fields:
                if field not in task:
                    errors.append(f"Gantt task {i} missing field: {field}")

            # Validate day format
            if 'Start' in task and not task['Start'].startswith('Day '):
                errors.append(f"Gantt task {i} Start must be in format 'Day X'")

            if 'End' in task and not task['End'].startswith('Day '):
                errors.append(f"Gantt task {i} End must be in format 'Day X'")

    elif chart_type == 'burndown':
        # Burndown chart validation would go here
        pass

    return len(errors) == 0, errors