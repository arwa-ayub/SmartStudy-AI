# 📚 SmartStudy AI

![Chat UI](assets/chat.png)


An AI-powered study assistant with chat-based learning, smart memory, and dynamic quiz generation.


SmartStudy AI is an interactive AI-powered study assistant designed to help students understand concepts, ask questions, and test their knowledge through dynamically generated quizzes.

Built with a focus on clarity, usability, and real learning, it combines conversational AI with structured assessment to create a smarter study experience.

---

## Features

### AI Chat Assistant
- Ask questions in natural language
- AI explains concepts clearly with examples
- Detects confusion and simplifies responses automatically
- Clean chat interface


### Screenshots
![Chat UI](assets/chat1.png)

![Quiz UI](assets/quiz0.png)

![Quiz UI](assets/quiz.png)

 ![Result](assets/quiz2.png)

### Smart Chat Memory
- Multiple chats supported
- Each chat is automatically named based on your first question
- Rename or delete chats anytime
- Sidebar-based navigation for easy access

### Quiz Generator
- Generate MCQ quizzes on any topic
- Choose number of questions dynamically
- Each question includes:
  - 4 options
  - 1 correct answer
  - Explanation with reasoning

### Chat Management
- Create new chats
- Rename chats
- Delete chats
- Organized conversation flow

---

## Tech Stack

- **Python**
- **Streamlit** (Frontend UI)
- **Groq API (LLaMA 3 models)** (AI engine)
- **dotenv** (environment variable handling)

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/arwa-ayub/SmartStudy-AI.git
cd SmartStudy-AI

### 2.Create virtual environment
python -m venv venv
venv\Scripts\activate

### 3.Install dependenscies
pip install -r requirements.txt

### 4. Setup environment variables
Create a .env file in the root directory:
GROQ_API_KEY=your_api_key_here

⚠️ Do NOT upload this file to GitHub.

### 5.Run the application
streamlit run app.py