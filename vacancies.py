import json
import enum
import logging

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
    def __init__(self):
        self.uri = "https://api.hh.ru/"
        self.headers = {
            "User-Agent": "hh-parser/2.0 (test@mail.ru)",
        }

    @property
    def uri_vacancies(self):
        return self.uri + 'vacancies'

    @property
    def uri_dictionaries(self):
        return self.uri + 'dictionaries'

    @property
    def uri_areas(self):
        return self.uri + 'areas'

    def get_areas(self):
        params = {'locale': 'RU'}
        result = requests.get(self.uri_areas, headers=self.headers, params=params)
        country_russia = 'Россия'
        if result.status_code == 200:
            result_json = result.json()
            for country in result_json:
                if country['name'] == country_russia:
                    return country['areas']
            else:
                raise ValueError(f'No country with name {country_russia}')
        else:
            raise ValueError(f'Error getting dictionaries: {result.status_code = }, {result.text}')

    def get_dictionaries(self):
        result = requests.get(self.uri_dictionaries, headers=self.headers)
        if result.status_code == 200:
            result_json = result.json()
            return result_json
        else:
            raise ValueError(f'Error getting dictionaries: {result.status_code = }, {result.text}')

    def get_experience(self, name: str) -> str:
        name = Experience(name).value
        experience_list = self.get_dictionaries()['experience']
        for row in experience_list:
            if row['name'] == name:
                return row['id']
        else:
            raise ValueError(f'Experience not found in list: {str(experience_list)}')

    def get_vacancies(self, query_filter: dict) -> dict:
        result = requests.get(self.uri_vacancies, params=query_filter, headers=self.headers)
        if result.status_code == 200:
            logging.debug(f'Request to {self.uri_vacancies} OK')
            result_json = result.json()
            return result_json
        else:
            logging.error(f'Error getting vacancies: {result.status_code = }, {result.text}')
            return {}

    def find_area_id(self, city: str) -> str:
        areas = self.get_areas()
        for area in areas:
            if area['name'] == city:
                return area['id']
        else:
            raise ValueError(f'No city with name {city}')

    def parse_vacancies(self):
        logging.info('Started parsing hh.ru')
        filter_city = 'Москва'
        filter_experience = 'От 3 до 6 лет'
        query_filter = {
            'text': 'Python',
            'area': self.find_area_id(filter_city),
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
            pages = vacancies_page_result['pages']
            if query_filter['page'] == pages - 1:
                logging.info(f'Got all pages of vacancies.')
                return result
            else:
                query_filter['page'] += 1
                result += vacancies_page_result['items']

    @staticmethod
    def write_vacancies(vacancies_list: list[dict], filename: str):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(json.dumps(vacancies_list, ensure_ascii=False, indent=2))
            logging.info(f'All vacancies saved as {filename}')


if __name__ == '__main__':
    api = ApiHH()
    vacancies = api.parse_vacancies()
    api.write_vacancies(vacancies, 'vacancies.json')
