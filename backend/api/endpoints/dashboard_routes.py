from flask import Blueprint, jsonify
from services.mongodb_service import mongodb_service
from modules.skill_recommendation.skill_acquisition_tracker import SkillAcquisitionTracker
from datetime import datetime, timedelta

dashboard_blueprint = Blueprint('dashboard', __name__)


@dashboard_blueprint.route('/promotion-insights', methods=['GET'])
def get_promotion_insights():
    """
    Get dashboard data for promotion-worthy employees.
    """
    try:
        # Get promotion-worthy employees
        promotion_ready = SkillAcquisitionTracker.get_promotion_worthy_employees()

        # Get recent skill acquisitions
        recent_achievements = mongodb_service.find_many(
            'Achievements',
            {
                'timestamp': {'$gte': datetime.now() - timedelta(days=30)},
                'type': 'skill_acquired'
            },
            sort=[('timestamp', -1)],
            limit=10
        )

        # Get top performers by score
        top_performers = mongodb_service.find_many(
            'Resumes',
            {'employee_score': {'$exists': True}},
            projection={
                'Name': 1,
                'employee_score': 1,
                'current_role': 1,
                'Skills': 1
            },
            sort=[('employee_score', -1)],
            limit=10
        )

        # Calculate statistics
        total_employees = mongodb_service.find_many('Resumes', {}).count()
        promotion_ready_count = len(promotion_ready)
        promotion_rate = (promotion_ready_count / total_employees * 100) if total_employees > 0 else 0

        # Format response
        for emp in promotion_ready:
            emp['_id'] = str(emp['_id'])

        for emp in top_performers:
            emp['_id'] = str(emp['_id'])

        for achievement in recent_achievements:
            achievement['_id'] = str(achievement['_id'])
            achievement['employee_id'] = str(achievement['employee_id'])

        return jsonify({
            'success': True,
            'promotion_insights': {
                'promotion_ready_employees': promotion_ready[:10],  # Top 10
                'total_promotion_ready': promotion_ready_count,
                'promotion_readiness_rate': round(promotion_rate, 1),
                'recent_skill_acquisitions': recent_achievements,
                'top_performers': top_performers
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting promotion insights: {str(e)}"
        }), 500


@dashboard_blueprint.route('/skill-development-metrics', methods=['GET'])
def get_skill_development_metrics():
    """
    Get organization-wide skill development metrics.
    """
    try:
        # Get all employees with skill history
        employees_with_history = mongodb_service.find_many(
            'Resumes',
            {'skill_acquisition_history': {'$exists': True, '$ne': []}}
        )

        # Calculate metrics
        total_skills_acquired = 0
        active_learners = 0
        skill_frequency = {}

        for emp in employees_with_history:
            history = emp.get('skill_acquisition_history', [])
            total_skills_acquired += len(history)

            # Check if active learner (acquired skill in last 90 days)
            recent_learning = any(
                (datetime.now() - item.get('acquired_date', datetime.min)).days < 90
                for item in history
            )
            if recent_learning:
                active_learners += 1

            # Track skill frequency
            for item in history:
                skill = item.get('skill', '')
                skill_frequency[skill] = skill_frequency.get(skill, 0) + 1

        # Get top trending skills
        trending_skills = sorted(
            skill_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Calculate learning velocity (skills per month)
        if employees_with_history:
            avg_skills_per_employee = total_skills_acquired / len(employees_with_history)
        else:
            avg_skills_per_employee = 0

        return jsonify({
            'success': True,
            'metrics': {
                'total_skills_acquired': total_skills_acquired,
                'active_learners': active_learners,
                'average_skills_per_employee': round(avg_skills_per_employee, 1),
                'trending_skills': [
                    {'skill': skill, 'count': count}
                    for skill, count in trending_skills
                ]
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting skill metrics: {str(e)}"
        }), 500