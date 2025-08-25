# MongoDB Atlas Setup Guide

This guide provides step-by-step instructions for setting up MongoDB Atlas for the AI Customer Service System.

## What is MongoDB Atlas?

MongoDB Atlas is a fully-managed cloud database service provided by MongoDB. It handles all the complexity of deploying, managing, and healing your deployments on the cloud service provider of your choice (AWS, Azure, and GCP).

## Setup Instructions

### 1. Create a MongoDB Atlas Account

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register)
2. Sign up for a free account or log in if you already have one

### 2. Create a New Cluster

1. Click on "Build a Database"
2. Choose your preferred cloud provider (AWS, Azure, or GCP)
3. Select the free tier option (M0 Sandbox) for development or choose a paid tier for production
4. Choose a region closest to your application's deployment location
5. Click "Create Cluster" (this may take a few minutes to provision)

### 3. Set Up Database Access

1. In the left sidebar, click on "Database Access" under Security
2. Click "Add New Database User"
3. Choose "Password" authentication method
4. Enter a username and a secure password
5. Set appropriate database user privileges ("Read and Write to Any Database" is common)
6. Click "Add User"

### 4. Configure Network Access

1. In the left sidebar, click on "Network Access" under Security
2. Click "Add IP Address"
3. For development, you can add your current IP address
4. For production, add the IP addresses of your servers or use `0.0.0.0/0` to allow access from anywhere (not recommended for production without additional security measures)
5. Click "Confirm"

### 5. Get Your Connection String

1. In the left sidebar, click on "Database" under Deployments
2. Click "Connect" on your cluster
3. Choose "Connect your application"
4. Select your driver and version (Python, latest version)
5. Copy the connection string

### 6. Update Your Application Configuration

1. Open your `.env` file
2. Replace the existing `MONGODB_URI` with your Atlas connection string:
   ```
   MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-name>.mongodb.net/hotel_service?retryWrites=true&w=majority
   ```
3. Replace `<username>`, `<password>`, and `<cluster-name>` with your actual values

## Database Management

### Creating Collections

MongoDB will automatically create collections when you first insert documents into them. However, you can also create them manually:

1. In the Atlas dashboard, click on "Collections" for your cluster
2. Click "Add My Own Data"
3. Enter a database name (e.g., "hotel_service")
4. Enter a collection name (e.g., "users", "conversations", "messages")

### Data Import/Export

#### Import Data

1. In the Atlas dashboard, click on "Collections" for your cluster
2. Click the "⋯" menu for your database
3. Select "Import Data"
4. Choose your file format (JSON or CSV) and upload your data

#### Export Data

1. In the Atlas dashboard, click on "Collections" for your cluster
2. Click the "⋯" menu for your database
3. Select "Export Data"
4. Choose your preferred export format

## Monitoring and Optimization

1. In the Atlas dashboard, click on "Metrics" for your cluster
2. Monitor database performance, connections, and operations
3. Set up alerts for critical metrics by clicking on "Alerts" in the left sidebar

## Backup and Restore

### Automated Backups

MongoDB Atlas provides automated backups for all paid clusters:

1. In the left sidebar, click on "Backup" under Data Services
2. Configure your backup policy

### Manual Backups

1. In the left sidebar, click on "Backup" under Data Services
2. Click "Take Snapshot Now"

### Restore from Backup

1. In the left sidebar, click on "Backup" under Data Services
2. Find the backup you want to restore
3. Click the "⋯" menu and select "Restore"

## Security Best Practices

1. Use strong, unique passwords for database users
2. Restrict network access to only necessary IP addresses
3. Enable two-factor authentication for your Atlas account
4. Regularly rotate credentials
5. Use IP access lists instead of allowing access from anywhere
6. Consider using VPC peering for production environments

## Troubleshooting

### Connection Issues

1. Verify your connection string is correct
2. Check that your IP address is in the allowed list
3. Ensure your username and password are correct
4. Verify that your cluster is active

### Performance Issues

1. Check your database metrics in the Atlas dashboard
2. Review your indexes and create new ones if necessary
3. Consider upgrading your cluster tier if you're experiencing resource limitations

## Connecting with MongoDB for VS Code

### 1. Install MongoDB for VS Code

1. In VS Code, open "Extensions" in the left navigation
2. Search for "MongoDB for VS Code"
3. Select the extension and click "Install"

### 2. Connect to MongoDB Atlas

1. In VS Code, open the Command Palette (View > Command Palette)
2. Search for "MongoDB: Connect" and click on "Connect with Connection String"
3. Paste your connection string:
   ```
   mongodb+srv://digantasadhukhan:<db_password>@cluster0.bhtdwyg.mongodb.net/
   ```
4. Replace `<db_password>` with the password for the digantasadhukhan user
5. Click "Create New Playground" in MongoDB for VS Code to get started

### 3. Using MongoDB Playground

1. Write and execute MongoDB queries in the playground
2. Browse your database structure in the MongoDB extension sidebar
3. Create, read, update, and delete documents directly from VS Code

## Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [MongoDB University](https://university.mongodb.com/) - Free courses on MongoDB
- [MongoDB Community Forums](https://www.mongodb.com/community/forums/)
- [MongoDB for VS Code Documentation](https://docs.mongodb.com/mongodb-vscode/)