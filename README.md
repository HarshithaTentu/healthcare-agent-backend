🏥 Healthcare AI Agent Backend

📌 Project Overview
This project is an AI-powered healthcare assistant backend built using FastAPI. It simulates an intelligent agent capable of answering healthcare queries, performing knowledge retrieval, and routing decisions based on user input.

--------------------------------------------------

🚀 Features
• Chat API for handling user health queries  
• Agent decision routing system  
• Knowledge base search functionality  
• Swagger UI for API testing  
• Modular and scalable backend architecture  

--------------------------------------------------

🛠️ Tech Stack
• Python  
• FastAPI  
• Uvicorn  
• REST APIs  
• Agentic System Design  

--------------------------------------------------

📂 Project Structure

healthcare-agent-backend
│
├── main.py
├── knowledge_base/
├── README.md
├── requirements.txt
└── .gitignore

--------------------------------------------------

⚙️ How To Run Locally

Step 1: Create Virtual Environment
python3 -m venv venv
source venv/bin/activate

Step 2: Install Dependencies
pip install -r requirements.txt

Step 3: Run Backend Server
uvicorn main:app --reload

Step 4: Open Swagger UI
http://127.0.0.1:8000/docs

--------------------------------------------------

🎯 Learning Outcomes
• Built a task-oriented AI agent backend  
• Implemented decision routing architecture  
• Practiced REST API design  
• Implemented backend knowledge retrieval  
• Understood backend and AI integration workflows  

## ⏱️ Voice Pipeline Latency (Sample)

Measured on local machine using offline Whisper + gTTS.

- STT (recording + transcription): ~6–10s
- Backend API call (FastAPI): ~15ms
- TTS (gTTS): ~1.8–2.0s
- End-to-end voice pipeline: ~8–12s

**Observation:**  
Most latency comes from audio processing (STT + TTS).  
The agent backend itself is fast, confirming audio as the primary bottleneck.


--------------------------------------------------

👩‍💻 Author
Harshitha Reddy  
Artificial Intelligence Student  
