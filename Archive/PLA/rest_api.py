from flask import Flask, request, jsonify
from scenario_loader import load_scenario
from prob import InferenceEngine

app = Flask(__name__)

# Load the knowledge base and queries
kb, queries = None, None

@app.route('/load', methods=['POST'])
def load_scenario_endpoint():
    global kb, queries
    data = request.json
    config_path = data.get("config_path")
    if not config_path:
        return jsonify({"error": "config_path is required"}), 400

    try:
        kb, queries = load_scenario(config_path)
        return jsonify({"message": "Scenario loaded successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/query', methods=['POST'])
def query_endpoint():
    global kb
    if not kb:
        return jsonify({"error": "No scenario loaded"}), 400

    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "query is required"}), 400

    engine = InferenceEngine(kb)
    prob, explanation = engine.query(query)
    return jsonify({
        "query": query,
        "probability": prob,
        "explanation": explanation
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
