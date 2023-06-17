#!/bin/bash

# Get the full directory name of the script no matter where it is being called from
SCRIPT_DIR=$(dirname "$(realpath "$0")")

# Change to the directory where the script is located
cd "$SCRIPT_DIR"

# Define colors
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Parse command-line options
while getopts "v" opt; do
  case ${opt} in
    v)
      verbose=true
      ;;
    \?)
      echo "Invalid option: -$OPTARG" 1>&2
      exit 1
      ;;
  esac
done

# Set the project directory to the directory containing the script
PROJECT_DIR=$SCRIPT_DIR

# Check and activate conda environment
if [[ $CONDA_PREFIX != *"/env" ]]; then
    printf "${BOLD}Checking conda environment...\n${NC}"
    if [[ $VERBOSE_MODE == "true" ]]; then
        printf "${BOLD}Conda environment '$PROJECT_DIR/env' not active. Activating now...\n${NC}"
    fi
    source activate $PROJECT_DIR/env
else
    if [[ $VERBOSE_MODE == "true" ]]; then
        printf "${BOLD}Conda environment '$PROJECT_DIR/env' is already active.\n${NC}"
    fi
fi

printf "${BOLD}Running pylint on /src and /tests folders...\n${NC}"
pylint_result=$(pylint ${PROJECT_DIR}/src ${PROJECT_DIR}/tests)
if [[ $? -eq 0 ]]; then
    printf "${GREEN}Pylint check passed.\n${NC}"
else
    printf "${RED}Pylint check failed. See output:\n${NC}"
    echo "${pylint_result}"
fi

printf "${BOLD}Running flake8 on /src and /tests folders...\n${NC}"
flake8_result=$(flake8 ${PROJECT_DIR}/src ${PROJECT_DIR}/tests)
if [[ $? -eq 0 ]]; then
    printf "${GREEN}flake8 check passed.\n${NC}"
else
    printf "${RED}flake8 check failed. See output:\n${NC}"
    echo "${flake8_result}"
fi

printf "${BOLD}Checking if GOOGLE_APPLICATION_CREDENTIALS is set and points to a json file...\n${NC}"
if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
    printf "${YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS is not set.\n${NC}"
elif [[ ! -f "${GOOGLE_APPLICATION_CREDENTIALS}" ]]; then
    printf "${YELLOW}Warning: GOOGLE_APPLICATION_CREDENTIALS does not point to a valid file.\n${NC}"
else
    printf "${GREEN}GOOGLE_APPLICATION_CREDENTIALS is set and points to a valid file.\n${NC}"
fi

printf "${BOLD}Checking gcloud authentication...\n${NC}"
gcloud_auth=$(gcloud auth list)
if [[ $? -eq 0 ]]; then
    printf "${GREEN}gcloud is authenticated.\n${NC}"
    if [[ $verbose = true ]]; then
        echo "${gcloud_auth}"
    fi
else
    printf "${RED}gcloud is not authenticated. Please check your setup.\n${NC}"
fi

printf "${BOLD}Checking package version...\n${NC}"
package_version=$(python -c "import toml; print(toml.load('${PWD}/pyproject.toml')['project']['version'])")
all_versions=$(gcloud artifacts versions list --package ArticleService --location europe-west6 --repository dev-projects --format='value(VERSION)')
sorted_versions=$(echo "${all_versions}" | sort -V)
latest_registry_version=$(echo "${sorted_versions}" | tail -n 1)
if [[ $package_version > $latest_registry_version ]]; then
    printf "${GREEN}Local version ($package_version) is higher than the latest version in the registry ($latest_registry_version).\n${NC}"
elif [[ $package_version == $latest_registry_version ]]; then
    printf "${YELLOW}Local version ($package_version) is equal to the latest version in the registry ($latest_registry_version).\n${NC}"
    exit 1
else
    printf "${RED}Local version ($package_version) is lower than the latest version in the registry ($latest_registry_version).\n${NC}"
    exit 2
fi


