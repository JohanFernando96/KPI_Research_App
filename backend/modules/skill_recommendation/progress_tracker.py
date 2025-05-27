from datetime import datetime, timedelta
import pytz  # Make sure this import is at the top

class ProgressTracker:
    """
    Class for tracking skill development progress.
    """

    @staticmethod
    def create_skill_development_plan(skill_gaps, recommended_resources, deadline=None):
        """
        Create a skill development plan with milestones and deadlines.

        Args:
            skill_gaps: List of skill gaps.
            recommended_resources: Recommended training resources.
            deadline: Optional deadline for completing the plan.

        Returns:
            dict: Skill development plan.
        """
        if not skill_gaps or not recommended_resources:
            return {}

        # Calculate end date (default to 3 months if not specified)
        if deadline:
            # Ensure deadline is timezone-aware
            if isinstance(deadline, str):
                # Parse ISO format string
                try:
                    end_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                except:
                    end_date = datetime.now(pytz.UTC) + timedelta(days=90)
            elif isinstance(deadline, datetime):
                if deadline.tzinfo is None:
                    # Make it timezone-aware (UTC)
                    end_date = pytz.UTC.localize(deadline)
                else:
                    end_date = deadline
            else:
                end_date = datetime.now(pytz.UTC) + timedelta(days=90)
        else:
            end_date = datetime.now(pytz.UTC) + timedelta(days=90)

        # Calculate milestone dates - ensure timezone-aware
        start_date = datetime.now(pytz.UTC)
        duration = (end_date - start_date).days

        # Create plan - convert datetime objects to ISO strings for JSON serialization
        plan = {
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'duration_days': duration,
            'skills': []
        }

        # Distribute skills evenly across the timeline
        skill_count = len(skill_gaps)
        days_per_skill = duration / skill_count if skill_count > 0 else duration

        # Create skill milestones
        current_date = start_date
        for i, skill in enumerate(skill_gaps):
            # Get skill name
            if isinstance(skill, dict):
                skill_name = skill.get('name', f"Skill {i + 1}")
                required_proficiency = skill.get('required_proficiency', 3)
            else:
                skill_name = skill
                required_proficiency = 3

            # Get resources for this skill
            if skill_name in recommended_resources:
                resources = recommended_resources[skill_name]
            else:
                resources = []

            # Calculate milestone date
            milestone_date = current_date + timedelta(days=days_per_skill)
            if milestone_date > end_date:
                milestone_date = end_date

            # Add skill to plan with ISO date strings
            plan['skills'].append({
                'name': skill_name,
                'required_proficiency': required_proficiency,
                'start_date': current_date.isoformat(),
                'target_date': milestone_date.isoformat(),
                'resources': resources,
                'status': 'Not Started',
                'progress': 0.0
            })

            # Update current date for next skill
            current_date = milestone_date

        return plan