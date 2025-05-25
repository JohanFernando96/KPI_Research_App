import json
from datetime import datetime, timedelta
from modules.kpi_generation.project_analyzer import ProjectAnalyzer
from services.openai_service import openai_service
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer


class KPIGenerator:
    """
    Enhanced KPI Generator that creates dynamic, team-aware KPIs based on actual team composition
    and individual capabilities rather than generic assumptions.
    """

    @staticmethod
    def generate_kpis(project_details, team_members=None):
        """
        Generate comprehensive KPIs based on project details and optional team composition.

        Args:
            project_details: Dictionary containing project information.
            team_members: Optional list of team members with their skills and experience.

        Returns:
            dict: Generated KPIs and metrics.
        """
        # Extract project parameters
        project_type = project_details.get('project_type', 'Software Development')
        team_size = int(project_details.get('project_team_size', 5))
        timeline = int(project_details.get('project_timeline', 90))
        technologies = project_details.get('project_languages', [])
        sprints = int(project_details.get('project_sprints', 5))

        # Analyze project to inform KPI generation
        type_analysis = ProjectAnalyzer.analyze_project_type(project_type)
        timeline_analysis = ProjectAnalyzer.analyze_timeline(timeline, team_size)
        tech_analysis = ProjectAnalyzer.analyze_technologies(technologies)

        # If team members provided, analyze team composition
        team_analysis = None
        if team_members and len(team_members) > 0:
            team_analysis = KPIGenerator._analyze_team_composition(team_members, project_details)

        # Create comprehensive prompt for OpenAI
        kpi_prompt = KPIGenerator._create_kpi_generation_prompt(
            project_type, team_size, timeline, technologies, sprints,
            type_analysis, timeline_analysis, tech_analysis, team_analysis
        )

        # Generate KPIs using OpenAI
        print(f"Generating KPIs with prompt length: {len(kpi_prompt)}")
        kpi_response = openai_service.generate_completion(kpi_prompt, temperature=0.3, max_tokens=2000)

        # Debug: Print the response
        print(f"OpenAI KPI Response: {kpi_response[:200]}...")  # Print first 200 chars

        # Parse and validate the response
        kpis = KPIGenerator._parse_kpi_response(kpi_response)

        # If team analysis available, apply team-specific adjustments
        if team_analysis:
            kpis = KPIGenerator._apply_team_based_adjustments(kpis, team_analysis)

        return kpis

    @staticmethod
    def _analyze_team_composition(team_members, project_details):
        """
        Analyze the actual team composition to inform realistic KPI generation.
        """
        if not team_members:
            return None

        # Initialize analysis metrics
        total_experience = 0
        all_skills = set()
        skill_counts = {}
        experience_levels = []
        role_distribution = {}

        # Analyze each team member
        for member in team_members:
            # Extract experience
            experience_items = member.get('Experience', [])
            years_exp = ExperienceAnalyzer.get_years_of_experience(experience_items)
            total_experience += years_exp
            exp_level = ExperienceAnalyzer.get_experience_level(years_exp)
            experience_levels.append(exp_level)

            # Count experience levels
            if exp_level not in role_distribution:
                role_distribution[exp_level] = 0
            role_distribution[exp_level] += 1

            # Analyze skills
            member_skills = member.get('Skills', [])
            for skill in member_skills:
                all_skills.add(skill)
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Calculate team metrics
        avg_experience = total_experience / len(team_members) if team_members else 0

        # Calculate skill coverage for required technologies
        required_skills = project_details.get('project_languages', [])
        if isinstance(required_skills, str):
            required_skills = [s.strip() for s in required_skills.split(',')]

        skill_coverage = KPIGenerator._calculate_skill_coverage(all_skills, required_skills)

        # Identify team strengths and weaknesses
        team_strengths = [skill for skill, count in skill_counts.items() if count >= 2]
        missing_skills = [skill for skill in required_skills
                          if not any(SkillMatcher.get_similarity(skill, team_skill) > 70
                                     for team_skill in all_skills)]

        # Calculate realistic velocity based on actual team composition
        velocity_estimate = KPIGenerator._estimate_team_velocity(experience_levels, len(team_members))

        return {
            'team_size': len(team_members),
            'avg_experience': round(avg_experience, 1),
            'skill_coverage': round(skill_coverage, 1),
            'experience_distribution': role_distribution,
            'team_strengths': team_strengths[:5],
            'missing_skills': missing_skills,
            'estimated_velocity': velocity_estimate,
            'has_skill_gaps': len(missing_skills) > 0,
            'experience_balance': KPIGenerator._calculate_experience_balance(role_distribution)
        }

    @staticmethod
    def _calculate_skill_coverage(team_skills, required_skills):
        """Calculate percentage of required skills covered by the team."""
        if not required_skills:
            return 100.0

        covered = 0
        for req_skill in required_skills:
            # Check if any team skill matches the required skill
            for team_skill in team_skills:
                if SkillMatcher.get_similarity(req_skill, team_skill) > 70:
                    covered += 1
                    break

        return (covered / len(required_skills)) * 100

    @staticmethod
    def _estimate_team_velocity(experience_levels, team_size):
        """Estimate realistic team velocity based on experience distribution."""
        # Velocity points per sprint per developer by experience level
        velocity_map = {
            'Junior': 6,
            'Mid-level': 10,
            'Senior': 15,
            'Lead': 18
        }

        # Calculate base velocity
        total_velocity = sum(velocity_map.get(level, 8) for level in experience_levels)

        # Apply team size efficiency factor
        if team_size <= 3:
            efficiency = 1.0  # Small teams are most efficient
        elif team_size <= 6:
            efficiency = 0.9  # Medium teams have some overhead
        elif team_size <= 10:
            efficiency = 0.8  # Larger teams have more overhead
        else:
            efficiency = 0.7  # Very large teams have significant overhead

        return round(total_velocity * efficiency)

    @staticmethod
    def _calculate_experience_balance(role_distribution):
        """Calculate how balanced the team experience is."""
        if not role_distribution:
            return 0

        total = sum(role_distribution.values())
        # Ideal distribution would have a mix of levels
        ideal_distribution = {
            'Junior': 0.2,
            'Mid-level': 0.4,
            'Senior': 0.3,
            'Lead': 0.1
        }

        # Calculate deviation from ideal
        deviation = 0
        for level, ideal_ratio in ideal_distribution.items():
            actual_ratio = role_distribution.get(level, 0) / total
            deviation += abs(actual_ratio - ideal_ratio)

        # Convert to balance score (0-100)
        balance_score = max(0, 100 - (deviation * 50))
        return round(balance_score)

    @staticmethod
    def _create_kpi_generation_prompt(project_type, team_size, timeline, technologies, sprints,
                                      type_analysis, timeline_analysis, tech_analysis, team_analysis):
        """Create a comprehensive prompt for KPI generation."""

        # Base project information
        prompt = f"""
        You are an expert in software project KPI generation. Generate realistic, data-driven KPIs based on the following:

        PROJECT DETAILS:
        - Project Type: {project_type}
        - Team Size: {team_size}
        - Timeline: {timeline} days
        - Technologies: {', '.join(technologies) if isinstance(technologies, list) else technologies}
        - Number of Sprints: {sprints}

        Generate comprehensive KPIs for these categories:
        1. PRODUCTIVITY METRICS: velocity, sprint_burndown_rate, lead_time, cycle_time, story_completion_ratio
        2. CODE QUALITY METRICS: defect_density, average_cyclomatic_complexity, test_coverage, code_churn, rework_ratio
        3. COLLABORATION METRICS: code_review_turnaround_time, merge_conflict_resolution_rate, peer_review_effectiveness
        4. ADAPTABILITY METRICS: feedback_implementation_rate, training_participation_rate, kpi_adjustment_responsiveness

        Return ONLY a valid JSON object with this exact structure:
        {{
            "productivity": {{
                "velocity": {{"value": "X story points per sprint", "target": "Y story points per sprint", "status": "On Track"}},
                "sprint_burndown_rate": {{"value": "X story points per day", "target": "Y story points per day", "status": "At Risk"}},
                "lead_time": {{"value": "X days", "target": "Y days", "status": "Below Target"}},
                "cycle_time": {{"value": "X hours per story point", "target": "Y hours per story point", "status": "On Track"}},
                "story_completion_ratio": {{"value": "X%", "target": "Y%", "status": "On Track"}}
            }},
            "code_quality": {{
                "defect_density": {{"value": "X defects per 1,000 LOC", "target": "Y defects per 1,000 LOC", "status": "On Track"}},
                "average_cyclomatic_complexity": {{"value": "X", "target": "Y", "status": "At Risk"}},
                "test_coverage": {{"value": "X%", "target": "Y%", "status": "Below Target"}},
                "code_churn": {{"value": "X%", "target": "Y%", "status": "On Track"}},
                "rework_ratio": {{"value": "X%", "target": "Y%", "status": "At Risk"}}
            }},
            "collaboration": {{
                "code_review_turnaround_time": {{"value": "X hours", "target": "Y hours", "status": "On Track"}},
                "merge_conflict_resolution_rate": {{"value": "X%", "target": "Y%", "status": "At Risk"}},
                "peer_review_effectiveness": {{"value": "X%", "target": "Y%", "status": "On Track"}}
            }},
            "adaptability": {{
                "feedback_implementation_rate": {{"value": "X%", "target": "Y%", "status": "At Risk"}},
                "training_participation_rate": {{"value": "X%", "target": "Y%", "status": "On Track"}},
                "kpi_adjustment_responsiveness": {{"value": "X days", "target": "Y days", "status": "On Track"}}
            }}
        }}

        Replace X and Y with realistic numeric values. Current values should be 70-85% of targets for a new project.
        Status should be "On Track", "At Risk", or "Below Target".
        """

        return prompt

    @staticmethod
    def _parse_kpi_response(kpi_response):
        """Parse and validate the KPI response from OpenAI."""
        if not kpi_response:
            raise ValueError("Empty response from OpenAI")

        # Try to parse the JSON response
        try:
            kpis = json.loads(kpi_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'(\{[\s\S]*\})', kpi_response)
            if json_match:
                try:
                    kpis = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse KPI response as JSON: {str(e)}")
            else:
                raise ValueError(f"No valid JSON found in response: {kpi_response[:200]}...")

        # Validate structure
        required_categories = ['productivity', 'code_quality', 'collaboration', 'adaptability']
        for category in required_categories:
            if category not in kpis:
                raise ValueError(f"Missing required category: {category}")

        return kpis

    @staticmethod
    def _apply_team_based_adjustments(kpis, team_analysis):
        """Apply additional team-based adjustments to generated KPIs."""
        adjusted_kpis = json.loads(json.dumps(kpis))  # Deep copy

        # Calculate adjustment factors based on team analysis
        skill_factor = team_analysis['skill_coverage'] / 100
        experience_factor = min(1.0, team_analysis['avg_experience'] / 5)  # Normalize to 5 years
        balance_factor = team_analysis['experience_balance'] / 100

        # Overall team effectiveness factor
        team_effectiveness = (skill_factor * 0.4 + experience_factor * 0.4 + balance_factor * 0.2)

        # Apply adjustments to specific KPIs
        if team_effectiveness < 0.7:  # Struggling team
            # Reduce velocity expectations
            if 'productivity' in adjusted_kpis and 'velocity' in adjusted_kpis['productivity']:
                KPIGenerator._adjust_kpi_by_factor(
                    adjusted_kpis['productivity']['velocity'],
                    team_effectiveness,
                    is_higher_better=True
                )

            # Increase quality targets (more defects expected)
            if 'code_quality' in adjusted_kpis and 'defect_density' in adjusted_kpis['code_quality']:
                KPIGenerator._adjust_kpi_by_factor(
                    adjusted_kpis['code_quality']['defect_density'],
                    2 - team_effectiveness,  # Inverse for "lower is better"
                    is_higher_better=False
                )

        return adjusted_kpis

    @staticmethod
    def _adjust_kpi_by_factor(kpi_item, factor, is_higher_better=True):
        """Adjust a KPI item by a factor."""
        try:
            # Extract numeric value from target
            target_str = kpi_item['target']
            if '%' in target_str:
                value = float(target_str.rstrip('%'))
                adjusted = value * factor
                kpi_item['target'] = f"{round(adjusted, 1)}%"
            elif ' ' in target_str:
                parts = target_str.split(' ', 1)
                value = float(parts[0])
                units = parts[1]
                adjusted = value * factor
                kpi_item['target'] = f"{round(adjusted, 1)} {units}"

            # Recalculate status
            kpi_item['status'] = KPIGenerator._calculate_status(
                kpi_item['value'],
                kpi_item['target'],
                is_higher_better
            )
        except Exception as e:
            print(f"Error adjusting KPI: {str(e)}")

    @staticmethod
    def _calculate_status(value_str, target_str, is_higher_better=True):
        """Calculate KPI status based on value vs target."""
        try:
            # Extract numeric values
            value = float(value_str.rstrip('%').split()[0] if ' ' in value_str or '%' in value_str else value_str)
            target = float(target_str.rstrip('%').split()[0] if ' ' in target_str or '%' in target_str else target_str)

            if is_higher_better:
                ratio = value / target if target > 0 else 0
            else:
                ratio = target / value if value > 0 else 0

            if ratio >= 0.9:
                return "On Track"
            elif ratio >= 0.7:
                return "At Risk"
            else:
                return "Below Target"
        except Exception as e:
            print(f"Error calculating status: {str(e)}")
            return "At Risk"

    @staticmethod
    def generate_comprehensive_project_kpis(project_details, team_data=None):
        """
        Generate comprehensive KPIs including team and individual levels.

        Args:
            project_details: Project information
            team_data: Team composition with roles and members

        Returns:
            dict: Multi-level KPI structure
        """
        # Extract team members if provided
        team_members = []
        if team_data:
            team_members = team_data.get('members', [])

        # Generate project-level KPIs with team awareness
        project_kpis = KPIGenerator.generate_kpis(project_details, team_members)

        # Generate individual KPIs for each team member
        individual_kpis = {}
        if team_data and team_data.get('role_assignments'):
            from modules.kpi_generation.individual_kpi_generator import IndividualKPIGenerator

            for assignment in team_data['role_assignments']:
                employee_id = assignment.get('employeeId')
                role_info = {
                    'role': assignment.get('roleName', 'Team Member'),
                    'skills': assignment.get('requiredSkills', [])
                }

                # Find employee data
                employee = next(
                    (m for m in team_members if str(m.get('_id')) == employee_id),
                    None
                )

                if employee:
                    individual_kpis[employee_id] = IndividualKPIGenerator.generate_individual_kpis(
                        project_kpis,
                        role_info,
                        employee,
                        team_members
                    )

        return {
            'project_level': project_kpis,
            'individual_level': individual_kpis,
            'team_metrics': KPIGenerator._analyze_team_composition(team_members,
                                                                   project_details) if team_members else None
        }

    @staticmethod
    def generate_gantt_chart_data(project_details, team_analysis=None):
        """
        Generate Gantt chart data with team composition awareness.
        """
        project_type = project_details.get('project_type', 'Software Development')
        timeline = int(project_details.get('project_timeline', 90))
        sprints = int(project_details.get('project_sprints', 5))
        technologies = project_details.get('project_languages', [])

        # Create prompt with team awareness
        gantt_prompt = f"""
        Generate a Gantt chart timeline for a {project_type} project:
        - Timeline: {timeline} days
        - Sprints: {sprints}
        - Technologies: {', '.join(technologies) if isinstance(technologies, list) else technologies}

        Return ONLY a JSON array with objects containing:
        - "Task": task name
        - "Start": "Day X" (where X is a number)
        - "End": "Day Y" (where Y is a number)

        Example format:
        [
            {{"Task": "Project Setup", "Start": "Day 1", "End": "Day 5"}},
            {{"Task": "Requirements Analysis", "Start": "Day 3", "End": "Day 10"}}
        ]

        Include all project phases with realistic overlaps.
        """

        print(f"Generating Gantt chart with prompt length: {len(gantt_prompt)}")
        gantt_response = openai_service.generate_completion(gantt_prompt, temperature=0.4)

        if not gantt_response:
            raise ValueError("Empty response from OpenAI for Gantt chart")

        print(f"OpenAI Gantt Response: {gantt_response[:200]}...")

        try:
            return json.loads(gantt_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON array from the response
            import re
            json_match = re.search(r'(\[[\s\S]*\])', gantt_response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse Gantt response as JSON: {str(e)}")
            else:
                raise ValueError(f"No valid JSON array found in Gantt response: {gantt_response[:200]}...")

    @staticmethod
    def generate_employee_criteria(project_details, current_team=None):
        """
        Generate employee criteria considering current team composition.
        """
        project_type = project_details.get('project_type', 'Software Development')
        team_size = int(project_details.get('project_team_size', 5))
        technologies = project_details.get('project_languages', [])

        # Analyze current team if provided
        current_skills = set()
        if current_team:
            for member in current_team:
                current_skills.update(member.get('Skills', []))

        criteria_prompt = f"""
        Generate team composition for a {project_type} project:
        - Required team size: {team_size}
        - Technologies: {', '.join(technologies) if isinstance(technologies, list) else technologies}

        Return ONLY a JSON array with exactly {team_size} roles:
        [
            {{
                "role": "Role Title",
                "skills": ["skill1", "skill2"],
                "priority": "High"
            }}
        ]

        Include diverse, complementary roles that cover all project needs.
        """

        print(f"Generating employee criteria with prompt length: {len(criteria_prompt)}")
        criteria_response = openai_service.generate_completion(criteria_prompt, temperature=0.4)

        if not criteria_response:
            raise ValueError("Empty response from OpenAI for employee criteria")

        print(f"OpenAI Criteria Response: {criteria_response[:200]}...")

        try:
            roles = json.loads(criteria_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON array from the response
            import re
            json_match = re.search(r'(\[[\s\S]*\])', criteria_response)
            if json_match:
                try:
                    roles = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse criteria response as JSON: {str(e)}")
            else:
                raise ValueError(f"No valid JSON array found in criteria response: {criteria_response[:200]}...")

        # Ensure correct number of roles
        if len(roles) > team_size:
            roles = roles[:team_size]
        elif len(roles) < team_size:
            # Generate additional roles if needed
            for i in range(len(roles), team_size):
                roles.append({
                    "role": f"Software Developer {i - len(roles) + 1}",
                    "skills": technologies if isinstance(technologies, list) else [technologies],
                    "priority": "Medium"
                })
        return roles

    @staticmethod
    def generate_sprint_breakdown(project_details, team_analysis=None):
        """
        Generate sprint breakdown considering team capabilities.
        """
        project_type = project_details.get('project_type', 'Software Development')
        sprints = int(project_details.get('project_sprints', 5))
        timeline = int(project_details.get('project_timeline', 90))
        technologies = project_details.get('project_languages', [])

        sprint_prompt = f"""
        Generate sprint breakdown for a {project_type} project:
        - {sprints} sprints over {timeline} days
        - Technologies: {', '.join(technologies) if isinstance(technologies, list) else technologies}

        Return ONLY a JSON object:
        {{
            "Sprint 1": ["task1", "task2"],
            "Sprint 2": ["task1", "task2"],
            "Sprint {sprints}": ["task1", "task2"]
        }}

        Include specific tasks for each sprint with logical progression.
        """

        print(f"Generating sprint breakdown with prompt length: {len(sprint_prompt)}")
        sprint_response = openai_service.generate_completion(sprint_prompt, temperature=0.4)

        if not sprint_response:
            raise ValueError("Empty response from OpenAI for sprint breakdown")

        print(f"OpenAI Sprint Response: {sprint_response[:200]}...")

        try:
            return json.loads(sprint_response)
        except json.JSONDecodeError as e:
            # Try to extract JSON object from the response
            import re
            json_match = re.search(r'(\{[\s\S]*\})', sprint_response)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse sprint response as JSON: {str(e)}")
            else:
                raise ValueError(f"No valid JSON object found in sprint response: {sprint_response[:200]}...")