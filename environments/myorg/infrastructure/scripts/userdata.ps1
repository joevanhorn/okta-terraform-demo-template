<powershell>
# ==============================================================================
# Windows Server User Data Script
# Executed on first boot to configure Domain Controller
# ==============================================================================

# Set error action preference
$ErrorActionPreference = "Continue"

# Create log directory
$LogDir = "C:\Terraform"
$LogFile = "$LogDir\bootstrap.log"
New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogMessage = "$Timestamp - $Message"
    Add-Content -Path $LogFile -Value $LogMessage
    Write-Host $LogMessage
}

Write-Log "===== Starting Domain Controller Bootstrap ====="
Write-Log "Environment: ${environment_name}"
Write-Log "Domain: ${ad_domain_name}"

# ==============================================================================
# Set Administrator Password
# ==============================================================================

Write-Log "Setting Administrator password..."
try {
    $AdminPassword = ConvertTo-SecureString "${admin_password}" -AsPlainText -Force
    $Admin = [ADSI]"WinNT://./Administrator,user"
    $Admin.SetPassword("${admin_password}")
    Write-Log "Administrator password set successfully"
} catch {
    Write-Log "ERROR setting Administrator password: $_"
}

# ==============================================================================
# Rename Computer
# ==============================================================================

Write-Log "Renaming computer to ${ad_netbios_name}-DC01..."
try {
    Rename-Computer -NewName "${ad_netbios_name}-DC01" -Force -ErrorAction Stop
    Write-Log "Computer renamed successfully"
} catch {
    Write-Log "ERROR renaming computer: $_"
}

# ==============================================================================
# Install AD-Domain-Services Role
# ==============================================================================

Write-Log "Installing Active Directory Domain Services role..."
try {
    Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools -ErrorAction Stop
    Write-Log "AD-Domain-Services role installed successfully"
} catch {
    Write-Log "ERROR installing AD-Domain-Services: $_"
    exit 1
}

# ==============================================================================
# Create Scheduled Task for DC Promotion (runs after reboot)
# ==============================================================================

Write-Log "Creating scheduled task for DC promotion..."

# Create the promotion script
$PromotionScript = @"
`$ErrorActionPreference = "Continue"
`$LogFile = "$LogFile"

function Write-Log {
    param([string]`$Message)
    `$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$LogMessage = "`$Timestamp - `$Message"
    Add-Content -Path `$LogFile -Value `$LogMessage
    Write-Host `$LogMessage
}

Write-Log "===== Starting DC Promotion ====="

# Promote to Domain Controller
Write-Log "Promoting server to Domain Controller..."
try {
    `$SafeModePassword = ConvertTo-SecureString "${ad_safe_mode_password}" -AsPlainText -Force

    Install-ADDSForest ``
        -DomainName "${ad_domain_name}" ``
        -DomainNetbiosName "${ad_netbios_name}" ``
        -SafeModeAdministratorPassword `$SafeModePassword ``
        -InstallDns ``
        -Force ``
        -ErrorAction Stop

    Write-Log "Domain Controller promotion initiated"
} catch {
    Write-Log "ERROR during DC promotion: `$_"
}
"@

$PromotionScriptPath = "$LogDir\promote-dc.ps1"
$PromotionScript | Out-File -FilePath $PromotionScriptPath -Encoding UTF8

# Create scheduled task to run promotion script after reboot
$TaskName = "PromoteDomainController"
$Action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File $PromotionScriptPath"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Principal $Principal -Settings $Settings -Force
Write-Log "Scheduled task created for DC promotion"

# ==============================================================================
# Create Post-Promotion Script (runs after DC is up)
# ==============================================================================

Write-Log "Creating post-promotion configuration script..."

$PostPromotionScript = @"
`$ErrorActionPreference = "Continue"
`$LogFile = "$LogFile"

function Write-Log {
    param([string]`$Message)
    `$Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    `$LogMessage = "`$Timestamp - `$Message"
    Add-Content -Path `$LogFile -Value `$LogMessage
    Write-Host `$LogMessage
}

Write-Log "===== Starting Post-Promotion Configuration ====="

# Wait for AD services to be ready
Write-Log "Waiting for Active Directory services..."
Start-Sleep -Seconds 60

# Import Active Directory module
Import-Module ActiveDirectory

# Create OU Structure
Write-Log "Creating Organizational Units..."
try {
    `$DomainDN = (Get-ADDomain).DistinguishedName

    # Top-level OUs
    New-ADOrganizationalUnit -Name "Users" -Path `$DomainDN -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Groups" -Path `$DomainDN -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Computers" -Path `$DomainDN -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Service Accounts" -Path `$DomainDN -ErrorAction SilentlyContinue

    # Department OUs under Users
    `$UsersOU = "OU=Users,`$DomainDN"
    New-ADOrganizationalUnit -Name "IT" -Path `$UsersOU -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "HR" -Path `$UsersOU -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Finance" -Path `$UsersOU -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Sales" -Path `$UsersOU -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Marketing" -Path `$UsersOU -ErrorAction SilentlyContinue
    New-ADOrganizationalUnit -Name "Engineering" -Path `$UsersOU -ErrorAction SilentlyContinue

    Write-Log "Organizational Units created successfully"
} catch {
    Write-Log "ERROR creating OUs: `$_"
}

# Create Sample Groups
Write-Log "Creating security groups..."
try {
    `$GroupsOU = "OU=Groups,`$DomainDN"

    # Department groups
    New-ADGroup -Name "IT-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "HR-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Finance-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Sales-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Marketing-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Engineering-Team" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue

    # Privileged groups
    New-ADGroup -Name "Domain-Admins-Delegated" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Server-Administrators" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue
    New-ADGroup -Name "Helpdesk-Tier1" -GroupScope Global -Path `$GroupsOU -ErrorAction SilentlyContinue

    Write-Log "Security groups created successfully"
} catch {
    Write-Log "ERROR creating groups: `$_"
}

# Create Sample Users
Write-Log "Creating sample users..."
try {
    # Default password for demo users
    `$DefaultPassword = ConvertTo-SecureString "Welcome123!" -AsPlainText -Force

    # IT Users
    `$ITOU = "OU=IT,OU=Users,`$DomainDN"
    New-ADUser -Name "John Admin" -SamAccountName "jadmin" -UserPrincipalName "jadmin@${ad_domain_name}" -Path `$ITOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue
    New-ADUser -Name "Sarah Support" -SamAccountName "ssupport" -UserPrincipalName "ssupport@${ad_domain_name}" -Path `$ITOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue

    # HR Users
    `$HROU = "OU=HR,OU=Users,`$DomainDN"
    New-ADUser -Name "Emily HR" -SamAccountName "ehr" -UserPrincipalName "ehr@${ad_domain_name}" -Path `$HROU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue
    New-ADUser -Name "Mike Recruiter" -SamAccountName "mrecruiter" -UserPrincipalName "mrecruiter@${ad_domain_name}" -Path `$HROU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue

    # Finance Users
    `$FinanceOU = "OU=Finance,OU=Users,`$DomainDN"
    New-ADUser -Name "David Finance" -SamAccountName "dfinance" -UserPrincipalName "dfinance@${ad_domain_name}" -Path `$FinanceOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue
    New-ADUser -Name "Lisa Accountant" -SamAccountName "laccountant" -UserPrincipalName "laccountant@${ad_domain_name}" -Path `$FinanceOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue

    # Sales Users
    `$SalesOU = "OU=Sales,OU=Users,`$DomainDN"
    New-ADUser -Name "Tom Sales" -SamAccountName "tsales" -UserPrincipalName "tsales@${ad_domain_name}" -Path `$SalesOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue
    New-ADUser -Name "Jennifer Rep" -SamAccountName "jrep" -UserPrincipalName "jrep@${ad_domain_name}" -Path `$SalesOU -AccountPassword `$DefaultPassword -Enabled `$true -ErrorAction SilentlyContinue

    Write-Log "Sample users created successfully (default password: Welcome123!)"
} catch {
    Write-Log "ERROR creating users: `$_"
}

# Add users to groups
Write-Log "Adding users to groups..."
try {
    Add-ADGroupMember -Identity "IT-Team" -Members "jadmin","ssupport" -ErrorAction SilentlyContinue
    Add-ADGroupMember -Identity "HR-Team" -Members "ehr","mrecruiter" -ErrorAction SilentlyContinue
    Add-ADGroupMember -Identity "Finance-Team" -Members "dfinance","laccountant" -ErrorAction SilentlyContinue
    Add-ADGroupMember -Identity "Sales-Team" -Members "tsales","jrep" -ErrorAction SilentlyContinue
    Add-ADGroupMember -Identity "Domain-Admins-Delegated" -Members "jadmin" -ErrorAction SilentlyContinue

    Write-Log "Users added to groups successfully"
} catch {
    Write-Log "ERROR adding users to groups: `$_"
}

# Download Okta AD Agent
Write-Log "Downloading Okta AD Agent..."
try {
    `$AgentUrl = "${okta_org_url}/bc/fileStoreRecord?id=fs01a8oq7h9EUxP5d0h8"
    `$AgentPath = "$LogDir\OktaADAgentSetup.exe"

    # Download agent installer
    Invoke-WebRequest -Uri `$AgentUrl -OutFile `$AgentPath -UseBasicParsing -ErrorAction Stop
    Write-Log "Okta AD Agent downloaded to `$AgentPath"
    Write-Log "To install: Run OktaADAgentSetup.exe and provide your Okta credentials"
} catch {
    Write-Log "ERROR downloading Okta AD Agent: `$_"
    Write-Log "You can manually download from: ${okta_org_url}/admin/access/identity/directories"
}

# Okta Privileged Access Setup
if ("${okta_opa_enabled}" -eq "True") {
    Write-Log "Okta Privileged Access is enabled"
    Write-Log "TODO: Configure Okta Privileged Access for RDP access"
    Write-Log "Manual steps required:"
    Write-Log "1. Create server group in Okta Admin"
    Write-Log "2. Add this server to the group"
    Write-Log "3. Configure RDP access policies"
}

Write-Log "===== Post-Promotion Configuration Complete ====="
Write-Log "Next steps:"
Write-Log "1. Install Okta AD Agent: $LogDir\OktaADAgentSetup.exe"
Write-Log "2. Configure AD sync in Okta Admin Console"
Write-Log "3. Test AD authentication"

# Remove scheduled tasks
Unregister-ScheduledTask -TaskName "PromoteDomainController" -Confirm:`$false -ErrorAction SilentlyContinue
Unregister-ScheduledTask -TaskName "PostPromotionConfig" -Confirm:`$false -ErrorAction SilentlyContinue
"@

$PostPromotionScriptPath = "$LogDir\post-promotion.ps1"
$PostPromotionScript | Out-File -FilePath $PostPromotionScriptPath -Encoding UTF8

# Create scheduled task for post-promotion configuration
$PostTaskName = "PostPromotionConfig"
$PostAction = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-ExecutionPolicy Bypass -File $PostPromotionScriptPath"
$PostTrigger = New-ScheduledTaskTrigger -AtStartup
$PostSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries

# Delay this task to run after DC promotion completes (5 minutes delay)
$PostTrigger.Delay = "PT5M"

Register-ScheduledTask -TaskName $PostTaskName -Action $PostAction -Trigger $PostTrigger -Principal $Principal -Settings $PostSettings -Force
Write-Log "Scheduled task created for post-promotion configuration"

# ==============================================================================
# Reboot to complete setup
# ==============================================================================

Write-Log "===== Initial Bootstrap Complete ====="
Write-Log "Rebooting to apply computer rename and begin DC promotion..."

# Reboot after 30 seconds
shutdown /r /t 30 /c "Rebooting to configure Domain Controller"

</powershell>
