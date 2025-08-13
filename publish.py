#!/usr/bin/env python3
# publish.py
import os, subprocess, sys
from generate_article import load_config, generate_one

cfg = load_config()
md_paths = []
for i in range(int(cfg.get("posts_per_run",1))):
    md, img = generate_one(cfg)
    md_paths.append(md)

def run(cmd):
    print("+", " ".join(cmd))
    subprocess.check_call(cmd)

run(["git", "config", "--global", "user.email", "action@github.com"])
run(["git", "config", "--global", "user.name", "github-actions"])
run(["git", "add", "docs"])
run(["git", "commit", "-m", "Auto: add generated post(s)"])
try:
    run(["git", "push"])
except Exception as e:
    print("Push likely failed (maybe no changes).", e)
print("Publish step finished.")
