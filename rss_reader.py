#!/usr/bin/env python3
import json
import os
import sys
import time
import hashlib
import re
from datetime import datetime, timedelta
import feedparser
from email.utils import parsedate_tz, mktime_tz
from typing import List, Dict, Any

import openai

class LLMInterface:
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    def generate_response(self, prompt, system_message):
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content

class Translator:
    def __init__(self):
        self.translation_cache = {}
        self.cache_file = "translation_cache.json"
        self.llm = LLMInterface()
        self.load_translation_cache()
    
    def load_translation_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                self.translation_cache = json.load(f)
    
    def save_translation_cache(self):
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.translation_cache, f, indent=2, ensure_ascii=False)
    
    def translate_text(self, text: str) -> str:
        if not text.strip():
            return text
        
        clean_text = re.sub(r'<[^>]+>', '', text).strip()
        if not clean_text:
            return text
        
        if clean_text in self.translation_cache:
            return self.translation_cache[clean_text]
        
        try:
            if not os.environ.get('OPENAI_API_KEY'):
                return f"[翻訳エラー: API_KEY未設定] {clean_text}"
            
            system_message = "あなたは日本語翻訳の専門家です。英語のテキストを自然な日本語に翻訳してください。翻訳結果のみを出力してください。"
            translated = self.llm.generate_response(clean_text, system_message)
            
            self.translation_cache[clean_text] = translated
            self.save_translation_cache()
            return translated
            
        except Exception as e:
            return f"[翻訳エラー] {clean_text}"

class RSSManager:
    def __init__(self, feeds_file: str = "rss_feeds.json"):
        self.feeds_file = feeds_file
        self.feeds = self.load_feeds()
        self.settings_file = "settings.json"
        self.settings = self.load_settings()
        self.translator = Translator()
    
    def load_feeds(self) -> List[Dict[str, str]]:
        if os.path.exists(self.feeds_file):
            with open(self.feeds_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_feeds(self):
        with open(self.feeds_file, 'w', encoding='utf-8') as f:
            json.dump(self.feeds, f, indent=2, ensure_ascii=False)
    
    def add_feed(self, url: str, name: str = None):
        if name is None:
            feed = feedparser.parse(url)
            name = feed.feed.get('title', url)
        
        self.feeds.append({"url": url, "name": name})
        self.save_feeds()
        print(f"フィード '{name}' を追加しました")
    
    def remove_feed(self, index: int):
        if 0 <= index < len(self.feeds):
            removed = self.feeds.pop(index)
            self.save_feeds()
            print(f"フィード '{removed['name']}' を削除しました")
        else:
            print("無効なインデックスです")
    
    def edit_feed(self, index: int, url: str = None, name: str = None):
        if 0 <= index < len(self.feeds):
            if url:
                self.feeds[index]["url"] = url
            if name:
                self.feeds[index]["name"] = name
            self.save_feeds()
            print(f"フィード '{self.feeds[index]['name']}' を更新しました")
        else:
            print("無効なインデックスです")
    
    def load_settings(self) -> Dict[str, Any]:
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"translation_enabled": False}
    
    def save_settings(self):
        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(self.settings, f, indent=2, ensure_ascii=False)
    
    def toggle_translation(self):
        self.settings["translation_enabled"] = not self.settings.get("translation_enabled", False)
        self.save_settings()
        status = "有効" if self.settings["translation_enabled"] else "無効"
        print(f"翻訳機能を{status}にしました")
    
    def list_feeds(self):
        if not self.feeds:
            print("フィードが登録されていません")
            return
        
        print("登録済みフィード:")
        for i, feed in enumerate(self.feeds):
            print(f"{i}: {feed['name']} ({feed['url']})")

class RSSReader:
    def __init__(self, rss_manager: RSSManager):
        self.rss_manager = rss_manager
        self.current_page = 0
        self.items_per_page = 20
        self.all_items = []
        self.cache_dir = "rss_cache"
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
    def get_cache_filename(self, url: str) -> str:
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"{url_hash}.json")
    
    def has_cache(self, cache_file: str) -> bool:
        return os.path.exists(cache_file)
    
    def parse_date(self, date_str: str) -> float:
        if not date_str:
            return 0
        try:
            parsed = parsedate_tz(date_str)
            if parsed:
                return mktime_tz(parsed)
        except:
            pass
        return 0
    
    def fetch_all_items(self):
        self.all_items = []
        print("記事を取得中...")
        
        for feed in self.rss_manager.feeds:
            try:
                cache_file = self.get_cache_filename(feed['url'])
                
                if self.has_cache(cache_file):
                    with open(cache_file, 'r', encoding='utf-8') as f:
                        cached_data = json.load(f)
                        for item in cached_data:
                            item['feed_name'] = feed['name']
                            self.all_items.append(item)
                    print(f"キャッシュから読み込み: {feed['name']}")
                else:
                    print(f"取得中: {feed['name']}")
                    parsed_feed = feedparser.parse(feed['url'])
                    feed_items = []
                    
                    for entry in parsed_feed.entries:
                        item = {
                            'title': entry.get('title', '無題'),
                            'link': entry.get('link', ''),
                            'description': entry.get('description', ''),
                            'published': entry.get('published', ''),
                            'published_timestamp': self.parse_date(entry.get('published', '')),
                            'feed_name': feed['name']
                        }
                        feed_items.append(item)
                        self.all_items.append(item)
                    
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(feed_items, f, indent=2, ensure_ascii=False)
                        
            except Exception as e:
                print(f"フィード '{feed['name']}' の取得でエラー: {e}")
        
        self.all_items.sort(key=lambda x: x.get('published_timestamp', 0), reverse=True)
    
    def show_list(self):
        if not self.all_items:
            self.fetch_all_items()
        
        if not self.all_items:
            print("記事がありません")
            return
        
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.all_items[start:end]
        
        translation_status = "翻訳ON" if self.rss_manager.settings.get("translation_enabled", False) else "翻訳OFF"
        print(f"\n=== RSS記事一覧 (ページ {self.current_page + 1}) - {translation_status} ===")
        
        for i, item in enumerate(page_items, start):
            title = item['title']
            description = item.get('description', '')
            
            if self.rss_manager.settings.get("translation_enabled", False):
                title = self.rss_manager.translator.translate_text(title)
                if description:
                    description = self.rss_manager.translator.translate_text(description)
            
            if description:
                clean_desc = re.sub(r'<[^>]+>', '', description)[:50]
                print(f"{i}: [{item['feed_name']}] {title}")
                print(f"     {clean_desc}...")
            else:
                print(f"{i}: [{item['feed_name']}] {title}")
        
        total_pages = (len(self.all_items) - 1) // self.items_per_page + 1
        print(f"\nページ {self.current_page + 1} / {total_pages}")
        print("コマンド: n(次), p(前), q(戻る), 数字(詳細表示)")
    
    def show_detail(self, index: int):
        if 0 <= index < len(self.all_items):
            item = self.all_items[index]
            print(f"\n=== 記事詳細 ===")
            
            if self.rss_manager.settings.get("translation_enabled", False):
                print(f"タイトル（原文）: {item['title']}")
                print(f"タイトル（翻訳）: {self.rss_manager.translator.translate_text(item['title'])}")
                print(f"フィード: {item['feed_name']}")
                print(f"公開日: {item['published']}")
                print(f"URL: {item['link']}")
                print(f"\n内容（原文）: {item['description'][:500]}...")
                print(f"\n内容（翻訳）: {self.rss_manager.translator.translate_text(item['description'][:500])}...")
            else:
                print(f"タイトル: {item['title']}")
                print(f"フィード: {item['feed_name']}")
                print(f"公開日: {item['published']}")
                print(f"URL: {item['link']}")
                print(f"内容: {item['description'][:500]}...")
            
            print("\nコマンド: b(戻る)")
        else:
            print("無効な記事番号です")
    
    def next_page(self):
        max_page = (len(self.all_items) - 1) // self.items_per_page
        if self.current_page < max_page:
            self.current_page += 1
            self.show_list()
        else:
            print("最後のページです")
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_list()
        else:
            print("最初のページです")

def main_menu(rss_manager: RSSManager):
    translation_status = "ON" if rss_manager.settings.get("translation_enabled", False) else "OFF"
    print("\n=== RSS リーダー ===")
    print("1. フィード一覧")
    print("2. 記事を読む")
    print("3. フィード追加")
    print("4. フィード削除")
    print("5. フィード編集")
    print(f"6. 翻訳切り替え (現在: {translation_status})")
    print("7. 終了")

def main():
    rss_manager = RSSManager()
    rss_reader = RSSReader(rss_manager)
    
    while True:
        try:
            main_menu(rss_manager)
            choice = input("\n選択してください (1-7): ").strip()
            
            if choice == "1":
                rss_manager.list_feeds()
            
            elif choice == "2":
                if not rss_manager.feeds:
                    print("フィードが登録されていません")
                    continue
                
                rss_reader.show_list()
                
                while True:
                    user_input = input("\nコマンドを入力: ").strip().lower()
                    
                    if user_input == 'q':
                        break
                    elif user_input == 'n':
                        rss_reader.next_page()
                    elif user_input == 'p':
                        rss_reader.prev_page()
                    elif user_input.isdigit():
                        article_index = int(user_input)
                        rss_reader.show_detail(article_index)
                        
                        while True:
                            detail_input = input("\nコマンドを入力: ").strip().lower()
                            if detail_input == 'b':
                                rss_reader.show_list()
                                break
                    else:
                        print("無効なコマンドです")
            
            elif choice == "3":
                url = input("RSS URL を入力: ").strip()
                name = input("フィード名を入力 (空白でURLから自動取得): ").strip()
                rss_manager.add_feed(url, name if name else None)
            
            elif choice == "4":
                rss_manager.list_feeds()
                if rss_manager.feeds:
                    try:
                        index = int(input("削除するフィードのインデックス: "))
                        rss_manager.remove_feed(index)
                    except ValueError:
                        print("無効な数字です")
            
            elif choice == "5":
                rss_manager.list_feeds()
                if rss_manager.feeds:
                    try:
                        index = int(input("編集するフィードのインデックス: "))
                        url = input("新しいURL (空白で変更なし): ").strip()
                        name = input("新しい名前 (空白で変更なし): ").strip()
                        rss_manager.edit_feed(index, url if url else None, name if name else None)
                    except ValueError:
                        print("無効な数字です")
            
            elif choice == "6":
                rss_manager.toggle_translation()
            
            elif choice == "7":
                print("終了します")
                break
            
            else:
                print("無効な選択です")
        
        except KeyboardInterrupt:
            print("\n終了します")
            break

if __name__ == "__main__":
    main()