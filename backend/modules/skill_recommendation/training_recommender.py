# backend/modules/skill_recommendation/training_recommender.py

class TrainingRecommender:
    """
    Enhanced class for recommending training resources based on skill gaps.
    """

    # Keep existing TRAINING_RESOURCES as fallback
    TRAINING_RESOURCES = {
        "Programming Fundamentals": [
            {
                "type": "Course",
                "name": "Introduction to Programming",
                "provider": "Coursera",
                "url": "https://www.coursera.org/learn/programming-fundamentals",
                "description": "Learn the basics of programming, including variables, loops, and functions."
            },
            {
                "type": "Book",
                "name": "Clean Code",
                "provider": "Robert C. Martin",
                "url": "https://www.amazon.com/Clean-Code-Handbook-Software-Craftsmanship/dp/0132350882",
                "description": "A handbook of good programming practices."
            }
        ],
        "Data Structures": [
            {
                "type": "Course",
                "name": "Data Structures and Algorithms",
                "provider": "Udemy",
                "url": "https://www.udemy.com/course/data-structures-and-algorithms",
                "description": "Learn the most common data structures and algorithms."
            }
        ],
        "Algorithms": [
            {
                "type": "Course",
                "name": "Algorithms Specialization",
                "provider": "Coursera",
                "url": "https://www.coursera.org/specializations/algorithms",
                "description": "Master algorithmic techniques for solving problems."
            }
        ],
        "Version Control": [
            {
                "type": "Tutorial",
                "name": "Git and GitHub Tutorial",
                "provider": "Atlassian",
                "url": "https://www.atlassian.com/git/tutorials",
                "description": "Learn Git version control and GitHub collaboration."
            }
        ],
        "Testing": [
            {
                "type": "Course",
                "name": "Software Testing and Automation",
                "provider": "Udacity",
                "url": "https://www.udacity.com/course/software-testing--cs258",
                "description": "Learn the fundamentals of software testing."
            }
        ],
        "Advanced Programming": [
            {
                "type": "Course",
                "name": "Advanced Programming Techniques",
                "provider": "edX",
                "url": "https://www.edx.org/learn/advanced-programming",
                "description": "Master advanced programming concepts and techniques."
            }
        ],
        "Architecture Design": [
            {
                "type": "Course",
                "name": "Software Architecture & Design",
                "provider": "Udacity",
                "url": "https://www.udacity.com/course/software-architecture-design--ud821",
                "description": "Learn how to design and architect software systems."
            }
        ],
        "System Design": [
            {
                "type": "Book",
                "name": "System Design Interview",
                "provider": "Alex Xu",
                "url": "https://www.amazon.com/System-Design-Interview-Insiders-Guide/dp/1736049119",
                "description": "A guide to system design concepts and practices."
            }
        ],
        "Communication": [
            {
                "type": "Course",
                "name": "Effective Communication Skills",
                "provider": "LinkedIn Learning",
                "url": "https://www.linkedin.com/learning/communication-foundations",
                "description": "Master the art of effective communication in the workplace."
            }
        ],
        "Leadership": [
            {
                "type": "Course",
                "name": "Leadership Development",
                "provider": "Harvard Business School Online",
                "url": "https://online.hbs.edu/courses/leadership-principles/",
                "description": "Develop essential leadership skills and principles."
            }
        ]
    }

    @staticmethod
    def get_resources_for_skill(skill_name, use_real_courses=True):
        """
        Get training resources for a specific skill.

        Args:
            skill_name: Name of the skill.
            use_real_courses: Whether to fetch real courses

        Returns:
            list: List of training resources.
        """
        # Try to get real courses first
        if use_real_courses:
            # Import here to avoid circular dependency
            from modules.skill_recommendation.course_recommender import CourseRecommender
            real_courses = CourseRecommender._fetch_real_courses(skill_name, 'intermediate')
            if real_courses:
                return real_courses

        # Fallback to static resources
        # Check exact match
        if skill_name in TrainingRecommender.TRAINING_RESOURCES:
            return TrainingRecommender.TRAINING_RESOURCES[skill_name]

        # Try case-insensitive match
        for key, resources in TrainingRecommender.TRAINING_RESOURCES.items():
            if key.lower() == skill_name.lower():
                return resources

        # Try partial match
        skill_lower = skill_name.lower()
        for key, resources in TrainingRecommender.TRAINING_RESOURCES.items():
            if skill_lower in key.lower() or key.lower() in skill_lower:
                return resources

        # No match found - try to generate recommendations
        if use_real_courses:
            from modules.skill_recommendation.course_recommender import CourseRecommender
            return CourseRecommender._fetch_real_courses(skill_name, 'beginner') or []

        return []

    @staticmethod
    def recommend_for_skill_gaps(skill_gaps, employee_level='intermediate'):
        """
        Recommend training resources for a list of skill gaps.
        Enhanced with real course recommendations.

        Args:
            skill_gaps: List of skill names or skill objects.
            employee_level: Skill level of employee

        Returns:
            dict: Recommendations by skill.
        """
        # Import here to avoid circular dependency
        from modules.skill_recommendation.course_recommender import CourseRecommender

        # Use CourseRecommender for real recommendations
        recommendations = CourseRecommender.get_real_course_recommendations(
            skill_gaps, employee_level
        )

        # Fill any gaps with static resources
        for skill in skill_gaps:
            skill_name = skill.get('name', '') if isinstance(skill, dict) else skill

            if skill_name not in recommendations:
                static_resources = TrainingRecommender.get_resources_for_skill(
                    skill_name, use_real_courses=False
                )
                if static_resources:
                    recommendations[skill_name] = static_resources

        return recommendations

    @staticmethod
    def recommend_for_career_progression(progression_analysis):
        """
        Enhanced recommendation for career progression with learning paths
        """
        if not progression_analysis:
            return {}

        # Import here to avoid circular dependency
        from modules.skill_recommendation.course_recommender import CourseRecommender

        # Extract key information
        current_role = progression_analysis.get('current_role', 'Unknown')
        next_role = progression_analysis.get('next_role', 'Unknown')
        skill_gaps = progression_analysis.get('skill_gaps', {})
        readiness = progression_analysis.get('readiness', 0)

        # Handle next_role_details structure
        if isinstance(progression_analysis.get('next_role_details'), dict):
            next_role = progression_analysis['next_role_details'].get('role_title', next_role)

        # Determine employee level based on readiness
        if readiness >= 0.7:
            employee_level = 'advanced'
        elif readiness >= 0.4:
            employee_level = 'intermediate'
        else:
            employee_level = 'beginner'

        # Get all skill gaps
        all_gaps = []
        for gap_type in ['technical', 'soft', 'domain']:
            gaps = skill_gaps.get(gap_type, [])
            all_gaps.extend(gaps)

        # Get course recommendations
        course_recommendations = CourseRecommender.get_real_course_recommendations(
            all_gaps[:10],  # Limit to top 10 skills
            employee_level
        )

        # Get learning path
        learning_path = CourseRecommender.get_learning_path(
            current_role,
            next_role,
            [g if isinstance(g, str) else g.get('name', '') for g in all_gaps]
        )

        # Structure recommendations
        recommendations = {
            'current_role': current_role,
            'next_role': next_role,
            'readiness': readiness,
            'employee_level': employee_level,
            'courses': course_recommendations,
            'learning_path': learning_path,
            'priority_skills': all_gaps[:5],  # Top 5 priority skills
            'estimated_time': TrainingRecommender._estimate_learning_time(all_gaps, readiness)
        }

        # Add alternative role recommendations if available
        if 'alternative_next_roles' in progression_analysis:
            recommendations['alternative_paths'] = progression_analysis['alternative_next_roles']

        return recommendations

    @staticmethod
    def _estimate_learning_time(skill_gaps, current_readiness):
        """Estimate time needed to bridge skill gaps"""
        num_gaps = len(skill_gaps)

        if current_readiness >= 0.8:
            time_per_skill = 2  # weeks
        elif current_readiness >= 0.6:
            time_per_skill = 3
        else:
            time_per_skill = 4

        total_weeks = num_gaps * time_per_skill

        return {
            'weeks': total_weeks,
            'months': round(total_weeks / 4, 1),
            'confidence': 'High' if num_gaps < 5 else 'Medium' if num_gaps < 10 else 'Low'
        }

    @staticmethod
    def recommend_for_project(project_skill_gap_analysis):
        """
        Enhanced project-specific recommendations
        """
        if not project_skill_gap_analysis:
            return {}

        # Import here to avoid circular dependency
        from modules.skill_recommendation.course_recommender import CourseRecommender
        from modules.employee_matching.skill_matcher import SkillMatcher

        # Get missing skills with details
        missing_skills_detailed = project_skill_gap_analysis.get('missing_skills_detailed', [])
        partial_matches = project_skill_gap_analysis.get('partial_matches', [])

        # Prioritize skills based on how close current skills are
        high_priority = []  # No close match
        medium_priority = []  # Some similarity
        low_priority = []  # High similarity but not quite there

        for skill_detail in missing_skills_detailed:
            similarity = skill_detail.get('similarity', 0)
            skill_name = skill_detail.get('skill', '')

            if similarity < 40:
                high_priority.append(skill_name)
            else:
                medium_priority.append(skill_name)

        # Add partial matches as low priority
        for partial in partial_matches:
            low_priority.append(partial.get('required', ''))

        # Get recommendations for each priority level
        recommendations = {
            'high_priority': CourseRecommender.get_real_course_recommendations(
                high_priority[:5], 'beginner'
            ),
            'medium_priority': CourseRecommender.get_real_course_recommendations(
                medium_priority[:3], 'intermediate'
            ),
            'low_priority': CourseRecommender.get_real_course_recommendations(
                low_priority[:2], 'advanced'
            ),
            'match_percentage': project_skill_gap_analysis.get('match_percentage', 0),
            'quick_wins': TrainingRecommender._identify_quick_wins(partial_matches)
        }

        return recommendations

    @staticmethod
    def _identify_quick_wins(partial_matches):
        """Identify skills that can be quickly improved"""
        quick_wins = []

        for match in partial_matches[:3]:  # Top 3
            quick_wins.append({
                'current_skill': match.get('partially_matched_with', ''),
                'target_skill': match.get('required', ''),
                'similarity': match.get('similarity', 0),
                'recommendation': f"Enhance your {match.get('partially_matched_with', '')} skills to cover {match.get('required', '')}"
            })

        return quick_wins