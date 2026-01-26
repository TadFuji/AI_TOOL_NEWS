# AI TOOL NEWS 🚀

**Automated AI News Aggregator & Static Site Generator**

[![Live Site](https://img.shields.io/badge/Live-Demo-00f2ff?style=for-the-badge&logo=github&logoColor=white)](https://TadFuji.github.io/AI_TOOL_NEWS/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](LICENSE)
[![Powered by Grok](https://img.shields.io/badge/Powered%20by-xAI%20Grok-white?style=for-the-badge&logo=x)](https://x.ai/)

AI TOOL NEWS is a fully automated system that monitors official X (Twitter) accounts of major AI tools and companies, filters for significant updates using LLMs, and generates a beautiful, Glassmorphism-styled news website.

🔗 **View the Live Site:** [https://TadFuji.github.io/AI_TOOL_NEWS/](https://TadFuji.github.io/AI_TOOL_NEWS/)

---

## ✨ Features

- **Automated Collection**: Scrapes X for the latest posts from 30+ top AI accounts (OpenAI, Google DeepMind, Anthropic, etc.).
- **Smart Filtering**: Uses **xAI Grok-4** to analyze tweets and filter out casual replies, keeping only "Newsworthy" updates.
- **Static Site Generation**: Converts collected data into a premium static HTML site (no database required).
- **Glassmorphism Design**: Features a modern, responsive UI with animated backgrounds and blurred glass cards.
- **Secure**: API keys are isolated in `.env` and strictly excluded from Git history.

## 🚧 Project Boundaries & Architecture

The user operates two distinct AI news systems. It is critical to maintain the separation of concerns between them.

| System | **AI_TOOL_NEWS** (This Project) | **ai-news-bot** (External Project) |
| :--- | :--- | :--- |
| **Primary Goal** | Real-time monitoring of specific AI Tool vendors on X. | Daily digest of general AI industry news via RSS. |
| **Data Source** | **Official X Accounts** (e.g., @OpenAI, @xAI) | **RSS Feeds** (TechCrunch, The Verge, Blogs) |
| **Frequency** | **Hourly** (Run via GitHub Actions) | **Daily** (07:00 AM JST) |
| **Output Channels** | Website, X Account (Immediate updates) | LINE, Website, X Account (Daily Summary) |
| **Content Tone** | **Gentle, Polite Japanese** (Automatic Translation) | Standard News Summary |
| **Location** | `~/Desktop/Antigravity/AI_TOOL_NEWS` | `~/Desktop/Antigravity/ai-news-bot` |

**DO NOT** mix RSS collection or LINE notification logic into this repository. This repository is strictly for **X-based real-time updates**.

## 🛠️ Installation & Usage

### Prerequisites
- Python 3.8+
- An xAI API Key (or compatible LLM key if you modify the script)

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/TadFuji/AI_TOOL_NEWS.git
   cd AI_TOOL_NEWS
   ```

2. **Install dependencies**
   ```bash
   pip install requests
   ```

3. **Configure API Key**
   Create a `.env` file in the root directory:
   ```env
   XAI_API_KEY=your_xai_api_key_here
   ```

### Daily Operation
1. **Collect News**
   ```bash
   python collect_ai_news.py
   ```
   This will generate markdown reports in the `reports/YYYY-MM-DD/` folder.

2. **Build Website**
   ```bash
   python build_site.py
   ```
   This updates `docs/index.html` with the latest data.

3. **Deploy**
   Push the changes to GitHub.
   ```bash
   git add .
   git commit -m "Update news"
   git push
   ```
   GitHub Pages will automatically serve the content from the `/docs` folder.

## 🎯 Configuration
You can add or remove monitoring targets by editing **`targets.json`**.
```json
{
    "category": "My Custom Tools",
    "tools": [
        { "name": "Tool Name", "accounts": ["@OfficialAccount"] }
    ]
}
```

## 🤝 Contributing
Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to add new tools or improve the filtering logic.

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
*Created by [TadFuji](https://github.com/TadFuji)*
