q@echo off
echo Empaquetando la aplicacion del dashboard...
pyinstaller --noconfirm --console --add-data "../assets;assets" --name AdmisionTech "bridge.py"
echo.
echo Proceso completado. El ejecutable se encuentra en la carpeta 'dist'.
pause