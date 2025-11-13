# Detailed Demo Build Guide (Comprehensive Tutorial)

**Welcome!** This guide will walk you through building a complete Okta infrastructure demo using Terraform - even if you've never heard of these tools before.

**⏱️ Time Required:** 2-3 hours (first time)
**📊 Difficulty:** Beginner-friendly (zero experience needed)
**📚 What You'll Learn:** Infrastructure as Code, Terraform basics, Git/GitHub, Command line essentials
**🎯 Best For:** Solutions Engineers, learning deeply, technical discussions

> **⚡ Super Quick (2 min)?** Just want to test this template fast? Copy `QUICKSTART_DEMO.tf.example` → uncomment → deploy! See [Super Quick Template Method](../SIMPLE_DEMO_BUILD_GUIDE.md#super-quick-template-method-new).

> **⚡ Want Quick Demos?** For a fast-track guide focused on AI-assisted demo building (30-45 min), see **[SIMPLE_DEMO_BUILD_GUIDE.md](../SIMPLE_DEMO_BUILD_GUIDE.md)** (assumes QUICKSTART.md completed).

> **📋 Secrets Reference:** This guide covers setting up Okta and AWS credentials. For a complete reference of all required GitHub secrets, see **[SECRETS_SETUP.md](../SECRETS_SETUP.md)**.

> **📚 Need Examples?** Browse `RESOURCE_EXAMPLES.tf` in your terraform directory for copy-paste examples of ALL Okta resource types, or see [terraform/README.md](../environments/myorg/terraform/README.md) for the complete template guide.

---

## 📖 Table of Contents

1. [What You'll Build (And Why It's Cool)](#1-what-youll-build-and-why-its-cool)
2. [Understanding the Basics](#2-understanding-the-basics)
3. [Before You Start - Prerequisites](#3-before-you-start---prerequisites)
4. [Setting Up Your Computer](#4-setting-up-your-computer)
5. [Getting the Code](#5-getting-the-code)
6. [Understanding What You Have](#6-understanding-what-you-have)
7. [Connecting to Okta](#7-connecting-to-okta)
8. [Your First Terraform Commands](#8-your-first-terraform-commands)
9. [Creating Your First Resource](#9-creating-your-first-resource)
10. [Viewing Your Work in Okta](#10-viewing-your-work-in-okta)
11. [Making Changes](#11-making-changes)
12. [Cleaning Up](#12-cleaning-up)
13. [Troubleshooting](#13-troubleshooting)
14. [Next Steps](#14-next-steps)

---

## 1. What You'll Build (And Why It's Cool)

### The End Result

By the end of this guide, you will have:
- ✅ Created Okta users automatically using code
- ✅ Created groups and assigned users to them
- ✅ Set up applications in Okta
- ✅ Made changes and seen them apply instantly
- ✅ Learned how to "undo" everything safely
- ✅ (Advanced) Explored Identity Governance (OIG) features
- ✅ (Optional) Used AI to generate Terraform code in seconds

### Why This Matters for Sales

**Traditional Way (Manual):**
1. Log into Okta Admin Console
2. Click "Add User" for each person
3. Fill out forms manually
4. Repeat 100 times for 100 users
5. Make a mistake? Start over.
6. Want to demo this for another customer? Repeat everything.

**The Terraform Way (Automated):**
1. Write code once describing what you want
2. Run one command
3. Terraform creates everything automatically
4. Need to demo again? Run the same command
5. Made a mistake? Change one line and re-run
6. Want to delete everything? One command.

**Real-World Example:**
Instead of spending 3 hours clicking through screens to set up a demo, you spend 10 minutes running commands. You can set up, tear down, and rebuild demos as many times as you need.

---

## 2. Understanding the Basics

Before we start, let's understand the tools you'll be using.

### What is Infrastructure as Code (IaC)?

**Simple Analogy:**
Think of IaC like a recipe for a cake:
- **Manual way:** You bake a cake, and if you want another one, you have to remember all the steps
- **Recipe way:** You write down the recipe once, and anyone can bake the same cake by following it

Infrastructure as Code is the "recipe" for your IT infrastructure. Instead of clicking buttons, you write down what you want in a file, and the computer builds it for you.

### What is Terraform?

**Terraform** is a tool that reads your "recipes" (code) and builds infrastructure for you.

**What it does:**
- Reads files you write (with a `.tf` extension)
- Talks to Okta (or AWS, Azure, etc.)
- Creates, updates, or deletes resources automatically
- Keeps track of what it created

**What it doesn't do:**
- It doesn't replace Okta
- It doesn't store your data
- It doesn't make decisions for you (you tell it what to do)

### What is Git and GitHub?

**Git** is like "Track Changes" in Microsoft Word, but for code:
- Saves every version of your files
- Lets you go back to earlier versions
- Shows you what changed

**GitHub** is like Google Drive for code:
- Stores your code online
- Lets teams share code
- Keeps backup copies

### What is the Command Line?

The **command line** (also called "terminal" or "bash") is a way to talk to your computer by typing commands instead of clicking.

**Think of it like:**
- Clicking buttons = talking to your computer in pictures
- Command line = talking to your computer in text

Don't worry - we'll explain every command you type!

---

## 3. Before You Start - Prerequisites

### What You Need

#### Required:
1. **A Computer** - Mac, Windows, or Linux
2. **Internet Connection** - To download tools and connect to Okta
3. **An Okta Account** with admin access
   - Ask your team for access to a demo tenant
   - You need "Super Admin" permissions
4. **AWS Account** (for secure state storage)
   - Free tier eligible
   - **Cost:** ~$0.50/month for typical demo usage
   - Stores Terraform state in S3 (not on your computer)
   - Enables team collaboration and automated workflows

#### Nice to Have:
1. **A text editor** - We recommend Visual Studio Code (free)
2. **Patience** - First time always takes longer (that's normal!)

#### About AWS State Storage

**Why AWS?** This demo uses Amazon S3 to store Terraform state files securely:
- ✅ **Team Collaboration:** Multiple people can work on the same demo
- ✅ **State History:** Rollback to previous versions if needed
- ✅ **State Locking:** Prevents conflicts when multiple people make changes
- ✅ **GitHub Actions:** Automated testing and deployment

**Alternative:** You can use local state (files on your computer), but you'll miss out on collaboration features and GitHub Actions workflows. See `docs/AWS_BACKEND_SETUP.md` for migration back to local if needed.

---

## 4. Setting Up Your Computer

We need to install several tools. Don't worry - we'll guide you through each one.

### Step 1: Install a Text Editor (5 minutes)

**What is it?** A program to read and write code files.

**Why do we need it?** To look at and modify the Terraform files.

**How to install:**

1. Go to: https://code.visualstudio.com/
2. Click "Download" for your operating system (Mac/Windows/Linux)
3. Run the installer
4. Click "Next" a few times
5. Done!

**Test it worked:**
- Open Visual Studio Code
- You should see a welcome screen

---

### Step 2: Install Git (10 minutes)

**What is it?** The tool that tracks changes to your files.

#### For Mac Users:

1. Open "Terminal" app:
   - Press `Command + Space`
   - Type "Terminal"
   - Press Enter

2. Type this command and press Enter:
   ```bash
   git --version
   ```

3. If you see a version number, Git is already installed! Skip to Step 3.

4. If not, you'll be prompted to install "Command Line Tools" - click "Install"

#### For Windows Users:

1. Go to: https://git-scm.com/download/win
2. Download the installer
3. Run it and click "Next" for all options (defaults are fine)
4. Restart your computer

**Test it worked:**

1. Open Terminal (Mac) or Git Bash (Windows)
2. Type:
   ```bash
   git --version
   ```
3. You should see something like: `git version 2.39.0`

✅ **Success!** Git is installed.

---

### Step 3: Install AWS CLI (10 minutes)

**What is it?** Command-line tool to interact with AWS services.

**Why do we need it?** To set up S3 storage for Terraform state and verify AWS resources.

#### For Mac Users:

1. Open Terminal
2. Type this command and press Enter:
   ```bash
   curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
   sudo installer -pkg AWSCLIV2.pkg -target /
   ```
3. Enter your Mac password when prompted

#### For Windows Users:

1. Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
2. Download and run the installer
3. Click "Next" through all options
4. Restart your command prompt/terminal

**Test it worked:**

1. Open a new Terminal/Command Prompt
2. Type:
   ```bash
   aws --version
   ```
3. You should see something like: `aws-cli/2.15.0 Python/3.11.6`

✅ **Success!** AWS CLI is installed.

#### Configure AWS Credentials

After AWS backend infrastructure is deployed (see Section 7.5), you'll need AWS credentials.

**Getting Your AWS Credentials (Using AWS Console/GUI):**

1. **Sign in to AWS Console**
   - Go to: https://console.aws.amazon.com/
   - Sign in with your AWS account
   - (Don't have AWS? Create free account at: https://aws.amazon.com/free/)

2. **Navigate to IAM (Identity and Access Management)**
   - In the search bar at the top, type: `IAM`
   - Click **IAM** from the results
   - Or go directly to: https://console.aws.amazon.com/iam/

3. **Create Access Keys**
   - Click **Users** in the left sidebar
   - Click on your username (or create a user if needed)
   - Click the **Security credentials** tab
   - Scroll down to **Access keys** section
   - Click **Create access key**
   - Select use case: **Command Line Interface (CLI)**
   - Check the box: "I understand the above recommendation"
   - Click **Next**
   - (Optional) Add description tag: "Terraform Local Development"
   - Click **Create access key**

4. **Save Your Credentials** ⚠️ IMPORTANT!
   - You'll see:
     - **Access key ID** (starts with `AKIA...`)
     - **Secret access key** (long random string)
   - Click **Download .csv file** (recommended)
   - Or copy both values to a secure note
   - ⚠️ You can NEVER see the secret again after closing this page!

5. **Configure AWS CLI**
   ```bash
   aws configure
   # Paste your values when prompted:
   # AWS Access Key ID: AKIAIOSFODNN7EXAMPLE
   # AWS Secret Access Key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
   # Default region name: us-east-1
   # Default output format: json
   ```

6. **Test It Works**
   ```bash
   aws sts get-caller-identity
   # Should show your AWS account ID and user info
   ```

✅ **Success!** AWS CLI is configured with your credentials.

**Security Note:** These credentials give access to your AWS account. Keep them secure:
- ✅ Store in password manager
- ✅ Don't commit to Git
- ✅ Don't share with others
- ❌ Never post online or in screenshots

**Note:** For GitHub Actions, we'll use OIDC (no credentials stored in GitHub), but you need local credentials for the initial infrastructure setup.

---

### Step 4: Install Terraform (10 minutes)

**What is it?** The tool that reads your code and talks to Okta.

#### For Mac Users:

1. Open Terminal

2. First, install Homebrew (a tool installer for Mac):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
   - This might take 5-10 minutes
   - You'll need to type your computer password

3. Install Terraform:
   ```bash
   brew install terraform
   ```

#### For Windows Users:

1. Go to: https://www.terraform.io/downloads
2. Download "Windows 386" or "Windows AMD64" (most common)
3. Unzip the downloaded file
4. Move `terraform.exe` to `C:\Windows\System32\`
5. Restart Git Bash

#### For Linux Users:

```bash
wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
sudo apt update && sudo apt install terraform
```

**Test it worked:**

```bash
terraform version
```

You should see: `Terraform v1.9.x` (or higher)

✅ **Success!** Terraform is installed.

---

### Step 4: Install Python (5 minutes)

**What is it?** A programming language (we use it for some helper scripts).

#### For Mac Users:

Python is usually pre-installed. Check:

```bash
python3 --version
```

If you see a version number like `Python 3.x.x`, you're good!

If not:
```bash
brew install python3
```

#### For Windows Users:

1. Go to: https://www.python.org/downloads/
2. Download Python 3.11 or higher
3. Run installer
4. **IMPORTANT:** Check "Add Python to PATH" during installation
5. Click "Install Now"

**Test it worked:**

```bash
python3 --version
```

✅ **Success!** Python is installed.

---

### Step 5: Set Up GitHub Account (5 minutes)

**What is it?** A website where the demo code lives.

1. Go to: https://github.com/
2. Click "Sign Up" (if you don't have an account)
3. Follow the prompts to create your account
4. Remember your username and password!

✅ **Success!** GitHub account ready.

---

## 5. Getting the Code

Now we'll download the demo code to your computer.

### Understanding What We're Doing

We're going to "clone" (make a copy of) the demo code from GitHub to your computer.

**Think of it like:**
- The code on GitHub = The original recipe book in a library
- Cloning = Making your own copy to take home
- Your computer = Your kitchen where you'll use the recipe

### Step-by-Step: Clone the Repository

**"Repository" = A folder that contains all the code**

1. **Open your Terminal or Git Bash**

2. **Navigate to where you want to put the code**

   Let's put it in your home folder:
   ```bash
   cd ~
   ```

   **What this means:**
   - `cd` = "change directory" (go to a folder)
   - `~` = your home folder

3. **Clone the repository:**

   ```bash
   git clone https://github.com/joevanhorn/okta-terraform-complete-demo.git
   ```

   **What this does:**
   - Downloads all the code to your computer
   - Creates a folder called `okta-terraform-complete-demo`

   **You should see:**
   ```
   Cloning into 'okta-terraform-complete-demo'...
   remote: Counting objects: 100% (500/500), done.
   remote: Compressing objects: 100% (300/300), done.
   Receiving objects: 100% (500/500), 1.5 MiB | 2.5 MiB/s, done.
   ```

4. **Go into the folder:**

   ```bash
   cd okta-terraform-complete-demo
   ```

5. **Look at what's inside:**

   ```bash
   ls
   ```

   **You should see folders like:**
   - `environments/`
   - `scripts/`
   - `docs/`
   - `.github/`

✅ **Success!** You have the code on your computer.

---

## 6. Understanding What You Have

Let's take a tour of what you downloaded.

### Open the Folder in Visual Studio Code

1. In your terminal, type:
   ```bash
   code .
   ```

   **What this does:** Opens Visual Studio Code with the current folder

   If that doesn't work, you can:
   - Open Visual Studio Code manually
   - Click File → Open Folder
   - Select `okta-terraform-complete-demo`

### The Folder Structure

You'll see this on the left side:

```
okta-terraform-complete-demo/
├── environments/          ← Different Okta setups
│   └── myorg/    ← The demo we'll use
│       ├── terraform/    ← The Terraform code files
│       ├── imports/      ← Data imported from Okta
│       └── config/       ← Configuration files
├── scripts/              ← Helper scripts
├── docs/                 ← Documentation (guides like this)
└── testing/              ← Test plans
```

**Think of it like:**
- `environments/` = Different "recipes" for different situations
- `myorg/` = The specific recipe we're using today
- `terraform/` = The actual recipe instructions
- `docs/` = The cookbook with explanations

**🔒 Important - Environment Isolation:**
Each `environments/` subdirectory represents a **separate Okta organization**. Never mix resources from different Okta orgs in the same environment directory. This ensures:
- Clean separation between demo, staging, and production
- No accidental changes to the wrong Okta org
- Each environment uses its own GitHub secrets

### Key Files to Know

In `environments/myorg/terraform/`, you'll find:

- **`provider.tf`** - Tells Terraform to talk to Okta (version 6.4.0+ required)
- **`variables.tf`** - Settings you can customize
- **`oig_entitlements.tf`** - OIG (Identity Governance) resources

**For this demo**, you'll create example files like:
- **`user.tf`** - Example code to create users
- **`group.tf`** - Example code to create groups
- **`app_oauth.tf`** - Example code to create applications

**Note:** The actual myorg environment may have different files depending on what's been imported. For learning purposes, you'll create these example files.

---

## 7. Connecting to Okta

Before Terraform can create anything, it needs to know:
1. **Which Okta organization** to connect to
2. **Permission** to make changes (via an API token)

### Step 1: Get Your Okta Details

You need three pieces of information:

1. **Org Name** - Example: `dev-12345678`
2. **Base URL** - Example: `okta.com` (or `oktapreview.com`)
3. **API Token** - A secret key that lets Terraform make changes

#### Finding Your Org Name:

1. Log into Okta Admin Console
2. Look at the URL in your browser
3. It looks like: `https://dev-12345678.okta.com/admin`
4. Your org name is: `dev-12345678`

#### Finding Your Base URL:

Look at the URL again:
- If it ends in `.okta.com` → Base URL is `okta.com`
- If it ends in `.oktapreview.com` → Base URL is `oktapreview.com`

#### Creating an API Token:

1. In Okta Admin Console, go to **Security → API**
2. Click the **Tokens** tab
3. Click **Create Token**
4. Give it a name: `Terraform Demo Token`
5. Click **Create Token**
6. **IMPORTANT:** Copy the token value that appears
   - It looks like: `00H_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789`
   - **You'll only see this once!** Save it somewhere safe
   - Don't share it with anyone

### Step 2: Create Your Configuration File

Now we'll create a file with your Okta details.

1. In Visual Studio Code, navigate to: `environments/myorg/terraform/`

2. Look for a file called `terraform.tfvars.example`

3. Right-click on it and select "Duplicate"

4. Rename the duplicate to: `terraform.tfvars` (remove `.example`)

5. Open `terraform.tfvars` and you'll see:

   ```hcl
   # Okta Configuration
   okta_org_name  = "your-org-name"
   okta_base_url  = "okta.com"
   okta_api_token = "your-api-token-here"
   ```

6. Replace the values with yours:

   ```hcl
   okta_org_name  = "dev-12345678"
   okta_base_url  = "oktapreview.com"
   okta_api_token = "00H_aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789"
   ```

7. **Save the file** (Command+S on Mac, Ctrl+S on Windows)

### Step 3: Verify the File is Ignored by Git

**Important Security Note:** We don't want to accidentally share our API token!

1. Open the file called `.gitignore` (in the root folder)

2. Look for this line:
   ```
   terraform.tfvars
   ```

3. If you see it, great! This means Git will ignore this file and won't upload it anywhere.

✅ **Success!** You're connected to Okta.

---

## 7.5. Setting Up AWS Backend (One-Time Setup)

Before you can use Terraform, you need to set up AWS to store the Terraform state files.

**What is State?** Terraform keeps track of what it created in a "state file" - think of it as Terraform's memory. We store this in AWS S3 instead of your computer so your team can collaborate.

### Step 1: Deploy AWS Backend Infrastructure

This creates the S3 bucket and DynamoDB table for state storage:

```bash
# Navigate to the aws-backend directory
cd ~/okta-terraform-complete-demo/aws-backend

# Initialize Terraform (one-time)
terraform init

# See what will be created
terraform plan
# You should see: S3 bucket, DynamoDB table, IAM roles

# Create the infrastructure
terraform apply
# Type "yes" when prompted
```

**What this creates:**
- S3 bucket: `okta-terraform-demo` (stores state files)
- DynamoDB table: `okta-terraform-state-lock` (prevents conflicts)
- IAM role: `GitHubActions-OktaTerraform` (for GitHub workflows)
- OIDC provider: For secure GitHub authentication

**Time:** 2-3 minutes

### Step 2: Save the AWS Role ARN

After `terraform apply` completes, you'll see outputs. Save this value:

```bash
# Copy this value - you'll need it for GitHub
terraform output github_actions_role_arn

# Example output:
# arn:aws:iam::123456789012:role/GitHubActions-OktaTerraform
```

**Write this down** or save it in a note - you'll use it in the next step!

### Step 3: Configure GitHub Secret

Now tell GitHub how to authenticate with AWS:

1. Go to your GitHub repository: https://github.com/YOUR_USERNAME/okta-terraform-complete-demo
2. Click **Settings** (top right)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret**
5. **Name:** `AWS_ROLE_ARN`
6. **Value:** Paste the ARN from Step 2
7. Click **Add secret**

✅ **Done!** GitHub can now authenticate with AWS securely (no passwords stored!)

### Understanding What You Did

You just created a secure, production-ready backend:
- ✅ State files stored in S3 (encrypted, versioned)
- ✅ State locking via DynamoDB (prevents conflicts)
- ✅ GitHub Actions can deploy automatically (via OIDC)
- ✅ Team members can collaborate safely

**Cost:** ~$0.50/month for typical demo usage

### Step 4: Verify in AWS Console (Optional but Recommended)

Want to see what was created? Let's look in the AWS Console:

#### View S3 Bucket (Where State Files Live)

1. **Go to S3 Console**
   - Navigate to: https://console.aws.amazon.com/s3/
   - Or search "S3" in the AWS Console search bar

2. **Find Your Bucket**
   - Look for bucket named: `okta-terraform-demo`
   - Click on the bucket name

3. **Explore the Bucket**
   - You should see:
     - **Versioning:** Enabled (shown at top)
     - **Encryption:** Enabled (shown in Properties tab)
   - The bucket might be empty now (state files created when you run Terraform)
   - After running Terraform, you'll see: `Okta-GitOps/myorg/terraform.tfstate`

**Screenshot Tip:** Take a screenshot of your empty bucket - you can compare it later after Terraform runs!

#### View DynamoDB Table (State Locking)

1. **Go to DynamoDB Console**
   - Navigate to: https://console.aws.amazon.com/dynamodb/
   - Or search "DynamoDB" in the AWS Console

2. **Find Your Table**
   - Click **Tables** in the left sidebar
   - Look for table named: `okta-terraform-state-lock`
   - Click on the table name

3. **Explore the Table**
   - Click **Explore table items** button
   - Should be empty (locks only appear during Terraform operations)
   - Click **Additional info** to see:
     - **Billing mode:** On-demand (pay per use)
     - **Encryption:** Enabled

**What This Table Does:** When someone runs Terraform, a lock record appears here temporarily. This prevents two people from making changes at the same time.

#### View IAM Role (GitHub Actions Authentication)

1. **Go to IAM Console**
   - Navigate to: https://console.aws.amazon.com/iam/
   - Or search "IAM" in the AWS Console

2. **Find the Role**
   - Click **Roles** in the left sidebar
   - Search for: `GitHubActions-OktaTerraform`
   - Click on the role name

3. **Explore the Role**
   - **Trust relationships** tab shows:
     - Trusted entity: `token.actions.githubusercontent.com`
     - Condition: Your repository name
   - **Permissions** tab shows:
     - Access to S3 bucket
     - Access to DynamoDB table

**What This Role Does:** GitHub Actions assumes this role (temporarily becomes this role) to access your S3 bucket and DynamoDB table. No long-term credentials needed!

✅ **Great!** Now you understand what infrastructure supports your Terraform state.

**Next:** You can now use Terraform with confidence that your state is safe!

---

## 8. Your First Terraform Commands

Now the fun part - actually using Terraform!

### Step 1: Navigate to the Terraform Folder

In your terminal:

```bash
cd ~/okta-terraform-complete-demo/environments/myorg/terraform
```

**What this does:** Goes to the folder with the Terraform code

### Step 2: Initialize Terraform

Type this command:

```bash
terraform init
```

**What this does:**
- Downloads the Okta plugin for Terraform
- Sets up Terraform to work in this folder
- Creates a `.terraform` folder with necessary files

**You should see:**
```
Initializing the backend...

Initializing provider plugins...
- Finding okta/okta versions matching ">= 6.4.0"...
- Installing okta/okta v6.4.x...
- Installed okta/okta v6.4.x

Terraform has been successfully initialized!
```

✅ **Success!** Terraform is ready to use.

**Note:** Provider version 6.4.0+ is required for OIG (Identity Governance) features.

**If you see errors:** Check the [Troubleshooting](#13-troubleshooting) section

### Step 3: Preview What Terraform Will Do

Before creating anything, let's see what Terraform wants to do:

```bash
terraform plan
```

**What this does:**
- Reads all the `.tf` files
- Compares them to what exists in Okta
- Shows you what it would create/change/delete

**You should see:**
```
Terraform will perform the following actions:

  # okta_user.john_doe will be created
  + resource "okta_user" "john_doe" {
      + email      = "john.doe@example.com"
      + first_name = "John"
      + last_name  = "Doe"
      ...
    }

Plan: 15 to add, 0 to change, 0 to destroy.
```

**Understanding the output:**
- `+` means CREATE (green)
- `~` means CHANGE (yellow)
- `-` means DELETE (red)
- The number at the end (`Plan: 15 to add`) tells you how many resources

**Don't worry!** Nothing has been created yet. This is just a preview.

---

## 9. Creating Your First Resource

Now let's actually create something in Okta!

### Understanding What We're Creating

Look at the file `user.tf`:

```hcl
resource "okta_user" "john_doe" {
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"
}
```

**Breaking this down:**
- `resource` = "I want to create something"
- `"okta_user"` = The type of thing (an Okta user)
- `"john_doe"` = A name for this resource (just for Terraform's reference)
- Everything in `{ }` = The details (email, name, etc.)

**Think of it like filling out a form:**
- Email: john.doe@example.com
- First Name: John
- Last Name: Doe

### Step 1: Create the Resources

Run this command:

```bash
terraform apply
```

**What happens:**
1. Terraform shows you the plan again
2. It asks: "Do you want to perform these actions?"
3. You type: `yes`
4. Terraform creates everything

**You should see:**
```
Do you want to perform these actions?
  Terraform will perform the actions described above.
  Only 'yes' will be accepted to approve.

  Enter a value:
```

**Type:** `yes` and press Enter

**You should then see:**
```
okta_user.john_doe: Creating...
okta_user.john_doe: Creation complete after 2s [id=00u1234567890]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

✅ **Success!** You just created a user in Okta using code!

**What just happened:**
1. Terraform read your code
2. It talked to Okta's API
3. It created the user
4. It saved information about what it created in a file called `terraform.tfstate`

---

## 10. Viewing Your Work in Okta

Let's verify that Terraform actually created the user.

### Step 1: Open Okta Admin Console

1. Go to your Okta admin URL (e.g., `https://dev-12345678.okta.com/admin`)
2. Log in

### Step 2: Find the User

1. Click **Directory** in the left menu
2. Click **People**
3. Look for "John Doe" (or search for `john.doe@example.com`)

**You should see:**
- Name: John Doe
- Email: john.doe@example.com
- Status: Active (or Staged)

✅ **Success!** The user you created with code is really in Okta!

### Cool Things to Notice

1. **You didn't click anything** - Terraform did it for you
2. **You can do this again** - Run the same command on a different Okta org
3. **It's documented** - The `.tf` file shows exactly what was created

---

## 11. Making Changes

Now let's modify our user and see how Terraform handles changes.

### Step 1: Edit the Code

1. Open `user.tf` in Visual Studio Code

2. Find the John Doe user:
   ```hcl
   resource "okta_user" "john_doe" {
     email      = "john.doe@example.com"
     first_name = "John"
     last_name  = "Doe"
     login      = "john.doe@example.com"
   }
   ```

3. Let's add a department. Change it to:
   ```hcl
   resource "okta_user" "john_doe" {
     email      = "john.doe@example.com"
     first_name = "John"
     last_name  = "Doe"
     login      = "john.doe@example.com"
     department = "Engineering"  ← Add this line
   }
   ```

4. **Save the file**

### Step 2: Preview the Change

```bash
terraform plan
```

**You should see:**
```
  # okta_user.john_doe will be updated in-place
  ~ resource "okta_user" "john_doe" {
        email      = "john.doe@example.com"
      + department = "Engineering"
        first_name = "John"
        ...
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```

**Notice:**
- `~` means "update" (not delete and recreate)
- `+ department` shows it's adding the department field
- `1 to change` means only updating one resource

### Step 3: Apply the Change

```bash
terraform apply
```

Type `yes` when prompted.

**You should see:**
```
okta_user.john_doe: Modifying... [id=00u1234567890]
okta_user.john_doe: Modifications complete after 1s

Apply complete! Resources: 0 added, 1 changed, 0 destroyed.
```

### Step 4: Verify in Okta

1. Go back to Okta Admin Console
2. Open John Doe's user profile
3. Look for the "Department" field
4. It should now say: "Engineering"

✅ **Success!** You modified a user using code!

---

## 12. Cleaning Up

When you're done with your demo, you can delete everything Terraform created.

### The Easy Way to Delete Everything

Run this command:

```bash
terraform destroy
```

**What this does:**
- Looks at what Terraform created (stored in `terraform.tfstate`)
- Deletes all of it from Okta

**You'll see:**
```
Plan: 0 to add, 0 to change, 15 to destroy.

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value:
```

**Type:** `yes`

**You should see:**
```
okta_user.john_doe: Destroying... [id=00u1234567890]
okta_user.john_doe: Destruction complete after 1s

Destroy complete! Resources: 15 destroyed.
```

### Verify in Okta

1. Go to Okta Admin Console → Directory → People
2. John Doe should be gone

**Important Notes:**
- This only deletes things **Terraform created**
- It won't delete things you created manually in Okta
- You can run `terraform apply` again to recreate everything

✅ **Success!** Clean demo environment.

---

## 13. Troubleshooting

### Problem: "terraform: command not found"

**What it means:** Terraform isn't installed or isn't in your PATH

**Solution:**
1. Reinstall Terraform (see [Step 3](#step-3-install-terraform-10-minutes))
2. Restart your terminal
3. Try again

---

### Problem: "Error: Invalid provider configuration"

**What it means:** Your `terraform.tfvars` file has issues

**Solution:**
1. Check that `terraform.tfvars` exists in `environments/myorg/terraform/`
2. Verify all three values are filled in:
   - `okta_org_name`
   - `okta_base_url`
   - `okta_api_token`
3. Make sure there are no extra spaces or quotes

---

### Problem: "Error: 401 Unauthorized"

**What it means:** Your API token is wrong or expired

**Solution:**
1. Go to Okta Admin Console → Security → API → Tokens
2. Create a new API token
3. Update `terraform.tfvars` with the new token
4. Try again

---

### Problem: "Error: Insufficient permissions"

**What it means:** Your API token doesn't have permission to create users

**Solution:**
1. Make sure you're using a Super Admin account
2. Create a new API token from a Super Admin account
3. Update `terraform.tfvars`

---

### Problem: Changes not showing in Okta

**Solution:**
1. Refresh the Okta Admin Console page
2. Run `terraform plan` to see if Terraform knows about the change
3. Check if you saved the `.tf` file

---

### Problem: "Error: Duplicate resource"

**What it means:** You're trying to create something that already exists

**Solution:**
1. Run `terraform destroy` to clean up
2. Or manually delete the conflicting resource in Okta
3. Run `terraform apply` again

---

## 14. Next Steps

Congratulations! You've learned the basics of Infrastructure as Code and Terraform!

### What You Accomplished

- ✅ Installed developer tools
- ✅ Downloaded code from GitHub
- ✅ Connected Terraform to Okta
- ✅ Created resources automatically
- ✅ Modified resources using code
- ✅ Cleaned up when done

### Continue Learning

#### Level 2: Create Your Own Resource

Try creating a new user:

1. Open `user.tf`
2. Add a new user block:
   ```hcl
   resource "okta_user" "your_name" {
     email      = "yourname@example.com"
     first_name = "Your"
     last_name  = "Name"
     login      = "yourname@example.com"
     department = "Sales"
   }
   ```
3. Run `terraform plan` to preview
4. Run `terraform apply` to create
5. Check Okta to verify

#### Level 3: Create a Group

1. Open `group.tf`
2. Add a new group:
   ```hcl
   resource "okta_group" "demo_team" {
     name        = "Demo Team"
     description = "Team for product demos"
   }
   ```
3. Apply it with Terraform
4. Verify in Okta

#### Level 4: Import Existing Resources

Learn how to bring existing Okta resources under Terraform management:
- See: `docs/TERRAFORM_RESOURCES.md`
- Section: "Use Case 1: Import Existing Infrastructure"

#### Level 5: Advanced - Identity Governance (OIG)

**What is OIG?**

OIG (Okta Identity Governance) helps you manage who has access to what in your organization. Think of it like:
- A security guard keeping track of who has keys to different rooms
- Automatically reviewing if people still need their access
- Organizing access permissions into bundles (like "Marketing Access" or "Engineering Tools")

**Key Concepts:**

1. **Entitlement Bundles** - Packages of access rights
   - Example: "Marketing Bundle" might include access to HubSpot, Salesforce, and Google Analytics
   - Instead of assigning 3 apps individually, assign 1 bundle

2. **Access Reviews** - Scheduled checkups
   - Periodically asks: "Does John still need admin access?"
   - Managers review and approve/revoke access

3. **Resource Owners** - Who's responsible for what
   - Every app/group has an owner
   - Owners get notified about access requests

4. **Governance Labels** - Tag and categorize resources
   - Example: Label sensitive apps as "Privileged" or "Crown Jewel"
   - Use labels to filter resources in access reviews
   - Managed via GitOps workflow (see below)

**Hands-On: Working with OIG Resources**

This repository includes automated workflows for importing OIG resources:

1. **View Entitlement Bundles:**
   ```bash
   cd environments/myorg/imports
   cat entitlements.json | head -20
   ```

   **What you'll see:** JSON data listing all entitlement bundles from Okta

2. **See the Terraform Configuration:**
   ```bash
   cd ../terraform
   cat oig_entitlements.tf | head -30
   ```

   **What this is:** Terraform code that manages entitlement bundles

3. **Import OIG Resources Automatically:**

   This repo has GitHub Actions workflows that automatically:
   - Connect to your Okta tenant
   - Export all entitlement bundles
   - Generate Terraform configuration
   - Keep everything in sync

   See: `.github/workflows/import-all-resources.yml` (replaces archived import workflows)

**Example: Creating an Entitlement Bundle**

```hcl
resource "okta_entitlement_bundle" "marketing_bundle" {
  name        = "Marketing Access Bundle"
  description = "Access to all marketing tools"
}
```

**What happens:**
1. Terraform creates the bundle in Okta
2. You can assign apps to this bundle in the Okta Admin Console
3. Users who get this bundle automatically get all apps in it

**Why This Matters for Sales:**

Traditional demo:
- "And here's how you manually assign 10 apps to a new marketing employee..."
- Customer: "That seems tedious"

OIG demo:
- "Watch me assign one bundle and the employee gets all 10 apps instantly"
- "Plus, we automatically review their access every quarter"
- Customer: "That's amazing! How much time does this save?"

**Next Steps with OIG:**
- Review the OIG validation plan: `testing/MANUAL_VALIDATION_PLAN.md` (Section 5)
- Explore all OIG resources: `docs/TERRAFORM_RESOURCES.md` (OIG section)
- Learn about resource owners and governance labels in the main docs

**Important Notes:**
- OIG requires Okta Identity Governance license
- Some OIG features are API-only (can't be managed in Terraform)
- This repo handles those with Python scripts in `scripts/`

**GitOps Workflow for Labels (NEW):**

This repository uses a modern GitOps approach for managing governance labels:

**The Old Way (Manual):**
1. Log into Okta Admin Console
2. Navigate to Identity Governance → Labels
3. Manually create labels and assign to resources
4. Repeat for every change
5. No audit trail, no version control

**The GitOps Way (Automated):**
1. Edit `environments/myorg/config/label_mappings.json`
2. Create a Pull Request
3. Automatic validation runs (syntax and ORN format check)
4. Merge to main → Automatic dry-run shows what will change
5. Manual approval → Apply labels to Okta
6. Complete audit trail in Git

**How to Use the Label GitOps Workflow:**

1. **View Current Labels:**
   ```bash
   cat environments/myorg/config/label_mappings.json | jq '.labels'
   ```

2. **Add a New Label Assignment:**
   ```bash
   # Edit the configuration file
   vim environments/myorg/config/label_mappings.json

   # Example: Add "Privileged" label to an app
   # Under "assignments" → "apps" → "Privileged", add the app ORN:
   # "orn:okta:idp:myorg:apps:oauth2:0oa123456789"
   ```

3. **Create Pull Request with Your Changes:**
   ```bash
   git checkout -b feature/add-privileged-label
   git add environments/myorg/config/label_mappings.json
   git commit -m "feat: Label CRM app as Privileged"
   git push -u origin feature/add-privileged-label

   gh pr create --title "Add Privileged label to CRM app" \
     --body "Marking the CRM application as privileged for governance"
   ```

4. **Automatic PR Validation:**
   - GitHub Actions runs `validate-label-mappings.yml` workflow
   - Validates JSON syntax (no syntax errors)
   - Validates ORN formats (all start with `orn:`)
   - Posts validation results as PR comment
   - NO Okta API calls needed (syntax check only)

5. **Review and Merge:**
   - Review the validation results
   - Get approval from teammate
   - Merge PR to main

6. **Automatic Dry-Run:**
   - On merge to main, `myorg-apply-labels-from-config.yml` runs
   - Automatically runs in **dry-run mode** (no changes made)
   - Connects to Okta API and validates labels exist
   - Shows what would be created/assigned
   - Posts results to workflow summary

7. **Manual Apply:**
   ```bash
   # After reviewing dry-run results, manually trigger apply
   gh workflow run apply-labels-from-config.yml \
     -f environment=myorg \
     -f dry_run=false
   ```

**Why This Matters:**

Traditional way:
- "Let me log into Okta and manually label 20 apps..."
- No history of what changed or why
- Easy to miss apps or make mistakes
- Customer: "How do you track governance changes?"

GitOps way:
- "All label changes go through code review"
- Complete audit trail in Git
- Automated validation catches errors before they reach Okta
- Customer: "Wow, infrastructure as code for governance labels!"

**Try It Now:**

1. View the current label configuration
2. Add the "Privileged" label to a test app
3. Create a PR and watch the validation run
4. Merge and see the automatic dry-run
5. Apply the changes to Okta

#### Level 6: AI-Assisted Demo Building (Optional - Speed Boost!)

**What is AI-Assisted Generation?**

Instead of writing Terraform code by hand, you can describe what you want in plain English, and an AI assistant (like Gemini, ChatGPT, or Claude) will write the code for you.

**Think of it like:**
- Manual way: You write every line of code yourself (slow, error-prone)
- AI way: You tell the AI what you want, it writes the code (fast, accurate)

**Real Example:**

Instead of typing out this Terraform code:
```hcl
resource "okta_user" "john_doe" {
  email      = "john.doe@example.com"
  first_name = "John"
  last_name  = "Doe"
  login      = "john.doe@example.com"
  status     = "ACTIVE"
}
# ... repeat 49 more times for 50 users
```

You simply tell the AI:
```
"Create 50 users across Engineering, Marketing, and Sales departments
with realistic names and appropriate titles"
```

And the AI generates all 50 user resources in seconds!

**Two Ways to Use AI:**

1. **Beginner-Friendly (Manual Mode):**
   - Open Gemini/ChatGPT/Claude in your browser
   - Copy/paste prompt templates from this repo
   - AI generates code
   - You copy code to your Terraform files
   - **Time:** ~5 minutes to create a full demo

2. **Advanced (CLI Tool):**
   - Install Python tool from this repo
   - Run one command
   - AI automatically generates and saves code
   - **Time:** ~1-2 minutes to create a full demo

**Step-by-Step: Beginner Mode**

1. **Open the AI Assistant Tool:**
   - Gemini: https://gemini.google.com/ (most users prefer this)
   - ChatGPT: https://chat.openai.com/
   - Claude: https://claude.ai/

2. **Give the AI Context:**

   Copy and paste these files into the AI chat:
   - `ai-assisted/context/repository_structure.md`
   - `ai-assisted/context/terraform_examples.md`
   - `ai-assisted/context/okta_resource_guide.md`

   **Why?** This teaches the AI how your repository works and what patterns to follow.

3. **Use a Prompt Template:**

   Open `ai-assisted/prompts/create_demo_environment.md` and fill in what you want:

   Example:
   ```
   Create a demo for a SaaS company.

   USERS:
   - Jane Smith (Engineering Manager)
   - 3 engineers
   - Bob Jones (Marketing Manager)
   - 2 marketing team members

   GROUPS:
   - Engineering Team
   - Marketing Team

   APPS:
   - GitHub (for Engineering)
   - Salesforce (for Marketing)
   ```

4. **Paste Your Prompt:**

   Copy your filled-out prompt and paste it into the AI chat.

5. **Get Your Code:**

   The AI will generate complete, ready-to-use Terraform files:
   - users.tf
   - groups.tf
   - apps.tf
   - etc.

6. **Copy to Your Environment:**

   ```bash
   cd environments/myorg/terraform

   # Paste generated users.tf content into users.tf
   # Paste generated groups.tf content into groups.tf
   # etc.
   ```

7. **Validate and Apply:**

   ```bash
   terraform fmt
   terraform validate
   terraform plan
   terraform apply
   ```

**Real-World Time Savings:**

| Task | Manual Coding | With AI | Time Saved |
|------|---------------|---------|------------|
| Create 5 users | 15 minutes | 2 minutes | 13 minutes (87%) |
| Full demo (users + groups + apps) | 45 minutes | 5 minutes | 40 minutes (89%) |
| Add OIG bundles | 20 minutes | 3 minutes | 17 minutes (85%) |

**Available Prompt Templates:**

This repository includes ready-to-use prompts:

- **Complete Demo:** `ai-assisted/prompts/create_demo_environment.md`
  - Full environment with users, groups, apps
  - Perfect for customer demos

- **Add Users:** `ai-assisted/prompts/add_users.md`
  - Quickly add more users to existing setup
  - Great for scaling demos

- **Create App:** `ai-assisted/prompts/create_app.md`
  - OAuth/OIDC applications
  - SAML integrations

- **OIG Setup:** `ai-assisted/prompts/oig_setup.md`
  - Entitlement bundles
  - Access reviews
  - Governance features

**Advanced: CLI Tool**

If you're comfortable with command line:

```bash
# Install (one time)
pip install google-generativeai

# Set API key (get from https://aistudio.google.com/app/apikey)
export GEMINI_API_KEY="your-key-here"

# Generate interactively
cd ai-assisted
python generate.py --interactive --provider gemini

# Or generate directly
python generate.py \
  --prompt "Create 10 marketing users and a Salesforce app" \
  --provider gemini \
  --output ../environments/myorg/terraform/marketing.tf
```

**Why This Matters for Sales:**

**Traditional Demo Prep:**
- "I need 2 hours to build this demo environment"
- "Let me manually type out all these users..."
- Customer: "Can you add 5 more users?" → 15 more minutes

**With AI-Assisted:**
- "Give me 5 minutes, I'll have the complete demo ready"
- Ask AI to generate everything
- Customer: "Can you add 5 more users?" → 30 seconds with AI

**This is a game-changer for:**
- Last-minute customer requests
- Quick POC environments
- Scaling demos up/down
- Testing different scenarios

**Try It Now:**

1. Go to https://gemini.google.com/
2. Copy and paste the context files from `ai-assisted/context/`
3. Try the prompt: "Create 3 users named Alice, Bob, and Charlie in Engineering department"
4. See the magic happen!

**Full Documentation:**
- `ai-assisted/README.md` - Complete guide to AI-assisted generation
- `ai-assisted/examples/example_session_gemini.md` - Real example session

### Resources for Learning More

**Terraform:**
- [Official Terraform Tutorial](https://learn.hashicorp.com/terraform)
- [Terraform Documentation](https://www.terraform.io/docs)

**Okta Terraform Provider:**
- [Provider Documentation](https://registry.terraform.io/providers/okta/okta/latest/docs)
- [Complete Resource Guide](../docs/TERRAFORM_RESOURCES.md)

**Git and GitHub:**
- [GitHub Hello World Guide](https://guides.github.com/activities/hello-world/)
- [Git Basics](https://git-scm.com/book/en/v2/Getting-Started-Git-Basics)

**Command Line:**
- [Command Line Crash Course](https://developer.mozilla.org/en-US/docs/Learn/Tools_and_testing/Understanding_client-side_tools/Command_line)

### Practice Ideas

1. **Build a complete demo environment:**
   - 10 users in different departments
   - 5 groups (Engineering, Sales, Marketing, IT, HR)
   - Assign users to groups
   - Create 2-3 applications

2. **Test disaster recovery:**
   - Build everything with `terraform apply`
   - Destroy it with `terraform destroy`
   - Rebuild it in under 5 minutes
   - Show customers how fast you can recover

3. **Multi-environment demos:**
   - Create separate environments for different demo scenarios
   - Keep them as code
   - Spin up the right one for each customer

### Getting Help

**If you get stuck:**

1. **Check the Troubleshooting section** (above)
2. **Review the validation plan:** `testing/MANUAL_VALIDATION_PLAN.md`
3. **Read the full docs:** `docs/` folder
4. **Ask your team** - Someone has probably seen the issue before
5. **Check official docs** - Terraform and Okta have great documentation

### Share Your Success

When you successfully build your first demo:
1. Take a screenshot of the Terraform output
2. Take a screenshot of the resources in Okta
3. Share with your team!

---

## Appendix: Quick Reference Commands

### Essential Terraform Commands

```bash
# Initialize Terraform (first time only)
terraform init

# See what Terraform will do (preview)
terraform plan

# Create/update resources
terraform apply

# Delete everything Terraform created
terraform destroy

# Check if your code is valid
terraform validate

# Format your code nicely
terraform fmt

# Show current state
terraform show
```

### Essential Git Commands

```bash
# Download code from GitHub
git clone <url>

# See what changed
git status

# Update your code from GitHub
git pull
```

### Essential Terminal Commands

```bash
# Go to a folder
cd folder-name

# Go to home folder
cd ~

# Go up one level
cd ..

# List files in current folder
ls

# Show current folder path
pwd

# Clear the screen
clear
```

---

## Glossary

**Apply** - Tell Terraform to make the changes (create/update/delete resources)

**API Token** - A secret key that gives Terraform permission to change Okta

**Clone** - Make a copy of code from GitHub to your computer

**Destroy** - Delete all resources that Terraform created

**Infrastructure as Code (IaC)** - Managing IT infrastructure using code files instead of manual processes

**Initialize** - Set up Terraform in a folder (download plugins, etc.)

**Plan** - Preview what Terraform will do without actually doing it

**Provider** - A plugin that lets Terraform talk to a service (Okta, AWS, etc.)

**Repository (Repo)** - A folder containing code, tracked by Git

**Resource** - Something Terraform manages (a user, group, app, etc.)

**State** - Terraform's memory of what it created (stored in `terraform.tfstate`)

**Terraform** - Tool that reads code and creates infrastructure

**Terminal** - Program where you type commands (also called "command line" or "bash")

---

**Congratulations on completing the demo build guide!**

You now understand the fundamentals of Infrastructure as Code and can build automated Okta demos. Keep practicing and exploring!

---

*Last updated: 2025-11-07*
