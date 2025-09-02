# %%
"""
Railway-Optimized Medical AI API
Handles missing large files gracefully for cloud deployment
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Global state
medical_api = None

def create_minimal_system():
    """Create a minimal working system for demonstration."""
    
    # Check if we have the full database
    if os.path.exists('medications.jsonl'):
        try:
            # Try to use the full system
            from production_api import create_production_api
            return create_production_api()
        except Exception as e:
            logging.warning(f"Could not load full system: {e}")
    
    # Create minimal demo system
    logging.info("Creating minimal demo system")
    
    class MinimalMedicalAPI:
        def __init__(self):
            self.request_count = 0
            self.demo_medications = {
                "60002283": {
                    "name": "ANASTROZOLE ACCORD 1 mg, comprimé pelliculé",
                    "form": "comprimé pelliculé",
                    "route": "orale",
                    "status": "Autorisation active",
                    "components": [{"dosage": "ANASTROZOLE", "refDosage": "1,00 mg"}]
                }
            }
        
        def health_check(self):
            return type('APIResponse', (), {
                'success': True,
                'to_dict': lambda: {
                    'success': True,
                    'data': {
                        'status': 'healthy',
                        'mode': 'minimal_demo',
                        'uptime_seconds': 60,
                        'request_count': self.request_count
                    },
                    'timestamp': datetime.now().isoformat()
                }
            })()
        
        def query_medication(self, query, options=None):
            self.request_count += 1
            
            # Simple demo response
            if "anastrozole" in query.lower():
                response = "L'ANASTROZOLE ACCORD 1 mg est un inhibiteur de l'aromatase sous forme de comprimé pelliculé pour administration orale. Il est indiqué dans le traitement du cancer du sein à récepteurs hormonaux positifs chez la femme ménopausée."
                confidence = 0.85
            else:
                response = f"Système de démonstration actif. Question reçue: '{query}'. Le système complet sera disponible une fois les données complètes chargées."
                confidence = 0.60
            
            return type('APIResponse', (), {
                'success': True,
                'to_dict': lambda: {
                    'success': True,
                    'data': {
                        'request_id': f"demo_{self.request_count}",
                        'query': query,
                        'response': response,
                        'confidence': confidence,
                        'approach_used': 'minimal_demo',
                        'model_used': 'demo_system',
                        'sources': ['minimal_database']
                    },
                    'metadata': {
                        'response_time_seconds': 0.1,
                        'endpoint': 'query_medication'
                    },
                    'timestamp': datetime.now().isoformat()
                }
            })()
        
        def search_medications(self, search_term, limit=10):
            return type('APIResponse', (), {
                'success': True,
                'to_dict': lambda: {
                    'success': True,
                    'data': {
                        'search_term': search_term,
                        'total_results': 1,
                        'medications': [{
                            'cis': '60002283',
                            'name': 'ANASTROZOLE ACCORD 1 mg, comprimé pelliculé',
                            'form': 'comprimé pelliculé',
                            'route': 'orale',
                            'status': 'Autorisation active',
                            'similarity_score': 0.95,
                            'components': [{'dosage': 'ANASTROZOLE', 'ref_dosage': '1,00 mg', 'nature': 'comprimé'}]
                        }]
                    },
                    'timestamp': datetime.now().isoformat()
                }
            })()
        
        def get_medication_by_cis(self, cis_code):
            if cis_code in self.demo_medications:
                med = self.demo_medications[cis_code]
                return type('APIResponse', (), {
                    'success': True,
                    'to_dict': lambda: {
                        'success': True,
                        'data': {
                            'cis': cis_code,
                            'found': True,
                            'medication': med
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                })()
            else:
                return type('APIResponse', (), {
                    'success': True,
                    'to_dict': lambda: {
                        'success': True,
                        'data': {
                            'cis': cis_code,
                            'found': False
                        },
                        'timestamp': datetime.now().isoformat()
                    }
                })()
    
    return MinimalMedicalAPI()

# Initialize the system
try:
    medical_api = create_minimal_system()
    logging.info("Medical API system initialized")
except Exception as e:
    logging.error(f"Failed to initialize: {e}")

# Routes
@app.route('/')
def api_info():
    return jsonify({
        'name': 'Medical AI API',
        'version': '1.0.0',
        'description': 'Production Medical AI API with RAG system',
        'status': 'operational',
        'mode': 'Railway deployment',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        health_result = medical_api.health_check()
        return jsonify(health_result.to_dict())
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/query', methods=['POST'])
def query_medication():
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
        
        query = data['query']
        options = data.get('options', {})
        
        result = medical_api.query_medication(query, options)
        return jsonify(result.to_dict())
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search', methods=['POST'])
def search_medications():
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        data = request.get_json()
        if not data or 'search_term' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing search_term parameter'
            }), 400
        
        search_term = data['search_term']
        limit = data.get('limit', 10)
        
        result = medical_api.search_medications(search_term, limit)
        return jsonify(result.to_dict())
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/medication/<cis_code>')
def get_medication_by_cis(cis_code):
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        result = medical_api.get_medication_by_cis(cis_code)
        return jsonify(result.to_dict())
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8080))
    print(f"🏥 Starting Medical AI API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
