import json
import enum
import logging
import time

import requests

logging.basicConfig(
    level=logging.INFO,
)


class Experience(enum.Enum):
    no_experience = 'Нет опыта'
    between_1_and_3 = 'От 1 года до 3 лет'
    between_3_and_6 = 'От 3 до 6 лет'
    more_than_6 = 'Более 6 лет'


class ApiHH:
    """Класс для работы с API hh.ru"""
    BASE_URI = "https://api.hh.ru"
    DEFAULT_HEADERS = {
        "User-Agent": "hh-parser/2.0 (test@mail.ru)",
    }
    REQUEST_DELAY = 0.5

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.DEFAULT_HEADERS)
        self._dictionaries_cache = None
        self._areas_cache = None

    def get_areas(self, country_name):
        if self._areas_cache:
            return self._areas_cache

        try:
            params = {'locale': 'RU'}
            result = self.session.get(f'{self.BASE_URI}/areas', params=params)
            result.raise_for_status()

            result_json = result.json()
            for country in result_json:
                if country['name'] == country_name:
                    self._areas_cache = country['areas']
                    return self._areas_cache
        except requests.exceptions.RequestException as e:
            logging.error(f'Error getting areas: {e}')
            raise

    def get_dictionaries(self):
        if self._dictionaries_cache:
            return self._dictionaries_cache
        try:
            result = self.session.get(f'{self.BASE_URI}/dictionaries')
            result.raise_for_status()
            self._dictionaries_cache = result.json()
            return self._dictionaries_cache
        except requests.exceptions.RequestException as e:
            raise ValueError(f'Error getting dictionaries: {e}')

    def get_experience(self, name: str) -> str:
        name = Experience(name).value
        experience_list = self.get_dictionaries()['experience']
        for row in experience_list:
            if row['name'] == name:
                return row['id']
        else:
            raise ValueError(f'Experience not found in list: {str(experience_list)}')

    def get_vacancies(self, query_filter: dict) -> dict:
        try:
            result = self.session.get(f'{self.BASE_URI}/vacancies', params=query_filter)
            result.raise_for_status()
            result_json = result.json()
            return result_json
        except requests.exceptions.RequestException as e:
            logging.error(f'Error getting vacancies: {e}')
            raise

    def find_area_id(self, country_name: str, city: str) -> str:
        areas = self.get_areas(country_name)
        for area in areas:
            if area['name'] == city:
                return area['id']
        else:
            raise ValueError(f'No city with name {city}')

    def parse_vacancies(self):
        logging.info('Started parsing hh.ru')
        filter_country = 'Россия'
        filter_city = 'Москва'
        filter_experience = 'От 3 до 6 лет'
        query_filter = {
            'text': 'Python',
            'area': self.find_area_id(filter_country, filter_city),
            'experience': self.get_experience(filter_experience),
            'per_page': 100,
            'page': 0
        }
        logging.info(
            f'Set filters:'
            f'{query_filter}'
        )
        result = []
        while True:
            vacancies_page_result = self.get_vacancies(query_filter)
            time.sleep(0.5)
            pages = vacancies_page_result['pages']
            if query_filter['page'] == pages - 1:
                logging.info(f'Got all pages of vacancies.')
                return result
            else:
                query_filter['page'] += 1
                result += vacancies_page_result['items']

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    @staticmethod
    def write_vacancies(vacancies_list: list[dict], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(vacancies_list, ensure_ascii=False, indent=2))
            logging.info(f'All vacancies saved as {filename}')


if __name__ == '__main__':
    with ApiHH() as api:
        vacancies = api.parse_vacancies()
        api.write_vacancies(vacancies, 'vacancies.json')
