from flask import Blueprint, request, jsonify
from spolujizda_core.database import db
from spolujizda_core.models import User, BlockedUser, UserStats
import hashlib

auth_bp = Blueprint('auth', __name__, url_prefix='/api/users')

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        phone = data.get('phone')
        password = data.get('password')
        
        email = data.get('email', '').strip()
        password_confirm = data.get('password_confirm')
        
        if not all([name, phone, password, password_confirm]):
            return jsonify({'error': 'Jméno, telefon, heslo a potvrzení hesla jsou povinné'}), 400
        
        if password != password_confirm:
            return jsonify({'error': 'Hesla se neshodují'}), 400
        
        # Normalizuje telefonní číslo - odebere všechny mezery a speciální znaky
        phone_clean = ''.join(filter(str.isdigit, phone))
        
        # Odstraní předvolbu
        if phone_clean.startswith('420'):
            phone_clean = phone_clean[3:]
        
        # Ověří formát (9 číslic)
        if len(phone_clean) != 9:
            return jsonify({'error': 'Neplatný formát telefonu (9 číslic)'}), 400
        
        # Vždy uloží ve formátu +420xxxxxxxxx
        phone_full = f'+420{phone_clean}'
        
        # Validace emailu pokud je zadán
        if email and '@' not in email:
            return jsonify({'error': 'Neplatný formát emailu'}), 400
        
        if User.query.filter_by(phone=phone_full).first():
            return jsonify({'error': 'Toto telefonní číslo je již registrováno'}), 409

        if email and User.query.filter_by(email=email).first():
            return jsonify({'error': 'Tento email je již registrován'}), 409
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        new_user = User(
            name=name,
            phone=phone_full,
            email=email if email else None,
            password_hash=password_hash,
            rating=5.0
        )
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'message': 'Uživatel úspěšně registrován'}), 201
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        login_field = data.get('phone')  # Může být telefon nebo email
        password = data.get('password')
        
        if not all([login_field, password]):
            return jsonify({'error': 'Telefon/email a heslo jsou povinné'}), 400
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        user = None
        if '@' in login_field:
            user = User.query.filter_by(email=login_field, password_hash=password_hash).first()
        else:
            phone_clean = ''.join(filter(str.isdigit, login_field))
            if phone_clean.startswith('420'):
                phone_clean = phone_clean[3:]
            phone_full = f'+420{phone_clean}'
            user = User.query.filter_by(phone=phone_full, password_hash=password_hash).first()
        
        if user:
            return jsonify({
                'message': 'Přihlášení úspěšné',
                'user_id': user.id,
                'name': user.name,
                'rating': user.rating or 5.0
            }), 200
        else:
            return jsonify({'error': 'Neplatné přihlašovací údaje'}), 401
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/list', methods=['GET'])
def list_users():
    try:
        users = User.query.order_by(User.created_at.desc()).all()
        result = []
        for user in users:
            result.append({
                'id': user.id,
                'name': user.name,
                'phone': user.phone,
                'password_hash': user.password_hash,
                'created_at': user.created_at.isoformat()
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/search', methods=['POST'])
def search_user():
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Zadejte email nebo telefon'}), 400
        
        user = None
        if '@' in query:
            user = User.query.filter(User.email.like(f'%{query}%')).first()
        else:
            phone_clean = ''.join(filter(str.isdigit, query))
            search_pattern = f'%{phone_clean}%'
            user = User.query.filter(User.phone.like(search_pattern)).first()

        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        return jsonify({
            'id': user.id,
            'name': user.name,
            'phone': user.phone,
            'email': user.email or '',
            'rating': user.rating or 5.0
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/block', methods=['POST'])
def block_user():
    try:
        data = request.get_json()
        blocker_id = data.get('blocker_id')
        
        if not blocker_id:
            return jsonify({'error': 'Přihlášení je vyžadováno'}), 401
        blocked_id = data.get('blocked_id')
        reason = data.get('reason', '')
        
        new_blocked_user = BlockedUser(
            blocker_id=blocker_id,
            blocked_id=blocked_id,
            reason=reason
        )
        db.session.add(new_blocked_user)
        db.session.commit()
        
        return jsonify({'message': 'Uživatel zablokován'}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/<int:user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Uživatel nenalezen'}), 404
        
        stats = UserStats.query.filter_by(user_id=user_id).first()
        
        if not stats:
            stats = UserStats(user_id=user_id)
            db.session.add(stats)
            db.session.commit()

        return jsonify({
            'total_rides': stats.total_rides,
            'total_distance': stats.total_distance,
            'co2_saved': stats.co2_saved,
            'money_saved': stats.money_saved
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500