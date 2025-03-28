#!/usr/bin/env python3
"""
GitHub Copilot Metrics Tracker

This script analyzes git history and VSCode extension data to track
GitHub Copilot usage and generate metrics for the project.
"""
import os
import json
import subprocess
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from pathlib import Path

# Configuration
REPO_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPILOT_VSCODE_DATA_PATH = os.path.expanduser("~/.config/Code/User/globalStorage/github.copilot")
OUTPUT_DIR = os.path.join(REPO_PATH, "copilot_metrics")

def get_git_history():
    """Retrieve git history with author and date information"""
    os.chdir(REPO_PATH)
    result = subprocess.run(
        ["git", "log", "--pretty=format:%h,%an,%ad,%s", "--date=short"],
        capture_output=True, text=True
    )
    commits = []
    for line in result.stdout.split("\n"):
        if line.strip():
            parts = line.split(",", 3)
            if len(parts) == 4:
                commits.append({
                    "hash": parts[0],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3]
                })
    return commits

def analyze_copilot_suggestions():
    """Analyze Copilot suggestion data from VSCode extension"""
    try:
        # This is a simplified example - actual data format may vary
        data_file = os.path.join(COPILOT_VSCODE_DATA_PATH, "suggestions.json")
        if os.path.exists(data_file):
            with open(data_file, "r") as f:
                data = json.load(f)
            return data
        return {"error": "No Copilot data found"}
    except Exception as e:
        return {"error": str(e)}

def analyze_commit_messages():
    """Analyze commit messages for Copilot-related keywords"""
    commits = get_git_history()
    copilot_commits = []
    for commit in commits:
        if any(keyword in commit["message"].lower() for keyword in 
               ["copilot", "ai assist", "ai generated", "ai suggested"]):
            copilot_commits.append(commit)
    return copilot_commits

def calculate_productivity_metrics():
    """Calculate productivity metrics based on git history"""
    commits = get_git_history()
    
    # Group commits by date
    commits_by_date = {}
    for commit in commits:
        date = commit["date"]
        if date not in commits_by_date:
            commits_by_date[date] = []
        commits_by_date[date].append(commit)
    
    # Calculate metrics
    dates = sorted(commits_by_date.keys())
    metrics = []
    for date in dates:
        # For each date, get diff stats for all commits
        lines_changed = 0
        for commit in commits_by_date[date]:
            result = subprocess.run(
                ["git", "show", "--stat", commit["hash"]],
                capture_output=True, text=True
            )
            stat_lines = result.stdout.split("\n")
            for line in stat_lines:
                if " insertions(+), " in line and " deletions(-)" in line:
                    parts = line.split()
                    try:
                        insertions = int(parts[parts.index("insertions(+),")-1])
                        deletions = int(parts[parts.index("deletions(-)")-1])
                        lines_changed += insertions + deletions
                    except (ValueError, IndexError):
                        pass
        
        metrics.append({
            "date": date,
            "commit_count": len(commits_by_date[date]),
            "lines_changed": lines_changed
        })
    
    return metrics

def generate_visualizations(metrics):
    """Generate visualizations of Copilot usage metrics"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Convert to DataFrame for easier visualization
    df = pd.DataFrame(metrics)
    df["date"] = pd.to_datetime(df["date"])
    
    # Plot commit frequency
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 1, 1)
    plt.bar(df["date"], df["commit_count"], color="steelblue")
    plt.title("Commits per Day")
    plt.ylabel("Commit Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    # Plot lines changed
    plt.subplot(2, 1, 2)
    plt.bar(df["date"], df["lines_changed"], color="darkgreen")
    plt.title("Lines Changed per Day")
    plt.ylabel("Lines Count")
    plt.grid(axis="y", linestyle="--", alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "productivity_metrics.png"))
    
    # Save raw data as CSV
    df.to_csv(os.path.join(OUTPUT_DIR, "productivity_data.csv"), index=False)

def main():
    """Main function to run the analysis"""
    print("Analyzing GitHub Copilot usage metrics...")
    
    # Get productivity metrics
    metrics = calculate_productivity_metrics()
    
    # Generate visualizations
    generate_visualizations(metrics)
    
    # Analyze Copilot-related commits
    copilot_commits = analyze_commit_messages()
    with open(os.path.join(OUTPUT_DIR, "copilot_commits.json"), "w") as f:
        json.dump(copilot_commits, f, indent=2)
    
    # Get Copilot suggestion data if available
    suggestion_data = analyze_copilot_suggestions()
    with open(os.path.join(OUTPUT_DIR, "suggestion_analysis.json"), "w") as f:
        json.dump(suggestion_data, f, indent=2)
    
    print(f"Analysis complete. Results saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    main() 