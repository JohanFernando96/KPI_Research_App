import numpy as np
from sklearn.linear_model import LinearRegression
import json


class KPIPredictor:
    """
    Predict KPI outcomes based on team composition and project parameters.
    """

    @staticmethod
    def predict_project_success(team_analysis, project_details):
        """
        Predict project success metrics based on team composition.

        Returns:
            dict: Predicted success metrics and risk factors
        """
        # Feature extraction
        features = KPIPredictor._extract_features(team_analysis, project_details)

        # Simple prediction model (in real implementation, use trained ML model)
        success_score = KPIPredictor._calculate_success_score(features)

        # Risk analysis
        risk_factors = KPIPredictor._identify_risk_factors(team_analysis, project_details)

        # Generate predictions
        predictions = {
            'success_probability': round(success_score * 100, 1),
            'predicted_completion': KPIPredictor._predict_completion_time(
                features, project_details.get('project_timeline', 90)
            ),
            'quality_forecast': KPIPredictor._predict_quality_metrics(features),
            'risk_factors': risk_factors,
            'recommendations': KPIPredictor._generate_recommendations(
                success_score, risk_factors
            )
        }

        return predictions

    @staticmethod
    def _extract_features(team_analysis, project_details):
        """Extract features for prediction model."""
        return {
            'team_size': team_analysis.get('team_size', 0),
            'avg_experience': team_analysis.get('avg_experience', 0),
            'skill_coverage': team_analysis.get('skill_coverage', 0) / 100,
            'has_junior_majority': team_analysis.get('experience_distribution', {}).get('Junior',
                                                                                        0) > team_analysis.get(
                'team_size', 1) / 2,
            'timeline_days': project_details.get('project_timeline', 90),
            'technology_complexity': len(project_details.get('project_languages', [])),
            'sprint_count': project_details.get('project_sprints', 5)
        }

    @staticmethod
    def _calculate_success_score(features):
        """Calculate project success probability."""
        # Weighted scoring based on features
        weights = {
            'skill_coverage': 0.3,
            'avg_experience': 0.25,
            'team_size_factor': 0.15,
            'timeline_factor': 0.15,
            'complexity_factor': 0.15
        }

        # Normalize team size (optimal is 4-6)
        optimal_team_size = 5
        team_size_factor = 1 - abs(features['team_size'] - optimal_team_size) / optimal_team_size * 0.5

        # Timeline factor (longer timelines have better success)
        timeline_factor = min(1, features['timeline_days'] / 120)

        # Complexity factor (fewer technologies is better)
        complexity_factor = max(0.5, 1 - features['technology_complexity'] / 10)

        # Calculate weighted score
        score = (
                features['skill_coverage'] * weights['skill_coverage'] +
                min(1, features['avg_experience'] / 5) * weights['avg_experience'] +
                team_size_factor * weights['team_size_factor'] +
                timeline_factor * weights['timeline_factor'] +
                complexity_factor * weights['complexity_factor']
        )

        return min(0.95, max(0.4, score))  # Cap between 40% and 95%

    @staticmethod
    def _predict_completion_time(features, planned_timeline):
        """Predict actual completion time."""
        # Factors that affect timeline
        delay_factors = []

        if features['skill_coverage'] < 0.8:
            delay_factors.append(1.1)  # 10% delay for skill gaps

        if features['has_junior_majority']:
            delay_factors.append(1.15)  # 15% delay for junior-heavy team

        if features['technology_complexity'] > 5:
            delay_factors.append(1.1)  # 10% delay for high complexity

        # Apply delay factors
        total_factor = 1.0
        for factor in delay_factors:
            total_factor *= factor

        predicted_days = planned_timeline * total_factor

        return {
            'predicted_days': round(predicted_days),
            'delay_risk': 'High' if total_factor > 1.2 else 'Medium' if total_factor > 1.1 else 'Low',
            'confidence': 85 if len(delay_factors) < 2 else 70
        }

    @staticmethod
    def _predict_quality_metrics(features):
        """Predict code quality metrics."""
        base_defect_density = 1.0  # defects per 1000 LOC

        # Adjust based on team experience
        if features['avg_experience'] < 2:
            defect_multiplier = 1.5
        elif features['avg_experience'] < 5:
            defect_multiplier = 1.0
        else:
            defect_multiplier = 0.7

        # Adjust based on skill coverage
        skill_multiplier = 2 - features['skill_coverage']

        predicted_defect_density = base_defect_density * defect_multiplier * skill_multiplier

        # Predict test coverage
        base_coverage = 80
        coverage_adjustment = features['skill_coverage'] * 20 - 10
        predicted_coverage = max(40, min(95, base_coverage + coverage_adjustment))

        return {
            'predicted_defect_density': round(predicted_defect_density, 2),
            'predicted_test_coverage': round(predicted_coverage),
            'code_quality_risk': 'High' if predicted_defect_density > 1.5 else 'Medium' if predicted_defect_density > 1.0 else 'Low'
        }

    @staticmethod
    def _identify_risk_factors(team_analysis, project_details):
        """Identify project risk factors."""
        risks = []

        # Team-related risks
        if team_analysis.get('skill_coverage', 100) < 70:
            risks.append({
                'type': 'skill_gap',
                'severity': 'High',
                'description': 'Critical skill gaps in team',
                'mitigation': 'Provide training or hire specialists'
            })

        if team_analysis.get('avg_experience', 0) < 2:
            risks.append({
                'type': 'experience',
                'severity': 'Medium',
                'description': 'Low average team experience',
                'mitigation': 'Assign senior mentors and increase code reviews'
            })

        # Project-related risks
        timeline = project_details.get('project_timeline', 90)
        team_size = team_analysis.get('team_size', 1)
        if timeline < 60 and team_size > 5:
            risks.append({
                'type': 'coordination',
                'severity': 'Medium',
                'description': 'Large team with tight timeline',
                'mitigation': 'Improve communication channels and reduce team size'
            })

        return risks

    @staticmethod
    def _generate_recommendations(success_score, risk_factors):
        """Generate actionable recommendations."""
        recommendations = []

        if success_score < 0.6:
            recommendations.append({
                'priority': 'High',
                'action': 'Consider extending timeline or reducing scope',
                'impact': 'Increase success probability by 15-20%'
            })

        for risk in risk_factors:
            if risk['severity'] == 'High':
                recommendations.append({
                    'priority': 'High',
                    'action': risk['mitigation'],
                    'impact': f"Mitigate {risk['type']} risk"
                })

        return recommendations