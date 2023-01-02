"""API utils"""

import logging
import requests
from algoliasearch.exceptions import RequestException, AlgoliaUnreachableHostException
from django.conf import settings

from lms.djangoapps.utils import AlgoliaClient

log = logging.getLogger(__name__)


def get_personalized_course_recommendations(user_id):
    """ Get personalize recommendations from Amplitude. """
    headers = {
        'Authorization': f'Api-Key {settings.AMPLITUDE_API_KEY}',
        'Content-Type': 'application/json'
    }
    params = {
        'user_id': user_id,
        'get_recs': True,
        'rec_id': settings.REC_ID,
    }
    try:
        response = requests.get(settings.AMPLITUDE_URL, params=params, headers=headers)
        if response.status_code == 200:
            response = response.json()
            recommendations = response.get('userData', {}).get('recommendations', [])
            if recommendations:
                is_control = recommendations[0].get('is_control')
                recommended_course_keys = recommendations[0].get('items')
                return is_control, recommended_course_keys
    except Exception as ex:  # pylint: disable=broad-except
        log.warning(f'Cannot get recommendations from Amplitude: {ex}')

    return True, []


def get_algolia_courses_recommendation(course_data):
    """ Get personalized courses recommendation from Algolia search. """
    algolia_client = AlgoliaClient.get_algolia_client()
    algolia_index = algolia_client.init_index(settings.ALGOLIA_COURSES_RECOMMENDATION_INDEX_NAME)

    if algolia_client:
        try:
            course_level_type = course_data['level_type']
            search_query = '+'.join(course_data['skill_names'])
            results = algolia_index.search(search_query, {'filters': f'(NOT course_key:{course_data["key"]})'}) # AND (level:"beginner" OR level:"advanced")

            return results.get('hits', [])
        except (AlgoliaUnreachableHostException, RequestException) as ex:
            log.exception(f'Unexpected exception while attempting to fetch courses data from Algolia: {str(ex)}')

    return []
