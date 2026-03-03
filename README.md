terminal 1-launch backend
cd autonomous-crisis-command/backend 
source venv/bin/activate
uvicorn main:app --reload --port 8000


terminal 2 -start ngrok 
ngrok http 8000

after that change url then stop backend and restart it

terminal 3 -frontend
cd autonomous-crisis-command/frontend 
npm install
npm run dev