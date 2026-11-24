@echo off
rem Starts the Pyslate shop agent with agent.json from this folder. Leave the window open.
cd /d "%~dp0"
py -3 -m shop_agent --config agent.json
pause
