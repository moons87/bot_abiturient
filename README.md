# Telegram-бот для абитуриентов колледжа

Telegram-бот для консультации абитуриентов: отвечает на вопросы на основе данных сайта и документов колледжа, проводит профориентационный тест и принимает записи на мероприятия.

## Возможности

- **Консультации** — специальности, гранты, общежитие через кнопочное меню и свободный текст
- **ИИ-ответы** — Claude Haiku анализирует вопрос и отвечает на основе данных колледжа
- **База знаний** — данные с сайта колледжа + PDF/Word/Excel документы
- **FAQ** — часто задаваемые вопросы, управляемые администратором
- **Профориентационный тест** — 15 вопросов, развёрнутый AI-отчёт с рекомендацией специальностей
- **Запись на мероприятия** — экскурсии и дни открытых дверей с уведомлением администратора
- **Автопарсинг** — сайт обновляется в базе знаний каждый понедельник в 03:00

## Стек

- Python 3.11+, aiogram 3.x, aiosqlite
- Anthropic Claude Haiku API
- BeautifulSoup4, PyMuPDF, python-docx, openpyxl
- APScheduler

## Быстрый старт

```bash
git clone https://github.com/moons87/bot_abiturient.git
cd bot_abiturient

python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt

cp .env.example .env
# Откройте .env и заполните значения

python bot/main.py
```

## Переменные окружения (.env)

| Переменная | Описание |
|-----------|---------|
| `BOT_TOKEN` | Токен бота от [@BotFather](https://t.me/BotFather) |
| `CLAUDE_API_KEY` | API ключ с [console.anthropic.com](https://console.anthropic.com) |
| `ADMIN_TELEGRAM_ID` | Ваш Telegram user ID (узнать через [@userinfobot](https://t.me/userinfobot)) |
| `COLLEGE_SITE_URL` | URL сайта колледжа для парсинга |
| `DB_PATH` | Путь к базе данных (по умолчанию `database.db`) |

## Первоначальная настройка

После запуска бота напишите ему как администратор:

```
/update        — загрузить данные с сайта колледжа
/reload_docs   — загрузить документы из папки docs/
/addfaq        — добавить вопрос в FAQ
/adddate       — добавить дату мероприятия
```

Для загрузки документов положите PDF, Word (.docx) или Excel (.xlsx) файлы в папку `docs/` и выполните `/reload_docs`.

## Команды администратора

| Команда | Описание |
|---------|---------|
| `/update` | Перепарсить сайт колледжа |
| `/reload_docs` | Загрузить документы из папки `docs/` |
| `/addfaq` | Добавить вопрос в FAQ |
| `/delfaq` | Удалить вопрос из FAQ |
| `/adddate` | Добавить дату мероприятия |
| `/deldate` | Удалить дату мероприятия |
| `/dates` | Список мероприятий с записавшимися |
| `/stats` | Статистика базы знаний и заявок |

## Структура проекта

```
├── bot/
│   ├── handlers/
│   │   ├── menu.py        # Главное меню, разделы
│   │   ├── faq.py         # FAQ
│   │   ├── profitest.py   # Профориентационный тест
│   │   ├── excursions.py  # Запись на мероприятия
│   │   ├── admin.py       # Команды администратора
│   │   └── free_text.py   # Свободный текст → Claude
│   ├── keyboards.py
│   ├── scheduler.py
│   └── main.py
├── knowledge/
│   ├── db.py              # SQLite CRUD
│   └── search.py          # Поиск по базе знаний
├── scraper/
│   ├── site_parser.py     # Парсинг сайта
│   └── doc_loader.py      # Загрузка документов
├── ai/
│   └── claude_client.py   # Claude API
├── tests/                 # 37 тестов
├── docs/                  # Сюда кладите PDF/Word/Excel
├── .env.example
└── requirements.txt
```

## Тесты

```bash
pytest tests/ -q
# 37 passed
```
