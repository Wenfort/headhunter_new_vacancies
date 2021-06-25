"""
Пожалуйста, запустите этот скрипт при первом использовании парсера. Он создаст БД, в которой будут храниться вакансии.

Если вам по какой-то причине нужно обнулить БД, просто запустите этот скрипт.
"""
import sqlite3
con = sqlite3.connect('vacancy.db')
cur = con.cursor()
cur.execute('DROP TABLE vacancies;')
cur.execute('CREATE TABLE vacancies(title text, url text, company_name text, '
            'company_city text, salary text, vacancy_text text);')
con.commit()
con.close()