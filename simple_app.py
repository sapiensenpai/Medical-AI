# %%
"""
Ultra-Simple Medical AI API for Railway
Bulletproof deployment that always works
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime

# Create Flask app
app = Flask(__name__)
CORS(app)

# Simple in-memory medical data
DEMO_MEDICATIONS = {
    "60002283": {
        "cis": "60002283",
        "name": "ANASTROZOLE ACCORD 1 mg, comprimé pelliculé",
        "form": "comprimé pelliculé",
        "route": "orale",
        "status": "Autorisation active",
        "description": "Inhibiteur de l'aromatase indiqué dans le traitement du cancer du sein à récepteurs hormonaux positifs chez la femme ménopausée."
    },
    "61955523": {
        "cis": "61955523", 
        "name": "TEMERITDUO 5 mg/12,5 mg, comprimé pelliculé",
        "form": "comprimé pelliculé",
        "route": "orale", 
        "status": "Autorisation active",
        "description": "Association fixe de nébivolol et hydrochlorothiazide pour le traitement de l'hypertension artérielle essentielle."
    }
}

# Request counter
request_count = 0

@app.route('/')
def home():
    """API information endpoint."""
    return jsonify({
        'name': 'Medical AI API',
        'version': '1.0.0',
        'description': 'Medical AI API with French medication database',
        'status': 'operational',
        'endpoints': [
            'GET /health - Health check',
            'POST /query - Ask medical questions', 
            'POST /search - Search medications',
            'GET /medication/<cis> - Get medication by CIS code'
        ],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health():
    """Simple health check that always works."""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'message': 'Medical AI API is operational',
        'timestamp': datetime.now().isoformat(),
        'request_count': request_count,
        'demo_medications': len(DEMO_MEDICATIONS)
    })

@app.route('/query', methods=['POST'])
def query():
    """Handle medical queries."""
    global request_count
    request_count += 1
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
        
        query_text = data['query'].lower()
        
        # Simple medical responses based on keywords
        if 'anastrozole' in query_text:
            response = "L'ANASTROZOLE ACCORD 1 mg est un inhibiteur de l'aromatase sous forme de comprimé pelliculé pour administration orale. Il est indiqué dans le traitement du cancer du sein à récepteurs hormonaux positifs chez la femme ménopausée. Posologie: 1 comprimé de 1 mg une fois par jour."
            confidence = 0.90
        elif 'temeritduo' in query_text or 'nébivolol' in query_text:
            response = "TEMERITDUO 5 mg/12,5 mg est une association fixe de nébivolol (bêta-bloquant sélectif) et d'hydrochlorothiazide (diurétique) sous forme de comprimé pelliculé. Il est indiqué dans le traitement de l'hypertension artérielle essentielle. Posologie: 1 comprimé par jour."
            confidence = 0.90
        elif 'hypertension' in query_text:
            response = "Pour l'hypertension artérielle, plusieurs médicaments sont disponibles comme TEMERITDUO (association nébivolol/hydrochlorothiazide). Le traitement doit être adapté selon le profil du patient et suivi par un médecin."
            confidence = 0.75
        elif 'cancer' in query_text and 'sein' in query_text:
            response = "Pour le cancer du sein, l'ANASTROZOLE ACCORD 1 mg est un inhibiteur de l'aromatase utilisé chez la femme ménopausée avec cancer du sein à récepteurs hormonaux positifs. Traitement adjuvant recommandé pendant 5 ans."
            confidence = 0.80
        else:
            response = f"Question reçue: '{data['query']}'. Système médical opérationnel. Pour des informations détaillées, consultez la base de données complète des médicaments français."
            confidence = 0.60
        
        return jsonify({
            'success': True,
            'data': {
                'request_id': f"req_{request_count}",
                'query': data['query'],
                'response': response,
                'confidence': confidence,
                'approach_used': 'demo_system',
                'model_used': 'medical_demo',
                'sources': ['demo_database']
            },
            'metadata': {
                'response_time_seconds': 0.1,
                'endpoint': 'query'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search', methods=['POST'])
def search():
    """Search medications."""
    try:
        data = request.get_json()
        if not data or 'search_term' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing search_term parameter'
            }), 400
        
        search_term = data['search_term'].lower()
        limit = data.get('limit', 10)
        
        # Simple search in demo data
        results = []
        for cis, med in DEMO_MEDICATIONS.items():
            if (search_term in med['name'].lower() or 
                search_term in med['description'].lower()):
                
                results.append({
                    'cis': med['cis'],
                    'name': med['name'],
                    'form': med['form'],
                    'route': med['route'],
                    'status': med['status'],
                    'similarity_score': 0.95,
                    'components': [{'dosage': 'Demo', 'ref_dosage': '1mg', 'nature': 'comprimé'}]
                })
        
        return jsonify({
            'success': True,
            'data': {
                'search_term': data['search_term'],
                'total_results': len(results),
                'medications': results[:limit]
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/medication/<cis_code>')
def get_medication(cis_code):
    """Get medication by CIS code."""
    if cis_code in DEMO_MEDICATIONS:
        med = DEMO_MEDICATIONS[cis_code]
        return jsonify({
            'success': True,
            'data': {
                'cis': cis_code,
                'found': True,
                'medication': med
            },
            'timestamp': datetime.now().isoformat()
        })
    else:
        return jsonify({
            'success': True,
            'data': {
                'cis': cis_code,
                'found': False,
                'message': f'CIS {cis_code} not found in demo database'
            },
            'timestamp': datetime.now().isoformat()
        })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"🏥 Starting Simple Medical AI API on port {port}")
    print(f"✅ Demo medications loaded: {len(DEMO_MEDICATIONS)}")
    print(f"🌐 Health check available at /health")
    
    app.run(host='0.0.0.0', port=port, debug=False)
