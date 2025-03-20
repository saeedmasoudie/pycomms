# PyComms

### **Overview**
**PyComms** is a scalable real-time communication platform built with Django Channels and WebRTC. The application enables users to engage in real-time voice and text interactions, offering rich features like team collaboration, direct communication, and user management.

Whether you're creating teams, managing channels, or diving into a multi-voice session within a single channel, PyComms is designed to facilitate seamless communication experiences with user-friendly features and backend efficiency.

---

### **Features**
#### **Completed Functionalities**
- **User Authentication:**
  - Signup and Signin.
  - Profile settings for personalized user experiences.

- **Channels:**
  - Create and manage channels.
  - Support for multiple simultaneous voice sessions in a single channel.
  - Channels-based chats (real-time).

- **Real-Time Communication:**
  - WebRTC-powered voice communication.
  - Backend powered by Django Channels.
  - Rate-limiting features to handle spam.

#### **In-Progress Functionalities**
- **Teams and Collaboration:**
  - Create and manage teams.
  - Assign and modify team roles.

- **Friends Management:**
  - Add friends.
  - View friend list.
  - Direct calls and chats with friends.

- **User Interaction:**
  - Search for users.
  - Manage user accounts.

- **Channel Ranks:**
  - Role management within channels, including Owner, Admin, and Member functionalities.

---

### **Tech Stack**
- **Backend:** Django with Django Channels for real-time communication.
- **Frontend:** Bootstrap for responsive UI and JavaScript for interactivity.
- **Real-Time Features:** WebRTC for voice communication and Redis for Django Channels layers.
- **Database:** PostgreSQL (or any database of your choice).

---

### **Installation**
```bash
# Clone the repository or download it from Zip
git clone https://github.com/saeedmasoudie/pycomms.git

# Navigate to the project directory
cd pycomms

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
source venv/bin/activate  # Unix/Linux
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### **Usage**
1. Setup your Database (Recomended -> PostgreSQL) - dont use SQLite
2. Change Setting File in Project
3. Navigate to http://localhost:8000.
4. Sign up or log in.
5. Explore the available functionalities, such as creating channels or chatting in real time.
6. Work with channels, chats, and multi-voice sessions.

### **Contributing**
This project is a work in progress, and contributions are welcome! If you'd like to collaborate:
- Fork the repository.
- Create a feature branch (git checkout -b feature-name).
- Commit your changes (git commit -m "Add feature-name").
- Push your branch and create a pull request.

### **Current Status**
PyComms is under active development. While several core features are functional, others are still being implemented. Feel free to explore and contribute!

### **Contact**
For questions or collaboration:
- Name: Saeed or Eric
- Email: SaeedMasoodi@yahoo.com
- Portfolio/Website: [SaeedMasoudie.ir](https://www.saeedmasoudie.ir/)
