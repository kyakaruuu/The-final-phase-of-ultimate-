# Ultimate Chemistry Bot - JEE Advanced

## Overview
A Telegram bot that provides triple-strategy AI-powered chemistry problem solving for JEE Advanced students. Uses Google Gemini AI to analyze chemistry problems from images and generates detailed PDF reports with solutions.

## Project Type
Python Telegram Bot (Console Application)

## Key Features
- **Triple-Strategy Analysis**: Systematic, MS Chouhan, and Paula Bruice approaches
- **98-99% Accuracy** using multiple verification methods
- **GitHub Knowledge Integration** from Global-Chem database
- **Beautiful PDF Reports** with professional formatting
- **JEE Advanced Logic** with trap detection
- **Multi-API Key Rotation** for reliability
- **Smart Image Enhancement** for better analysis

## Technology Stack
- **Language**: Python 3.11
- **Bot Framework**: python-telegram-bot 20.7
- **AI Model**: Google Gemini 2.0 Flash
- **Database**: SQLite with SQLAlchemy ORM
- **Machine Learning**: scikit-learn, networkx (knowledge graphs)
- **Data Visualization**: matplotlib, seaborn, plotly
- **Image Processing**: Pillow 10.1.0
- **PDF Generation**: WeasyPrint 59.0
- **Template Engine**: Jinja2 3.1.2
- **HTTP Clients**: httpx, aiohttp
- **Async**: asyncio, nest-asyncio
- **Scheduling**: APScheduler (for smart automation)

## Required Secrets
- `BOT_TOKEN`: Telegram Bot API token from @BotFather
- `GEMINI_KEY_1`: Primary Google Gemini API key (required)
- `GEMINI_KEY_2` to `GEMINI_KEY_5`: Additional Gemini keys (optional, for redundancy)

## Project Structure
```
├── ULTIMATE_JE.py                  # Main bot application
├── advanced_features.py            # Core advanced features (gamification, etc.)
├── complete_command_handlers.py    # All 52 feature command handlers
├── feature_modules/                # ⭐ NEW: 52 features organized by category
│   ├── intelligence/               # Self-learning, error patterns, cognitive load, knowledge graph
│   ├── social/                     # Peer comparison, collective intelligence, study groups
│   ├── personalization/            # Learning styles, adaptive difficulty, study time
│   ├── content/                    # Trending topics, daily facts, video integration
│   ├── analytics_advanced/         # Heatmaps, comparative analytics, predictions
│   ├── collaboration/              # Question exchange, voting, doubt resolution
│   ├── automation/                 # Smart reminders, auto-quizzes, notifications
│   ├── advanced/                   # Voice, OCR, AR viewer, multi-language
│   └── master_integration.py       # Central hub coordinating all features
├── phase1_admin.py                 # Admin commands
├── phase1_features.py              # Text queries, feedback
├── phase2_exam.py                  # Mock test functionality
├── phase2_features.py              # Hints, flashcards, themes
├── phase2_predictors.py            # pKa and JEE frequency analysis
├── phase2_visualizer.py            # Molecule and concept map visualization
├── requirements.txt                # Python dependencies
├── COMPLETE_FEATURE_LIST.md        # ⭐ Complete documentation of all 52 features
├── Procfile                        # Deployment command
└── nixpacks.toml                   # Nixpacks configuration
```

## Recent Changes

- **2025-10-27**: 🎉 COMPLETE FEATURE ARSENAL - ALL 52 FEATURES IMPLEMENTED!
  - ✅ **Intelligence Upgrades (6 features):** Self-Learning Engine, Error Pattern Recognition, Cognitive Load Detection, Predictive Intervention, Socratic Dialogue Mode, Knowledge Graph Reasoning
  - ✅ **Social Learning (4 features):** Anonymous Peer Comparison, Collective Intelligence, Study Groups Matching, Student-Generated Content
  - ✅ **Hyper-Personalization (5 features):** Learning Style Detection, Adaptive Difficulty Engine, Optimal Study Time Predictor, Custom Hint Levels, Career Goal Alignment
  - ✅ **Dynamic Content (6 features):** Trending Topics Dashboard, Daily Chemistry Facts, Video Integration, Research Paper Summaries, Exam Pattern Analysis, Mnemonic Generator
  - ✅ **Advanced Analytics (4 features):** Strength/Weakness Heatmap, Comparative Analytics, Performance Prediction Model, JEE Rank Predictor
  - ✅ **Collaborative Features (5 features):** Question Exchange, Explanation Voting, Doubt Resolution Network, Study Challenges, Anonymous Q&A
  - ✅ **Smart Automation (6 features):** Smart Reminders, Auto-Generated Quizzes, Progress Reports, Exam Countdown, Auto-Tagging System, Smart Notifications
  - ✅ **Advanced Features (8 features):** Voice Input Support, Multi-Language Support (Hindi/English), OCR for Handwritten Notes, Concept Dependency Tree, AI Study Buddy Personality, Parent Dashboard, Offline Mode Cache, AR Molecule Viewer
  - 📁 Created highly organized `feature_modules/` directory structure with 8 category folders
  - 🎯 Implemented master integration hub coordinating all 52 features
  - 🚀 Added 14+ new Telegram commands for all features
  - 📚 Created comprehensive documentation in COMPLETE_FEATURE_LIST.md

- **2025-10-27**: Initial advanced features implementation
  - Created SQLite database with full schema (users, achievements, analytics)
  - Integrated AnalyticsEngine for performance tracking
  - Added ContentGenerator for AI-generated practice problems
  - Implemented Multi-Agent Debate System (3-5 AI agents)
  - User tracking system with gamification (levels, XP, streaks)
  - Achievement system with 6 badges
  - Personalized learning paths based on user weaknesses

- **2025-10-27**: Initial Replit environment setup
  - Installed Python 3.11 and all dependencies
  - Installed system dependencies (cairo, pango, gdk-pixbuf)
  - Configured workflow for console output

## How It Works
1. Students send chemistry problem images via Telegram
2. Bot enhances image quality and analyzes using Gemini AI
3. Downloads chemistry knowledge base from GitHub (Global-Chem)
4. Applies triple-strategy analysis (Systematic, MS Chouhan, Bruice)
5. Generates professional PDF report with complete solution
6. Typical response time: 2-8 minutes

## Commands Available

### Core Commands
- `/start` - Welcome message and feature overview
- `/help` - Detailed usage instructions
- `/stats` - View knowledge base statistics
- `/settings` - Adjust preferences
- `/about` - Bot information

### Visualization & Learning
- `/molecule <formula>` - 3D molecule viewer
- `/conceptmap <topic>` - Interactive concept maps
- `/hint` - Progressive hints system
- `/flashcard` - Dynamic study flashcards
- `/mocktest` - Practice exam mode
- `/pka <molecule>` - pKa estimation
- `/jeefrequency <topic>` - Topic frequency analysis

### ✨ Personalized Features
- `/dashboard` - View your performance stats, level, XP, streaks
- `/weaknesses` - See your weak topics with practice suggestions
- `/achievements` - View earned and locked achievement badges
- `/leaderboard [daily/weekly/alltime]` - See rankings
- `/practice <topic>` - Generate AI-powered practice problems
- `/multidebate` - Multi-agent debate mode

### 🧠 Intelligence & Learning
- `/learninginsights` - Discover how you learn best
- `/erroranalysis <topic>` - Analyze your common mistakes
- `/cognitivestate` - Check if you're tired or in flow state
- `/socratic <topic>` - Learn through Socratic questioning
- `/knowledgegraph <concept>` - View concept relationships
- `/learningstyle` - Detect your learning style (visual/verbal/kinesthetic)
- `/studytime` - Find when you learn best (morning/evening)

### 📊 Analytics & Comparison
- `/peercompare` - Compare your performance to other students
- `/communityinsights <topic>` - See what the community has learned
- `/heatmap` - Visual map of your strengths and weaknesses
- `/jeerank` - Predict your potential JEE rank

### 🌍 Social & Content
- `/findpartner` - Find study partners at your skill level
- `/trending` - See which topics are hot in recent JEE papers
- `/fact` - Get daily chemistry facts for motivation

### Admin Commands (Owner Only)
- Various admin commands for user management and bot control

## Notes
- This is a console application (Telegram bot), not a web server
- First run downloads chemistry knowledge from GitHub (30-90 seconds)
- Knowledge is cached to chemistry_cache.json for faster subsequent runs
- Bot requires active internet connection to communicate with Telegram and Gemini APIs

## Important: Only One Bot Instance
⚠️ **Telegram allows only ONE instance of a bot to run at a time.**

If you see this error:
```
Conflict: terminated by other getUpdates request; make sure that only one bot instance is running
```

This means another instance of your bot is running elsewhere. To fix:
1. Stop any other instances (check your local computer, other servers, Railway, etc.)
2. Wait 1-2 minutes for Telegram to release the connection
3. Restart the bot in Replit

The bot is properly configured and will work once other instances are stopped.
