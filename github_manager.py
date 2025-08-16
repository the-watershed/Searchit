
"""
github_manager.py: Simple CLI/GUI tool to upload, update, and branch your project on GitHub.
Requires: git, requests, PyQt5 (for GUI)
Usage: Run and follow prompts to authenticate, create repo, push, pull, and branch.
"""
import os
import subprocess
import sys
import requests
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QFileDialog, QMessageBox, QDialog, QFormLayout

GITHUB_API = "https://api.github.com"

import json
CONFIG_FILE = os.path.join(os.path.dirname(__file__), "github_manager_config.json")

class SettingsDialog(QDialog):
    def __init__(self, parent, token, username, email):
        super().__init__(parent)
        self.setWindowTitle("GitHub Settings")
        self.setModal(True)
        layout = QFormLayout()
        self.token_input = QLineEdit(token)
        self.username_input = QLineEdit(username)
        self.email_input = QLineEdit(email)
        layout.addRow("GitHub Token:", self.token_input)
        layout.addRow("Git Username:", self.username_input)
        layout.addRow("Git Email:", self.email_input)
        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)
        self.setLayout(layout)

    def get_values(self):
        return (
            self.token_input.text().strip(),
            self.username_input.text().strip(),
            self.email_input.text().strip(),
        )
class GitHubManager(QWidget):

    def ensure_git_identity(self):
        # Check if user.name and user.email are set, prompt if not, and set them
        name = email = None
        try:
            name = subprocess.check_output([self.git_path, "config", "--get", "user.name"], encoding="utf-8").strip()
        except Exception:
            pass
        try:
            email = subprocess.check_output([self.git_path, "config", "--get", "user.email"], encoding="utf-8").strip()
        except Exception:
            pass
        if not name:
            from PyQt5.QtWidgets import QInputDialog
            name, ok = QInputDialog.getText(self, "Git User Name", "Enter your name for git commits:")
            if ok and name:
                subprocess.run([self.git_path, "config", "--global", "user.name", name])
        if not email:
            from PyQt5.QtWidgets import QInputDialog
            email, ok = QInputDialog.getText(self, "Git User Email", "Enter your email for git commits:")
            if ok and email:
                subprocess.run([self.git_path, "config", "--global", "user.email", email])

    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Project Uploader/Manager")
        self.setGeometry(200, 200, 500, 300)
        # Find git.exe via Windows registry, fallback to config
        self.git_path = None
        config_git = None
        config_file = os.path.join(os.path.dirname(__file__), "github_manager_config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r") as f:
                    data = json.load(f)
                    config_git = data.get("git_path")
            except Exception:
                pass
        if config_git and os.path.exists(config_git):
            self.git_path = config_git
        else:
            try:
                import winreg
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\GitForWindows") as key:
                    install_path, _ = winreg.QueryValueEx(key, "InstallPath")
                    candidate = os.path.join(install_path, "cmd", "git.exe")
                    if os.path.exists(candidate):
                        self.git_path = candidate
            except Exception:
                pass
        if not self.git_path:
            QMessageBox.critical(self, "Git Not Found", "Git is not installed or not found in the registry. Please install Git for Windows from https://git-scm.com/download/win and restart this program.")
            self.setDisabled(True)
            return
        self.init_ui()
        self.load_config()
        # Auto-detect GitHub username if not set
        if not self.repo_input.text().strip():
            try:
                username = subprocess.check_output([self.git_path, "config", "--get", "user.name"], encoding="utf-8").strip()
                if username:
                    self.repo_input.setText(f"{username}/")
            except Exception:
                pass

    def init_ui(self):
        from PyQt5.QtWidgets import QTextEdit
        layout = QVBoxLayout()
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("Enter your GitHub Personal Access Token")
        layout.addWidget(QLabel("GitHub Token:"))
        layout.addWidget(self.token_input)
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("username/repo (leave blank to create new)")
        layout.addWidget(QLabel("Repository (owner/repo):"))
        layout.addWidget(self.repo_input)
        self.create_btn = QPushButton("Create New Repo on GitHub")
        self.create_btn.clicked.connect(self.create_repo)
        layout.addWidget(self.create_btn)
        self.push_btn = QPushButton("Push Local Project to GitHub")
        self.push_btn.clicked.connect(self.push_repo)
        layout.addWidget(self.push_btn)
        self.branch_input = QLineEdit()
        self.branch_input.setPlaceholderText("branch-name")
        layout.addWidget(QLabel("Branch Name (for new branch):"))
        layout.addWidget(self.branch_input)
        self.branch_btn = QPushButton("Create & Switch Branch")
        self.branch_btn.clicked.connect(self.create_branch)
        layout.addWidget(self.branch_btn)
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.open_settings)
        layout.addWidget(self.settings_btn)
        # Log window at the bottom
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(120)
        layout.addWidget(QLabel("Log:"))
        layout.addWidget(self.log_box)
        self.setLayout(layout)

    def open_settings(self):
        # Get current values
        token = self.token_input.text().strip()
        # Try to get git username/email from config or git
        try:
            username = subprocess.check_output([self.git_path, "config", "--get", "user.name"], encoding="utf-8").strip()
        except Exception:
            username = ""
        try:
            email = subprocess.check_output([self.git_path, "config", "--get", "user.email"], encoding="utf-8").strip()
        except Exception:
            email = ""
        dlg = SettingsDialog(self, token, username, email)
        if dlg.exec_():
            new_token, new_username, new_email = dlg.get_values()
            self.token_input.setText(new_token)
            # Save to git config if changed
            if new_username:
                subprocess.run([self.git_path, "config", "--global", "user.name", new_username])
            if new_email:
                subprocess.run([self.git_path, "config", "--global", "user.email", new_email])
            self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    self.token_input.setText(data.get("token", ""))
                    self.repo_input.setText(data.get("repo", ""))
            except Exception:
                pass
        # Always save config after loading to persist any new changes
        self.save_config()

    def save_config(self):
        data = {
            "token": self.token_input.text().strip(),
            "repo": self.repo_input.text().strip(),
            "git_path": self.git_path or ""
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(data, f)

    def log(self, msg):
        self.log_box.append(msg)

    def create_repo(self):
        token = self.token_input.text().strip()
        repo = self.repo_input.text().strip()
        if not token:
            QMessageBox.warning(self, "Error", "GitHub token required.")
            return
        if repo:
            QMessageBox.information(self, "Info", "Repo already exists. Use push to update.")
            self.save_config()
            return
        # Create new repo
        name = os.path.basename(os.getcwd())
        url = f"{GITHUB_API}/user/repos"
        payload = {"name": name}
        headers = {"Authorization": f"token {token}"}
        self.log(f"[POST] {url}\nPayload: {payload}\nHeaders: {{'Authorization': 'token ...'}}")
        resp = requests.post(url, json=payload, headers=headers)
        self.log(f"[RESPONSE] {resp.status_code} {resp.text}")
        if resp.status_code == 201:
            QMessageBox.information(self, "Success", f"Created repo: {name}")
            self.repo_input.setText(f"{resp.json()['owner']['login']}/{name}")
            self.save_config()
        else:
            QMessageBox.warning(self, "Error", f"Failed to create repo: {resp.text}")
            self.save_config()

    def run_git(self, args, log_prefix="[GIT]"):
        """
        Run a git command, log both stdout and stderr, and return (stdout, stderr, returncode).
        """
        self.log(f"{log_prefix} {' '.join(args)}")
        try:
            result = subprocess.run([self.git_path] + args, capture_output=True, text=True)
            if result.stdout:
                self.log(f"[stdout] {result.stdout.strip()}")
            if result.stderr:
                self.log(f"[stderr] {result.stderr.strip()}")
            if result.returncode != 0:
                self.log(f"[error] Command failed with code {result.returncode}")
            return result.stdout, result.stderr, result.returncode
        except Exception as e:
            self.log(f"[exception] {e}")
            return "", str(e), 1

    def push_repo(self):
        self.ensure_git_identity()
        repo = self.repo_input.text().strip()
        token = self.token_input.text().strip()
        if not repo or not token:
            self.log("[error] Repo and token required.")
            QMessageBox.warning(self, "Error", "Repo and token required.")
            self.save_config()
            return
        # Remove any trailing slashes and .git from repo input
        # Remove any trailing .git, /, or .git/ from repo input
        repo_url = repo.strip()
        while repo_url.endswith('/') or repo_url.endswith('.git'):
            if repo_url.endswith('/'):
                repo_url = repo_url[:-1]
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]
        url = f"https://{token}:x-oauth-basic@github.com/{repo_url}"
        # Initialize repo if needed
        if not os.path.exists(".git"):
            self.run_git(["init"])
            self.run_git(["add", "."])
            self.run_git(["commit", "-m", "Initial commit"])
            self.run_git(["branch", "-M", "main"])
            # Check if remote already exists
            out, err, code = self.run_git(["remote"], log_prefix="[GIT-CHK]")
            if "origin" not in out:
                self.run_git(["remote", "add", "origin", url])
            else:
                self.log("[info] Remote 'origin' already exists, skipping add.")
        else:
            self.run_git(["add", "."])
            # Only commit if there are staged changes
            out, err, code = self.run_git(["diff", "--cached", "--name-only"], log_prefix="[GIT-CHK]")
            if out.strip():
                self.run_git(["commit", "-m", "Update"])
            else:
                self.log("[info] No changes to commit.")
        # Push and log all output
        out, err, code = self.run_git(["push", "-u", "origin", "main"])
        if code == 0:
            self.log("[success] Pushed to GitHub.")
            QMessageBox.information(self, "Success", "Pushed to GitHub.")
        else:
            self.log("[error] Push failed. See log above.")
            QMessageBox.warning(self, "Error", "Push failed. See log for details.")
        self.save_config()

    def create_branch(self):
        self.ensure_git_identity()
        branch = self.branch_input.text().strip()
        if not branch:
            QMessageBox.warning(self, "Error", "Branch name required.")
            self.save_config()
            return
        self.log(f"[GIT] git checkout -b {branch}")
        self.log(subprocess.run([self.git_path, "checkout", "-b", branch], capture_output=True, text=True).stdout)
        self.save_config()
        QMessageBox.information(self, "Success", f"Switched to branch: {branch}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = GitHubManager()
    win.show()
    sys.exit(app.exec_())
