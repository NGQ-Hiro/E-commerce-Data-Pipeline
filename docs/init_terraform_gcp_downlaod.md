# Install GCP CLI

## Install

- Download Google Cloud CLI installer
- Run .exe

## What does it do ?

- High privileges
- Create projects, create service account, ...
- Ussually for set up project

# Install terraform

## Install

- Download from https://developer.hashicorp.com/terraform/install#windows window AMD64
- Add path into environment C:\terraform_1.14.3_windows_amd64

## What does it do ?

- Belongs to one project
- Build infrastructure in that project
- If credentials leak -> attacker only damage one project not whole accounts

# Set up Project

## GCP

- gcloud init
  sign in with your gg account
  choose or create new project

## SSH
- ssh-keygen -t ed25519 -f ~/.ssh/gcloud -C "gcloud"


## Teraform

- Create project
- Add billing
- Add Service account for Terraform
- Add role for Terraform (
  Storage admin -> create bucket,
  Service Account Admin -> create account service for kafka, dbt ..
  Service Account Key Admin -> create key for service run from local
  )
- Create Json key for Terraform
- Store key to main.tf can access key
- Create main.tf using Projectid, key...
- From now add all service via Terraform (not need to mannual)