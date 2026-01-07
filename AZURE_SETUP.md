# Azure Setup Instructions

This guide will help you set up Azure SQL Database and Azure App Service to run the Portfolio Analytics application.

## Prerequisites

- Azure account (free tier available)
- Azure CLI installed (`az --version` to check)
- Python 3.10+ installed
- Node.js 18+ installed (for React dashboard)

## Step 1: Create Azure SQL Database

### Option A: Using Azure Portal

1. Go to [Azure Portal](https://portal.azure.com)
2. Click "Create a resource" → Search for "SQL Database"
3. Fill in the details:
   - **Subscription**: Your subscription
   - **Resource Group**: Create new or use existing
   - **Database name**: `portfolio-analytics-db`
   - **Server**: Create new server
     - Server name: `portfolio-analytics-server` (must be unique)
     - Location: Choose closest to you
     - Authentication method: SQL authentication
     - Admin username: `adminuser` (or your choice)
     - Password: Create a strong password (save this!)
   - **Compute + storage**: Basic tier (cheapest option for testing)
4. Click "Review + create" → "Create"
5. Wait for deployment (2-3 minutes)

### Option B: Using Azure CLI

```bash
# Login to Azure
az login

# Create resource group
az group create --name portfolio-analytics-rg --location eastus

# Create SQL server
az sql server create \
  --name portfolio-analytics-server \
  --resource-group portfolio-analytics-rg \
  --location eastus \
  --admin-user adminuser \
  --admin-password YourStrongPassword123!

# Create SQL database
az sql db create \
  --resource-group portfolio-analytics-rg \
  --server portfolio-analytics-server \
  --name portfolio-analytics-db \
  --service-objective Basic
```

## Step 2: Configure Firewall Rules

Allow your IP address to access the database:

### Using Azure Portal:
1. Go to your SQL server resource
2. Click "Networking" in the left menu
3. Under "Public access", select "Selected networks"
4. Click "Add your client IPv4 address"
5. Click "Save"

### Using Azure CLI:
```bash
# Get your IP address
MY_IP=$(curl -s https://api.ipify.org)

# Add firewall rule
az sql server firewall-rule create \
  --resource-group portfolio-analytics-rg \
  --server portfolio-analytics-server \
  --name AllowMyIP \
  --start-ip-address $MY_IP \
  --end-ip-address $MY_IP
```

## Step 3: Update Configuration

Update `config.py` with your Azure SQL Database credentials:

```python
AZURE_SERVER = "portfolio-analytics-server.database.windows.net"
AZURE_DATABASE = "portfolio-analytics-db"
AZURE_USERNAME = "adminuser"
AZURE_PASSWORD = "YourStrongPassword123!"
```

## Step 4: Install ODBC Driver

### macOS:
```bash
brew tap microsoft/mssql-release https://github.com/Microsoft/homebrew-mssql-release
brew update
brew install msodbcsql18
```

### Linux (Ubuntu/Debian):
```bash
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update
ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

### Windows:
Download and install from: https://docs.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server

## Step 5: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 6: Run ETL Pipeline

Test the connection and populate the database:

```bash
python etl_pipeline.py
```

This will:
- Fetch stock data for all tickers
- Clean the data
- Store it in Azure SQL Database

## Step 7: (Optional) Deploy to Azure App Service

### Create App Service:

```bash
# Create App Service plan
az appservice plan create \
  --name portfolio-analytics-plan \
  --resource-group portfolio-analytics-rg \
  --sku B1 \
  --is-linux

# Create web app
az webapp create \
  --resource-group portfolio-analytics-rg \
  --plan portfolio-analytics-plan \
  --name portfolio-analytics-app \
  --runtime "PYTHON:3.10"
```

### Configure Environment Variables:

```bash
az webapp config appsettings set \
  --resource-group portfolio-analytics-rg \
  --name portfolio-analytics-app \
  --settings \
    AZURE_SERVER="portfolio-analytics-server.database.windows.net" \
    AZURE_DATABASE="portfolio-analytics-db" \
    AZURE_USERNAME="adminuser" \
    AZURE_PASSWORD="YourStrongPassword123!"
```

### Deploy Code:

```bash
# Install Azure CLI extension
az extension add --name webapp

# Deploy from local directory
az webapp up \
  --resource-group portfolio-analytics-rg \
  --name portfolio-analytics-app \
  --runtime "PYTHON:3.10"
```

## Step 8: Run Backend API Locally

```bash
# Install Flask dependencies
pip install flask flask-cors

# Run the API
python app.py
```

The API will be available at `http://localhost:5000`

## Step 9: Run React Dashboard

```bash
cd dashboard
npm install
npm start
```

The dashboard will be available at `http://localhost:3000`

## Troubleshooting

### Connection Issues:
- Verify firewall rules allow your IP
- Check that server name includes `.database.windows.net`
- Ensure ODBC driver is installed correctly
- Test connection: `python -c "import pyodbc; print(pyodbc.drivers())"`

### Database Issues:
- Verify database exists in Azure Portal
- Check that credentials are correct in `config.py`
- Ensure database is not paused (Basic tier can auto-pause)

### Cost Optimization:
- Use Basic tier for development (can auto-pause)
- Set up auto-pause to save costs
- Delete resources when not in use

## Next Steps

1. Run `etl_pipeline.py` to populate initial data
2. Implement `forecast_model.py` with gradient boosting
3. Run `portfolio_metrics.py` to generate analytics
4. Start the Flask API: `python app.py`
5. Start the React dashboard: `cd dashboard && npm start`

## Security Notes

- Never commit `config.py` to git (already in `.gitignore`)
- Use Azure Key Vault for production credentials
- Enable SSL/TLS for all connections
- Regularly rotate database passwords

