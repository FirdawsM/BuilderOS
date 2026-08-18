
from flask import Flask, render_template, request, redirect, url_for, jsonify
import builderos

app = Flask(__name__)

@app.route("/")
def home():
    projects = builderos.get_all_projects_status()
    token_status = builderos.verify_github_token()
    return render_template(
        "index.html", 
        projects=projects, 
        token_status=token_status
    )

@app.route("/api/projects")
def api_projects():
    return jsonify(builderos.get_all_projects_status())

@app.route("/api/project/create", methods=["POST"])
def api_create_project():
    data = request.json
    name = data.get("name")
    path = data.get("path")
    
    if not name or not path:
        return jsonify({"error": "Name and path are required"}), 400
        
    result = builderos.create_local_project(name, path)
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result)

@app.route("/api/project/<project_name>/github", methods=["POST"])
def api_connect_github(project_name):
    data = request.json
    remote_url = data.get("remote_url")
    
    if not remote_url:
        return jsonify({"error": "Remote URL is required"}), 400
        
    result = builderos.set_github_remote(project_name, remote_url)
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify(result)

@app.route("/api/github/token", methods=["POST"])
def api_save_token():
    data = request.json
    token = data.get("token")
    
    if not token:
        return jsonify({"error": "Token is required"}), 400
        
    result = builderos.save_github_token(token)
    if "error" in result:
        return jsonify(result), 400
        
    return jsonify({
        "success": True, 
        "status": builderos.verify_github_token()
    })

@app.route("/api/github/verify")
def api_verify_token():
    return jsonify(builderos.verify_github_token())

@app.route("/commit/<project_name>", methods=["POST"])
def commit(project_name):
    message = request.form.get("message", "Update via BuilderOS")
    projects = builderos.load_registry()
    project = next((p for p in projects if p["name"] == project_name), None)
    
    if project:
        builderos.commit_project(project["path"], message)
        
    return redirect(url_for("home"))

@app.route("/push/<project_name>", methods=["POST"])
def push(project_name):
    projects = builderos.load_registry()
    project = next((p for p in projects if p["name"] == project_name), None)
    
    if project:
        builderos.push_project(project["path"])
        
    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True, port=5008)