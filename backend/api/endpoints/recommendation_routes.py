from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
import json
from datetime import datetime

from services.mongodb_service import mongodb_service
from services.openai_service import openai_service
from modules.skill_recommendation.skill_gap_analyzer import SkillGapAnalyzer
from modules.skill_recommendation.role_hierarchy import RoleHierarchy
from modules.skill_recommendation.training_recommender import TrainingRecommender
from modules.skill_recommendation.progress_tracker import ProgressTracker
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
from utils.error_handlers import ValidationError, NotFoundError

recommendation_blueprint = Blueprint('recommendations', __name__)


from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
import json
from datetime import datetime

from services.mongodb_service import mongodb_service
from services.openai_service import openai_service
from modules.skill_recommendation.skill_gap_analyzer import SkillGapAnalyzer
from modules.skill_recommendation.role_hierarchy import RoleHierarchy
from modules.skill_recommendation.training_recommender import TrainingRecommender
from modules.skill_recommendation.progress_tracker import ProgressTracker
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
from utils.error_handlers import ValidationError, NotFoundError

recommendation_blueprint = Blueprint('recommendations', __name__)


@recommendation_blueprint.route('/employees/<employee_id>/skill-gap', methods=['POST'])
def analyze_employee_skill_gap(employee_id):
    """
    Endpoint for analyzing an employee's skill gap against a role or project.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Get employee skills
        employee_skills = employee.get('Skills', [])

        # Determine the type of analysis
        analysis_type = data.get('analysis_type', 'role')

        if analysis_type == 'role':
            # Role-based skill gap analysis
            role_name = data.get('role_name')

            if not role_name:
                return jsonify({
                    'success': False,
                    'message': "Role name is required for role-based analysis"
                }), 400

            # Analyze skill gap for the role
            analysis = SkillGapAnalyzer.analyze_role_skill_gap(employee_skills, role_name)

        elif analysis_type == 'project':
            # Project-based skill gap analysis
            project_skills = data.get('project_skills', [])

            if not project_skills:
                return jsonify({
                    'success': False,
                    'message': "Project skills are required for project-based analysis"
                }), 400

            # Analyze skill gap for the project
            analysis = SkillGapAnalyzer.analyze_project_skill_gap(employee_skills, project_skills)

        elif analysis_type == 'career':
            # Career progression analysis
            current_role = data.get('current_role')

            if not current_role:
                # If current role not provided, determine it from experience
                experience_items = employee.get('Experience', [])
                experience_years = ExperienceAnalyzer.get_years_of_experience(experience_items)
                current_role = RoleHierarchy.find_matching_role(employee_skills, experience_years)
            else:
                # Calculate years of experience
                experience_items = employee.get('Experience', [])
                experience_years = ExperienceAnalyzer.get_years_of_experience(experience_items)

            # Analyze career progression
            analysis = SkillGapAnalyzer.analyze_career_progression(
                employee_skills,
                current_role,
                experience_years
            )

        else:
            return jsonify({
                'success': False,
                'message': f"Invalid analysis type: {analysis_type}"
            }), 400

        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'analysis_type': analysis_type,
            'analysis': analysis
        })

    except NotFoundError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 404
    except ValidationError as e:
        # Fix the recursion error by converting the exception to a string directly
        # instead of relying on str(e) which might cause recursion
        return jsonify({
            'success': False,
            'message': "Validation error: " + (e.args[0] if e.args else "Unknown validation error")
        }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error analyzing skill gap: {type(e).__name__}: {str(e) if hasattr(e, '__str__') else repr(e)}"
        }), 500


@recommendation_blueprint.route('/employees/<employee_id>/recommend-training', methods=['POST'])
@recommendation_blueprint.route('/employees/<employee_id>/recommend-training', methods=['POST'])
def recommend_employee_training(employee_id):
    """
    Endpoint for recommending training resources for an employee.
    """
    try:
        data = request.json

        if not data:
            return jsonify({
                'success': False,
                'message': "No data provided"
            }), 400

        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            return jsonify({
                'success': False,
                'message': f"Employee with ID {employee_id} not found"
            }), 404

        # Get employee skills
        employee_skills = employee.get('Skills', [])

        # Determine the type of recommendation
        recommendation_type = data.get('recommendation_type', 'career')

        if recommendation_type == 'skill_gaps':
            # Recommendations based on specific skill gaps
            skill_gaps = data.get('skill_gaps', [])

            if not skill_gaps:
                # Return empty recommendations instead of error
                return jsonify({
                    'success': True,
                    'employee_id': employee_id,
                    'recommendation_type': recommendation_type,
                    'recommendations': {},
                    'message': 'No skill gaps identified'
                })

            # Get recommendations for skill gaps
            recommendations = TrainingRecommender.recommend_for_skill_gaps(skill_gaps)

        elif recommendation_type == 'project':
            # Recommendations based on project requirements
            project_skills = data.get('project_skills', [])

            if not project_skills:
                return jsonify({
                    'success': False,
                    'message': "Project skills are required for project-based recommendations"
                }), 400

            # Analyze project skill gap
            project_analysis = SkillGapAnalyzer.analyze_project_skill_gap(employee_skills, project_skills)

            # Get recommendations for project skill gap
            recommendations = TrainingRecommender.recommend_for_project(project_analysis)

        elif recommendation_type == 'career':
            # Recommendations for career progression
            current_role = data.get('current_role')

            if not current_role:
                # If current role not provided, determine it from experience
                experience_items = employee.get('Experience', [])
                if experience_items:
                    current_role = experience_items[0].get('Role', 'Unknown')
                else:
                    current_role = 'Unknown'

            # Calculate years of experience
            experience_items = employee.get('Experience', [])
            experience_years = ExperienceAnalyzer.get_years_of_experience(experience_items)

            # Analyze career progression
            progression_analysis = SkillGapAnalyzer.analyze_career_progression(
                employee_skills,
                current_role,
                experience_years
            )

            # Get recommendations for career progression
            recommendations = TrainingRecommender.recommend_for_career_progression(progression_analysis)

        else:
            return jsonify({
                'success': False,
                'message': f"Invalid recommendation type: {recommendation_type}"
            }), 400

        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'recommendation_type': recommendation_type,
            'recommendations': recommendations
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f"Error recommending training: {str(e)}"
        }), 500

@recommendation_blueprint.route('/employees/<employee_id>/development-plan', methods=['POST'])
def create_development_plan(employee_id):
    """
    Endpoint for creating a skill development plan for an employee.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Get required data
        skill_gaps = data.get('skill_gaps', [])
        recommended_resources = data.get('recommended_resources', {})
        deadline_str = data.get('deadline')

        # Parse deadline if provided
        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str)
            except ValueError:
                raise ValidationError(f"Invalid deadline format: {deadline_str}")

        # Create development plan
        development_plan = ProgressTracker.create_skill_development_plan(
            skill_gaps,
            recommended_resources,
            deadline
        )

        # Add metadata to the plan
        development_plan['employee_id'] = employee_id
        development_plan['created_at'] = datetime.now()
        development_plan['overall_progress'] = 0.0

        # Store the development plan in MongoDB
        plan_id = mongodb_service.insert_one('DevelopmentPlans', development_plan)

        # Update employee with reference to the development plan
        mongodb_service.update_one(
            'Resumes',
            {'_id': object_id},
            {'$push': {'development_plans': plan_id}}
        )

        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'plan_id': str(plan_id),
            'development_plan': development_plan
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error creating development plan: {str(e)}"
        }), 500


@recommendation_blueprint.route('/employees/<employee_id>/development-plan/<plan_id>', methods=['GET'])
def get_development_plan(employee_id, plan_id):
    """
    Endpoint for retrieving a skill development plan.
    """
    try:
        # Convert string IDs to ObjectIds
        employee_object_id = ObjectId(employee_id)
        plan_object_id = ObjectId(plan_id)

        # Retrieve the development plan from MongoDB
        development_plan = mongodb_service.find_one('DevelopmentPlans', {'_id': plan_object_id})

        if not development_plan:
            raise NotFoundError(f"Development plan with ID {plan_id} not found")

        # Check if the plan belongs to the employee
        if development_plan.get('employee_id') != employee_id:
            raise ValidationError("Development plan does not belong to the specified employee")

        # Convert ObjectId to string for JSON serialization
        development_plan['_id'] = str(development_plan['_id'])

        # Convert datetime objects to strings
        for key in ['start_date', 'end_date', 'created_at']:
            if key in development_plan and isinstance(development_plan[key], datetime):
                development_plan[key] = development_plan[key].isoformat()

        # Convert datetime objects in skills
        for skill in development_plan.get('skills', []):
            for key in ['start_date', 'target_date']:
                if key in skill and isinstance(skill[key], datetime):
                    skill[key] = skill[key].isoformat()

        return jsonify({
            'success': True,
            'development_plan': development_plan
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving development plan: {str(e)}"
        }), 500


@recommendation_blueprint.route('/employees/<employee_id>/development-plan/<plan_id>/track-progress', methods=['POST'])
def track_development_progress(employee_id, plan_id):
    """
    Endpoint for tracking progress in a skill development plan.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string IDs to ObjectIds
        employee_object_id = ObjectId(employee_id)
        plan_object_id = ObjectId(plan_id)

        # Retrieve the development plan from MongoDB
        development_plan = mongodb_service.find_one('DevelopmentPlans', {'_id': plan_object_id})

        if not development_plan:
            raise NotFoundError(f"Development plan with ID {plan_id} not found")

        # Check if the plan belongs to the employee
        if development_plan.get('employee_id') != employee_id:
            raise ValidationError("Development plan does not belong to the specified employee")

        # Get update data
        skill_name = data.get('skill_name')
        progress = data.get('progress')
        completed_resources = data.get('completed_resources', [])

        if not skill_name or progress is None:
            raise ValidationError("Skill name and progress are required")

        # Update progress
        updated_plan = ProgressTracker.update_progress(
            development_plan,
            skill_name,
            progress,
            completed_resources
        )

        # Update the development plan in MongoDB
        mongodb_service.update_one(
            'DevelopmentPlans',
            {'_id': plan_object_id},
            {'$set': updated_plan}
        )

        # Convert ObjectId to string for JSON serialization
        updated_plan['_id'] = str(updated_plan['_id'])

        # Convert datetime objects to strings
        for key in ['start_date', 'end_date', 'created_at']:
            if key in updated_plan and isinstance(updated_plan[key], datetime):
                updated_plan[key] = updated_plan[key].isoformat()

        # Convert datetime objects in skills
        for skill in updated_plan.get('skills', []):
            for key in ['start_date', 'target_date']:
                if key in skill and isinstance(skill[key], datetime):
                    skill[key] = skill[key].isoformat()

        return jsonify({
            'success': True,
            'message': f"Progress updated for {skill_name}",
            'updated_plan': updated_plan
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error tracking progress: {str(e)}"
        }), 500


@recommendation_blueprint.route('/job-roles', methods=['GET'])
def get_job_roles():
    """
    Endpoint for retrieving all job roles in the hierarchy.
    """
    try:
        # Get the role hierarchy
        role_hierarchy = RoleHierarchy.get_role_hierarchy()

        # Prepare response data
        roles = []
        for role_name, role_data in role_hierarchy.items():
            roles.append({
                'name': role_name,
                'level': role_data.get('level', 0),
                'min_experience': role_data.get('min_experience', 0),
                'next_role': role_data.get('next_role')
            })

        # Sort roles by level
        roles.sort(key=lambda x: x['level'])

        return jsonify({
            'success': True,
            'roles': roles
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving job roles: {str(e)}"
        }), 500


@recommendation_blueprint.route('/job-roles/<role_name>', methods=['GET'])
def get_job_role(role_name):
    """
    Endpoint for retrieving details of a specific job role.
    """
    try:
        # Get the role data
        role_data = RoleHierarchy.get_role_hierarchy(role_name)

        if not role_data:
            raise NotFoundError(f"Job role '{role_name}' not found")

        return jsonify({
            'success': True,
            'role': {
                'name': role_name,
                'level': role_data.get('level', 0),
                'min_experience': role_data.get('min_experience', 0),
                'next_role': role_data.get('next_role'),
                'required_skills': role_data.get('required_skills', {})
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving job role: {str(e)}"
        }), 500

@recommendation_blueprint.route('/employees/<employee_id>/development-plans', methods=['GET'])
def get_employee_development_plans(employee_id):
    """
    Get all development plans for an employee.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Find all development plans for this employee
        development_plans = mongodb_service.find_many(
            'DevelopmentPlans',
            {'employee_id': employee_id},
            sort=[('created_at', -1)]  # Sort by newest first
        )

        # Convert ObjectIds and dates to strings
        for plan in development_plans:
            plan['_id'] = str(plan['_id'])
            plan['id'] = str(plan['_id'])  # Add id field for frontend

            # Convert datetime objects
            for key in ['start_date', 'end_date', 'created_at']:
                if key in plan and isinstance(plan[key], datetime):
                    plan[key] = plan[key].isoformat()

            # Convert dates in skills
            for skill in plan.get('skills', []):
                for key in ['start_date', 'target_date']:
                    if key in skill and isinstance(skill[key], datetime):
                        skill[key] = skill[key].isoformat()

        return jsonify({
            'success': True,
            'plans': development_plans
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving development plans: {str(e)}"
        }), 500