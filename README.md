# YouTube Subscriptions to Atom Feed

This repository allows you to create an Atom RSS feed for your current YouTube subscriptions, and can be automated to update regularly via GitHub Actions.

## Setup Guide

Follow these steps to get started:

### 1. Configure Google Cloud YouTube Data API

- Go to the [Google Cloud Console](https://console.cloud.google.com/apis/dashboard).
- Create a new project (or select an existing one).
- Enable the **YouTube Data API v3** for your project.
- Go to **APIs & Services → Credentials**.
- Click **Create Credentials → OAuth client ID**.
- Choose "Desktop app" and get your `client_id` and `client_secret`.
- Download the generated `credentials.json` file.

### 2. Place `credentials.json` in the Configs Folder

- Move your `credentials.json` file into a new folder called `configs` at the root of this repo. For example:

  ```
  configs/credentials.json
  ```

### 3. Initialize Your Refresh Token

- Run the following command to generate `outputs/token.json` (required for API authentication):

  ```bash
  pip install -r requirements.txt
  python init_token.py
  ```

- This will guide you through Google's OAuth login flow.  
- Once done, you should see a new file: `outputs/token.json`.

### 4. Add Secrets to GitHub

- Open your repository on GitHub.
- Go to **Settings → Secrets and variables → Actions**.
- Add the following repository secrets, copying the values from your credentials and token:

  - `YT_CLIENT_ID` — from your `credentials.json`
  - `YT_CLIENT_SECRET` — from your `credentials.json`
  - `YT_REFRESH_TOKEN` — from the generated `outputs/token.json` (`refresh_token` field)

### 5. That's it!

From now, the workflow will automatically fetch new videos from your subscriptions and publish them into an Atom feed (`feed.xml`) in the repo.

You can now subscribe your feed reader to the public `feed.xml` on the `gh-pages` branch.

Enjoy!

