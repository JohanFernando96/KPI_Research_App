from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from datetime import datetime

from services.mongodb_service import mongodb_service
from modules.skill_recommendation.dynamic_role_analyzer import DynamicRoleAnalyzer
from modules.skill_recommendation.resource_finder import ResourceFinder
from modules.skill_recommendation.skill_acquisition_tracker import SkillAcquisitionTracker
from utils.error_handlers import ValidationError, NotFoundError

skill_development_blueprint = Blueprint('skill_development', __name__)


@skill_development_blueprint.route('/analyze-role/<role_name>', methods=['GET'])
def analyze_role_requirements(role_name):
    """
    Dynamically analyze role requirements using AI.
    """
    try:
        industry = request.args.get('industry', 'Software Development')

        # Get dynamic role analysis
        role_analysis = DynamicRoleAnalyzer.analyze_role_requirements(role_name, industry)

        if not role_analysis:
            return jsonify({
                'success': False,
                'message': 'Could not analyze role'
            }), 400

        return jsonify({
            'success': True,
            'role_analysis': role_analysis
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error analyzing role: {str(e)}"
        }), 500


@skill_development_blueprint.route('/career-path/<employee_id>', methods=['GET'])
def get_personalized_career_path(employee_id):
    """
    Get personalized career path for an employee.
    """
    try:
        # Get employee
        employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
        if not employee:
            raise NotFoundError(f"Employee {employee_id} not found")

        # Get current role and experience
        current_role = employee.get('current_role', {}).get('title', '')
        if not current_role and employee.get('Experience'):
            current_role = employee['Experience'][0].get('Role', '')

        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        years_exp = ExperienceAnalyzer.get_years_of_experience(employee.get('Experience', []))

        skills = employee.get('Skills', [])

        # Get personalized career path
        career_path = DynamicRoleAnalyzer.determine_career_path(
            current_role, years_exp, skills
        )

        return jsonify({
            'success': True,
            'career_path': career_path,
            'current_role': current_role,
            'years_experience': years_exp
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting career path: {str(e)}"
        }), 500


@skill_development_blueprint.route('/find-resources', methods=['POST'])
def find_learning_resources():
    """
    Find learning resources for a skill using web scraping and AI.
    """
    try:
        data = request.json
        skill_name = data.get('skill_name')
        skill_level = data.get('skill_level', 'beginner')

        if not skill_name:
            raise ValidationError("Skill name is required")

        # Check cache first
        cached = mongodb_service.find_one(
            'LearningResources',
            {'skill': skill_name, 'level': skill_level}
        )

        if cached and (datetime.now() - cached.get('updated_at', datetime.min)).days < 7:
            resources = cached.get('resources', [])
        else:
            # Find new resources
            resources = ResourceFinder.find_learning_resources(skill_name, skill_level)

        return jsonify({
            'success': True,
            'skill': skill_name,
            'level': skill_level,
            'resources': resources
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error finding resources: {str(e)}"
        }), 500


@skill_development_blueprint.route('/complete-course', methods=['POST'])
def complete_course():
    """
    Mark a course as completed and update employee skills.
    """
    try:
        data = request.json

        employee_id = data.get('employee_id')
        skill_name = data.get('skill_name')
        course_details = data.get('course_details', {})

        if not employee_id or not skill_name:
            raise ValidationError("Employee ID and skill name are required")

        # Track course completion
        result = SkillAcquisitionTracker.complete_course(
            employee_id, skill_name, course_details
        )

        if not result['success']:
            return jsonify(result), 400

        return jsonify({
            'success': True,
            'message': 'Course completed successfully',
            'new_score': result['new_score'],
            'skill_proficiency': result['proficiency'],
            'promotion_readiness': result['promotion_readiness']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error completing course: {str(e)}"
        }), 500


@skill_development_blueprint.route('/promotion-worthy', methods=['GET'])
def get_promotion_worthy_employees():
    """
    Get all employees ready for promotion.
    """
    try:
        employees = SkillAcquisitionTracker.get_promotion_worthy_employees()

        # Convert ObjectIds to strings
        for emp in employees:
            emp['_id'] = str(emp['_id'])

        return jsonify({
            'success': True,
            'total': len(employees),
            'employees': employees
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting promotion-worthy employees: {str(e)}"
        }), 500


@skill_development_blueprint.route('/employee-score/<employee_id>', methods=['GET'])
def get_employee_score(employee_id):
    """
    Get detailed employee score and breakdown.
    """
    try:
        employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
        if not employee:
            raise NotFoundError(f"Employee {employee_id} not found")

        # Recalculate score to ensure it's up to date
        skills = employee.get('Skills', [])
        proficiencies = employee.get('skill_proficiencies', {})

        score = SkillAcquisitionTracker.calculate_employee_score(
            employee, skills, proficiencies
        )

        # Get score breakdown
        breakdown = employee.get('score_breakdown', {})

        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'total_score': score,
            'score_breakdown': breakdown,
            'badge': SkillAcquisitionTracker._determine_badge(score)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting employee score: {str(e)}"
        }), 500


@skill_development_blueprint.route('/skill-recommendations/<employee_id>', methods=['GET'])
def get_skill_recommendations(employee_id):
    """
    Get personalized skill recommendations for career growth.
    """
    try:
        employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
        if not employee:
            raise NotFoundError(f"Employee {employee_id} not found")

        # Get career path analysis
        current_role = employee.get('current_role', {}).get('title', '')
        if not current_role and employee.get('Experience'):
            current_role = employee['Experience'][0].get('Role', '')

        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        years_exp = ExperienceAnalyzer.get_years_of_experience(employee.get('Experience', []))
        skills = employee.get('Skills', [])

        # Get career path
        career_path = DynamicRoleAnalyzer.determine_career_path(
            current_role, years_exp, skills
        )

        # Get skill gaps for next role
        next_role = career_path.get('next_role', {})
        skill_gaps = next_role.get('skill_gaps', [])

        # Find resources for each skill gap
        recommendations = []
        for skill in skill_gaps[:5]:  # Top 5 skills to focus on
            resources = ResourceFinder.find_learning_resources(skill, 'beginner')
            recommendations.append({
                'skill': skill,
                'priority': 'High' if skill in next_role.get('required_skills', [])[:3] else 'Medium',
                'resources': resources[:3]  # Top 3 resources per skill
            })

        return jsonify({
            'success': True,
            'current_role': current_role,
            'next_role': next_role.get('title', ''),
            'readiness_score': career_path.get('readiness_for_next_level', 0),
            'skill_recommendations': recommendations
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error getting recommendations: {str(e)}"
        }), 500