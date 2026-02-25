# eVoting Project

This is a Django-based eVoting system, containerized with Docker and using PostgreSQL as the database. This guide will help you run the project locally.

---

## 🛠 Prerequisites

Before you start, make sure you have installed:

* [Git](https://git-scm.com/downloads)
* [Docker](https://docs.docker.com/get-docker/)
* [Docker Compose](https://docs.docker.com/compose/install/)
* Python 3.11 (only if you want to run outside Docker)

> **Note:** Docker will handle all dependencies inside containers, so Python installation is optional if using Docker.

---

## 📥 Clone the Project

```bash
git clone https://github.com/yourusername/e-voting.git
cd e-voting
```

---

## 🔹 Project Structure

```text
e-voting/
│
├── backend/                 # Django project + apps
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   ├── evoting/             # Django project folder
│   ├── elections/           # Django apps
│   └── .dockerignore
│
├── docker-compose.yml       # Docker Compose configuration
├── .env                     # Environment variables
└── .gitignore
```

---

## 🔹 Environment Variables

Create a `.env` file in the project root with:

```env
POSTGRES_DB=evoting_db
POSTGRES_USER=evoting_user
POSTGRES_PASSWORD=evoting_password
POSTGRES_HOST=db
```

> You can change the values as needed, but make sure they match `settings.py`.

---

## 🐳 Run with Docker Compose

### Step 1 — Build the containers

```bash
docker-compose build
```

### Step 2 — Start the services

```bash
docker-compose up -d
```

* Backend will run at [http://localhost:8000](http://localhost:8000)
* PostgreSQL will run in a separate container

---

## 🔹 Running Django Commands

If you need to run Django commands (migrations, superuser, shell), use:

```bash
docker-compose run backend python manage.py migrate
docker-compose run backend python manage.py createsuperuser
docker-compose run backend python manage.py shell
```

---

## 🔹 Accessing the Admin Panel

* URL: [http://localhost:8000/admin](http://localhost:8000/admin)
* Use the superuser credentials created above

---

## 🔹 Stop Containers

```bash
docker-compose down
```

> This stops all containers but preserves PostgreSQL data in Docker volumes.

---

## 🔹 Notes

* All backend dependencies are handled inside Docker.
* Any code changes in `backend/` will reflect in the container automatically (due to volume mounting).
* Make sure Docker is running before executing any commands.
