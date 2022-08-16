import logging
import os

import requests
from dotenv import load_dotenv
from terminaltables import AsciiTable


def process_vacancy_hh(language):
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
            'area': '1',
            'text': f'Программист {language}',
            'period': '30'
        }
        page = page + 1
        url = 'https://api.hh.ru/vacancies'
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        vacancys = response.json()
        if vacancys.get('items'):
            vacancies_found = vacancys['found']
            pages = vacancys['pages']
            for vacancy in vacancys['items']:
                if vacancy['salary']:
                    predicted_salary = predict_rub_salary_for_hh(vacancy['salary'])
                    if predicted_salary:
                        total_salary += predicted_salary
                        vacancies_processed += 1
                        average_salary = int(total_salary/vacancies_processed)
        else:
            break
    vacancy_params = {
        'language': language,
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancy_params


def predict_rub_salary_for_hh(salary):
    if salary['currency'] == 'RUR':
        if salary['from'] and salary['to']:
            return (salary['from'] + salary['to'])/2
        elif salary['from']:
            return salary['from']*1.2
        elif salary['to']:
            return salary['to']*0.8


def process_vacancy_sj(language, sj_token):
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
            'town': 4,
            'keyword': f'Программист {language}'
        }
        url = "https://api.superjob.ru/2.0/vacancies/"
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        if response.json()['objects']:
            vacancies_found = response.json()['total']
            for vacancy in response.json()['objects']:
                if vacancy:
                    predicted_salary = predict_rub_salary_for_superJob(vacancy)
                    if predicted_salary:
                        total_salary += predicted_salary
                        vacancies_processed += 1
                        average_salary = int(total_salary / vacancies_processed)
            page = page + 1
            if not response.json()['more']:
                break
        else:
            break
    vacancy_params = {
        'language': language,
        'vacancies_found': vacancies_found,
        'vacancies_processed': vacancies_processed,
        'average_salary': average_salary
    }
    return vacancy_params


def predict_rub_salary_for_superJob(vacancy):
    if vacancy['currency'] == 'rub':
        if vacancy['payment_from'] and vacancy['payment_to']:
            return vacancy['payment_from'] + vacancy['payment_to']/2
        elif vacancy['payment_from']:
            return vacancy['payment_from']*1.2
        elif vacancy['payment_from']:
            return vacancy['payment_from']*0.8


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
    sj_salarys = []
    hh_salarys = []

    for language in languages:
        try:
            hh_salarys.append(process_vacancy_hh(language))
            sj_salarys.append(process_vacancy_sj(language, sj_token))
        except requests.exceptions.HTTPError as error:
            logging.warning('код сломался, иди чини')
    sj_table = make_table(sj_salarys, 'SuperJob Moscow')
    hh_table = make_table(hh_salarys, 'HeadHunter Moscow')
    print(sj_table.table)
    print(hh_table.table)