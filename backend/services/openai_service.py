# backend/services/openai_service.py

import json
import time
import os
from openai import OpenAI
from config import active_config

# Initialize the OpenAI client with proper configuration
try:
    # Check if API key exists
    api_key = active_config.OPENAI_API_KEY
    if not api_key:
        raise ValueError("OpenAI API key not found in configuration")

    # Initialize client with minimal parameters to avoid httpx issues
    client = OpenAI(
        api_key=api_key,
        # Don't pass any proxy-related parameters
    )
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    client = None


class OpenAIService:
    """
    Enhanced service for OpenAI API operations.
    Provides specialized methods for project analysis and KPI generation.
    """

    @staticmethod
    def generate_completion(prompt, model=None, temperature=0.7, max_tokens=1500):
        """Generate a completion using OpenAI's ChatCompletion API."""
        if not client:
            print("OpenAI client not initialized")
            return ""

        try:
            # Add retry logic for API rate limits
            max_retries = 3
            retry_delay = 2  # seconds

            for attempt in range(max_retries):
                try:
                    response = client.chat.completions.create(
                        model=model or active_config.OPENAI_MODEL or "gpt-3.5-turbo",
                        messages=[
                            {"role": "system",
                             "content": "You are a helpful assistant specializing in software project management, KPI analysis, and team performance optimization."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content.strip()
                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                    else:
                        raise
        except Exception as e:
            print(f"Error in OpenAI API call: {e}")
            raise

    @staticmethod
    def parse_cv_data(extracted_text):
        """Parse CV text into structured format using OpenAI."""
        prompt = f"""
        You are an expert CV parser. Extract and structure the following CV information into the required JSON format.

        Required Format:
        {{
            "Name": "<Full Name>",
            "Contact Information": {{
                "Email": "<Email Address>",
                "Phone": "<Phone Number>",
                "Address": "<Physical Address>",
                "LinkedIn": "<LinkedIn Profile URL>"
            }},
            "Skills": [
                // List ALL technical skills, tools, technologies, languages, frameworks mentioned
                // Include each skill as a separate item
                // Preserve the original naming (e.g., "Node.js" not "NodeJS")
            ],
            "Experience": [
                {{
                    "Role": "<Job Title>",
                    "Company": "<Company Name>",
                    "Duration": "<Start Date> - <End Date or Present>",
                    "Responsibilities": [
                        // List each responsibility as a separate item
                        // Include technologies used within responsibilities
                    ]
                }}
            ],
            "Education": [
                {{
                    "Degree": "<Degree Name>",
                    "Institution": "<University/College Name>",
                    "Duration": "<Start Date> - <End Date>",
                    "Details": "<GPA, Honors, Relevant Coursework, etc.>"
                }}
            ],
            "Certifications and Courses": [
                // List FULL certification names, not abbreviations or single characters
                // Each certification should be a complete, meaningful entry
                // Examples: "AWS Certified Solutions Architect", "Google Cloud Professional Data Engineer"
            ],
            "Extra-Curricular Activities": [
                // List activities, volunteer work, etc.
            ]
        }}

        CRITICAL INSTRUCTIONS:
        1. Extract ALL skills mentioned anywhere in the CV (in skills section, experience, projects, etc.)
        2. For Certifications: Extract complete certification names. Never return single characters or list markers.
        3. Preserve exact skill names as written (don't normalize or change them)
        4. If a section is not found, use an empty array [] or empty object {{}}
        5. Ensure all dates are in a consistent format
        6. Extract technologies mentioned in experience descriptions and add them to skills if not already listed

        CV Text to Parse:
        {extracted_text}

        Return only the JSON object, no additional text or markdown formatting.
        """

        try:
            response = OpenAIService.generate_completion(prompt, temperature=0, max_tokens=3000)

            # Clean the response
            cleaned_response = response.strip()

            # Remove markdown code blocks if present
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]

            return cleaned_response

        except Exception as e:
            print(f"Error parsing CV data: {e}")
            # Return a basic structure if OpenAI fails
            return json.dumps({
                "Name": "",
                "Contact Information": {
                    "Email": "",
                    "Phone": "",
                    "Address": "",
                    "LinkedIn": ""
                },
                "Skills": [],
                "Experience": [],
                "Education": [],
                "Certifications and Courses": [],
                "Extra-Curricular Activities": []
            })

    @staticmethod
    def generate_kpis(project_details):
        """
        Generate KPIs for a project using OpenAI's advanced capabilities.
        Creates comprehensive, realistic KPI targets based on project parameters.

        Args:
            project_details: Dictionary of project details.

        Returns:
            dict: Generated KPIs with targets and descriptions.
        """
        # Use fallback if OpenAI client is not available
        if not client:
            return OpenAIService._generate_fallback_kpis(project_details)

        prompt = f"""
        You are a Project Management KPI specialist. Based on the following project details:
        - Project Type: {project_details.get('project_type', 'N/A')}
        - Project Timeline: {project_details.get('project_timeline', 'N/A')} days
        - Team Size: {project_details.get('project_team_size', 'N/A')}
        - Technologies: {', '.join(project_details.get('project_languages', ['N/A']))}
        - Number of Sprints: {project_details.get('project_sprints', 'N/A')}

        Generate comprehensive KPIs grouped into the following categories:
        1. Productivity & Agile Performance
        2. Code Quality & Efficiency 
        3. Collaboration & Communication
        4. Adaptability & Continuous Improvement

        For each KPI, include:
        - A realistic baseline value (current)
        - A realistic target value
        - A status indicator ("On Track", "At Risk", or "Below Target")

        The KPIs should follow this exact JSON structure:
        {{
          "productivity": {{
            "velocity": {{ "value": "X story points per sprint", "target": "Y story points per sprint", "status": "Status" }},
            "sprint_burndown_rate": {{ "value": "X story points per day", "target": "Y story points per day", "status": "Status" }},
            "lead_time": {{ "value": "X hours", "target": "Y hours", "status": "Status" }},
            "cycle_time": {{ "value": "X hours", "target": "Y hours", "status": "Status" }},
            "story_completion_ratio": {{ "value": "X%", "target": "Y%", "status": "Status" }}
          }},
          "code_quality": {{
            "defect_density": {{ "value": "X defects per 1,000 LOC", "target": "Y defects per 1,000 LOC", "status": "Status" }},
            "average_cyclomatic_complexity": {{ "value": "X", "target": "Y", "status": "Status" }},
            "test_coverage": {{ "value": "X%", "target": "Y%", "status": "Status" }},
            "code_churn": {{ "value": "X%", "target": "Y%", "status": "Status" }},
            "rework_ratio": {{ "value": "X%", "target": "Y%", "status": "Status" }}
          }},
          "collaboration": {{
            "code_review_turnaround_time": {{ "value": "X hours", "target": "Y hours", "status": "Status" }},
            "merge_conflict_resolution_rate": {{ "value": "X%", "target": "Y%", "status": "Status" }},
            "peer_review_effectiveness": {{ "value": "X%", "target": "Y%", "status": "Status" }}
          }},
          "adaptability": {{
            "feedback_implementation_rate": {{ "value": "X%", "target": "Y%", "status": "Status" }},
            "training_participation_rate": {{ "value": "X%", "target": "Y%", "status": "Status" }},
            "kpi_adjustment_responsiveness": {{ "value": "X days", "target": "Y days", "status": "Status" }}
          }}
        }}

        Base your targets on industry standards for this project type, team size, and technology stack.
        Current values should show realistic variations from targets - some ahead, some behind.
        Ensure KPI values match the project details logically (e.g., larger teams should have higher velocity).

        Return only the JSON object, no additional text.
        """

        try:
            kpi_response = OpenAIService.generate_completion(prompt, temperature=0.4)
            # Clean the response to ensure it's valid JSON
            kpi_response = kpi_response.strip()
            if kpi_response.startswith('```json'):
                kpi_response = kpi_response[7:]
            if kpi_response.endswith('```'):
                kpi_response = kpi_response[:-3]
            kpis = json.loads(kpi_response.strip())
            return kpis
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating KPIs with OpenAI: {e}")
            # Return fallback KPIs
            return OpenAIService._generate_fallback_kpis(project_details)

    @staticmethod
    def _generate_fallback_kpis(project_details):
        """Generate fallback KPIs when OpenAI is not available."""
        team_size = int(project_details.get('project_team_size', 5))
        sprints = int(project_details.get('project_sprints', 5))

        return {
            "productivity": {
                "velocity": {"value": f"{team_size * 8} story points per sprint",
                             "target": f"{team_size * 10} story points per sprint", "status": "At Risk"},
                "sprint_burndown_rate": {"value": "4 story points per day", "target": "5 story points per day",
                                         "status": "At Risk"},
                "lead_time": {"value": "72 hours", "target": "48 hours", "status": "Below Target"},
                "cycle_time": {"value": "36 hours", "target": "24 hours", "status": "At Risk"},
                "story_completion_ratio": {"value": "75%", "target": "85%", "status": "At Risk"}
            },
            "code_quality": {
                "defect_density": {"value": "2.5 defects per 1,000 LOC", "target": "1.5 defects per 1,000 LOC",
                                   "status": "Below Target"},
                "average_cyclomatic_complexity": {"value": "12", "target": "10", "status": "At Risk"},
                "test_coverage": {"value": "70%", "target": "80%", "status": "At Risk"},
                "code_churn": {"value": "15%", "target": "10%", "status": "Below Target"},
                "rework_ratio": {"value": "12%", "target": "8%", "status": "At Risk"}
            },
            "collaboration": {
                "code_review_turnaround_time": {"value": "24 hours", "target": "16 hours", "status": "At Risk"},
                "merge_conflict_resolution_rate": {"value": "85%", "target": "95%", "status": "At Risk"},
                "peer_review_effectiveness": {"value": "80%", "target": "90%", "status": "At Risk"}
            },
            "adaptability": {
                "feedback_implementation_rate": {"value": "70%", "target": "85%", "status": "At Risk"},
                "training_participation_rate": {"value": "60%", "target": "80%", "status": "Below Target"},
                "kpi_adjustment_responsiveness": {"value": "5 days", "target": "3 days", "status": "At Risk"}
            }
        }

    @staticmethod
    def analyze_project_complexity(project_details):
        """
        Analyze project complexity and risk factors using OpenAI.
        Provides insights for KPI calibration and team planning.

        Args:
            project_details: Dictionary of project details.

        Returns:
            dict: Analysis of project complexity and risk factors.
        """
        if not client:
            return {
                "complexity_rating": "Medium",
                "focus_areas": ["Productivity", "Quality"],
                "risks": ["Timeline constraints", "Technology stack complexity"]
            }

        prompt = f"""
        As a Project Analysis expert, analyze the complexity and risk factors for this project:
        - Project Type: {project_details.get('project_type', 'N/A')}
        - Project Timeline: {project_details.get('project_timeline', 'N/A')} days
        - Team Size: {project_details.get('project_team_size', 'N/A')}
        - Technologies: {', '.join(project_details.get('project_languages', ['N/A']))}
        - Number of Sprints: {project_details.get('project_sprints', 'N/A')}

        Provide a detailed analysis including:
        1. Overall project complexity rating (Low, Medium, High, Very High)
        2. Technical complexity assessment
        3. Team coordination complexity
        4. Timeline risk assessment
        5. Technology risk factors
        6. Recommended focus areas for KPIs

        Return your analysis as a structured JSON object with clear ratings and detailed explanations.
        Return only the JSON object, no additional text.
        """

        try:
            analysis_response = OpenAIService.generate_completion(prompt, temperature=0.3, max_tokens=2000)
            # Clean the response
            analysis_response = analysis_response.strip()
            if analysis_response.startswith('```json'):
                analysis_response = analysis_response[7:]
            if analysis_response.endswith('```'):
                analysis_response = analysis_response[:-3]
            analysis = json.loads(analysis_response.strip())
            return analysis
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error analyzing project with OpenAI: {e}")
            # Return basic analysis for fallback
            return {
                "complexity_rating": "Medium",
                "focus_areas": ["Productivity", "Quality"],
                "risks": ["Timeline constraints", "Technology stack complexity"]
            }

    @staticmethod
    def recommend_skill_development(employee_data, project_criteria):
        """Recommend skills for development based on employee data and project criteria."""
        if not client:
            return json.dumps({
                "technical_skills": ["Python", "JavaScript", "SQL"],
                "soft_skills": ["Communication", "Team Leadership"],
                "resources": []
            })

        prompt = f"""
        You are a career advisor. Based on the following project requirements and employee's skills, recommend skills, 
        languages, or technologies they should pursue to grow in their career.

        Project Requirements:
        {{
            "Languages": "{project_criteria.get('languages', 'N/A')}",
            "Relevant Field": "{project_criteria.get('field', 'N/A')}"
        }}

        Employee Data:
        {employee_data}

        Provide detailed recommendations for the employee, including specific courses, certifications, or resources 
        they could use to acquire these skills. Include both technical and soft skills that would help them excel 
        in projects with these requirements.

        Format your response as a structured JSON object with clear categories of skills to develop and specific 
        resources for each.
        Return only the JSON object, no additional text.
        """
        try:
            return OpenAIService.generate_completion(prompt, temperature=0.7)
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            return json.dumps({
                "technical_skills": ["Python", "JavaScript", "SQL"],
                "soft_skills": ["Communication", "Team Leadership"],
                "resources": []
            })

    @staticmethod
    def generate_gantt_chart_data(project_details):
        """
        Generate detailed Gantt chart data for project planning.
        Creates realistic task timelines based on project parameters.

        Args:
            project_details: Dictionary of project details.

        Returns:
            list: Detailed Gantt chart data with tasks, dependencies and timing.
        """
        if not client:
            return OpenAIService._generate_fallback_gantt_data(project_details)

        prompt = f"""
        As a Project Planning expert, create a detailed Gantt chart for this project:
        - Project Type: {project_details.get('project_type', 'N/A')}
        - Project Timeline: {project_details.get('project_timeline', 'N/A')} days
        - Team Size: {project_details.get('project_team_size', 'N/A')}
        - Technologies: {', '.join(project_details.get('project_languages', ['N/A']))}
        - Number of Sprints: {project_details.get('project_sprints', 'N/A')}

        Generate a comprehensive task breakdown with:
        1. Task name
        2. Start day (as "Day X" format)
        3. End day (as "Day Y" format)

        Tasks should include:
        - Project kickoff/planning
        - Design and architecture phases
        - Development sprints
        - Testing phases
        - Deployment preparation
        - Final deployment and handover

        Tasks should follow a logical sequence with appropriate overlaps and dependencies.
        The total timeline should match the provided project timeline of {project_details.get('project_timeline', 'N/A')} days.

        Return your Gantt chart data as a JSON array of task objects, each with "Task", "Start", and "End" properties.
        For example: [{"Task": "Project Kickoff", "Start": "Day 1", "End": "Day 3"}, ...]
        Return only the JSON array, no additional text.
        """

        try:
            gantt_response = OpenAIService.generate_completion(prompt, temperature=0.4)
            # Clean the response
            gantt_response = gantt_response.strip()
            if gantt_response.startswith('```json'):
                gantt_response = gantt_response[7:]
            if gantt_response.endswith('```'):
                gantt_response = gantt_response[:-3]
            gantt_data = json.loads(gantt_response.strip())
            return gantt_data
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating Gantt data with OpenAI: {e}")
            # Return fallback data
            return OpenAIService._generate_fallback_gantt_data(project_details)

    @staticmethod
    def _generate_fallback_gantt_data(project_details):
        """Generate fallback Gantt chart data."""
        timeline = int(project_details.get('project_timeline', 90))
        sprints = int(project_details.get('project_sprints', 5))
        sprint_length = timeline // sprints

        return [
            {"Task": "Project Kickoff", "Start": "Day 1", "End": "Day 3"},
            {"Task": "Requirements Analysis", "Start": "Day 3", "End": "Day 7"},
            {"Task": "System Design", "Start": "Day 7", "End": "Day 14"},
            {"Task": "Sprint 1", "Start": "Day 14", "End": f"Day {14 + sprint_length}"},
            {"Task": "Sprint 2", "Start": f"Day {14 + sprint_length}", "End": f"Day {14 + 2 * sprint_length}"},
            {"Task": "Sprint 3", "Start": f"Day {14 + 2 * sprint_length}", "End": f"Day {14 + 3 * sprint_length}"},
            {"Task": "Testing Phase", "Start": f"Day {14 + 3 * sprint_length}", "End": f"Day {timeline - 7}"},
            {"Task": "Deployment", "Start": f"Day {timeline - 7}", "End": f"Day {timeline}"}
        ]

    @staticmethod
    def generate_sprint_breakdown(project_details):
        """
        Generate detailed sprint breakdown for project planning.
        Creates realistic sprint tasks based on project parameters.

        Args:
            project_details: Dictionary of project details.

        Returns:
            dict: Sprint breakdown with detailed tasks for each sprint.
        """
        if not client:
            return OpenAIService._generate_fallback_sprint_breakdown(project_details)

        prompt = f"""
        As an Agile Sprint Planning expert, create a detailed sprint breakdown for this project:
        - Project Type: {project_details.get('project_type', 'N/A')}
        - Project Timeline: {project_details.get('project_timeline', 'N/A')} days
        - Team Size: {project_details.get('project_team_size', 'N/A')}
        - Technologies: {', '.join(project_details.get('project_languages', ['N/A']))}
        - Number of Sprints: {project_details.get('project_sprints', 'N/A')}

        Generate a detailed breakdown of tasks for each sprint, considering:
        1. The project type and its typical lifecycle
        2. The technology stack and implementation order
        3. A logical progression from planning to deployment
        4. Technical dependencies between components

        Each sprint should have specific, concrete tasks that are:
        - Appropriate for the sprint's place in the project timeline
        - Realistic in scope given the team size
        - Specific to the technologies being used
        - Following a logical progression

        Return your sprint breakdown as a JSON object where:
        - Keys are "Sprint 1", "Sprint 2", etc.
        - Values are arrays of task names for that sprint

        For example:
        {{
          "Sprint 1": ["Set up development environment", "Create database schema", ...],
          "Sprint 2": ["Implement user authentication", "Create API endpoints", ...],
          ...
        }}

        Return only the JSON object, no additional text.
        """

        try:
            sprint_response = OpenAIService.generate_completion(prompt, temperature=0.4)
            # Clean the response
            sprint_response = sprint_response.strip()
            if sprint_response.startswith('```json'):
                sprint_response = sprint_response[7:]
            if sprint_response.endswith('```'):
                sprint_response = sprint_response[:-3]
            sprint_data = json.loads(sprint_response.strip())
            return sprint_data
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating sprint breakdown with OpenAI: {e}")
            # Return fallback data
            return OpenAIService._generate_fallback_sprint_breakdown(project_details)

    @staticmethod
    def _generate_fallback_sprint_breakdown(project_details):
        """Generate fallback sprint breakdown."""
        sprints = int(project_details.get('project_sprints', 5))
        result = {}

        for i in range(1, sprints + 1):
            if i == 1:
                result[f"Sprint {i}"] = [
                    "Set up development environment",
                    "Create project structure",
                    "Set up database",
                    "Create basic models"
                ]
            elif i == 2:
                result[f"Sprint {i}"] = [
                    "Implement user authentication",
                    "Create API endpoints",
                    "Build core features"
                ]
            elif i == 3:
                result[f"Sprint {i}"] = [
                    "Enhance features",
                    "Implement business logic",
                    "Add validation"
                ]
            elif i == sprints:
                result[f"Sprint {i}"] = [
                    "Final testing",
                    "Bug fixes",
                    "Deployment preparation"
                ]
            else:
                result[f"Sprint {i}"] = [
                    "Feature development",
                    "Integration testing",
                    "Code review"
                ]

        return result

    @staticmethod
    def generate_team_composition(project_details):
        """
        Generate optimal team composition based on project requirements.
        Suggests roles and required skills based on project parameters.

        Args:
            project_details: Dictionary of project details.

        Returns:
            list: Required roles and skills for the project.
        """
        if not client:
            return OpenAIService._generate_fallback_team_composition(project_details)

        prompt = f"""
        As a Technical Staffing expert, recommend the optimal team composition for this project:
        - Project Type: {project_details.get('project_type', 'N/A')}
        - Project Timeline: {project_details.get('project_timeline', 'N/A')} days
        - Team Size: {project_details.get('project_team_size', 'N/A')}
        - Technologies: {', '.join(project_details.get('project_languages', ['N/A']))}
        - Number of Sprints: {project_details.get('project_sprints', 'N/A')}

        Generate a detailed team composition with exactly {project_details.get('project_team_size', 'N/A')} roles that includes:
        1. Specific role titles appropriate for the project
        2. Required technical skills for each role
        3. A mix of roles appropriate for the project type and technology stack

        Each role should have:
        - A clear title (e.g., "Frontend Developer", "DevOps Engineer")
        - A comprehensive list of required skills, prioritizing the project's technologies
        - Skills that are specific and relevant, not generic

        Return your team composition as a JSON array of role objects, each with "role" and "skills" properties.
        For example: [{"role": "Frontend Developer", "skills": ["React", "JavaScript", "CSS"]}, ...]

        Ensure the total number of roles exactly matches the team size of {project_details.get('project_team_size', 'N/A')}.
        Return only the JSON array, no additional text.
        """

        try:
            team_response = OpenAIService.generate_completion(prompt, temperature=0.4)
            # Clean the response
            team_response = team_response.strip()
            if team_response.startswith('```json'):
                team_response = team_response[7:]
            if team_response.endswith('```'):
                team_response = team_response[:-3]
            team_data = json.loads(team_response.strip())
            return team_data
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating team composition with OpenAI: {e}")
            # Return fallback data
            return OpenAIService._generate_fallback_team_composition(project_details)

    @staticmethod
    def _generate_fallback_team_composition(project_details):
        """Generate fallback team composition."""
        team_size = int(project_details.get('project_team_size', 5))
        languages = project_details.get('project_languages', ['Python', 'JavaScript'])

        if isinstance(languages, str):
            languages = [lang.strip() for lang in languages.split(',')]

        roles = []

        # Lead role
        if team_size >= 1:
            roles.append({
                "role": "Technical Lead",
                "skills": languages + ["System Design", "Team Management", "Code Review"]
            })

        # Backend developers
        if team_size >= 2:
            roles.append({
                "role": "Backend Developer",
                "skills": [languages[0] if languages else "Python", "API Development", "Database Design", "SQL"]
            })

        # Frontend developer
        if team_size >= 3:
            roles.append({
                "role": "Frontend Developer",
                "skills": ["JavaScript", "React", "HTML", "CSS", "Responsive Design"]
            })

        # QA Engineer
        if team_size >= 4:
            roles.append({
                "role": "QA Engineer",
                "skills": ["Test Automation", "Manual Testing", "Selenium", "API Testing"]
            })

        # DevOps
        if team_size >= 5:
            roles.append({
                "role": "DevOps Engineer",
                "skills": ["Docker", "CI/CD", "AWS", "Kubernetes"]
            })

        # Fill remaining positions with full-stack developers
        while len(roles) < team_size:
            roles.append({
                "role": "Full-Stack Developer",
                "skills": languages + ["Database", "API Development", "Frontend Development"]
            })

        return roles[:team_size]

    @staticmethod
    def analyze_project_progress(current_metrics, original_plan):
        """
        Analyze current project progress against the original plan.
        Provides insights for KPI adjustment and corrective actions.

        Args:
            current_metrics: Dictionary of current project metrics.
            original_plan: Dictionary of original project plan and KPIs.

        Returns:
            dict: Analysis of project progress with recommendations.
        """
        if not client:
            return {
                "project_health": "Needs Attention",
                "recommendations": ["Review KPI targets", "Focus on underperforming areas"]
            }

        prompt = f"""
        As a Project Analysis expert, analyze the current project progress against the original plan:

        Original Plan:
        {json.dumps(original_plan, indent=2)}

        Current Metrics:
        {json.dumps(current_metrics, indent=2)}

        Provide a detailed analysis including:
        1. Overall project health assessment
        2. Areas performing better than expected
        3. Areas performing worse than expected
        4. Root causes of deviations
        5. Recommended adjustments to KPI targets
        6. Actionable recommendations for improvement

        Return your analysis as a structured JSON object with clear assessments and detailed recommendations.
        Return only the JSON object, no additional text.
        """

        try:
            analysis_response = OpenAIService.generate_completion(prompt, temperature=0.3, max_tokens=2000)
            # Clean the response
            analysis_response = analysis_response.strip()
            if analysis_response.startswith('```json'):
                analysis_response = analysis_response[7:]
            if analysis_response.endswith('```'):
                analysis_response = analysis_response[:-3]
            analysis = json.loads(analysis_response.strip())
            return analysis
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error analyzing project progress with OpenAI: {e}")
            # Return basic analysis for fallback
            return {
                "project_health": "Needs Attention",
                "recommendations": ["Review KPI targets", "Focus on underperforming areas"]
            }

    @staticmethod
    def generate_retrospective_insights(sprint_data, kpi_data):
        """
        Generate retrospective insights based on sprint and KPI data.
        Provides actionable insights for team improvement.

        Args:
            sprint_data: Dictionary of sprint performance data.
            kpi_data: Dictionary of current KPI metrics.

        Returns:
            dict: Retrospective insights with strengths, areas for improvement, and action items.
        """
        if not client:
            return {
                "strengths": ["Team collaboration"],
                "improvements": ["Sprint planning accuracy"],
                "actions": ["Review estimation process"]
            }

        prompt = f"""
        As an Agile Coach, analyze the following sprint and KPI data to generate insights for a sprint retrospective:

        Sprint Performance:
        {json.dumps(sprint_data, indent=2)}

        KPI Metrics:
        {json.dumps(kpi_data, indent=2)}

        Generate a comprehensive retrospective analysis that includes:
        1. Key strengths demonstrated during the sprint
        2. Areas for improvement with specific examples
        3. Concrete action items for the next sprint
        4. KPI trends and their implications
        5. Recommended focus areas for the team

        Return your analysis as a structured JSON object with clear, actionable insights.
        Return only the JSON object, no additional text.
        """

        try:
            insights_response = OpenAIService.generate_completion(prompt, temperature=0.4, max_tokens=2000)
            # Clean the response
            insights_response = insights_response.strip()
            if insights_response.startswith('```json'):
                insights_response = insights_response[7:]
            if insights_response.endswith('```'):
                insights_response = insights_response[:-3]
            insights = json.loads(insights_response.strip())
            return insights
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error generating retrospective insights with OpenAI: {e}")
            # Return basic insights for fallback
            return {
                "strengths": ["Team collaboration"],
                "improvements": ["Sprint planning accuracy"],
                "actions": ["Review estimation process"]
            }


# Singleton instance of OpenAI service
openai_service = OpenAIService()