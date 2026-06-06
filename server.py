from flask import Flask, request, send_file, jsonify, json
from tikr.scraper import TIKR
from tikr.utils import scraper_utils
from tikr.DBUtils import create_database, list_users, is_user_approved, add_approved_user, block_user, unblock_user, log_user_activity

import os
import shutil
import tempfile
import sys
from dotenv import load_dotenv
import traceback

# =====================================================
# ✅ Load environment variables
# =====================================================
load_dotenv(dotenv_path=".env")

defaults = {
    "TIKR_TEST_MODE": "0",
    "TIKR_EXPORT_YEARS": "10",
    "TIKR_PRODUCTION_MODE": "1",  # fuerza modo productivo
}

for key, default in defaults.items():
    os.environ.setdefault(key, default)

# =====================================================
# ✅ Validate required environment variables
# =====================================================
REQUIRED_ENV_VARS = [
#    "TIKR_ACCOUNT_USERNAME",
#    "TIKR_ACCOUNT_PASSWORD",
    "TIKR_TEST_MODE",
    "TIKR_PRODUCTION_MODE",
    "TIKR_EXPORT_YEARS",
    "TICKER_USERID",
    "SUPER_USER_PASS",
]

missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    print(f"❌ Error: faltan variables de entorno requeridas: {', '.join(missing)}")
    sys.exit(1)

# =====================================================
# ✅ Flask app setup
# =====================================================
app = Flask(__name__)
test_mode = int(os.environ.get("TIKR_TEST_MODE", 0))
production_mode = int(os.environ.get("TIKR_PRODUCTION_MODE", 1))
user_id = os.environ.get("TICKER_USERID", "")

def get_client_ip():
    # Check X-Forwarded-For first
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()
    # Fallback to the direct TCP peer
    return request.remote_addr


create_database()

# =====================================================
# ✅ Common functions
# =====================================================

def _get_common_data(request):
    data = request.get_json(silent=True) or {}
    ticker = data.get("asset") or request.form.get("asset") or request.args.get("asset")
    token = data.get("token") or request.form.get("token") or request.args.get("token")
    with_actual_year_included = data.get("with_actual_year_included") or request.form.get("with_actual_year_included") or request.args.get("with_actual_year_included")
    user_number = data.get("user_number") or request.form.get("user_number") or request.args.get("user_number")

    # Default to 1 if not provided (wich not includes the actual year), but if provided, must be 0 or 1
    # They need to be switched
    if with_actual_year_included is None:
        with_actual_year_included = 1
    else:
        with_actual_year_included = int(with_actual_year_included)
        with_actual_year_included = 0 if with_actual_year_included == 1 else 1

    if not ticker:
        raise {"error": "Se requiere 'asset'.", "error_number": 400}

    if production_mode == 1:
        if not token:
            raise {"error": "Se requiere 'token'.", "error_number": 400}
        if not user_number:
            raise {"error": "Se requiere 'user_number'.", "error_number": 400}
        if not is_user_approved(user_number):
            raise {"error": "Usuario no autorizado", "error_number": 403}
        if (with_actual_year_included not in [0,1]):
            raise {"error": "'with_actual_year_included' debe ser 0 o 1.", "error_number": 400}
    
    return [user_number, token, ticker, with_actual_year_included]


def normalizar_claves_json(objeto: any) -> any:
    """
    Realiza un recorrido recursivo sobre estructuras de datos anidadas
    para garantizar que todas las claves se transformen al tipo 'str'.
    Esta normalización previene excepciones de colisión de tipos
    durante el ordenamiento lexicográfico en la serialización.
    """
    if isinstance(objeto, dict):
        return {str(clave): normalizar_claves_json(valor) for clave, valor in objeto.items()}
    elif isinstance(objeto, list):
        return [normalizar_claves_json(elemento) for elemento in objeto]
    else:
        # Se retorna el valor original para tipos primitivos (int, float, str, booleanos)
        return objeto
    

# =====================================================
# ✅ Routes
# =====================================================

@app.route("/v0.1/getCompanyInfo", methods=["POST"])
def get_company_info():
    data = request.get_json(silent=True) or {}
    ticker = data.get("asset") or request.form.get("asset") or request.args.get("asset")
    token = data.get("token") or request.form.get("token") or request.args.get("token")

    scraper = TIKR(test_mode, production_mode)
    scraper.set_token(token)
    
    if test_mode == 0:
        tid, cid = scraper.find_company_info(ticker, user_id)
    else:
        tid, cid = 2590360, 24937  # Apple Inc.
    
    if not (tid and cid):
        return jsonify({"error": "No se encontró la compañía"}), 404
    
    return jsonify({"tid": tid, "cid": cid}), 200


@app.route("/v0.1/getAssetExcel", methods=["POST"])
def get_asset_excel():
    try:
        [user_number, token, ticker, with_actual_year_included] = _get_common_data(request)
    except e:
        return jsonify({"error": e.error}), e.error_number

    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_file_path = tmp.name

        client_ip = get_client_ip()
        log_user_activity(user_number, client_ip, token)
        
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)

        if test_mode == 0:
            tid, cid = scraper.find_company_info(ticker)
        else:
            tid, cid = 2590360, 24937  # Apple Inc.

        if not (tid and cid):
            return jsonify({"error": "No se encontró la compañía"}), 404

        scraper.get_financials(ticker, tid, cid, with_actual_year_included)
        exported_files = scraper.export(ticker, 'xlsx')
        if not exported_files:
            return jsonify({"error": "No se exportaron archivos"}), 500

        industry = scraper.get_industry(tid, cid)
        print(f"Industria identificada: {industry}")
        plantilla = "IDC"
        if any(word in industry for word in ["Financial", "Bank", "Capital Markets", "Finance", "Insurance", "Mortgage"]):
            plantilla = "Financiera"
            print(f"Usando plantilla financiera: {industry}")
        elif "REITs" in industry:
            plantilla = "REITs"
            print(f"Usando plantilla REITs: {industry}")

        print("Editar el archivo de Excel")
        shutil.copy(f"plantillas/Plantilla_TIKR_{plantilla}.xlsx", temp_file_path)
        scraper.edit_excel_file(temp_file_path, tid, cid, plantilla)

        return send_file(temp_file_path, as_attachment=True, download_name=f"Plantilla_TIKR_{ticker}.xlsx")

    except RuntimeError as e:
        traceback.print_exc()
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/getAssetJSON", methods=["POST"])
def get_asset_json():
    try:
        [user_number, token, ticker, with_actual_year_included] = _get_common_data(request)
    except e:
        return jsonify({"error": e.error}), e.error_number

    try:
        client_ip = get_client_ip()
        log_user_activity(user_number, client_ip, token)
        
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)

        if test_mode == 0:
            tid, cid = scraper.find_company_info(ticker, user_id)
        else:
            tid, cid = 2590360, 24937  # Apple Inc.

        if not (tid and cid):
            return jsonify({"error": "No se encontró la compañía"}), 404

        scraper.get_financials(ticker, tid, cid, with_actual_year_included)
        payload = scraper.export(ticker, 'json')
        if not payload:
            return jsonify({"error": "No se ha podido exportar"}), 500

        payload_normalizado = normalizar_claves_json(payload)
        response = app.response_class(
            response=json.dumps(payload_normalizado),
            status=200,
            mimetype='application/json'
        )
        return response

    except RuntimeError as e:
        traceback.print_exc()
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/generateToken", methods=["POST"])
def generateToken():
    try:
        token = scraper_utils.get_access_token()
        return jsonify({"token": token }), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/listUsers", methods=["POST"])
def listUsers():
    data = request.get_json(silent=True) or {}
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403

    try:
        userList = list_users()
        json_salida = json.dumps(userList, indent=4, ensure_ascii=False)
        return json_salida
    
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/createApprovedUser", methods=["POST"])
def createApprovedUser():
    data = request.get_json(silent=True) or {}
    user_number = data.get("user_number") or request.form.get("user_number") or request.args.get("user_number")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403

    if not user_number:
        return jsonify({"error": "Se requiere 'user_number'."}), 400
    try:
        add_approved_user(user_number)
        return jsonify({"message": f"Usuario {user_number} creado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/blockUser", methods=["POST"])
def blockUser():
    data = request.get_json(silent=True) or {}
    user_number = data.get("user_number") or request.form.get("user_number") or request.args.get("user_number")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403
    
    if not user_number:
        return jsonify({"error": "Se requiere 'user_number'."}), 400
    try:
        block_user(user_number)
        return jsonify({"message": f"Usuario {user_number} bloqueado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/unblockUser", methods=["POST"])
def unblockUser():
    data = request.get_json(silent=True) or {}
    user_number = data.get("user_number") or request.form.get("user_number") or request.args.get("user_number")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403
    
    if not user_number:
        return jsonify({"error": "Se requiere 'user_number'."}), 400
    try:
        unblock_user(user_number)
        return jsonify({"message": f"Usuario {user_number} desbloqueado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# =====================================================
# ✅ Production entrypoint (Waitress)
# =====================================================
if __name__ == "__main__":
    from waitress import serve
    port = int(os.getenv("PORT", 5050))
    print(f"🚀 Servidor Flask en modo PRODUCCIÓN con Waitress: http://0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port)
