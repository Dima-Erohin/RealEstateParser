# Real Estate Parser

Python-скрипт для парсинга данных о недвижимости с различных сайтов. Получает GET/POST запросы с JSON, содержащим список сайтов и CSS-селекторы, парсит данные и возвращает результаты в формате JSON.

## Возможности

- Парсинг данных о недвижимости с нескольких сайтов одновременно
- Гибкая настройка через CSS-селекторы
- REST API на FastAPI
- Поддержка GET и POST запросов
- Автоматическая нормализация URL
- Обработка ошибок и валидация данных
- Извлечение фото из различных атрибутов (src, data-src, data-lazy-src, background-image)

## Установка

1. Клонируйте репозиторий или скачайте файлы проекта

2. Установите зависимости:
```bash
pip install -r requirements.txt
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

**POST запрос:**
```bash
curl -X POST http://localhost:5000/parse \
  -H "Content-Type: application/json" \
  -d @example_input.json
```

**GET запрос:**
```bash
curl "http://localhost:5000/parse?data=%5B%7B%22site_url%22%3A%22https%3A%2F%2Fexample.com%22%2C%22selectors%22%3A%7B%22object_url%22%3A%22a.listing%22%7D%7D%5D"
```

Или используя Python:
```python
import requests
import json

with open('example_input.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

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

JSON должен содержать массив объектов, каждый из которых описывает сайт для парсинга:

```json
[
  {
    "site_url": "https://example-real-estate.com",
    "selectors": {
      "object_url": "a.listing-link",
      "title": ".listing-title",
      "description": ".listing-description",
      "address": ".listing-address",
      "price": ".listing-price",
      "rooms": ".listing-rooms",
      "floor": ".listing-floor",
      "area": ".listing-area",
      "photos": ".listing-photo img"
    }
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

## Формат выходных данных

Результат возвращается в виде массива JSON объектов:

```json
[
  {
    "site_url": "https://example-real-estate.com",
    "object_url": "https://example-real-estate.com/listing/123",
    "title": "Квартира 2 комнаты",
    "description": "Уютная квартира в центре города",
    "address": "ул. Примерная, д. 1",
    "price": "5 000 000 руб.",
    "rooms": "2",
    "floor": "5",
    "area": "45 м²",
    "photos": [
      "https://example-real-estate.com/photos/1.jpg",
      "https://example-real-estate.com/photos/2.jpg"
    ]
  }
]
```

## Структура проекта

```
RealEstateParser/
├── parser.py           # Основной класс парсера
├── api_server.py       # FastAPI веб-сервер
├── requirements.txt    # Зависимости проекта
├── example_input.json  # Пример входных данных
├── .gitignore         # Git ignore файл
└── README.md          # Документация
```

## Особенности

- **Относительные URL**: Автоматически преобразуются в абсолютные относительно базового URL сайта
- **Множественные источники фото**: Поддержка различных атрибутов для lazy-loading изображений
- **Обработка ошибок**: Продолжает работу даже при ошибках на отдельных сайтах
- **Задержки между запросами**: Настраиваемая задержка для избежания блокировок
- **User-Agent**: Используется реалистичный User-Agent для запросов

## Настройка парсера

В классе `RealEstateParser` можно настроить:

```python
parser = RealEstateParser(
    timeout=30,    # Таймаут для HTTP запросов (секунды)
    delay=1.0      # Задержка между запросами (секунды)
)
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
- requests
- beautifulsoup4
- lxml
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

