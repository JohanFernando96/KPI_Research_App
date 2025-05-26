# backend/modules/cv_processing/cv_validator.py

import re  # Add this import at the top


class CVValidator:
    """Class for validating parsed CV data."""

    @staticmethod
    def validate_cv_structure(cv_data):
        """
        Validate the structure of parsed CV data.

        Args:
            cv_data: Parsed CV data to validate.

        Returns:
            tuple: (is_valid, errors) where is_valid is a boolean and errors is a list of error messages.
        """
        errors = []

        # Check for required top-level fields
        required_fields = ['Name', 'Contact Information', 'Skills', 'Experience', 'Education']
        for field in required_fields:
            if field not in cv_data:
                errors.append(f"Missing required field: {field}")

        # Validate Contact Information
        if 'Contact Information' in cv_data:
            contact_info = cv_data['Contact Information']
            if not isinstance(contact_info, dict):
                errors.append("Contact Information must be an object")
            else:
                contact_fields = ['Email', 'Phone']
                for field in contact_fields:
                    if field not in contact_info or not contact_info[field]:
                        errors.append(f"Missing required contact information: {field}")

        # Validate Skills
        if 'Skills' in cv_data:
            skills = cv_data['Skills']
            if not isinstance(skills, list):
                errors.append("Skills must be an array")
            elif len(skills) == 0:
                errors.append("Skills array is empty")

        # Validate Experience
        if 'Experience' in cv_data:
            experience = cv_data['Experience']
            if not isinstance(experience, list):
                errors.append("Experience must be an array")
            else:
                for i, exp in enumerate(experience):
                    if not isinstance(exp, dict):
                        errors.append(f"Experience item {i} must be an object")
                    else:
                        exp_fields = ['Role', 'Company', 'Duration']
                        for field in exp_fields:
                            if field not in exp or not exp[field]:
                                errors.append(f"Missing required experience field in item {i}: {field}")

        # Validate Education
        if 'Education' in cv_data:
            education = cv_data['Education']
            if not isinstance(education, list):
                errors.append("Education must be an array")
            else:
                for i, edu in enumerate(education):
                    if not isinstance(edu, dict):
                        errors.append(f"Education item {i} must be an object")
                    else:
                        edu_fields = ['Degree', 'Institution']
                        for field in edu_fields:
                            if field not in edu or not edu[field]:
                                errors.append(f"Missing required education field in item {i}: {field}")

        # Overall validation result
        is_valid = len(errors) == 0

        return is_valid, errors

    @staticmethod
    def validate_cv_content(cv_data):
        """
        Validate the content of parsed CV data.

        Args:
            cv_data: Parsed CV data to validate.

        Returns:
            tuple: (is_valid, warnings) where is_valid is a boolean and warnings is a list of warning messages.
        """
        warnings = []

        # Check name format
        if 'Name' in cv_data and cv_data['Name']:
            name = cv_data['Name']
            if len(name.split()) < 2:
                warnings.append("Name might be incomplete (less than two words)")

        # Check email format
        if 'Contact Information' in cv_data and 'Email' in cv_data['Contact Information']:
            email = cv_data['Contact Information']['Email']
            if email and '@' not in email:
                warnings.append("Email address format might be invalid")

        # Check for reasonable number of skills
        if 'Skills' in cv_data and isinstance(cv_data['Skills'], list):
            num_skills = len(cv_data['Skills'])
            if num_skills < 3:
                warnings.append("Very few skills listed (less than 3)")
            elif num_skills > 30:
                warnings.append("Unusually high number of skills (more than 30)")

        # Check for reasonable experience
        if 'Experience' in cv_data and isinstance(cv_data['Experience'], list):
            num_exp = len(cv_data['Experience'])
            if num_exp == 0:
                warnings.append("No work experience listed")

        # Check for education
        if 'Education' in cv_data and isinstance(cv_data['Education'], list):
            num_edu = len(cv_data['Education'])
            if num_edu == 0:
                warnings.append("No education listed")

        # Validate certifications
        if 'Certifications and Courses' in cv_data and isinstance(cv_data['Certifications and Courses'], list):
            certs = cv_data['Certifications and Courses']
            invalid_certs = []

            for cert in certs:
                if not isinstance(cert, str):
                    invalid_certs.append(cert)
                    continue

                # Check if certification is just a single character or list marker
                cert_trimmed = cert.strip()
                if len(cert_trimmed) <= 2 or cert_trimmed in ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j']:
                    invalid_certs.append(cert)
                # Fix: Use re.match instead of string.match
                elif re.match(r'^[0-9][\.\:\-\)]?$', cert_trimmed):  # Matches "1.", "2:", etc.
                    invalid_certs.append(cert)

            if invalid_certs:
                warnings.append(
                    f"Found {len(invalid_certs)} invalid certification entries (single characters or list markers)")

        # Overall content validation result (warnings don't invalidate the CV)
        is_valid = True

        return is_valid, warnings