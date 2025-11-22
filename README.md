# Real Estate Parser

Python-скрипт для парсинга данных о недвижимости с различных сайтов. Получает GET/POST запросы с JSON, содержащим список сайтов и CSS-селекторы, парсит данные и возвращает результаты в формате JSON.

Использует **Playwright** для работы с JavaScript-сайтами и динамическим контентом.

## Возможности

- Парсинг данных о недвижимости с нескольких сайтов одновременно
- Гибкая настройка через CSS-селекторы
- REST API на FastAPI
- Поддержка GET и POST запросов
- Автоматическая нормализация URL
- Обработка ошибок и валидация данных
- Извлечение фото из различных атрибутов (src, data-src, data-lazy-src, background-image)
- **Работа с JavaScript-сайтами** через Playwright
- **Headless режим** для деплоя на хостинг без GUI

## Установка

1. Клонируйте репозиторий или скачайте файлы проекта

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. **Установите браузеры для Playwright** (обязательно):
```bash
playwright install chromium
```

Или установите все браузеры:
```bash
playwright install
```

Для деплоя на Linux-хостинг используйте:
```bash
playwright install-deps chromium
playwright install chromium
```

## Использование

### Вариант 1: Веб-сервер (рекомендуется)

Запустите API сервер:
```bash
python api_server.py
```

Или используя uvicorn напрямую:
```bash
uvicorn api_server:app --host 0.0.0.0 --port 5000
```

Сервер будет доступен по адресу `http://localhost:5000`

#### Документация API

После запуска сервера автоматическая документация доступна по адресам:
- Swagger UI: `http://localhost:5000/docs`
- ReDoc: `http://localhost:5000/redoc`

#### Примеры запросов

**POST запрос (один объект):**
```bash
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d '{"site_url":"https://realt.by/sale/flats/","selectors":{"object_url":"a[aria-label*=\"Ссылка на объект\"]@href","title":"img[title]@title","description":".md:block.text-basic.text-subhead.hidden span.line-clamp-2","address":"p.text-basic.w-full.text-subhead.md:text-body","price":".text-title.font-semibold.text-basic-900","rooms":"p.flex.flex-wrap.text-headline span:nth-child(1)","floor":"p.flex.flex-wrap.text-headline span:nth-child(3)","area":"p.flex.flex-wrap.text-headline span:nth-child(2)","photos":".swiper-slide img@src"}}'
```

**POST запрос (массив объектов):**
```bash
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

Или используя Python:
```python
import requests
import json

data = {
    "site_url": "https://realt.by/sale/flats/",
    "selectors": {
        "object_url": "a[aria-label*='Ссылка на объект']@href",
        "title": "img[title]@title",
        "description": ".md:block.text-basic.text-subhead.hidden span.line-clamp-2",
        "address": "p.text-basic.w-full.text-subhead.md:text-body",
        "price": ".text-title.font-semibold.text-basic-900",
        "rooms": "p.flex.flex-wrap.text-headline span:nth-child(1)",
        "floor": "p.flex.flex-wrap.text-headline span:nth-child(3)",
        "area": "p.flex.flex-wrap.text-headline span:nth-child(2)",
        "photos": ".swiper-slide img@src"
    }
}

response = requests.post('http://localhost:5000/parse', json=data)
results = response.json()
print(json.dumps(results, ensure_ascii=False, indent=2))
```

### Вариант 2: Командная строка

```bash
# Из файла
python parser.py example_input.json

# Из stdin
cat example_input.json | python parser.py
```

## Формат входных данных

JSON может быть одним объектом или массивом объектов:

**Один объект:**
```json
{
  "site_url": "https://example-real-estate.com",
  "selectors": {
    "object_url": "a.listing-link@href",
    "title": ".listing-title",
    "description": ".listing-description",
    "address": ".listing-address",
    "price": ".listing-price",
    "rooms": ".listing-rooms",
    "floor": ".listing-floor",
    "area": ".listing-area",
    "photos": ".listing-photo img@src"
  }
}
```

**Массив объектов:**
```json
[
  {
    "site_url": "https://example-real-estate.com",
    "selectors": {...}
  },
  {
    "site_url": "https://another-site.com",
    "selectors": {...}
  }
]
```

### Поля селекторов

- `object_url` (обязательно) - CSS-селектор для ссылки на объект недвижимости
- `title` - селектор для названия объекта
- `description` - селектор для описания
- `address` - селектор для адреса
- `price` - селектор для цены
- `rooms` - селектор для количества комнат
- `floor` - селектор для этажа
- `area` - селектор для площади
- `photos` - селектор для фотографий (извлекаются URL из атрибутов src, data-src, data-lazy-src или background-image)

### Синтаксис селекторов с атрибутами

Поддерживаются два формата:
- `selector@attr` (например: `a@href`, `img@src`)
- `selector::attr(attr)` (например: `a::attr(href)`, `img::attr(src)`)

## Формат выходных данных

Результат возвращается в виде массива JSON объектов:

```json
[
  {
    "site_url": "https://realt.by/sale/flats/",
    "object_url": "https://realt.by/sale/flats/12345",
    "title": "Квартира 2 комнаты",
    "description": "Уютная квартира в центре города",
    "address": "ул. Примерная, д. 1",
    "price": "5 000 000 руб.",
    "rooms": "2",
    "floor": "5",
    "area": "45 м²",
    "photos": [
      "https://realt.by/photos/1.jpg",
      "https://realt.by/photos/2.jpg"
    ]
  }
]
```

## Структура проекта

```
RealEstateParser/
├── parser.py           # Основной класс парсера (Playwright)
├── api_server.py       # FastAPI веб-сервер
├── requirements.txt    # Зависимости проекта
├── example_input.json  # Пример входных данных
├── .gitignore         # Git ignore файл
└── README.md          # Документация
```

## Особенности

- **Playwright**: Работает с JavaScript-сайтами и динамическим контентом
- **Headless режим**: По умолчанию запускается без GUI (подходит для серверов)
- **Относительные URL**: Автоматически преобразуются в абсолютные относительно базового URL сайта
- **Множественные источники фото**: Поддержка различных атрибутов для lazy-loading изображений
- **Обработка ошибок**: Продолжает работу даже при ошибках на отдельных сайтах
- **Задержки между запросами**: Настраиваемая задержка для избежания блокировок
- **User-Agent**: Используется реалистичный User-Agent для запросов

## Настройка парсера

В классе `RealEstateParser` можно настроить:

```python
parser = RealEstateParser(
    timeout=30000,    # Таймаут для загрузки страниц (в миллисекундах)
    delay=1.0,        # Задержка между запросами (в секундах)
    headless=True     # Запуск браузера в headless режиме (без GUI)
)
```

## Деплой на хостинг

### Требования для Linux-хостинга:

1. Установите системные зависимости:
```bash
playwright install-deps chromium
```

2. Установите браузер Chromium:
```bash
playwright install chromium
```

3. Убедитесь, что используется headless режим (по умолчанию `headless=True`)

4. Для некоторых хостингов может потребоваться установка дополнительных библиотек:
```bash
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

## Health Check

Проверить статус сервера:
```bash
curl http://localhost:5000/health
```

Ответ:
```json
{"status": "ok"}
```

## Требования

- Python 3.7+
- playwright
- fastapi
- uvicorn
- pydantic

## Лицензия

Этот проект предоставляется "как есть" для использования.

## Поддержка

При возникновении проблем проверьте:
1. Правильность CSS-селекторов
2. Доступность сайтов для парсинга
3. Формат входного JSON
4. Логи сервера (выводятся в stderr)
5. Установлены ли браузеры Playwright: `playwright install chromium`
