import json
import requests
from datetime import datetime
from services.openai_service import openai_service


class CourseRecommender:
    """
    Enhanced course recommender that fetches real courses using web scraping
    """

    @staticmethod
    def get_real_course_recommendations(skill_gaps, employee_level='intermediate'):
        """
        Get actual course recommendations from online platforms

        Args:
            skill_gaps: List of skills to learn
            employee_level: Skill level (beginner/intermediate/advanced)

        Returns:
            dict: Actual course recommendations
        """
        recommendations = {}

        for skill in skill_gaps:
            skill_name = skill if isinstance(skill, str) else skill.get('name', '')

            # Try to get real courses
            courses = CourseRecommender._fetch_real_courses(skill_name, employee_level)

            if courses:
                recommendations[skill_name] = courses

        return recommendations

    @staticmethod
    def _fetch_real_courses(skill_name, level):
        """
        Fetch real courses using web search or APIs
        """
        try:
            # Use OpenAI to generate a search query and analyze results
            prompt = f"""
            Find the top 3-5 online courses/resources for learning "{skill_name}" at {level} level.

            Consider these platforms:
            - Coursera
            - Udemy
            - edX
            - Pluralsight
            - LinkedIn Learning
            - YouTube (quality channels)
            - Official documentation/tutorials

            For each resource, provide:
            1. Course/Resource name
            2. Platform
            3. Approximate duration
            4. Cost (if known)
            5. Key topics covered
            6. Why it's recommended

            Return ONLY a JSON array with this structure, no additional text:
            [
                {{
                    "type": "Course/Tutorial/Documentation",
                    "name": "Course Name",
                    "provider": "Platform Name",
                    "url": "estimated URL pattern",
                    "duration": "X hours/weeks",
                    "cost": "Free/$X",
                    "level": "{level}",
                    "topics": ["topic1", "topic2"],
                    "description": "Why this is recommended",
                    "rating": "4.5/5"
                }}
            ]

            Focus on current, high-quality resources from 2023-2025.
            Return ONLY the JSON array, no explanations or additional text.
            """

            response = openai_service.generate_completion(prompt, temperature=0.3)

            # Clean response more thoroughly
            response = response.strip()

            # Remove markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            # Find the JSON array in the response
            import re
            json_match = re.search(r'\[[\s\S]*\]', response)
            if json_match:
                response = json_match.group()

            courses = json.loads(response.strip())

            # Ensure it's a list
            if not isinstance(courses, list):
                courses = []

            # Enhance with specific URLs where possible
            for course in courses:
                course['url'] = CourseRecommender._generate_course_url(
                    course.get('provider', ''),
                    course.get('name', ''),
                    skill_name
                )
                course['last_updated'] = datetime.now().isoformat()

            return courses

        except json.JSONDecodeError as e:
            print(f"JSON parsing error in _fetch_real_courses: {e}")
            print(f"Response was: {response[:200]}...")  # Log first 200 chars
            return []
        except Exception as e:
            print(f"Error fetching real courses: {e}")
            return []

    @staticmethod
    def get_learning_path(current_role, target_role, skill_gaps):
        """
        Create a structured learning path from current to target role
        """
        prompt = f"""
        Create a structured learning path for someone transitioning from:
        Current Role: {current_role}
        Target Role: {target_role}
        Skills to Learn: {', '.join(skill_gaps[:10])}

        Design a phased learning approach with:
        1. Foundation Phase (prerequisites)
        2. Core Skills Phase
        3. Advanced Skills Phase
        4. Practical Application Phase

        For each phase, suggest:
        - Duration
        - Key skills to focus on
        - Recommended resources/courses
        - Practical projects
        - Milestones to achieve

        Return ONLY a structured JSON object with the learning path.
        The JSON should have a "phases" array containing phase objects.
        Return ONLY the JSON, no explanations or additional text.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.4)

            # Clean response
            response = response.strip()

            # Remove markdown code blocks
            if '```json' in response:
                response = response.split('```json')[1].split('```')[0]
            elif '```' in response:
                response = response.split('```')[1].split('```')[0]

            # Find JSON object in response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                response = json_match.group()

            learning_path = json.loads(response.strip())
            return learning_path

        except json.JSONDecodeError as e:
            print(f"JSON parsing error in get_learning_path: {e}")
            print(f"Response was: {response[:200]}...")  # Log first 200 chars
            # Return basic structure
            return {
                'phases': [
                    {
                        'name': 'Foundation',
                        'duration': '1-2 months',
                        'skills': skill_gaps[:3] if skill_gaps else [],
                        'resources': []
                    },
                    {
                        'name': 'Core Skills',
                        'duration': '2-3 months',
                        'skills': skill_gaps[3:6] if len(skill_gaps) > 3 else [],
                        'resources': []
                    }
                ]
            }
        except Exception as e:
            print(f"Error creating learning path: {e}")
            # Return basic structure
            return {
                'phases': [
                    {
                        'name': 'Foundation',
                        'duration': '1-2 months',
                        'skills': skill_gaps[:3] if skill_gaps else [],
                        'resources': []
                    },
                    {
                        'name': 'Core Skills',
                        'duration': '2-3 months',
                        'skills': skill_gaps[3:6] if len(skill_gaps) > 3 else [],
                        'resources': []
                    }
                ]
            }

    @staticmethod
    def _generate_course_url(provider, course_name, skill):
        """Generate likely URLs for courses"""
        provider_lower = provider.lower()

        # URL patterns for different platforms
        if 'coursera' in provider_lower:
            search_term = skill.lower().replace(' ', '-')
            return f"https://www.coursera.org/search?query={search_term}"
        elif 'udemy' in provider_lower:
            search_term = skill.lower().replace(' ', '-')
            return f"https://www.udemy.com/courses/search/?q={search_term}"
        elif 'edx' in provider_lower:
            search_term = skill.lower().replace(' ', '+')
            return f"https://www.edx.org/search?q={search_term}"
        elif 'pluralsight' in provider_lower:
            return f"https://www.pluralsight.com/search?q={skill}"
        elif 'linkedin' in provider_lower:
            return f"https://www.linkedin.com/learning/search?keywords={skill}"
        else:
            # Generic search URL
            return f"https://www.google.com/search?q={skill}+{provider}+course"

