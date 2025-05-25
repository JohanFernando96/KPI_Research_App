from modules.employee_matching.skill_matcher import SkillMatcher
from modules.employee_matching.experience_analyzer import ExperienceAnalyzer


class TeamUtils:
    """
    Utility functions for team analysis and optimization.
    """

    @staticmethod
    def calculate_team_diversity_score(team_members):
        """
        Calculate diversity score based on skills and experience.

        Returns:
            float: Diversity score (0-1)
        """
        if len(team_members) <= 1:
            return 0

        # Skill diversity
        all_skills = []
        for member in team_members:
            all_skills.extend(member.get('Skills', []))

        unique_skills = set(all_skills)
        skill_diversity = len(unique_skills) / len(all_skills) if all_skills else 0

        # Experience diversity
        experience_levels = set()
        for member in team_members:
            exp_years = ExperienceAnalyzer.get_years_of_experience(member.get('Experience', []))
            exp_level = ExperienceAnalyzer.get_experience_level(exp_years)
            experience_levels.add(exp_level)

        exp_diversity = len(experience_levels) / 4  # 4 possible levels

        # Combined diversity score
        return (skill_diversity * 0.6 + exp_diversity * 0.4)

    @staticmethod
    def find_skill_overlaps(team_members):
        """
        Find skills that multiple team members share.

        Returns:
            dict: Skill -> count of team members with that skill
        """
        skill_counts = {}

        for member in team_members:
            for skill in member.get('Skills', []):
                skill_lower = skill.lower()
                skill_counts[skill_lower] = skill_counts.get(skill_lower, 0) + 1

        # Return only skills shared by 2+ members
        return {skill: count for skill, count in skill_counts.items() if count >= 2}

    @staticmethod
    def calculate_team_strength_score(team_members, required_skills):
        """
        Calculate overall team strength score.

        Args:
            team_members: List of team members
            required_skills: List of required skills for the project

        Returns:
            dict: Detailed strength analysis
        """
        # Skill coverage
        team_skills = set()
        for member in team_members:
            team_skills.update(member.get('Skills', []))

        covered_skills = 0
        for req_skill in required_skills:
            if any(SkillMatcher.get_similarity(req_skill, team_skill) > 70 for team_skill in team_skills):
                covered_skills += 1

        skill_coverage = covered_skills / len(required_skills) if required_skills else 1.0

        # Experience strength
        total_experience = 0
        senior_count = 0

        for member in team_members:
            years = ExperienceAnalyzer.get_years_of_experience(member.get('Experience', []))
            total_experience += years

            if years >= 5:
                senior_count += 1

        avg_experience = total_experience / len(team_members) if team_members else 0
        seniority_ratio = senior_count / len(team_members) if team_members else 0

        # Collaboration potential (based on shared skills)
        skill_overlaps = TeamUtils.find_skill_overlaps(team_members)
        collaboration_score = min(1.0, len(skill_overlaps) / 5)  # Normalize to max 5 shared skills

        # Overall strength
        overall_score = (
                skill_coverage * 0.4 +
                min(1.0, avg_experience / 5) * 0.3 +  # Normalize experience to 5 years
                seniority_ratio * 0.2 +
                collaboration_score * 0.1
        )

        return {
            'overall_score': round(overall_score * 100, 1),
            'skill_coverage': round(skill_coverage * 100, 1),
            'avg_experience': round(avg_experience, 1),
            'seniority_ratio': round(seniority_ratio * 100, 1),
            'collaboration_potential': round(collaboration_score * 100, 1),
            'shared_skills': list(skill_overlaps.keys())[:5]  # Top 5 shared skills
        }

    @staticmethod
    def suggest_pair_programming_partners(team_members):
        """
        Suggest optimal pair programming partners based on complementary skills.

        Returns:
            list: List of suggested pairings with reasons
        """
        if len(team_members) < 2:
            return []

        pairings = []

        # Analyze each possible pair
        for i in range(len(team_members)):
            for j in range(i + 1, len(team_members)):
                member1 = team_members[i]
                member2 = team_members[j]

                # Get their skills
                skills1 = set(member1.get('Skills', []))
                skills2 = set(member2.get('Skills', []))

                # Calculate complementarity
                shared = skills1 & skills2
                unique_to_1 = skills1 - skills2
                unique_to_2 = skills2 - skills1

                # Get experience levels
                exp1 = ExperienceAnalyzer.get_years_of_experience(member1.get('Experience', []))
                exp2 = ExperienceAnalyzer.get_years_of_experience(member2.get('Experience', []))
                exp_diff = abs(exp1 - exp2)

                # Score the pairing
                score = 0
                reasons = []

                # Good if they have some shared skills (common ground)
                if len(shared) >= 2:
                    score += 0.3
                    reasons.append(f"Share {len(shared)} common skills")

                # Good if they have complementary skills
                if len(unique_to_1) >= 2 and len(unique_to_2) >= 2:
                    score += 0.4
                    reasons.append("Complementary skill sets")

                # Good if experience difference is 2-5 years (mentoring opportunity)
                if 2 <= exp_diff <= 5:
                    score += 0.3
                    reasons.append(f"Good mentoring opportunity ({exp_diff} years difference)")

                if score >= 0.5:  # Threshold for good pairing
                    pairings.append({
                        'member1': {
                            'id': str(member1.get('_id', '')),
                            'name': member1.get('Name', 'Unknown')
                        },
                        'member2': {
                            'id': str(member2.get('_id', '')),
                            'name': member2.get('Name', 'Unknown')
                        },
                        'score': score,
                        'reasons': reasons
                    })

        # Sort by score
        pairings.sort(key=lambda x: x['score'], reverse=True)

        return pairings[:5]  # Return top 5 pairings

    @staticmethod
    def identify_knowledge_silos(team_members):
        """
        Identify potential knowledge silos in the team.

        Returns:
            list: Skills that only one person knows
        """
        skill_holders = {}

        for member in team_members:
            for skill in member.get('Skills', []):
                skill_lower = skill.lower()
                if skill_lower not in skill_holders:
                    skill_holders[skill_lower] = []
                skill_holders[skill_lower].append({
                    'id': str(member.get('_id', '')),
                    'name': member.get('Name', 'Unknown')
                })

        # Find skills with only one holder
        silos = []
        for skill, holders in skill_holders.items():
            if len(holders) == 1:
                silos.append({
                    'skill': skill,
                    'holder': holders[0],
                    'risk': 'High' if skill in ['database', 'security', 'deployment'] else 'Medium'
                })

        return silos