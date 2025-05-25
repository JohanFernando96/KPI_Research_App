class TeamBasedKPIGenerator:
    """
    Generates team-based KPIs considering team composition and individual strengths.
    """

    @staticmethod
    def generate_team_based_kpis(project_kpis, team_members, role_assignments, project_details):
        """
        Generate KPIs adjusted for the specific team composition.

        Args:
            project_kpis: Base project KPIs
            team_members: List of team member details
            role_assignments: Role assignments for team members
            project_details: Project information

        Returns:
            dict: Team-based KPIs with adjustments
        """
        try:
            # Calculate team metrics
            team_metrics = TeamBasedKPIGenerator._calculate_team_metrics(team_members)

            # Adjust KPIs based on team composition
            adjusted_kpis = TeamBasedKPIGenerator._adjust_kpis_for_team(
                project_kpis, team_metrics, project_details
            )

            # Generate team-specific recommendations
            recommendations = TeamBasedKPIGenerator._generate_team_recommendations(
                team_metrics, adjusted_kpis
            )

            return {
                'adjusted_kpis': adjusted_kpis,
                'team_metrics': team_metrics,
                'recommendations': recommendations,
                'confidence_level': TeamBasedKPIGenerator._calculate_confidence(team_metrics)
            }

        except Exception as e:
            print(f"Error generating team-based KPIs: {str(e)}")
            return {
                'adjusted_kpis': project_kpis,
                'team_metrics': {},
                'recommendations': [],
                'confidence_level': 0.5
            }

    @staticmethod
    def _calculate_team_metrics(team_members):
        """Calculate overall team metrics."""
        if not team_members:
            return {
                'average_experience': 0,
                'skill_coverage': 0,
                'skill_diversity': 0,
                'experience_distribution': 'unknown'
            }

        # Calculate average experience
        total_experience = 0
        experience_counts = {'junior': 0, 'mid': 0, 'senior': 0, 'lead': 0}

        for member in team_members:
            years = member.get('_derived', {}).get('total_years_experience', 0)
            total_experience += years

            if years < 2:
                experience_counts['junior'] += 1
            elif years < 5:
                experience_counts['mid'] += 1
            elif years < 8:
                experience_counts['senior'] += 1
            else:
                experience_counts['lead'] += 1

        avg_experience = total_experience / len(team_members) if team_members else 0

        # Calculate skill coverage and diversity
        all_skills = set()
        for member in team_members:
            skills = member.get('Skills', [])
            all_skills.update(skills)

        skill_diversity = len(all_skills)

        # Determine experience distribution
        max_count = max(experience_counts.values())
        if experience_counts['junior'] == max_count:
            distribution = 'junior-heavy'
        elif experience_counts['senior'] == max_count or experience_counts['lead'] == max_count:
            distribution = 'senior-heavy'
        else:
            distribution = 'balanced'

        return {
            'average_experience': avg_experience,
            'skill_coverage': skill_diversity,
            'skill_diversity': skill_diversity,
            'experience_distribution': distribution,
            'team_size': len(team_members),
            'experience_counts': experience_counts
        }

    @staticmethod
    def _adjust_kpis_for_team(project_kpis, team_metrics, project_details):
        """Adjust KPIs based on team composition."""
        adjusted_kpis = {}

        # Adjustment factors based on team metrics
        experience_factor = 1.0
        if team_metrics['average_experience'] < 3:
            experience_factor = 0.85  # Less experienced teams need more achievable targets
        elif team_metrics['average_experience'] > 7:
            experience_factor = 1.15  # More experienced teams can handle higher targets

        # Adjust each KPI category
        for category, kpis in project_kpis.items():
            adjusted_kpis[category] = {}

            for kpi_name, kpi_data in kpis.items():
                adjusted_value = kpi_data.copy()

                # Extract numeric values
                current_val = TeamBasedKPIGenerator._extract_numeric(kpi_data.get('value', '0'))
                target_val = TeamBasedKPIGenerator._extract_numeric(kpi_data.get('target', '0'))

                # Apply adjustments based on team composition
                if category == 'productivity':
                    # Junior-heavy teams might have lower initial velocity
                    if team_metrics['experience_distribution'] == 'junior-heavy':
                        target_val = target_val * 0.8
                    elif team_metrics['experience_distribution'] == 'senior-heavy':
                        target_val = target_val * 1.1

                elif category == 'code_quality':
                    # Experienced teams should have better quality targets
                    target_val = target_val * experience_factor

                elif category == 'collaboration':
                    # Larger teams might need more time for collaboration
                    if team_metrics['team_size'] > 7:
                        if 'turnaround_time' in kpi_name:
                            target_val = target_val * 1.2

                # Update the adjusted KPI
                adjusted_value['target'] = TeamBasedKPIGenerator._format_kpi_value(
                    kpi_name, target_val
                )
                adjusted_value['team_adjusted'] = True

                adjusted_kpis[category][kpi_name] = adjusted_value

        return adjusted_kpis

    @staticmethod
    def _generate_team_recommendations(team_metrics, adjusted_kpis):
        """Generate recommendations based on team composition."""
        recommendations = []

        # Experience-based recommendations
        if team_metrics['average_experience'] < 3:
            recommendations.append({
                'type': 'mentorship',
                'priority': 'high',
                'title': 'Implement Mentorship Program',
                'description': 'With a junior-heavy team, consider pairing junior developers with senior mentors.',
                'impact': 'productivity'
            })

        if team_metrics['experience_distribution'] == 'junior-heavy':
            recommendations.append({
                'type': 'training',
                'priority': 'high',
                'title': 'Focus on Code Reviews',
                'description': 'Increase code review frequency to ensure quality with less experienced team.',
                'impact': 'code_quality'
            })

        # Skill diversity recommendations
        if team_metrics['skill_diversity'] < 10:
            recommendations.append({
                'type': 'skills',
                'priority': 'medium',
                'title': 'Diversify Team Skills',
                'description': 'Limited skill diversity may create bottlenecks. Consider cross-training.',
                'impact': 'adaptability'
            })

        # Team size recommendations
        if team_metrics['team_size'] > 8:
            recommendations.append({
                'type': 'process',
                'priority': 'medium',
                'title': 'Implement Sub-team Structure',
                'description': 'Large team size may impact communication. Consider breaking into sub-teams.',
                'impact': 'collaboration'
            })

        return recommendations

    @staticmethod
    def _calculate_confidence(team_metrics):
        """Calculate confidence level in the adjusted KPIs."""
        confidence = 0.5  # Base confidence

        # Higher experience increases confidence
        if team_metrics['average_experience'] > 5:
            confidence += 0.2
        elif team_metrics['average_experience'] > 3:
            confidence += 0.1

        # Balanced team increases confidence
        if team_metrics['experience_distribution'] == 'balanced':
            confidence += 0.15

        # Good skill diversity increases confidence
        if team_metrics['skill_diversity'] > 15:
            confidence += 0.15

        return min(confidence, 1.0)

    @staticmethod
    def _extract_numeric(value_str):
        """Extract numeric value from KPI string."""
        if isinstance(value_str, (int, float)):
            return float(value_str)

        import re
        match = re.search(r'(\d+(?:\.\d+)?)', str(value_str))
        return float(match.group(1)) if match else 0.0

    @staticmethod
    def _format_kpi_value(kpi_name, value):
        """Format KPI value based on the KPI type."""
        value = round(value, 1)

        if 'velocity' in kpi_name:
            return f"{value} story points per sprint"
        elif 'time' in kpi_name or 'turnaround' in kpi_name:
            return f"{value} hours"
        elif 'density' in kpi_name:
            return f"{value} defects per 1,000 LOC"
        elif 'coverage' in kpi_name or 'rate' in kpi_name or 'ratio' in kpi_name:
            return f"{value}%"
        else:
            return str(value)