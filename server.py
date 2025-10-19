from flask import Flask, request, send_file, jsonify
from tikr.scraper import TIKR  # importa tu clase principal
from tikr.DBUtils import create_database

import os
import shutil
import tempfile
import sys

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
edit_file = int(os.environ.get('TIKR_EDIT_FILE'))

create_database()

@app.route("/get", methods=["GET"])
def scrape():
    ticker = request.args.get("asset")

    if not ticker:
        return jsonify({"error": "Asset is required, e.g. /get?asset=AAPL"}), 400

    try:
         # Crear un archivo temporal para guardar el Excel
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            temp_file_path = tmp.name

        # Copiar plantilla a archivo temporal
        shutil.copy("Plantilla_TIKR.xlsx", temp_file_path)

        # Ejecutar tu scraper (ajustá según cómo se llame tu método principal)
        scraper = TIKR(test_mode)

        if test_mode == 0:
            tid, cid = scraper.find_company_info(ticker)
        else:
            tid, cid = 2590360, 24937  # Apple Inc.
    
        if not (tid and cid):
            return jsonify({"error": "Could not find company"}), 404
        
        scraper.get_financials(ticker, tid, cid)
        exported_files = scraper.export(ticker)
        if not exported_files:
            return jsonify({"error": "No files exported"}), 500
        
        scraper.edit_excel_file(temp_file_path, tid, cid)

        # Enviar el archivo como descarga
        return send_file(temp_file_path, as_attachment=True, download_name=f"Plantilla_TIKR_{ticker}.xlsx")

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5555))
    print(f"✅ Servidor Flask iniciado en http://0.0.0.0:{port}")
    app.run(host="0.0.0.0", port=port, debug=False)
