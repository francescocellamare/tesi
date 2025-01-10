
## 📂 Directories

### `demo/`
Project used for testing

### `lambdaCode/`
Holds all lambda functions' code distributed as follow:
- `createReport/`: create the report extracting data from commit and test validation
- `handleReport/`: handle each case for generating tests
- `sendEmail/`
- `approval/`: handling the dev's selection inside the email, used by the API Gateway
- `sendPullRequestEmail/`
- `createPullRequest/`
- `checkPullRequest/`: checks the PR status each 30s for 5 minutes, final check before deploy
- `adaptOutput/`: parsing the image definition artifact according to ECS requirements
- `stats`: not used till now

### `lambdalayer/`
Used for configuration of _handleReport_ lambda function

### `resources/`
Holds all the needed files as follow:
- `grafana/`: configuration files for creating the local docker image
- `script/`: set of script for setup of the dashboard .csv files and path selection

### `makefile`
Commands to:
- handle S3 bucket
- handle report creation and delation (it's package each time due to the local code pushed inside a S3 bucket)

### `my_template.yml`
Original template

### `packaged_template.yml`
Template created using the command ```make create_template``` and deployed with ```make deploy_template```
