# import requests
# from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
# from django.urls import reverse

# # Constants (You can keep these in settings.py for better management)
# CLIENT_ID = 'your_client_id'  # Replace with your Upstox Client ID
# CLIENT_SECRET = 'your_api_secret'  # Replace with your Upstox API Secret
# REDIRECT_URI = 'https://yourdomain.com/callback'  # Make sure it matches the registered redirect URI
AUTHORIZATION_URL = 'https://login.upstox.com/login/v2/oauth/authorize'
# TOKEN_URL = 'https://api.upstox.com/v2/login/authorization/token'

# def get_upstox_auth_url():
#     """
#     Generates the Upstox authorization URL where the user will authenticate.
#     """
#     auth_url = f"{AUTHORIZATION_URL}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}"
#     return auth_url

# def get_access_token(auth_code):
#     """
#     Exchanges the authorization code for an access token.
#     """
#     data = {
#         'client_id': CLIENT_ID,
#         'client_secret': CLIENT_SECRET,
#         'redirect_uri': REDIRECT_URI,
#         'code': auth_code,
#         'grant_type': 'authorization_code'
#     }
    
#     response = requests.post(TOKEN_URL, data=data)
    
#     if response.status_code == 200:
#         token_data = response.json()
#         return token_data['access_token']
#     else:
#         raise Exception(f"Error getting access token: {response.text}")

# def place_order(access_token, order_data):
#     """
#     Places an order using Upstox API with the provided access token.
#     """
#     order_url = 'https://api.upstox.com/v2/orders'
#     headers = {'Authorization': f'Bearer {access_token}'}
    
#     response = requests.post(order_url, headers=headers, json=order_data)
    
#     if response.status_code == 200:
#         return response.json()
#     else:
#         raise Exception(f"Error placing order: {response.text}")

# def order_view(request):
#     """
#     Redirect user to Upstox for authentication, and then retrieve the code.
#     """
#     # Step 1: Redirect user to Upstox login
#     auth_url = get_upstox_auth_url()
#     return HttpResponseRedirect(auth_url)

# def callback_view(request):
#     """
#     Handle the callback after Upstox authentication and exchange the code for an access token.
#     """
#     auth_code = request.GET.get('code')
    
#     if auth_code:
#         try:
#             # Step 2: Exchange the authorization code for an access token
#             access_token = get_access_token(auth_code)
            
#             # Step 3: Prepare order data (Replace with actual order details)
#             order_data = {
#                 'symbol': 'RELIANCE',
#                 'quantity': 1,
#                 'order_type': 'LIMIT',
#                 'price': 2200.0,
#                 'product_type': 'DELIVERY',
#                 'side': 'BUY',
#                 'time_in_force': 'DAY',
#             }
            
#             # Step 4: Place an order using the access token
#             order_response = place_order(access_token, order_data)
            
#             # Step 5: Handle response and display confirmation
#             return HttpResponse(f"Order placed successfully: {order_response}")
#         except Exception as e:
#             return HttpResponse(f"Error: {str(e)}")
    
#     return HttpResponse("Error: No authorization code received.")
from django.shortcuts import redirect
from django.http import HttpResponse
import requests

# URL to initiate the OAuth flow
OAUTH_URL = "https://api.upstox.com/v2/login/authorization/dialog"
AUTHORIZATION_URL= 'https://login.upstox.com/login/v2/oauth/authorize'
CLIENT_ID = "674ce251-a2e0-4e00-9e5e-7d49dc51ab82"
REDIRECT_URI = "https://finvachi.com/"  # Updated redirect URI
        
CLIENT_SECRET = "r6hphy99so"  # Add your Upstox client secret

def login(request):
    """Redirect the user to the Upstox login page for authorization."""
    # Prepare query parameters
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
    }
    auth_url = requests.get(OAUTH_URL, params=params) # Redirect the user to the Upstox login page
    print(auth_url.url)
    return redirect(auth_url.url)

def callback(request):
    REDIRECT_URI =  "http://localhost:8000/callback/"
    """Handle the callback from Upstox with the authorization code."""
    # Get the 'code' parameter from the query string
    auth_code = request.GET.get('code')

    if auth_code:
        # Once we have the code, exchange it for the access token
        token_url = "https://api.upstox.com/v2/login/token"
        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": auth_code,
            "grant_type": "authorization_code",
        }

        # Make the POST request to exchange the code for a token
        response = requests.post(token_url, data=data)
        
        if response.status_code == 200:
            # Successfully got the access token
            token_data = response.json()
            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")  # Optionally, store the refresh token for future use

            # You can now use the access token to make authenticated requests to the Upstox API
            return HttpResponse(f"Access Token: {access_token}")
        else:
            return HttpResponse(f"Error: {response.status_code} - {response.text}")

    return HttpResponse("Error: No code found in the URL")
