import requests

BASE_URL = "http://127.0.0.1:8000"

def safe_print_json(resp, label):
    print(f"--- {label} ---")
    print("Status:", resp.status_code)
    try:
        print("JSON:", resp.json())
    except Exception:
        print("Contenido no JSON:", resp.text)
    print("\n")

# --- 1️⃣ Registro de usuario ---
register_url = f"{BASE_URL}/api/auth/register/"
register_data = {
    "username": "usuario1",
    "email": "usuario1@gmail.com",
    "password": "1234"
}

resp = requests.post(register_url, json=register_data)
safe_print_json(resp, "Registro")

# --- 2️⃣ Login ---
login_url = f"{BASE_URL}/api/auth/login/"
login_data = {
    "username": "usuario1",
    "password": "1234"
}

resp = requests.post(login_url, json=login_data)
safe_print_json(resp, "Login")

tokens = resp.json()
access_token = tokens.get("access")
refresh_token = tokens.get("refresh")

# --- 3️⃣ Acceso a endpoint protegido ---
protected_url = f"{BASE_URL}/dashboard/prueba/"
headers = {"Authorization": f"Bearer {access_token}"}

resp = requests.get(protected_url, headers=headers)
safe_print_json(resp, "Endpoint protegido")

# --- 4️⃣ Renovar token ---
refresh_url = f"{BASE_URL}/api/auth/token/refresh/"
refresh_data = {"refresh": refresh_token}

resp = requests.post(refresh_url, json=refresh_data)
safe_print_json(resp, "Renovar token")
