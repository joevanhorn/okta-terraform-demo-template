# Prompt: Deploy Active Directory Infrastructure

Use this prompt template to have an AI assistant generate AWS infrastructure for Active Directory integration with Okta.

---

## Step 1: Provide Context

Copy and paste the following context files to your AI assistant:

**Repository Structure:**
```
[Paste contents of: ai-assisted/context/repository_structure.md]
```

**Terraform Examples:**
```
[Paste contents of: ai-assisted/context/terraform_examples.md]
```

**Resource Guide:**
```
[Paste contents of: ai-assisted/context/okta_resource_guide.md]
```

---

## Step 2: Use This Prompt Template

Copy this template and fill in your specific requirements:

```
I need to deploy AWS infrastructure for Active Directory integration with Okta using Terraform.
Please generate valid Terraform configuration files following the examples and patterns provided
in the context above.

ENVIRONMENT DETAILS:
- Target environment: production
- Files should go in: environments/myorg/infrastructure/

INFRASTRUCTURE REQUIREMENTS:
[Describe what you need]
Example: "Windows Server 2022 as Active Directory Domain Controller with Okta AD Agent
pre-downloaded, ready for manual installation"

DOMAIN CONFIGURATION:
- Domain name: [e.g., demo.local or corp.example.com]
- NetBIOS name: [e.g., DEMO or CORP]
- Okta org URL: [e.g., https://dev-12345.okta.com]

ACTIVE DIRECTORY SETUP:
[List OUs, groups, and sample users needed]
Example:
- Organizational Units: IT, HR, Finance, Sales, Marketing, Engineering
- Security Groups: IT-Team, HR-Team, Finance-Team, Sales-Team, Marketing-Team, Engineering-Team
- Sample Users: 2 users per department with realistic names

NETWORK CONFIGURATION:
[List network requirements]
Example:
- VPC CIDR: 10.0.0.0/16
- Public subnet for Domain Controller
- Private subnet for future expansion
- Restrict RDP access to specific IP ranges (security consideration)

AWS RESOURCES:
[List EC2 and other AWS resource requirements]
Example:
- EC2 instance type: t3.medium (minimum for DC)
- Windows Server 2022
- Elastic IP for stable public address
- Security groups with all AD ports (DNS, LDAP, Kerberos, RDP, SMB, etc.)

AUTOMATION LEVEL:
[Specify what should be automated]
Example:
- Fully automated DC promotion
- Automated OU structure creation
- Automated security group creation
- Automated sample user creation with default password
- Okta AD Agent installer pre-downloaded to C:\Terraform\

OPTIONAL FEATURES:
[List any optional features]
Example:
- Okta Privileged Access integration for RDP
- Custom OU structure
- Additional security groups

OUTPUT REQUIREMENTS:
1. Generate separate .tf files for each infrastructure component:
   - provider.tf (AWS provider with S3 backend)
   - variables.tf (all infrastructure variables)
   - vpc.tf (VPC, subnets, IGW, routing)
   - security-groups.tf (security groups with AD ports)
   - ad-domain-controller.tf (EC2 instance with user_data)
   - outputs.tf (connection info and next steps)
   - scripts/userdata.ps1 (PowerShell automation script)
   - terraform.tfvars.example (example configuration)
   - .gitignore (protect sensitive files)
   - README.md (deployment guide)

2. Follow these rules:
   - Use S3 backend for state storage (per environment)
   - Mark passwords as sensitive variables
   - Include ALL Active Directory ports in security groups
   - Use IMDSv2 for EC2 metadata
   - Include comprehensive PowerShell automation in user_data
   - Provide clear next steps in outputs
   - Add security warnings for RDP access restrictions

3. PowerShell user_data should include:
   - Logging to C:\Terraform\bootstrap.log
   - Administrator password configuration
   - Computer rename (e.g., DEMO-DC01)
   - AD-Domain-Services role installation
   - Scheduled task for DC promotion (runs after first reboot)
   - Scheduled task for post-promotion setup (OUs, groups, users)
   - Okta AD Agent download

4. Security best practices:
   - Never commit passwords to git
   - Warn about RDP CIDR restrictions
   - Use environment variables for sensitive values
   - Encrypt state in S3
   - Use DynamoDB for state locking

Please generate complete, ready-to-use Terraform infrastructure code.
```

---

## Step 3: Review and Validate

After the AI generates the code:

1. **Copy the generated files** to your infrastructure directory:
   ```bash
   cd environments/myorg/infrastructure
   # Create files with generated code
   ```

2. **Create terraform.tfvars** from the example:
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   vim terraform.tfvars  # Add your passwords and Okta org URL
   ```

3. **Set environment variables** (alternative to tfvars):
   ```bash
   export TF_VAR_admin_password="YourPassword123!"
   export TF_VAR_ad_safe_mode_password="YourSafeModePassword123!"
   export TF_VAR_okta_org_url="https://dev-12345.okta.com"
   ```

4. **Validate syntax:**
   ```bash
   terraform fmt
   terraform validate
   ```

5. **Review for security:**
   - No hardcoded passwords
   - .gitignore includes *.tfvars and *.tfstate
   - allowed_rdp_cidrs restricted to your IP
   - All sensitive variables marked as sensitive

6. **Initialize Terraform:**
   ```bash
   terraform init
   ```

7. **Test plan:**
   ```bash
   terraform plan
   ```

8. **Review the plan** before applying:
   - Check EC2 instance type (t3.medium minimum)
   - Verify security group rules include all AD ports
   - Confirm S3 backend path is correct
   - Verify VPC and subnet configuration

9. **Apply when ready:**
   ```bash
   terraform apply
   ```

10. **Wait for automated setup** (15-20 minutes):
    - Computer rename and reboot (2 minutes)
    - AD role installation (3 minutes)
    - DC promotion and reboot (5 minutes)
    - OU/group/user creation (3 minutes)
    - Okta AD Agent download (1 minute)

11. **Connect via RDP:**
    ```bash
    # Get connection info
    terraform output rdp_connection_string
    terraform output dc_public_ip
    ```

12. **Verify setup on Domain Controller:**
    - Open Server Manager → verify AD DS role
    - Open Active Directory Users and Computers → verify OUs and users
    - Check logs: `C:\Terraform\bootstrap.log`
    - Verify Okta AD Agent installer: `C:\Terraform\OktaADAgentSetup.exe`

---

## Example Filled Template

Here's an example of how you might fill out the template:

```
I need to deploy AWS infrastructure for Active Directory integration with Okta using Terraform.

ENVIRONMENT DETAILS:
- Target environment: production
- Files should go in: environments/myorg/infrastructure/

INFRASTRUCTURE REQUIREMENTS:
Windows Server 2022 as Active Directory Domain Controller with fully automated setup,
pre-downloaded Okta AD Agent installer, and sample users for demo purposes.

DOMAIN CONFIGURATION:
- Domain name: demo.local
- NetBIOS name: DEMO
- Okta org URL: https://dev-12345.okta.com

ACTIVE DIRECTORY SETUP:
- Organizational Units: IT, HR, Finance, Sales, Marketing, Engineering
- Security Groups: IT-Team, HR-Team, Finance-Team, Sales-Team, Marketing-Team,
  Engineering-Team, Domain-Admins-Delegated, Server-Administrators, Helpdesk-Tier1
- Sample Users: 8 users total with realistic names
  * IT: jadmin (John Admin), ssupport (Sarah Support)
  * HR: ehr (Emily HR), mrecruiter (Mike Recruiter)
  * Finance: dfinance (David Finance), laccountant (Lisa Accountant)
  * Sales: tsales (Tom Sales), jrep (Jennifer Rep)
- All users: Default password "Welcome123!" (for demo only)

NETWORK CONFIGURATION:
- VPC CIDR: 10.0.0.0/16
- Public subnet: 10.0.1.0/24 (for Domain Controller)
- Private subnet: 10.0.2.0/24 (reserved for future use)
- Restrict RDP access to my IP only (security best practice)

AWS RESOURCES:
- EC2 instance type: t3.medium
- Windows Server 2022 (latest AMI)
- Elastic IP for stable public address
- Security groups with ALL AD ports:
  * DNS (53 TCP/UDP)
  * Kerberos (88 TCP/UDP)
  * RPC Endpoint Mapper (135)
  * NetBIOS (137-139)
  * LDAP (389 TCP/UDP)
  * SMB (445)
  * Kerberos Password (464 TCP/UDP)
  * LDAPS (636)
  * Global Catalog (3268-3269)
  * Dynamic RPC (49152-65535)
  * WinRM (5985-5986)
  * RDP (3389)

AUTOMATION LEVEL:
- Fully automated DC promotion
- Automated OU structure creation (Users, Groups, Computers, Service Accounts + department OUs)
- Automated security group creation (all department groups)
- Automated sample user creation with default password "Welcome123!"
- Okta AD Agent installer automatically downloaded to C:\Terraform\OktaADAgentSetup.exe
- Comprehensive logging to C:\Terraform\bootstrap.log

OPTIONAL FEATURES:
- Okta Privileged Access placeholder for RDP integration
- Cost estimation in documentation (~$35-40/month)
- Troubleshooting guide for common issues

OUTPUT: Generate complete Terraform infrastructure files following the requirements above.
```

---

## Tips for Best Results

1. **Security first:** Always restrict RDP to your IP, never use 0.0.0.0/0 in production
2. **Use strong passwords:** Minimum 8 characters with complexity
3. **Test in dev first:** Deploy to development environment before production
4. **Monitor costs:** t3.medium costs ~$30/month, stop when not in use
5. **Document setup:** Take notes during deployment for team documentation
6. **Backup important data:** Though infrastructure is code, document any manual changes
7. **Review logs:** Check C:\Terraform\bootstrap.log if setup doesn't complete

---

## Common Follow-Up Prompts

After generating initial infrastructure code, you might want to:

**Change domain name:**
```
"Update the infrastructure to use domain name 'corp.example.com' instead
of 'demo.local', and NetBIOS name 'CORP' instead of 'DEMO'"
```

**Add more sample users:**
```
"Add 5 more sample users to the PowerShell user_data script:
- 2 IT users
- 2 HR users
- 1 Finance user
Use realistic names and follow the existing pattern"
```

**Customize OU structure:**
```
"Add two additional OUs to the infrastructure:
- Contractors (under Users)
- Test Accounts (under Users)
Include security groups for each"
```

**Change instance size:**
```
"Update the infrastructure to use t3.large instance type instead of t3.medium
for better performance during demos"
```

**Add VPN access:**
```
"Modify the security groups to allow VPN access from IP range 10.100.0.0/16
instead of direct RDP from the internet"
```

**Fix deployment errors:**
```
"I got this error during terraform apply: [paste error].
Please fix the infrastructure code to resolve this issue."
```

**Add Okta Privileged Access:**
```
"Add placeholder configuration for Okta Privileged Access (OPA)
integration for RDP access management"
```

---

## Deployment Checklist

Use this checklist during deployment:

- [ ] AWS credentials configured (`aws sts get-caller-identity`)
- [ ] S3 backend bucket exists and accessible
- [ ] DynamoDB table exists for state locking
- [ ] Environment variables set or terraform.tfvars created
- [ ] Strong passwords chosen (8+ chars with complexity)
- [ ] RDP CIDR restricted to your IP
- [ ] Terraform initialized (`terraform init`)
- [ ] Terraform plan reviewed (`terraform plan`)
- [ ] Deployment applied (`terraform apply`)
- [ ] Wait 15-20 minutes for automated setup
- [ ] Verify RDP connection works
- [ ] Check Server Manager for AD DS role
- [ ] Verify OUs created in Active Directory
- [ ] Verify sample users exist
- [ ] Check C:\Terraform\bootstrap.log for any errors
- [ ] Verify Okta AD Agent installer downloaded
- [ ] Install Okta AD Agent manually
- [ ] Configure Okta AD integration in Admin Console

---

## Cost Considerations

**Monthly AWS costs** (us-east-1 region):
- EC2 t3.medium: ~$30/month (24/7)
- EBS 50GB gp3: ~$4/month
- Elastic IP: ~$3.60/month (if not attached)
- Data transfer: ~$1/month (lab use)

**Total:** ~$35-40/month

**Cost-saving tips:**
- Stop EC2 instance when not in use (saves ~$30/month)
- Use t3.small for testing only (not recommended for production demos)
- Destroy with `terraform destroy` when environment not needed
- Use scheduled start/stop for demo days only

---

## Troubleshooting Common Issues

**Issue: Terraform apply fails**
- Check AWS credentials: `aws sts get-caller-identity`
- Verify S3 bucket exists and is accessible
- Check DynamoDB table exists
- Review error message for specific issues

**Issue: Can't connect via RDP**
- Verify security group allows your IP
- Check instance is running: `terraform output dc_instance_id`
- Wait for setup to complete (15-20 minutes)
- Verify public IP: `terraform output dc_public_ip`

**Issue: Domain Controller not promoted**
- Connect via RDP
- Check logs: `C:\Terraform\bootstrap.log`
- Verify scheduled tasks ran:
  ```powershell
  Get-ScheduledTask | Where-Object {$_.TaskName -like "*Domain*"}
  ```
- Check for errors in Windows Event Viewer

**Issue: Okta AD Agent not downloaded**
- Check logs: `C:\Terraform\bootstrap.log`
- Verify okta_org_url variable is correct
- Manually download from Okta Admin Console:
  Directory → Directory Integrations → Add Directory → Active Directory

**Issue: Sample users not created**
- Check post-promotion scheduled task ran
- Review logs: `C:\Terraform\bootstrap.log`
- Verify domain services running:
  ```powershell
  Get-Service ADWS, DNS, Netlogon
  ```
- Manually run: `C:\Terraform\post-promotion.ps1`

---

## Next Steps

After successfully deploying infrastructure:

1. **Install Okta AD Agent** (manual step):
   - Run `C:\Terraform\OktaADAgentSetup.exe`
   - Follow installation wizard
   - Provide Okta admin credentials
   - Select domain to sync

2. **Configure Okta AD Integration**:
   - Log in to Okta Admin Console
   - Navigate to: Directory → Directory Integrations
   - Add Directory: Active Directory
   - Configure sync settings
   - Run initial sync

3. **Set up Okta resources**:
   - Navigate to `environments/myorg/terraform/`
   - Create Okta users, groups, apps, entitlement bundles
   - Configure policies and access reviews

4. **Test AD authentication**:
   - Verify users sync from AD to Okta
   - Test login with AD credentials
   - Verify group memberships

5. **Document your setup**:
   - Note any customizations made
   - Document RDP credentials securely
   - Create teardown procedure

6. **Consider implementing**:
   - Group Policies (via DC)
   - Backup/disaster recovery plan
   - Monitoring and alerting
   - Additional OUs and security groups as needed

For more scenarios, see:
- `prompts/create_demo_environment.md` - Create Okta resources after infrastructure
- `prompts/oig_setup.md` - Set up Identity Governance features
- `prompts/create_app.md` - Add applications for AD users
