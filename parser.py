import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import sqlite3
import telebot
import time
import re
from settings import *


@dataclass
class VacancyData:
    title: str
    url: str
    company_name: str
    company_city: str
    salary: str
    vacancy_text: str


class HTMLGrabber:

    def __init__(self):

        self.url = 'https://hh.ru/search/vacancy'

        self.headers = {
            'Cookie': COOKIES,
            'User-Agent': USER_AGENT,
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        }

        self.payload = {
            'clusters': 'true',
            'enable_snippets': 'true',
            'schedule': 'fullDay',
            'text': '',
            'order_by': 'publication_time'
        }

    def get_vacancies_page_html(self, text, is_remote_job):
        """
        Метод принимает название профессии, по которой нужно найти вакансию, а также
            логическое значение, указывающее на то, какие вакансии нужны пользователю, удаленные или офис.
        """
        self.payload['text'] = text

        if is_remote_job:
            self.payload['schedule'] = 'remote'

        return self.get_page_html(self.url, self.payload)

    def get_page_html(self, url, params=None):
        r = requests.get(url, headers=self.headers, params=params)
        content = r.content.decode('UTF-8')
        soup = BeautifulSoup(content, 'html.parser')
        return soup


class Parser:
    def __init__(self):
        pass

    @staticmethod
    def get_elements_from_bs4(html, tag, selector_type, selector_name, all_elements=False):
        if all_elements:
            return html.find_all(tag, {selector_type: selector_name})
        return html.find(tag, {selector_type: selector_name})

    def get_salary(self, html):
        """
        Данных о зарплате может не быть.
        """
        salary = self.get_elements_from_bs4(html, 'div', 'class', 'vacancy-serp-item__sidebar').text
        return salary if salary else 'Зарплата не указана'

    def get_vacancy_data(self, html):
        """
        Данные о вакансиях находятся в специальных датасетах. Этот метод парсит все необходимые данные.

        Если нужно спарсить еще какие-то данные, например, дату размещения объявления, используйте как шаблон
        метод get_salary, посколько в рекламных размещениях даты может не быть вообще.

        Не забудьте добавить новый аттрибут в датакласс и поле в БД
        """
        title = self.get_elements_from_bs4(html, 'span', 'class', 'resume-search-item__name').text
        url = self.get_elements_from_bs4(html, 'a', 'class', 'bloko-link').get('href')
        company_name = self.get_elements_from_bs4(html, 'div', 'class', 'vacancy-serp-item__meta-info-company').text
        company_city = self.get_elements_from_bs4(html, 'span', 'class', 'vacancy-serp-item__meta-info').text
        vacancy_text = self.get_elements_from_bs4(html, 'div', 'class', 'g-user-content').text
        salary = self.get_salary(html)

        return VacancyData(title=title, url=url, company_name=company_name,
                           company_city=company_city, salary=salary, vacancy_text=vacancy_text)

    def get_vacancies_list(self, html):
        return [self.get_vacancy_data(offer) for offer in html]

    def get_all_offers_html_block(self, html):
        return self.get_elements_from_bs4(html, 'div', 'class', 'vacancy-serp-item', all_elements=True)

    def get_vacancy_item_text(self, html):
        return self.get_elements_from_bs4(html, 'div', 'class', 'vacancy-description').text


class TelegramBot:

    def __init__(self):
        self.bot = telebot.TeleBot(TELEGRAM_API_KEY)

    def send_new_vacancies_to_telegram(self, new_vacancies, job_name):
        """
        Метод проверяет есть ли слова из заголовка в стоп-листе (стоп лист лежит в настройках). Если таких слов нет,
        подготавливает сообщение по шаблону и отправляет его.
        """
        for vacancy in new_vacancies:
            if not self.vacancy_title_in_stop_list(vacancy.title):
                message = self.make_vacancy_message(vacancy, job_name)
                self.send_to_chanel(message)

    def vacancy_title_in_stop_list(self, vacancy_title):
        """
        Заголовок вакансии разбивается на слова, из каждого слова удаляются знаки препинания, затем оно переводится
        в lowercase. Слова преобразуются в set и сравниваются с сетом стоп-слов из настроек. Если совпадения найдены,
        такая вакансия не нужна.
        """
        words_in_title = [self.delete_punctuation_from_title(word_in_title).lower() for word_in_title in
                          vacancy_title.split()]

        words_in_title = set(words_in_title)

        return bool(words_in_title & IGNORED_WORDS_IN_TITLE)

    @staticmethod
    def delete_punctuation_from_title(title):
        """
        Удаляет любые знаки пунктуации
        """
        title_without_puctuation = re.sub(r'[^\w\s]', '', title)
        return title_without_puctuation

    def make_vacancy_message(self, vacancy, additional_info=''):
        """
        В additional info попадает название профессии, по которой найдена вакансия. Поле можно использовать для
        передачи каких-то дополнительной информации без занесения в БД. Например, сообщать что вакансия удаленная,
        но работодатель не указал это при создании вакансии, а только в тексте.
        """
        telegram_message = f'*{vacancy.title}\n*' \
                           f'От {vacancy.company_name} из {vacancy.company_city} ({vacancy.salary})\n' \
                           f'{vacancy.url}\n' \
                           f'{additional_info}'

        return telegram_message

    def send_to_chanel(self, message):
        """
        parse_mode='Markdown' позволяет декорировать текст. Например, *текст* делает его болдом.
        """
        self.bot.send_message(TELEGRAM_CHAT_ID, message, parse_mode='Markdown')


class DatabaseInterface:
    connection = sqlite3.connect('vacancy.db')
    cursor = connection.cursor()

    def __init__(self):
        pass

    def add_to_database_nonexisting_vacancies(self, vacancy_datasets):
        """
        Метод проверяет есть ли

        Дополнительно, все датасеты новых вакансий добавляются в список, чтобы отправить его телеграм боту.

        Можно было сделать все проверки за один запрос, но поскольку парсер проводит большую часть времени в режиме сна
        (чтобы алгоритмы hh.ru не забанили за навязчивый парсинг), максимальная нагрузка на ДБ - 40 запросов в минуту,
        принял решение не усложнять SQL запрос.
        """
        new_vacancies = list()
        for vacancy in vacancy_datasets:
            if not self.check_is_vacancy_in_database(vacancy):
                new_vacancies.append(vacancy)
                self.add_new_vacancy_to_database(vacancy)

        self.connection.commit()
        self.new_vacancies = new_vacancies

    def add_new_vacancy_to_database(self, vacancy):
        vacancy.vacancy_text = vacancy.vacancy_text.replace("'", "''")
        sql = f"INSERT INTO vacancies VALUES ('{vacancy.title}', '{vacancy.url}', '{vacancy.company_name}', '{vacancy.company_city}', '{vacancy.salary}', '{vacancy.vacancy_text}')"
        self.cursor.execute(sql)

    def check_is_vacancy_in_database(self, vacancy):
        sql = f"SELECT * FROM vacancies WHERE title='{vacancy.title}' AND company_name='{vacancy.company_name}';"
        self.cursor.execute(sql)
        data = self.cursor.fetchall()
        return data

class Manager:
    def __init__(self):
        self.database_interface = DatabaseInterface()
        self.bot = TelegramBot()

    def start(self):
        """
        Сценарий работы сервиса. Проверяет какие типы вакансий нужно спарсить и получает данные.

        Часть блока после IS_REMOTE_JOB сначала собирает данные по вакансиям из списка REMOTE_JOBS, затем идет в список
        FULLTIME JOBS и ищет в вакансиях упоминания об удаленной работе.
        """
        if IS_FULLTIME_JOB:
            self.parse_jobs(FULLTIME_JOBS, is_remote_job=False, send_new_vacancies_to_telegram=True)

        if IS_REMOTE_JOB:
            self.parse_jobs(REMOTE_JOBS, is_remote_job=True, send_new_vacancies_to_telegram=True)
            self.parse_jobs(FULLTIME_JOBS, is_remote_job=False, send_new_vacancies_to_telegram=False)

    def parse_jobs(self, job_names, is_remote_job, send_new_vacancies_to_telegram):
        """
        Если в send_new_vacancies_to_telegram приходит значение True, то абсолютно все новые вакансии уходят в Telegram.
        Если приходит False, то подразумевается другая логика. В данный момент, в этом блоке выполняется перепроверка
        офисных вакансий на наличие в них слов, указаывающих на возможность удаленки. И только такие вакансии приходят
        в Telegram. В дальнейшем эту логику можно расширять, добавляя новые виды фильтрации вакансий для вывода.
        """
        for job_name in job_names:
            all_vacancy_datasets = self.get_all_vacancies_by_user_job_request(job_name, is_remote_job)
            self.database_interface.add_to_database_nonexisting_vacancies(all_vacancy_datasets)

            if send_new_vacancies_to_telegram:
                self.bot.send_new_vacancies_to_telegram(self.database_interface.new_vacancies, job_name)
            else:
                self.check_fulltime_vacancies_for_remote_availability_in_vacancy_text()
            time.sleep(10)

    def check_fulltime_vacancies_for_remote_availability_in_vacancy_text(self):
        """
        Метод парсит текст со страницы вакансии. И ищет в нем слово 'удал' или 'remote'. Если находит,
        подготавливает сообщение для бота и отправляет его.

        Иногда бывают ложные срабатывания, например, когда на странице есть фраза "удаление вирусов", но
        основная цель парсера - найти абсолютно все вакансии, ничего не упустив. Наличие минимального количества
        "лишних" - вполне допустимо.

        В тексте вакансий может быть "удалённая работа", "удаленная работа", "удалёнка" и т.д. 'удал' находит всё.
        """
        grabber = HTMLGrabber()
        parser = Parser()

        for new_vacancy in self.database_interface.new_vacancies:

            vacancy_html = grabber.get_page_html(new_vacancy.url)
            vacancy_text = parser.get_vacancy_item_text(vacancy_html)

            if 'удал' in vacancy_text or 'Удал' in vacancy_text or 'remote' in vacancy_text:
                if not self.bot.vacancy_title_in_stop_list(new_vacancy.title):
                    telegram_message = self.bot.make_vacancy_message(new_vacancy,
                                                                     'Получено через проверку вакансий без удаленки')
                    self.bot.send_to_chanel(telegram_message)

            time.sleep(10)

    def get_all_vacancies_by_user_job_request(self, job_name, is_remote_job):
        """
        Получает HTML код страницы с 20 свежими вакансиями, парсит его и создает датасеты с полценными данными.
        Поскольку дальше html код нигде не понадобится, возвращает только список готовых датасетов.
        """
        grabber = HTMLGrabber()
        vacancy_page_html = grabber.get_vacancies_page_html(job_name, is_remote_job)

        parser = Parser()
        all_vacancies_on_page_html = parser.get_all_offers_html_block(vacancy_page_html)
        all_vacancy_datasets = parser.get_vacancies_list(all_vacancies_on_page_html)

        return all_vacancy_datasets


while True:
    manager = Manager()
    manager.start()
    print('Круг завершен. Сплю 60 сек')
    time.sleep(60)
