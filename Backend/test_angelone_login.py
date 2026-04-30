import pyotp
from SmartApi import SmartConnect

API_KEY = "qem5ag3W"
CLIENT_ID = "A1420760"
PASSWORD = "1986"
TOTP_SECRET = "7DFMHZE3BDRCIHMLFT4N3QVCPU"

def main():
    try:
        smart = SmartConnect(api_key=API_KEY)

        totp = pyotp.TOTP(TOTP_SECRET).now()
        print("Generated TOTP:", totp)

        session = smart.generateSession(CLIENT_ID, PASSWORD, totp)

        if not session:
            print("Login failed")
            return

        data = session.get("data", {})

        access_token = data.get("jwtToken")
        refresh_token = data.get("refreshToken")
        feed_token = smart.getfeedToken()

        print("\n===== RESULT =====")
        print("Access token:", bool(access_token))
        print("Refresh token:", bool(refresh_token))
        print("Feed token:", bool(feed_token))

        if access_token and refresh_token and feed_token:
            print("\nSUCCESS: Angel One login working")
        else:
            print("\nFAIL: Token missing")

    except Exception as e:
        print("ERROR:", str(e))

if __name__ == "__main__":
    main()