import json
from services.openai_service import openai_service
from modules.employee_matching.skill_matcher import SkillMatcher


class CareerPathAnalyzer:
    """
    Analyzes career paths using LLM to understand actual role progressions
    """

    @staticmethod
    def analyze_career_path(current_role, skills, experience_years):
        """
        Use LLM to analyze the actual career path for a given role

        Args:
            current_role: Current job title/role
            skills: List of current skills
            experience_years: Years of experience

        Returns:
            dict: Career path analysis with next roles and required skills
        """
        prompt = f"""
        Analyze the career progression for a professional with the following profile:
        - Current Role: {current_role}
        - Years of Experience: {experience_years}
        - Current Skills: {', '.join(skills[:20])}  # Limit skills for prompt

        Based on industry standards and common career progressions, provide:
        1. The most logical next role(s) in their career path
        2. Alternative career paths they could pursue
        3. Required skills for each potential next role
        4. Skill gaps based on their current skills

        Consider both vertical progression (promotions) and lateral moves (role changes).

        Return a JSON object with this structure:
        {{
            "current_role_analysis": {{
                "role": "{current_role}",
                "seniority_level": "Junior/Mid/Senior/Lead/Principal",
                "typical_years_required": number
            }},
            "next_roles": [
                {{
                    "role_title": "Next Role Title",
                    "progression_type": "vertical/lateral",
                    "typical_timeline": "X-Y years",
                    "probability": "High/Medium/Low",
                    "required_skills": {{
                        "technical": ["skill1", "skill2"],
                        "soft": ["skill1", "skill2"],
                        "domain": ["skill1", "skill2"]
                    }},
                    "key_responsibilities": ["resp1", "resp2"]
                }}
            ],
            "alternative_paths": [
                {{
                    "path_name": "Technical Leadership",
                    "roles": ["Role1", "Role2", "Role3"],
                    "description": "Path description"
                }}
            ]
        }}

        Be specific to the actual role and industry. Don't use generic titles.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.3)
            # Clean and parse response
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            career_data = json.loads(response.strip())

            # Enhance with skill gap analysis
            career_data = CareerPathAnalyzer._enhance_with_skill_gaps(
                career_data, skills
            )

            return career_data

        except Exception as e:
            print(f"Error analyzing career path with LLM: {e}")
            # Fallback to basic analysis
            return CareerPathAnalyzer._fallback_career_analysis(
                current_role, experience_years
            )

    @staticmethod
    def _enhance_with_skill_gaps(career_data, current_skills):
        """
        Enhance career data with detailed skill gap analysis
        """
        if 'next_roles' not in career_data:
            return career_data

        for role in career_data['next_roles']:
            if 'required_skills' not in role:
                continue

            # Analyze skill gaps for each category
            skill_gaps = {
                'technical': [],
                'soft': [],
                'domain': []
            }

            skill_matches = {
                'technical': [],
                'soft': [],
                'domain': []
            }

            for category in ['technical', 'soft', 'domain']:
                required = role['required_skills'].get(category, [])

                for req_skill in required:
                    # Check if employee has this skill or similar
                    matched = False
                    best_match = None
                    best_score = 0

                    for curr_skill in current_skills:
                        similarity = SkillMatcher.get_similarity(req_skill, curr_skill)
                        if similarity > best_score:
                            best_score = similarity
                            best_match = curr_skill

                    if best_score >= 70:  # 70% similarity threshold
                        skill_matches[category].append({
                            'required': req_skill,
                            'current': best_match,
                            'similarity': best_score
                        })
                        matched = True

                    if not matched:
                        skill_gaps[category].append(req_skill)

            # Add gaps and matches to role data
            role['skill_gaps'] = skill_gaps
            role['skill_matches'] = skill_matches
            role['readiness_score'] = CareerPathAnalyzer._calculate_readiness(
                skill_gaps, skill_matches
            )

        return career_data

    @staticmethod
    def _calculate_readiness(gaps, matches):
        """Calculate readiness score based on gaps and matches"""
        total_required = sum(
            len(gaps.get(cat, [])) + len(matches.get(cat, []))
            for cat in ['technical', 'soft', 'domain']
        )

        total_matched = sum(
            len(matches.get(cat, []))
            for cat in ['technical', 'soft', 'domain']
        )

        if total_required == 0:
            return 100

        return round((total_matched / total_required) * 100, 1)

    @staticmethod
    def _fallback_career_analysis(current_role, experience_years):
        """Fallback career analysis when LLM is not available"""
        # Basic role progression mapping
        role_progressions = {
            'software engineer': {
                'next': 'Senior Software Engineer',
                'timeline': '2-3 years',
                'alt_path': 'Full Stack Developer'
            },
            'senior software engineer': {
                'next': 'Lead Software Engineer',
                'timeline': '3-4 years',
                'alt_path': 'Software Architect'
            },
            'data analyst': {
                'next': 'Senior Data Analyst',
                'timeline': '2-3 years',
                'alt_path': 'Data Scientist'
            },
            # Add more mappings as needed
        }

        role_lower = current_role.lower()
        progression = role_progressions.get(role_lower, {})

        return {
            'current_role_analysis': {
                'role': current_role,
                'seniority_level': 'Mid' if experience_years > 2 else 'Junior',
                'typical_years_required': experience_years
            },
            'next_roles': [
                {
                    'role_title': progression.get('next', 'Senior ' + current_role),
                    'progression_type': 'vertical',
                    'typical_timeline': progression.get('timeline', '2-4 years'),
                    'probability': 'High',
                    'required_skills': {
                        'technical': ['Advanced Programming', 'System Design'],
                        'soft': ['Leadership', 'Communication'],
                        'domain': ['Project Management']
                    }
                }
            ],
            'alternative_paths': []
        }