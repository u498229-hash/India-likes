# MINISTER LIKE API - FULLY WORKING
# POWERED BY : @minister_69
# CHANNEL : @minister_6T9

from flask import Flask, request, jsonify
import asyncio
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from google.protobuf.json_format import MessageToJson
import binascii
import aiohttp
import requests
import json
import like_pb2
import like_count_pb2
import uid_generator_pb2
import time
from collections import defaultdict
from datetime import datetime, timezone
import random
import os
import urllib.parse
import jwt
from datetime import timedelta
import ssl
import warnings

# Ignore SSL warnings
warnings.filterwarnings("ignore")

app = Flask(__name__)

# ========== CONFIG ==========
KEY_LIMIT = 90
tracker = defaultdict(lambda: [0, time.time()])
liked_cache = defaultdict(set)
TOKEN_CACHE = {}

# ========== LOAD ACCOUNTS ==========
def load_accounts(server_name):
    try:
        server_files = {
            "IND": "account_ind.txt",
            "BR": "account_br.txt",
            "US": "account_br.txt",
            "SAC": "account_br.txt",
            "NA": "account_br.txt",
            "PK": "account_pk.txt",
            "BD": "account_bd.txt",
            "RU": "account_bd.txt"
        }
        
        filename = server_files.get(server_name, "account_ind.txt")
        print(f"📂 Looking for: {filename}")
        
        if not os.path.exists(filename):
            fallback_files = ["account_ind.txt", "account_br.txt", "account_bd.txt", "account_pk.txt"]
            for f in fallback_files:
                if os.path.exists(f):
                    filename = f
                    print(f"✅ Using fallback: {filename}")
                    break
            else:
                print(f"❌ No account file found!")
                return []
        
        accounts = []
        with open(filename, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if ':' in line:
                    parts = line.split(':', 1)
                    uid = parts[0].strip()
                    password = parts[1].strip()
                    if uid and password and uid.isdigit():
                        accounts.append({"uid": uid, "password": password})
        
        print(f"✅ Loaded {len(accounts)} accounts from {filename}")
        return accounts
    except Exception as e:
        print(f"❌ Error loading accounts: {e}")
        return []

# ========== TOKEN GENERATION ==========
async def generate_jwt_token(uid, password):
    try:
        encoded_password = urllib.parse.quote(password)
        url = f"https://ff-jwt-gen-api.lovable.app/api/public/token?uid={uid}&password={encoded_password}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('jwt_token') or data.get('token')
                return None
    except Exception as e:
        print(f"❌ Token generation error: {e}")
        return None

async def get_valid_token(uid, password):
    if uid in TOKEN_CACHE:
        cached = TOKEN_CACHE[uid]
        remaining = (cached["expires_at"] - datetime.now(timezone.utc)).total_seconds()
        if remaining > 1800:
            return cached["token"]
    
    token = await generate_jwt_token(uid, password)
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        exp = payload.get("exp")
        TOKEN_CACHE[uid] = {
            "token": token,
            "expires_at": datetime.fromtimestamp(exp, tz=timezone.utc)
        }
    except:
        TOKEN_CACHE[uid] = {
            "token": token,
            "expires_at": datetime.now(timezone.utc) + timedelta(hours=24)
        }
    
    return token

# ========== ENCRYPTION ==========
def encrypt_message(plaintext):
    key = b'Yg&tc%DEuh6%Zc^8'
    iv = b'6oyZDr22E3ychjM%'
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_message = pad(plaintext, AES.block_size)
    return binascii.hexlify(cipher.encrypt(padded_message)).decode('utf-8')

def enc(uid):
    message = uid_generator_pb2.uid_generator()
    message.krishna_ = int(uid)
    message.teamXdarks = 1
    return encrypt_message(message.SerializeToString())

# ========== PROTOBUF ==========
def create_protobuf_message(user_id, region):
    message = like_pb2.like()
    message.uid = int(user_id)
    region_map = {
        "IND": "IND", "BD": "BD", "BR": "BR", "PK": "PK",
        "US": "US", "SAC": "SAC", "NA": "NA", "RU": "RU"
    }
    message.region = region_map.get(region, region)
    return message.SerializeToString()

def decode_protobuf(binary):
    try:
        items = like_count_pb2.Info()
        items.ParseFromString(binary)
        return items
    except Exception as e:
        print(f"❌ Decode error: {e}")
        return None

# ========== API REQUESTS ==========
def get_player_info(encrypted_uid, server_name, token):
    """Get player info with proper URL for each server"""
    # Primary endpoints
    endpoints = {
        "IND": "https://client.ind.freefiremobile.com",
        "BR": "https://client.us.freefiremobile.com",
        "US": "https://client.us.freefiremobile.com",
        "SAC": "https://client.us.freefiremobile.com",
        "NA": "https://client.us.freefiremobile.com",
        "PK": "https://client.pk.freefiremobile.com",
        "BD": "https://clientbp.ggpolarbear.com",
        "RU": "https://clientbp.ggpolarbear.com"
    }
    
    # Fallback endpoints
    fallbacks = {
        "PK": ["https://client.us.freefiremobile.com", "https://clientbp.ggpolarbear.com"],
        "IND": ["https://clientbp.ggpolarbear.com"],
        "BD": ["https://client.us.freefiremobile.com"],
        "BR": ["https://clientbp.ggpolarbear.com"]
    }
    
    # Build URL list
    urls_to_try = []
    base = endpoints.get(server_name, "https://clientbp.ggpolarbear.com")
    urls_to_try.append(f"{base}/GetPlayerPersonalShow")
    
    for fallback in fallbacks.get(server_name, []):
        urls_to_try.append(f"{fallback}/GetPlayerPersonalShow")
    
    urls_to_try = list(dict.fromkeys(urls_to_try))
    
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9)',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB54'
    }
    
    edata = bytes.fromhex(encrypted_uid)
    
    for url in urls_to_try:
        try:
            print(f"🔄 Trying player info: {url}")
            response = requests.post(url, data=edata, headers=headers, verify=False, timeout=10)
            if response and response.status_code == 200:
                print(f"✅ Player info success: {url}")
                return decode_protobuf(response.content)
            else:
                print(f"❌ Player info failed: {response.status_code if response else 'No response'}")
        except Exception as e:
            print(f"⚠️ Error: {e}")
            continue
    
    return None

async def send_like(encrypted_uid, token, server_name):
    """Send like with proper URL"""
    # Primary endpoints
    endpoints = {
        "IND": "https://client.ind.freefiremobile.com",
        "BR": "https://client.us.freefiremobile.com",
        "US": "https://client.us.freefiremobile.com",
        "SAC": "https://client.us.freefiremobile.com",
        "NA": "https://client.us.freefiremobile.com",
        "PK": "https://client.pk.freefiremobile.com",
        "BD": "https://clientbp.ggpolarbear.com",
        "RU": "https://clientbp.ggpolarbear.com"
    }
    
    fallbacks = {
        "PK": ["https://client.us.freefiremobile.com", "https://clientbp.ggpolarbear.com"],
        "IND": ["https://clientbp.ggpolarbear.com"],
        "BD": ["https://client.us.freefiremobile.com"],
        "BR": ["https://clientbp.ggpolarbear.com"]
    }
    
    # Build URL list
    urls_to_try = []
    base = endpoints.get(server_name, "https://clientbp.ggpolarbear.com")
    urls_to_try.append(f"{base}/LikeProfile")
    
    for fallback in fallbacks.get(server_name, []):
        urls_to_try.append(f"{fallback}/LikeProfile")
    
    urls_to_try = list(dict.fromkeys(urls_to_try))
    
    headers = {
        'User-Agent': 'Dalvik/2.1.0 (Linux; U; Android 9)',
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-GA': 'v1 1',
        'ReleaseVersion': 'OB54'
    }
    
    edata = bytes.fromhex(encrypted_uid)
    
    for url in urls_to_try:
        try:
            print(f"🔄 Sending like to: {url}")
            async with aiohttp.ClientSession() as session:
                async with session.post(url, data=edata, headers=headers, timeout=10, ssl=False) as response:
                    status = response.status
                    print(f"📡 Like response: {status}")
                    if status == 200:
                        return status
        except Exception as e:
            print(f"⚠️ Like error: {e}")
            continue
    
    return 500

# ========== MAIN LOGIC ==========
async def process_account(target_uid, encrypted_uid, account, semaphore, server_name):
    async with semaphore:
        try:
            print(f"🔄 Processing account: {account['uid']}")
            token = await get_valid_token(account['uid'], account['password'])
            if not token:
                print(f"❌ No token for {account['uid']}")
                return 500, account['uid']
            
            status = await send_like(encrypted_uid, token, server_name)
            
            if status == 200:
                liked_cache[target_uid].add(account['uid'])
                print(f"✅ {account['uid']} liked successfully")
                return status, account['uid']
            else:
                print(f"❌ {account['uid']} failed with status {status}")
                return status, account['uid']
        except Exception as e:
            print(f"❌ Error processing {account['uid']}: {e}")
            return 500, account['uid']

async def send_all_likes(target_uid, server_name):
    protobuf_message = create_protobuf_message(target_uid, server_name)
    encrypted_uid = encrypt_message(protobuf_message)
    
    accounts = load_accounts(server_name)
    if not accounts:
        return {'success': 0, 'failed': 0, 'total': 0, 'already_liked': 0}
    
    already_liked = liked_cache.get(target_uid, set())
    fresh_accounts = [acc for acc in accounts if acc['uid'] not in already_liked]
    
    print(f"📊 Total: {len(accounts)} | Fresh: {len(fresh_accounts)} | Already: {len(already_liked)}")
    
    if not fresh_accounts:
        return {
            'success': 0, 
            'failed': 0, 
            'total': len(accounts),
            'already_liked': len(already_liked),
            'fresh_used': 0
        }
    
    random.shuffle(fresh_accounts)
    semaphore = asyncio.Semaphore(20)
    tasks = []
    for acc in fresh_accounts[:1000]:
        tasks.append(process_account(target_uid, encrypted_uid, acc, semaphore, server_name))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    successful = 0
    failed = 0
    for r in results:
        if isinstance(r, tuple):
            status, uid = r
            if status == 200:
                successful += 1
            else:
                failed += 1
    
    print(f"📊 Results: Success: {successful}, Failed: {failed}")
    
    return {
        'success': successful,
        'failed': failed,
        'total': len(accounts),
        'already_liked': len(already_liked),
        'fresh_used': len(fresh_accounts[:1000])
    }

# ========== FLASK ROUTES ==========
@app.route('/like', methods=['GET'])
def handle_requests():
    uid = request.args.get("uid")
    server_name = request.args.get("server_name", "").upper()
    key = request.args.get("key")
    client_ip = request.remote_addr

    if key != "JMLB":
        return jsonify({"error": "Invalid API key 🔑"}), 403

    if not uid or not server_name:
        return jsonify({"error": "UID and server_name required"}), 400
    
    valid_servers = ["IND", "BR", "US", "SAC", "NA", "BD", "RU", "PK"]
    if server_name not in valid_servers:
        return jsonify({"error": f"Invalid server. Use: {valid_servers}"}), 400

    print(f"🚀 Request: UID={uid}, Server={server_name}, IP={client_ip}")

    accounts = load_accounts(server_name)
    if not accounts:
        return jsonify({"error": f"No accounts for {server_name}"}), 500
    
    check_token = None
    for account in accounts[:5]:
        try:
            check_token = asyncio.run(get_valid_token(account['uid'], account['password']))
            if check_token:
                print(f"✅ Token generated with UID: {account['uid']}")
                break
        except Exception as e:
            print(f"❌ Token error: {e}")
            continue
    
    if not check_token:
        return jsonify({"error": "Token generation failed"}), 500
    
    encrypted_uid = enc(uid)
    
    # Get player info before
    before = get_player_info(encrypted_uid, server_name, check_token)
    if before is None:
        return jsonify({"error": "Could not get player info", "status": 0}), 200

    try:
        before_data = json.loads(MessageToJson(before))
        before_like = int(before_data['AccountInfo'].get('Likes', 0))
        print(f"📊 Before likes: {before_like}")
    except Exception as e:
        print(f"❌ Parse error: {e}")
        return jsonify({"error": "Data parsing failed"}), 200

    # Send likes
    result = asyncio.run(send_all_likes(uid, server_name))

    # Get player info after
    after = get_player_info(encrypted_uid, server_name, check_token)
    if after is None:
        return jsonify({"error": "Could not verify likes after"}), 200

    try:
        after_data = json.loads(MessageToJson(after))
        after_like = int(after_data['AccountInfo']['Likes'])
        player_name = str(after_data['AccountInfo']['PlayerNickname'])
        
        like_given = after_like - before_like
        status = 1 if like_given > 0 else 2
        
        print(f"📊 After likes: {after_like} | Given: {like_given} | Status: {status}")

        return jsonify({
            "LikesGivenByAPI": like_given,
            "LikesafterCommand": after_like,
            "LikesbeforeCommand": before_like,
            "PlayerNickname": player_name,
            "UID": uid,
            "status": status,
            "server": server_name,
            "accounts_used": result['fresh_used'],
            "successful_likes": result['success']
        })
    except Exception as e:
        print(f"❌ Final error: {e}")
        return jsonify({"error": str(e), "status": 0}), 500

@app.route('/reset-cache', methods=['GET'])
def reset_cache():
    key = request.args.get("key")
    if key != "JMLB":
        return jsonify({"error": "Invalid key"}), 403
    global liked_cache, TOKEN_CACHE, tracker
    liked_cache.clear()
    TOKEN_CACHE.clear()
    tracker.clear()
    return jsonify({"message": "All caches cleared", "credit": "@minister_69"})

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "working",
        "servers": ["IND", "BR", "US", "SAC", "NA", "BD", "RU", "PK"],
        "version": "2.0",
        "credit": "@minister_69"
    })

def get_today_midnight_timestamp():
    now = datetime.now()
    midnight = datetime(now.year, now.month, now.day)
    return midnight.timestamp()

# ========== MAIN ==========
if __name__ == '__main__':
    print("=" * 60)
    print("🚀 MINISTER LIKE API v2.0 - COMPLETE WORKING")
    print("=" * 60)
    print("📁 Account files needed:")
    print("   - account_ind.txt (IND server)")
    print("   - account_pk.txt (PK server)")
    print("   - account_bd.txt (BD/RU server)")
    print("   - account_br.txt (BR/US/SAC/NA servers)")
    print("=" * 60)
    print("🔧 Features:")
    print("   ✅ Smart endpoint selection")
    print("   ✅ Multiple fallback URLs")
    print("   ✅ Detailed logging")
    print("   ✅ Cache management")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5001, debug=False, use_reloader=False)