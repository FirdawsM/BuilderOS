from flask import Flask
import builderos

app = Flask(__name__)

@app.route("/")
def home():
    projects = builderos.load_registry()

    rows = ""
    for p in projects:
        status = builderos.get_git_status(p["path"])
        rows += f"""
        <tr>
            <td>{p['name']}</td>
            <td>{p.get('status', 'unknown')}</td>
            <td>{status.get('branch', '-')}</td>
            <td>{status.get('modified_files', 0)}</td>
            <td>{status.get('untracked_files', 0)}</td>
            <td>{'Clean' if status.get('clean') else 'Changes pending'}</td>
        </tr>
        """

    return f"""
    <html>
    <head><title>BuilderOS</title></head>
    <body>
        <h1>BuilderOS</h1>
        <table border="1" cellpadding="8">
            <tr>
                <th>Project</th><th>Status</th><th>Branch</th>
                <th>Modified</th><th>Untracked</th><th>Working Tree</th>
            </tr>
            {rows}
        </table>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(debug=True, port=5000)