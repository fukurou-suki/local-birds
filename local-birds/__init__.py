import requests
import os
from geopy.distance import geodesic
import smtplib
from email.mime.text import MIMEText
from formatter import build_html_from_observations, build_markdown_from_observations
from dotenv import load_dotenv

load_dotenv()

def get_current_location_by_ip():
    # Get public IP address and its location
    ip_request = requests.get('http://ipinfo.io/json')
    ip_address = ip_request.json()
    return {
        'ip': ip_address['ip'],
        'city': ip_address['city'],
        'region': ip_address['region'],
        'country': ip_address['country'],
        'lat': ip_address['loc'].split(',')[0],
        'lng': ip_address['loc'].split(',')[1],
        'org': ip_address['org'],
        'postal': ip_address['postal'],
        'timezone': ip_address['timezone'],
    }

location_info = get_current_location_by_ip()
print('IP location:')
print(location_info)
CURRENT_LOCATION_LATITUDE = location_info['lat']
CURRENT_LOCATION_LONGITUDE = location_info['lng']
CURRENT_LOCATION = (CURRENT_LOCATION_LATITUDE, CURRENT_LOCATION_LONGITUDE, 'Current Location')

LOCATION_CORDINATES = os.getenv('LOCATION_CORDINATES')
locations = [CURRENT_LOCATION]
if LOCATION_CORDINATES:
    locations = []
    locs = LOCATION_CORDINATES.split('/')
    for loc in locs:
        loc_name = loc.split(':')[0].strip()
        loc_latitude = float(loc.split(':')[1].split(',')[0].strip())
        loc_longitude = float(loc.split(':')[1].split(',')[1].strip())
        locations.append((loc_latitude, loc_longitude, loc_name))

location_list = ', '.join([location[2] for location in locations])
FILTER_MODE = os.getenv('FILTER_MODE')
ADDITIONAL_SPECIES_CODES = os.getenv('ADDITIONAL_SPECIES_CODES')
additional_species_codes = [code.strip() for code in ADDITIONAL_SPECIES_CODES.split(',')] if ADDITIONAL_SPECIES_CODES else []
DAYS_BACK = os.getenv('DAYS_BACK')
MAX_DISTANCE_FROM_LOCATION = os.getenv('MAX_DISTANCE_FROM_LOCATION')
additional_species_desc = f'and additionals({ADDITIONAL_SPECIES_CODES}) ' if ADDITIONAL_SPECIES_CODES else ''
filter_description = f'Notable observations {additional_species_desc}in last {DAYS_BACK} days within {MAX_DISTANCE_FROM_LOCATION}mi of {location_list}' if FILTER_MODE == 'NOTABLE' else f'Owl observations in last {DAYS_BACK} days within {MAX_DISTANCE_FROM_LOCATION}mi of {location_list}'

def send_email(observations, subject, recipients):
    # The email address and password you use to send the email
    SENDER_EMAIL_ADDRESS = os.getenv('SENDER_EMAIL_ADDRESS')
    # If you use Gmail, you need to generate an app password
    SENDER_EMAIL_PASSWORD = os.getenv('SENDER_EMAIL_PASSWORD')

    body = build_html_from_observations(observations, filter_description)
    msg = MIMEText(body, 'html')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL_ADDRESS
    msg['To'] = recipients
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
        smtp_server.login(SENDER_EMAIL_ADDRESS, SENDER_EMAIL_PASSWORD)
        smtp_server.send_message(msg)
    print("Email sent!")

def send_telegram_message(observations):
    markdown = build_markdown_from_observations(observations, filter_description)
    print(markdown)

    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    telegram_bot_uri = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage';

    requests.post(telegram_bot_uri, data={'chat_id': TELEGRAM_CHAT_ID, 'text': markdown, 'parse_mode': 'Markdown','disable_web_page_preview': 'true'})
    print("Telegram message sent!")

# eBird API key
EBIRD_API_KEY = os.getenv('EBIRD_API_KEY')

# change if you prefer to use region code instead of ip address
CURRENT_REGION_CODE='US-CA-085'
SPECIES_CODES=['grhowl', 'brnowl', 'wesowl1', 'nopowl', 'nswowl', 'brdowl', 'burowl']

EBIRD_REPORT_PREFIX = 'https://ebird.org/checklist/'
DEFAULT_DAYS_BACK = 1
DEFAULT_MAX_DISTANCE_KM = 50
DEFAULT_MAX_RESULT = 100

CHECKLIST_BASE_URL = 'https://api.ebird.org/v2/product/checklist/view/'
OBSERVATION_BASE_URL = 'https://api.ebird.org/v2/data/obs/'
NEAREST_OBSERVATION_BASE_URL = 'https://api.ebird.org/v2/data/nearest/geo/recent/'
RECENT_NEARBY_NOTABLE_OBSERVATION_BASE_URL = 'https://api.ebird.org/v2/data/obs/geo/recent/notable/'


# Change the email subject to your preference
EMAIL_SUBJECT = os.getenv('EMAIL_SUBJECT')
# Change the recipients to your email addresses
RECIPIENTS = os.getenv('EMAIL_RECIPIENTS')

def main():
    responses = []
    max_distance_in_km = int(int(MAX_DISTANCE_FROM_LOCATION)*1.6)
    if FILTER_MODE == 'NOTABLE':
        for coordinate in locations:
            responses.append(get_notable_observations_from_coordinate(coordinate, max_distance_in_km, DAYS_BACK))
        for species_code in additional_species_codes:
            for coordinate in locations:
                responses.append(get_observations_from_coordinate_by_specicies(species_code, coordinate, max_distance_in_km, DAYS_BACK, 20))
    elif FILTER_MODE == 'OWL':
        for species_code in SPECIES_CODES:
            for coordinate in locations:
                responses.append(get_observations_from_coordinate_by_specicies(species_code, coordinate, max_distance_in_km, DAYS_BACK))
    results = []
    for resp in responses:
        for observation in resp['response']:
            results.append(construct_observation_result(observation, resp['from']))
    results.sort(key=lambda x: (x['species'], x['from'], x['distance']))

    if os.getenv('ENABLE_EMAIL_ALERT') == 'true':
        send_email(results, subject = EMAIL_SUBJECT, recipients = RECIPIENTS)

    if os.getenv('ENABLE_TELEGRAM_ALERT') == 'true':
        send_telegram_message(results)


def get_observations_from_region_code(region_code, species_code, days_back=DEFAULT_DAYS_BACK, max_result=DEFAULT_MAX_RESULT, should_include_provisional=False):
    base_url = OBSERVATION_BASE_URL + region_code + '/recent/' + species_code
    params = {
        'back': days_back,
        'maxResults': max_result,
        'includeProvisional': should_include_provisional
    }
    headers = {'X-eBirdApiToken': EBIRD_API_KEY}
    response = requests.get(base_url, headers=headers, params=params).json()
    return response

def get_observations_from_coordinate_by_specicies(species_code, coordinate, dist=DEFAULT_MAX_DISTANCE_KM, days_back=DEFAULT_DAYS_BACK, max_result=DEFAULT_MAX_RESULT, should_include_provisional=False):
    base_url = NEAREST_OBSERVATION_BASE_URL + species_code
    params = {
        'lat': coordinate[0],
        'lng': coordinate[1],
        'dist': dist,
        'back': days_back,
        'maxResults': max_result,
        'includeProvisional': should_include_provisional
    }
    headers = {'X-eBirdApiToken': EBIRD_API_KEY}
    response = requests.get(base_url, headers=headers, params=params).json()
    response_with_from_coordinate = {
        'from': coordinate,
        'response': response,

    }
    return response_with_from_coordinate

def get_notable_observations_from_coordinate(coordinate, dist=DEFAULT_MAX_DISTANCE_KM, days_back=DEFAULT_DAYS_BACK, max_result=DEFAULT_MAX_RESULT):
    base_url = RECENT_NEARBY_NOTABLE_OBSERVATION_BASE_URL
    params = {
        'lat': coordinate[0],
        'lng': coordinate[1],
        'dist': dist,
        'back': days_back,
        'maxResults': max_result
    }
    headers = {'X-eBirdApiToken': EBIRD_API_KEY}
    response = requests.get(base_url, headers=headers, params=params).json()
    response_with_from_coordinate = {
        'from': coordinate,
        'response': response,

    }
    return response_with_from_coordinate


def construct_observation_result(observation, from_coordinate):
        latitude = observation['lat']
        longitude = observation['lng']
        observation_loc = (latitude, longitude)

        distance = geodesic((from_coordinate[0], from_coordinate[1]), observation_loc).miles
        checklist_info = get_checklist_info(observation['subId'])
        return {
            'from': from_coordinate[2],
            'species': observation['comName'],
            'distance': int(distance),
            'howMany': observation.get('howMany', 1),
            'obsDt': observation['obsDt'],
            'locName': observation['locName'],
            'comments': potentially_get_comments(checklist_info, observation['speciesCode']),
            'hasPhotos': '✅' if has_photos(checklist_info, observation['speciesCode']) else '❌',
            'ebird_link': EBIRD_REPORT_PREFIX + observation['subId'],
        }

def get_checklist_info(sub_id):
    headers = {'X-eBirdApiToken': EBIRD_API_KEY}
    response = requests.get(CHECKLIST_BASE_URL + sub_id, headers=headers).json()
    return response

def potentially_get_comments(checklist_info, species_code):
    for observation in checklist_info['obs']:
        if observation['speciesCode'] == species_code:
            return observation.get('comments', None)
    return None

def has_photos(checklist_info, species_code):
    for observation in checklist_info['obs']:
        if observation['speciesCode'] == species_code:
            if not observation.get('mediaCounts', None):
                return False
            if not observation['mediaCounts'].get('P', None):
                return False
            return True
    return None

if __name__ == '__main__':
    main()