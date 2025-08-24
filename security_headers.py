# Bezpečnostní hlavičky
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' unpkg.com api.qrserver.com; style-src 'self' 'unsafe-inline' unpkg.com; img-src 'self' data: api.qrserver.com *.tile.openstreetmap.org"
    return response