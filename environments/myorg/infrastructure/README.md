# Active Directory Infrastructure

This directory contains Terraform configuration for deploying AWS infrastructure to support Active Directory integration with Okta.

## What Gets Deployed

This Terraform configuration creates:

- **VPC with public and private subnets**
- **Windows Server 2022 EC2 instance** configured as Active Directory Domain Controller
- **Security groups** with all necessary AD ports
- **Elastic IP** for stable public address
- **Automated AD setup** including:
  - Domain Controller promotion
  - Organizational Units (IT, HR, Finance, Sales, etc.)
  - Security Groups
  - Sample users with realistic names
  - Okta AD Agent installer download

## Prerequisites

### 1. AWS Account

- AWS account with appropriate permissions
- AWS CLI configured or environment variables set
- GitHub Actions OIDC role configured (if using CI/CD)

### 2. Terraform

```bash
# Install Terraform 1.9.0+
terraform version
```

### 3. Required Variables

You must provide these sensitive variables (never commit to git):

```bash
# Option 1: Environment variables (recommended)
export TF_VAR_admin_password="YourAdminPassword123!"
export TF_VAR_ad_safe_mode_password="YourSafeModePassword123!"
export TF_VAR_okta_org_url="https://dev-12345.okta.com"

# Option 2: terraform.tfvars file (gitignored)
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

**Password Requirements:**
- Minimum 8 characters
- Include uppercase, lowercase, numbers, and special characters
- Example: `Welcome123!`

## Quick Start

### Step 1: Configure Variables

```bash
# Navigate to infrastructure directory
cd environments/myorg/infrastructure

# Copy example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit with your values
vim terraform.tfvars

# Or use environment variables
export TF_VAR_admin_password="YourAdminPassword123!"
export TF_VAR_ad_safe_mode_password="YourSafeModePassword123!"
export TF_VAR_okta_org_url="https://dev-12345.okta.com"
```

### Step 2: Initialize Terraform

```bash
terraform init
```

This connects to the S3 backend and downloads required providers.

### Step 3: Review Plan

```bash
terraform plan
```

Review the resources that will be created.

### Step 4: Apply Configuration

```bash
terraform apply
```

**Deployment time:** ~3-5 minutes for infrastructure + 15-20 minutes for AD setup

### Step 5: Wait for Automated Setup

The server will automatically:
1. Rename computer (2 minutes)
2. Install AD-Domain-Services role (3 minutes)
3. Reboot and promote to Domain Controller (5 minutes)
4. Create AD structure (OUs, groups, users) (3 minutes)
5. Download Okta AD Agent installer (1 minute)

**Total setup time:** 15-20 minutes after `terraform apply` completes

### Step 6: Connect via RDP

```bash
# Get connection information
terraform output rdp_connection_string

# Or manually:
# Address: <public_ip from outputs>
# Username: Administrator
# Password: <value from TF_VAR_admin_password>
```

### Step 7: Verify Setup

On the Domain Controller:

1. **Open Server Manager**
   - Verify "AD DS" role is installed
   - Check for any errors

2. **Open Active Directory Users and Computers**
   - Verify domain exists
   - Check OUs: Users, Groups, Computers, Service Accounts
   - Verify department OUs (IT, HR, Finance, etc.)
   - Check sample users exist

3. **View Setup Logs**
   ```powershell
   # View bootstrap log
   Get-Content C:\Terraform\bootstrap.log

   # Check for errors
   Get-Content C:\Terraform\bootstrap.log | Select-String "ERROR"
   ```

### Step 8: Install Okta AD Agent

1. **Locate the installer:**
   - Path: `C:\Terraform\OktaADAgentSetup.exe`

2. **Run the installer:**
   - Double-click `OktaADAgentSetup.exe`
   - Follow the wizard
   - Provide Okta admin credentials
   - Select domain to sync

3. **Verify agent installation:**
   - Check Windows Services for "Okta AD Agent"
   - Verify agent is running

### Step 9: Configure Okta AD Integration

1. **Log in to Okta Admin Console**
2. **Navigate to:** Directory → Directory Integrations
3. **Add Directory:** Active Directory
4. **Configure:**
   - Domain Controller: `<dc_public_ip>` or `<dc_hostname>`
   - Domain: `demo.local` (or your configured domain)
   - Agent: Select the agent you just installed
5. **Configure sync settings:**
   - Select OUs to sync
   - Configure attribute mappings
   - Set sync schedule
6. **Run initial sync**

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ VPC (10.0.0.0/16)                                           │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Public Subnet (10.0.1.0/24)                         │   │
│  │                                                       │   │
│  │   ┌──────────────────────────────────────┐         │   │
│  │   │ Domain Controller EC2                │         │   │
│  │   │ - Windows Server 2022                │         │   │
│  │   │ - AD-Domain-Services                 │         │   │
│  │   │ - Elastic IP (public access)         │         │   │
│  │   │ - Security Group (AD + RDP)          │         │   │
│  │   └──────────────────────────────────────┘         │   │
│  │                                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Private Subnet (10.0.2.0/24)                        │   │
│  │ (Reserved for future expansion)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
         │
         │ Internet Gateway
         ▼
    🌐 Internet
```

## Active Directory Structure

### Organizational Units

```
demo.local
├── Users (custom OU)
│   ├── IT
│   ├── HR
│   ├── Finance
│   ├── Sales
│   ├── Marketing
│   └── Engineering
├── Groups (custom OU)
├── Computers (custom OU)
└── Service Accounts (custom OU)
```

### Sample Groups

- `IT-Team`
- `HR-Team`
- `Finance-Team`
- `Sales-Team`
- `Marketing-Team`
- `Engineering-Team`
- `Domain-Admins-Delegated` (privileged)
- `Server-Administrators` (privileged)
- `Helpdesk-Tier1`

### Sample Users

| Username     | Display Name     | Department | Password    |
|--------------|------------------|------------|-------------|
| jadmin       | John Admin       | IT         | Welcome123! |
| ssupport     | Sarah Support    | IT         | Welcome123! |
| ehr          | Emily HR         | HR         | Welcome123! |
| mrecruiter   | Mike Recruiter   | HR         | Welcome123! |
| dfinance     | David Finance    | Finance    | Welcome123! |
| laccountant  | Lisa Accountant  | Finance    | Welcome123! |
| tsales       | Tom Sales        | Sales      | Welcome123! |
| jrep         | Jennifer Rep     | Sales      | Welcome123! |

**All users:** Default password is `Welcome123!`

## Security Considerations

### ⚠️ Important Security Notes

1. **RDP Access:** By default allows RDP from anywhere (`0.0.0.0/0`)
   - **Change this!** Set `allowed_rdp_cidrs` to your IP address
   - Example: `["1.2.3.4/32"]`

2. **Passwords:** Sample users have simple passwords for demo purposes
   - Change these in production environments
   - Implement password policies via Group Policy

3. **Public IP:** Domain Controller has a public IP
   - Consider using VPN or bastion host for production
   - Use security groups to restrict access

4. **Sensitive Variables:** Never commit passwords to git
   - Use environment variables
   - Or terraform.tfvars (which is gitignored)
   - Or AWS Secrets Manager

5. **HTTPS Okta Agent:** Agent download requires HTTPS connection
   - Ensure security certificates are valid

## Cost Estimation

**Monthly AWS costs** (us-east-1, as of 2024):

- EC2 t3.medium instance: ~$30/month (730 hours)
- EBS volume (50GB gp3): ~$4/month
- Elastic IP: ~$3.60/month (if not associated with running instance)
- Data transfer: Variable (usually < $1/month for lab use)

**Total:** ~$35-40/month

**Cost-saving tips:**
- Stop instance when not in use (saves EC2 costs)
- Use smaller instance type for testing (t3.small)
- Delete when not needed (`terraform destroy`)

## Troubleshooting

### Issue: Terraform Apply Fails

**Problem:** Error during terraform apply

**Solutions:**
1. Check AWS credentials: `aws sts get-caller-identity`
2. Verify S3 backend exists and is accessible
3. Check DynamoDB table exists: `okta-terraform-state-lock`
4. Review error message for specific issues

### Issue: Can't Connect via RDP

**Problem:** Connection timeout or refused

**Solutions:**
1. Verify security group allows your IP
2. Check instance is running: `terraform output dc_instance_id`
3. Wait for setup to complete (15-20 minutes)
4. Check public IP: `terraform output dc_public_ip`

### Issue: Domain Controller Not Promoted

**Problem:** AD not configured after 20+ minutes

**Solutions:**
1. Connect via RDP
2. Check logs: `C:\Terraform\bootstrap.log`
3. Verify scheduled tasks ran:
   ```powershell
   Get-ScheduledTask | Where-Object {$_.TaskName -like "*Domain*"}
   ```
4. Manually promote if needed:
   ```powershell
   Install-ADDSForest -DomainName "demo.local" -DomainNetbiosName "DEMO"
   ```

### Issue: Okta AD Agent Download Fails

**Problem:** Agent installer not downloaded

**Solutions:**
1. Check logs: `C:\Terraform\bootstrap.log`
2. Manually download from Okta Admin Console:
   - Directory → Directory Integrations → Add Directory
   - Select Active Directory → Download Agent
3. Verify `okta_org_url` variable is correct

### Issue: Sample Users Not Created

**Problem:** Users don't exist in AD

**Solutions:**
1. Check post-promotion log: `C:\Terraform\bootstrap.log`
2. Manually run script:
   ```powershell
   C:\Terraform\post-promotion.ps1
   ```
3. Verify domain services are running:
   ```powershell
   Get-Service ADWS, DNS, Netlogon
   ```

## Cleanup

### Destroy Infrastructure

```bash
# Destroy all resources
terraform destroy

# Or target specific resources
terraform destroy -target=aws_instance.domain_controller
```

**Warning:** This will permanently delete:
- EC2 instance
- All AD data
- VPC and networking

**Important:** State remains in S3 backend for history.

## Customization

### Change Domain Name

Edit `terraform.tfvars`:
```hcl
ad_domain_name  = "corp.example.com"
ad_netbios_name = "CORP"
```

### Add More Sample Users

Edit `scripts/userdata.ps1` and add to the "Create Sample Users" section:

```powershell
New-ADUser -Name "New User" -SamAccountName "nuser" `
    -UserPrincipalName "nuser@${ad_domain_name}" `
    -Path $ITOU -AccountPassword $DefaultPassword `
    -Enabled $true -ErrorAction SilentlyContinue
```

### Change Instance Size

Edit `terraform.tfvars`:
```hcl
dc_instance_type = "t3.large" # More powerful
# or
dc_instance_type = "t3.small" # Cost savings (testing only)
```

### Customize OU Structure

Edit `scripts/userdata.ps1` in the "Create OU Structure" section.

## Integration with Okta Terraform

This infrastructure is designed to work alongside the Okta Terraform configuration in `../terraform/`.

**Workflow:**
1. Deploy infrastructure: `cd infrastructure && terraform apply`
2. Wait for AD setup (~20 minutes)
3. Install and configure Okta AD Agent
4. Configure Okta resources: `cd ../terraform && terraform apply`
5. Set up AD sync in Okta Admin Console

## Next Steps

After infrastructure is deployed:

1. **Install Okta AD Agent** (see Step 8 above)
2. **Configure Okta AD Integration** (see Step 9 above)
3. **Set up Okta Privileged Access** (if enabled)
4. **Test AD authentication**
5. **Configure additional OUs and users as needed**
6. **Implement Group Policies**
7. **Set up backup/disaster recovery**

## Support

For issues or questions:
- Check `C:\Terraform\bootstrap.log` on the DC
- Review Terraform output: `terraform output next_steps`
- See main repository documentation
- Review Okta AD Agent documentation

## References

- [Okta AD Agent Documentation](https://help.okta.com/en-us/Content/Topics/Directory/ad-agent-main.htm)
- [Windows Server Active Directory](https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview)
- [AWS EC2 Windows Instances](https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/concepts.html)
