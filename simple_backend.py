"""Thin wrapper to reuse the single source of truth for API routes in simple_web.py."""

from simple_web import app


if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
