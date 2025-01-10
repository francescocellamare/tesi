## 📂 Directories

### `demo/`
Project used for testing.

### `lambdaCode/`
Contains the code for all Lambda functions, structured as follows:
- **`createReport/`**: Creates a report by extracting data from commits and validating tests.
- **`handleReport/`**: Manages each case for generating tests.
- **`sendEmail/`**: Handles email sending functionality.
- **`approval/`**: Processes developer selections from emails, used by the API Gateway.
- **`sendPullRequestEmail/`**: Sends pull request notifications via email.
- **`createPullRequest/`**: Automates the creation of pull requests.
- **`checkPullRequest/`**: Monitors pull request status every 30 seconds for 5 minutes, performing the final check before deployment.
- **`adaptOutput/`**: Parses the image definition artifact to meet ECS requirements.
- **`stats/`**: Reserved for future use (currently unused).

### `lambdalayer/`
Contains configuration files used by the `handleReport` Lambda function.

### `resources/`
Holds all necessary resource files:
- **`grafana/`**: Configuration files for creating a local Docker image of Grafana.
- **`script/`**: Scripts for setting up the dashboard, including `.csv` file preparation and path selection.

### `makefile`
Provides commands for:
- Managing the S3 bucket.
- Creating and deleting reports (packaged each time before pushing to the S3 bucket).

### `my_template.yml`
The original CloudFormation template.

### `packaged_template.yml`
The processed CloudFormation template created using the command `make create_template` and deployed with `make deploy_template`.
