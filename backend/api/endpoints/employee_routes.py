from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
import json

from services.mongodb_service import mongodb_service
from services.openai_service import openai_service
from modules.employee_matching.candidate_ranker import CandidateRanker
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
from utils.error_handlers import ValidationError, NotFoundError

employee_blueprint = Blueprint('employees', __name__)


@employee_blueprint.route('', methods=['GET'])
def get_all_employees():
    """
    Endpoint for retrieving all employees from the database.
    """
    try:
        # Get all employees from MongoDB
        employees = mongodb_service.find_many('Resumes')

        # Convert ObjectId to string for JSON serialization
        for employee in employees:
            employee['_id'] = str(employee['_id'])

        return jsonify({
            'success': True,
            'total': len(employees),
            'data': employees
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving employees: {str(e)}"
        }), 500


@employee_blueprint.route('/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    """
    Endpoint for retrieving an employee by ID.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Convert ObjectId to string for JSON serialization
        employee['_id'] = str(employee['_id'])

        return jsonify({
            'success': True,
            'data': employee
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving employee: {str(e)}"
        }), 500


@employee_blueprint.route('/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """
    Endpoint for updating an employee's information.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Check if employee exists
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Remove _id from the update data if present
        if '_id' in data:
            del data['_id']

        # Update the employee in MongoDB
        result = mongodb_service.update_one('Resumes', {'_id': object_id}, {'$set': data})

        return jsonify({
            'success': True,
            'message': f"Employee updated successfully",
            'modified_count': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error updating employee: {str(e)}"
        }), 500


@employee_blueprint.route('/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """
    Endpoint for deleting an employee.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Check if employee exists
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Delete the employee from MongoDB
        result = mongodb_service.delete_one('Resumes', {'_id': object_id})

        return jsonify({
            'success': True,
            'message': f"Employee deleted successfully",
            'deleted_count': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error deleting employee: {str(e)}"
        }), 500


@employee_blueprint.route('/<employee_id>/skills', methods=['GET'])
def get_employee_skills(employee_id):
    """
    Endpoint for retrieving an employee's skills breakdown.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Get skills
        skills = employee.get('Skills', [])

        # Get derived skill categories if available
        skill_categories = employee.get('_derived', {}).get('skill_categories', {})

        # If no derived skill categories, create them
        if not skill_categories:
            programming_keywords = ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php']
            framework_keywords = ['react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel']
            database_keywords = ['sql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'nosql']

            skill_categories = {
                'programming': [],
                'frameworks': [],
                'databases': [],
                'other': []
            }

            for skill in skills:
                skill_lower = skill.lower()
                if any(keyword in skill_lower for keyword in programming_keywords):
                    skill_categories['programming'].append(skill)
                elif any(keyword in skill_lower for keyword in framework_keywords):
                    skill_categories['frameworks'].append(skill)
                elif any(keyword in skill_lower for keyword in database_keywords):
                    skill_categories['databases'].append(skill)
                else:
                    skill_categories['other'].append(skill)

        # Prepare response
        skills_breakdown = {
            'total_skills': len(skills),
            'skills': skills,
            'categories': skill_categories
        }

        return jsonify({
            'success': True,
            'data': skills_breakdown
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving employee skills: {str(e)}"
        }), 500


@employee_blueprint.route('/match', methods=['POST'])
def match_employees():
    """
    Endpoint for matching employees to project criteria.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Extract project criteria
        project_criteria = data.get('project_criteria', {})

        if not project_criteria:
            raise ValidationError("No project criteria provided")

        # Get the number of employees to match
        people_count = int(project_criteria.get('people_count', 1))

        # Get all employees from MongoDB
        employees = mongodb_service.find_many('Resumes')

        # Filter employees by experience if field is specified
        if 'field' in project_criteria and project_criteria['field']:
            filtered_employees = []

            for employee in employees:
                experience_items = employee.get('Experience', [])
                has_relevant_exp, _, _ = ExperienceAnalyzer.has_relevant_experience(
                    experience_items, project_criteria['field']
                )

                if has_relevant_exp:
                    filtered_employees.append(employee)

            employees = filtered_employees

        # Rank the candidates
        ranked_candidates = CandidateRanker.rank_candidates(employees, project_criteria)

        # Select the top N candidates
        top_candidates = CandidateRanker.select_best_candidates(ranked_candidates, count=people_count)

        # Prepare response
        matched_employees = []

        for candidate_data in top_candidates:
            candidate = candidate_data['candidate']
            scores = candidate_data['scores']
            total_score = candidate_data['total_score']

            # Convert ObjectId to string
            candidate['_id'] = str(candidate['_id'])

            # Get skill gap
            candidate_skills = candidate.get('Skills', [])
            project_languages = project_criteria.get('languages', '').split(',') if isinstance(
                project_criteria.get('languages'), str) else project_criteria.get('languages', [])
            skill_gap = SkillMatcher.get_skill_gap(candidate_skills, project_languages)

            matched_employees.append({
                'employee': candidate,
                'scores': scores,
                'total_score': total_score,
                'skill_gap': skill_gap
            })

        return jsonify({
            'success': True,
            'matched_employees': matched_employees,
            'total_candidates': len(employees),
            'total_matches': len(matched_employees)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error matching employees: {str(e)}"
        }), 500


@employee_blueprint.route('/<employee_id>/career-path', methods=['GET'])
def get_career_path(employee_id):
    """
    Endpoint for retrieving an employee's career progression information.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(employee_id)

        # Retrieve the employee from MongoDB
        employee = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Get career progression information
        experience_items = employee.get('Experience', [])
        years_experience = ExperienceAnalyzer.get_years_of_experience(experience_items)
        experience_level = ExperienceAnalyzer.get_experience_level(years_experience)

        # Get current role from most recent experience
        current_role = None
        if experience_items:
            # Assuming the first experience item is the most recent
            current_role = experience_items[0].get('Role', 'Unknown')

        # Create career progression data
        career_progression = {
            'current_role': current_role,
            'years_experience': years_experience,
            'experience_level': experience_level,
            'next_level': 'Senior' if experience_level == 'Mid-level' else 'Lead' if experience_level == 'Senior' else 'Architect' if experience_level == 'Lead' else 'Mid-level',
            'skills_to_improve': []  # This would be populated by the skill recommendation module
        }

        return jsonify({
            'success': True,
            'data': career_progression
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving career path: {str(e)}"
        }), 500


@employee_blueprint.route('/match-with-kpis', methods=['POST'])
def match_employees_with_kpis():
    """
    Endpoint for matching employees to project criteria with specialized KPIs.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Extract project criteria
        project_criteria = data.get('project_criteria', {})
        project_kpis = data.get('project_kpis', {})
        role_criteria = data.get('role_criteria', {})

        if not project_criteria:
            raise ValidationError("No project criteria provided")

        # Get the number of employees to match
        people_count = int(project_criteria.get('people_count', 5))

        # Get all employees from MongoDB
        employees = mongodb_service.find_many('Resumes')

        # Import candidate ranker here to avoid circular imports
        from modules.employee_matching.candidate_ranker import CandidateRanker
        from modules.employee_matching.skill_matcher import SkillMatcher
        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        from modules.kpi_generation.individual_kpi_generator import IndividualKPIGenerator

        # Rank all candidates - include even those with partial matches
        ranked_candidates = CandidateRanker.rank_candidates(
            employees, project_criteria, include_all_matches=True
        )

        # Select the top N candidates
        top_candidates = CandidateRanker.select_best_candidates(ranked_candidates, count=people_count)

        # Prepare response
        matched_employees = []

        for candidate_data in top_candidates:
            candidate = candidate_data['candidate']
            scores = candidate_data['scores']
            total_score = candidate_data['total_score']
            compatibility_percentage = candidate_data.get('compatibility_percentage', 0)

            # Convert ObjectId to string
            candidate['_id'] = str(candidate['_id'])

            # Get skill gap and compatibility details
            candidate_skills = candidate.get('Skills', [])
            project_languages = project_criteria.get('languages', '').split(',') if isinstance(
                project_criteria.get('languages'), str) else project_criteria.get('languages', [])
            skill_compatibility = SkillMatcher.calculate_skill_compatibility(candidate_skills, project_languages)

            # Generate specialized KPIs if project KPIs are provided
            specialized_kpis = None
            if project_kpis and role_criteria:
                specialized_kpis = IndividualKPIGenerator.generate_individual_kpis(
                    project_kpis, role_criteria, candidate
                )

            matched_employees.append({
                'employee': candidate,
                'scores': scores,
                'total_score': total_score,
                'compatibility_percentage': compatibility_percentage,
                'skill_compatibility': skill_compatibility,
                'specialized_kpis': specialized_kpis
            })

        return jsonify({
            'success': True,
            'matched_employees': matched_employees,
            'total_candidates': len(employees),
            'total_matches': len(matched_employees)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error matching employees: {str(e)}"
        }), 500