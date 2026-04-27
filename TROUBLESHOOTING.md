# 🔧 Решение проблем (Troubleshooting)

## ❌ Частые ошибки и решения

### Ошибка 1: `ValueError: Ошибка! BOT_TOKEN не найден`

**Симптомы:**
```
ValueError: Ошибка! BOT_TOKEN не найден.
Создайте файл .env и добавьте: BOT_TOKEN=ваш_токен_от_botfather
```

**Причины:**
- Файл `.env` не создан
- В `.env` нет переменной `BOT_TOKEN`
- `.env` находится не в правильной папке

**Решение:**
1. Убедитесь, что вы в папке проекта `demobotaitu`
2. Создайте файл `.env`:
   ```bash
   copy .env.example .env  # Windows
   cp .env.example .env    # Linux/Mac
   ```
3. Откройте `.env` и замените `YOUR_BOT_TOKEN_HERE` на ваш реальный токен:
   ```
   BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYZ
   ```
4. Перезапустите бота: `python main.py`

---

### Ошибка 2: `ModuleNotFoundError: No module named 'aiogram'`

**Симптомы:**
```
ModuleNotFoundError: No module named 'aiogram'
```

**Причина:** Зависимости не установлены

**Решение:**
```bash
# Установите все зависимости
pip install -r requirements.txt

# Или, если это не помогло, установите явно:
pip install aiogram==3.3.0
pip install aiosqlite==0.19.0
pip install icalevents==0.1.30
pip install httpx==0.25.0
pip install apscheduler==3.10.4
pip install python-dotenv==1.0.0
```

Если используете виртуальное окружение:
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Затем установите зависимости
pip install -r requirements.txt
```

---

### Ошибка 3: `ConnectionError` или сообщение не отправляется

**Симптомы:**
```
httpx.ConnectError: Unable to connect to Canvas
ssl.SSLError: Cannot connect to Canvas LMS
```

**Причины:**
1. Нет интернета
2. Canvas сервер недоступен
3. URL на календарь неправильный

**Решение:**
1. **Проверьте интернет:**
   ```bash
   ping google.com
   ```

2. **Проверьте правильность URL:**
   - Команда: `/set_link https://canvas.instructure.com/feeds/calendars/xxxxxxxx.ics`
   - URL должен содержать `.ics`
   - URL должен быть с `https://` или `http://`

3. **Проверьте, что календарь доступен:**
   - В Canvas перейдите в Календарь
   - Найдите параметры доступа (должно быть "Public" или "Accessible")
   - Если приватный → сделайте публичным

4. **Используйте /check для диагностики:**
   ```
   /check
   ```
   Если видите список дедлайнов → URL работает!

---

### Ошибка 4: Команда `/set_link` возвращает ошибку валидации

**Симптомы:**
```
❌ Ошибка валидации ссылки.
Ссылка должна:
• Начинаться с http:// или https://
• Содержать расширение .ics
```

**Проверьте:**
```bash
# Правильно:
/set_link https://canvas.instructure.com/feeds/calendars/abc123def456.ics

# Неправильно:
/set_link canvas.instructure.com/feeds/calendars/abc123.ics  # Нет https://
/set_link https://canvas.instructure.com/calendar/abc123      # Нет .ics
```

---

### Ошибка 5: Бот не отвечает на команды

**Проверьте по порядку:**

1. **Токен правильный?**
   ```
   /me в BotFather
   ```
   Должны увидеть информацию о вашем боте.

2. **Бот работает?**
   Посмотрите на экран консоли:
   ```
   ✅ Бот @YourBotName подключен и готов к работе!
   👂 Слушаю сообщения...
   ```

3. **Интернет соединение?**
   ```bash
   ping t.me
   ```

4. **Посмотрите логи:**
   ```bash
   tail -f bot.log  # Linux/Mac
   type bot.log     # Windows (или откройте файл в редакторе)
   ```

---

### Ошибка 6: Уведомления о дедлайнах не приходят

**Проверьте:**

1. **Ссылка сохранена?**
   ```
   /status
   ```
   Должна показать "✅ Статус: Активен"

2. **В календаре есть дедлайны?**
   ```
   /check
   ```
   Должна показать список дедлайнов

3. **Правильный диапазон времени?**
   - Бот отправляет сообщение только один раз
   - За 71-72 часа до дедлайна (примерно за 3 дня)
   - Если до дедлайна осталось больше 3 дней → будет ждать
   - Если прошло 3 дня → уведомление уже отправлено (один раз!)

4. **Календарь обновился?**
   - Обновите кэш: `Ctrl + R` в Canvas
   - Попросите бота заново проверить: подождите до следующего часа

5. **Посмотрите логи:**
   ```bash
   tail -f bot.log | grep "НАПОМИНАНИЕ"
   ```

---

### Ошибка 7: `sqlite3.OperationalError: database is locked`

**Симптомы:**
```
sqlite3.OperationalError: database is locked
```

**Причина:** Несколько экземпляров бота пишут в БД одновременно

**Решение:**
1. **Остановите все запущенные экземпляры:**
   ```bash
   # Найдите процесс
   ps aux | grep main.py  # Linux/Mac
   tasklist | findstr python  # Windows
   
   # Остановите (Ctrl + C в консоли)
   ```

2. **Запустите один экземпляр:**
   ```bash
   python main.py
   ```

3. **Если проблема повторяется:**
   - Удалите `bot_database.db`
   - Перезапустите бота (БД пересоздастся)

---

### Ошибка 8: `TypeError: object datetime.date can't be used in 'await' expression`

**Причина:** Проблема в парсинге iCal

**Решение:**
- Обновите `icalevents`:
  ```bash
  pip install --upgrade icalevents
  ```

---

## 📊 Диагностика

### Проверить все ли компоненты работают:

```bash
# 1. Проверить Python версию
python --version  # Должно быть 3.10+

# 2. Проверить установленные пакеты
pip list | grep -E "aiogram|aiosqlite|icalevents|httpx|apscheduler|python-dotenv"

# 3. Проверить конфигурацию
# Откройте .env - должен содержать BOT_TOKEN

# 4. Запустить бота с подробным логированием
# Откройте config.py и измените:
# LOG_LEVEL = "DEBUG"  # Было INFO
python main.py

# 5. Посмотреть логи
tail -100 bot.log  # Linux/Mac - последние 100 строк
```

### Тестовый сценарий:

```
1. /start                                          ✅ Получить приветствие
2. /set_link https://your-canvas-ical-feed.ics   ✅ Ссылка сохранена
3. /status                                         ✅ Показать статус
4. /check                                          ✅ Показать дедлайны
5. /help                                           ✅ Показать справку
```

Если все команды работают → бот готов!

---

## 🆘 Крайние случаи

### Проблема: Бот "зависает" или не отвечает

**Диагностика:**
1. Посмотрите логи `bot.log`
2. Если видите бесконечные ошибки → найдите дедлайн
3. Проверьте /check - может быть срок очень большого файла

**Решение:**
- Удалите проблемный календарь: `/set_link` с новой ссылкой
- Перезапустите бота

### Проблема: Бот отправил одно и то же сообщение дважды

**Причина:** Возможно есть два процесса бота

**Решение:**
```bash
# Найдите процессы
ps aux | grep main.py  # Linux
tasklist | findstr python  # Windows

# Остановите все
# Перезапустите один
python main.py
```

### Проблема: ОЗУ растет

**Причина:** Утечка памяти (редко) или очень большой календарь

**Решение:**
1. Перезапустите бота время от времени (1-2 раза в неделю)
2. Если проблема в календаре → очистите его от старых событий

---

## 📞 Где искать помощь

1. **Логи бота** → `/bot.log`
2. **Документация** → `README.md`, `ARCHITECTURE.md`
3. **Быстрый старт** → `INSTALL.md`
4. **Справка в боте** → `/help`

---

**Успехов!** 🚀
