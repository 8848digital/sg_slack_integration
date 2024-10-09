# Slack Integration

## Project Description
This project integrates the Slack messaging app with ERPNext, enabling creation and deletion of slack channels, user addition, user removal and other slack features.

## How to Install and Run the Project

### Installation Steps:
1. **Install ERPNext**: Ensure that you have ERPNext installed on your system. Follow the [ERPNext Installation Guide](https://frappeframework.com/docs/user/en/installation) if needed.

2. **Clone the Repository**:
    git get-app https://github.com/8848digital/slack-integration.git
    cd slack-integration
   
3. **Install Required Dependencies**:
    Install the required dependencies for the project by running the following command inside your ERPNext directory:
    bench install-app slack_integration
   
4. **Apply Migration**:
    Run the following to migrate changes to your database:
    bench migrate
   
5. **Configure Slack**: 
    - Go to Slack, create an app and get your Slack API token.
    - Add the Slack API token to the ERPNext settings (`Slack Integration Settings` settings in your ERPNext instance).


### How to Use the Project

1. **Configure Slack Settings**: 
    - Navigate to the Slack Integration module in ERPNext.
    - Configure the necessary API keys and tokens.
  
## How to Contribute to the Project

We welcome contributions from the community! Here's how you can contribute to the project:

1. **Fork the Repository**: Start by forking the repository on GitHub.
   
2. **Clone Your Fork**: Clone your forked repository to your local machine:
    git clone https://github.com/8848digital/slack-integration.git
   
4. **Create a New Branch**: Create a new branch for your changes:
    git checkout -b my-new-feature

5. **Make Changes**: Implement your feature or fix the bug.

6. **Test Your Changes**: Ensure your changes work by testing in your local ERPNext setup.

7. **Commit Your Changes**: 
    git commit -m "Add new feature"
    
8. **Push to Your Fork**:
    git push origin my-new-feature
    
9. **Submit a Pull Request**: Open a pull request from your fork to the main repository, describing the changes you've made.

### Guidelines for Contributing to Frappe Projects:
- Ensure your code follows the Frappe framework's coding standards.
- Provide adequate comments and documentation.
- Test your changes thoroughly before submitting a pull request.
- Follow the Frappe Contribution Guidelines, which you can find [here](https://frappeframework.com/contribute).

## Credits
Developed by the **8848 Team Members**.

## License
This project is licensed under the MIT License.

## Tests
Test cases for this project have not yet been written. Stay tuned for future updates.
