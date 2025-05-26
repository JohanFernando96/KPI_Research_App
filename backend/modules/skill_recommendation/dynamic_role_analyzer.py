import json
from services.openai_service import openai_service
from services.mongodb_service import mongodb_service
from datetime import datetime


class DynamicRoleAnalyzer:
    """
    Dynamic role analysis using AI instead of hardcoded hierarchies.
    """

    @staticmethod
    def analyze_role_requirements(role_name, industry="Software Development"):
        """
        Use AI to determine role requirements dynamically.

        Args:
            role_name: Name of the role to analyze
            industry: Industry context

        Returns:
            dict: Role requirements and progression path
        """
        prompt = f"""
        As an HR and Career Development expert, analyze the role "{role_name}" in the {industry} industry.

        Provide a comprehensive analysis including:
        1. Required technical skills (with proficiency levels 1-5)
        2. Required soft skills (with proficiency levels 1-5)
        3. Minimum years of experience
        4. Typical next role in career progression
        5. Previous role in career progression
        6. Key responsibilities
        7. Industry-specific requirements

        Format the response as a JSON object with this structure:
        {{
            "role": "{role_name}",
            "level": <numeric level 1-5>,
            "technical_skills": [
                {{"name": "skill", "min_proficiency": 3, "importance": "critical|high|medium|low"}}
            ],
            "soft_skills": [
                {{"name": "skill", "min_proficiency": 3, "importance": "critical|high|medium|low"}}
            ],
            "min_experience": <years>,
            "next_role": "role name",
            "previous_role": "role name",
            "responsibilities": ["responsibility1", "responsibility2"],
            "certifications": ["relevant certifications"],
            "tools": ["specific tools/platforms"]
        }}

        Be specific and realistic based on current industry standards.
        Return only the JSON object.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.3)
            # Clean and parse response
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            role_data = json.loads(response.strip())

            # Cache the analysis in MongoDB for future use
            mongodb_service.update_one(
                'RoleAnalysis',
                {'role_name': role_name, 'industry': industry},
                {'$set': {
                    'analysis': role_data,
                    'updated_at': datetime.now()
                }},
                upsert=True
            )

            return role_data

        except Exception as e:
            print(f"Error analyzing role: {e}")
            # Check cache
            cached = mongodb_service.find_one(
                'RoleAnalysis',
                {'role_name': role_name, 'industry': industry}
            )
            if cached:
                return cached.get('analysis', {})
            return {}

    @staticmethod
    def determine_career_path(current_role, years_experience, employee_skills):
        """
        Determine personalized career progression path.
        """
        prompt = f"""
        As a Career Development expert, create a personalized career progression path.

        Current Status:
        - Role: {current_role}
        - Experience: {years_experience} years
        - Skills: {', '.join(employee_skills[:20])}  # Limit for prompt size

        Provide:
        1. Assessment of current position fit
        2. Recommended next role (1-2 years)
        3. Aspirational role (3-5 years)
        4. Alternative career paths based on skills
        5. Key skills to develop for progression

        Format as JSON:
        {{
            "current_fit_score": <0-100>,
            "readiness_for_next_level": <0-100>,
            "next_role": {{
                "title": "role",
                "timeline": "1-2 years",
                "required_skills": ["skill1", "skill2"],
                "skill_gaps": ["missing1", "missing2"]
            }},
            "aspirational_role": {{
                "title": "role",
                "timeline": "3-5 years",
                "preparation_needed": ["area1", "area2"]
            }},
            "alternative_paths": [
                {{"role": "role", "fit_score": 85, "reason": "strong match with skills"}}
            ]
        }}

        Return only JSON.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.4)
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            return json.loads(response.strip())

        except Exception as e:
            print(f"Error determining career path: {e}")
            return {
                "current_fit_score": 70,
                "readiness_for_next_level": 50,
                "next_role": {
                    "title": "Senior " + current_role,
                    "timeline": "1-2 years",
                    "required_skills": [],
                    "skill_gaps": []
                }
            }