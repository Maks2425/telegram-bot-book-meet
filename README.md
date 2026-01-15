# Telegram Bot - Book Meet

Мінімальний каркас Telegram-бота на Python з використанням віртуального середовища.

## Встановлення та налаштування

### 1. Створення віртуального середовища

```powershell
python -m venv venv
```

### 2. Активація віртуального середовища

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
venv\Scripts\activate.bat
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Встановлення залежностей

Після активації venv:
```powershell
pip install -r requirements.txt
```

Або безпосередньо через Python з venv:
```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

### 4. Налаштування токена

1. Скопіюйте файл `.env.example` в `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```

2. Відкрийте файл `.env` і замініть `your_bot_token_here` на ваш реальний токен від [@BotFather](https://t.me/BotFather):
   ```env
   BOT_TOKEN=ваш_токен_бота_тут
   ```

3. (Опціонально) Додайте свій Telegram ID для отримання сповіщень про нові бронювання:
   ```env
   OWNER_TELEGRAM_ID=123456789
   ```
   
   **Як знайти свій Telegram ID:**
   - Напишіть боту [@userinfobot](https://t.me/userinfobot) в Telegram
   - Він надішле вам ваш ID
   - Скопіюйте число та додайте в `.env` файл

## Запуск бота

### Варіант 1: З активацією venv

1. Активуйте віртуальне середовище:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

2. Запустіть бота:
   ```powershell
   python main.py
   ```

### Варіант 2: Безпосередньо через Python з venv

```powershell
.\venv\Scripts\python.exe main.py
```

## Деактивація віртуального середовища

Коли закінчите роботу:
```powershell
deactivate
```

## Структура проекту

```
telegram-bot-book-meet/
├── .env                 # Файл з токеном (не комітиться в git)
├── .env.example         # Приклад конфігурації
├── .gitignore          # Ігнорування файлів для git
├── config.py           # Модуль конфігурації
├── main.py             # Головний файл бота
├── requirements.txt    # Залежності проекту
└── venv/               # Віртуальне середовище (не комітиться в git)
```

## Команди бота

- `/start` - Привітання та підтвердження роботи бота

## Безпека

⚠️ **Важливо:** 
- Ніколи не комітьте файл `.env` в git
- Файл `.env` вже додано в `.gitignore`
- Не діліться своїм токеном з іншими

## Вимоги

- Python 3.8+
- pip

## Розробка

Проект використовує:
- `python-telegram-bot==20.7` - бібліотека для роботи з Telegram Bot API
- `python-dotenv==1.0.0` - завантаження змінних оточення з `.env` файлу

