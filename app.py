from flask import Flask, request, jsonify
import os
from datetime import datetime
import json
import requests

app = Flask(__name__)

# Supabase configuration - hardcoded for now
SUPABASE_URL = "https://vbwjmeadqwumfrwonkqr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZid2ptZWFkcXd1bWZyd29ua3FyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4MjY5MjMsImV4cCI6MjA2NzQwMjkyM30.g__aZKZyrV-HL3fuS2qzRsJK2OD1dl3DkCWaOe__dVg"

# Current version configuration
CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://ucarecdn.com/02ca4cac-d237-43f8-ae1f-f9e724b46280/setup.exe"

@app.route('/')
def home():
    return jsonify({
        "message": "User Tracking API is running!",
        "version": CURRENT_VERSION,
        "endpoints": [
            "GET /health - Health check",
            "POST /register - Register user",
            "GET /check-update - Check for updates",
            "GET /admin/stats - Get statistics"
        ]
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "version": CURRENT_VERSION
    })

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.get_json() or {}
        device_id = data.get('device_id', 'unknown')
        version = data.get('version', '0.0.0')
        
        # For now, just return success without database
        # TODO: Add Supabase integration
        
        needs_update = version != CURRENT_VERSION
        
        return jsonify({
            "message": "User registered successfully",
            "needs_update": needs_update,
            "current_version": CURRENT_VERSION,
            "user_version": version,
            "device_id": device_id
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check-update', methods=['GET'])
def check_update():
    """Check if an update is available"""
    try:
        device_id = request.args.get('device_id', 'unknown')
        user_version = request.args.get('version', '0.0.0')
        
        update_available = user_version != CURRENT_VERSION
        
        response = {
            "update_available": update_available,
            "current_version": CURRENT_VERSION,
            "user_version": user_version,
            "device_id": device_id
        }
        
        if update_available:
            response["download_url"] = UPDATE_URL
            response["force_update"] = False
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def get_stats():
    """Get basic statistics"""
    try:
        return jsonify({
            "total_users": 0,  # TODO: Get from database
            "current_version": CURRENT_VERSION,
            "download_url": UPDATE_URL,
            "status": "API is working!"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 Starting server on port {port}")
    print(f"📊 Current version: {CURRENT_VERSION}")
    print(f"🔗 Download URL: {UPDATE_URL}")
    app.run(debug=False, host='0.0.0.0', port=port)
