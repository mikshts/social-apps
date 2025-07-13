@echo off
echo Starting Redis server...
start redis-server

timeout /t 2 >nul

echo Starting Daphne server...
cd /d "C:\Users\Lenovo\Downloads\second copy of social_book-20250708T152616Z-1-001\second copy of social_book\social_book">
daphne -b 0.0.0.0 -p 8000 social_book.asgi:application

pause
 