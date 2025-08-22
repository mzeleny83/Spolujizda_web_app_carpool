#!/usr/bin/env python3
import sqlite3
import os

DATABASE = 'spolujizda.db'

def delete_all_users():
    """Vymaže všechny uživatele a jejich data z databáze"""
    try:
        conn = sqlite3.connect(DATABASE)
        c = conn.cursor()
        
        # Vymaž data v pořadí kvůli foreign key constraints
        tables_to_clear = [
            'blocked_users',
            'ratings', 
            'messages',
            'reservations',
            'recurring_rides',
            'user_stats',
            'sms_codes',
            'rides',
            'users'
        ]
        
        for table in tables_to_clear:
            c.execute(f'DELETE FROM {table}')
            print(f"✅ Vymazána tabulka: {table}")
        
        conn.commit()
        conn.close()
        print("✅ Všechna uživatelská data vymazána")
        
    except Exception as e:
        print(f"❌ Chyba: {e}")

if __name__ == '__main__':
    if os.path.exists(DATABASE):
        delete_all_users()
    else:
        print(f"❌ Databáze {DATABASE} neexistuje")