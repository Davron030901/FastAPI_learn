#install
pip install -r requirements.txt 
#React port 5043
npm install axios react-router-dom @types/react-router-dom tailwindcss @heroicons/react
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev
npm run build
npm run preview
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install axios react-router-dom @types/react-router-dom tailwindcss @heroicons/react
npx tailwindcss init -p
npm run dev
#FastAPI run

uvicorn main:app --reload  --port 8000
