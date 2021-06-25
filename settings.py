"""
Укажите какие вакансии нужно парсить.
IS_REMOTE_JOB - удаленные
IS_FULLTIME_JOB - офис

Если указаны только удаленные вакансии, парсер все равно перепроверяет вакансии, в которых удаленка не указана.
Если в тексте такой вакансии упоминается удаленка, в телеграм придет уведомление.

Некоторые работодатели допускают возможность удаленной работы, но не ставят в настройках вакансии галочку напротив
этого пункта. Из-за этого стандартный поиск по удаленке их не находит.
"""
IS_REMOTE_JOB = True
IS_FULLTIME_JOB = False

TELEGRAM_API_KEY = '1723692698:AAHSErrcQLPCWnxKDFE292Rtcpzi_2Rkb_8'
TELEGRAM_CHAT_ID = 1391057391

"""
Укажите слова, которых не должно быть в заголовке вакансии. Например, python используется в множестве профессий, так что
бэкендеру есть смысл добавить в список стоп-слов qa, devops, java.
Пример: 

IGNORED_WORDS_IN_TITLE = {'qa', 'devops', 'java'}

ВАЖНО! Используйте буквы только в нижнем регистре (lowercase).
"""
IGNORED_WORDS_IN_TITLE = {'fullstack', 'full-stack', 'full', 'recruiter',
                          'java', 'unity', 'курс', 'онлайнкурс', 'курса', 'онлайнкурса', 'support', 'ruby', 'аналитик',
                          'qa', 'devops', 'affilate', 'преподаватель', 'smm', 'с', 'c', 'go', 'golang',
                          'analyst', 'менеджер', 'frontend', 'front-end', 'marketing', 'data'}

"""
Укажите вакансии для парсинга. Вы можете разделить вакансии по разным спискам. Например, вы согласны работать удаленно
по вакансии middle QA, но по вакансиям python junior и fullstack junior рассматриваете только офис. В таком случае
укажите такие данные:

REMOTE_JOBS = ('middle QA')
FULLTIME_JOBS = ('python junior', 'fullstack junior')
"""
REMOTE_JOBS = ('Junior python', 'python', 'django', 'junior django')
FULLTIME_JOBS = ()

"""
Для парсинга hh.ru необходимо использовать собственные cookies и user-agent
Вы можете получить их после первого посещения сайта. Просто скопируйте соответствующие headers. 

Не рекомендуется использовать COOKIES авторизованного пользователя. Теоретически, это может привести к 
блокировке аккаунта.
"""
COOKIES = '__ddg1=g7JnzpX4bxR1KwrHzUEs; _xsrf=437c9bcaf21187307f17fbbc766d1895; ' \
          'hhtoken=JJAu88WjJ55IXPVC!qaPkf82v3r5; hhuid=7g4vwhDksLJfVmDTCcAy8g--; region_clarified=NOT_SET; ' \
          '_xsrf=437c9bcaf21187307f17fbbc766d1895; display=desktop; hhrole=anonymous; regions=56 '
USER_AGENT = 'PostmanRuntime/7.28.0'
