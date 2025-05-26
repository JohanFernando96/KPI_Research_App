from datetime import datetime, timedelta
import pytz  # Add this import


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
            if isinstance(deadline, datetime):
                if deadline.tzinfo is None:
                    # Make it timezone-aware (UTC)
                    end_date = pytz.UTC.localize(deadline)
                else:
                    end_date = deadline
            else:
                # If it's a string, parse it
                end_date = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
                if end_date.tzinfo is None:
                    end_date = pytz.UTC.localize(end_date)
        else:
            end_date = datetime.now(pytz.UTC) + timedelta(days=90)

        # Calculate milestone dates - ensure timezone-aware
        start_date = datetime.now(pytz.UTC)
        duration = (end_date - start_date).days

        # Create plan
        plan = {
            'start_date': start_date,
            'end_date': end_date,
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

            # Add skill to plan
            plan['skills'].append({
                'name': skill_name,
                'required_proficiency': required_proficiency,
                'start_date': current_date,
                'target_date': milestone_date,
                'resources': resources,
                'status': 'Not Started',
                'progress': 0.0
            })

            # Update current date for next skill
            current_date = milestone_date

        return plan

    @staticmethod
    def update_progress(development_plan, skill_name, progress, completed_resources=None):
        """
        Update progress for a skill in the development plan.

        Args:
            development_plan: Skill development plan.
            skill_name: Name of the skill to update.
            progress: Progress value (0.0 to 1.0).
            completed_resources: List of completed training resources.

        Returns:
            dict: Updated development plan.
        """
        if not development_plan or 'skills' not in development_plan:
            return development_plan

        # Make a copy of the plan
        updated_plan = development_plan.copy()
        updated_skills = []

        for skill in development_plan['skills']:
            # Find the skill to update
            if skill['name'].lower() == skill_name.lower():
                # Update progress
                skill_copy = skill.copy()
                skill_copy['progress'] = min(1.0, max(0.0, progress))  # Ensure progress is between 0 and 1

                # Update status based on progress
                if skill_copy['progress'] >= 1.0:
                    skill_copy['status'] = 'Completed'
                elif skill_copy['progress'] > 0:
                    skill_copy['status'] = 'In Progress'

                # Update completed resources
                if completed_resources:
                    # Mark resources as completed
                    updated_resources = []
                    for resource in skill_copy.get('resources', []):
                        resource_copy = resource.copy()
                        resource_name = resource.get('name', '')
                        if resource_name in completed_resources:
                            resource_copy['completed'] = True
                        updated_resources.append(resource_copy)

                    skill_copy['resources'] = updated_resources

                updated_skills.append(skill_copy)
            else:
                updated_skills.append(skill.copy())

        updated_plan['skills'] = updated_skills

        # Update overall progress
        total_progress = sum(skill.get('progress', 0) for skill in updated_skills)
        overall_progress = total_progress / len(updated_skills) if updated_skills else 0
        updated_plan['overall_progress'] = overall_progress

        return updated_plan