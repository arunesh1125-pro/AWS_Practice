import json
import urllib.request
import urllib.parse

# Core Authentication Configurations
CLIENT_ID      = '5afv1vumh632q9bgeqjto3lebn'
REDIRECT_URI   = 'https://localhost:8000/callback'

# CRITICAL: Update this string with your exact custom prefix from Step 1
DOMAIN_PREFIX  = 'ml-platform-auth-arunesh'
COGNITO_DOMAIN = f'https://{DOMAIN_PREFIX}.auth.ap-south-1.amazoncognito.com'

# ── 1. Hosted UI Code Exchange Logic ──────────────────────────────────
def exchange_code_for_tokens(authorization_code, redirect_uri):
    """
    Exchanges an OAuth authorization code for actual JWT tokens.
    """
    token_endpoint = f"{COGNITO_DOMAIN}/oauth2/token"
    print(f"Targeting OAuth2 Token Endpoint: {token_endpoint}")

    data = urllib.parse.urlencode({
        'grant_type':   'authorization_code',
        'code':          authorization_code,
        'client_id':     CLIENT_ID,
        'redirect_uri':  redirect_uri
    }).encode('utf-8')

    request = urllib.request.Request(
        token_endpoint,
        data=data,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST'
    )

    try:
        print(f"Sending POST payload with Authorization Code: {authorization_code[:8]}...")
        with urllib.request.urlopen(request) as response:
            tokens = json.loads(response.read())
        
        print("SUCCESS: JWT Token packet acquired.")
        return {
            'idToken':      tokens['id_token'],
            'accessToken':  tokens['access_token'],
            'refreshToken': tokens['refresh_token']
        }
    except urllib.error.HTTPError as http_err:
        error_body = http_err.read().decode('utf-8')
        print(f"\n[Exchange Failed] Cognito Endpoint Rejected Request:")
        print(f"  * HTTP Code: {http_err.code}")
        print(f"  * Details:   {error_body}")
        return None

# ── Simulation Runner ──────────────────────────────────────────────────
if __name__ == "__main__":
    print("==================================================")
    print(" COGNITO OAUTH2 HOSTED UI TEST BENCH")
    print("==================================================")
    
    hosted_ui_login_url = (
        f"{COGNITO_DOMAIN}/login?client_id={CLIENT_ID}"
        f"&response_type=code&scope=email+openid+profile"
        f"&redirect_uri={urllib.parse.quote_plus(REDIRECT_URI)}"
    )
    
    # Your live code token (single-use, already consumed)
    mock_incoming_code = "04e58ad2-ad61-4a60-8d5a-3bb9a0e7ed6c"
    
    print("Simulating a backend web route intercepting the callback payload...")
    token_packet = exchange_code_for_tokens(mock_incoming_code, REDIRECT_URI)
    
    if token_packet:
        print("\n==================================================")
        print(" EXTRACTED SECURITY TOKEN PACKET DETAILS")
        print("==================================================")
        print(f"  * ID Token (Truncated):     {token_packet['idToken'][:30]}...")
        print(f"  * Access Token (Truncated): {token_packet['accessToken'][:30]}...")
        print(f"  * Refresh Token:            Provided [Valid for session recovery]")
        print("==================================================")

