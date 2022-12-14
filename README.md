<!-- markdownlint-configure-file {
  "MD033": false,
  "MD041": false
} -->
<div align="center">

<img src="https://user-images.githubusercontent.com/20788334/198634875-096afc35-ce49-4b8e-815d-9d5f71ac7c90.png" width="200" height="100"/>

# AWS Slapdash

[![PyPI version](https://badge.fury.io/py/aws-slapdash.svg)](https://badge.fury.io/py/aws-slapdash)

AWS Slapdash is a faster way to browse your **AWS Resources**, powered by Slapdash.

It integrates with Slapdash to enable to jump to any AWS resource without loading
any AWS console pages with just a few key strokes.

<img src="https://user-images.githubusercontent.com/20788334/198823323-392f76c7-3161-40bd-a426-0d4490a62601.gif" width="75%" height="75%"/>

</div>

- [AWS Slapdash](#aws-slapdash)
  - [What is Slapdash?](#what-is-slapdash)
  - [Why Do I Need It?](#why-do-i-need-it)
  - [Installation](#installation)
    - [Step 0: Prerequisites](#step-0-prerequisites)
    - [Step 1: Install AWS Slapdash](#step-1-install-aws-slapdash)
    - [Step 2: Add commands to Slapdash](#step-2-add-commands-to-slapdash)
    - [Step 3: Configure the AWS profile](#step-3-configure-the-aws-profile)
  - [Usage & Configuration](#usage--configuration)
    - [Set AWS Profile & Region](#set-aws-profile--region)
    - [AWS Vault](#aws-vault)
  - [Features](#features)
    - [Cloud Formation](#cloud-formation)
    - [Dynamo DB](#dynamo-db)
    - [EC2](#ec2)
    - [Secrets Manager](#secrets-manager)
    - [ECS](#ecs)

## What is Slapdash?

[Slapdash](https://slapdash.com/home) is a command bar widget that can be pulled
up anywhere, and you can search through all of your applications.

## Why Do I Need It?

Navigating through AWS console can be time consuming, imagine you want to check
you EC2 instance status and you have to navigate through 1 or 2 pages to get there.

What if you could get the page you want in AWS without having to navigate from
the console there and load all those pages?
This is what this project helps you to achieve.

## Installation

### Step 0: Prerequisites

1. Create an account and download [Slapdash](https://slapdash.com/home)
2. Install Python (+3.7). You can use [Pyenv](https://github.com/pyenv/pyenv).

### Step 1: Install AWS Slapdash

```bash
pip install aws-slapdash
```

Then copy the path that pip installed the package with command `pip show aws-slapdash`.
This will be needed for next step.

### Step 2: Add commands to Slapdash

Open your slapdash command bar, the default shortcut is `ctrl+j`.
Type in "new command", press enter then select the "Local Command" option.

1. specify the script path by navigating to the path
   you got in the last step and choose the `aws.py` script.
2. Select a name for the command e.g. aws.
3. Optionally choose a keyboard shortcut for the command.

### Step 3: Configure the AWS profile

Run the slapdash command with `ctrl+j` and then executing the command you imported.
Then select configure option by pressing Tab on it, Fill the AWS account and region.

For more info on the Configuration read the configuration section.

## Usage & Configuration

Configuration for all the scripts are under `~/.config/aws_slapdash/config.json`.

There is a configuration script named `configure.py`,
you can import this config to your slapdash and configure from slapdash itself.

### Set AWS Profile & Region

use these keys in the config file(or use the config command):

```json
{
  "profile": "profile_name",
  "region": "region_name"
}
```

### AWS Vault

You can enable the AWS vault integration with setting:

```json
{
  "awsVault": true
}
```

After this the commands will try to switch the profile using AWS vault command.
This means that if you try to execute a command when AWS profile is not set,
The command will try to authenticate with AWS vault and you will be navigated to
AWS for that.
After the first authentication it will work until the tokens expire.

Since AWS vault might asks for your password when you run a command you can
[longer the remember password duration](https://github.com/99designs/aws-vault/blob/master/USAGE.md#keychain)
for AWS vault longer so you don't have to
type it every time.

## Features

Here is a list of supported AWS services.

All of the features are read-only commands, meaning that you cannot
create or destroy something with them,
which keeps you safe from shooting yourself in the foot.

### Cloud Formation

Displays all active cloud formation stacks and their latest status.
Opens the stack page upon select.

### Dynamo DB

Displays all Dynamo DB tables.
Opens the table page upon select.

The following features are available on each table:

- Open Query page for that table
- View and copy: table size, item count

### EC2

Displays all EC2 instances and their current state.

The following features are available on each instance:

- View and copy: Public DNS name - connect with SSH command

### Secrets Manager

Displays all secrets names. Opens the secret page upon select.

The following features are available on each secret:

- Copy: Secret value
- View and Copy: Secret name

### ECS

Displays all ECS clusters. Opens cluster page upon select.

The following features are available on each cluster:

- Create new task
- View any task logs
