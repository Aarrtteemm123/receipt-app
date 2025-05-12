# 📦 Requirements

* 🐳 **Docker** v27.3.1
* 🐙 **Docker Compose** v2.29.7
* 🔧 **Git** v2.34.1
* 🛠️ **GNU Make** 4.3

---

# 🚀 Installation Guide

### 1. Create project directory

```bash
mkdir receipt && cd receipt
```

### 2. Clone repositories

```bash
git clone https://github.com/Aarrtteemm123/receipt-app.git
```

### 3. Prepare environment

```bash
cd receipt-app
cp .env-example .env
```

Recommend set ACCESS_TOKEN_EXPIRE_MINUTES=50 for check project

### 4. Initialize project

```bash
make create
```

### 5. Run tests

```bash
make run-tests
```

### 🔐 Access URLs

* **App**: [http://localhost:8000/healthcheck](http://localhost:8000/healthcheck)
* **Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Docs 2**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

# 🐳 Docker Services Overview

| 🚢 **Service** | 🌐 **Host** | 📍 **Port** | 📝 **Description**        |
|----------------| ----------- | ----------- |---------------------------|
| `app`          | localhost   | `8000`      | Main application.         |
| `redis`        | localhost   | `6379`      | Redis instance for app.   |
| `postgres`     | localhost   | `5432`      | PostgreSQL database.      |
| `pgadmin`      | localhost   | `8080`      | PostgreSQL GUI interface. |
