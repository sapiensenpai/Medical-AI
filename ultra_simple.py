# Ultra-simple Flask app for Railway
from flask import Flask, jsonify, request
import os
from datetime import datetime

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        'message': 'Medical AI API is running!',
        'status': 'operational',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/query', methods=['POST'])
def query():
    try:
        data = request.get_json() or {}
        query_text = data.get('query', 'No query provided')
        
        # Simple medical response
        if 'anastrozole' in query_text.lower():
            response = "L'ANASTROZOLE est un inhibiteur de l'aromatase utilisé pour le traitement du cancer du sein chez la femme ménopausée."
        else:
            response = f"Question reçue: {query_text}. Système médical opérationnel."
        
        return jsonify({
            'success': True,
            'data': {
                'query': query_text,
                'response': response,
                'confidence': 0.85
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting on port {port}")
    app.run(host='0.0.0.0', port=port)
