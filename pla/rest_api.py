from flask import Flask, request, jsonify
from .scenario_loader import load_scenario, ScenarioFormatError
from .prob import InferenceEngine

app = Flask(__name__)

# The currently loaded scenario (kb + queries + context sets)
scenario = None

@app.route('/load', methods=['POST'])
def load_scenario_endpoint():
    global scenario
    data = request.json
    config_path = data.get("config_path")
    context_set = str(data.get("context_number", "1"))  # Default to set "1"
    if not config_path:
        return jsonify({"error": "config_path is required"}), 400

    try:
        loaded = load_scenario(config_path)
        loaded.activate(context_set)
    except (FileNotFoundError, ScenarioFormatError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    scenario = loaded
    return jsonify({
        "message": "Scenario loaded successfully",
        "context_set": scenario.active_set,
        "active_variables": scenario.active_variables,
    }), 200

@app.route('/query', methods=['POST'])
def query_endpoint():
    if scenario is None:
        return jsonify({"error": "No scenario loaded"}), 400

    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "query is required"}), 400

    engine = InferenceEngine(scenario.kb)
    prob, explanation = engine.query(query)
    return jsonify({
        "query": query,
        "probability": prob,
        "explanation": explanation
    }), 200

if __name__ == '__main__':
    app.run(debug=True)
