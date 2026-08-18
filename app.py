from flask import Flask, render_template, request, redirect, url_for
import builderos

app = Flask(__name__)

def get_project_data():
    projects = builderos.load_registry()
    project_data = []
    for p in projects:
        status = builderos.get_git_status(p["path"])
        project_data.append({
            "name": p["name"],
            "status": p.get("status", "unknown"),
            "branch": status.get("branch", "-"),
            "modified_files": status.get("modified_files", 0),
            "untracked_files": status.get("untracked_files", 0),
            "ahead": status.get("ahead", 0),
            "clean": status.get("clean", True),
            "clean_label": "Clean" if status.get("clean") else "Changes pending"
        })
    return project_data


@app.route("/")
def home():
    return render_template("index.html", projects=get_project_data())


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
    app.run(debug=True, port=5000)