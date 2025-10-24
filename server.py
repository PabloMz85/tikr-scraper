from flask import Flask, request, send_file, jsonify
from tikr.scraper import TIKR  # importa tu clase principal
from tikr.DBUtils import create_database, is_user_approved, add_approved_user, block_user

import os
import shutil
import tempfile
import sys
from dotenv import load_dotenv
import traceback

# Load environment variables from .env (supports spaces around '=' and quoted values)
load_dotenv(dotenv_path=".env")

defaults = {
    "TIKR_TEST_MODE": 0,
    "TIKR_EDIT_FILE": 1,
    "TIKR_EXPORT_FORMAT": "db",
    "TIKR_EXPORT_YEARS": "10",
}

for key, default in defaults.items():
    os.environ.setdefault(key, default)

REQUIRED_ENV_VARS = [
    "TIKR_ACCOUNT_USERNAME",
    "TIKR_ACCOUNT_PASSWORD",
    "TIKR_TEST_MODE",
    "TIKR_EDIT_FILE",
    "TIKR_EXPORT_FORMAT",
    "TIKR_EXPORT_YEARS",
]

missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    print(f"❌ Error: faltan variables de entorno requeridas: {', '.join(missing)}")
    sys.exit(1)


app = Flask(__name__)
test_mode = int(os.environ.get('TIKR_TEST_MODE'))
production_mode = int(os.environ.get('TIKR_PRODUCTION_MODE'))
edit_file = int(os.environ.get('TIKR_EDIT_FILE'))

create_database()

@app.route("/v0.1/getAssetExcel", methods=["POST"])
def scrape():
    # Support JSON and form data for POST; fallback to query args for backward compatibility
    data = request.get_json(silent=True) or {}
    ticker = (data.get("asset") or request.form.get("asset") or request.args.get("asset"))
    token = (data.get("token") or request.form.get("token") or request.args.get("token"))
    user_number = (data.get("user_number") or request.form.get("user_number") or request.args.get("user_number"))

    if not ticker:
        return jsonify({
            "error": "Se requiere 'asset'."
        }), 400

    # In production mode, require a token explicitly to avoid 500 on invalid/empty token
    if production_mode == 1 and not token:
        return jsonify({
            "error": "Se requiere 'token'."
        }), 400

    # In production mode, require a user_number representing the approved user
    if production_mode == 1 and not user_number:
        return jsonify({
            "error": "Se requiere 'user_number'."
        }), 400

    # Validate approved user
    if production_mode == 1 and not is_user_approved(user_number):
        return jsonify({"error": "Usuario no autorizado"}), 403

    try:
         # Crear un archivo temporal para guardar el Excel
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_file_path = tmp.name

        # Ejecutar tu scraper (ajustá según cómo se llame tu método principal)
        scraper = TIKR(test_mode, production_mode)
        scraper.set_token(token)
        
        if test_mode == 0:
            tid, cid = scraper.find_company_info(ticker)
        else:
            tid, cid = 2590360, 24937  # Apple Inc.
    
        if not (tid and cid):
            return jsonify({"error": "No se encontró la compañía"}), 404
        
        scraper.get_financials(ticker, tid, cid)
        exported_files = scraper.export(ticker)
        if not exported_files:
            return jsonify({"error": "No se exportaron archivos"}), 500
        
        # Identificar la industria para saber que plantilla usar
        industry = scraper.get_industry(tid, cid)
        print(f'Industria identificada: {industry}')
        plantilla = 'IDC'
        # Seleccionar plantilla según industria
        if ('Financial' in industry) or ('Bank' in industry) or ('Capital Markets' in industry) or ('Finance' in industry) or ('Insurance' in industry) or ('Mortgage' in industry):
            plantilla = 'Financiera'
            print(f'Usando plantilla de industria financiera debido a: {industry}')
        elif ('REITs' in industry):
            plantilla = 'REITs'
            print(f'Usando plantilla de industria REITs debido a: {industry}')
        
        print('Editar el archivo de Excel')

        # Copiar plantilla a archivo temporal
        shutil.copy(f"plantillas/Plantilla_TIKR_{plantilla}.xlsx", temp_file_path)
        scraper.edit_excel_file(temp_file_path, tid, cid, plantilla)

        # Enviar el archivo como descarga
        return send_file(temp_file_path, as_attachment=True, download_name=f"Plantilla_TIKR_{ticker}.xlsx")

    except RuntimeError as e:
        # Commonly raised for invalid/expired token in production_mode
        traceback.print_exc()
        return jsonify({"error": f"Token inválido o expirado: {str(e)}"}), 401
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/v0.1/createApprovedUser", methods=["POST"])
def createApprovedUser():
    # Support JSON and form data for POST; fallback to query args for backward compatibility
    data = request.get_json(silent=True) or {}
    user_number = (data.get("user_number") or request.form.get("user_number") or request.args.get("user_number"))
    if not user_number:
        return jsonify({
            "error": "Se requiere 'user_number' en el cuerpo de la solicitud POST (JSON o form), por ejemplo: {\"user_number\": \"10001\"}"
        }), 400

    try:
        add_approved_user(user_number)
        return jsonify({"message": f"Usuario {user_number} creado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500

@app.route("/v0.1/blockUser", methods=["POST"])
def blockUser():
    # Support JSON and form data for POST; fallback to query args for backward compatibility
    data = request.get_json(silent=True) or {}
    user_number = (data.get("user_number") or request.form.get("user_number") or request.args.get("user_number"))
    if not user_number:
        return jsonify({
            "error": "Se requiere 'user_number' en el cuerpo de la solicitud POST (JSON o form), por ejemplo: {\"user_number\": \"10001\"}"
        }), 400

    try:
        block_user(user_number)
        return jsonify({"message": f"Usuario {user_number} bloqueado exitosamente."}), 200
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    print(f"✅ Servidor Flask iniciado en http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
