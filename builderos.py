import json
import re
import os
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

REGISTRY_FILE = Path(__file__).parent / "projects.json"
ENV_FILE = Path(__file__).parent / ".env"


def load_registry():
    if REGISTRY_FILE.exists():
        with open(REGISTRY_FILE, "r") as f:
            return json.load(f)
    return []


def save_registry(projects):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(projects, f, indent=2)


def get_all_projects_status():
    """Fetches enriched status for all projects, sorted with PENDING/ERROR first."""
    projects = load_registry()
    enriched_projects = []
    
    for p in projects:
        status_info = get_git_status(p["path"])
        last_commit = get_last_commit(p["path"])
        
        # Determine UI status
        if status_info.get("error"):
            ui_status = "ERROR"
        elif status_info.get("clean"):
            ui_status = "CLEAN"
        else:
            ui_status = "PENDING"
            
        enriched_projects.append({
            "name": p["name"],
            "path": p["path"],
            "github_url": p.get("github_url", ""),
            "registry_status": p.get("status", "in progress"),
            "ui_status": ui_status,
            "branch": status_info.get("branch", "unknown"),
            "ahead": status_info.get("ahead", 0),
            "behind": status_info.get("behind", 0),
            "modified_files": status_info.get("modified_files", 0),
            "untracked_files": status_info.get("untracked_files", 0),
            "clean": status_info.get("clean", False),
            "last_commit": last_commit,
            "error": status_info.get("error")
        })
    
    # Sort: PENDING and ERROR first, then CLEAN
    def sort_key(proj):
        if proj["ui_status"] in ["PENDING", "ERROR"]:
            return 0
        return 1
        
    enriched_projects.sort(key=sort_key)
    return enriched_projects


def create_local_project(name, path):
    """Creates a local directory, initializes git, and adds to registry."""
    abs_path = str(Path(path).resolve())
    
    # Create directory if it doesn't exist
    Path(abs_path).mkdir(parents=True, exist_ok=True)
    
    # Initialize git repo
    init_result = subprocess.run(
        ["git", "init"],
        cwd=abs_path,
        capture_output=True,
        text=True
    )
    
    if init_result.returncode != 0:
        return {"error": f"git init failed: {init_result.stderr.strip()}"}
    
    # Add to registry
    add_project(name, abs_path, github_url=None, status="in progress")
    
    return {"success": True, "path": abs_path}


def set_github_remote(name, remote_url):
    """Links an existing local project to a GitHub repository."""
    projects = load_registry()
    target_project = next((p for p in projects if p["name"] == name), None)
            
    if not target_project:
        return {"error": f"Project '{name}' not found."}
        
    # Try to add remote
    result = subprocess.run(
        ["git", "remote", "add", "origin", remote_url],
        cwd=target_project["path"],
        capture_output=True,
        text=True
    )
    
    # If remote already exists, update it
    if result.returncode != 0 and "already exists" in result.stderr:
        result = subprocess.run(
            ["git", "remote", "set-url", "origin", remote_url],
            cwd=target_project["path"],
            capture_output=True,
            text=True
        )
        
    if result.returncode != 0:
        return {"error": f"Failed to set remote: {result.stderr.strip()}"}
        
    # Update registry
    for p in projects:
        if p["name"] == name:
            p["github_url"] = remote_url
            break
    save_registry(projects)
    
    return {"success": True, "github_url": remote_url}


def verify_github_token(token=None):
    """Actually tests the token against the GitHub API."""
    if token is None:
        token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return {"connected": False, "error": "No token provided"}
    
    try:
        response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            timeout=5
        )
        if response.status_code == 200:
            user = response.json()
            return {"connected": True, "username": user.get("login"), "suffix": token[-4:]}
        else:
            return {"connected": False, "error": f"HTTP {response.status_code}"}
    except Exception as e:
        return {"connected": False, "error": str(e)}



def select_project(projects):
    if not projects:
        print("No projects tracked yet.")
        return None

    print("\nTracked projects:")
    for i, p in enumerate(projects, 1):
        print(f"  {i}. {p['name']} [{p.get('status', 'unknown')}]")

    choice = input("Select a project number (or 'a' for all): ").strip().lower()

    if choice == "a":
        return projects

    try:
        index = int(choice) - 1
        if 0 <= index < len(projects):
            return [projects[index]]
    except ValueError:
        pass

    print("Invalid selection.")
    return None


def project_menu(project):
    while True:
        status = get_git_status(project["path"])
        print(f"\n{project['name']} [{project.get('status', 'unknown')}]: {status}")
        review_and_commit(project)

        again = input(f"\n[{project['name']}] (r)efresh, (q)uit to main menu: ").strip().lower()
        if again == "q":
            break


def add_project(name, path, github_url=None, status="in progress"):
    projects = load_registry()
    projects.append({
        "name": name,
        "path": str(Path(path).resolve()),
        "github_url": github_url,
        "status": status
    })
    save_registry(projects)
    print(f"Added project: {name}")


def remove_project(name):
    projects = load_registry()
    filtered = [p for p in projects if p["name"] != name]

    if len(filtered) == len(projects):
        print(f"No project named '{name}' found in registry.")
        return

    save_registry(filtered)
    print(f"Removed '{name}' from registry (local files untouched).")


def set_status(name, status):
    valid = ["not started", "in progress", "done"]
    if status not in valid:
        print(f"Status must be one of: {valid}")
        return

    projects = load_registry()
    for p in projects:
        if p["name"] == name:
            p["status"] = status
            save_registry(projects)
            print(f"{name} marked as: {status}")
            return

    print(f"No project named '{name}' found.")


def parse_branch_info(branch_line):
    no_commits_match = re.search(r"No commits yet on (\S+)", branch_line)
    if no_commits_match:
        return {"branch": no_commits_match.group(1), "ahead": 0, "behind": 0}

    branch_match = re.search(r"## (\S+?)(\.\.\.|$)", branch_line)
    branch_name = branch_match.group(1) if branch_match else "unknown"

    ahead_match = re.search(r"ahead (\d+)", branch_line)
    behind_match = re.search(r"behind (\d+)", branch_line)

    ahead = int(ahead_match.group(1)) if ahead_match else 0
    behind = int(behind_match.group(1)) if behind_match else 0

    return {"branch": branch_name, "ahead": ahead, "behind": behind}


def get_git_status(path):
    result = subprocess.run(
        ["git", "status", "--porcelain", "--branch"],
        cwd=path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    lines = result.stdout.strip().split("\n")
    branch_line = lines[0] if lines else ""
    file_lines = lines[1:] if len(lines) > 1 else []

    modified = sum(1 for line in file_lines if line.startswith(" M") or line.startswith("M "))
    untracked = sum(1 for line in file_lines if line.startswith("??"))
    branch_info = parse_branch_info(branch_line)

    return {
        "branch": branch_info["branch"],
        "ahead": branch_info["ahead"],
        "behind": branch_info["behind"],
        "modified_files": modified,
        "untracked_files": untracked,
        "clean": len(file_lines) == 0
    }


def get_last_commit(path):
    # Safety check: ensure it's actually a git repo
    if not (Path(path) / ".git").exists():
        return "Not a git repository"
        
    result = subprocess.run(
        ["git", "log", "-1", "--pretty=%s"],
        cwd=path,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return "No commits yet"
    message = result.stdout.strip()
    return message if message else "No commits yet"


def get_github_token_status():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return {"connected": False}
    suffix = token[-4:] if len(token) >= 4 else token
    return {"connected": True, "suffix": suffix}


def save_github_token(token):
    token = token.strip()
    if not token:
        return {"error": "Token cannot be empty."}

    lines = []
    found = False
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                if line.startswith("GITHUB_TOKEN="):
                    lines.append(f"GITHUB_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)
    if not found:
        lines.append(f"GITHUB_TOKEN={token}\n")

    with open(ENV_FILE, "w") as f:
        f.writelines(lines)

    os.environ["GITHUB_TOKEN"] = token
    return {"success": True}


def commit_project(path, message):
    add_result = subprocess.run(
        ["git", "add", "."],
        cwd=path,
        capture_output=True,
        text=True
    )

    if add_result.returncode != 0:
        return {"error": f"git add failed: {add_result.stderr.strip()}"}

    commit_result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=path,
        capture_output=True,
        text=True
    )

    if commit_result.returncode != 0:
        return {"error": f"git commit failed: {commit_result.stderr.strip()}"}

    return {"success": True, "output": commit_result.stdout.strip()}


def push_project(path):
    result = subprocess.run(
        ["git", "push"],
        cwd=path,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        if "no upstream branch" in result.stderr or "does not have a commit checked out" in result.stderr:
            branch_result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=path,
                capture_output=True,
                text=True
            )
            branch_name = branch_result.stdout.strip() or "main"

            retry_result = subprocess.run(
                ["git", "push", "--set-upstream", "origin", branch_name],
                cwd=path,
                capture_output=True,
                text=True
            )

            if retry_result.returncode != 0:
                return {"error": retry_result.stderr.strip()}
            return {"success": True, "output": retry_result.stdout.strip() or retry_result.stderr.strip()}

        return {"error": result.stderr.strip()}

    return {"success": True, "output": result.stdout.strip() or result.stderr.strip()}


def review_and_commit(project):
    status = get_git_status(project["path"])

    if status.get("clean"):
        print(f"{project['name']}: nothing to commit, working tree clean.")
        return

    print(f"\n{project['name']} has changes:")
    print(f"  Modified files: {status['modified_files']}")
    print(f"  Untracked files: {status['untracked_files']}")

    confirm = input(f"Commit these changes for {project['name']}? (y/n): ").strip().lower()
    if confirm != "y":
        print("Skipped.")
        return

    message = input("Commit message: ").strip()
    if not message:
        message = "Update via BuilderOS"

    result = commit_project(project["path"], message)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print(f"Committed: {message}")

    push_confirm = input(f"Push {project['name']} to GitHub now? (y/n): ").strip().lower()
    if push_confirm == "y":
        push_result = push_project(project["path"])
        if "error" in push_result:
            print(f"Push error: {push_result['error']}")
        else:
            print("Pushed to GitHub.")


def create_github_repo(name, private=True, description=""):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return {"error": "GITHUB_TOKEN not set."}

    try:
        response = requests.post(
            "https://api.github.com/user/repos",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json"
            },
            json={"name": name, "private": private, "description": description},
            timeout=15
        )
    except requests.exceptions.ConnectionError:
        return {"error": "No internet connection — couldn't reach GitHub."}
    except requests.exceptions.Timeout:
        return {"error": "GitHub API timed out — try again."}

    if response.status_code == 201:
        data = response.json()
        return {"success": True, "clone_url": data["clone_url"], "html_url": data["html_url"]}

    if response.status_code == 422:
        errors = response.json().get("errors", [])
        if any(e.get("message", "").startswith("name already exists") for e in errors):
            return {
                "error": "duplicate_name",
                "message": f"A repo named '{name}' already exists on GitHub. Choose a different name."
            }

    return {
        "error": "api_error",
        "message": f"{response.status_code}: {response.json().get('message', 'Unknown error')}"
    }


def clone_repo(clone_url, local_path):
    try:
        result = subprocess.run(
            ["git", "clone", clone_url, local_path],
            capture_output=True,
            text=True,
            timeout=60
        )
    except subprocess.TimeoutExpired:
        return {"error": "Clone timed out — check your internet connection."}
    except Exception as e:
        return {"error": f"Unexpected error during clone: {e}"}

    if result.returncode != 0:
        return {"error": result.stderr.strip()}

    return {"success": True}


def new_project_flow():
    name = input("New project name: ").strip()
    description = input("Description (optional): ").strip()

    result = create_github_repo(name, private=True, description=description)
    if "error" in result:
        print(f"Error creating repo: {result.get('message', result['error'])}")
        return

    print(f"Created on GitHub: {result['html_url']}")
    local_path = input(f"Local folder path to clone into (e.g. /home/firdos/{name}): ").strip()

    clone_result = clone_repo(result["clone_url"], local_path)
    if "error" in clone_result:
        print(f"Clone failed: {clone_result['error']}")
        print(f"Note: the GitHub repo was still created at {result['html_url']} — you may want to clone it manually.")
        return

    print(f"Cloned to {local_path}")
    add_project(name, local_path, result["html_url"])


if __name__ == "__main__":
    action = input("BuilderOS — (s)tatus check, (n)ew project, (r)emove, or (u)pdate status? ").strip().lower()

    if action == "n":
        new_project_flow()
    elif action == "r":
        name = input("Project name to remove: ").strip()
        remove_project(name)
    elif action == "u":
        name = input("Project name: ").strip()
        status = input("New status (not started / in progress / done): ").strip().lower()
        set_status(name, status)
    else:
        projects = load_registry()
        selected = select_project(projects)
        if selected:
            if len(selected) == 1:
                project_menu(selected[0])
            else:
                for project in selected:
                    status = get_git_status(project["path"])
                    print(f"{project['name']} [{project.get('status', 'unknown')}]: {status}")
                    review_and_commit(project)