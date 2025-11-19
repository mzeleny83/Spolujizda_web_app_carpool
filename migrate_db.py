
import os
import sys
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
import datetime

# --- Konfigurace ---
# Databáze, ze které se budou data kopírovat (webová aplikace)
SOURCE_DB = 'sqlite:///simple_app.db'
# Databáze, do které se budou data vkládat (mobilní aplikace)
DEST_DB = 'sqlite:///sql_app.db'

# --- Definice modelů pro ZDROJOVOU databázi (app.py) ---
BaseSource = declarative_base()

class UserSource(BaseSource):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    rating = Column(Float, default=5.0)

class RideSource(BaseSource):
    __tablename__ = 'rides'
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, nullable=False)
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    departure_time = Column(String, nullable=False)
    available_seats = Column(Integer, nullable=False)
    price = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)

# --- Definice modelů pro CÍLOVOU databázi (enhanced_app.py / mobile) ---
BaseDest = declarative_base()

class UserDest(BaseDest):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True)
    phone = Column(String(20), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    phone_verified = Column(Boolean, default=False)
    profile_photo = Column(String(255))
    id_verified = Column(Boolean, default=False)
    license_verified = Column(Boolean, default=False)
    rating = Column(Float, default=5.0)
    total_rides = Column(Integer, default=0)
    home_city = Column(String(100))
    bio = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.now)

class RideDest(BaseDest):
    __tablename__ = 'rides'
    id = Column(Integer, primary_key=True)
    driver_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    from_lat = Column(Float)
    from_lng = Column(Float)
    to_lat = Column(Float)
    to_lng = Column(Float)
    departure_time = Column(DateTime, nullable=False)
    available_seats = Column(Integer, nullable=False)
    price = Column(Float)
    description = Column(Text)
    car_model = Column(String(100))
    car_color = Column(String(50))
    smoking_allowed = Column(Boolean, default=False)
    pets_allowed = Column(Boolean, default=False)
    recurring = Column(Boolean, default=False)
    recurring_days = Column(String(20))
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.datetime.now)

# --- Logika migrace ---
def migrate_data():
    # Připojení k databázím
    source_engine = create_engine(SOURCE_DB)
    dest_engine = create_engine(DEST_DB)
    SourceSession = sessionmaker(bind=source_engine)
    DestSession = sessionmaker(bind=dest_engine)
    source_session = SourceSession()
    dest_session = DestSession()

    # Vytvoření tabulek v cílové DB, pokud neexistují
    BaseDest.metadata.create_all(dest_engine)

    # --- Migrace Uživatelů (Users) ---
    print("Migruji uživatele...")
    users_source = source_session.query(UserSource).all()
    for user_s in users_source:
        # Zkontrolujeme, zda uživatel s daným telefonem již v cílové DB neexistuje
        exists = dest_session.query(UserDest).filter(UserDest.phone == user_s.phone).first()
        if not exists:
            user_d = UserDest(
                # id=user_s.id, # Necháme auto-increment v cílové DB
                name=user_s.name,
                phone=user_s.phone,
                password_hash=user_s.password_hash,
                rating=user_s.rating,
                # Nová pole v cílové DB budou mít výchozí hodnoty
                phone_verified=False,
                id_verified=False,
                license_verified=False,
                total_rides=0,
                email=f"user_{user_s.phone}@example.com" # Doplňujeme fiktivní email
            )
            dest_session.add(user_d)
    dest_session.commit()
    print(f"Migrace uživatelů dokončena. Zpracováno {len(users_source)} záznamů.")

    # --- Migrace Jízd (Rides) ---
    print("\nMigruji jízdy...")
    rides_source = source_session.query(RideSource).all()
    for ride_s in rides_source:
        # Zjistíme nové ID řidiče v cílové databázi
        driver_source = source_session.query(UserSource).filter(UserSource.id == ride_s.driver_id).first()
        if not driver_source:
            continue # Přeskočíme jízdy, kde nenajdeme řidiče

        driver_dest = dest_session.query(UserDest).filter(UserDest.phone == driver_source.phone).first()
        if not driver_dest:
            continue # Přeskočíme jízdy, kde řidič nebyl migrován

        # Zkontrolujeme, zda podobná jízda již neexistuje
        exists = dest_session.query(RideDest).filter(
            RideDest.driver_id == driver_dest.id,
            RideDest.from_location == ride_s.from_location,
            RideDest.to_location == ride_s.to_location,
            # Porovnání času může být složité, pokud formáty nejsou stejné
            # Pro jednoduchost předpokládáme, že pokud ostatní sedí, je to tatáž jízda
        ).first()

        if not exists:
            try:
                # Převedeme string na datetime, pokud je to potřeba
                if isinstance(ride_s.departure_time, str):
                    departure_dt = datetime.datetime.fromisoformat(ride_s.departure_time)
                else:
                    departure_dt = ride_s.departure_time
            except ValueError:
                print(f"Varování: Nelze převést 'departure_time' '{ride_s.departure_time}' pro jízdu ID {ride_s.id}. Přeskakuji.")
                continue

            ride_d = RideDest(
                driver_id=driver_dest.id,
                from_location=ride_s.from_location,
                to_location=ride_s.to_location,
                departure_time=departure_dt,
                available_seats=ride_s.available_seats,
                price=ride_s.price,
                description=ride_s.description,
                status='active'
            )
            dest_session.add(ride_d)
    dest_session.commit()
    print(f"Migrace jízd dokončena. Zpracováno {len(rides_source)} záznamů.")

    # Zavření session
    source_session.close()
    dest_session.close()
    print("\n\nMigrace dat dokončena!")

if __name__ == '__main__':
    # Záloha cílové databáze pro jistotu
    if os.path.exists('sql_app.db'):
        backup_name = f"sql_app.db.bak_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Vytvářím zálohu cílové databáze jako '{backup_name}'...")
        os.rename('sql_app.db', backup_name)

    migrate_data()
