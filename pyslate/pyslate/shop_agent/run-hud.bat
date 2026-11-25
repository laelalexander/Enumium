@echo off
rem Full-screen shop-floor board. Add --line laser --title "LASER BAY" for one area.
rem Press F11 in Windows Terminal for full screen. Ctrl+C to quit.
cd /d "%~dp0"
py -3 -m shop_agent hud --config agent.json %*
