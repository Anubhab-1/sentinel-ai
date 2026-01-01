# 🐘 Free Database Setup Guide (PostgreSQL)

You can get a **Permanent, Free Database** in 5 minutes. This will stop your users/history from being deleted when the server restarts.

## Option A: Render (Best if you host on Render)
Render gives you a free database for 30 days (good for testing) or a paid one. For a **forever free** option, use **Neon** (Option B).

### Option B: Neon.tech (Recommended - Forever Free)
Neon provides a generous free tier that never sleeps.

1.  **Go to [Neon.tech](https://neon.tech)** and Sign Up (Log in with GitHub).
2.  Click **"New Project"**.
3.  Name it `sentinel-db` and click **Create Project**.
4.  Copy the **Connection String** shown on the dashboard.
    *   It looks like: `postgres://neondb_owner:AbCd123...@ep-cool-frog.aws.neon.tech/neondb?sslmode=require`

## How to Connect it to Sentinel

### 1. Local Testing (On your Laptop)
1.  Open your `.env` file.
2.  Add/Update this line:
    ```ini
    DATABASE_URL="<paste_your_neon_link_here>"
    ```
3.  Restart your app (`docker-compose restart` or `flask run`).
4.  **Done!** Your local app is now saving data to the cloud.

### 2. Production (On Render/Railway)
1.  Go to your **Render Dashboard**.
2.  Click on your **Sentinel Service**.
3.  Go to **"Environment"** tab.
4.  Click **"Add Environment Variable"**.
5.  **Key**: `DATABASE_URL`
6.  **Value**: `<paste_your_neon_link_here>`
7.  Click **Save Changes**.
8.  Render will redeploy automatically.

## Verification
1.  Register a new account.
2.  Restart the server (or trigger a deploy).
3.  Try to login. **Your account will still exist!** 🎉
