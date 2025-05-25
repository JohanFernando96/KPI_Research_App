from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
from modules.skill_recommendation.role_hierarchy import RoleHierarchy


class RoleSkillAligner:
    """
    Analyze alignment between employee skills and their role requirements.
    """

    @staticmethod
    def analyze_role_alignment(employee, assigned_role):
        """
        Analyze how well an employee's skills align with their assigned role.

        Args:
            employee: Employee data with skills and experience
            assigned_role: The role assigned to the employee

        Returns:
            dict: Alignment analysis
        """
        # Get employee data
        employee_skills = employee.get('Skills', [])
        experience_items = employee.get('Experience', [])

        # Get role requirements from hierarchy
        role_requirements = RoleHierarchy.get_required_skills(assigned_role)

        # Analyze technical skills alignment
        tech_requirements = role_requirements.get('technical', [])
        tech_alignment = RoleSkillAligner._analyze_skill_category_alignment(
            employee_skills, tech_requirements, 'technical'
        )

        # Analyze soft skills alignment
        soft_requirements = role_requirements.get('soft', [])
        soft_alignment = RoleSkillAligner._analyze_skill_category_alignment(
            employee_skills, soft_requirements, 'soft'
        )

        # Check experience requirements
        min_experience = RoleHierarchy.get_min_experience(assigned_role)
        actual_experience = ExperienceAnalyzer.get_years_of_experience(experience_items)
        experience_alignment = {
            'required': min_experience,
            'actual': actual_experience,
            'meets_requirement': actual_experience >= min_experience,
            'gap': max(0, min_experience - actual_experience)
        }

        # Calculate overall alignment score
        tech_score = tech_alignment['alignment_percentage']
        soft_score = soft_alignment['alignment_percentage']
        exp_score = 100 if experience_alignment['meets_requirement'] else (
            actual_experience / min_experience * 100 if min_experience > 0 else 0
        )

        overall_score = (tech_score * 0.5 + soft_score * 0.3 + exp_score * 0.2)

        # Determine readiness level
        readiness_level = RoleSkillAligner._determine_readiness_level(overall_score)

        # Generate recommendations
        recommendations = RoleSkillAligner._generate_alignment_recommendations(
            tech_alignment, soft_alignment, experience_alignment
        )

        return {
            'role': assigned_role,
            'overall_alignment': round(overall_score, 1),
            'readiness_level': readiness_level,
            'technical_alignment': tech_alignment,
            'soft_skills_alignment': soft_alignment,
            'experience_alignment': experience_alignment,
            'recommendations': recommendations
        }

    @staticmethod
    def _analyze_skill_category_alignment(employee_skills, required_skills, category):
        """
        Analyze alignment for a specific skill category.
        """
        if not required_skills:
            return {
                'alignment_percentage': 100,
                'matched_skills': [],
                'missing_skills': [],
                'proficiency_gaps': []
            }

        matched_skills = []
        missing_skills = []
        proficiency_gaps = []

        for req_skill in required_skills:
            skill_name = req_skill.get('name', '')
            min_proficiency = req_skill.get('min_proficiency', 3)

            # Check if employee has this skill
            found = False
            for emp_skill in employee_skills:
                if SkillMatcher.get_similarity(skill_name, emp_skill) > 80:
                    matched_skills.append({
                        'name': skill_name,
                        'has_skill': True,
                        'estimated_proficiency': 3  # Default estimate
                    })
                    found = True
                    break

            if not found:
                missing_skills.append({
                    'name': skill_name,
                    'required_proficiency': min_proficiency,
                    'priority': 'High' if min_proficiency >= 4 else 'Medium'
                })

        alignment_percentage = (
            len(matched_skills) / len(required_skills) * 100
            if required_skills else 100
        )

        return {
            'alignment_percentage': round(alignment_percentage, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'proficiency_gaps': proficiency_gaps
        }

    @staticmethod
    def _determine_readiness_level(overall_score):
        """
        Determine readiness level based on alignment score.
        """
        if overall_score >= 90:
            return "Fully Ready"
        elif overall_score >= 75:
            return "Ready with Minor Gaps"
        elif overall_score >= 60:
            return "Partially Ready"
        elif overall_score >= 40:
            return "Significant Development Needed"
        else:
            return "Major Reskilling Required"

    @staticmethod
    def _generate_alignment_recommendations(tech_alignment, soft_alignment, exp_alignment):
        """
        Generate specific recommendations for improving role alignment.
        """
        recommendations = []

        # Technical skill recommendations
        if tech_alignment['missing_skills']:
            high_priority = [s for s in tech_alignment['missing_skills']
                             if s.get('priority') == 'High']
            if high_priority:
                recommendations.append({
                    'type': 'technical_skills',
                    'priority': 'High',
                    'action': f"Urgently develop skills in: {', '.join([s['name'] for s in high_priority[:3]])}"
                })

        # Soft skill recommendations
        if soft_alignment['missing_skills']:
            recommendations.append({
                'type': 'soft_skills',
                'priority': 'Medium',
                'action': f"Improve soft skills: {', '.join([s['name'] for s in soft_alignment['missing_skills'][:2]])}"
            })

        # Experience recommendations
        if not exp_alignment['meets_requirement']:
            recommendations.append({
                'type': 'experience',
                'priority': 'Low',
                'action': f"Gain {exp_alignment['gap']} more years of experience through challenging projects"
            })

        return recommendations