from datetime import datetime
from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
import json

from services.mongodb_service import mongodb_service
from services.chart_service import chart_service
from modules.kpi_generation.kpi_generator import KPIGenerator
from modules.kpi_generation.team_kpi_generator import TeamKPIGenerator
from modules.kpi_generation.individual_kpi_generator import IndividualKPIGenerator
from modules.kpi_generation.chart_generator import ChartGenerator
from modules.kpi_generation.kpi_adjuster import KPIAdjuster
from modules.kpi_generation.kpi_predictor import KPIPredictor
from modules.kpi_generation.kpi_learner import KPILearner
from utils.error_handlers import ValidationError, NotFoundError
from utils.json_utils import serialize_mongo

kpi_blueprint = Blueprint('kpi', __name__)


@kpi_blueprint.route('/generate', methods=['POST'])
def generate_kpis():
    """
    Enhanced endpoint for generating KPIs with optional team awareness.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Check if team members are provided
        team_members = data.get('team_members', [])

        # Generate KPIs with team awareness
        kpis = KPIGenerator.generate_kpis(data, team_members)

        # Generate additional project data
        team_analysis = None
        if team_members:
            team_analysis = KPIGenerator._analyze_team_composition(team_members, data)

        gantt_data = KPIGenerator.generate_gantt_chart_data(data, team_analysis)
        employee_criteria = KPIGenerator.generate_employee_criteria(data, team_members)
        sprint_breakdown = KPIGenerator.generate_sprint_breakdown(data, team_analysis)

        # Prepare response
        response = {
            'kpis': kpis,
            'gantt_chart_data': gantt_data,
            'employee_criteria': employee_criteria,
            'sprint_breakdown': sprint_breakdown,
            'team_analysis': team_analysis
        }

        return jsonify({
            'success': True,
            'data': response
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis', methods=['POST'])
def create_project_kpis(project_id):
    """
    Endpoint for creating KPIs for a specific project.
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

        # Generate KPIs
        kpis = KPIGenerator.generate_kpis(data)

        # Generate Gantt chart data
        gantt_data = KPIGenerator.generate_gantt_chart_data(data)

        # Generate employee criteria
        employee_criteria = KPIGenerator.generate_employee_criteria(data)

        # Generate sprint breakdown
        sprint_breakdown = KPIGenerator.generate_sprint_breakdown(data)

        # Generate charts
        try:
            # Generate Gantt chart
            gantt_chart_path = ChartGenerator.generate_gantt_chart(gantt_data, project_id)

            # Generate burndown chart
            burndown_chart_path = ChartGenerator.generate_burndown_chart(
                int(data.get('project_timeline', 90)),
                int(data.get('project_sprints', 5)),
                project_id
            )

            # Generate velocity chart
            velocity_chart_path = ChartGenerator.generate_velocity_chart(
                int(data.get('project_sprints', 5)),
                int(data.get('project_team_size', 5)),
                project_id
            )

            # Generate KPI radar chart
            kpi_radar_chart_path = ChartGenerator.generate_kpi_radar_chart(kpis, project_id)

            # Add chart paths to the data
            charts = {
                'gantt_chart': gantt_chart_path,
                'burndown_chart': burndown_chart_path,
                'velocity_chart': velocity_chart_path,
                'kpi_radar_chart': kpi_radar_chart_path
            }
        except Exception as chart_error:
            charts = {
                'error': f"Error generating charts: {str(chart_error)}"
            }

        # Create KPI document
        kpi_doc = {
            'project_id': object_id,
            'kpis': kpis,
            'gantt_chart_data': gantt_data,
            'employee_criteria': employee_criteria,
            'sprint_breakdown': sprint_breakdown,
            'charts': charts,
            'project_details': data,
            'created_at': datetime.now()
        }

        # Save KPIs to MongoDB
        kpi_id = mongodb_service.insert_one('ProjectKPIs', kpi_doc)

        # Update project with KPI ID
        mongodb_service.update_one(
            'Projects',
            {'_id': object_id},
            {'$set': {'kpi_id': kpi_id}}
        )

        return jsonify({
            'success': True,
            'message': "Project KPIs created successfully",
            'kpi_id': str(kpi_id),
            'data': {
                'kpis': kpis,
                'charts': charts
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error creating project KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis', methods=['GET'])
def get_project_kpis(project_id):
    """
    Endpoint for retrieving KPIs for a specific project.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project with ID {project_id} not found")

        # Convert ObjectId to string for JSON serialization
        kpi_doc['_id'] = str(kpi_doc['_id'])
        kpi_doc['project_id'] = str(kpi_doc['project_id'])

        return jsonify({
            'success': True,
            'data': kpi_doc
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving project KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/generate-team-based', methods=['POST'])
def generate_project_team_kpis(project_id):
    """
    Generate KPIs based on actual team composition and individual capabilities.
    """
    try:
        data = request.json

        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Get project
        project = mongodb_service.find_one('Projects', {'_id': object_id})
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get team data
        team_data = project.get('team', {})
        role_assignments = team_data.get('role_assignments', [])

        # Fetch team member details
        team_members = []
        employee_ids = team_data.get('employee_ids', [])

        # Also get employees from role assignments
        for assignment in role_assignments:
            emp_id = assignment.get('employeeId')
            if emp_id and emp_id not in employee_ids:
                employee_ids.append(emp_id)

        # Fetch all team members
        if employee_ids:
            for emp_id in employee_ids:
                try:
                    employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(emp_id)})
                    if employee:
                        team_members.append(employee)
                except:
                    continue

        # Prepare project details
        project_details = {
            'project_type': project.get('project_type'),
            'project_timeline': project.get('project_timeline'),
            'project_team_size': len(team_members) or project.get('project_team_size'),
            'project_languages': project.get('project_languages'),
            'project_sprints': project.get('project_sprints', 5)
        }

        # Generate comprehensive KPIs
        comprehensive_kpis = KPIGenerator.generate_comprehensive_project_kpis(
            project_details,
            {
                'members': team_members,
                'role_assignments': role_assignments
            }
        )

        # Generate predictions if team data available
        predictions = None
        if team_members:
            team_analysis = KPIGenerator._analyze_team_composition(team_members, project_details)
            predictions = KPIPredictor.predict_project_success(team_analysis, project_details)

        # Apply historical learning if available
        if comprehensive_kpis.get('project_level'):
            comprehensive_kpis['project_level'] = KPILearner.apply_learned_patterns(
                comprehensive_kpis['project_level'],
                project_details
            )

        # Generate charts based on team capabilities
        charts = {}
        try:
            team_kpis = comprehensive_kpis.get('project_level', {})

            # Generate various charts
            gantt_data = KPIGenerator.generate_gantt_chart_data(
                project_details,
                comprehensive_kpis.get('team_metrics')
            )
            charts['gantt_chart'] = ChartGenerator.generate_gantt_chart(gantt_data, project_id)

            charts['burndown_chart'] = ChartGenerator.generate_burndown_chart(
                int(project_details['project_timeline']),
                int(project_details['project_sprints']),
                project_id
            )

            charts['velocity_chart'] = ChartGenerator.generate_velocity_chart(
                int(project_details['project_sprints']),
                len(team_members),
                project_id
            )

            charts['kpi_radar_chart'] = ChartGenerator.generate_kpi_radar_chart(
                team_kpis,
                project_id
            )

            charts['kpi_breakdown'] = ChartGenerator.generate_kpi_breakdown_chart(
                team_kpis,
                project_id
            )

            # Generate individual performance charts
            if comprehensive_kpis.get('individual_level'):
                charts['individual_charts'] = {}
                for employee_id, individual_kpis in comprehensive_kpis['individual_level'].items():
                    charts['individual_charts'][employee_id] = ChartGenerator.generate_kpi_radar_chart(
                        individual_kpis,
                        f"{project_id}_{employee_id}"
                    )

        except Exception as chart_error:
            charts['error'] = f"Error generating charts: {str(chart_error)}"

        # Save comprehensive KPIs
        kpi_doc = {
            'project_id': object_id,
            'kpis': comprehensive_kpis,
            'team_composition': {
                'size': len(team_members),
                'members': [str(m['_id']) for m in team_members],
                'analysis': comprehensive_kpis.get('team_metrics')
            },
            'predictions': predictions,
            'charts': charts,
            'project_details': project_details,
            'created_at': datetime.now(),
            'generation_type': 'team_based'
        }

        kpi_id = mongodb_service.insert_one('ProjectKPIs', kpi_doc)

        # Update project
        mongodb_service.update_one(
            'Projects',
            {'_id': object_id},
            {'$set': {
                'kpi_id': kpi_id,
                'has_team_kpis': True,
                'kpi_generation_date': datetime.now()
            }}
        )

        return jsonify({
            'success': True,
            'message': "Team-based KPIs generated successfully",
            'kpi_id': str(kpi_id),
            'data': {
                'comprehensive_kpis': serialize_mongo(comprehensive_kpis),
                'charts': charts,
                'team_analysis': comprehensive_kpis.get('team_metrics'),
                'predictions': predictions
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error generating team-based KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/charts/<chart_type>', methods=['GET'])
def get_project_chart(project_id, chart_type):
    """
    Endpoint for retrieving a specific chart for a project.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project with ID {project_id} not found")

        # Check if the chart exists
        if 'charts' not in kpi_doc or chart_type not in kpi_doc['charts']:
            raise NotFoundError(f"Chart of type {chart_type} not found for project with ID {project_id}")

        chart_path = kpi_doc['charts'][chart_type]

        # In a real API, you might return the file directly
        # For this example, we'll just return the path
        return jsonify({
            'success': True,
            'chart_path': chart_path
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving project chart: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/adjust', methods=['POST'])
def adjust_project_kpis(project_id):
    """
    Endpoint for adjusting KPIs based on project progress.
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

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project with ID {project_id} not found")

        # Extract project progress from request
        project_progress = data.get('project_progress', {})

        # Extract team performance from request
        team_performance = data.get('team_performance', None)

        # Adjust KPIs based on progress
        original_kpis = kpi_doc['kpis']
        adjusted_kpis = KPIAdjuster.adjust_kpis_based_on_progress(
            original_kpis,
            project_progress,
            team_performance
        )

        # Update KPI document
        mongodb_service.update_one(
            'ProjectKPIs',
            {'_id': kpi_doc['_id']},
            {'$set': {
                'kpis': adjusted_kpis,
                'last_adjusted': datetime.now()
            }}
        )

        return jsonify({
            'success': True,
            'message': "Project KPIs adjusted successfully",
            'data': {
                'original_kpis': original_kpis,
                'adjusted_kpis': adjusted_kpis
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error adjusting project KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/adjust-for-changes', methods=['POST'])
def adjust_kpis_for_project_changes(project_id):
    """
    Endpoint for adjusting KPIs based on project changes.
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

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project with ID {project_id} not found")

        # Extract updated project details from request
        updated_project = data.get('updated_project', {})

        if not updated_project:
            raise ValidationError("No updated project details provided")

        # Get original project details
        original_project = kpi_doc['project_details']

        # Adjust KPIs based on project changes
        original_kpis = kpi_doc['kpis']
        adjusted_kpis = KPIAdjuster.adjust_kpis_for_project_changes(
            original_kpis,
            original_project,
            updated_project
        )

        # Update KPI document
        mongodb_service.update_one(
            'ProjectKPIs',
            {'_id': kpi_doc['_id']},
            {'$set': {
                'kpis': adjusted_kpis,
                'project_details': updated_project,
                'last_adjusted': datetime.now()
            }}
        )

        return jsonify({
            'success': True,
            'message': "Project KPIs adjusted for changes successfully",
            'data': {
                'original_kpis': original_kpis,
                'adjusted_kpis': adjusted_kpis
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error adjusting project KPIs for changes: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/employees/<employee_id>/individual-kpis', methods=['GET'])
def get_employee_individual_kpis(project_id, employee_id):
    """
    Get individual KPIs for a specific employee in a project.
    """
    try:
        # Get project KPIs
        kpi_doc = mongodb_service.find_one(
            'ProjectKPIs',
            {'project_id': ObjectId(project_id)}
        )

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project {project_id} not found")

        # Check if individual KPIs exist
        individual_kpis = kpi_doc.get('kpis', {}).get('individual_level', {}).get(employee_id)

        if not individual_kpis:
            # Generate individual KPIs on demand
            employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(employee_id)})
            if not employee:
                raise NotFoundError(f"Employee {employee_id} not found")

            # Get project
            project = mongodb_service.find_one('Projects', {'_id': ObjectId(project_id)})

            # Find employee's role in project
            team_data = project.get('team', {})
            role_assignment = next(
                (a for a in team_data.get('role_assignments', [])
                 if a.get('employeeId') == employee_id),
                None
            )

            if role_assignment:
                role_criteria = {
                    'role': role_assignment.get('roleName', 'Team Member'),
                    'skills': []  # Could be populated from role requirements
                }

                # Generate individual KPIs
                project_kpis = kpi_doc.get('kpis', {}).get('project_level', {})
                individual_kpis = IndividualKPIGenerator.generate_individual_kpis(
                    project_kpis,
                    role_criteria,
                    employee
                )

                # Save to database
                mongodb_service.update_one(
                    'ProjectKPIs',
                    {'_id': kpi_doc['_id']},
                    {
                        '$set': {
                            f'kpis.individual_level.{employee_id}': individual_kpis
                        }
                    }
                )

        return jsonify({
            'success': True,
            'employee_id': employee_id,
            'individual_kpis': serialize_mongo(individual_kpis) if individual_kpis else None
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving individual KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/predict-success', methods=['GET'])
def predict_success(project_id):
    """
    Predict project success based on team composition and KPIs.
    """
    try:
        # Get project
        project = mongodb_service.find_one('Projects', {'_id': ObjectId(project_id)})
        if not project:
            raise NotFoundError(f"Project {project_id} not found")

        # Get team members
        team_data = project.get('team', {})
        employee_ids = team_data.get('employee_ids', [])

        team_members = []
        for emp_id in employee_ids:
            employee = mongodb_service.find_one('Resumes', {'_id': ObjectId(emp_id)})
            if employee:
                team_members.append(employee)

        # Prepare project details
        project_details = {
            'project_type': project.get('project_type'),
            'project_timeline': project.get('project_timeline'),
            'project_team_size': len(team_members),
            'project_languages': project.get('project_languages'),
            'project_sprints': project.get('project_sprints', 5)
        }

        # Analyze team and predict success
        team_analysis = KPIGenerator._analyze_team_composition(team_members, project_details)
        predictions = KPIPredictor.predict_project_success(team_analysis, project_details)

        return jsonify({
            'success': True,
            'predictions': predictions,
            'team_analysis': team_analysis
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error predicting project success: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/recommendations', methods=['GET'])
def get_project_recommendations(project_id):
    """
    Endpoint for retrieving KPI recommendations for a project.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs for project with ID {project_id} not found")

        # Generate recommendations based on current KPIs
        try:
            kpis = kpi_doc.get('kpis', {})
            recommendations = []

            # Check for KPIs that are at risk or below target
            for category, metrics in kpis.items():
                for metric_name, metric_data in metrics.items():
                    if metric_data.get('status') in ['At Risk', 'Below Target']:
                        recommendations.append({
                            'title': f"Improve {metric_name.replace('_', ' ').title()}",
                            'description': f"This {category} metric is currently {metric_data.get('status').lower()}. Current value: {metric_data.get('value')}, Target: {metric_data.get('target')}.",
                            'actionItems': [
                                f"Review {category} practices related to {metric_name.replace('_', ' ')}",
                                f"Consider adjusting the target if it's unrealistic for this project"
                            ],
                            'priority': 'high' if metric_data.get('status') == 'Below Target' else 'medium',
                            'category': category
                        })

            return jsonify({
                'success': True,
                'recommendations': recommendations
            })
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return jsonify({
                'success': True,
                'recommendations': []
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving project KPI recommendations: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/employees/<employee_id>/progress', methods=['POST'])
def update_employee_progress(project_id, employee_id):
    """
    Endpoint for updating employee-specific KPI progress.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Convert string IDs to ObjectId
        project_object_id = ObjectId(project_id)
        employee_object_id = ObjectId(employee_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': project_object_id})
        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Check if employee exists
        employee = mongodb_service.find_one('Resumes', {'_id': employee_object_id})
        if not employee:
            raise NotFoundError(f"Employee with ID {employee_id} not found")

        # Check if project team includes this employee
        if not 'team' in project or 'employee_ids' not in project['team'] or employee_id not in project['team'][
            'employee_ids']:
            raise ValidationError(f"Employee {employee_id} is not part of project {project_id}")

        # Get or create employee KPI progress collection entry
        employee_kpi_progress = mongodb_service.find_one(
            'EmployeeKPIProgress',
            {
                'project_id': project_object_id,
                'employee_id': employee_object_id
            }
        )

        if employee_kpi_progress:
            # Update existing progress
            mongodb_service.update_one(
                'EmployeeKPIProgress',
                {'_id': employee_kpi_progress['_id']},
                {
                    '$set': {
                        'progress': data,
                        'updated_at': datetime.now()
                    }
                }
            )
        else:
            # Create new progress entry
            mongodb_service.insert_one(
                'EmployeeKPIProgress',
                {
                    'project_id': project_object_id,
                    'employee_id': employee_object_id,
                    'progress': data,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
            )

        return jsonify({
            'success': True,
            'message': f"Employee KPI progress updated successfully",
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error updating employee KPI progress: {str(e)}"
        }), 500


@kpi_blueprint.route('/learn-from-history', methods=['POST'])
def learn_from_history():
    """
    Analyze completed projects to improve KPI generation.
    """
    try:
        # Learn from historical data
        patterns = KPILearner.learn_from_completed_projects()

        if patterns:
            return jsonify({
                'success': True,
                'message': "Successfully learned from completed projects",
                'patterns': patterns
            })
        else:
            return jsonify({
                'success': False,
                'message': "No completed projects found to learn from"
            }), 404

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error learning from projects: {str(e)}"
        }), 500


# Add these endpoints to kpi_routes.py

@kpi_blueprint.route('/projects/<project_id>/kpis/generate-team-based', methods=['POST'])
def generate_team_based_kpis(project_id):
    """
    Endpoint for generating team-based KPIs considering team composition.
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

        # Get team composition
        team_data = project.get('team', {})
        employee_ids = team_data.get('employee_ids', [])
        role_assignments = team_data.get('role_assignments', [])

        # Get project KPIs
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"Project KPIs not found for project {project_id}")

        # Get employee details for team-based analysis
        team_members = []
        if employee_ids:
            employee_object_ids = [ObjectId(id) for id in employee_ids]
            employees = mongodb_service.find_many('Resumes', {'_id': {'$in': employee_object_ids}})

            # Convert ObjectIds to strings
            for emp in employees:
                emp['_id'] = str(emp['_id'])
            team_members = employees

        # Import team-based KPI generator
        from modules.kpi_generation.team_based_kpi_generator import TeamBasedKPIGenerator

        # Generate team-based KPIs
        team_based_kpis = TeamBasedKPIGenerator.generate_team_based_kpis(
            project_kpis=kpi_doc.get('kpis', {}),
            team_members=team_members,
            role_assignments=role_assignments,
            project_details=project
        )

        # Store team-based KPIs
        mongodb_service.update_one(
            'ProjectKPIs',
            {'_id': kpi_doc['_id']},
            {'$set': {
                'team_based_kpis': team_based_kpis,
                'team_kpis_generated_at': datetime.now()
            }}
        )

        return jsonify({
            'success': True,
            'team_based_kpis': team_based_kpis,
            'message': 'Team-based KPIs generated successfully'
        })

    except Exception as e:
        print(f"Error generating team-based KPIs: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error generating team-based KPIs: {str(e)}"
        }), 500


@kpi_blueprint.route('/projects/<project_id>/kpis/predict-success', methods=['GET'])
def predict_project_success(project_id):
    """
    Endpoint for predicting project success based on current KPIs and team.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(project_id)

        # Check if project exists
        project = mongodb_service.find_one('Projects', {'_id': object_id})

        if not project:
            raise NotFoundError(f"Project with ID {project_id} not found")

        # Get KPI document
        kpi_doc = mongodb_service.find_one('ProjectKPIs', {'project_id': object_id})

        if not kpi_doc:
            raise NotFoundError(f"KPIs not found for project {project_id}")

        # Get team data
        team_data = project.get('team', {})
        employee_ids = team_data.get('employee_ids', [])

        # Get employee details
        team_members = []
        if employee_ids:
            employee_object_ids = [ObjectId(id) for id in employee_ids]
            employees = mongodb_service.find_many('Resumes', {'_id': {'$in': employee_object_ids}})

            for emp in employees:
                emp['_id'] = str(emp['_id'])
            team_members = employees

        # Import success predictor
        from modules.kpi_generation.project_success_predictor import ProjectSuccessPredictor

        # Predict project success
        prediction = ProjectSuccessPredictor.predict_success(
            project_kpis=kpi_doc.get('kpis', {}),
            team_members=team_members,
            project_details={
                'type': project.get('project_type'),
                'timeline': project.get('project_timeline'),
                'team_size': project.get('project_team_size'),
                'sprints': project.get('project_sprints'),
                'languages': project.get('project_languages')
            }
        )

        return jsonify({
            'success': True,
            'prediction': prediction
        })

    except Exception as e:
        print(f"Error predicting project success: {str(e)}")
        return jsonify({
            'success': False,
            'message': f"Error predicting project success: {str(e)}"
        }), 500