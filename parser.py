#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Real Estate Parser Script
Получает JSON с сайтами и селекторами, парсит данные и возвращает результаты
"""

import json
import sys
import re
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
import time


class RealEstateParser:
    """Класс для парсинга недвижимости с различных сайтов"""
    
    def __init__(self, timeout: int = 30, delay: float = 1.0):
        """
        Инициализация парсера
        
        Args:
            timeout: Таймаут для HTTP запросов
            delay: Задержка между запросами (в секундах)
        """
        self.timeout = timeout
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Загружает страницу и возвращает BeautifulSoup объект
        
        Args:
            url: URL страницы для загрузки
            
        Returns:
            BeautifulSoup объект или None при ошибке
        """
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Ошибка при загрузке {url}: {e}", file=sys.stderr)
            return None
    
    def extract_text(self, element: Any, selector: str) -> str:
        """
        Извлекает текст или атрибут по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если указан атрибут, извлекается значение атрибута, иначе текст
        
        Args:
            element: BeautifulSoup элемент для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            
        Returns:
            Извлеченный текст/атрибут или пустая строка
        """
        if not selector or not element:
            return ""
        
        try:
            clean_selector, attr = self.parse_selector_with_attr(selector)
            
            found = element.select_one(clean_selector) if clean_selector else element
            
            if found:
                if attr:
                    # Извлекаем атрибут
                    return found.get(attr, "")
                else:
                    # Извлекаем текст
                    return found.get_text(strip=True)
        except Exception as e:
            print(f"Ошибка при извлечении по селектору '{selector}': {e}", file=sys.stderr)
        
        return ""
    
    def extract_attr(self, element: Any, selector: str, attr: str = 'href') -> str:
        """
        Извлекает атрибут по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если атрибут указан в селекторе, используется он, иначе используется параметр attr
        
        Args:
            element: BeautifulSoup элемент для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            attr: Название атрибута по умолчанию (если не указан в селекторе)
            
        Returns:
            Значение атрибута или пустая строка
        """
        if not selector or not element:
            return ""
        
        try:
            clean_selector, selector_attr = self.parse_selector_with_attr(selector)
            # Используем атрибут из селектора, если указан, иначе используем параметр
            target_attr = selector_attr if selector_attr else attr
            
            found = element.select_one(clean_selector) if clean_selector else element
            if found:
                return found.get(target_attr, "")
        except Exception as e:
            print(f"Ошибка при извлечении атрибута по селектору '{selector}': {e}", file=sys.stderr)
        
        return ""
    
    def extract_list(self, element: Any, selector: str, attr: Optional[str] = None) -> List[str]:
        """
        Извлекает список значений по CSS-селектору
        
        Поддерживает селекторы с атрибутами: selector@attr или selector::attr(attr)
        Если атрибут указан в селекторе, используется он, иначе используется параметр attr
        
        Args:
            element: BeautifulSoup элемент для поиска
            selector: CSS-селектор (может содержать @attr или ::attr(attr))
            attr: Атрибут для извлечения (если None и не указан в селекторе, извлекается текст)
            
        Returns:
            Список значений
        """
        if not selector or not element:
            return []
        
        try:
            clean_selector, selector_attr = self.parse_selector_with_attr(selector)
            # Используем атрибут из селектора, если указан, иначе используем параметр
            target_attr = selector_attr if selector_attr else attr
            
            found_elements = element.select(clean_selector) if clean_selector else [element]
            
            if target_attr:
                return [elem.get(target_attr, "") for elem in found_elements if elem.get(target_attr)]
            else:
                return [elem.get_text(strip=True) for elem in found_elements if elem.get_text(strip=True)]
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
    
    def parse_object(self, object_element: Any, selectors: Dict[str, str], base_url: str) -> Dict[str, Any]:
        """
        Парсит один объект недвижимости
        
        Args:
            object_element: BeautifulSoup элемент объекта
            selectors: Словарь с CSS-селекторами
            base_url: Базовый URL сайта
            
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
            
            # object_element уже найден по clean_selector (или его части)
            # Пробуем извлечь атрибут из самого элемента
            object_url = object_element.get(target_attr, "")
            
            # Если не найден в самом элементе и есть clean_selector, ищем внутри
            if not object_url and clean_selector:
                found = object_element.select_one(clean_selector)
                if found:
                    object_url = found.get(target_attr, "")
            
            result["object_url"] = self.normalize_url(object_url, base_url)
            
            # Если URL объекта - это сам элемент, используем его href
            if not result["object_url"] and object_element.name == 'a':
                result["object_url"] = self.normalize_url(object_element.get("href", ""), base_url)
        
        # Извлекаем остальные поля
        # Селекторы могут быть относительными (относительно object_element) или абсолютными
        # Поддерживается синтаксис @attr и ::attr(attr)
        for field in ["title", "description", "address", "price", "rooms", "floor", "area"]:
            if field in selectors:
                result[field] = self.extract_text(object_element, selectors[field])
        
        # Извлекаем фото
        if "photos" in selectors:
            # extract_list теперь поддерживает @attr и ::attr(attr) синтаксис
            # Если атрибут указан в селекторе, он будет использован
            clean_photo_selector, photo_attr = self.parse_selector_with_attr(selectors["photos"])
            
            if photo_attr:
                # Атрибут указан в селекторе, используем его
                photo_urls = self.extract_list(object_element, selectors["photos"])
            else:
                # Пробуем разные атрибуты по порядку
                photo_urls = self.extract_list(object_element, clean_photo_selector, "src")
                if not photo_urls:
                    photo_urls = self.extract_list(object_element, clean_photo_selector, "data-src")
                if not photo_urls:
                    photo_urls = self.extract_list(object_element, clean_photo_selector, "data-lazy-src")
                if not photo_urls:
                    # Пробуем background-image в style
                    img_elements = object_element.select(clean_photo_selector) if clean_photo_selector else []
                    for img in img_elements:
                        style = img.get("style", "")
                        if "url(" in style:
                            match = re.search(r'url\(["\']?([^"\']+)["\']?\)', style)
                            if match:
                                photo_urls.append(match.group(1))
            
            # Нормализуем URL фото
            result["photos"] = [self.normalize_url(url, base_url) for url in photo_urls if url]
        
        return result
    
    def parse_site(self, site_url: str, selectors: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Парсит все объекты на сайте
        
        Args:
            site_url: URL сайта
            selectors: Словарь с CSS-селекторами
            
        Returns:
            Список объектов недвижимости
        """
        results = []
        
        # Загружаем главную страницу
        soup = self.fetch_page(site_url)
        if not soup:
            return results
        
        # Проверяем наличие селектора для объектов
        if "object_url" not in selectors:
            print(f"Предупреждение: для сайта {site_url} не указан селектор 'object_url'", file=sys.stderr)
            return results
        
        # Находим все объекты на странице
        # Извлекаем чистый селектор (без @attr или ::attr(attr)) для поиска элементов
        object_selector_full = selectors["object_url"]
        object_selector, _ = self.parse_selector_with_attr(object_selector_full)
        object_elements = soup.select(object_selector) if object_selector else []
        
        if not object_elements:
            print(f"Не найдено объектов на странице {site_url} по селектору '{object_selector}'", file=sys.stderr)
            return results
        
        print(f"Найдено {len(object_elements)} объектов на {site_url}", file=sys.stderr)
        
        # Парсим каждый объект
        for obj_elem in object_elements:
            try:
                obj_data = self.parse_object(obj_elem, selectors, site_url)
                # Добавляем только если есть хотя бы URL объекта
                if obj_data["object_url"]:
                    results.append(obj_data)
            except Exception as e:
                print(f"Ошибка при парсинге объекта на {site_url}: {e}", file=sys.stderr)
                continue
        
        # Задержка между запросами
        if self.delay > 0:
            time.sleep(self.delay)
        
        return results
    
    def parse_all_sites(self, sites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Парсит все сайты из списка
        
        Args:
            sites: Список сайтов с URL и селекторами
            
        Returns:
            Список всех объектов недвижимости
        """
        all_results = []
        
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
            site_results = self.parse_site(site_url, selectors)
            all_results.extend(site_results)
        
        return all_results


def main():
    """Главная функция для работы из командной строки"""
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
    parser = RealEstateParser()
    results = parser.parse_all_sites(data)
    
    # Выводим результат в формате JSON
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

