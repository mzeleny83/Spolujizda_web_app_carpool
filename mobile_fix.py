#!/usr/bin/env python3
"""
Mobilní opravy pro Spolujízda aplikaci
Řešení problémů s prázdnou stránkou na mobilních zařízeních
"""

from flask import Flask, request, jsonify, render_template, make_response
import re
import os

def detect_mobile_device(user_agent):
    """Detekuje mobilní zařízení podle User-Agent"""
    mobile_patterns = [
        r'Mobile', r'Android', r'iPhone', r'iPad', r'iPod',
        r'BlackBerry', r'Windows Phone', r'Opera Mini'
    ]
    
    for pattern in mobile_patterns:
        if re.search(pattern, user_agent, re.IGNORECASE):
            return True
    return False

def add_mobile_fixes(app):
    """Přidá mobilní opravy do Flask aplikace"""
    
    @app.before_request
    def mobile_compatibility():
        """Zajistí mobilní kompatibilitu"""
        user_agent = request.headers.get('User-Agent', '')
        
        # Detekce mobilního zařízení
        if detect_mobile_device(user_agent):
            # Nastavení mobilních hlaviček
            request.is_mobile = True
        else:
            request.is_mobile = False
    
    @app.after_request
    def add_mobile_headers(response):
        """Přidá hlavičky pro mobilní kompatibilitu"""
        
        # Základní mobilní hlavičky
        response.headers['X-UA-Compatible'] = 'IE=edge'
        response.headers['Viewport'] = 'width=device-width, initial-scale=1.0, user-scalable=no'
        
        # Prevence cache problémů na mobilu
        if hasattr(request, 'is_mobile') and request.is_mobile:
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        
        # PWA hlavičky pro mobilní instalaci
        response.headers['X-Mobile-App'] = 'Spolujizda'
        
        # Zabránění zoom problémům
        if request.path == '/':
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        return response
    
    # Mobilní route pro diagnostiku
    @app.route('/mobile-debug')
    def mobile_debug():
        """Diagnostická stránka pro mobilní zařízení"""
        user_agent = request.headers.get('User-Agent', 'Neznámý')
        is_mobile = detect_mobile_device(user_agent)
        
        debug_info = {
            'user_agent': user_agent,
            'is_mobile': is_mobile,
            'headers': dict(request.headers),
            'remote_addr': request.remote_addr,
            'method': request.method,
            'url': request.url,
            'is_secure': request.is_secure
        }
        
        html = f"""
        <!DOCTYPE html>
        <html lang="cs">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
            <title>Mobilní diagnostika - Spolujízda</title>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background: #f5f5f5;
                    font-size: 14px;
                }}
                .info {{ 
                    background: white; 
                    padding: 15px; 
                    border-radius: 8px; 
                    margin: 10px 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                }}
                .mobile {{ background: #d4edda; border-left: 4px solid #28a745; }}
                .desktop {{ background: #cce7ff; border-left: 4px solid #007bff; }}
                pre {{ 
                    background: #f8f9fa; 
                    padding: 10px; 
                    border-radius: 4px; 
                    overflow-x: auto;
                    font-size: 12px;
                }}
                .btn {{
                    display: inline-block;
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 5px;
                }}
            </style>
        </head>
        <body>
            <h1>📱 Mobilní diagnostika</h1>
            
            <div class="info {'mobile' if is_mobile else 'desktop'}">
                <h2>{'📱 Mobilní zařízení' if is_mobile else '💻 Desktop zařízení'}</h2>
                <p><strong>User Agent:</strong> {user_agent}</p>
                <p><strong>IP adresa:</strong> {debug_info['remote_addr']}</p>
                <p><strong>HTTPS:</strong> {'✅ Ano' if debug_info['is_secure'] else '❌ Ne'}</p>
                <p><strong>URL:</strong> {debug_info['url']}</p>
            </div>
            
            <div class="info">
                <h3>🔧 Testy funkčnosti</h3>
                <button onclick="testGPS()" class="btn">📍 Test GPS</button>
                <button onclick="testLocalStorage()" class="btn">💾 Test LocalStorage</button>
                <button onclick="testWebSocket()" class="btn">🔌 Test WebSocket</button>
                <div id="testResults" style="margin-top: 15px;"></div>
            </div>
            
            <div class="info">
                <h3>📋 HTTP hlavičky</h3>
                <pre>{chr(10).join([f'{k}: {v}' for k, v in debug_info['headers']])}</pre>
            </div>
            
            <a href="/" class="btn">🏠 Zpět na hlavní stránku</a>
            
            <script>
                function testGPS() {{
                    const results = document.getElementById('testResults');
                    if (navigator.geolocation) {{
                        results.innerHTML += '<p>📍 GPS: Podporováno, testuje se...</p>';
                        navigator.geolocation.getCurrentPosition(
                            (pos) => {{
                                results.innerHTML += `<p>✅ GPS: Funguje - Lat: ${{pos.coords.latitude.toFixed(4)}}, Lng: ${{pos.coords.longitude.toFixed(4)}}</p>`;
                            }},
                            (err) => {{
                                results.innerHTML += `<p>❌ GPS: Chyba - ${{err.message}}</p>`;
                            }}
                        );
                    }} else {{
                        results.innerHTML += '<p>❌ GPS: Nepodporováno</p>';
                    }}
                }}
                
                function testLocalStorage() {{
                    const results = document.getElementById('testResults');
                    try {{
                        localStorage.setItem('test', 'hodnota');
                        const value = localStorage.getItem('test');
                        localStorage.removeItem('test');
                        results.innerHTML += '<p>✅ LocalStorage: Funguje</p>';
                    }} catch (e) {{
                        results.innerHTML += `<p>❌ LocalStorage: Chyba - ${{e.message}}</p>`;
                    }}
                }}
                
                function testWebSocket() {{
                    const results = document.getElementById('testResults');
                    try {{
                        const ws = new WebSocket('ws://localhost:8080');
                        ws.onopen = () => {{
                            results.innerHTML += '<p>✅ WebSocket: Připojeno</p>';
                            ws.close();
                        }};
                        ws.onerror = (err) => {{
                            results.innerHTML += '<p>❌ WebSocket: Chyba připojení</p>';
                        }};
                    }} catch (e) {{
                        results.innerHTML += `<p>❌ WebSocket: Nepodporováno - ${{e.message}}</p>`;
                    }}
                }}
                
                // Automatický test při načtení
                window.onload = function() {{
                    document.getElementById('testResults').innerHTML = '<h4>🔄 Spouštím automatické testy...</h4>';
                    setTimeout(testLocalStorage, 500);
                    setTimeout(testGPS, 1000);
                    setTimeout(testWebSocket, 1500);
                }};
            </script>
        </body>
        </html>
        """
        
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response

def create_mobile_optimized_index():
    """Vytvoří mobilně optimalizovanou verzi index.html"""
    
    mobile_fixes_js = """
    // Mobilní opravy pro Spolujízda
    (function() {
        'use strict';
        
        // Detekce mobilního zařízení
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|Windows Phone/i.test(navigator.userAgent);
        
        if (isMobile) {
            console.log('📱 Mobilní zařízení detekováno');
            
            // Oprava viewport
            let viewport = document.querySelector('meta[name="viewport"]');
            if (viewport) {
                viewport.setAttribute('content', 'width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover');
            }
            
            // Prevence zoom při focus na input
            document.addEventListener('focusin', function(e) {
                if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                    document.querySelector('meta[name="viewport"]').setAttribute('content', 'width=device-width, initial-scale=1.0, user-scalable=no, maximum-scale=1.0');
                }
            });
            
            document.addEventListener('focusout', function(e) {
                document.querySelector('meta[name="viewport"]').setAttribute('content', 'width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover');
            });
            
            // Oprava touch eventů
            document.addEventListener('touchstart', function() {}, { passive: true });
            
            // Mobilní CSS opravy
            const mobileCSS = `
                <style id="mobile-fixes">
                    /* Mobilní opravy */
                    body { 
                        -webkit-text-size-adjust: 100%; 
                        -webkit-tap-highlight-color: transparent;
                        touch-action: manipulation;
                    }
                    
                    input, textarea, select {
                        font-size: 16px !important; /* Prevence zoom na iOS */
                    }
                    
                    .container {
                        padding: 10px;
                        max-width: 100vw;
                        overflow-x: hidden;
                    }
                    
                    .left-column {
                        width: 100% !important;
                        position: relative !important;
                    }
                    
                    .right-panel {
                        width: 100% !important;
                        height: 60vh !important;
                    }
                    
                    #map {
                        height: 60vh !important;
                        min-height: 300px !important;
                    }
                    
                    .main-content {
                        flex-direction: column !important;
                    }
                    
                    .form-container {
                        margin: 10px 0 !important;
                        padding: 15px !important;
                    }
                    
                    button {
                        min-height: 44px !important; /* iOS doporučení */
                        font-size: 16px !important;
                    }
                    
                    .modal-content {
                        margin: 10% auto !important;
                        width: 95% !important;
                        max-width: 400px !important;
                    }
                    
                    /* Skrytí panel toggle na mobilu */
                    .panel-toggle {
                        display: none !important;
                    }
                </style>
            `;
            
            document.head.insertAdjacentHTML('beforeend', mobileCSS);
            
            // Oprava mapy pro mobil
            window.addEventListener('load', function() {
                if (window.map && window.L) {
                    setTimeout(function() {
                        map.invalidateSize();
                        console.log('📱 Mapa přizpůsobena pro mobil');
                    }, 1000);
                }
            });
            
            // Diagnostika pro debugging
            console.log('📱 Mobilní opravy aplikovány');
            console.log('Screen:', screen.width + 'x' + screen.height);
            console.log('Viewport:', window.innerWidth + 'x' + window.innerHeight);
            console.log('User Agent:', navigator.userAgent);
        }
        
        // Globální error handler
        window.addEventListener('error', function(e) {
            console.error('🚨 JavaScript chyba:', e.error);
            
            // Zobrazení chyby uživateli na mobilu
            if (isMobile) {
                const errorDiv = document.createElement('div');
                errorDiv.style.cssText = `
                    position: fixed; top: 10px; left: 10px; right: 10px; 
                    background: #dc3545; color: white; padding: 10px; 
                    border-radius: 5px; z-index: 9999; font-size: 14px;
                `;
                errorDiv.innerHTML = `❌ Chyba: ${e.message} <button onclick="this.parentNode.remove()" style="float: right; background: none; border: none; color: white;">✕</button>`;
                document.body.appendChild(errorDiv);
                
                setTimeout(() => {
                    if (errorDiv.parentNode) errorDiv.remove();
                }, 5000);
            }
        });
        
    })();
    """
    
    return mobile_fixes_js

if __name__ == '__main__':
    print("📱 Mobilní opravy pro Spolujízda")
    print("Tento soubor obsahuje opravy pro mobilní kompatibilitu.")
    print("Importujte add_mobile_fixes(app) do hlavní aplikace.")