# %%
"""
Flask Web API for Medical AI System
Ready for SwiftUI Integration

This creates a production-ready REST API that your SwiftUI app can call
to access the medical AI system with RAG capabilities.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import logging
from datetime import datetime
from production_api import create_production_api, ProductionMedicalAPI

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for SwiftUI app

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Initialize medical API
medical_api: ProductionMedicalAPI = None

def initialize_medical_api():
    """Initialize the medical API system."""
    global medical_api
    try:
        medical_api = create_production_api()
        logging.info("Medical API initialized successfully")
        return True
    except Exception as e:
        logging.error(f"Failed to initialize medical API: {e}")
        return False

# Initialize on startup
if not initialize_medical_api():
    logging.error("Failed to start medical API")

# %%
@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized',
            'timestamp': datetime.now().isoformat()
        }), 503
    
    try:
        health_result = medical_api.health_check()
        return jsonify(health_result.to_dict()), 200 if health_result.success else 503
        
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/query', methods=['POST'])
def query_medication():
    """Main medication query endpoint."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        # Get request data
        data = request.get_json()
        
        if not data or 'query' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing query parameter'
            }), 400
        
        query = data['query']
        options = data.get('options', {})
        
        # Process query
        result = medical_api.query_medication(query, options)
        
        # Return response
        status_code = 200 if result.success else 400
        return jsonify(result.to_dict()), status_code
        
    except Exception as e:
        logging.error(f"Query endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/search', methods=['POST'])
def search_medications():
    """Search medications endpoint."""
    
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
        
        # Validate limit
        if limit > 50:
            limit = 50
        
        result = medical_api.search_medications(search_term, limit)
        
        status_code = 200 if result.success else 400
        return jsonify(result.to_dict()), status_code
        
    except Exception as e:
        logging.error(f"Search endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/medication/<cis_code>', methods=['GET'])
def get_medication_by_cis(cis_code):
    """Get medication by CIS code endpoint."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        # Validate CIS code format
        if not cis_code.isdigit() or len(cis_code) != 8:
            return jsonify({
                'success': False,
                'error': 'Invalid CIS code format (must be 8 digits)'
            }), 400
        
        result = medical_api.get_medication_by_cis(cis_code)
        
        status_code = 200 if result.success else 404
        return jsonify(result.to_dict()), status_code
        
    except Exception as e:
        logging.error(f"CIS lookup failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/batch', methods=['POST'])
def batch_query():
    """Batch query endpoint."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        data = request.get_json()
        
        if not data or 'queries' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing queries parameter'
            }), 400
        
        queries = data['queries']
        
        if not isinstance(queries, list):
            return jsonify({
                'success': False,
                'error': 'Queries must be a list'
            }), 400
        
        result = medical_api.batch_query(queries)
        
        status_code = 200 if result.success else 400
        return jsonify(result.to_dict()), status_code
        
    except Exception as e:
        logging.error(f"Batch endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/stats', methods=['GET'])
def get_api_stats():
    """API statistics endpoint."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        result = medical_api.get_api_stats()
        return jsonify(result.to_dict()), 200
        
    except Exception as e:
        logging.error(f"Stats endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/models', methods=['GET'])
def get_model_status():
    """Get fine-tuning model status."""
    
    if not medical_api:
        return jsonify({
            'success': False,
            'error': 'Medical API not initialized'
        }), 503
    
    try:
        if medical_api.assistant:
            status = medical_api.assistant.get_system_status()
            
            model_data = {
                'fine_tuned_models_count': status['openai_models']['fine_tuned_models'],
                'available_models': status['openai_models']['models_list'],
                'system_health': status['system_health'],
                'rag_system_status': status['rag_system']
            }
            
            return jsonify({
                'success': True,
                'data': model_data,
                'timestamp': datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Assistant not available'
            }), 503
            
    except Exception as e:
        logging.error(f"Models endpoint failed: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/', methods=['GET'])
def api_info():
    """API information endpoint."""
    
    return jsonify({
        'name': 'Medical AI API',
        'version': '1.0.0',
        'description': 'Production Medical AI API with RAG system',
        'endpoints': {
            'GET /health': 'Health check',
            'POST /query': 'Query medications (requires: {"query": "text"})',
            'POST /search': 'Search medications (requires: {"search_term": "text", "limit": 10})',
            'GET /medication/<cis_code>': 'Get medication by CIS code',
            'POST /batch': 'Batch queries (requires: {"queries": ["text1", "text2"]})',
            'GET /stats': 'API usage statistics',
            'GET /models': 'Model status and availability'
        },
        'status': 'operational',
        'timestamp': datetime.now().isoformat()
    })

# %%
def run_api_server(host='127.0.0.1', port=5000, debug=False):
    """Run the Flask API server."""
    
    print("🌐 Starting Medical AI Flask API Server")
    print("=" * 40)
    print(f"🏥 Medical AI System: {'✅ Ready' if medical_api else '❌ Not Ready'}")
    print(f"🌍 Server: http://{host}:{port}")
    print(f"📋 API Docs: http://{host}:{port}/")
    print(f"🔍 Health Check: http://{host}:{port}/health")
    print()
    print("📱 SwiftUI Integration:")
    print(f"   Base URL: http://{host}:{port}")
    print(f"   Query endpoint: POST /query")
    print(f"   Search endpoint: POST /search")
    print()
    print("⚠️  IMPORTANT: Deploy on secure backend server for production!")
    print("=" * 40)
    
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    # Check if running in production or development
    if os.getenv('FLASK_ENV') == 'production':
        # Production settings
        run_api_server(host='0.0.0.0', port=8080, debug=False)
    else:
        # Development settings
        run_api_server(host='127.0.0.1', port=5000, debug=True)
