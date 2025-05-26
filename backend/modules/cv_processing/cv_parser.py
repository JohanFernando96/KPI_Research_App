import json
from services.openai_service import openai_service
from modules.cv_processing.cv_extractor import CVExtractor


class CVParser:
    """Class for parsing CV text into structured data."""

    @staticmethod
    def parse_cv(file_path):
        """
        Extract and parse a CV from a file path.

        Args:
            file_path: Path to the CV file.

        Returns:
            dict: Structured CV data.
        """
        try:
            # Extract text from CV
            extracted_text = CVExtractor.extract_text(file_path)

            # Preprocess the extracted text
            preprocessed_text = CVExtractor.preprocess_text(extracted_text)

            # Parse the text using OpenAI
            parsed_data_str = openai_service.parse_cv_data(preprocessed_text)

            # Convert the string response to a dictionary
            try:
                parsed_data = json.loads(parsed_data_str)
            except json.JSONDecodeError:
                raise ValueError("Failed to parse OpenAI response as JSON")

            # Add the original file path and raw text for reference
            parsed_data['_meta'] = {
                'source_file': file_path,
                'raw_text_length': len(extracted_text)
            }

            # Enhance the parsed data with AI-powered categorization
            enhanced_data = CVParser.enhance_parsed_data(parsed_data)

            return enhanced_data
        except Exception as e:
            print(f"Error parsing CV: {e}")
            raise

    @staticmethod
    def enhance_parsed_data(parsed_data):
        """
        Enhance the parsed CV data with AI-powered skill categorization and additional derived information.

        Args:
            parsed_data: The parsed CV data.

        Returns:
            dict: Enhanced CV data.
        """
        enhanced_data = parsed_data.copy()

        # Calculate total years of experience
        if 'Experience' in enhanced_data and isinstance(enhanced_data['Experience'], list):
            total_experience = 0
            for exp in enhanced_data['Experience']:
                if 'Duration' in exp and '-' in exp['Duration']:
                    try:
                        start, end = exp['Duration'].split('-')

                        # Handle "Present" or current positions
                        import datetime
                        current_year = datetime.datetime.now().year
                        end = end.lower().replace('present', str(current_year)).strip()
                        start = start.strip()

                        # Extract years
                        if len(start) >= 4 and len(end) >= 4:
                            start_year = int(start[-4:])
                            end_year = int(end[-4:])
                            duration = end_year - start_year
                            if duration > 0:
                                total_experience += duration
                    except Exception:
                        # If we can't parse the duration, just continue
                        continue

            enhanced_data['_derived'] = enhanced_data.get('_derived', {})
            enhanced_data['_derived']['total_years_experience'] = total_experience

        # Use AI to categorize skills intelligently
        if 'Skills' in enhanced_data and isinstance(enhanced_data['Skills'], list) and len(enhanced_data['Skills']) > 0:
            skill_categories = CVParser._categorize_skills_with_ai(enhanced_data['Skills'])

            enhanced_data['_derived'] = enhanced_data.get('_derived', {})
            enhanced_data['_derived']['skill_categories'] = skill_categories

        # Analyze experience for project types and domains
        if 'Experience' in enhanced_data and isinstance(enhanced_data['Experience'], list):
            experience_analysis = CVParser._analyze_experience_with_ai(enhanced_data['Experience'])
            enhanced_data['_derived']['experience_analysis'] = experience_analysis

        return enhanced_data

    @staticmethod
    def _categorize_skills_with_ai(skills_list):
        """
        Use AI to intelligently categorize skills.

        Args:
            skills_list: List of skills to categorize.

        Returns:
            dict: Categorized skills.
        """
        if not skills_list:
            return {}

        # Create a prompt for AI to categorize skills
        prompt = f"""
        Analyze and categorize the following technical skills into appropriate categories.

        Skills to categorize:
        {json.dumps(skills_list, indent=2)}

        Please categorize these skills into the following categories:
        1. "programming_languages" - Programming and scripting languages (e.g., Python, Java, JavaScript, C++, etc.)
        2. "frameworks_libraries" - Frameworks and libraries (e.g., React, Django, Spring Boot, etc.)
        3. "databases" - Database systems and data storage (e.g., MySQL, MongoDB, PostgreSQL, Redis, etc.)
        4. "frontend_design" - Frontend technologies and design tools (e.g., CSS, HTML, Sass, Figma, etc.)
        5. "cloud_devops" - Cloud platforms and DevOps tools (e.g., AWS, Docker, Kubernetes, Jenkins, etc.)
        6. "data_analytics" - Data science and analytics tools (e.g., Pandas, NumPy, Tableau, PowerBI, etc.)
        7. "mobile_development" - Mobile development specific (e.g., Swift, Kotlin, React Native, Flutter, etc.)
        8. "testing_qa" - Testing and QA tools (e.g., Selenium, Jest, JUnit, Cypress, etc.)
        9. "version_control" - Version control and collaboration (e.g., Git, GitHub, GitLab, Bitbucket, etc.)
        10. "project_management" - Project management and methodologies (e.g., Agile, Scrum, JIRA, etc.)
        11. "soft_skills" - Soft skills and methodologies (e.g., Team Leadership, Communication, etc.)
        12. "other_technical" - Other technical skills that don't fit above categories

        For each skill:
        - Identify the most appropriate category
        - If a skill could fit multiple categories, choose the most specific/primary one
        - Consider the context and common usage of the skill
        - Handle variations and abbreviations intelligently (e.g., JS = JavaScript)

        Return the result as a JSON object with categories as keys and arrays of skills as values.
        Only include categories that have at least one skill.
        Ensure each skill appears in exactly one category.

        Example format:
        {{
            "programming_languages": ["Python", "Java"],
            "frameworks_libraries": ["React", "Django"],
            "databases": ["MongoDB", "PostgreSQL"]
        }}

        Return only the JSON object, no additional text or explanation.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.1, max_tokens=1500)

            # Parse the response
            categorized_skills = json.loads(response.strip())

            # Validate that all skills were categorized
            categorized_count = sum(len(skills) for skills in categorized_skills.values())
            if categorized_count < len(skills_list):
                # Find uncategorized skills
                all_categorized = []
                for category_skills in categorized_skills.values():
                    all_categorized.extend(category_skills)

                uncategorized = [skill for skill in skills_list if skill not in all_categorized]
                if uncategorized:
                    if 'other_technical' not in categorized_skills:
                        categorized_skills['other_technical'] = []
                    categorized_skills['other_technical'].extend(uncategorized)

            return categorized_skills

        except Exception as e:
            print(f"Error in AI skill categorization: {e}")
            # Fallback to basic categorization
            return {
                "uncategorized": skills_list
            }

    @staticmethod
    def _analyze_experience_with_ai(experience_list):
        """
        Use AI to analyze experience and extract insights.

        Args:
            experience_list: List of experience entries.

        Returns:
            dict: Experience analysis.
        """
        if not experience_list:
            return {}

        # Create a prompt for AI to analyze experience
        prompt = f"""
        Analyze the following work experience entries and extract key insights:

        Experience data:
        {json.dumps(experience_list, indent=2)}

        Please provide the following analysis:
        1. "industries" - List of industries worked in
        2. "domains" - Technical domains and areas of expertise demonstrated
        3. "project_types" - Types of projects worked on (e.g., web applications, mobile apps, data pipelines, etc.)
        4. "technologies_used" - Key technologies mentioned in responsibilities
        5. "leadership_experience" - Any leadership or mentoring experience mentioned
        6. "key_achievements" - Notable achievements or impacts mentioned
        7. "career_progression" - Analysis of career growth pattern

        Return the result as a JSON object with these keys.
        Be specific and extract actual information from the experience, don't make assumptions.

        Example format:
        {{
            "industries": ["E-commerce", "Financial Services"],
            "domains": ["Web Development", "Cloud Architecture"],
            "project_types": ["E-learning platforms", "Payment systems"],
            "technologies_used": ["React", "Node.js", "AWS"],
            "leadership_experience": ["Led team of 5", "Mentored junior developers"],
            "key_achievements": ["Improved performance by 40%", "Reduced costs by 25%"],
            "career_progression": "Steady growth from Developer to Senior Engineer"
        }}

        Return only the JSON object, no additional text.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.2, max_tokens=1500)

            # Parse the response
            experience_analysis = json.loads(response.strip())

            return experience_analysis

        except Exception as e:
            print(f"Error in AI experience analysis: {e}")
            # Return empty analysis on error
            return {}