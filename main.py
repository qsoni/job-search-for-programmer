import logging
import os
from pprint import pprint
import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable



def process_vacancy_hh(language, period, area):
    all_salaries = []
    vacancies_found = 0
    total_salary = 0
    vacancies_processed = 0
    average_salary = 0
    headers = {
        'User-Agent': 'dvmnmyapp/1.0 (my-app-feedback@gmail.com)'
    }
    page = 1
    pages = 2
    while page < pages:
        params = {
            'page': page,
            'area': area,
            'text': f'Программист {language}',
            'period': period
        }
        page = page + 1
        url = 'https://api.hh.ru/vacancies'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_on_page = response.json()
        if vacancies_on_page.get('items'):
            vacancies_found = vacancies_on_page['found']
            pages = vacancies_on_page['pages']
            for vacancy in vacancies_on_page['items']:
                salary = vacancy.get('salary')
                if salary:
                    currency = vacancy.get('salary').get('currency')
                    salary_from = salary.get('from')
                    salary_to = salary.get('to')
                    predicted_salary = predict_rub_salary(currency, salary_from, salary_to)
                    if predicted_salary:
                        all_salaries.append(predicted_salary)
    vacancies_processed = len(all_salaries)
    average_salary = int(sum(all_salaries)/vacancies_processed)
    vacancy_params = {
        'language': language,
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancy_params

def process_vacancy_sj(language, sj_token, town):
    all_salaries = []
    vacancies_found = 0
    total_salary = 0
    vacancies_processed = 0
    average_salary = 0
    headers = {
        'X-Api-App-Id': sj_token,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    page = 1
    while True:
        params = {
            'page': page,
            'town': town,
            'keyword': f'Программист {language}'
        }
        url = 'https://api.superjob.ru/2.0/vacancies/'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_page = response.json()
        vacancies_found = vacancies_page['total']
        for vacancy in vacancies_page['objects']:
            currency = vacancy['currency']
            salary_from = vacancy['payment_from']
            salary_to = vacancy['payment_to']
            predicted_salary = predict_rub_salary(currency, salary_to, salary_from)
            if predicted_salary:
                all_salaries.append(predicted_salary)
        page = page + 1
        if not vacancies_page['more']:
            break
    vacancies_processed = len(all_salaries)
    if vacancies_processed :
        average_salary = int(sum(all_salaries) / vacancies_processed)
    vacancy_params = {
        'language': language,
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancy_params


def predict_rub_salary(currency, salary_to, salary_from ):
    if not (currency == 'rub' or currency == 'RUR'):
        return None
    if salary_to and salary_from:
        return (salary_to + salary_from)/2
    elif salary_from:
        return salary_from*1.2
    elif salary_to:
        return salary_to*0.8


def make_table(languages_information, title):
    table_payload = [['Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата']]
    for language_information in languages_information:
        table_row = [
            language_information['language'],
            language_information['vacancies_found'],
            language_information['vacancies_processed'],
            language_information['average_salary']
        ]
        table_payload.append(table_row)
    table = AsciiTable(table_payload, title)
    return table


if __name__ == '__main__':
    load_dotenv()
    town = os.getenv('TOWN')
    area = os.getenv('AREA')
    period = os.getenv('PERIOD')
    sj_token = os.getenv('SJ_TOKEN')
    languages = [
        'Python',
        'Java',
        'Javascript',
        'C++',
        'C#',
        'PHP',
        'Ruby',
        'C',
        'Go'
    ]
    sj_salaries = []
    hh_salaries = []



    for language in languages:
        try:
            hh_salaries.append(process_vacancy_hh(language, period, area))
            sj_salaries.append(process_vacancy_sj(language, sj_token, town))
        except requests.exceptions.HTTPError as error:
            logging.warning(f'произошла ошибка при получении данных с HeadHunter или SuperJob {error}')
    sj_table = make_table(sj_salaries, 'SuperJob Moscow')
    hh_table = make_table(hh_salaries, 'HeadHunter Moscow')
    print(sj_table.table)
    print(hh_table.table)