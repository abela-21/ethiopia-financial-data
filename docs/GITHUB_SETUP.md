# GitHub Repository Setup Guide

## Creating a New GitHub Repository

### Step 1: Create Repository on GitHub
1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Fill in repository details:
   - **Repository name**: `ethiopia-capital-market`
   - **Description**: `A comprehensive financial data platform for Ethiopia's capital market`
   - **Visibility**: Choose Public or Private
   - **Initialize**: Do NOT check "Add a README file" (we already have one)
5. Click "Create repository"

### Step 2: Connect Local Project to GitHub

Open your terminal and run these commands in your project directory:

```bash
# Initialize git repository (if not already done)
git init

# Add all files to git
git add .

# Create initial commit
git commit -m "Initial commit: Ethiopia Capital Market Platform"

# Add GitHub repository as remote origin
git remote add origin https://github.com/YOUR_USERNAME/ethiopia-capital-market.git

# Push to GitHub
git push -u origin main
```

Replace `YOUR_USERNAME` with your actual GitHub username.

### Step 3: Repository Configuration

#### Branch Protection (Recommended)
1. Go to your repository on GitHub
2. Click "Settings" tab
3. Click "Branches" in the left sidebar
4. Click "Add rule" for main branch
5. Enable:
   - Require pull request reviews before merging
   - Require status checks to pass before merging

#### Repository Topics
Add these topics to help others discover your repository:
- `ethiopia`
- `finance`
- `capital-market`
- `flask`
- `postgresql`
- `data-visualization`
- `economic-indicators`

### Step 4: Environment Variables for Deployment

If deploying from GitHub, set these secrets in your repository:

1. Go to repository Settings → Secrets and variables → Actions
2. Add these repository secrets:
   - `DATABASE_URL`: Your PostgreSQL connection string
   - `SESSION_SECRET`: A secure random string

### Step 5: Collaborative Development

#### For Team Members:
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/ethiopia-capital-market.git

# Navigate to project directory
cd ethiopia-capital-market

# Install dependencies
pip install -e .

# Set up environment variables
export DATABASE_URL="your_database_url"
export SESSION_SECRET="your_secret_key"

# Load sample data
python Data/load_data.py

# Run the application
gunicorn --bind 0.0.0.0:5000 --reload main:app
```

#### Development Workflow:
```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes and commit
git add .
git commit -m "Add new feature"

# Push feature branch
git push origin feature/new-feature

# Create pull request on GitHub
# After review and merge, update main branch
git checkout main
git pull origin main
```

### Step 6: Continuous Integration (Optional)

Create `.github/workflows/ci.yml` for automated testing:

```yaml
name: CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -e .
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/test_db
        SESSION_SECRET: test-secret
      run: |
        python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

### Repository Structure
Your repository will include:
- Complete source code
- Documentation (README, ARCHITECTURE, etc.)
- Sample data files
- Deployment configuration
- License and contributing guidelines

The repository is now ready for collaborative development and deployment!