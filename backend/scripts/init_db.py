#!/usr/bin/env python
"""
Script to initialize the application database and create necessary collections.
Run this after setting up MongoDB to ensure proper structure and indexes.
"""

import os
import sys
import json
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
import argparse

# Add parent directory to path so we can import from project modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import project configurations
from config import active_config


def init_database(drop_existing=False, sample_data=False):
    """
    Initialize the MongoDB database and collections with proper indexes.

    Args:
        drop_existing: Whether to drop existing collections (dangerous in production!)
        sample_data: Whether to populate with sample data for development/testing
    """
    print(f"Connecting to MongoDB at {active_config.MONGO_URI}...")
    client = MongoClient(active_config.MONGO_URI)
    db = client[active_config.MONGO_DB]

    print(f"Connected to database '{active_config.MONGO_DB}'")

    # Drop existing collections if requested
    if drop_existing:
        print("Dropping existing collections...")
        for collection in ['Resumes', 'Projects', 'ProjectKPIs', 'DevelopmentPlans']:
            db.drop_collection(collection)
            print(f"  Dropped collection: {collection}")

    # Create Resumes collection with indexes
    print("Setting up Resumes collection...")
    resumes_collection = db['Resumes']
    resumes_collection.create_index([('Name', ASCENDING)], background=True)
    resumes_collection.create_index([('Skills', ASCENDING)], background=True)

    # Create Projects collection with indexes
    print("Setting up Projects collection...")
    projects_collection = db['Projects']
    projects_collection.create_index([('name', ASCENDING)], background=True)
    projects_collection.create_index([('project_type', ASCENDING)], background=True)
    projects_collection.create_index([('status', ASCENDING)], background=True)
    projects_collection.create_index([('created_at', DESCENDING)], background=True)

    # Create ProjectKPIs collection with indexes
    print("Setting up ProjectKPIs collection...")
    kpis_collection = db['ProjectKPIs']
    kpis_collection.create_index([('project_id', ASCENDING)], unique=True, background=True)

    # Create DevelopmentPlans collection with indexes
    print("Setting up DevelopmentPlans collection...")
    plans_collection = db['DevelopmentPlans']
    plans_collection.create_index([('employee_id', ASCENDING)], background=True)

    # Insert sample data if requested
    if sample_data:
        insert_sample_data(db)

    print("Database initialization complete!")


def insert_sample_data(db):
    """Insert sample data for development and testing purposes."""
    print("Adding sample data...")

    # Sample employee/resume data
    sample_resumes = [
        {
            "Name": "John Doe",
            "Contact Information": {
                "Email": "john.doe@example.com",
                "Phone": "+1 (555) 123-4567",
                "Address": "123 Main St, Anytown, USA",
                "LinkedIn": "linkedin.com/in/johndoe"
            },
            "Skills": ["Python", "JavaScript", "React", "Node.js", "MongoDB", "Docker"],
            "Experience": [
                {
                    "Role": "Senior Software Engineer",
                    "Company": "Tech Solutions Inc.",
                    "Duration": "2020-01 - Present",
                    "Responsibilities": [
                        "Developed scalable web applications using React and Node.js",
                        "Implemented CI/CD pipelines using Docker and GitHub Actions",
                        "Mentored junior developers and led code reviews"
                    ]
                },
                {
                    "Role": "Software Developer",
                    "Company": "WebApp Creators",
                    "Duration": "2017-03 - 2019-12",
                    "Responsibilities": [
                        "Built RESTful APIs using Express and MongoDB",
                        "Developed frontend components with React",
                        "Implemented automated tests using Jest and Cypress"
                    ]
                }
            ],
            "Education": [
                {
                    "Degree": "B.S. Computer Science",
                    "Institution": "University of Technology",
                    "Duration": "2013-09 - 2017-05",
                    "Details": "GPA 3.8/4.0, Dean's List"
                }
            ],
            "_derived": {
                "total_years_experience": 6,
                "skill_categories": {
                    "programming": ["Python", "JavaScript"],
                    "frameworks": ["React", "Node.js"],
                    "databases": ["MongoDB"],
                    "other": ["Docker"]
                }
            }
        },
        {
            "Name": "Jane Smith",
            "Contact Information": {
                "Email": "jane.smith@example.com",
                "Phone": "+1 (555) 987-6543",
                "Address": "456 Oak Ave, Somewhere, USA",
                "LinkedIn": "linkedin.com/in/janesmith"
            },
            "Skills": ["Java", "Spring Boot", "AWS", "MySQL", "Kubernetes", "Terraform"],
            "Experience": [
                {
                    "Role": "DevOps Engineer",
                    "Company": "Cloud Solutions Ltd.",
                    "Duration": "2019-06 - Present",
                    "Responsibilities": [
                        "Implemented infrastructure as code using Terraform and AWS CloudFormation",
                        "Managed Kubernetes clusters for microservices deployment",
                        "Automated deployment pipelines using Jenkins and GitLab CI"
                    ]
                },
                {
                    "Role": "Backend Developer",
                    "Company": "Enterprise Systems Co.",
                    "Duration": "2016-08 - 2019-05",
                    "Responsibilities": [
                        "Developed microservices using Java and Spring Boot",
                        "Implemented database solutions with MySQL and PostgreSQL",
                        "Created and maintained RESTful APIs"
                    ]
                }
            ],
            "Education": [
                {
                    "Degree": "M.S. Software Engineering",
                    "Institution": "State Technical University",
                    "Duration": "2014-09 - 2016-05",
                    "Details": "Thesis on distributed systems"
                },
                {
                    "Degree": "B.S. Computer Engineering",
                    "Institution": "Engineering College",
                    "Duration": "2010-09 - 2014-05",
                    "Details": "Graduated with honors"
                }
            ],
            "_derived": {
                "total_years_experience": 7,
                "skill_categories": {
                    "programming": ["Java"],
                    "frameworks": ["Spring Boot"],
                    "databases": ["MySQL"],
                    "other": ["AWS", "Kubernetes", "Terraform"]
                }
            }
        }
    ]

    # Insert sample resume data
    if db['Resumes'].count_documents({}) == 0:
        db['Resumes'].insert_many(sample_resumes)
        print(f"Added {len(sample_resumes)} sample resumes")

    # Sample project data
    sample_projects = [
        {
            "name": "E-Commerce Platform Redesign",
            "project_type": "Web Development",
            "project_timeline": 120,
            "project_team_size": 5,
            "project_languages": ["React", "Node.js", "MongoDB", "Express", "Redis"],
            "project_sprints": 6,
            "description": "Redesign and modernize the existing e-commerce platform to improve user experience and performance.",
            "status": "In Progress",
            "created_at": datetime.now()
        },
        {
            "name": "Mobile Banking App",
            "project_type": "Mobile Development",
            "project_timeline": 90,
            "project_team_size": 4,
            "project_languages": ["React Native", "Node.js", "Firebase", "Swift", "Kotlin"],
            "project_sprints": 5,
            "description": "Develop a secure mobile banking application with biometric authentication and real-time transaction monitoring.",
            "status": "Planning",
            "created_at": datetime.now()
        }
    ]

    # Insert sample project data
    project_ids = []
    if db['Projects'].count_documents({}) == 0:
        result = db['Projects'].insert_many(sample_projects)
        project_ids = result.inserted_ids
        print(f"Added {len(sample_projects)} sample projects")

    # Add sample KPIs for each project
    if project_ids and db['ProjectKPIs'].count_documents({}) == 0:
        from modules.kpi_generation.kpi_generator import KPIGenerator
        from modules.kpi_generation.chart_generator import ChartGenerator

        for i, project_id in enumerate(project_ids):
            project = sample_projects[i]

            # Generate KPIs
            kpis = KPIGenerator.generate_kpis(project)

            # Generate Gantt chart data
            gantt_data = KPIGenerator.generate_gantt_chart_data(project)

            # Generate employee criteria
            employee_criteria = KPIGenerator.generate_employee_criteria(project)

            # Generate sprint breakdown
            sprint_breakdown = KPIGenerator.generate_sprint_breakdown(project)

            # Create KPI document
            kpi_doc = {
                "project_id": project_id,
                "kpis": kpis,
                "gantt_chart_data": gantt_data,
                "employee_criteria": employee_criteria,
                "sprint_breakdown": sprint_breakdown,
                "charts": {},
                "project_details": project,
                "created_at": datetime.now()
            }

            # Save KPIs to MongoDB
            db['ProjectKPIs'].insert_one(kpi_doc)

            # Update project with KPI ID
            db['Projects'].update_one(
                {"_id": project_id},
                {"$set": {"kpi_id": kpi_doc['_id']}}
            )

        print(f"Added KPIs for {len(project_ids)} sample projects")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Initialize the application database')
    parser.add_argument('--drop', action='store_true', help='Drop existing collections before initialization')
    parser.add_argument('--sample-data', action='store_true', help='Add sample data for development/testing')

    args = parser.parse_args()

    init_database(drop_existing=args.drop, sample_data=args.sample_data)