import os
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from bson.objectid import ObjectId
from datetime import datetime

from services.mongodb_service import mongodb_service
from modules.cv_processing.cv_parser import CVParser
from modules.cv_processing.cv_validator import CVValidator
from utils.file_utils import allowed_file, save_file
from utils.error_handlers import ValidationError, NotFoundError
from utils.json_utils import serialize_mongo

from backend.utils.file_utils import validate_file_type, validate_file_size

cv_blueprint = Blueprint('cv', __name__)


@cv_blueprint.route('/upload', methods=['POST'])
def upload_cv():
    """
    Endpoint for uploading and parsing a CV.
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': 'No file provided'
            }), 400

        file = request.files['file']

        # Check if file has a name
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': 'No file selected'
            }), 400

        # Validate file type
        is_valid, error_msg = validate_file_type(file.filename)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400

        # Validate file size
        is_valid, error_msg = validate_file_size(file)
        if not is_valid:
            return jsonify({
                'success': False,
                'message': error_msg
            }), 400

        # Save the file
        cv_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], 'cvs')
        os.makedirs(cv_folder, exist_ok=True)

        filepath = save_file(file, cv_folder)

        try:
            # Parse the CV
            parsed_data = CVParser.parse_cv(filepath)

            # Validate the parsed CV structure
            is_valid, errors = CVValidator.validate_cv_structure(parsed_data)

            if not is_valid:
                # Still save but mark as having errors
                parsed_data['_validation_errors'] = errors

            # Validate CV content
            is_content_valid, warnings = CVValidator.validate_cv_content(parsed_data)

            if warnings:
                parsed_data['_validation_warnings'] = warnings

            # Add metadata
            parsed_data['_meta']['uploaded_at'] = datetime.now()
            parsed_data['_meta']['original_filename'] = file.filename

            # Save to MongoDB
            cv_id = mongodb_service.insert_one('Resumes', parsed_data)

            # Convert ObjectId to string for JSON response
            parsed_data['_id'] = str(cv_id)

            return jsonify({
                'success': True,
                'message': 'CV uploaded and parsed successfully',
                'cv_id': str(cv_id),
                'data': parsed_data,
                'validation': {
                    'is_valid': is_valid,
                    'errors': errors,
                    'warnings': warnings
                }
            })

        except Exception as parse_error:
            # Log the full error for debugging
            import traceback
            current_app.logger.error(f"CV parsing error: {str(parse_error)}")
            current_app.logger.error(traceback.format_exc())

            # Clean up the uploaded file
            try:
                os.remove(filepath)
            except:
                pass

            return jsonify({
                'success': False,
                'message': f"Error processing CV: {str(parse_error)}",
                'error_type': type(parse_error).__name__
            }), 500

    except Exception as e:
        import traceback
        current_app.logger.error(f"CV upload error: {str(e)}")
        current_app.logger.error(traceback.format_exc())

        return jsonify({
            'success': False,
            'message': f"Error uploading CV: {str(e)}"
        }), 500


@cv_blueprint.route('/parse/<cv_id>', methods=['GET'])
def get_parsed_cv(cv_id):
    """
    Endpoint for retrieving a parsed CV by ID.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(cv_id)

        # Retrieve the CV from MongoDB
        cv_data = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not cv_data:
            raise NotFoundError(f"CV with ID {cv_id} not found")

        return jsonify({
            'success': True,
            'data': serialize_mongo(cv_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error retrieving CV: {str(e)}"
        }), 500


@cv_blueprint.route('/list', methods=['GET'])
def list_cvs():
    """
    Endpoint for listing all parsed CVs.
    """
    try:
        # Retrieve all CVs from MongoDB
        cvs = mongodb_service.find_many('Resumes')

        return jsonify({
            'success': True,
            'total': len(cvs),
            'data': serialize_mongo(cvs)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error listing CVs: {str(e)}"
        }), 500


@cv_blueprint.route('/validate', methods=['POST'])
def validate_cv():
    """
    Endpoint for validating a CV without storing it.
    Accepts JSON data of a parsed CV.
    """
    try:
        data = request.json

        if not data:
            raise ValidationError("No data provided")

        # Validate CV structure
        is_valid_structure, structure_errors = CVValidator.validate_cv_structure(data)

        # Validate CV content
        is_valid_content, content_warnings = CVValidator.validate_cv_content(data)

        return jsonify({
            'success': True,
            'is_valid_structure': is_valid_structure,
            'structure_errors': structure_errors,
            'is_valid_content': is_valid_content,
            'content_warnings': content_warnings
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error validating CV: {str(e)}"
        }), 500


@cv_blueprint.route('/test-parse', methods=['POST'])
def test_cv_parse():
    """Test endpoint to debug CV parsing without file upload."""
    try:
        data = request.json

        if not data or 'text' not in data:
            return jsonify({
                'success': False,
                'message': 'No text provided'
            }), 400

        # Try to parse the provided text
        parsed_data_str = openai_service.parse_cv_data(data['text'])

        # Try to parse as JSON
        try:
            parsed_data = json.loads(parsed_data_str)
            return jsonify({
                'success': True,
                'raw_response': parsed_data_str,
                'parsed_data': parsed_data
            })
        except json.JSONDecodeError as e:
            return jsonify({
                'success': False,
                'message': f'JSON parsing failed: {str(e)}',
                'raw_response': parsed_data_str
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500


@cv_blueprint.route('/recategorize-skills/<cv_id>', methods=['POST'])
def recategorize_skills(cv_id):
    """
    Endpoint to re-categorize skills for an already parsed CV.
    """
    try:
        # Convert string ID to ObjectId
        object_id = ObjectId(cv_id)

        # Retrieve the CV from MongoDB
        cv_data = mongodb_service.find_one('Resumes', {'_id': object_id})

        if not cv_data:
            raise NotFoundError(f"CV with ID {cv_id} not found")

        # Re-categorize skills using AI
        if 'Skills' in cv_data and cv_data['Skills']:
            from modules.cv_processing.cv_parser import CVParser

            # Get fresh AI categorization
            skill_categories = CVParser._categorize_skills_with_ai(cv_data['Skills'])

            # Update the CV data
            if '_derived' not in cv_data:
                cv_data['_derived'] = {}

            cv_data['_derived']['skill_categories'] = skill_categories

            # Update in database
            mongodb_service.update_one(
                'Resumes',
                {'_id': object_id},
                {'$set': {'_derived.skill_categories': skill_categories}}
            )

            return jsonify({
                'success': True,
                'message': 'Skills recategorized successfully',
                'skill_categories': skill_categories
            })
        else:
            return jsonify({
                'success': False,
                'message': 'No skills found to categorize'
            }), 400

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f"Error recategorizing skills: {str(e)}"
        }), 500
