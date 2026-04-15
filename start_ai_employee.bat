@echo off
echo Starting AI Employee Silver Tier...
cd /d E:\AI_Employee_Silver_Tier
python scripts\orchestrator.py >> logs\orchestrator.log 2>&1
