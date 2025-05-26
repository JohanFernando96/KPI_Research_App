from modules.skill_recommendation.role_hierarchy import RoleHierarchy
from modules.skill_recommendation.career_path_analyzer import CareerPathAnalyzer
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer


class SkillGapAnalyzer:
    """
    Enhanced class for analyzing skill gaps with career path awareness
    """

    @staticmethod
    def analyze_role_skill_gap(employee_skills, role_name, current_role=None):
        """
        Analyze the gap between an employee's skills and those required for a specific role.
        Now with enhanced skill matching and career path awareness.

        Args:
            employee_skills: List of employee skills.
            role_name: Name of the role to analyze against.
            current_role: Current role of the employee (optional)

        Returns:
            dict: Analysis of skill gaps.
        """
        if not employee_skills:
            employee_skills = []

        # Get required skills for the role from hierarchy or LLM
        required_skills = RoleHierarchy.get_required_skills(role_name)

        # If no predefined requirements, use LLM to understand the role
        if not required_skills.get('technical') and not required_skills.get('soft'):
            # Use career path analyzer to get role requirements
            career_analysis = CareerPathAnalyzer.analyze_career_path(
                role_name, employee_skills, 0
            )

            if career_analysis and 'current_role_analysis' in career_analysis:
                # Extract skills from the analysis
                required_skills = {
                    'technical': [],
                    'soft': []
                }
                # Populate from LLM analysis if available

        # Analyze technical skills with fuzzy matching
        tech_skills = required_skills.get('technical', [])
        tech_gaps = []
        tech_matches = []
        tech_partial_matches = []

        for skill_item in tech_skills:
            skill_name = skill_item['name'] if isinstance(skill_item, dict) else skill_item
            min_proficiency = skill_item.get('min_proficiency', 3) if isinstance(skill_item, dict) else 3

            # Enhanced skill matching with similarity check
            best_match = None
            best_score = 0

            for emp_skill in employee_skills:
                similarity = SkillMatcher.get_similarity(skill_name, emp_skill)
                if similarity > best_score:
                    best_score = similarity
                    best_match = emp_skill

            if best_score >= 80:  # Strong match
                tech_matches.append({
                    'name': skill_name,
                    'matched_with': best_match,
                    'similarity': best_score,
                    'required_proficiency': min_proficiency
                })
            elif best_score >= 60:  # Partial match
                tech_partial_matches.append({
                    'name': skill_name,
                    'partially_matched_with': best_match,
                    'similarity': best_score,
                    'required_proficiency': min_proficiency
                })
            else:  # No match
                tech_gaps.append({
                    'name': skill_name,
                    'required_proficiency': min_proficiency,
                    'closest_skill': best_match if best_score > 40 else None,
                    'similarity': best_score if best_score > 40 else 0
                })

        # Analyze soft skills similarly
        soft_skills = required_skills.get('soft', [])
        soft_gaps = []
        soft_matches = []
        soft_partial_matches = []

        for skill_item in soft_skills:
            skill_name = skill_item['name'] if isinstance(skill_item, dict) else skill_item
            min_proficiency = skill_item.get('min_proficiency', 3) if isinstance(skill_item, dict) else 3

            best_match = None
            best_score = 0

            for emp_skill in employee_skills:
                similarity = SkillMatcher.get_similarity(skill_name, emp_skill)
                if similarity > best_score:
                    best_score = similarity
                    best_match = emp_skill

            if best_score >= 80:
                soft_matches.append({
                    'name': skill_name,
                    'matched_with': best_match,
                    'similarity': best_score,
                    'required_proficiency': min_proficiency
                })
            elif best_score >= 60:
                soft_partial_matches.append({
                    'name': skill_name,
                    'partially_matched_with': best_match,
                    'similarity': best_score,
                    'required_proficiency': min_proficiency
                })
            else:
                soft_gaps.append({
                    'name': skill_name,
                    'required_proficiency': min_proficiency,
                    'closest_skill': best_match if best_score > 40 else None,
                    'similarity': best_score if best_score > 40 else 0
                })

        # Calculate coverage percentages with partial matches
        tech_full_coverage = len(tech_matches) / len(tech_skills) if tech_skills else 1.0
        tech_partial_coverage = len(tech_partial_matches) / len(tech_skills) if tech_skills else 0.0
        tech_total_coverage = (len(tech_matches) + len(tech_partial_matches) * 0.5) / len(
            tech_skills) if tech_skills else 1.0

        soft_full_coverage = len(soft_matches) / len(soft_skills) if soft_skills else 1.0
        soft_partial_coverage = len(soft_partial_matches) / len(soft_skills) if soft_skills else 0.0
        soft_total_coverage = (len(soft_matches) + len(soft_partial_matches) * 0.5) / len(
            soft_skills) if soft_skills else 1.0

        overall_coverage = (tech_total_coverage + soft_total_coverage) / 2

        # Prepare analysis result
        analysis = {
            'role': role_name,
            'current_role': current_role,
            'technical': {
                'gaps': tech_gaps,
                'matches': tech_matches,
                'partial_matches': tech_partial_matches,
                'full_coverage': tech_full_coverage,
                'partial_coverage': tech_partial_coverage,
                'total_coverage': tech_total_coverage
            },
            'soft': {
                'gaps': soft_gaps,
                'matches': soft_matches,
                'partial_matches': soft_partial_matches,
                'full_coverage': soft_full_coverage,
                'partial_coverage': soft_partial_coverage,
                'total_coverage': soft_total_coverage
            },
            'overall_coverage': overall_coverage,
            'is_qualified': overall_coverage >= 0.7,
            'readiness_level': SkillGapAnalyzer._determine_readiness_level(overall_coverage)
        }

        return analysis

    @staticmethod
    def analyze_career_progression(employee_skills, current_role, experience_years):
        """
        Enhanced career progression analysis using LLM for accurate career paths
        """
        if not employee_skills:
            employee_skills = []

        # Use CareerPathAnalyzer for intelligent career path analysis
        career_path_data = CareerPathAnalyzer.analyze_career_path(
            current_role, employee_skills, experience_years
        )

        # Extract the most probable next role
        next_roles = career_path_data.get('next_roles', [])

        if not next_roles:
            # Fallback to RoleHierarchy
            return SkillGapAnalyzer._fallback_career_progression(
                employee_skills, current_role, experience_years
            )

        # Get the highest probability next role
        primary_next_role = max(next_roles, key=lambda x: {
            'High': 3, 'Medium': 2, 'Low': 1
        }.get(x.get('probability', 'Low'), 0))

        # Extract skill gaps from the career path analysis
        skill_gaps = primary_next_role.get('skill_gaps', {})
        skill_matches = primary_next_role.get('skill_matches', {})

        # Calculate readiness
        readiness = primary_next_role.get('readiness_score', 0) / 100

        # Check timeline expectations
        timeline = primary_next_role.get('typical_timeline', '2-3 years')
        timeline_parts = timeline.split('-')
        min_years = int(timeline_parts[0].strip().split()[0]) if timeline_parts else 2

        # Prepare progression analysis
        progression_analysis = {
            'current_role': current_role,
            'current_role_analysis': career_path_data.get('current_role_analysis', {}),
            'next_role': primary_next_role.get('role_title'),
            'next_role_details': primary_next_role,
            'alternative_next_roles': [
                role.get('role_title') for role in next_roles[1:3]
            ],  # Top 3 alternatives
            'is_at_top': False,
            'readiness': readiness,
            'skill_readiness': readiness,
            'experience_readiness': 1.0 if experience_years >= min_years else experience_years / min_years,
            'expected_timeline': timeline,
            'skill_gaps': skill_gaps,
            'skill_matches': skill_matches,
            'is_ready': readiness >= 0.8,
            'alternative_career_paths': career_path_data.get('alternative_paths', [])
        }

        return progression_analysis

    @staticmethod
    def _determine_readiness_level(coverage):
        """Determine readiness level based on coverage percentage"""
        if coverage >= 0.9:
            return "Fully Ready"
        elif coverage >= 0.75:
            return "Nearly Ready"
        elif coverage >= 0.6:
            return "Moderately Ready"
        elif coverage >= 0.4:
            return "Partially Ready"
        else:
            return "Significant Development Needed"

    @staticmethod
    def _fallback_career_progression(employee_skills, current_role, experience_years):
        """Fallback method using RoleHierarchy"""
        # Get current role data
        current_role_data = RoleHierarchy.get_role_hierarchy(current_role)
        if not current_role_data:
            # If current role not found in hierarchy, find the best match
            current_role = RoleHierarchy.find_matching_role(employee_skills, experience_years)
            current_role_data = RoleHierarchy.get_role_hierarchy(current_role)

        # Get next role
        next_role = current_role_data.get('next_role', None)

        if not next_role:
            # At the top of the hierarchy
            return {
                'current_role': current_role,
                'next_role': None,
                'is_at_top': True,
                'readiness': 1.0,
                'skill_gaps': {}
            }

        # Analyze skill gap for next role
        next_role_analysis = SkillGapAnalyzer.analyze_role_skill_gap(
            employee_skills, next_role, current_role
        )

        # Check experience requirements
        next_role_min_exp = RoleHierarchy.get_min_experience(next_role)
        experience_gap = max(0, next_role_min_exp - experience_years)

        # Calculate overall readiness
        skill_readiness = next_role_analysis['overall_coverage']
        exp_readiness = 1.0 if experience_gap == 0 else min(1.0, experience_years / next_role_min_exp)
        overall_readiness = (skill_readiness * 0.7) + (exp_readiness * 0.3)

        # Prepare progression analysis
        tech_gaps = next_role_analysis['technical']['gaps']
        soft_gaps = next_role_analysis['soft']['gaps']

        return {
            'current_role': current_role,
            'next_role': next_role,
            'is_at_top': False,
            'readiness': overall_readiness,
            'skill_readiness': skill_readiness,
            'experience_readiness': exp_readiness,
            'experience_gap': experience_gap,
            'skill_gaps': {
                'technical': tech_gaps,
                'soft': soft_gaps
            },
            'is_ready': overall_readiness >= 0.8
        }

    @staticmethod
    def analyze_project_skill_gap(employee_skills, project_skills):
        """
        Enhanced project skill gap analysis with fuzzy matching
        """
        if not employee_skills:
            employee_skills = []

        if not project_skills:
            project_skills = []

        # Analyze each project skill requirement
        missing_skills = []
        matching_skills = []
        partial_matches = []

        for proj_skill in project_skills:
            best_match = None
            best_score = 0

            for emp_skill in employee_skills:
                similarity = SkillMatcher.get_similarity(proj_skill, emp_skill)
                if similarity > best_score:
                    best_score = similarity
                    best_match = emp_skill

            if best_score >= 80:
                matching_skills.append({
                    'required': proj_skill,
                    'matched_with': best_match,
                    'similarity': best_score
                })
            elif best_score >= 60:
                partial_matches.append({
                    'required': proj_skill,
                    'partially_matched_with': best_match,
                    'similarity': best_score
                })
            else:
                missing_skills.append({
                    'skill': proj_skill,
                    'closest_match': best_match if best_score > 40 else None,
                    'similarity': best_score if best_score > 40 else 0
                })

        # Calculate similarity considering partial matches
        full_matches = len(matching_skills)
        partial_match_weight = len(partial_matches) * 0.5
        total_required = len(project_skills)

        similarity = (full_matches + partial_match_weight) / total_required if total_required > 0 else 1.0

        # Prepare analysis result
        analysis = {
            'missing_skills': [ms['skill'] for ms in missing_skills],
            'missing_skills_detailed': missing_skills,
            'matching_skills': matching_skills,
            'partial_matches': partial_matches,
            'similarity': similarity,
            'match_percentage': round(similarity * 100, 1),
            'is_qualified': similarity >= 0.7,
            'readiness_level': SkillGapAnalyzer._determine_readiness_level(similarity)
        }

        return analysis