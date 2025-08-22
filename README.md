# NeuroSync - Intelligent AI Assistant

![NeuroSync](https://img.shields.io/badge/NeuroSync-AI%2520Assistant-purple)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%2520App-red)
![Python](https://img.shields.io/badge/Python-3.8%252B-blue)

NeuroSync is a sophisticated AI-powered chatbot application that provides intelligent conversations, code assistance, learning roadmaps, and research capabilities with a modern, responsive interface.

---

## 🌟 Features
- **Intelligent Conversations**: AI-powered chat with context awareness  
- **Code Assistance**: Get help with programming questions and code examples  
- **Learning Roadmaps**: Create structured learning paths for any topic  
- **Research Capabilities**: Web search and Wikipedia integration  
- **Beautiful UI**: Modern design with light/dark theme support  
- **User Authentication**: Secure login and registration system  
- **Conversation History**: Save and revisit previous conversations  
- **Export Functionality**: Download chat conversations as text files  

---

## 🛠️ Technology Stack

### Frontend & Framework
- **Streamlit** – Web application framework  
- **HTML5/CSS3** – Custom styling with CSS variables  
- **JavaScript** – Interactive UI elements and animations  
- **Plotly** – Data visualization for chat statistics  

### Backend & AI Integration
- **Python 3.8+** – Backend programming language  
- **LangChain** – AI application framework  
- **AI Tools Integration**:
  - Web search functionality  
  - Wikipedia integration  
  - Mathematical calculator  
  - Knowledge management system  
  - Roadmap generation engine  
  - Code assistance tools  

### Database & Storage
- **SQLite** – Lightweight database for data persistence  
- **Custom ORM** – Database management layer  

### Security & Authentication
- **bcrypt** – Secure password hashing  
- **Session Management** – Token-based authentication  
- **SQLite Database** – Secure user data storage  

---

## 📦 Installation

### Prerequisites
- Python **3.8 or higher**  
- **pip** (Python package manager)  

### Step-by-Step Setup
```bash
# Clone the repository

git clone [(https://github.com/ankit071105/neurosync)]


cd neurosync
python -m venv venv
source venv/bin/activate  

# Install dependencies
pip3 install streamlit langchain langchain-google-genai langchain-community faiss-cpu wikipedia duckduckgo-search python-dotenv bcrypt plotly
pip install -r requirements.txt


# Initialize the database
python main.py
streamlit run main.py
```

```bash
neurosync/
├── main.py                 # Main application entry point
├── auth.py                 # Authentication and user management
├── database.py             # Database operations and models
├── agentic_engine.py       # AI agent and response generation
├── utils.py                # Utility functions and helpers
├── style.css               # Custom CSS styling
├── hover.js                # JavaScript for interactive effects
├── requirements.txt        # Python dependencies
└── README.md               # Project documentation
```

## 🤝 Contributing

We welcome contributions!
- **Fork the repository**
- **Create a feature branch (git checkout -b feature/amazing-feature)**
- **Commit changes (git commit -m 'Add amazing feature')**
- **Push to your branch (git push origin feature/amazing-feature)**
- **Open a Pull Request**





