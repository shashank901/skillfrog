# SkillForge Labs – Project Workspace

This repo hosts the lab projects used by SkillForge. Use Codespaces to edit a lab branch in the browser, then let the lab runner rebuild/redeploy.

## Edit in Codespaces
- Branch naming: each lab run uses `<candidate_id>-<lab_id>`.
- One-click link template (replace IDs):  
  `https://codespaces.new/co-intel-labs/hol-projects/tree/<candidate_id>-<lab_id>`
- Steps:
  1) Open the link above for your branch.
  2) Work in the Codespace (Python 3.11 base; port 8080 forwarded).  
     Install deps in the project folder, e.g. `pip install -r requirements.txt` and `pytest`.
  3) Commit and push to the same branch.
  4) Rerun the lab runner to rebuild/redeploy:  
     `LAB_PORT=8080 scripts/lab_start.sh <candidate_id> <lab_id> <project_path>`

## Notes
- `.devcontainer` config is included for a ready-to-code Codespace.
- Keep commits on your `<candidate>-<lab>` branch; the lab runner will deploy from it.
