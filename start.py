#!/usr/bin/env python3
"""
Startup script for the Multi-Channel AI Customer Service System
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_requirements():
    """Check if all required services are available"""
    print("🔍 Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # Check if Redis is running
    try:
        import redis
        # Check for REDIS_URL environment variable (used on Render and other cloud platforms)
        redis_url = os.getenv('REDIS_URL')
        if redis_url:
            r = redis.from_url(redis_url)
        else:
            # Fallback to localhost for local development
            r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✅ Redis is running")
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        print("Please ensure Redis is running or REDIS_URL is correctly configured.")
        # Don't fail in production environments
        if os.getenv('FLASK_ENV') == 'production':
            print("⚠️ Continuing despite Redis error in production environment")
            return True
        return False
    
    # Check environment variables
    # In production, we'll use different API keys based on what's available
    if os.getenv('FLASK_ENV') != 'production':
        # Only check these in development environment
        optional_apis = ['GOOGLE_API_KEY', 'OPENAI_API_KEY']
        available_apis = [var for var in optional_apis if os.getenv(var)]
        
        if not available_apis:
            print("⚠️ No API keys found. At least one of these is recommended:")
            print(f"   {', '.join(optional_apis)}")
            print("Please copy .env.example to .env and fill in at least one API key.")
            # Don't fail, just warn
    
    # Always required in any environment
    required_vars = ['SECRET_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars and os.getenv('FLASK_ENV') != 'production':
        # In development, show a warning
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please copy .env.example to .env and fill in the required values.")
        return False
    elif missing_vars and os.getenv('FLASK_ENV') == 'production':
        # In production, these should be set by the platform
        print(f"⚠️ Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("These should be configured in your deployment platform.")
        # Continue anyway in production
    
    print("✅ All requirements met")
    return True

def setup_database():
    """Initialize database"""
    print("🗄️  Setting up database...")
    
    try:
        # Initialize migrations if not exists
        if not Path("migrations/versions").exists():
            subprocess.run([sys.executable, "-m", "flask", "db", "init"], check=True)
            print("✅ Database migrations initialized")
        
        # Create migration
        subprocess.run([sys.executable, "-m", "flask", "db", "migrate", "-m", "Initial migration"], check=True)
        
        # Apply migrations
        subprocess.run([sys.executable, "-m", "flask", "db", "upgrade"], check=True)
        print("✅ Database setup complete")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Database setup failed: {e}")
        return False
    
    return True

def start_services():
    """Start all required services"""
    print("🚀 Starting services...")
    
    processes = []
    
    try:
        # Start Celery worker
        print("Starting Celery worker...")
        celery_process = subprocess.Popen([
            sys.executable, "-m", "celery", "-A", "celery_worker.celery", 
            "worker", "--loglevel=info"
        ])
        processes.append(("Celery Worker", celery_process))
        
        # Start Flask application
        print("Starting Flask application...")
        flask_process = subprocess.Popen([
            sys.executable, "run.py"
        ])
        processes.append(("Flask App", flask_process))
        
        print("✅ All services started successfully!")
        print("\n" + "="*50)
        print("🏨 Grand Hotel AI Customer Service System")
        print("="*50)
        print("🌐 Web Interface: http://localhost:5000")
        print("👨‍💼 Admin Dashboard: http://localhost:5000/admin/dashboard")
        print("📞 Voice webhook: http://localhost:5000/voice/webhook")
        print("="*50)
        print("\nPress Ctrl+C to stop all services")
        
        # Wait for processes
        try:
            while True:
                time.sleep(1)
                # Check if any process has died
                for name, process in processes:
                    if process.poll() is not None:
                        print(f"❌ {name} has stopped unexpectedly")
                        raise KeyboardInterrupt
        except KeyboardInterrupt:
            print("\n🛑 Shutting down services...")
            for name, process in processes:
                print(f"Stopping {name}...")
                process.terminate()
                process.wait()
            print("✅ All services stopped")
    
    except Exception as e:
        print(f"❌ Error starting services: {e}")
        # Clean up any started processes
        for name, process in processes:
            try:
                process.terminate()
                process.wait()
            except:
                pass

def main():
    """Main startup function"""
    print("🏨 Grand Hotel AI Customer Service System")
    print("=" * 50)
    
    # Set Flask app environment variable
    os.environ['FLASK_APP'] = 'run.py'
    
    if not check_requirements():
        sys.exit(1)
    
    if not setup_database():
        sys.exit(1)
    
    start_services()

if __name__ == "__main__":
    main()
