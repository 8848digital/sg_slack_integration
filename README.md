# Slack Integration

## Project Description
This project integrates the Slack messaging app with ERPNext, enabling creation and deletion of slack channels, user addition, user removal and other slack features.

## How to Install and Run the Project

### Installation Steps:
1. **Install ERPNext**: Ensure that you have ERPNext installed on your system. Follow the [ERPNext Installation Guide](https://frappeframework.com/docs/user/en/installation) if needed.
2. **Clone the Repository**:
    ```bash
    git clone https://github.com/your-username/slack-integration.git
    cd slack-integration
    ```
3. **Install Required Dependencies**:
    Install the required dependencies for the project by running the following command inside your ERPNext directory:
    ```bash
    bench get-app slack_integration /path/to/slack-integration
    ```
4. **Apply Migration**:
    Run the following to migrate changes to your database:
    ```bash
    bench migrate
    ```

5. **Configure Slack**: 
    - Go to Slack, create an app and get your Slack API token.
    - Add the Slack API token to the ERPNext settings (`Slack Integration` settings in your ERPNext instance).

6. **Start Bench**:
    Start the ERPNext instance by running:
    ```bash
    bench start
    ```

### How to Use the Project

1. **Configure Slack Settings**: 
    - Navigate to the Slack Integration module in ERPNext.
    - Set up your Slack channels, and configure the necessary API keys and tokens.
  
2. **Send and Receive Messages**:
    - After configuration, you can send messages from ERPNext to Slack channels.
    - Configure automated notifications for specific events or actions within ERPNext.

3. **Automated Notifications**:
    - Set up custom notifications to trigger Slack messages based on defined actions (e.g., new sales order, task assignment).

## Credits
Developed by the **8848 Team Members**.

##
