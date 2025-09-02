# %%
import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import argparse

# NOTE: This script requires the openai library
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI library not installed. Run: pip install openai")

# Configuration
LOGS_DIR = "/Users/xavi/Desktop/MonMedicamentScraper/Database/logs"
AUDIT_DIR = "/Users/xavi/Desktop/MonMedicamentScraper/Database/audit"
MODELS_DIR = "/Users/xavi/Desktop/MonMedicamentScraper/Database/trained_models"

# Setup directories
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(AUDIT_DIR, exist_ok=True)

# Setup logging
log_file = os.path.join(LOGS_DIR, f"finetuning_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# %%
class FineTuningMonitor:
    """Comprehensive fine-tuning job monitor with compliance logging."""
    
    def __init__(self, api_key: str, organization: Optional[str] = None):
        """Initialize monitor with API credentials."""
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not installed")
        
        self.client = openai.OpenAI(
            api_key=api_key,
            organization=organization
        )
        
        self.session_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        logging.info(f"Initialized monitor with session ID: {self.session_id}")
    
    def list_fine_tuning_jobs(self, limit: int = 20) -> List[Dict]:
        """List recent fine-tuning jobs."""
        try:
            response = self.client.fine_tuning.jobs.list(limit=limit)
            jobs = []
            
            for job in response.data:
                job_info = {
                    'id': job.id,
                    'model': job.model,
                    'status': job.status,
                    'created_at': job.created_at,
                    'finished_at': job.finished_at,
                    'fine_tuned_model': job.fine_tuned_model,
                    'training_file': job.training_file,
                    'validation_file': job.validation_file,
                    'trained_tokens': job.trained_tokens,
                    'estimated_finish': job.estimated_finish
                }
                jobs.append(job_info)
            
            logging.info(f"Retrieved {len(jobs)} fine-tuning jobs")
            return jobs
            
        except Exception as e:
            logging.error(f"Error listing jobs: {e}")
            return []
    
    def get_job_details(self, job_id: str) -> Optional[Dict]:
        """Get detailed information about a specific job."""
        try:
            response = self.client.fine_tuning.jobs.retrieve(job_id)
            
            job_details = {
                'id': response.id,
                'object': response.object,
                'model': response.model,
                'created_at': response.created_at,
                'finished_at': response.finished_at,
                'fine_tuned_model': response.fine_tuned_model,
                'organization_id': response.organization_id,
                'result_files': response.result_files,
                'status': response.status,
                'validation_file': response.validation_file,
                'training_file': response.training_file,
                'hyperparameters': response.hyperparameters.__dict__ if response.hyperparameters else None,
                'trained_tokens': response.trained_tokens,
                'estimated_finish': response.estimated_finish,
                'error': response.error.__dict__ if response.error else None
            }
            
            logging.info(f"Retrieved details for job: {job_id}")
            return job_details
            
        except Exception as e:
            logging.error(f"Error getting job details for {job_id}: {e}")
            return None
    
    def get_job_events(self, job_id: str, limit: int = 50) -> List[Dict]:
        """Get training events/logs for a job."""
        try:
            response = self.client.fine_tuning.jobs.list_events(fine_tuning_job_id=job_id, limit=limit)
            events = []
            
            for event in response.data:
                event_info = {
                    'id': event.id,
                    'object': event.object,
                    'created_at': event.created_at,
                    'level': event.level,
                    'message': event.message,
                    'type': event.type
                }
                events.append(event_info)
            
            logging.info(f"Retrieved {len(events)} events for job: {job_id}")
            return events
            
        except Exception as e:
            logging.error(f"Error getting job events for {job_id}: {e}")
            return []
    
    def monitor_job_progress(self, job_id: str, check_interval: int = 60, 
                           max_duration: int = 24*60*60) -> Dict:
        """Monitor a specific job until completion."""
        logging.info(f"Starting monitoring for job: {job_id}")
        
        start_time = time.time()
        max_end_time = start_time + max_duration
        
        monitoring_log = {
            'job_id': job_id,
            'session_id': self.session_id,
            'start_time': datetime.fromtimestamp(start_time).isoformat(),
            'status_checks': [],
            'final_status': None,
            'total_duration': 0,
            'events_log': []
        }
        
        while time.time() < max_end_time:
            try:
                # Get current status
                job_details = self.get_job_details(job_id)
                if not job_details:
                    logging.error("Failed to get job details")
                    break
                
                current_time = datetime.now().isoformat()
                status_check = {
                    'timestamp': current_time,
                    'status': job_details['status'],
                    'trained_tokens': job_details['trained_tokens'],
                    'estimated_finish': job_details['estimated_finish']
                }
                
                monitoring_log['status_checks'].append(status_check)
                
                logging.info(f"Job {job_id} status: {job_details['status']}")
                if job_details['trained_tokens']:
                    logging.info(f"Trained tokens: {job_details['trained_tokens']:,}")
                
                # Check if job is complete
                if job_details['status'] in ['succeeded', 'failed', 'cancelled']:
                    end_time = time.time()
                    monitoring_log['final_status'] = job_details['status']
                    monitoring_log['total_duration'] = end_time - start_time
                    monitoring_log['end_time'] = datetime.fromtimestamp(end_time).isoformat()
                    
                    # Get final events
                    events = self.get_job_events(job_id)
                    monitoring_log['events_log'] = events
                    
                    # Save job details if successful
                    if job_details['status'] == 'succeeded':
                        self._save_successful_model_info(job_details)
                    
                    logging.info(f"Job monitoring complete: {job_details['status']}")
                    break
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logging.error(f"Error during monitoring: {e}")
                time.sleep(check_interval)
        
        # Save monitoring log
        self._save_monitoring_log(monitoring_log)
        return monitoring_log
    
    def _save_successful_model_info(self, job_details: Dict):
        """Save information about successfully trained models."""
        if job_details['fine_tuned_model']:
            model_info = {
                'model_id': job_details['fine_tuned_model'],
                'job_id': job_details['id'],
                'base_model': job_details['model'],
                'created_at': job_details['created_at'],
                'finished_at': job_details['finished_at'],
                'training_file': job_details['training_file'],
                'trained_tokens': job_details['trained_tokens'],
                'hyperparameters': job_details['hyperparameters'],
                'session_id': self.session_id,
                'saved_at': datetime.now().isoformat()
            }
            
            model_file = os.path.join(MODELS_DIR, f"model_{job_details['fine_tuned_model'].replace(':', '_')}.json")
            
            with open(model_file, 'w', encoding='utf-8') as f:
                json.dump(model_info, f, indent=2, ensure_ascii=False)
            
            logging.info(f"✅ Model info saved: {model_file}")
    
    def _save_monitoring_log(self, monitoring_log: Dict):
        """Save monitoring log for audit purposes."""
        log_file = os.path.join(AUDIT_DIR, f"monitoring_log_{monitoring_log['job_id']}_{self.session_id}.json")
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(monitoring_log, f, indent=2, ensure_ascii=False)
        
        logging.info(f"📋 Monitoring log saved: {log_file}")
    
    def test_fine_tuned_model(self, model_id: str, test_prompts: List[str]) -> Dict:
        """Test a fine-tuned model with sample prompts."""
        logging.info(f"Testing model: {model_id}")
        
        test_results = {
            'model_id': model_id,
            'test_timestamp': datetime.now().isoformat(),
            'session_id': self.session_id,
            'test_cases': []
        }
        
        for i, prompt in enumerate(test_prompts):
            try:
                logging.info(f"Testing prompt {i+1}/{len(test_prompts)}")
                
                response = self.client.chat.completions.create(
                    model=model_id,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.7
                )
                
                test_case = {
                    'prompt': prompt,
                    'response': response.choices[0].message.content,
                    'usage': {
                        'prompt_tokens': response.usage.prompt_tokens,
                        'completion_tokens': response.usage.completion_tokens,
                        'total_tokens': response.usage.total_tokens
                    },
                    'model': response.model,
                    'success': True
                }
                
            except Exception as e:
                test_case = {
                    'prompt': prompt,
                    'error': str(e),
                    'success': False
                }
                logging.error(f"Test failed for prompt: {e}")
            
            test_results['test_cases'].append(test_case)
        
        # Save test results
        test_file = os.path.join(MODELS_DIR, f"test_results_{model_id.replace(':', '_')}.json")
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_results, f, indent=2, ensure_ascii=False)
        
        logging.info(f"🧪 Test results saved: {test_file}")
        return test_results
    
    def generate_compliance_report(self, job_ids: List[str]) -> Dict:
        """Generate compliance report for multiple jobs."""
        logging.info("Generating compliance report...")
        
        report = {
            'report_id': f"compliance_{self.session_id}",
            'generated_at': datetime.now().isoformat(),
            'session_id': self.session_id,
            'jobs_analyzed': len(job_ids),
            'jobs': [],
            'summary': {
                'successful_jobs': 0,
                'failed_jobs': 0,
                'total_trained_tokens': 0,
                'total_training_time': 0
            }
        }
        
        for job_id in job_ids:
            job_details = self.get_job_details(job_id)
            if job_details:
                job_report = {
                    'job_id': job_id,
                    'status': job_details['status'],
                    'model': job_details['model'],
                    'fine_tuned_model': job_details['fine_tuned_model'],
                    'created_at': job_details['created_at'],
                    'finished_at': job_details['finished_at'],
                    'trained_tokens': job_details['trained_tokens'] or 0,
                    'training_duration': None
                }
                
                # Calculate training duration
                if job_details['created_at'] and job_details['finished_at']:
                    duration = job_details['finished_at'] - job_details['created_at']
                    job_report['training_duration'] = duration
                    report['summary']['total_training_time'] += duration
                
                # Update summary
                if job_details['status'] == 'succeeded':
                    report['summary']['successful_jobs'] += 1
                elif job_details['status'] == 'failed':
                    report['summary']['failed_jobs'] += 1
                
                report['summary']['total_trained_tokens'] += job_details['trained_tokens'] or 0
                report['jobs'].append(job_report)
        
        # Save compliance report
        report_file = os.path.join(AUDIT_DIR, f"compliance_report_{self.session_id}.json")
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logging.info(f"📊 Compliance report saved: {report_file}")
        return report

# %%
def main():
    """Main function with CLI interface."""
    parser = argparse.ArgumentParser(description="Fine-tuning job monitor")
    parser.add_argument('--job-id', help='Monitor specific job ID')
    parser.add_argument('--list-jobs', action='store_true', help='List recent jobs')
    parser.add_argument('--test-model', help='Test specific model ID')
    parser.add_argument('--compliance-report', nargs='+', help='Generate compliance report for job IDs')
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    organization = os.getenv('OPENAI_ORGANIZATION')
    
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        return
    
    if not OPENAI_AVAILABLE:
        print("❌ OpenAI library not installed")
        return
    
    monitor = FineTuningMonitor(api_key, organization)
    
    if args.list_jobs:
        jobs = monitor.list_fine_tuning_jobs()
        print(f"\n📋 Recent Fine-Tuning Jobs:")
        for job in jobs:
            status_emoji = "✅" if job['status'] == 'succeeded' else "❌" if job['status'] == 'failed' else "⏳"
            print(f"  {status_emoji} {job['id']} - {job['status']} - {job['model']}")
    
    elif args.job_id:
        monitor.monitor_job_progress(args.job_id)
    
    elif args.test_model:
        test_prompts = [
            "Quelles sont les informations principales du médicament CIS 60002283?",
            "Quelle est la composition du médicament ANASTROZOLE ACCORD 1 mg?",
            "Sous quelle forme se présente le médicament TEMERITDUO?"
        ]
        monitor.test_fine_tuned_model(args.test_model, test_prompts)
    
    elif args.compliance_report:
        monitor.generate_compliance_report(args.compliance_report)
    
    else:
        print("Use --help for available options")

# %%
if __name__ == "__main__":
    if len(os.sys.argv) == 1:
        # Interactive mode
        print("🔍 Fine-Tuning Monitor")
        print("=" * 40)
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("❌ OPENAI_API_KEY environment variable not set")
            exit(1)
        
        if not OPENAI_AVAILABLE:
            print("❌ OpenAI library not installed")
            exit(1)
        
        monitor = FineTuningMonitor(api_key)
        
        # List recent jobs
        jobs = monitor.list_fine_tuning_jobs(10)
        if jobs:
            print(f"\n📋 Recent Fine-Tuning Jobs:")
            for i, job in enumerate(jobs):
                status_emoji = "✅" if job['status'] == 'succeeded' else "❌" if job['status'] == 'failed' else "⏳"
                print(f"  {i+1}. {status_emoji} {job['id']} - {job['status']} - {job['model']}")
            
            print(f"\n🚀 To monitor a job: python {__file__} --job-id JOB_ID")
            print(f"🧪 To test a model: python {__file__} --test-model MODEL_ID")
        else:
            print("No fine-tuning jobs found")
    else:
        main()
