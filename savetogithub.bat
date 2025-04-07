@echo off
git rm -r --cached .
git add .
git commit -m "Update proyek %date%"
git push origin main