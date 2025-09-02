# %%
"""
RAG (Retrieval-Augmented Generation) System for Medical Medication Database

This system provides intelligent retrieval of medication information to enhance
OpenAI model responses with accurate, contextual data.
"""

import os
import json
import numpy as np
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re
from dataclasses import dataclass

# Setup logging
log_file = f"/Users/xavi/Desktop/MonMedicamentScraper/Database/logs/rag_system_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

@dataclass
class MedicationRecord:
    """Structured medication record for RAG system."""
    cis: str
    name: str
    pharma_form: str
    admin_route: str
    status: str
    components: List[Dict]
    rcp_text: str
    notice_text: str
    
    def to_searchable_text(self) -> str:
        """Convert to searchable text for embeddings."""
        components_text = " ".join([
            f"{comp.get('dosage', '')} {comp.get('refDosage', '')}" 
            for comp in self.components
        ])
        
        # Clean and format text
        rcp_clean = self._clean_text(self.rcp_text)
        notice_clean = self._clean_text(self.notice_text)
        
        searchable = f"""
        CIS: {self.cis}
        Nom: {self.name}
        Forme: {self.pharma_form}
        Administration: {self.admin_route}
        Statut: {self.status}
        Composition: {components_text}
        
        Résumé des caractéristiques:
        {rcp_clean[:2000]}
        
        Notice patient:
        {notice_clean[:1000]}
        """.strip()
        
        return searchable
    
    def _clean_text(self, text: str) -> str:
        """Clean text for better processing."""
        if not text:
            return ""
        
        # Remove escape sequences
        text = text.replace("\\n", "\n").replace("\\t", " ")
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove navigation elements
        text = re.sub(r'Retour en haut de la page.*', '', text, flags=re.DOTALL)
        text = re.sub(r'Plan du site\|.*', '', text, flags=re.DOTALL)
        
        return text.strip()

class MedicationRAG:
    """RAG system for medication information retrieval."""
    
    def __init__(self, database_file: str):
        self.database_file = database_file
        self.medications: List[MedicationRecord] = []
        self.embeddings: Optional[np.ndarray] = None
        self.openai_client = None
        
        # Initialize OpenAI client
        self._init_openai_client()
        
        # Load medication database
        self._load_medication_database()
        
        logging.info(f"RAG system initialized with {len(self.medications)} medications")
    
    def _init_openai_client(self):
        """Initialize OpenAI client for embeddings."""
        try:
            import openai
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
                logging.info("OpenAI client initialized for embeddings")
            else:
                logging.warning("OPENAI_API_KEY not set")
        except ImportError:
            logging.error("OpenAI library not available")
    
    def _load_medication_database(self):
        """Load and structure medication database."""
        logging.info(f"Loading medication database from {self.database_file}")
        
        try:
            with open(self.database_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        medication = MedicationRecord(
                            cis=data.get('cis', ''),
                            name=data.get('name', ''),
                            pharma_form=data.get('pharmaForm', ''),
                            admin_route=data.get('adminRoute', ''),
                            status=data.get('status', ''),
                            components=data.get('components', []),
                            rcp_text=data.get('rcp_text', ''),
                            notice_text=data.get('notice_text', '')
                        )
                        
                        self.medications.append(medication)
                        
                    except json.JSONDecodeError as e:
                        logging.warning(f"JSON error at line {line_num}: {e}")
                    except Exception as e:
                        logging.error(f"Error processing line {line_num}: {e}")
            
            logging.info(f"Successfully loaded {len(self.medications)} medication records")
            
        except Exception as e:
            logging.error(f"Failed to load database: {e}")
    
    def generate_embeddings(self, batch_size: int = 100) -> bool:
        """Generate embeddings for all medications."""
        if not self.openai_client:
            logging.error("OpenAI client not available for embeddings")
            return False
        
        logging.info("Starting embedding generation...")
        
        # Prepare texts for embedding
        texts = [med.to_searchable_text() for med in self.medications]
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(texts) + batch_size - 1) // batch_size
            
            logging.info(f"Processing embedding batch {batch_num}/{total_batches}")
            
            try:
                response = self.openai_client.embeddings.create(
                    model="text-embedding-3-small",  # Cost-effective embedding model
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
                
                logging.info(f"✅ Batch {batch_num} completed ({len(batch_embeddings)} embeddings)")
                
            except Exception as e:
                logging.error(f"❌ Batch {batch_num} failed: {e}")
                return False
        
        # Convert to numpy array
        self.embeddings = np.array(all_embeddings)
        
        # Save embeddings
        embeddings_file = "/Users/xavi/Desktop/MonMedicamentScraper/Database/medication_embeddings.npy"
        np.save(embeddings_file, self.embeddings)
        
        logging.info(f"✅ Generated and saved {len(all_embeddings)} embeddings to {embeddings_file}")
        return True
    
    def load_embeddings(self) -> bool:
        """Load pre-generated embeddings."""
        embeddings_file = "/Users/xavi/Desktop/MonMedicamentScraper/Database/medication_embeddings.npy"
        
        try:
            self.embeddings = np.load(embeddings_file)
            logging.info(f"✅ Loaded {self.embeddings.shape[0]} embeddings from file")
            return True
        except Exception as e:
            logging.warning(f"Could not load embeddings: {e}")
            return False
    
    def search_medications(self, query: str, top_k: int = 5) -> List[Tuple[MedicationRecord, float]]:
        """Search for relevant medications using semantic similarity."""
        
        if self.embeddings is None:
            logging.error("Embeddings not available. Run generate_embeddings() first.")
            return []
        
        if not self.openai_client:
            logging.error("OpenAI client not available")
            return []
        
        try:
            # Generate query embedding
            query_response = self.openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query
            )
            
            query_embedding = np.array(query_response.data[0].embedding)
            
            # Calculate similarities
            similarities = np.dot(self.embeddings, query_embedding)
            
            # Get top-k most similar medications
            top_indices = np.argsort(similarities)[-top_k:][::-1]
            
            results = []
            for idx in top_indices:
                medication = self.medications[idx]
                similarity = similarities[idx]
                results.append((medication, similarity))
            
            logging.info(f"Found {len(results)} relevant medications for query: '{query[:50]}...'")
            return results
            
        except Exception as e:
            logging.error(f"Search failed: {e}")
            return []
    
    def get_context_for_query(self, query: str, max_context_length: int = 4000) -> str:
        """Get relevant context for a query to enhance model responses."""
        
        # Search for relevant medications
        relevant_meds = self.search_medications(query, top_k=3)
        
        if not relevant_meds:
            return "Aucune information pertinente trouvée dans la base de données."
        
        context_parts = []
        current_length = 0
        
        for medication, similarity in relevant_meds:
            # Create context entry
            components_text = ", ".join([
                f"{comp.get('dosage', '')} {comp.get('refDosage', '')}" 
                for comp in medication.components if comp.get('dosage')
            ])
            
            context_entry = f"""
Médicament: {medication.name}
CIS: {medication.cis}
Forme: {medication.pharma_form}
Administration: {medication.admin_route}
Statut: {medication.status}
Composition: {components_text}
Pertinence: {similarity:.3f}
"""
            
            # Add detailed info if space allows
            if current_length + len(context_entry) < max_context_length:
                # Add key sections from RCP
                rcp_sections = self._extract_key_sections(medication.rcp_text)
                if rcp_sections:
                    context_entry += f"\nInformations clés:\n{rcp_sections}\n"
                
                context_parts.append(context_entry.strip())
                current_length += len(context_entry)
            else:
                break
        
        return "\n\n".join(context_parts)
    
    def _extract_key_sections(self, rcp_text: str, max_length: int = 800) -> str:
        """Extract key sections from RCP text."""
        if not rcp_text:
            return ""
        
        # Clean text
        text = rcp_text.replace("\\n", "\n")
        
        key_sections = []
        
        # Extract indications
        indications_match = re.search(r'4\.1\.\s*Indications thérapeutiques\s*(.*?)(?=4\.2\.|$)', text, re.DOTALL | re.IGNORECASE)
        if indications_match:
            indications = indications_match.group(1).strip()[:300]
            key_sections.append(f"Indications: {indications}")
        
        # Extract posology
        posology_match = re.search(r'4\.2\.\s*Posologie et mode d\'administration\s*(.*?)(?=4\.3\.|$)', text, re.DOTALL | re.IGNORECASE)
        if posology_match:
            posology = posology_match.group(1).strip()[:300]
            key_sections.append(f"Posologie: {posology}")
        
        # Extract contraindications
        contra_match = re.search(r'4\.3\.\s*Contre-indications\s*(.*?)(?=4\.4\.|$)', text, re.DOTALL | re.IGNORECASE)
        if contra_match:
            contra = contra_match.group(1).strip()[:200]
            key_sections.append(f"Contre-indications: {contra}")
        
        result = "\n".join(key_sections)
        return result[:max_length] if len(result) > max_length else result
    
    def enhanced_query(self, query: str, model_id: str = None) -> Dict:
        """Enhanced query using RAG + fine-tuned model."""
        
        if not self.openai_client:
            return {'success': False, 'error': 'OpenAI client not available'}
        
        # Get relevant context
        context = self.get_context_for_query(query)
        
        # Enhanced prompt with context
        enhanced_prompt = f"""
Contexte médical pertinent:
{context}

Question: {query}

Répondez en utilisant les informations du contexte ci-dessus. Si l'information n'est pas disponible dans le contexte, indiquez-le clairement.
"""
        
        try:
            # Use fine-tuned model if available, otherwise use base model
            if model_id:
                model = model_id
            elif hasattr(self, 'fine_tuned_models') and self.fine_tuned_models:
                model = self.fine_tuned_models[0]
            else:
                model = "gpt-3.5-turbo"  # Fallback to base model
            
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "Vous êtes un assistant médical spécialisé dans les médicaments français. Utilisez uniquement les informations fournies dans le contexte pour répondre aux questions."
                    },
                    {
                        "role": "user",
                        "content": enhanced_prompt
                    }
                ],
                max_tokens=800,
                temperature=0.1  # Low temperature for factual accuracy
            )
            
            return {
                'success': True,
                'query': query,
                'context': context,
                'response': response.choices[0].message.content,
                'model': model,
                'usage': response.usage.__dict__,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logging.error(f"Enhanced query failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'query': query,
                'context': context
            }

# %%
class MedicationSearchEngine:
    """Advanced search engine for medication database."""
    
    def __init__(self, rag_system: MedicationRAG):
        self.rag = rag_system
        self.search_index = self._build_search_index()
    
    def _build_search_index(self) -> Dict:
        """Build search index for fast lookups."""
        logging.info("Building search index...")
        
        index = {
            'cis_to_med': {},
            'name_to_med': {},
            'component_to_meds': {},
            'form_to_meds': {},
            'keywords': {}
        }
        
        for i, med in enumerate(self.rag.medications):
            # CIS index
            index['cis_to_med'][med.cis] = i
            
            # Name index (with variations)
            name_clean = med.name.lower().strip()
            index['name_to_med'][name_clean] = i
            
            # Component index
            for comp in med.components:
                if comp.get('dosage'):
                    dosage = comp['dosage'].lower()
                    if dosage not in index['component_to_meds']:
                        index['component_to_meds'][dosage] = []
                    index['component_to_meds'][dosage].append(i)
            
            # Form index
            if med.pharma_form:
                form = med.pharma_form.lower()
                if form not in index['form_to_meds']:
                    index['form_to_meds'][form] = []
                index['form_to_meds'][form].append(i)
            
            # Keyword extraction
            keywords = self._extract_keywords(med)
            for keyword in keywords:
                if keyword not in index['keywords']:
                    index['keywords'][keyword] = []
                index['keywords'][keyword].append(i)
        
        logging.info("Search index built successfully")
        return index
    
    def _extract_keywords(self, medication: MedicationRecord) -> List[str]:
        """Extract searchable keywords from medication."""
        keywords = []
        
        # Name keywords
        name_words = medication.name.lower().split()
        keywords.extend([word for word in name_words if len(word) > 3])
        
        # Component keywords
        for comp in medication.components:
            if comp.get('dosage'):
                dosage_words = comp['dosage'].lower().split()
                keywords.extend([word for word in dosage_words if len(word) > 3])
        
        # Remove common words
        stop_words = {'pour', 'avec', 'sans', 'dans', 'sous', 'forme', 'comprimé', 'gélule'}
        keywords = [kw for kw in keywords if kw not in stop_words]
        
        return list(set(keywords))
    
    def quick_lookup(self, query: str) -> List[MedicationRecord]:
        """Fast lookup using search index."""
        query_lower = query.lower()
        results = []
        
        # Check for CIS code
        cis_match = re.search(r'(\d{8})', query)
        if cis_match:
            cis_code = cis_match.group(1)
            if cis_code in self.search_index['cis_to_med']:
                idx = self.search_index['cis_to_med'][cis_code]
                results.append(self.rag.medications[idx])
                return results
        
        # Check exact name match
        for name, idx in self.search_index['name_to_med'].items():
            if name in query_lower:
                results.append(self.rag.medications[idx])
        
        # Check component matches
        for component, indices in self.search_index['component_to_meds'].items():
            if component in query_lower:
                for idx in indices[:3]:  # Limit to 3 per component
                    if self.rag.medications[idx] not in results:
                        results.append(self.rag.medications[idx])
        
        # Check keyword matches
        query_words = query_lower.split()
        for word in query_words:
            if word in self.search_index['keywords']:
                for idx in self.search_index['keywords'][word][:2]:  # Limit to 2 per keyword
                    if self.rag.medications[idx] not in results:
                        results.append(self.rag.medications[idx])
        
        return results[:10]  # Return top 10 matches

# %%
def setup_rag_system() -> MedicationRAG:
    """Setup and initialize the RAG system."""
    
    print("🚀 Setting up RAG System for Medical Database")
    print("=" * 50)
    
    database_file = "/Users/xavi/Desktop/MonMedicamentScraper/Database/medications.jsonl"
    
    if not os.path.exists(database_file):
        print(f"❌ Database file not found: {database_file}")
        return None
    
    # Initialize RAG system
    rag = MedicationRAG(database_file)
    
    # Check if embeddings exist
    embeddings_file = "/Users/xavi/Desktop/MonMedicamentScraper/Database/medication_embeddings.npy"
    
    if os.path.exists(embeddings_file):
        print("📁 Loading existing embeddings...")
        if rag.load_embeddings():
            print("✅ Embeddings loaded successfully")
        else:
            print("⚠️  Failed to load embeddings, will regenerate")
            if rag.generate_embeddings():
                print("✅ New embeddings generated")
            else:
                print("❌ Failed to generate embeddings")
    else:
        print("🔄 Generating embeddings for the first time...")
        if rag.generate_embeddings():
            print("✅ Embeddings generated successfully")
        else:
            print("❌ Failed to generate embeddings")
    
    return rag

def demo_rag_queries(rag: MedicationRAG):
    """Demonstrate RAG system capabilities."""
    
    print("\n🧪 RAG System Demo")
    print("=" * 20)
    
    # Initialize search engine
    search_engine = MedicationSearchEngine(rag)
    
    test_queries = [
        "Informations sur le médicament CIS 60002283",
        "Quels médicaments contiennent de l'anastrozole?",
        "Médicaments sous forme de comprimé pelliculé",
        "Indications thérapeutiques de la manidipine",
        "Contre-indications des inhibiteurs calciques"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n🔍 Test {i}: {query}")
        print("-" * 40)
        
        # Quick lookup first
        quick_results = search_engine.quick_lookup(query)
        print(f"🚀 Quick lookup: {len(quick_results)} results")
        
        # Semantic search
        if rag.embeddings is not None:
            semantic_results = rag.search_medications(query, top_k=3)
            print(f"🧠 Semantic search: {len(semantic_results)} results")
            
            for j, (med, score) in enumerate(semantic_results, 1):
                print(f"  {j}. {med.name} (CIS: {med.cis}) - Score: {score:.3f}")
        
        # Enhanced query (if model available)
        enhanced_result = rag.enhanced_query(query)
        if enhanced_result.get('success'):
            print(f"✅ Enhanced response generated")
            print(f"📝 Response preview: {enhanced_result['response'][:100]}...")
        else:
            print(f"⚠️  Enhanced query not available: {enhanced_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    print("🏥 Medical RAG System")
    print("=" * 25)
    
    # Setup RAG system
    rag = setup_rag_system()
    
    if rag:
        # Demo the system
        demo_rag_queries(rag)
        
        print("\n🎯 RAG SYSTEM READY!")
        print("=" * 25)
        print("✅ Medication database loaded")
        print("✅ Search index built")
        print("✅ Embeddings ready")
        print("✅ Enhanced query system active")
        
        print(f"\n📋 Usage Examples:")
        print(f"from rag_system import setup_rag_system")
        print(f"rag = setup_rag_system()")
        print(f"result = rag.enhanced_query('Votre question ici')")
        
    else:
        print("❌ Failed to setup RAG system")
        
    print(f"\n📝 Logs: {log_file}")
