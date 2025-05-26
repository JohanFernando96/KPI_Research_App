from datetime import datetime
from services.mongodb_service import mongodb_service
from modules.skill_recommendation.dynamic_role_analyzer import DynamicRoleAnalyzer
from bson import ObjectId


class SkillAcquisitionTracker:
    """
    Track skill acquisition and calculate employee scores.
    """

    @staticmethod
    def complete_course(employee_id, skill_name, course_details):
        """
        Mark a course/skill as completed and update employee profile.

        Args:
            employee_id: Employee ID
            skill_name: Name of the skill acquired
            course_details: Details about the completed course
        """
        try:
            # Get employee
            employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
            if not employee:
                return {'success': False, 'message': 'Employee not found'}

            # Update skills if not already present
            current_skills = employee.get('Skills', [])
            if skill_name not in current_skills:
                current_skills.append(skill_name)

            # Track skill acquisition history
            skill_history = employee.get('skill_acquisition_history', [])
            skill_history.append({
                'skill': skill_name,
                'acquired_date': datetime.now(),
                'course': course_details.get('course_name', ''),
                'provider': course_details.get('provider', ''),
                'certificate': course_details.get('certificate_url', ''),
                'duration': course_details.get('duration', ''),
                'verified': course_details.get('verified', False)
            })

            # Update proficiency tracking
            skill_proficiencies = employee.get('skill_proficiencies', {})
            current_proficiency = skill_proficiencies.get(skill_name, 0)

            # Increase proficiency based on course completion
            if course_details.get('verified'):
                proficiency_increase = 2  # Verified courses give more proficiency
            else:
                proficiency_increase = 1

            new_proficiency = min(5, current_proficiency + proficiency_increase)
            skill_proficiencies[skill_name] = new_proficiency

            # Calculate new employee score
            employee_score = SkillAcquisitionTracker.calculate_employee_score(
                employee, current_skills, skill_proficiencies
            )

            # Check promotion readiness
            promotion_analysis = SkillAcquisitionTracker.check_promotion_readiness(
                employee, current_skills, skill_proficiencies
            )

            # Update employee record
            update_data = {
                'Skills': current_skills,
                'skill_acquisition_history': skill_history,
                'skill_proficiencies': skill_proficiencies,
                'employee_score': employee_score,
                'promotion_readiness': promotion_analysis,
                'last_skill_update': datetime.now()
            }

            mongodb_service.update_one(
                'Resumes',
                {'_id': ObjectId(employee_id)},
                {'$set': update_data}
            )

            # Log achievement
            SkillAcquisitionTracker._log_achievement(employee_id, skill_name, employee_score)

            return {
                'success': True,
                'new_score': employee_score,
                'proficiency': new_proficiency,
                'promotion_readiness': promotion_analysis
            }

        except Exception as e:
            print(f"Error completing course: {e}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def calculate_employee_score(employee, skills, proficiencies):
        """
        Calculate comprehensive employee score.
        """
        score_components = {
            'skill_count': 0,
            'skill_proficiency': 0,
            'experience': 0,
            'certifications': 0,
            'continuous_learning': 0
        }

        # 1. Skill count score (max 20 points)
        skill_count = len(skills)
        score_components['skill_count'] = min(20, skill_count * 0.5)

        # 2. Skill proficiency score (max 30 points)
        if proficiencies:
            avg_proficiency = sum(proficiencies.values()) / len(proficiencies)
            score_components['skill_proficiency'] = (avg_proficiency / 5) * 30

        # 3. Experience score (max 25 points)
        experience_items = employee.get('Experience', [])
        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        years_exp = ExperienceAnalyzer.get_years_of_experience(experience_items)
        score_components['experience'] = min(25, years_exp * 2.5)

        # 4. Certifications score (max 15 points)
        certs = employee.get('Certifications and Courses', [])
        score_components['certifications'] = min(15, len(certs) * 3)

        # 5. Continuous learning score (max 10 points)
        skill_history = employee.get('skill_acquisition_history', [])
        recent_learning = [
            s for s in skill_history
            if (datetime.now() - s.get('acquired_date', datetime.min)).days < 180
        ]
        score_components['continuous_learning'] = min(10, len(recent_learning) * 2)

        # Calculate total score
        total_score = sum(score_components.values())

        # Store component breakdown
        employee['score_breakdown'] = score_components

        return round(total_score, 1)

    @staticmethod
    def check_promotion_readiness(employee, skills, proficiencies):
        """
        Check if employee is ready for promotion.
        """
        # Get current role and experience
        current_role = employee.get('current_role', {}).get('title', '')
        if not current_role and employee.get('Experience'):
            current_role = employee['Experience'][0].get('Role', '')

        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        years_exp = ExperienceAnalyzer.get_years_of_experience(employee.get('Experience', []))

        # Get next role requirements
        role_analysis = DynamicRoleAnalyzer.analyze_role_requirements(current_role)
        next_role = role_analysis.get('next_role', '')

        if not next_role:
            return {
                'ready': False,
                'reason': 'No clear progression path identified',
                'score': 0
            }

        # Analyze requirements for next role
        next_role_requirements = DynamicRoleAnalyzer.analyze_role_requirements(next_role)

        # Check skill match
        required_technical = next_role_requirements.get('technical_skills', [])
        required_soft = next_role_requirements.get('soft_skills', [])

        technical_match = 0
        soft_match = 0
        critical_missing = []

        # Check technical skills
        for req_skill in required_technical:
            skill_name = req_skill['name']
            min_proficiency = req_skill['min_proficiency']
            importance = req_skill.get('importance', 'medium')

            # Check if employee has the skill
            has_skill = any(skill.lower() == skill_name.lower() for skill in skills)
            skill_proficiency = proficiencies.get(skill_name, 0)

            if has_skill and skill_proficiency >= min_proficiency:
                technical_match += 1
            elif importance == 'critical':
                critical_missing.append(skill_name)

        # Check soft skills
        for req_skill in required_soft:
            skill_name = req_skill['name']
            has_skill = any(skill.lower() == skill_name.lower() for skill in skills)
            if has_skill:
                soft_match += 1

        # Calculate readiness score
        tech_score = (technical_match / len(required_technical) * 100) if required_technical else 100
        soft_score = (soft_match / len(required_soft) * 100) if required_soft else 100

        # Check experience requirement
        min_exp = next_role_requirements.get('min_experience', 0)
        exp_met = years_exp >= min_exp

        # Overall readiness
        readiness_score = (tech_score * 0.5 + soft_score * 0.3 + (100 if exp_met else 50) * 0.2)

        is_ready = readiness_score >= 80 and len(critical_missing) == 0 and exp_met

        return {
            'ready': is_ready,
            'score': round(readiness_score, 1),
            'next_role': next_role,
            'technical_readiness': round(tech_score, 1),
            'soft_skill_readiness': round(soft_score, 1),
            'experience_met': exp_met,
            'min_experience_required': min_exp,
            'critical_missing_skills': critical_missing,
            'recommendation': 'Ready for promotion' if is_ready else f'Continue developing: {", ".join(critical_missing[:3])}'
        }

    @staticmethod
    def _log_achievement(employee_id, skill_name, new_score):
        """
        Log skill achievements for gamification.
        """
        achievement = {
            'employee_id': employee_id,
            'type': 'skill_acquired',
            'skill': skill_name,
            'new_score': new_score,
            'timestamp': datetime.now(),
            'badge': SkillAcquisitionTracker._determine_badge(new_score)
        }

        mongodb_service.insert_one('Achievements', achievement)

    @staticmethod
    def _determine_badge(score):
        """
        Determine badge based on score.
        """
        if score >= 90:
            return 'Expert'
        elif score >= 75:
            return 'Advanced'
        elif score >= 60:
            return 'Proficient'
        elif score >= 40:
            return 'Intermediate'
        else:
            return 'Beginner'

    @staticmethod
    def get_promotion_worthy_employees():
        """
        Get all employees ready for promotion.
        """
        # Find employees with high promotion readiness
        employees = mongodb_service.find_many(
            'Resumes',
            {'promotion_readiness.ready': True},
            projection={
                'Name': 1,
                'current_role': 1,
                'employee_score': 1,
                'promotion_readiness': 1,
                'Skills': 1,
                'Experience': 1
            }
        )

        # Sort by readiness score
        employees.sort(
            key=lambda x: x.get('promotion_readiness', {}).get('score', 0),
            reverse=True
        )

        return employees