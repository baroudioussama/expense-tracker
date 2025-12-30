# 💰 Personal Expense Tracker

A full-stack expense tracking application with AI-powered categorization and financial insights.

## 🌟 Features

- ✅ **User Authentication** - Register, login, and password reset
- 💸 **Expense Tracking** - Track expenses with AI auto-categorization
- 💵 **Income Management** - Manage multiple income sources
- 📊 **Dashboard** - Visual charts and financial overview
- 💡 **AI Recommendations** - Personalized financial advice
- 🤖 **Chatbot** - AI assistant for financial queries
- 🐳 **Docker Support** - Fully containerized application

## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Database
- **SQLAlchemy** - ORM
- **Scikit-learn** - ML for expense categorization
- **JWT** - Authentication

### Frontend
- **React** - UI library
- **Recharts** - Data visualization
- **Axios** - API requests
- **React Router** - Navigation

### DevOps
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start with Docker

1. **Clone the repository:**
```bash
git clone https://github.com/baroudioussama/expense-tracker.git
cd expense-tracker
```

2. **Create `.env` file in root:**
```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
POSTGRES_DB=expense_tracker_db
SECRET_KEY=your-secret-key-here
```

3. **Start all services:**
```bash
docker-compose up --build
```

4. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## 💻 Local Development

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm start
```

## 📁 Project Structure
```
expense-tracker/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── category_classifier.py  # ML model
│   │   └── transactions.csv     # Training data
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   └── context/           # React context
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
└── README.md
```

## 🎯 Key Features Explained

### AI-Powered Categorization
The app uses machine learning to automatically categorize expenses based on description and merchant name, trained on 1500+ transactions.

### Financial Recommendations
Get personalized insights based on:
- 50-30-20 budget rule
- Spending trends
- Savings rate
- Category analysis

### Chatbot Assistant
Ask questions like:
- "What's my balance?"
- "Show my expenses"
- "Give me savings tips"

## 🔒 Security

- Password hashing with bcrypt
- JWT token authentication
- Protected API endpoints
- CORS configuration

## 📊 API Endpoints

- `POST /register` - User registration
- `POST /login` - User login
- `GET /expenses` - List expenses
- `POST /expenses` - Create expense
- `GET /recommendations` - Financial insights
- `POST /chat` - Chatbot interaction

For full API documentation, visit: http://localhost:8000/docs

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 👤 Author

Baroudi Oussama - [https://github.com/yourusername](https://github.com/baroudioussama)

## 🙏 Acknowledgments

- FastAPI documentation
- React documentation
- Scikit-learn for ML capabilities
