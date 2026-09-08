Step 1 — Open the workspace
create a folder to run the project

C:\Projects\MyApiTesting\

in VS Code.

Step 2 — Configure the project - copy the zip file and extract here
Open:

config\project.env - rename

Put in:

MULESOFT_GIT_REPOSITORY_URL=https://git.company.com/team/customer-api.git
MULESOFT_GIT_BRANCH=Develop

ANYPOINT_ORG_ID=xxxxxxxx
ANYPOINT_BUSINESS_GROUP_ID=xxxxxxxx
ANYPOINT_ENVIRONMENT=DEV
ANYPOINT_APPLICATION_NAME=customer-api
ANYPOINT_APPLICATION_ID=xxxxxxxx

POSTMAN_GIT_REPOSITORY_URL=https://git.company.com/team/customer-api-postman.git
POSTMAN_GIT_BRANCH=Develop

POSTMAN_COLLECTION_PATH=collections/customer-api.postman_collection.json
POSTMAN_DEV_ENVIRONMENT_PATH=environments/DEV.postman_environment.json

That's the project-specific information.

Step 3 — Configure credentials
Use the organization's approved credential mechanism.

For the local fallback:

credentials\credentials.env

The Git credentials should be read-only.

The Anypoint credentials should have application read-only/artifact retrieval permissions.

Step 4 — Run one prompt
From the VS Code Claude Code session, use the following prompt.

Final execution prompt