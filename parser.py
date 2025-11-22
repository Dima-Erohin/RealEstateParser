#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Estate Parser Script
Получает JSON с сайтами и селекторами, парсит данные и возвращает результаты
Использует Playwright Async API для работы с JavaScript-сайтами
"""

import json
import sys
import re
import asyncio
from playwright.async_api import async_playwright, Page, ElementHandle, Browser, BrowserContext
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


class RealEstateParser:
    """Класс для парсинга недвижимости с различных сайтов"""
    
    def __init__(self, timeout: int = 60000, delay: float = 1.0, headless: bool = True):
        """
        Инициализация парсера
        
        Args:
            timeout: Таймаут для загрузки страниц (в миллисекундах)
            delay: Задержка между запросами (в секундах)
            headless: Запуск браузера в headless режиме (без GUI)
        """
        self.timeout = timeout
        self.delay = delay
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """Асинхронный контекстный менеджер для автоматического закрытия браузера"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-setuid-sandbox']  # Для деплоя на хостинг
        )
        self.context = await self.browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрытие браузера при выходе из контекста"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def _ensure_browser(self):
        """Обеспечивает инициализацию браузера"""
        if not self.context:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            if not self.browser:
                self.browser = await self.playwright.chromium.launch(
                    headless=self.headless,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
            if not self.context:
                self.context = await self.browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
    
    async def fetch_page(self, url: str) -> Optional[Page]:
        """
        Загружает страницу и возвращает Page объект
        
        Args:
            url: URL страницы для загрузки
            
        Returns:
            Page объект или None при ошибке
        """
        await self._ensure_browser()
        
        try:
            page = await self.context.new_page()
            await page.goto(url, wait_until='networkidle', timeout=self.timeout)
            # Небольшая задержка для загрузки динамического контента
            await page.wait_for_timeout(1000)
            return page
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}", file=sys.stderr)
            return None
    
    async def extract_text(self, element: Any, selector: str, page: Optional[Page] = None) -> str:
        """
        Извлекает текст или атрибут по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если указан атрибут, извлекается значение атрибута, иначе текст
        
        Args:
            element: ElementHandle или Page для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            page: Page объект (если element - это Page)
            
        Returns:
            Извлеченный текст/атрибут или пустая строка
        """
        if not selector:
            return ""
        
        try:
            clean_selector, attr = self.parse_selector_with_attr(selector)
            
            # Определяем, где искать
            search_element = page if page else element
            
            if not search_element:
                return ""
            
            if clean_selector:
                found = await search_element.query_selector(clean_selector)
            else:
                found = element if isinstance(element, ElementHandle) else None
            
            if found:
                if attr:
                    # Извлекаем атрибут
                    result = await found.get_attribute(attr) or ""
                    return result.strip()
                else:
                    # Извлекаем текст
                    result = await found.text_content() or ""
                    return result.strip()
        except Exception as e:
            print(f"Ошибка при извлечении по селектору '{selector}': {e}", file=sys.stderr)
        
        return ""
    
    async def extract_attr(self, element: Any, selector: str, attr: str = 'href', page: Optional[Page] = None) -> str:
        """
        Извлекает атрибут по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если атрибут указан в селекторе, используется он, иначе используется параметр attr
        
        Args:
            element: ElementHandle или Page для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            attr: Название атрибута по умолчанию (если не указан в селекторе)
            page: Page объект (если element - это Page)
            
        Returns:
            Значение атрибута или пустая строка
        """
        if not selector:
            return ""
        
        try:
            clean_selector, selector_attr = self.parse_selector_with_attr(selector)
            # Используем атрибут из селектора, если указан, иначе используем параметр
            target_attr = selector_attr if selector_attr else attr
            
            # Определяем, где искать
            search_element = page if page else element
            
            if not search_element:
                return ""
            
            if clean_selector:
                found = await search_element.query_selector(clean_selector)
            else:
                found = element if isinstance(element, ElementHandle) else None
            
            if found:
                result = await found.get_attribute(target_attr) or ""
                return result.strip()
        except Exception as e:
            print(f"Ошибка при извлечении атрибута по селектору '{selector}': {e}", file=sys.stderr)
        
        return ""
    
    async def extract_list(self, element: Any, selector: str, attr: Optional[str] = None, page: Optional[Page] = None) -> List[str]:
        """
        Извлекает список значений по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если атрибут указан в селекторе, используется он, иначе используется параметр attr
        
        Args:
            element: ElementHandle или Page для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            attr: Атрибут для извлечения (если None и не указан в селекторе, извлекается текст)
            page: Page объект (если element - это Page)
            
        Returns:
            Список значений
        """
        if not selector:
            return []
        
        try:
            clean_selector, selector_attr = self.parse_selector_with_attr(selector)
            # Используем атрибут из селектора, если указан, иначе используем параметр
            target_attr = selector_attr if selector_attr else attr
            
            # Определяем, где искать
            search_element = page if page else element
            
            if not search_element:
                return []
            
            if clean_selector:
                found_elements = await search_element.query_selector_all(clean_selector)
            else:
                found_elements = [element] if isinstance(element, ElementHandle) else []
            
            results = []
            for elem in found_elements:
                try:
                    if target_attr:
                        value = await elem.get_attribute(target_attr)
                        if value:
                            results.append(value.strip())
                    else:
                        value = await elem.text_content()
                        if value:
                            results.append(value.strip())
                except Exception:
                    continue
            
            return results
        except Exception as e:
            print(f"Ошибка при извлечении списка по селектору '{selector}': {e}", file=sys.stderr)
        
        return []
    
    def parse_selector_with_attr(self, selector: str) -> tuple[str, Optional[str]]:
        """
        Парсит селектор с указанием атрибута
        
        Поддерживает форматы:
        - selector@attr (например: "a@href", "img@src")
        - selector::attr(attr) (например: "a::attr(href)", "img::attr(src)")
        
        Args:
            selector: Селектор с возможным указанием атрибута
            
        Returns:
            Кортеж (чистый_селектор, атрибут или None)
        """
        if not selector:
            return selector, None
        
        # Формат: selector::attr(attr)
        match = re.search(r'::attr\(([^)]+)\)$', selector)
        if match:
            attr = match.group(1)
            clean_selector = selector[:match.start()].rstrip()
            return clean_selector, attr
        
        # Формат: selector@attr
        if '@' in selector:
            parts = selector.rsplit('@', 1)
            if len(parts) == 2:
                clean_selector = parts[0].rstrip()
                attr = parts[1].strip()
                return clean_selector, attr
        
        return selector, None
    
    def normalize_url(self, url: str, base_url: str) -> str:
        """
        Нормализует URL (делает абсолютным относительно base_url)
        
        Args:
            url: Относительный или абсолютный URL
            base_url: Базовый URL
            
        Returns:
            Абсолютный URL
        """
        if not url:
            return ""
        
        if url.startswith('http://') or url.startswith('https://'):
            return url
        
        return urljoin(base_url, url)
    
    async def parse_object(self, object_element: ElementHandle, selectors: Dict[str, str], base_url: str, page: Page) -> Dict[str, Any]:
        """
        Парсит один объект недвижимости
        
        Args:
            object_element: ElementHandle объект недвижимости
            selectors: Словарь с CSS-селекторами
            base_url: Базовый URL сайта
            page: Page объект для поиска внутри элемента
            
        Returns:
            Словарь с данными объекта
        """
        result = {
            "site_url": base_url,
            "object_url": "",
            "title": "",
            "description": "",
            "address": "",
            "price": "",
            "rooms": "",
            "floor": "",
            "area": "",
            "photos": []
        }
        
        # Извлекаем URL объекта
        if "object_url" in selectors:
            object_url_selector = selectors["object_url"]
            clean_selector, selector_attr = self.parse_selector_with_attr(object_url_selector)
            
            # Определяем атрибут для извлечения
            target_attr = selector_attr if selector_attr else "href"
            
            # Пробуем извлечь атрибут из самого элемента
            object_url = await object_element.get_attribute(target_attr) or ""
            
            # Если не найден в самом элементе и есть clean_selector, ищем внутри
            if not object_url and clean_selector:
                found = await object_element.query_selector(clean_selector)
                if found:
                    object_url = await found.get_attribute(target_attr) or ""
            
            result["object_url"] = self.normalize_url(object_url, base_url)
            
            # Если URL объекта - это сам элемент (ссылка), используем его href
            if not result["object_url"]:
                tag_name = await object_element.evaluate("el => el.tagName.toLowerCase()")
                if tag_name == 'a':
                    object_url = await object_element.get_attribute("href") or ""
                    result["object_url"] = self.normalize_url(object_url, base_url)
        
        # Извлекаем остальные поля
        # Селекторы могут быть относительными (относительно object_element) или абсолютными
        # Поддерживается синтаксис @attr и ::attr(attr)
        for field in ["title", "description", "address", "price", "rooms", "floor", "area"]:
            if field in selectors:
                result[field] = await self.extract_text(object_element, selectors[field], page)
        
        # Извлекаем фото
        if "photos" in selectors:
            # extract_list теперь поддерживает @attr и ::attr(attr) синтаксис
            # Если атрибут указан в селекторе, он будет использован
            clean_photo_selector, photo_attr = self.parse_selector_with_attr(selectors["photos"])
            
            if photo_attr:
                # Атрибут указан в селекторе, используем его
                photo_urls = await self.extract_list(object_element, selectors["photos"], page=page)
            else:
                # Пробуем разные атрибуты по порядку
                photo_urls = await self.extract_list(object_element, clean_photo_selector, "src", page)
                if not photo_urls:
                    photo_urls = await self.extract_list(object_element, clean_photo_selector, "data-src", page)
                if not photo_urls:
                    photo_urls = await self.extract_list(object_element, clean_photo_selector, "data-lazy-src", page)
                if not photo_urls:
                    # Пробуем background-image в style
                    img_elements = await object_element.query_selector_all(clean_photo_selector) if clean_photo_selector else []
                    for img in img_elements:
                        try:
                            style = await img.get_attribute("style") or ""
                            if "url(" in style:
                                match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                                if match:
                                    photo_urls.append(match.group(1))
                        except Exception:
                            continue
            
            # Нормализуем URL фото
            result["photos"] = [self.normalize_url(url, base_url) for url in photo_urls if url]
        
        return result
    
    async def parse_site(self, site_url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Парсит все объекты на сайте
        
        Args:
            site_url: URL сайта
            selectors: Словарь с CSS-селекторами
            
        Returns:
            Список объектов недвижимости
        """
        results = []
        page = None
        
        try:
            # Загружаем главную страницу
            page = await self.fetch_page(site_url)
            if not page:
                return results
            
            # Проверяем наличие селектора для объектов
            if "object_url" not in selectors:
                print(f"Предупреждение: для сайта {site_url} не указан селектор 'object_url'", file=sys.stderr)
                return results
            
            # Находим все объекты на странице
            # Извлекаем чистый селектор (без @attr или ::attr(attr)) для поиска элементов
            object_selector_full = selectors["object_url"]
            object_selector, _ = self.parse_selector_with_attr(object_selector_full)
            
            if not object_selector:
                print(f"Не удалось извлечь селектор из '{object_selector_full}'", file=sys.stderr)
                return results
            
            object_elements = await page.query_selector_all(object_selector)
            
            if not object_elements:
                print(f"Не найдено объектов на странице {site_url} по селектору '{object_selector}'", file=sys.stderr)
                return results
            
            print(f"Найдено {len(object_elements)} объектов на {site_url}", file=sys.stderr)
            
            # Парсим каждый объект
            for obj_elem in object_elements:
                try:
                    obj_data = await self.parse_object(obj_elem, selectors, site_url, page)
                    # Добавляем только если есть хотя бы URL объекта
                    if obj_data["object_url"]:
                        results.append(obj_data)
                except Exception as e:
                    print(f"Ошибка при парсинге объекта на {site_url}: {e}", file=sys.stderr)
                    continue
        
        finally:
            # Закрываем страницу
            if page:
                try:
                    await page.close()
                except Exception:
                    pass
        
        # Задержка между запросами
        if self.delay > 0:
            await asyncio.sleep(self.delay)
        
        return results
    
    async def parse_all_sites(self, sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Парсит все сайты из списка
        
        Args:
            sites: Список сайтов с URL и селекторами
            
        Returns:
            Список всех объектов недвижимости
        """
        all_results = []
        
        # Инициализируем браузер, если еще не инициализирован
        await self._ensure_browser()
        
        for site in sites:
            site_url = site.get("site_url", "")
            selectors = site.get("selectors", {})
            
            if not site_url:
                print("Пропущен сайт без URL", file=sys.stderr)
                continue
            
            if not selectors:
                print(f"Пропущен сайт {site_url} без селекторов", file=sys.stderr)
                continue
            
            print(f"Парсинг сайта: {site_url}", file=sys.stderr)
            site_results = await self.parse_site(site_url, selectors)
            all_results.extend(site_results)
        
        return all_results
    
    async def cleanup(self):
        """Явное закрытие браузера (если не используется контекстный менеджер)"""
        if self.context:
            try:
                await self.context.close()
            except Exception:
                pass
            self.context = None
        if self.browser:
            try:
                await self.browser.close()
            except Exception:
                pass
            self.browser = None
        if self.playwright:
            try:
                await self.playwright.stop()
            except Exception:
                pass
            self.playwright = None


async def main_async():
    """Асинхронная главная функция для работы из командной строки"""
    # Читаем JSON из stdin или из аргументов командной строки
    if len(sys.argv) > 1:
        # Читаем из файла
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        # Читаем из stdin
        input_text = sys.stdin.read()
        if not input_text.strip():
            print("Ошибка: не предоставлены данные для парсинга", file=sys.stderr)
            sys.exit(1)
        data = json.loads(input_text)
    
    # Проверяем формат данных
    if not isinstance(data, list):
        print("Ошибка: ожидается список сайтов", file=sys.stderr)
        sys.exit(1)
    
    # Создаем парсер и парсим
    parser = RealEstateParser(headless=True)
    try:
        results = await parser.parse_all_sites(data)
        # Выводим результат в формате JSON
        print(json.dumps(results, ensure_ascii=False, indent=2))
    finally:
        # Очищаем ресурсы
        await parser.cleanup()


def main():
    """Главная функция для работы из командной строки"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
