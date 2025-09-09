import enum

import requests


class Experience(enum.Enum):
    no_experience = 'Нет опыта'
    between_1_and_3 = 'От 1 года до 3 лет'
    between_3_and_6 = 'От 3 до 6 лет'
    more_than_6 = 'Более 6 лет'


class ApiHH:
    def __init__(self):
        self.uri = "https://api.hh.ru/"
        self.headers = {
            "User-Agent": "hh-parser/2.0 (sampaccs@mail.ru)",
        }

    @property
    def uri_vacancies(self):
        return self.uri + 'vacancies'

    @property
    def uri_dictionaries(self):
        return self.uri + 'dictionaries'

    def get_dictionaries(self):
        result = requests.get(self.uri_dictionaries, headers=self.headers)
        result_json = result.json()
        return result_json

    def get_experience(self, name: str) -> str:
        name = Experience(name).value
        experience_list = self.get_dictionaries()['experience']
        for row in experience_list:
            if row['name'] == name:
                return row['id']
        else:
            print(f'Experience not found in list: {str(experience_list)}')

    def get_vacancies(self) -> dict:
        vacancies_filter = {
            'text': 'Python',
            'experience': self.get_experience('От 3 до 6 лет')
        }
        result = requests.get(self.uri_vacancies, params=vacancies_filter, headers=self.headers)
        result_json = result.json()
        return result_json


if __name__ == '__main__':
    api = ApiHH()
    print(api.get_vacancies())
