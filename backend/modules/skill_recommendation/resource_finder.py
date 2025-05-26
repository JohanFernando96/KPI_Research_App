import requests
from bs4 import BeautifulSoup
import json
from services.openai_service import openai_service
from datetime import datetime
import time


class ResourceFinder:
    """
    Find training resources using web scraping and APIs.
    """

    # API endpoints for course platforms
    PLATFORM_APIS = {
        'coursera': 'https://api.coursera.org/api/courses.v1',
        'udemy': 'https://www.udemy.com/api-2.0/courses',
        'edx': 'https://courses.edx.org/api/courses/v1/courses/',
        'pluralsight': 'https://api.pluralsight.com/api-v0.9/search'
    }

    @staticmethod
    def find_learning_resources(skill_name, skill_level="beginner"):
        """
        Find learning resources for a specific skill using multiple methods.
        """
        resources = []

        # Method 1: Web scraping for free resources
        free_resources = ResourceFinder._scrape_free_resources(skill_name)
        resources.extend(free_resources)

        # Method 2: Course platform search
        course_resources = ResourceFinder._search_course_platforms(skill_name, skill_level)
        resources.extend(course_resources)

        # Method 3: AI-powered recommendation
        ai_resources = ResourceFinder._get_ai_recommendations(skill_name, skill_level)
        resources.extend(ai_resources)

        # Rank and deduplicate resources
        ranked_resources = ResourceFinder._rank_resources(resources, skill_name)

        # Cache results
        mongodb_service.update_one(
            'LearningResources',
            {'skill': skill_name, 'level': skill_level},
            {'$set': {
                'resources': ranked_resources[:20],  # Top 20 resources
                'updated_at': datetime.now()
            }},
            upsert=True
        )

        return ranked_resources[:10]  # Return top 10

    @staticmethod
    def _scrape_free_resources(skill_name):
        """
        Scrape free learning resources from educational websites.
        """
        resources = []

        # Search on GitHub for tutorials and guides
        try:
            github_query = f"{skill_name} tutorial learning awesome"
            github_url = f"https://api.github.com/search/repositories?q={github_query}&sort=stars"

            headers = {'Accept': 'application/vnd.github.v3+json'}
            response = requests.get(github_url, headers=headers, timeout=5)

            if response.status_code == 200:
                data = response.json()
                for repo in data.get('items', [])[:5]:
                    resources.append({
                        'type': 'GitHub Repository',
                        'name': repo['name'],
                        'provider': 'GitHub',
                        'url': repo['html_url'],
                        'description': repo.get('description', ''),
                        'free': True,
                        'stars': repo.get('stargazers_count', 0),
                        'source': 'github'
                    })
        except Exception as e:
            print(f"Error scraping GitHub: {e}")

        # Search on documentation sites
        doc_sites = [
            {'name': 'MDN', 'base_url': 'https://developer.mozilla.org/en-US/search?q='},
            {'name': 'W3Schools', 'base_url': 'https://www.w3schools.com/search/search_result.asp?q='},
            {'name': 'GeeksforGeeks', 'base_url': 'https://www.geeksforgeeks.org/search/?q='}
        ]

        for site in doc_sites:
            try:
                # Note: In production, respect robots.txt and rate limits
                time.sleep(0.5)  # Be respectful

                search_url = f"{site['base_url']}{skill_name}"
                response = requests.get(search_url, timeout=5, headers={
                    'User-Agent': 'Mozilla/5.0 (Educational Purpose Bot)'
                })

                if response.status_code == 200:
                    resources.append({
                        'type': 'Documentation',
                        'name': f"{skill_name} Documentation",
                        'provider': site['name'],
                        'url': search_url,
                        'description': f"Official documentation and tutorials for {skill_name}",
                        'free': True,
                        'source': 'documentation'
                    })
            except Exception as e:
                print(f"Error scraping {site['name']}: {e}")

        return resources

    @staticmethod
    def _search_course_platforms(skill_name, skill_level):
        """
        Search course platforms for paid courses.
        """
        resources = []

        # Simulated course search (in production, use actual APIs with keys)
        platforms = [
            {
                'name': 'Coursera',
                'type': 'Course',
                'price_range': '$39-79/month',
                'certificate': True
            },
            {
                'name': 'Udemy',
                'type': 'Course',
                'price_range': '$20-200',
                'certificate': True
            },
            {
                'name': 'Pluralsight',
                'type': 'Course Path',
                'price_range': '$29-45/month',
                'certificate': False
            }
        ]

        for platform in platforms:
            # Construct search URL (simplified)
            search_url = f"https://www.{platform['name'].lower()}.com/search?q={skill_name}"

            resources.append({
                'type': platform['type'],
                'name': f"{skill_name} {skill_level.title()} Course",
                'provider': platform['name'],
                'url': search_url,
                'description': f"Comprehensive {skill_level} course on {skill_name}",
                'free': False,
                'price_range': platform['price_range'],
                'certificate': platform['certificate'],
                'level': skill_level,
                'source': 'course_platform'
            })

        return resources

    @staticmethod
    def _get_ai_recommendations(skill_name, skill_level):
        """
        Get AI-powered resource recommendations.
        """
        prompt = f"""
        Recommend the best learning resources for "{skill_name}" at {skill_level} level.

        Include:
        1. Free online tutorials/guides (with actual URLs if known)
        2. Recommended books
        3. YouTube channels or playlists
        4. Practice platforms or exercises
        5. Community forums or discussion groups

        Format as JSON array with structure:
        [
            {{
                "type": "Tutorial|Book|Video|Practice|Community",
                "name": "resource name",
                "provider": "provider/author",
                "url": "actual URL or search query",
                "description": "why this resource is good",
                "free": true/false,
                "estimated_time": "2 hours|1 week|etc"
            }}
        ]

        Provide real, high-quality resources. Return only JSON.
        """

        try:
            response = openai_service.generate_completion(prompt, temperature=0.3)
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.endswith('```'):
                response = response[:-3]

            resources = json.loads(response.strip())

            # Add source metadata
            for resource in resources:
                resource['source'] = 'ai_recommendation'
                resource['skill_level'] = skill_level

            return resources

        except Exception as e:
            print(f"Error getting AI recommendations: {e}")
            return []

    @staticmethod
    def _rank_resources(resources, skill_name):
        """
        Rank resources by relevance and quality.
        """
        # Simple ranking based on source trust and features
        source_weights = {
            'github': 0.9,  # High quality, free
            'documentation': 0.85,  # Official docs
            'course_platform': 0.8,  # Structured learning
            'ai_recommendation': 0.7  # Good but verify
        }

        for resource in resources:
            score = source_weights.get(resource.get('source', ''), 0.5)

            # Bonus for free resources
            if resource.get('free', False):
                score += 0.1

            # Bonus for certificates
            if resource.get('certificate', False):
                score += 0.05

            # Bonus for GitHub stars
            if resource.get('stars', 0) > 1000:
                score += 0.1

            resource['relevance_score'] = score

        # Sort by score
        resources.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)

        return resources