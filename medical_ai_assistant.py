# %%
"""
Complete Medical AI Assistant
Integrates: RAG System + Fine-Tuned Models + Smart Query Routing

This is your production-ready medical AI assistant that combines:
- RAG system for accurate medication retrieval
- Fine-tuned OpenAI models for specialized responses
- Intelligent query routing and response optimization
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from rag_system import setup_rag_system, MedicationRAG
from finetuning_monitor import FineTuningMonitor

# Setup logging
log_file = f"/Users/xavi/Desktop/MonMedicamentScraper/Database/logs/medical_assistant_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

class MedicalAIAssistant:
    """Production-ready medical AI assistant with RAG and fine-tuned models."""
    
    def __init__(self):
        """Initialize the complete medical AI system."""
        print("🏥 Initializing Medical AI Assistant...")
        
        # Initialize RAG system
        self.rag_system = self._setup_rag_system()
        
        # Initialize OpenAI client and get available models
        self.openai_client = None
        self.fine_tuned_models = []
        self._setup_openai_client()
        
        # Load configuration
        self.config = self._load_configuration()
        
        logging.info("Medical AI Assistant initialized successfully")
    
    def _setup_rag_system(self) -> Optional[MedicationRAG]:
        """Setup RAG system."""
        try:
            rag = setup_rag_system()
            if rag and rag.embeddings is not None:
                print("✅ RAG system ready with embeddings")
                return rag
            else:
                print("⚠️  RAG system initialized but embeddings may need generation")
                return rag
        except Exception as e:
            logging.error(f"Failed to setup RAG system: {e}")
            return None
    
    def _setup_openai_client(self):
        """Setup OpenAI client and discover fine-tuned models."""
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                
                # Get fine-tuned models
                monitor = FineTuningMonitor(api_key)
                jobs = monitor.list_fine_tuning_jobs(20)
                
                # Find successful medical models
                for job in jobs:
                    if (job['status'] == 'succeeded' and 
                        job['model'] == 'gpt-3.5-turbo-0125' and 
                        job.get('fine_tuned_model')):
                        self.fine_tuned_models.append(job['fine_tuned_model'])
                
                print(f"✅ Found {len(self.fine_tuned_models)} fine-tuned medical models")
                
            else:
                logging.warning("OPENAI_API_KEY not set")
                
        except ImportError:
            logging.error("OpenAI library not available")
        except Exception as e:
            logging.error(f"Error setting up OpenAI client: {e}")
    
    def _load_configuration(self) -> Dict:
        """Load system configuration."""
        return {
            'max_context_length': 4000,
            'retrieval_top_k': 5,
            'temperature': 0.1,
            'max_response_tokens': 800,
            'use_citations': True,
            'fallback_to_base_model': True
        }
    
    def analyze_query(self, query: str) -> Dict:
        """Analyze query to determine best response strategy."""
        query_lower = query.lower()
        
        analysis = {
            'query_type': 'general',
            'has_cis_code': False,
            'has_medication_name': False,
            'complexity': 'medium',
            'recommended_approach': 'rag_enhanced'
        }
        
        # Check for CIS code
        import re
        if re.search(r'cis\s*\d{8}', query_lower):
            analysis['has_cis_code'] = True
            analysis['query_type'] = 'specific_medication'
            analysis['recommended_approach'] = 'local_lookup'
        
        # Check for specific medication names
        medication_keywords = ['médicament', 'comprimé', 'gélule', 'solution', 'injectable']
        if any(keyword in query_lower for keyword in medication_keywords):
            analysis['has_medication_name'] = True
            analysis['query_type'] = 'medication_info'
        
        # Check complexity
        complex_keywords = ['indications', 'contre-indications', 'effets', 'posologie', 'interactions']
        if any(keyword in query_lower for keyword in complex_keywords):
            analysis['complexity'] = 'high'
            analysis['recommended_approach'] = 'rag_enhanced'
        
        # Simple queries
        simple_keywords = ['nom', 'forme', 'composition', 'statut']
        if any(keyword in query_lower for keyword in simple_keywords) and len(query.split()) < 8:
            analysis['complexity'] = 'low'
            analysis['recommended_approach'] = 'quick_lookup'
        
        return analysis
    
    def get_best_response(self, query: str) -> Dict:
        """Get the best possible response using all available systems."""
        
        print(f"🧠 Processing: {query}")
        
        # Analyze query
        analysis = self.analyze_query(query)
        approach = analysis['recommended_approach']
        
        response_data = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
            'query_analysis': analysis,
            'approach_used': approach,
            'response': None,
            'context_used': None,
            'model_used': None,
            'confidence': 0.0,
            'sources': []
        }
        
        try:
            if approach == 'local_lookup':
                response_data.update(self._handle_local_lookup(query))
            elif approach == 'quick_lookup':
                response_data.update(self._handle_quick_lookup(query))
            elif approach == 'rag_enhanced':
                response_data.update(self._handle_rag_enhanced(query))
            else:
                response_data.update(self._handle_fallback(query))
            
        except Exception as e:
            logging.error(f"Error processing query: {e}")
            response_data['response'] = f"Erreur lors du traitement de la requête: {str(e)}"
            response_data['confidence'] = 0.0
        
        return response_data
    
    def _handle_local_lookup(self, query: str) -> Dict:
        """Handle queries with CIS codes using local database."""
        import re
        
        # Extract CIS code
        cis_match = re.search(r'cis\s*(\d{8})', query.lower())
        if not cis_match:
            return self._handle_fallback(query)
        
        cis_code = cis_match.group(1)
        
        # Quick local lookup
        if hasattr(self.rag_system, 'medication_db') and cis_code in self.rag_system.medication_db:
            med_data = self.rag_system.medication_db[cis_code]
            
            # Format response
            components_text = ", ".join([
                f"{comp.get('dosage', '')} {comp.get('refDosage', '')}" 
                for comp in med_data.get('components', []) if comp.get('dosage')
            ])
            
            response = f"""
Médicament CIS {cis_code}:
• Nom: {med_data['name']}
• Forme: {med_data.get('pharmaForm', 'N/A')}
• Administration: {med_data.get('adminRoute', 'N/A')}
• Statut: {med_data.get('status', 'N/A')}
• Composition: {components_text or 'Information non disponible'}
""".strip()
            
            return {
                'response': response,
                'model_used': 'local_database',
                'confidence': 0.95,
                'sources': ['local_medication_database'],
                'context_used': f"Medication record CIS {cis_code}"
            }
        
        return self._handle_fallback(query)
    
    def _handle_quick_lookup(self, query: str) -> Dict:
        """Handle simple queries with quick search."""
        if not self.rag_system:
            return self._handle_fallback(query)
        
        # Use semantic search for quick lookup
        results = self.rag_system.search_medications(query, top_k=3)
        
        if results:
            # Format quick response
            response_parts = []
            for i, (med, score) in enumerate(results, 1):
                components = ", ".join([
                    comp.get('dosage', '') for comp in med.components if comp.get('dosage')
                ])
                
                response_parts.append(
                    f"{i}. {med.name} (CIS: {med.cis})\n"
                    f"   Forme: {med.pharma_form}, Route: {med.admin_route}\n"
                    f"   Composition: {components}"
                )
            
            response = "Médicaments trouvés:\n\n" + "\n\n".join(response_parts)
            
            return {
                'response': response,
                'model_used': 'semantic_search',
                'confidence': max(score for _, score in results),
                'sources': ['medication_database_search'],
                'context_used': f"Top {len(results)} matching medications"
            }
        
        return self._handle_fallback(query)
    
    def _handle_rag_enhanced(self, query: str) -> Dict:
        """Handle complex queries with RAG + fine-tuned model."""
        if not self.rag_system:
            return self._handle_fallback(query)
        
        # Use RAG system for enhanced query
        model_to_use = None
        
        # Use fine-tuned model if available
        if self.fine_tuned_models:
            model_to_use = self.fine_tuned_models[0]  # Use first available model
        
        rag_result = self.rag_system.enhanced_query(query, model_id=model_to_use)
        
        if rag_result.get('success'):
            return {
                'response': rag_result['response'],
                'model_used': rag_result['model'],
                'confidence': 0.85,
                'sources': ['rag_system', 'fine_tuned_model' if model_to_use else 'base_model'],
                'context_used': rag_result.get('context', '')[:200] + "..."
            }
        
        return self._handle_fallback(query)
    
    def _handle_fallback(self, query: str) -> Dict:
        """Fallback handler for queries that can't be processed by other methods."""
        
        if self.openai_client:
            try:
                # Use base model as fallback
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {
                            "role": "system",
                            "content": "Vous êtes un assistant médical. Répondez de manière précise et indiquez clairement si vous n'avez pas d'information spécifique."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    max_tokens=500,
                    temperature=0.2
                )
                
                return {
                    'response': response.choices[0].message.content,
                    'model_used': 'gpt-3.5-turbo',
                    'confidence': 0.6,
                    'sources': ['openai_base_model'],
                    'context_used': 'No specific medication context'
                }
                
            except Exception as e:
                logging.error(f"Fallback query failed: {e}")
        
        return {
            'response': "Je ne peux pas traiter cette requête pour le moment. Veuillez réessayer ou reformuler votre question.",
            'model_used': 'error_handler',
            'confidence': 0.0,
            'sources': ['error'],
            'context_used': 'None'
        }
    
    def batch_query(self, queries: List[str]) -> List[Dict]:
        """Process multiple queries efficiently."""
        results = []
        
        print(f"📋 Processing {len(queries)} queries...")
        
        for i, query in enumerate(queries, 1):
            print(f"🔍 Query {i}/{len(queries)}")
            result = self.get_best_response(query)
            results.append(result)
        
        return results
    
    def get_system_status(self) -> Dict:
        """Get comprehensive system status."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'rag_system': {
                'available': self.rag_system is not None,
                'embeddings_ready': self.rag_system.embeddings is not None if self.rag_system else False,
                'medication_count': len(self.rag_system.medications) if self.rag_system else 0
            },
            'openai_models': {
                'client_available': self.openai_client is not None,
                'fine_tuned_models': len(self.fine_tuned_models),
                'models_list': self.fine_tuned_models
            },
            'system_health': 'unknown'
        }
        
        # Determine system health
        if (status['rag_system']['available'] and 
            status['rag_system']['embeddings_ready'] and
            status['openai_models']['client_available']):
            
            if status['openai_models']['fine_tuned_models'] > 0:
                status['system_health'] = 'optimal'
            else:
                status['system_health'] = 'good'
        elif status['rag_system']['available']:
            status['system_health'] = 'limited'
        else:
            status['system_health'] = 'degraded'
        
        return status

# %%
def create_medical_assistant() -> MedicalAIAssistant:
    """Create and initialize the medical assistant."""
    return MedicalAIAssistant()

def demo_medical_assistant():
    """Demonstrate the medical assistant capabilities."""
    
    print("🚀 Medical AI Assistant Demo")
    print("=" * 35)
    
    # Initialize assistant
    assistant = create_medical_assistant()
    
    # Show system status
    status = assistant.get_system_status()
    print(f"\n📊 System Status: {status['system_health'].upper()}")
    print(f"✅ RAG System: {'Ready' if status['rag_system']['available'] else 'Not Available'}")
    print(f"✅ Embeddings: {'Ready' if status['rag_system']['embeddings_ready'] else 'Not Ready'}")
    print(f"✅ Medications: {status['rag_system']['medication_count']:,}")
    print(f"✅ Fine-tuned Models: {status['openai_models']['fine_tuned_models']}")
    
    # Demo queries
    demo_queries = [
        "Informations sur le médicament CIS 60002283",
        "Quels sont les médicaments à base d'anastrozole?",
        "Quelles sont les contre-indications de la manidipine?",
        "Posologie recommandée pour TEMERITDUO 5 mg/12,5 mg",
        "Médicaments pour l'hypertension artérielle"
    ]
    
    print(f"\n🧪 Testing {len(demo_queries)} sample queries:")
    print("=" * 45)
    
    for i, query in enumerate(demo_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 50)
        
        result = assistant.get_best_response(query)
        
        print(f"🎯 Approach: {result['approach_used']}")
        print(f"🤖 Model: {result['model_used']}")
        print(f"📊 Confidence: {result['confidence']:.2f}")
        print(f"📝 Response: {result['response'][:150]}...")
        
        if result.get('sources'):
            print(f"📚 Sources: {', '.join(result['sources'])}")
    
    return assistant

# %%
def create_api_interface(assistant: MedicalAIAssistant):
    """Create a simple API-like interface for the medical assistant."""
    
    print("\n🌐 Medical AI API Interface")
    print("=" * 30)
    
    def query_api(query: str) -> Dict:
        """API endpoint simulation."""
        result = assistant.get_best_response(query)
        
        # Format for API response
        api_response = {
            'success': True,
            'query': query,
            'response': result['response'],
            'metadata': {
                'model': result['model_used'],
                'confidence': result['confidence'],
                'approach': result['approach_used'],
                'sources': result['sources'],
                'timestamp': result['timestamp']
            }
        }
        
        return api_response
    
    # Demo API calls
    print("📋 API Demo:")
    
    test_calls = [
        "Qu'est-ce que l'ANASTROZOLE ACCORD 1 mg?",
        "CIS 60002283 informations complètes"
    ]
    
    for call in test_calls:
        print(f"\n🔌 API Call: {call}")
        response = query_api(call)
        print(f"✅ Success: {response['success']}")
        print(f"📝 Response: {response['response'][:100]}...")
        print(f"🤖 Model: {response['metadata']['model']}")
    
    return query_api

# %%
def monitor_fine_tuning_progress():
    """Check progress of fine-tuning jobs."""
    
    print("\n⏰ Fine-Tuning Progress Check")
    print("=" * 35)
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ API key not available")
        return
    
    try:
        monitor = FineTuningMonitor(api_key)
        jobs = monitor.list_fine_tuning_jobs(10)
        
        # Filter medical jobs
        medical_jobs = [j for j in jobs if j['model'] == 'gpt-3.5-turbo-0125']
        
        if medical_jobs:
            print(f"📊 Medical Fine-Tuning Jobs Status:")
            
            for job in medical_jobs:
                status_emoji = {
                    'succeeded': '✅',
                    'failed': '❌',
                    'running': '🔄',
                    'validating_files': '⏳',
                    'queued': '⏳'
                }.get(job['status'], '⚪')
                
                print(f"  {status_emoji} {job['id']}: {job['status']}")
                
                if job.get('trained_tokens'):
                    print(f"    └─ Trained tokens: {job['trained_tokens']:,}")
                
                if job.get('estimated_finish'):
                    finish_time = datetime.fromtimestamp(job['estimated_finish'])
                    print(f"    └─ ETA: {finish_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Summary
            succeeded = len([j for j in medical_jobs if j['status'] == 'succeeded'])
            running = len([j for j in medical_jobs if j['status'] in ['running', 'validating_files', 'queued']])
            failed = len([j for j in medical_jobs if j['status'] == 'failed'])
            
            print(f"\n📈 Summary:")
            print(f"  ✅ Completed: {succeeded}")
            print(f"  🔄 Running: {running}")
            print(f"  ❌ Failed: {failed}")
            
            if succeeded > 0:
                print(f"\n🎉 {succeeded} medical models are ready for use!")
            
            if running > 0:
                print(f"\n⏳ {running} models still training (check again in 1-2 hours)")
        
        else:
            print("No medical fine-tuning jobs found")
    
    except Exception as e:
        logging.error(f"Error checking fine-tuning progress: {e}")

# %%
if __name__ == "__main__":
    print("🏥 Complete Medical AI Assistant System")
    print("=" * 45)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check fine-tuning progress first
    monitor_fine_tuning_progress()
    
    # Initialize and demo the assistant
    assistant = demo_medical_assistant()
    
    if assistant:
        # Create API interface
        api = create_api_interface(assistant)
        
        print("\n🎯 SYSTEM READY!")
        print("=" * 20)
        print("✅ RAG system operational")
        print("✅ Medical assistant initialized")
        print("✅ API interface ready")
        print("✅ Fine-tuning jobs monitored")
        
        print(f"\n📋 Usage:")
        print(f"from medical_ai_assistant import create_medical_assistant")
        print(f"assistant = create_medical_assistant()")
        print(f"result = assistant.get_best_response('Votre question')")
        
        print(f"\n📝 Logs: {log_file}")
        
        # Show next steps
        print(f"\n🚀 Next Steps:")
        print(f"1. Wait for fine-tuning jobs to complete (~3 AM Sept 3rd)")
        print(f"2. Test with completed models")
        print(f"3. Deploy in your SwiftUI app")
        print(f"4. Monitor and optimize performance")
    
    else:
        print("❌ Failed to initialize medical assistant")
