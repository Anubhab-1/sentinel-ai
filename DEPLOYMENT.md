# 🚀 Deployment Guide: How to Share Sentinel AI

Since **Sentinel AI** is a dynamic application (it uses Python, a Database, and a Redis background worker), you cannot host it on GitHub Pages (which is only for static HTML sites).

You need a server that runs **Docker**. Here are the two best ways to share it with your friends.

---

## Option 1: The "Quick & Free" Way (ngrok)
**Best for:** Showing friends immediately without setting up a server.
**How it works:** It creates a secure tunnel from the internet directly to your laptop.
**Downside:** The app stops working when you turn off your computer or close the terminal.

### Steps:
1.  **Start your App**:
    Ensure your app is running locally:
    ```powershell
    docker-compose up
    ```

2.  **Download ngrok**:
    - Go to [ngrok.com](https://ngrok.com) and sign up (it's free).
    - Download the Windows version and unzip it.

3.  **Start the Tunnel**:
    Open a *new* terminal window and run:
    ```powershell
    ngrok http 5002
    ```
    *(Note: 5002 is the port Sentinel runs on)*

4.  **Share the Link**:
    ngrok will give you a URL like `https://a1b2-c3d4.ngrok-free.app`.
    Send this link to your friends. They can now access the app running on your laptop!

---

## Option 2: The "Professional" Way (Cloud Hosting)
**Best for:** A permanent link that works 24/7.
**Cost:** Free tiers available, but heavy usage might cost money.
**Platforms:** [Render](https://render.com), [Railway](https://railway.app), or [Fly.io](https://fly.io).

We recommended **Railway** or **Render** because they support `docker-compose` easily.

### Example: Deploying on Railway.app
1.  **Push your code to GitHub** (you already have a repository).
2.  **Sign up** at [railway.app](https://railway.app) using your GitHub account.
3.  Click **"New Project"** -> **"Deploy from GitHub repo"**.
4.  Select your **Sentinel** repository.
5.  Railway will detect the `Dockerfile` or `docker-compose.yml`.
    - **Important**: You need to add a Redis service within Railway.
    - Set your **Environment Variables** in the Railway dashboard (copy them from your `.env` file):
        - `SECRET_KEY`
        - `PERPLEXITY_API_KEY`
        - `API_KEY`
6.  Click **Deploy**. Railway will give you a permanent `https://sentinel-production.up.railway.app` link.

6.  Click **Deploy**. Railway will give you a permanent `https://sentinel-production.up.railway.app` link.

---

## Option 3: Standard Docker Deployment (VPS)
If you have a VPS (DigitalOcean, AWS EC2), use `docker-compose`:

1.  **Clone Repo**:
    ```bash
    git clone https://github.com/Anubhab-1/sentinel-ai.git
    cd sentinel-ai
    ```

2.  **Environment**:
    Create a `.env` file (see `.env.example` or docs).

3.  **Run**:
    ```bash
    docker-compose up -d --build
    ```

## ⚙️ Production Configuration
For production environments, ensure:
- `FLASK_ENV=production`
- `FLASK_DEBUG=false`
- `SECRET_KEY` is a strong random string.
- Using a production WSGI server (Gunicorn is built into our Dockerfile).

---

## Summary
| Method | Difficulty | Cost | Uptime |
| :--- | :--- | :--- | :--- |
| **ngrok** | ⭐ Very Easy | Free | Only while laptop is on |
| **Railway/Render** | ⭐⭐⭐ Medium | Free Tier / $5/mo | 24/7 |
| **VPS (Docker)** | ⭐⭐⭐⭐ Hard | $5/mo+ | 24/7 |

**Recommendation:** Cloud Hosting (Option 2) for long-term usage.
