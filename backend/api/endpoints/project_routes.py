from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
import json
from datetime import datetime

from services.mongodb_service import mongodb_service
from utils.error_handlers import ValidationError, NotFoundError

project_blueprint = Blueprint('projects', __name__)


@project_blueprint.route('', methods=['POST'])
def create_project():
    """
    Endpoint for creating a new project.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Required fields
        required_fields = ['name', 'project_type', 'project_timeline', 'project_team_size']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

        # Add created_at timestamp
        data['created_at'] = datetime.now()

        # Add status if not provided
        if 'status' not in data:
            data['status'] = 'Planning'

        # Insert project into MongoDB
        project_id = mongodb_service.insert_one('Projects', data)

        return jsonify({
            'success': True,
            'message': "Project created successfully",
            'project_id': str(project_id)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error creating project: {str(e)}"
        }), 500


@project_blueprint.route('', methods=['GET'])
def get_all_projects():
    """
    Endpoint for retrieving all projects.
    """
    try:
        # Get all projects from MongoDB
        projects = mongodb_service.find_many('Projects')

        # Convert ObjectId to string for JSON serialization
        for project in projects:
            project['_id'] = str(project['_id'])
            if 'kpi_id' in project and project['kpi_id']:
                project['kpi_id'] = str(project['kpi_id'])

        return jsonify({
            'success': True,
            'total': len(projects),
            'data': projects
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving projects: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>', methods=['GET'])
def get_project(project_id):
    """
    Endpoint for retrieving a project by ID.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Retrieve the project from MongoDB
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Convert ObjectId to string for JSON serialization
        project['_id'] = str(project['_id'])
        if 'kpi_id' in project and project['kpi_id']:
            project['kpi_id'] = str(project['kpi_id'])

        return jsonify({
            'success': True,
            'data': project
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving project: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>', methods=['PUT'])
def update_project(project_id):
    """
    Endpoint for updating a project.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Remove _id from the update data if present
        if '_id' in data:
            del data['_id']

        # Add updated_at timestamp
        data['updated_at'] = datetime.now()

        # Update the project in MongoDB
        result = mongodb_service.update_one('Projects', {'_id': object_id}, {'$set': data})

        return jsonify({
            'success': True,
            'message': f"Project updated successfully",
            'modified_count': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error updating project: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>', methods=['DELETE'])
def delete_project(project_id):
    """
    Endpoint for deleting a project.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Delete any related KPIs
        if 'kpi_id' in project and project['kpi_id']:
            mongodb_service.delete_one('ProjectKPIs', {'_id': project['kpi_id']})

        # Delete the project from MongoDB
        result = mongodb_service.delete_one('Projects', {'_id': object_id})

        return jsonify({
            'success': True,
            'message': f"Project deleted successfully",
            'deleted_count': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error deleting project: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>/team', methods=['GET'])
def get_project_team(project_id):
    """
    Endpoint for retrieving a project's team composition.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get team composition from project
        team = project.get('team', {})

        # If team has employee_ids, fetch employee details
        if 'employee_ids' in team and team['employee_ids']:
            employee_ids = team['employee_ids']

            # Convert string IDs to ObjectIds
            object_ids = [ObjectId(id) for id in employee_ids]

            # Fetch employees from MongoDB
            employees = mongodb_service.find_many('Resumes', {'_id': {'$in': object_ids}})

            # Convert ObjectId to string for JSON serialization
            for employee in employees:
                employee['_id'] = str(employee['_id'])

            team['employees'] = employees

        return jsonify({
            'success': True,
            'data': team
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving project team: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>/match-employees', methods=['POST'])
def match_employees_to_project(project_id):
    """
    Endpoint for matching employees to a project.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get all employees from MongoDB
        employees = mongodb_service.find_many('Resumes')

        # Get project criteria
        project_criteria = {
            'languages': project.get('project_languages', ''),
            'field': project.get('project_type', 'Software Development'),
            'people_count': project.get('project_team_size', 1),
            'project_type': project.get('project_type', 'Software Development')
        }

        # Import candidate ranker here to avoid circular imports
        from modules.employee_matching.candidate_ranker import CandidateRanker
        from modules.employee_matching.skill_matcher import SkillMatcher
        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer

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
        people_count = int(project_criteria.get('people_count', 1))
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
            project_languages = project_criteria.get('languages', '').split(',') if isinstance(project_criteria.get('languages'), str) else project_criteria.get('languages', [])
            skill_gap = SkillMatcher.get_skill_gap(candidate_skills, project_languages)

            matched_employees.append({
                'employee': candidate,
                'scores': scores,
                'total_score': total_score,
                'skill_gap': skill_gap
            })

        # Update project with matched employees
        employee_ids = [candidate_data['employee']['_id'] for candidate_data in matched_employees]

        # Update the project in MongoDB
        mongodb_service.update_one(
            'Projects',
            {'_id': object_id},
            {'$set': {
                'team': {
                    'employee_ids': employee_ids,
                    'updated_at': datetime.now()
                }
            }}
        )

        return jsonify({
            'success': True,
            'matched_employees': matched_employees,
            'total_candidates': len(employees),
            'total_matches': len(matched_employees)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error matching employees to project: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>/team/add-employee', methods=['POST'])
def add_employee_to_team(project_id):
    """
    Endpoint for adding an employee to a specific team role.
    """
    try:
        data = request.json
        print(f"Received data for add_employee_to_team: {data}")

        if not data:
            return jsonify({
                'success': False,
                'message': "No data provided"
            }), 400

        if 'employeeId' not in data:
            return jsonify({
                'success': False,
                'message': "Missing employeeId in request"
            }), 400

        if 'roleId' not in data:
            return jsonify({
                'success': False,
                'message': "Missing roleId in request"
            }), 400

        employee_id = data['employeeId']
        role_id = data['roleId']
        role_name = data.get('roleName', 'Unknown Role')

        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Check if employee exists
        employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
        if not employee:
            return jsonify({
                'success': False,
                'message': f"Employee with ID {employee_id} not found"
            }), 404

        # Initialize team data structure if needed
        if 'team' not in project:
            project['team'] = {
                'employee_ids': [],
                'role_assignments': [],
                'updated_at': datetime.now()
            }
        elif 'role_assignments' not in project['team']:
            project['team']['role_assignments'] = []

        # Check if employee already assigned to this role
        existing = next((item for item in project['team'].get('role_assignments', [])
                         if item.get('roleId') == role_id), None)

        if existing:
            # Update existing role assignment
            existing['employeeId'] = employee_id
            existing['updated_at'] = datetime.now()
            print(f"Updated existing role assignment: {existing}")
        else:
            # Add new role assignment
            assignment = {
                'roleId': role_id,
                'roleName': role_name,
                'employeeId': employee_id,
                'updated_at': datetime.now()
            }
            project['team']['role_assignments'].append(assignment)
            print(f"Added new role assignment: {assignment}")

        # Make sure employee_id is in the overall team list
        if 'employee_ids' not in project['team']:
            project['team']['employee_ids'] = []

        if employee_id not in project['team']['employee_ids']:
            project['team']['employee_ids'].append(employee_id)

        project['team']['updated_at'] = datetime.now()

        # Update the project in MongoDB
        mongodb_service.update_one(
            'Projects',
            {'_id': object_id},
            {'$set': {'team': project['team']}}
        )

        return jsonify({
            'success': True,
            'message': f"Employee assigned to role successfully",
            'role_assignments': project['team']['role_assignments']
        })

    except Exception as e:
        print(f"Error in add_employee_to_team: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error assigning employee to role: {str(e)}"
        }), 500


@project_blueprint.route('/<project_id>/optimize-team', methods=['POST'])
def optimize_project_team(project_id):
    """
    Optimize team composition for better KPIs.
    """
    try:
        # Get project
        project = mongodb_service.find_one('Projects', {'_id': ObjectId(project_id)})
        if not project:
            raise NotFoundError(f"Project {project_id} not found")

        # Get current team
        team_data = project.get('team', {})
        current_team_ids = team_data.get('employee_ids', [])

        # Analyze current team performance potential
        current_team = []
        for emp_id in current_team_ids:
            employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(emp_id)})
            if employee:
                current_team.append(employee)

        # Get project requirements
        project_details = {
            'project_type': project.get('project_type'),
            'project_timeline': project.get('project_timeline'),
            'project_team_size': project.get('project_team_size'),
            'project_languages': project.get('project_languages'),
            'project_sprints': project.get('project_sprints', 5)
        }

        # Analyze current team
        from modules.kpi_generation.kpi_predictor import KPIPredictor
        current_analysis = KPIGenerator._analyze_team_composition(current_team, project_details)
        current_predictions = KPIPredictor.predict_project_success(current_analysis, project_details)

        # Find optimization opportunities
        optimization_suggestions = []

        # Check for skill gaps
        if current_analysis['missing_skills']:
            # Find employees who have missing skills
            missing_skills = current_analysis['missing_skills']

            all_employees = mongodb_service.find_many('Resumes')
            skill_providers = []

            for emp in all_employees:
                if str(emp['_id']) not in current_team_ids:
                    emp_skills = emp.get('Skills', [])
                    provided_skills = [
                        skill for skill in missing_skills
                        if any(SkillMatcher.get_similarity(skill, emp_skill) > 70
                               for emp_skill in emp_skills)
                    ]

                    if provided_skills:
                        skill_providers.append({
                            'employee_id': str(emp['_id']),
                            'name': emp.get('Name', 'Unknown'),
                            'provides_skills': provided_skills,
                            'all_skills': emp_skills
                        })

            # Sort by number of missing skills provided
            skill_providers.sort(key=lambda x: len(x['provides_skills']), reverse=True)

            optimization_suggestions.append({
                'type': 'add_skill_provider',
                'reason': 'Fill critical skill gaps',
                'suggestions': skill_providers[:3],
                'impact': 'Could improve skill coverage by 20-30%'
            })

        # Check for experience imbalance
        if current_analysis['experience_balance'] < 50:
            exp_dist = current_analysis['experience_distribution']

            if exp_dist.get('Junior', 0) > len(current_team) / 2:
                optimization_suggestions.append({
                    'type': 'add_senior_member',
                    'reason': 'Team is too junior-heavy',
                    'impact': 'Could improve velocity by 15-20% and reduce defects'
                })

            if not exp_dist.get('Lead') and len(current_team) > 3:
                optimization_suggestions.append({
                    'type': 'add_tech_lead',
                    'reason': 'Team lacks technical leadership',
                    'impact': 'Could improve code quality and team coordination'
                })

        # Check team size efficiency
        if len(current_team) > 8:
            optimization_suggestions.append({
                'type': 'reduce_team_size',
                'reason': 'Team is too large, causing coordination overhead',
                'suggestion': 'Consider splitting into two smaller teams',
                'impact': 'Could improve efficiency by 10-15%'
            })

        return jsonify({
            'success': True,
            'current_team_analysis': current_analysis,
            'current_predictions': current_predictions,
            'optimization_suggestions': optimization_suggestions
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error optimizing team: {str(e)}"
        }), 500