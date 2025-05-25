from services.mongodb_service import mongodb_service
import numpy as np
from datetime import datetime, timedelta
import json  # Add this missing import


class KPILearner:
    """
    Learn from historical project data to improve KPI generation.
    """

    @staticmethod
    def learn_from_completed_projects():
        """
        Analyze completed projects to extract KPI patterns.
        """
        # Get completed projects
        completed_projects = mongodb_service.find_many(
            'Projects',
            {'status': 'Completed'}
        )

        if not completed_projects:
            return None

        # Extract patterns
        patterns = {
            'velocity_patterns': KPILearner._analyze_velocity_patterns(completed_projects),
            'quality_patterns': KPILearner._analyze_quality_patterns(completed_projects),
            'timeline_patterns': KPILearner._analyze_timeline_patterns(completed_projects)
        }

        # Store learned patterns
        mongodb_service.update_one(
            'KPIPatterns',
            {'type': 'learned_patterns'},
            {
                '$set': {
                    'patterns': patterns,
                    'updated_at': datetime.now(),
                    'projects_analyzed': len(completed_projects)
                }
            },
            upsert=True
        )

        return patterns

    @staticmethod
    def _analyze_velocity_patterns(projects):
        """Analyze velocity patterns from completed projects."""
        velocity_data = []

        for project in projects:
            kpi_doc = mongodb_service.find_one(
                'ProjectKPIs',
                {'project_id': project['_id']}
            )

            if kpi_doc and 'kpis' in kpi_doc:
                velocity = kpi_doc['kpis'].get('productivity', {}).get('velocity', {})
                if velocity.get('value') and velocity.get('target'):
                    try:
                        actual = float(velocity['value'].split()[0])
                        target = float(velocity['target'].split()[0])
                        team_size = project.get('project_team_size', 5)

                        velocity_data.append({
                            'actual_per_person': actual / team_size,
                            'target_per_person': target / team_size,
                            'achievement_rate': actual / target if target > 0 else 0,
                            'project_type': project.get('project_type', 'Unknown')
                        })
                    except:
                        pass

        # Calculate patterns
        if velocity_data:
            avg_achievement = np.mean([d['achievement_rate'] for d in velocity_data])
            by_project_type = {}

            for data in velocity_data:
                ptype = data['project_type']
                if ptype not in by_project_type:
                    by_project_type[ptype] = []
                by_project_type[ptype].append(data['actual_per_person'])

            type_averages = {
                ptype: np.mean(values)
                for ptype, values in by_project_type.items()
            }

            return {
                'average_achievement_rate': round(avg_achievement, 2),
                'velocity_by_project_type': type_averages,
                'recommendation': 'Adjust velocity targets based on historical achievement rates'
            }

        return None

    @staticmethod
    def _analyze_quality_patterns(projects):
        """Analyze quality patterns from completed projects."""
        # Placeholder implementation
        return {
            'average_defect_density': 1.5,
            'test_coverage_average': 75,
            'recommendation': 'Focus on improving test coverage'
        }

    @staticmethod
    def _analyze_timeline_patterns(projects):
        """Analyze timeline patterns from completed projects."""
        # Placeholder implementation
        return {
            'on_time_delivery_rate': 0.7,
            'average_delay_percentage': 15,
            'recommendation': 'Add buffer time to project estimates'
        }

    @staticmethod
    def apply_learned_patterns(base_kpis, project_details):
        """
        Apply learned patterns to improve KPI accuracy.
        """
        # Get learned patterns
        patterns_doc = mongodb_service.find_one(
            'KPIPatterns',
            {'type': 'learned_patterns'}
        )

        if not patterns_doc or 'patterns' not in patterns_doc:
            return base_kpis

        patterns = patterns_doc['patterns']
        adjusted_kpis = json.loads(json.dumps(base_kpis))  # Deep copy

        # Apply velocity adjustments
        if 'velocity_patterns' in patterns and patterns['velocity_patterns']:
            velocity_pattern = patterns['velocity_patterns']
            achievement_rate = velocity_pattern.get('average_achievement_rate', 1.0)

            # Adjust velocity targets based on historical achievement
            if 'productivity' in adjusted_kpis and 'velocity' in adjusted_kpis['productivity']:
                try:
                    current_target = adjusted_kpis['productivity']['velocity']['target']
                    target_value = float(current_target.split()[0])

                    # Apply historical achievement rate
                    adjusted_value = target_value * achievement_rate

                    # Check project type specific data
                    project_type = project_details.get('project_type')
                    if project_type in velocity_pattern.get('velocity_by_project_type', {}):
                        type_velocity = velocity_pattern['velocity_by_project_type'][project_type]
                        team_size = project_details.get('project_team_size', 5)
                        adjusted_value = type_velocity * team_size

                    adjusted_kpis['productivity']['velocity'][
                        'target'] = f"{round(adjusted_value)} story points per sprint"
                except:
                    pass

        return adjusted_kpis