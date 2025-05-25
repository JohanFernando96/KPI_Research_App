from difflib import SequenceMatcher
import re


class SkillMatcher:
    """
    Class for matching and comparing skills between employees and requirements.
    """

    @staticmethod
    def calculate_skill_similarity(employee_skills, required_skills):
        """
        Calculate similarity between employee skills and required skills.

        Args:
            employee_skills: List of skills the employee has
            required_skills: List of required skills

        Returns:
            float: Similarity score between 0 and 1
        """
        if not required_skills:
            return 1.0

        if not employee_skills:
            return 0.0

        matched = 0
        for req_skill in required_skills:
            if SkillMatcher._has_skill(employee_skills, req_skill):
                matched += 1

        return matched / len(required_skills)

    @staticmethod
    def calculate_skill_match(employee_skills, required_skills):
        """
        Calculate detailed skill match information.

        Args:
            employee_skills: List of skills the employee has
            required_skills: List of required skills

        Returns:
            tuple: (match_percentage, matched_skills, missing_skills)
        """
        if not required_skills:
            return 1.0, [], []

        matched_skills = []
        missing_skills = []

        for req_skill in required_skills:
            matched = False
            for emp_skill in employee_skills:
                if SkillMatcher.get_similarity(req_skill, emp_skill) > 70:
                    matched_skills.append(req_skill)
                    matched = True
                    break

            if not matched:
                missing_skills.append(req_skill)

        match_percentage = len(matched_skills) / len(required_skills) if required_skills else 0

        return match_percentage, matched_skills, missing_skills

    @staticmethod
    def get_skill_gap(employee_skills, required_skills):
        """
        Get the skills that an employee is missing.

        Args:
            employee_skills: List of skills the employee has
            required_skills: List of required skills

        Returns:
            list: Skills that the employee doesn't have
        """
        if not required_skills:
            return []

        missing_skills = []
        for req_skill in required_skills:
            if not SkillMatcher._has_skill(employee_skills, req_skill):
                missing_skills.append(req_skill)

        return missing_skills

    @staticmethod
    def calculate_skill_compatibility(employee_skills, required_skills):
        """
        Calculate comprehensive skill compatibility metrics.

        Args:
            employee_skills: List of skills the employee has
            required_skills: List of required skills

        Returns:
            dict: Compatibility metrics
        """
        match_percentage, matched_skills, missing_skills = SkillMatcher.calculate_skill_match(
            employee_skills, required_skills
        )

        # Calculate additional metrics
        extra_skills = [skill for skill in employee_skills if skill not in matched_skills]

        return {
            'match_percentage': round(match_percentage * 100, 1),
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'extra_skills': extra_skills[:10],  # Limit to top 10
            'total_skills': len(employee_skills),
            'required_skills_count': len(required_skills),
            'compatibility_score': SkillMatcher._calculate_compatibility_score(
                match_percentage, len(extra_skills), len(employee_skills)
            )
        }

    @staticmethod
    def get_similarity(skill1, skill2):
        """
        Calculate similarity between two skills.

        Args:
            skill1: First skill string
            skill2: Second skill string

        Returns:
            float: Similarity percentage (0-100)
        """
        if not skill1 or not skill2:
            return 0.0

        # Normalize skills for comparison
        skill1_normalized = SkillMatcher._normalize_skill(skill1)
        skill2_normalized = SkillMatcher._normalize_skill(skill2)

        # Exact match
        if skill1_normalized == skill2_normalized:
            return 100.0

        # Check for common variations
        if SkillMatcher._are_skill_variations(skill1_normalized, skill2_normalized):
            return 90.0

        # Use sequence matching for similarity
        similarity = SequenceMatcher(None, skill1_normalized, skill2_normalized).ratio()

        # Check for substring matches
        if skill1_normalized in skill2_normalized or skill2_normalized in skill1_normalized:
            similarity = max(similarity, 0.8)

        return similarity * 100

    @staticmethod
    def _normalize_skill(skill):
        """Normalize a skill string for comparison."""
        # Convert to lowercase and remove extra spaces
        normalized = skill.lower().strip()

        # Remove common variations
        normalized = re.sub(r'\.js$', '', normalized)  # Remove .js suffix
        normalized = re.sub(r'js$', '', normalized)  # Remove js suffix
        normalized = re.sub(r'\s+', ' ', normalized)  # Normalize spaces

        # Common replacements
        replacements = {
            'javascript': 'javascript',
            'js': 'javascript',
            'node.js': 'nodejs',
            'node': 'nodejs',
            'react.js': 'react',
            'vue.js': 'vue',
            'angular.js': 'angular',
            'mongodb': 'mongodb',
            'mongo': 'mongodb',
            'postgresql': 'postgresql',
            'postgres': 'postgresql',
            'mysql': 'mysql',
            'ms sql': 'sql server',
            'mssql': 'sql server',
        }

        for old, new in replacements.items():
            if normalized == old:
                normalized = new
                break

        return normalized

    @staticmethod
    def _are_skill_variations(skill1, skill2):
        """Check if two skills are known variations of each other."""
        variations = [
            {'javascript', 'js', 'ecmascript'},
            {'typescript', 'ts'},
            {'python', 'py'},
            {'c++', 'cpp', 'cplusplus'},
            {'c#', 'csharp', 'c sharp'},
            {'nodejs', 'node', 'node.js'},
            {'react', 'reactjs', 'react.js'},
            {'angular', 'angularjs', 'angular.js'},
            {'vue', 'vuejs', 'vue.js'},
            {'mongodb', 'mongo'},
            {'postgresql', 'postgres'},
            {'docker', 'containers', 'containerization'},
            {'kubernetes', 'k8s'},
            {'aws', 'amazon web services'},
            {'gcp', 'google cloud platform', 'google cloud'},
            {'azure', 'microsoft azure'},
        ]

        for variation_set in variations:
            if skill1 in variation_set and skill2 in variation_set:
                return True

        return False

    @staticmethod
    def _has_skill(employee_skills, required_skill):
        """Check if employee has a required skill (with fuzzy matching)."""
        for emp_skill in employee_skills:
            if SkillMatcher.get_similarity(required_skill, emp_skill) > 70:
                return True
        return False

    @staticmethod
    def _calculate_compatibility_score(match_percentage, extra_skills_count, total_skills):
        """Calculate overall compatibility score."""
        # Base score from match percentage
        base_score = match_percentage * 70

        # Bonus for having relevant extra skills
        extra_skills_bonus = min(extra_skills_count * 2, 20)

        # Bonus for overall skill breadth
        skill_breadth_bonus = min(total_skills * 0.5, 10)

        return min(base_score + extra_skills_bonus + skill_breadth_bonus, 100)