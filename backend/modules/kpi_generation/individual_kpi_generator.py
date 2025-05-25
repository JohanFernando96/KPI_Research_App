import json
from services.openai_service import openai_service
from modules.kpi_generation.kpi_generator import KPIGenerator
from modules.employee_matching.skill_matcher import SkillMatcher
from modules.skill_recommendation.role_hierarchy import RoleHierarchy


class IndividualKPIGenerator:
    """
    Enhanced class for generating specialized KPIs for individual team members,
    based on their actual skills, experience, and role alignment.
    """

    @staticmethod
    def generate_individual_kpis(project_kpis, role_criteria, employee=None, team_composition=None):
        """
        Generate specialized KPIs for a specific role or team member based on their actual capabilities.

        Args:
            project_kpis: The overall project KPIs
            role_criteria: The skills and requirements for the role
            employee: Optional employee data if available
            team_composition: Optional team composition data for context

        Returns:
            dict: Specialized KPIs for the role or employee
        """
        # Analyze employee's actual capabilities first
        employee_analysis = IndividualKPIGenerator._analyze_employee_capabilities(employee, role_criteria)

        # Generate KPIs using enhanced prompt with capability analysis
        try:
            role_name = role_criteria.get("role", "Team Member")
            role_skills = role_criteria.get("skills", [])

            # Create a comprehensive prompt for OpenAI
            prompt = f"""
            You are a specialized KPI generator for software development teams. Generate realistic, individualized KPIs 
            based on the employee's actual capabilities and experience level.

            Overall Project KPIs:
            {json.dumps(project_kpis, indent=2)}

            Role Information:
            - Role Name: {role_name}
            - Required Skills: {', '.join(role_skills)}

            Employee Analysis:
            - Skills Match Score: {employee_analysis['skill_match_percentage']}%
            - Experience Level: {employee_analysis['experience_level']}
            - Years of Experience: {employee_analysis['years_experience']}
            - Matching Skills: {', '.join(employee_analysis['matching_skills'])}
            - Missing Skills: {', '.join(employee_analysis['missing_skills'])}
            - Skill Proficiency Estimate: {employee_analysis['estimated_proficiency']}
            - Role Alignment: {employee_analysis['role_alignment']}%

            Based on this analysis, generate realistic KPIs that:
            1. Account for the employee's current skill level (not everyone performs at 100%)
            2. Consider missing skills that may impact productivity
            3. Adjust expectations based on experience level
            4. Include learning curve considerations for missing skills
            5. Set achievable targets that promote growth

            For each KPI category, adjust the targets based on:
            - Junior (0-2 years): 60-70% of ideal performance
            - Mid-level (2-5 years): 75-85% of ideal performance  
            - Senior (5+ years): 85-95% of ideal performance
            - Skill gaps should further reduce expectations by 5-10% per major missing skill

            Generate KPIs with realistic current values and achievable targets.
            Return as valid JSON matching the project KPI structure.
            """

            # Get KPI suggestions from OpenAI
            kpi_response = openai_service.generate_completion(prompt, temperature=0.3, max_tokens=2000)

            # Parse and validate response
            individual_kpis = json.loads(kpi_response)

            # Apply skill-based adjustments
            individual_kpis = IndividualKPIGenerator._apply_skill_based_adjustments(
                individual_kpis, employee_analysis, role_criteria
            )

            return individual_kpis

        except Exception as e:
            print(f"Error generating AI-based individual KPIs: {e}")
            # Enhanced fallback method
            return IndividualKPIGenerator._generate_skill_based_kpis(
                project_kpis, role_criteria, employee, employee_analysis
            )

    @staticmethod
    def _analyze_employee_capabilities(employee, role_criteria):
        """
        Analyze employee's actual capabilities compared to role requirements.
        """
        if not employee:
            return {
                'skill_match_percentage': 0,
                'experience_level': 'Unknown',
                'years_experience': 0,
                'matching_skills': [],
                'missing_skills': role_criteria.get('skills', []),
                'estimated_proficiency': 'Beginner',
                'role_alignment': 0
            }

        # Get employee data
        employee_skills = employee.get('Skills', [])
        required_skills = role_criteria.get('skills', [])

        # Calculate skill match
        match_percentage, matched_skills, missing_skills = SkillMatcher.calculate_skill_match(
            employee_skills, required_skills
        )

        # Analyze experience
        from modules.employee_matching.experience_analyzer import ExperienceAnalyzer
        experience_items = employee.get('Experience', [])
        years_experience = ExperienceAnalyzer.get_years_of_experience(experience_items)
        experience_level = ExperienceAnalyzer.get_experience_level(years_experience)

        # Estimate proficiency based on experience and skills
        proficiency = IndividualKPIGenerator._estimate_proficiency(
            years_experience, match_percentage, len(employee_skills)
        )

        # Calculate role alignment
        role_name = role_criteria.get('role', '')
        has_relevant_exp, _, exp_score = ExperienceAnalyzer.has_relevant_experience(
            experience_items, role_name
        )

        role_alignment = (match_percentage * 0.6 + (exp_score / 100) * 0.4) * 100

        return {
            'skill_match_percentage': round(match_percentage * 100, 1),
            'experience_level': experience_level,
            'years_experience': years_experience,
            'matching_skills': matched_skills,
            'missing_skills': missing_skills,
            'estimated_proficiency': proficiency,
            'role_alignment': round(role_alignment, 1)
        }

    @staticmethod
    def _estimate_proficiency(years_experience, skill_match, total_skills):
        """
        Estimate overall proficiency level based on multiple factors.
        """
        # Weight factors
        exp_weight = 0.4
        skill_match_weight = 0.4
        skill_breadth_weight = 0.2

        # Normalize years of experience (0-1 scale, capped at 10 years)
        exp_score = min(years_experience / 10, 1.0)

        # Skill breadth score (having many skills indicates broader knowledge)
        breadth_score = min(total_skills / 20, 1.0)

        # Calculate weighted score
        proficiency_score = (
                exp_score * exp_weight +
                skill_match * skill_match_weight +
                breadth_score * skill_breadth_weight
        )

        # Map to proficiency levels
        if proficiency_score >= 0.8:
            return "Expert"
        elif proficiency_score >= 0.6:
            return "Advanced"
        elif proficiency_score >= 0.4:
            return "Intermediate"
        elif proficiency_score >= 0.2:
            return "Beginner"
        else:
            return "Novice"

    @staticmethod
    def _apply_skill_based_adjustments(kpis, employee_analysis, role_criteria):
        """
        Apply realistic adjustments to KPIs based on employee's actual capabilities.
        """
        # Define adjustment factors based on proficiency
        proficiency_factors = {
            "Expert": 0.95,
            "Advanced": 0.85,
            "Intermediate": 0.75,
            "Beginner": 0.65,
            "Novice": 0.55
        }

        base_factor = proficiency_factors.get(employee_analysis['estimated_proficiency'], 0.7)

        # Additional penalty for missing critical skills
        missing_skills_penalty = len(employee_analysis['missing_skills']) * 0.05
        final_factor = max(0.4, base_factor - missing_skills_penalty)

        # Apply adjustments to specific KPIs
        adjusted_kpis = json.loads(json.dumps(kpis))  # Deep copy

        # Productivity adjustments
        if 'productivity' in adjusted_kpis:
            # Velocity should be lower for less experienced/skilled employees
            if 'velocity' in adjusted_kpis['productivity']:
                adjusted_kpis['productivity']['velocity'] = IndividualKPIGenerator._adjust_kpi_value(
                    adjusted_kpis['productivity']['velocity'],
                    final_factor,
                    is_higher_better=True
                )

            # Cycle time should be higher (worse) for less experienced
            if 'cycle_time' in adjusted_kpis['productivity']:
                adjusted_kpis['productivity']['cycle_time'] = IndividualKPIGenerator._adjust_kpi_value(
                    adjusted_kpis['productivity']['cycle_time'],
                    2 - final_factor,  # Inverse for "lower is better" metrics
                    is_higher_better=False
                )

        # Code quality adjustments based on experience
        if 'code_quality' in adjusted_kpis:
            quality_factor = final_factor

            # Less experienced developers typically have lower test coverage
            if 'test_coverage' in adjusted_kpis['code_quality']:
                adjusted_kpis['code_quality']['test_coverage'] = IndividualKPIGenerator._adjust_kpi_value(
                    adjusted_kpis['code_quality']['test_coverage'],
                    quality_factor * 0.9,  # Test coverage is particularly affected
                    is_higher_better=True
                )

        return adjusted_kpis

    @staticmethod
    def _adjust_kpi_value(kpi_data, adjustment_factor, is_higher_better=True):
        """
        Adjust a specific KPI value based on the adjustment factor.
        """
        try:
            # Extract numeric value from target
            target_str = kpi_data.get('target', '')
            if '%' in target_str:
                target_value = float(target_str.rstrip('%'))
                adjusted_value = target_value * adjustment_factor
                adjusted_value = max(0, min(100, adjusted_value))  # Keep percentages in valid range
                kpi_data['target'] = f"{adjusted_value:.1f}%"
            elif ' ' in target_str:
                parts = target_str.split(' ', 1)
                target_value = float(parts[0])
                units = parts[1]
                adjusted_value = target_value * adjustment_factor
                kpi_data['target'] = f"{adjusted_value:.1f} {units}"

            # Update status based on new target
            kpi_data['status'] = IndividualKPIGenerator._calculate_status(
                kpi_data.get('value', ''),
                kpi_data['target'],
                is_higher_better
            )

        except (ValueError, IndexError):
            pass  # Keep original if parsing fails

        return kpi_data

    @staticmethod
    def _calculate_status(value_str, target_str, is_higher_better=True):
        """
        Calculate status based on current value vs target.
        """
        try:
            # Extract numeric values
            value = float(value_str.rstrip('%').split()[0] if ' ' in value_str or '%' in value_str else value_str)
            target = float(target_str.rstrip('%').split()[0] if ' ' in target_str or '%' in target_str else target_str)

            if is_higher_better:
                ratio = value / target if target > 0 else 0
                if ratio >= 0.9:
                    return "On Track"
                elif ratio >= 0.7:
                    return "At Risk"
                else:
                    return "Below Target"
            else:
                # For "lower is better" metrics
                ratio = target / value if value > 0 else 0
                if ratio >= 0.9:
                    return "On Track"
                elif ratio >= 0.7:
                    return "At Risk"
                else:
                    return "Below Target"
        except:
            return "At Risk"  # Default if parsing fails

    @staticmethod
    def _generate_skill_based_kpis(project_kpis, role_criteria, employee, employee_analysis):
        """
        Enhanced fallback method that generates KPIs based on actual employee capabilities.
        """
        # Start with project KPIs as base
        individual_kpis = json.loads(json.dumps(project_kpis))

        # Apply systematic adjustments based on employee analysis
        skill_match = employee_analysis['skill_match_percentage'] / 100
        experience_multiplier = {
            'Junior': 0.7,
            'Mid-level': 0.85,
            'Senior': 0.95,
            'Lead': 1.0
        }.get(employee_analysis['experience_level'], 0.8)

        # Combine factors
        overall_multiplier = (skill_match * 0.6 + experience_multiplier * 0.4)

        # Apply to each KPI category with specific logic
        for category, kpis in individual_kpis.items():
            for kpi_name, kpi_data in kpis.items():
                # Determine if higher or lower is better for this KPI
                lower_is_better = kpi_name in [
                    'cycle_time', 'lead_time', 'defect_density',
                    'code_churn', 'rework_ratio', 'code_review_turnaround_time'
                ]

                # Apply adjustments
                individual_kpis[category][kpi_name] = IndividualKPIGenerator._adjust_kpi_value(
                    kpi_data,
                    2 - overall_multiplier if lower_is_better else overall_multiplier,
                    is_higher_better=not lower_is_better
                )

        return individual_kpis