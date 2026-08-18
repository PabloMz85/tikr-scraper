from flask import Flask, request, send_file, jsonify, json
from tikr.scraper import TIKR
from tikr.utils import scraper_utils
from tikr.DBUtils import list_users, is_user_approved, add_approved_user, block_user, unblock_user, log_user_activity, ensure_schema, ensure_default_admin_user
from token_manager import ensure_valid_token

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
    "TIKR_USERID",
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
user_id = os.environ.get("TIKR_USERID", "")

def get_client_ip():
    # Check X-Forwarded-For first
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()
    # Fallback to the direct TCP peer
    return request.remote_addr


class APIError(Exception):
    """Excepción para errores de API que incluye el código HTTP a devolver."""
    def __init__(self, error, error_number):
        super().__init__(error)
        self.error = error
        self.error_number = error_number


def _find_company(scraper, ticker):
    """Resolve (tid, cid) for a ticker.

    Raises APIError(503) when the search service (Algolia) is unreachable.
    Returns (None, None) when no company matches the ticker.
    """
    if test_mode != 0:
        return 2590360, 24937  # Apple Inc.
    result = scraper.find_company_info(ticker, user_id)
    if result is None:
        raise APIError("Servicio de búsqueda no disponible, inténtalo nuevamente en un momento", 503)
    return result


# =====================================================
# ✅ Common functions
# =====================================================

def _get_common_data(request):
    data = request.get_json(silent=True) or {}
    ticker = data.get("asset") or request.form.get("asset") or request.args.get("asset")
    token = data.get("token") or request.form.get("token") or request.args.get("token")
    # Each source is checked with `is None` (not `or`) so an explicit 0 is not
    # mistaken for a missing parameter and replaced by the default.
    with_actual_year_included = data.get("with_actual_year_included")
    if with_actual_year_included is None:
        with_actual_year_included = request.form.get("with_actual_year_included")
    if with_actual_year_included is None:
        with_actual_year_included = request.args.get("with_actual_year_included")
    user_name = data.get("user_name") or request.form.get("user_name") or request.args.get("user_name")

    # Default to 1 if not provided (wich not includes the actual year), but if provided, must be 0 or 1
    # They need to be switched
    if with_actual_year_included is None:
        with_actual_year_included = 1
    else:
        with_actual_year_included = int(with_actual_year_included)
        with_actual_year_included = 0 if with_actual_year_included == 1 else 1

    if not ticker:
        raise APIError("Se requiere 'asset'.", 400)

    if production_mode == 1:
        if not token:
            raise APIError("Se requiere 'token'.", 400)
        if not user_name:
            raise APIError("Se requiere 'user_name'.", 400)
        if not is_user_approved(user_name):
            raise APIError("Usuario no autorizado", 403)
        if (with_actual_year_included not in [0,1]):
            raise APIError("'with_actual_year_included' debe ser 0 o 1.", 400)
    
    return [user_name, token, ticker, with_actual_year_included]


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
@app.route("/v0.1/health")
def health():
    return {"ok": True}

@app.route("/v0.1/getCompanyInfo", methods=["POST"])
def get_company_info():
    data = request.get_json(silent=True) or {}
    ticker = data.get("asset") or request.form.get("asset") or request.args.get("asset")
    token = data.get("token") or request.form.get("token") or request.args.get("token")

    scraper = TIKR(test_mode, production_mode)
    scraper.set_token(token)

    try:
        tid, cid = _find_company(scraper, ticker)
    except APIError as e:
        traceback.print_exc()
        return jsonify({"error": e.error}), e.error_number

    if not (tid and cid):
        return jsonify({"error": "No se encontró la compañía"}), 404

    return jsonify({"tid": tid, "cid": cid}), 200


@app.route("/v0.1/getLastPrice", methods=["GET"])
def get_last_price():
    ticker = request.args.get("asset")
    token = request.args.get("token")
    if not ticker:
        return jsonify({"error": "Se requiere 'asset'."}), 400

    try:
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)

        tid, cid = _find_company(scraper, ticker)

        if not (tid and cid):
            return jsonify({"error": "No se encontró la compañía"}), 404

        last_quote = scraper_utils.get_last_quote_data(scraper.access_token, scraper.headers, tid, cid, test_mode)
        if not last_quote or not last_quote.get('last'):
            return jsonify({"error": "No se pudo obtener el precio"}), 500

        last_price = last_quote.get('last')[0].get('latestPrice', '')
        if last_price == '':
            return jsonify({"error": "No se pudo obtener el precio"}), 500

        return jsonify({"ticker": ticker, "price": round(float(last_price), 2)}), 200

    except APIError as e:
        traceback.print_exc()
        return jsonify({"error": e.error}), e.error_number
    except RuntimeError as e:
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/getAssetExcel", methods=["POST"])
def get_asset_excel():
    try:
        [user_name, token, ticker, with_actual_year_included] = _get_common_data(request)
    except APIError as e:
        return jsonify({"error": e.error}), e.error_number
    except ConnectionError as e:
        traceback.print_exc()
        return jsonify({"error": "Servicio temporalmente no disponible", "details": str(e)}), 503

    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_file_path = tmp.name

        client_ip = get_client_ip()
        log_user_activity(user_name, client_ip, token)
        
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)

        tid, cid = _find_company(scraper, ticker)

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

    except APIError as e:
        traceback.print_exc()
        return jsonify({"error": e.error}), e.error_number
    except RuntimeError as e:
        traceback.print_exc()
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/getAssetJSON", methods=["POST"])
def get_asset_json():
    try:
        [user_name, token, ticker, with_actual_year_included] = _get_common_data(request)
    except APIError as e:
        return jsonify({"error": e.error}), e.error_number
    except ConnectionError as e:
        traceback.print_exc()
        return jsonify({"error": "Servicio temporalmente no disponible", "details": str(e)}), 503

    try:
        client_ip = get_client_ip()
        log_user_activity(user_name, client_ip, token)
        
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)

        tid, cid = _find_company(scraper, ticker)

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

    except APIError as e:
        traceback.print_exc()
        return jsonify({"error": e.error}), e.error_number
    except RuntimeError as e:
        traceback.print_exc()
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/generateToken", methods=["POST"])
def generateToken():
    try:
        token = ensure_valid_token()
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
    user_name = data.get("user_name") or request.form.get("user_name") or request.args.get("user_name")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403

    if not user_name:
        return jsonify({"error": "Se requiere 'user_name'."}), 400
    try:
        add_approved_user(user_name)
        return jsonify({"message": f"Usuario {user_name} creado exitosamente."}), 200
    except ConnectionError as e:
        # El servidor web no se cae, responde un HTTP 503 elegante
        return {"error": "Servicio temporalmente no disponible", "details": str(e)}, 503
    except Exception as e:
        return {"error": "Error interno del servidor", "details": str(e)}, 500


@app.route("/v0.1/blockUser", methods=["POST"])
def blockUser():
    data = request.get_json(silent=True) or {}
    user_name = data.get("user_name") or request.form.get("user_name") or request.args.get("user_name")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403
    
    if not user_name:
        return jsonify({"error": "Se requiere 'user_name'."}), 400
    try:
        block_user(user_name)
        return jsonify({"message": f"Usuario {user_name} bloqueado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@app.route("/v0.1/unblockUser", methods=["POST"])
def unblockUser():
    data = request.get_json(silent=True) or {}
    user_name = data.get("user_name") or request.form.get("user_name") or request.args.get("user_name")
    super_admin_pass = data.get("super_admin_pass") or request.form.get("super_admin_pass") or request.args.get("super_admin_pass")
    print(super_admin_pass)
    print(os.getenv("SUPER_USER_PASS"))
    if super_admin_pass != os.getenv("SUPER_USER_PASS"):
        return jsonify({"error": "Acceso denegado."}), 403
    
    if not user_name:
        return jsonify({"error": "Se requiere 'user_name'."}), 400
    try:
        unblock_user(user_name)
        return jsonify({"message": f"Usuario {user_name} desbloqueado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


# =====================================================
# ✅ Production entrypoint (Waitress)
# =====================================================
if __name__ == "__main__":
    from waitress import serve
    port = int(os.getenv("PORT", 5050))
    try:
        ensure_schema()
        ensure_default_admin_user()
    except Exception as e:
        print(f"⚠️ No se pudo verificar el esquema de la BD al iniciar: {e}", file=sys.stderr)
    print(f"🚀 Servidor Flask en modo PRODUCCIÓN con Waitress: http://0.0.0.0:{port}")
    serve(app, host="0.0.0.0", port=port)
