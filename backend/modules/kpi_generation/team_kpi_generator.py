import json
from services.openai_service import openai_service
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer


class TeamKPIGenerator:
    """
    Generate team-level KPIs based on actual team composition and collective capabilities.
    """

    @staticmethod
    def generate_team_based_kpis(project_details, team_members):
        """
        Generate realistic team KPIs based on actual team capabilities.

        Args:
            project_details: Project information
            team_members: List of team member data with skills and experience

        Returns:
            dict: Team-based KPIs
        """
        # Analyze team composition
        team_analysis = TeamKPIGenerator._analyze_team_composition(team_members, project_details)

        # Generate KPIs using team analysis
        prompt = f"""
        Generate realistic team KPIs based on the actual team composition and capabilities.

        Project Details:
        - Type: {project_details.get('project_type')}
        - Timeline: {project_details.get('project_timeline')} days
        - Technologies: {', '.join(project_details.get('project_languages', []))}
        - Sprints: {project_details.get('project_sprints')}

        Team Analysis:
        - Team Size: {team_analysis['team_size']}
        - Average Experience: {team_analysis['avg_experience']} years
        - Skill Coverage: {team_analysis['skill_coverage']}%
        - Experience Distribution: {json.dumps(team_analysis['experience_distribution'])}
        - Collective Strengths: {', '.join(team_analysis['team_strengths'])}
        - Collective Weaknesses: {', '.join(team_analysis['team_weaknesses'])}
        - Team Velocity Estimate: {team_analysis['estimated_velocity']} story points/sprint

        Generate KPIs that reflect:
        1. Realistic velocity based on team's actual experience levels
        2. Quality metrics adjusted for skill gaps
        3. Collaboration metrics considering team size and distribution
        4. Learning curve for missing skills

        Consider:
        - Teams with skill gaps need 10-20% more time
        - Mixed experience levels may slow velocity by 15%
        - New team formation adds 20% ramp-up time in first sprint

        Return realistic KPIs as JSON matching the standard KPI structure.
        """

        kpi_response = openai_service.generate_completion(prompt, temperature=0.3)

        try:
            team_kpis = json.loads(kpi_response)
            # Apply team-specific adjustments
            return TeamKPIGenerator._apply_team_adjustments(team_kpis, team_analysis)
        except:
            raise ValueError("Failed to generate team-based KPIs")

    @staticmethod
    def _analyze_team_composition(team_members, project_details):
        """
        Analyze the team's collective capabilities.
        """
        if not team_members:
            return {
                'team_size': 0,
                'avg_experience': 0,
                'skill_coverage': 0,
                'experience_distribution': {},
                'team_strengths': [],
                'team_weaknesses': [],
                'estimated_velocity': 0
            }

        # Collect team data
        total_experience = 0
        all_skills = set()
        experience_levels = []
        skill_counts = {}

        for member in team_members:
            # Get experience
            exp_years = ExperienceAnalyzer.get_years_of_experience(
                member.get('Experience', [])
            )
            total_experience += exp_years
            exp_level = ExperienceAnalyzer.get_experience_level(exp_years)
            experience_levels.append(exp_level)

            # Collect skills
            for skill in member.get('Skills', []):
                all_skills.add(skill)
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

        # Calculate team metrics
        avg_experience = total_experience / len(team_members)

        # Experience distribution
        exp_distribution = {}
        for level in experience_levels:
            exp_distribution[level] = exp_distribution.get(level, 0) + 1

        # Skill coverage
        required_skills = project_details.get('project_languages', [])
        if isinstance(required_skills, str):
            required_skills = [s.strip() for s in required_skills.split(',')]

        covered_skills = 0
        for req_skill in required_skills:
            if any(req_skill.lower() in skill.lower() for skill in all_skills):
                covered_skills += 1

        skill_coverage = (covered_skills / len(required_skills) * 100) if required_skills else 100

        # Identify strengths (skills multiple people have)
        team_strengths = [skill for skill, count in skill_counts.items() if count >= 2]

        # Identify weaknesses (required skills no one has)
        team_weaknesses = []
        for req_skill in required_skills:
            if not any(req_skill.lower() in skill.lower() for skill in all_skills):
                team_weaknesses.append(req_skill)

        # Estimate velocity based on team composition
        velocity_per_dev = {
            'Junior': 6,
            'Mid-level': 10,
            'Senior': 15,
            'Lead': 18
        }

        estimated_velocity = sum(
            velocity_per_dev.get(level, 8) for level in experience_levels
        )

        # Apply team size efficiency factor
        if len(team_members) <= 3:
            estimated_velocity *= 1.0
        elif len(team_members) <= 6:
            estimated_velocity *= 0.9
        else:
            estimated_velocity *= 0.8

        return {
            'team_size': len(team_members),
            'avg_experience': round(avg_experience, 1),
            'skill_coverage': round(skill_coverage, 1),
            'experience_distribution': exp_distribution,
            'team_strengths': team_strengths[:5],
            'team_weaknesses': team_weaknesses,
            'estimated_velocity': round(estimated_velocity)
        }

    @staticmethod
    def _apply_team_adjustments(kpis, team_analysis):
        """
        Apply team-specific adjustments to KPIs.
        """
        # Skill coverage adjustment
        coverage_factor = team_analysis['skill_coverage'] / 100

        # Experience balance factor
        exp_dist = team_analysis['experience_distribution']
        total_members = team_analysis['team_size']

        # Teams with mixed experience levels work less efficiently
        if len(exp_dist) > 2:  # More than 2 different experience levels
            balance_factor = 0.85
        elif 'Junior' in exp_dist and exp_dist.get('Junior', 0) > total_members / 2:
            balance_factor = 0.75  # Junior-heavy team
        else:
            balance_factor = 0.95

        # Combined adjustment factor
        team_factor = coverage_factor * balance_factor

        # Apply to productivity KPIs
        if 'productivity' in kpis and 'velocity' in kpis['productivity']:
            # Use the team's estimated velocity
            current_velocity = int(team_analysis['estimated_velocity'] * 0.8)
            target_velocity = team_analysis['estimated_velocity']
            kpis['productivity']['velocity']['value'] = f"{current_velocity} story points per sprint"
            kpis['productivity']['velocity']['target'] = f"{target_velocity} story points per sprint"
            kpis['productivity']['velocity'][
                'status'] = "At Risk" if current_velocity < target_velocity * 0.9 else "On Track"

        return kpis