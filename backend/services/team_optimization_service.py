from services.mongodb_service import mongodb_service
from services.openai_service import openai_service
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.kpi_generation.kpi_generator import KPIGenerator
from modules.kpi_generation.kpi_predictor import KPIPredictor
import itertools


class TeamOptimizationService:
    """
    Service for optimizing team composition to maximize project success.
    """

    @staticmethod
    def find_optimal_team(project_details, available_employees, constraints=None):
        """
        Find the optimal team composition for a project.

        Args:
            project_details: Project requirements
            available_employees: List of available employees
            constraints: Optional constraints (e.g., must include certain employees)

        Returns:
            dict: Optimal team composition with predicted performance
        """
        team_size = project_details.get('project_team_size', 5)
        required_skills = project_details.get('project_languages', [])

        # If constraints specify certain employees must be included
        must_include = []
        if constraints and 'must_include_ids' in constraints:
            must_include = [
                emp for emp in available_employees
                if str(emp['_id']) in constraints['must_include_ids']
            ]
            available_employees = [
                emp for emp in available_employees
                if str(emp['_id']) not in constraints['must_include_ids']
            ]
            team_size -= len(must_include)

        # Score all possible combinations (for small teams)
        if len(available_employees) <= 20 and team_size <= 5:
            best_team = TeamOptimizationService._exhaustive_search(
                available_employees, team_size, project_details, must_include
            )
        else:
            # Use heuristic approach for larger pools
            best_team = TeamOptimizationService._heuristic_search(
                available_employees, team_size, project_details, must_include
            )

        return best_team

    @staticmethod
    def _exhaustive_search(candidates, team_size, project_details, must_include):
        """
        Try all combinations to find optimal team (for small candidate pools).
        """
        best_score = -1
        best_team = None
        best_analysis = None

        # Try all combinations
        for combination in itertools.combinations(candidates, team_size):
            team = list(combination) + must_include

            # Analyze this team
            analysis = KPIGenerator._analyze_team_composition(team, project_details)
            predictions = KPIPredictor.predict_project_success(analysis, project_details)

            # Calculate overall score
            score = (
                    predictions['success_probability'] / 100 * 0.4 +
                    analysis['skill_coverage'] / 100 * 0.3 +
                    analysis['experience_balance'] / 100 * 0.2 +
                    (1 - len(analysis['missing_skills']) / 10) * 0.1
            )

            if score > best_score:
                best_score = score
                best_team = team
                best_analysis = {
                    'team': team,
                    'analysis': analysis,
                    'predictions': predictions,
                    'score': score
                }

        return best_analysis

    @staticmethod
    def _heuristic_search(candidates, team_size, project_details, must_include):
        """
        Use heuristic approach for larger candidate pools.
        """
        selected_team = must_include.copy()
        remaining_slots = team_size

        # Sort candidates by individual fit
        scored_candidates = []
        for candidate in candidates:
            # Calculate individual score
            skills = candidate.get('Skills', [])
            experience = len(candidate.get('Experience', []))

            # Skill match score
            skill_match = SkillMatcher.calculate_skill_similarity(
                skills,
                project_details.get('project_languages', [])
            )

            # Experience score (normalized)
            exp_score = min(experience / 5, 1.0)

            # Combined score
            score = skill_match * 0.7 + exp_score * 0.3

            scored_candidates.append({
                'candidate': candidate,
                'score': score,
                'skills': skills
            })

        # Sort by score
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)

        # Build team iteratively
        team_skills = set()
        for member in must_include:
            team_skills.update(member.get('Skills', []))

        # Add members that provide most value
        for scored in scored_candidates:
            if remaining_slots <= 0:
                break

            candidate = scored['candidate']
            candidate_skills = set(scored['skills'])

            # Calculate value added (new skills brought to team)
            new_skills = candidate_skills - team_skills
            value_score = len(new_skills) / len(candidate_skills) if candidate_skills else 0

            # Combine with individual score
            combined_score = scored['score'] * 0.6 + value_score * 0.4

            # Add if score is good enough
            if combined_score > 0.5 or remaining_slots <= 2:
                selected_team.append(candidate)
                team_skills.update(candidate_skills)
                remaining_slots -= 1

        # Analyze final team
        analysis = KPIGenerator._analyze_team_composition(selected_team, project_details)
        predictions = KPIPredictor.predict_project_success(analysis, project_details)

        return {
            'team': selected_team,
            'analysis': analysis,
            'predictions': predictions,
            'score': predictions['success_probability'] / 100
        }

    @staticmethod
    def suggest_team_improvements(current_team, project_details, available_employees):
        """
        Suggest specific improvements to current team composition.
        """
        # Analyze current team
        current_analysis = KPIGenerator._analyze_team_composition(current_team, project_details)

        suggestions = []

        # Check for critical skill gaps
        if current_analysis['missing_skills']:
            for skill in current_analysis['missing_skills'][:3]:  # Top 3 missing skills
                # Find best candidate with this skill
                best_candidate = None
                best_score = 0

                for emp in available_employees:
                    if any(SkillMatcher.get_similarity(skill, s) > 70 for s in emp.get('Skills', [])):
                        # This candidate has the missing skill
                        skill_match = SkillMatcher.calculate_skill_similarity(
                            emp.get('Skills', []),
                            [skill]
                        )
                        if skill_match > best_score:
                            best_score = skill_match
                            best_candidate = emp

                if best_candidate:
                    suggestions.append({
                        'action': 'add_member',
                        'reason': f'Fill skill gap: {skill}',
                        'candidate': {
                            'id': str(best_candidate['_id']),
                            'name': best_candidate.get('Name', 'Unknown'),
                            'skills': best_candidate.get('Skills', [])
                        },
                        'impact': 'High'
                    })

        # Check for experience imbalance
        if current_analysis['experience_balance'] < 50:
            exp_dist = current_analysis['experience_distribution']

            # Too many juniors?
            if exp_dist.get('Junior', 0) > len(current_team) * 0.5:
                # Find a senior to add or suggest replacing a junior
                senior_candidates = [
                    emp for emp in available_employees
                    if ExperienceAnalyzer.get_experience_level(
                        ExperienceAnalyzer.get_years_of_experience(emp.get('Experience', []))
                    ) in ['Senior', 'Lead']
                ]

                if senior_candidates:
                    suggestions.append({
                        'action': 'add_senior',
                        'reason': 'Balance experience levels',
                        'candidates': [
                            {
                                'id': str(c['_id']),
                                'name': c.get('Name', 'Unknown'),
                                'experience_level': ExperienceAnalyzer.get_experience_level(
                                    ExperienceAnalyzer.get_years_of_experience(c.get('Experience', []))
                                )
                            }
                            for c in senior_candidates[:3]
                        ],
                        'impact': 'Medium'
                    })

        # Check team size
        if len(current_team) > 8:
            suggestions.append({
                'action': 'reduce_size',
                'reason': 'Team too large, causing coordination overhead',
                'recommendation': 'Consider splitting into two teams or removing low-contributors',
                'impact': 'Medium'
            })

        return suggestions


# Singleton instance
team_optimization_service = TeamOptimizationService()