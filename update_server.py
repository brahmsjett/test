from flask import Flask, request, jsonify
from supabase import create_client, Client
import os
from datetime import datetime
import json

app = Flask(__name__)

# Import configuration
from config import SUPABASE_URL, SUPABASE_KEY

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Current version configuration
CURRENT_VERSION = "1.0.0"
UPDATE_URL = "https://ucarecdn.com/02ca4cac-d237-43f8-ae1f-f9e724b46280/setup.exe"

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})

@app.route('/register', methods=['POST'])
def register_user():
    """Register a new user or update existing user info"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        version = data.get('version', '0.0.0')
        user_info = data.get('user_info', {})
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # Check if user already exists
        existing_user = supabase.table('users').select("*").eq('device_id', device_id).execute()
        
        user_data = {
            'device_id': device_id,
            'current_version': version,
            'last_seen': datetime.now().isoformat(),
            'user_info': json.dumps(user_info),
            'total_launches': 1
        }
        
        if existing_user.data:
            # Update existing user
            user_data['total_launches'] = existing_user.data[0]['total_launches'] + 1
            result = supabase.table('users').update(user_data).eq('device_id', device_id).execute()
        else:
            # Create new user
            user_data['first_seen'] = datetime.now().isoformat()
            result = supabase.table('users').insert(user_data).execute()
        
        # Check if update is needed
        needs_update = version != CURRENT_VERSION
        
        # Log the registration
        log_data = {
            'device_id': device_id,
            'action': 'register',
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'details': json.dumps({'needs_update': needs_update})
        }
        supabase.table('user_logs').insert(log_data).execute()
        
        return jsonify({
            "message": "User registered successfully",
            "needs_update": needs_update,
            "current_version": CURRENT_VERSION,
            "user_version": version
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check-update', methods=['GET'])
def check_update():
    """Check if an update is available for a user"""
    try:
        device_id = request.args.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # Get user's current version
        user = supabase.table('users').select("current_version").eq('device_id', device_id).execute()
        
        if not user.data:
            return jsonify({"error": "User not found"}), 404
        
        user_version = user.data[0]['current_version']
        update_available = user_version != CURRENT_VERSION
        
        # Log the update check
        log_data = {
            'device_id': device_id,
            'action': 'check_update',
            'version': user_version,
            'timestamp': datetime.now().isoformat(),
            'details': json.dumps({
                'update_available': update_available,
                'current_version': CURRENT_VERSION
            })
        }
        supabase.table('user_logs').insert(log_data).execute()
        
        response = {
            "update_available": update_available,
            "current_version": CURRENT_VERSION,
            "user_version": user_version
        }
        
        if update_available:
            response["download_url"] = UPDATE_URL
            response["force_update"] = False  # You can control this
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-downloaded', methods=['POST'])
def update_downloaded():
    """Log when a user downloads an update"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # Log the download
        log_data = {
            'device_id': device_id,
            'action': 'update_downloaded',
            'version': CURRENT_VERSION,
            'timestamp': datetime.now().isoformat(),
            'details': json.dumps({'download_url': UPDATE_URL})
        }
        supabase.table('user_logs').insert(log_data).execute()
        
        return jsonify({"message": "Download logged successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update-installed', methods=['POST'])
def update_installed():
    """Log when a user successfully installs an update"""
    try:
        data = request.get_json()
        device_id = data.get('device_id')
        new_version = data.get('version', CURRENT_VERSION)
        
        if not device_id:
            return jsonify({"error": "device_id is required"}), 400
        
        # Update user's version
        supabase.table('users').update({
            'current_version': new_version,
            'last_updated': datetime.now().isoformat()
        }).eq('device_id', device_id).execute()
        
        # Log the installation
        log_data = {
            'device_id': device_id,
            'action': 'update_installed',
            'version': new_version,
            'timestamp': datetime.now().isoformat(),
            'details': json.dumps({'success': True})
        }
        supabase.table('user_logs').insert(log_data).execute()
        
        return jsonify({"message": "Update installation logged successfully"})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/users', methods=['GET'])
def get_all_users():
    """Admin endpoint to get all users"""
    try:
        users = supabase.table('users').select("*").execute()
        return jsonify({
            "users": users.data,
            "total_users": len(users.data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/logs', methods=['GET'])
def get_user_logs():
    """Admin endpoint to get user activity logs"""
    try:
        limit = request.args.get('limit', 100)
        logs = supabase.table('user_logs').select("*").order('timestamp', desc=True).limit(limit).execute()
        return jsonify({
            "logs": logs.data,
            "total_logs": len(logs.data)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/set-version', methods=['POST'])
def set_current_version():
    """Admin endpoint to update the current version"""
    try:
        data = request.get_json()
        new_version = data.get('version')
        new_url = data.get('download_url')
        
        if not new_version:
            return jsonify({"error": "version is required"}), 400
        
        global CURRENT_VERSION, UPDATE_URL
        CURRENT_VERSION = new_version
        
        if new_url:
            UPDATE_URL = new_url
        
        # Log the version change
        log_data = {
            'device_id': 'admin',
            'action': 'version_updated',
            'version': new_version,
            'timestamp': datetime.now().isoformat(),
            'details': json.dumps({
                'new_version': new_version,
                'new_url': new_url
            })
        }
        supabase.table('user_logs').insert(log_data).execute()
        
        return jsonify({
            "message": "Version updated successfully",
            "current_version": CURRENT_VERSION,
            "download_url": UPDATE_URL
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats', methods=['GET'])
def get_stats():
    """Admin endpoint to get usage statistics"""
    try:
        # Get total users
        users = supabase.table('users').select("device_id", count='exact').execute()
        total_users = users.count
        
        # Get users by version
        version_stats = supabase.table('users').select("current_version").execute()
        version_counts = {}
        for user in version_stats.data:
            version = user['current_version']
            version_counts[version] = version_counts.get(version, 0) + 1
        
        # Get recent activity
        recent_logs = supabase.table('user_logs').select("action").gte('timestamp', datetime.now().replace(hour=0, minute=0, second=0).isoformat()).execute()
        activity_counts = {}
        for log in recent_logs.data:
            action = log['action']
            activity_counts[action] = activity_counts.get(action, 0) + 1
        
        return jsonify({
            "total_users": total_users,
            "current_version": CURRENT_VERSION,
            "version_distribution": version_counts,
            "today_activity": activity_counts,
            "download_url": UPDATE_URL
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
