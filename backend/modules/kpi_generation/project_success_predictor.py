class ProjectSuccessPredictor:
    """
    Predicts project success based on KPIs and team composition.
    """

    @staticmethod
    def predict_success(project_kpis, team_members, project_details):
        """
        Predict project success probability.

        Args:
            project_kpis: Current project KPIs
            team_members: List of team members
            project_details: Project information

        Returns:
            dict: Success prediction with risk factors
        """
        try:
            # Calculate individual scores
            kpi_score = ProjectSuccessPredictor._calculate_kpi_score(project_kpis)
            team_score = ProjectSuccessPredictor._calculate_team_score(team_members, project_details)
            timeline_score = ProjectSuccessPredictor._calculate_timeline_score(project_details)

            # Calculate overall success probability
            success_probability = (
                    kpi_score * 0.4 +
                    team_score * 0.35 +
                    timeline_score * 0.25
            )

            # Identify risk factors
            risk_factors = ProjectSuccessPredictor._identify_risk_factors(
                project_kpis, team_members, project_details,
                {'kpi': kpi_score, 'team': team_score, 'timeline': timeline_score}
            )

            # Generate recommendations
            recommendations = ProjectSuccessPredictor._generate_success_recommendations(
                risk_factors, success_probability
            )

            return {
                'success_probability': round(success_probability * 100, 1),
                'scores': {
                    'kpi_health': round(kpi_score * 100, 1),
                    'team_strength': round(team_score * 100, 1),
                    'timeline_feasibility': round(timeline_score * 100, 1)
                },
                'risk_factors': risk_factors,
                'recommendations': recommendations,
                'confidence_level': ProjectSuccessPredictor._calculate_prediction_confidence(
                    team_members, project_kpis
                )
            }

        except Exception as e:
            print(f"Error predicting project success: {str(e)}")
            return {
                'success_probability': 50,
                'scores': {
                    'kpi_health': 50,
                    'team_strength': 50,
                    'timeline_feasibility': 50
                },
                'risk_factors': [],
                'recommendations': [],
                'confidence_level': 'low'
            }

    @staticmethod
    def _calculate_kpi_score(project_kpis):
        """Calculate score based on KPI performance."""
        if not project_kpis:
            return 0.5

        total_kpis = 0
        on_track_kpis = 0

        for category, kpis in project_kpis.items():
            for kpi_name, kpi_data in kpis.items():
                total_kpis += 1
                status = kpi_data.get('status', 'Below Target')

                if status == 'On Track':
                    on_track_kpis += 1
                elif status == 'At Risk':
                    on_track_kpis += 0.6
                else:  # Below Target
                    on_track_kpis += 0.3

        return on_track_kpis / total_kpis if total_kpis > 0 else 0.5

    @staticmethod
    def _calculate_team_score(team_members, project_details):
        """Calculate score based on team composition."""
        if not team_members:
            return 0.3

        required_size = project_details.get('team_size', 5)
        actual_size = len(team_members)

        # Size match score
        size_score = 1.0 - abs(required_size - actual_size) / required_size
        size_score = max(0, min(1, size_score))

        # Experience score
        total_experience = sum(
            member.get('_derived', {}).get('total_years_experience', 0)
            for member in team_members
        )
        avg_experience = total_experience / len(team_members) if team_members else 0
        experience_score = min(1.0, avg_experience / 8)  # 8 years as optimal

        # Skills coverage score
        required_skills = []
        if isinstance(project_details.get('languages'), list):
            required_skills = project_details['languages']
        elif isinstance(project_details.get('languages'), str):
            required_skills = [s.strip() for s in project_details['languages'].split(',')]

        team_skills = set()
        for member in team_members:
            team_skills.update(member.get('Skills', []))

        skill_coverage = 0
        if required_skills:
            matched_skills = sum(
                1 for skill in required_skills
                if any(skill.lower() in team_skill.lower() for team_skill in team_skills)
            )
            skill_coverage = matched_skills / len(required_skills)
        else:
            skill_coverage = 0.7  # Default if no specific skills required

        # Combine scores
        return (size_score * 0.3 + experience_score * 0.35 + skill_coverage * 0.35)

    @staticmethod
    def _calculate_timeline_score(project_details):
        """Calculate score based on timeline feasibility."""
        timeline = project_details.get('timeline', 90)
        team_size = project_details.get('team_size', 5)
        sprints = project_details.get('sprints', 5)

        # Calculate days per sprint
        days_per_sprint = timeline / sprints if sprints > 0 else 14

        # Ideal is 10-14 days per sprint
        if 10 <= days_per_sprint <= 14:
            sprint_score = 1.0
        elif 7 <= days_per_sprint < 10 or 14 < days_per_sprint <= 21:
            sprint_score = 0.8
        else:
            sprint_score = 0.5

        # Project duration score (very short or very long projects are riskier)
        if 30 <= timeline <= 180:
            duration_score = 1.0
        elif 20 <= timeline < 30 or 180 < timeline <= 365:
            duration_score = 0.7
        else:
            duration_score = 0.4

        return (sprint_score * 0.6 + duration_score * 0.4)

    @staticmethod
    def _identify_risk_factors(project_kpis, team_members, project_details, scores):
        """Identify project risk factors."""
        risk_factors = []

        # KPI-based risks
        if scores['kpi'] < 0.6:
            risk_factors.append({
                'type': 'kpi',
                'severity': 'high' if scores['kpi'] < 0.4 else 'medium',
                'title': 'Poor KPI Performance',
                'description': 'Multiple KPIs are below target, indicating project health issues.'
            })

        # Team-based risks
        if scores['team'] < 0.6:
            if len(team_members) < project_details.get('team_size', 5) * 0.8:
                risk_factors.append({
                    'type': 'team',
                    'severity': 'high',
                    'title': 'Understaffed Team',
                    'description': 'Team size is significantly below requirements.'
                })

            # Check experience distribution
            junior_count = sum(
                1 for member in team_members
                if member.get('_derived', {}).get('total_years_experience', 0) < 2
            )
            if junior_count > len(team_members) * 0.6:
                risk_factors.append({
                    'type': 'team',
                    'severity': 'medium',
                    'title': 'Inexperienced Team',
                    'description': 'Majority of team members are junior developers.'
                })

        # Timeline risks
        if scores['timeline'] < 0.6:
            risk_factors.append({
                'type': 'timeline',
                'severity': 'high' if scores['timeline'] < 0.4 else 'medium',
                'title': 'Timeline Concerns',
                'description': 'Project timeline may be too aggressive or poorly structured.'
            })

        return risk_factors

    @staticmethod
    def _generate_success_recommendations(risk_factors, success_probability):
        """Generate recommendations to improve success probability."""
        recommendations = []

        if success_probability < 60:
            recommendations.append({
                'priority': 'critical',
                'title': 'Immediate Action Required',
                'description': 'Project has low success probability. Consider project restructuring.',
                'actions': [
                    'Review and adjust project scope',
                    'Reassess team composition',
                    'Recalibrate KPI targets'
                ]
            })

        # Address specific risk factors
        for risk in risk_factors:
            if risk['type'] == 'kpi' and risk['severity'] == 'high':
                recommendations.append({
                    'priority': 'high',
                    'title': 'Improve KPI Performance',
                    'description': 'Focus on bringing critical KPIs back on track.',
                    'actions': [
                        'Conduct KPI root cause analysis',
                        'Implement corrective actions',
                        'Consider KPI target adjustments'
                    ]
                })

            elif risk['type'] == 'team':
                if 'Understaffed' in risk['title']:
                    recommendations.append({
                        'priority': 'high',
                        'title': 'Address Staffing Gap',
                        'description': 'Add qualified team members to meet project requirements.',
                        'actions': [
                            'Fast-track hiring process',
                            'Consider contractor resources',
                            'Redistribute workload'
                        ]
                    })
                elif 'Inexperienced' in risk['title']:
                    recommendations.append({
                        'priority': 'medium',
                        'title': 'Enhance Team Skills',
                        'description': 'Implement measures to support junior team members.',
                        'actions': [
                            'Pair programming sessions',
                            'Technical mentorship program',
                            'Additional code reviews'
                        ]
                    })

            elif risk['type'] == 'timeline' and risk['severity'] == 'high':
                recommendations.append({
                    'priority': 'high',
                    'title': 'Timeline Adjustment',
                    'description': 'Review and potentially extend project timeline.',
                    'actions': [
                        'Re-evaluate sprint duration',
                        'Consider scope reduction',
                        'Add buffer time for risks'
                    ]
                })

        return recommendations

    @staticmethod
    def _calculate_prediction_confidence(team_members, project_kpis):
        """Calculate confidence level in the prediction."""
        # More data points increase confidence
        data_points = 0

        if team_members:
            data_points += len(team_members)

        if project_kpis:
            for category in project_kpis.values():
                data_points += len(category)

        if data_points < 10:
            return 'low'
        elif data_points < 20:
            return 'medium'
        else:
            return 'high'