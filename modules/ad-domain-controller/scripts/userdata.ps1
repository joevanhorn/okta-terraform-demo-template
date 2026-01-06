# ==============================================================================
# AD DOMAIN CONTROLLER FULL SETUP SCRIPT
# ==============================================================================
# This script is downloaded from S3 by the bootstrap script and performs:
# - AD DS installation and forest configuration
# - OU structure creation
# - Sample groups and users for demo purposes
# - Optional Okta AD Agent installation
# ==============================================================================

$ErrorActionPreference = "Stop"
Start-Transcript -Path "C:\userdata.log" -Append

Write-Output "=========================================="
Write-Output "AD Full Setup Script Starting"
Write-Output "$(Get-Date)"
Write-Output "=========================================="

# Load configuration
$ConfigPath = "C:\ad-config.json"
if (Test-Path $ConfigPath) {
    $Config = Get-Content $ConfigPath | ConvertFrom-Json
    $SecretArn = $Config.SecretArn
    $AwsRegion = $Config.AwsRegion
    $DomainName = $Config.DomainName
    $NetbiosName = $Config.NetbiosName
    $CreateSampleData = $Config.CreateSampleData -eq "true"
    $OktaAgentToken = $Config.OktaAgentToken
    $OktaOrgUrl = $Config.OktaOrgUrl
} else {
    Write-Output "ERROR: Configuration file not found at $ConfigPath"
    Stop-Transcript
    exit 1
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

function Wait-ForADDS {
    param(
        [int]$MaxWaitSeconds = 300,
        [int]$CheckIntervalSeconds = 10
    )

    $elapsed = 0
    while ($elapsed -lt $MaxWaitSeconds) {
        try {
            Get-ADDomain -ErrorAction Stop | Out-Null
            Write-Output "AD Domain Services are ready"
            return $true
        } catch {
            Write-Output "Waiting for AD DS to be ready... ($elapsed seconds)"
            Start-Sleep -Seconds $CheckIntervalSeconds
            $elapsed += $CheckIntervalSeconds
        }
    }

    Write-Output "Timeout waiting for AD DS"
    return $false
}

function New-OUIfNotExists {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Description = ""
    )

    $OUPath = "OU=$Name,$Path"
    try {
        Get-ADOrganizationalUnit -Identity $OUPath -ErrorAction Stop | Out-Null
        Write-Output "OU already exists: $Name"
    } catch {
        Write-Output "Creating OU: $Name"
        New-ADOrganizationalUnit -Name $Name -Path $Path -Description $Description -ProtectedFromAccidentalDeletion $false
    }
}

function New-GroupIfNotExists {
    param(
        [string]$Name,
        [string]$Path,
        [string]$Description = "",
        [string]$GroupScope = "Global",
        [string]$GroupCategory = "Security"
    )

    try {
        Get-ADGroup -Identity $Name -ErrorAction Stop | Out-Null
        Write-Output "Group already exists: $Name"
    } catch {
        Write-Output "Creating group: $Name"
        New-ADGroup -Name $Name -Path $Path -Description $Description -GroupScope $GroupScope -GroupCategory $GroupCategory
    }
}

function New-UserIfNotExists {
    param(
        [string]$SamAccountName,
        [string]$FirstName,
        [string]$LastName,
        [string]$Department,
        [string]$Title,
        [string]$Path,
        [SecureString]$Password,
        [string[]]$Groups = @()
    )

    $DisplayName = "$FirstName $LastName"
    $UserPrincipalName = "$SamAccountName@$DomainName"

    try {
        Get-ADUser -Identity $SamAccountName -ErrorAction Stop | Out-Null
        Write-Output "User already exists: $SamAccountName"
    } catch {
        Write-Output "Creating user: $SamAccountName"
        New-ADUser `
            -SamAccountName $SamAccountName `
            -UserPrincipalName $UserPrincipalName `
            -Name $DisplayName `
            -DisplayName $DisplayName `
            -GivenName $FirstName `
            -Surname $LastName `
            -Department $Department `
            -Title $Title `
            -Path $Path `
            -AccountPassword $Password `
            -PasswordNeverExpires $true `
            -Enabled $true

        # Add to groups
        foreach ($Group in $Groups) {
            try {
                Add-ADGroupMember -Identity $Group -Members $SamAccountName
                Write-Output "  Added to group: $Group"
            } catch {
                Write-Output "  Failed to add to group $Group : $_"
            }
        }
    }
}

# ==============================================================================
# MAIN SETUP
# ==============================================================================

# Check if AD is ready
if (-not (Wait-ForADDS)) {
    Write-Output "AD DS not ready, this script may need to run after reboot"
    Stop-Transcript
    exit 0
}

# Get domain DN
$DomainDN = (Get-ADDomain).DistinguishedName
Write-Output "Domain DN: $DomainDN"

# Get credentials for new users
$SecretValue = aws secretsmanager get-secret-value --secret-id $SecretArn --region $AwsRegion --query SecretString --output text | ConvertFrom-Json
$DefaultPassword = ConvertTo-SecureString $SecretValue.admin_password -AsPlainText -Force

# ==============================================================================
# CREATE OU STRUCTURE
# ==============================================================================

if ($CreateSampleData) {
    Write-Output ""
    Write-Output "Creating OU Structure..."
    Write-Output "========================"

    # Top-level OUs
    New-OUIfNotExists -Name "Company" -Path $DomainDN -Description "Company organizational units"
    $CompanyOU = "OU=Company,$DomainDN"

    # Department OUs
    New-OUIfNotExists -Name "Users" -Path $CompanyOU -Description "All company users"
    New-OUIfNotExists -Name "Groups" -Path $CompanyOU -Description "Security and distribution groups"
    New-OUIfNotExists -Name "Computers" -Path $CompanyOU -Description "Company computers"
    New-OUIfNotExists -Name "Service Accounts" -Path $CompanyOU -Description "Service accounts"

    $UsersOU = "OU=Users,$CompanyOU"
    $GroupsOU = "OU=Groups,$CompanyOU"

    # Department sub-OUs under Users
    New-OUIfNotExists -Name "Engineering" -Path $UsersOU -Description "Engineering department"
    New-OUIfNotExists -Name "Sales" -Path $UsersOU -Description "Sales department"
    New-OUIfNotExists -Name "Marketing" -Path $UsersOU -Description "Marketing department"
    New-OUIfNotExists -Name "Finance" -Path $UsersOU -Description "Finance department"
    New-OUIfNotExists -Name "HR" -Path $UsersOU -Description "Human Resources department"
    New-OUIfNotExists -Name "IT" -Path $UsersOU -Description "IT department"
    New-OUIfNotExists -Name "Executives" -Path $UsersOU -Description "Executive team"

    # ==============================================================================
    # CREATE GROUPS
    # ==============================================================================

    Write-Output ""
    Write-Output "Creating Groups..."
    Write-Output "=================="

    # Department groups
    New-GroupIfNotExists -Name "Engineering" -Path $GroupsOU -Description "Engineering team members"
    New-GroupIfNotExists -Name "Sales" -Path $GroupsOU -Description "Sales team members"
    New-GroupIfNotExists -Name "Marketing" -Path $GroupsOU -Description "Marketing team members"
    New-GroupIfNotExists -Name "Finance" -Path $GroupsOU -Description "Finance team members"
    New-GroupIfNotExists -Name "HR" -Path $GroupsOU -Description "HR team members"
    New-GroupIfNotExists -Name "IT" -Path $GroupsOU -Description "IT team members"
    New-GroupIfNotExists -Name "Executives" -Path $GroupsOU -Description "Executive team"

    # Role-based groups
    New-GroupIfNotExists -Name "Managers" -Path $GroupsOU -Description "All managers"
    New-GroupIfNotExists -Name "Contractors" -Path $GroupsOU -Description "Contract workers"
    New-GroupIfNotExists -Name "Remote Workers" -Path $GroupsOU -Description "Remote/WFH employees"

    # Application access groups
    New-GroupIfNotExists -Name "Salesforce Users" -Path $GroupsOU -Description "Salesforce application access"
    New-GroupIfNotExists -Name "Jira Users" -Path $GroupsOU -Description "Jira application access"
    New-GroupIfNotExists -Name "Confluence Users" -Path $GroupsOU -Description "Confluence application access"
    New-GroupIfNotExists -Name "GitHub Users" -Path $GroupsOU -Description "GitHub application access"
    New-GroupIfNotExists -Name "AWS Console Users" -Path $GroupsOU -Description "AWS Console access"
    New-GroupIfNotExists -Name "VPN Users" -Path $GroupsOU -Description "VPN access"

    # Privilege groups
    New-GroupIfNotExists -Name "IT Admins" -Path $GroupsOU -Description "IT Administrators"
    New-GroupIfNotExists -Name "Security Team" -Path $GroupsOU -Description "Security team members"
    New-GroupIfNotExists -Name "Help Desk" -Path $GroupsOU -Description "Help desk staff"

    # ==============================================================================
    # CREATE SAMPLE USERS
    # ==============================================================================

    Write-Output ""
    Write-Output "Creating Sample Users..."
    Write-Output "========================"

    # Engineering Users
    $EngOU = "OU=Engineering,$UsersOU"
    New-UserIfNotExists -SamAccountName "jsmith" -FirstName "John" -LastName "Smith" -Department "Engineering" -Title "Senior Software Engineer" -Path $EngOU -Password $DefaultPassword -Groups @("Engineering", "GitHub Users", "Jira Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "ejohnson" -FirstName "Emily" -LastName "Johnson" -Department "Engineering" -Title "Engineering Manager" -Path $EngOU -Password $DefaultPassword -Groups @("Engineering", "Managers", "GitHub Users", "Jira Users", "AWS Console Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "mwilliams" -FirstName "Michael" -LastName "Williams" -Department "Engineering" -Title "DevOps Engineer" -Path $EngOU -Password $DefaultPassword -Groups @("Engineering", "IT Admins", "GitHub Users", "AWS Console Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "sbrown" -FirstName "Sarah" -LastName "Brown" -Department "Engineering" -Title "Software Engineer" -Path $EngOU -Password $DefaultPassword -Groups @("Engineering", "GitHub Users", "Jira Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "dlee" -FirstName "David" -LastName "Lee" -Department "Engineering" -Title "QA Engineer" -Path $EngOU -Password $DefaultPassword -Groups @("Engineering", "Jira Users", "VPN Users")

    # Sales Users
    $SalesOU = "OU=Sales,$UsersOU"
    New-UserIfNotExists -SamAccountName "rwilson" -FirstName "Robert" -LastName "Wilson" -Department "Sales" -Title "Sales Director" -Path $SalesOU -Password $DefaultPassword -Groups @("Sales", "Managers", "Salesforce Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "jdavis" -FirstName "Jennifer" -LastName "Davis" -Department "Sales" -Title "Account Executive" -Path $SalesOU -Password $DefaultPassword -Groups @("Sales", "Salesforce Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "tmartin" -FirstName "Thomas" -LastName "Martin" -Department "Sales" -Title "Sales Representative" -Path $SalesOU -Password $DefaultPassword -Groups @("Sales", "Salesforce Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "agarcia" -FirstName "Amanda" -LastName "Garcia" -Department "Sales" -Title "Sales Engineer" -Path $SalesOU -Password $DefaultPassword -Groups @("Sales", "Engineering", "Salesforce Users", "VPN Users")

    # Marketing Users
    $MarketingOU = "OU=Marketing,$UsersOU"
    New-UserIfNotExists -SamAccountName "cmartinez" -FirstName "Christopher" -LastName "Martinez" -Department "Marketing" -Title "Marketing Director" -Path $MarketingOU -Password $DefaultPassword -Groups @("Marketing", "Managers", "Salesforce Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "lrodriguez" -FirstName "Laura" -LastName "Rodriguez" -Department "Marketing" -Title "Content Manager" -Path $MarketingOU -Password $DefaultPassword -Groups @("Marketing", "Confluence Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "kthompson" -FirstName "Kevin" -LastName "Thompson" -Department "Marketing" -Title "Marketing Analyst" -Path $MarketingOU -Password $DefaultPassword -Groups @("Marketing", "Salesforce Users", "VPN Users")

    # Finance Users
    $FinanceOU = "OU=Finance,$UsersOU"
    New-UserIfNotExists -SamAccountName "mwhite" -FirstName "Michelle" -LastName "White" -Department "Finance" -Title "CFO" -Path $FinanceOU -Password $DefaultPassword -Groups @("Finance", "Executives", "Managers", "VPN Users")
    New-UserIfNotExists -SamAccountName "bharris" -FirstName "Brian" -LastName "Harris" -Department "Finance" -Title "Financial Analyst" -Path $FinanceOU -Password $DefaultPassword -Groups @("Finance", "VPN Users")
    New-UserIfNotExists -SamAccountName "nclark" -FirstName "Nicole" -LastName "Clark" -Department "Finance" -Title "Accountant" -Path $FinanceOU -Password $DefaultPassword -Groups @("Finance", "VPN Users")

    # HR Users
    $HROU = "OU=HR,$UsersOU"
    New-UserIfNotExists -SamAccountName "plewis" -FirstName "Patricia" -LastName "Lewis" -Department "HR" -Title "HR Director" -Path $HROU -Password $DefaultPassword -Groups @("HR", "Managers", "VPN Users")
    New-UserIfNotExists -SamAccountName "jwalker" -FirstName "James" -LastName "Walker" -Department "HR" -Title "HR Specialist" -Path $HROU -Password $DefaultPassword -Groups @("HR", "VPN Users")

    # IT Users
    $ITOU = "OU=IT,$UsersOU"
    New-UserIfNotExists -SamAccountName "shernandez" -FirstName "Steven" -LastName "Hernandez" -Department "IT" -Title "IT Director" -Path $ITOU -Password $DefaultPassword -Groups @("IT", "IT Admins", "Managers", "AWS Console Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "ayoung" -FirstName "Angela" -LastName "Young" -Department "IT" -Title "System Administrator" -Path $ITOU -Password $DefaultPassword -Groups @("IT", "IT Admins", "AWS Console Users", "VPN Users")
    New-UserIfNotExists -SamAccountName "dking" -FirstName "Daniel" -LastName "King" -Department "IT" -Title "Help Desk Technician" -Path $ITOU -Password $DefaultPassword -Groups @("IT", "Help Desk", "VPN Users")
    New-UserIfNotExists -SamAccountName "rscott" -FirstName "Rachel" -LastName "Scott" -Department "IT" -Title "Security Analyst" -Path $ITOU -Password $DefaultPassword -Groups @("IT", "Security Team", "AWS Console Users", "VPN Users")

    # Executive Users
    $ExecOU = "OU=Executives,$UsersOU"
    New-UserIfNotExists -SamAccountName "cexec" -FirstName "Charles" -LastName "Executive" -Department "Executive" -Title "CEO" -Path $ExecOU -Password $DefaultPassword -Groups @("Executives", "Managers", "VPN Users")
    New-UserIfNotExists -SamAccountName "vpresident" -FirstName "Victoria" -LastName "President" -Department "Executive" -Title "COO" -Path $ExecOU -Password $DefaultPassword -Groups @("Executives", "Managers", "VPN Users")

    Write-Output ""
    Write-Output "Sample data creation complete!"
    Write-Output "=============================="
}

# ==============================================================================
# INSTALL OKTA AD AGENT (OPTIONAL)
# ==============================================================================

if ($OktaAgentToken -ne "" -and $OktaOrgUrl -ne "") {
    Write-Output ""
    Write-Output "Installing Okta AD Agent..."
    Write-Output "============================"

    $AgentInstallerUrl = "https://op1static.oktacdn.com/fs/agents/OktaADAgentSetup.exe"
    $AgentInstallerPath = "C:\OktaADAgentSetup.exe"

    try {
        Write-Output "Downloading Okta AD Agent installer..."
        Invoke-WebRequest -Uri $AgentInstallerUrl -OutFile $AgentInstallerPath

        Write-Output "Running Okta AD Agent installer..."
        $InstallArgs = "/q /S ORG_URL=$OktaOrgUrl AGENT_REGISTRATION_TOKEN=$OktaAgentToken"
        Start-Process -FilePath $AgentInstallerPath -ArgumentList $InstallArgs -Wait

        Write-Output "Okta AD Agent installation complete"
    } catch {
        Write-Output "Failed to install Okta AD Agent: $_"
    }
}

Write-Output ""
Write-Output "=========================================="
Write-Output "AD Setup Complete"
Write-Output "$(Get-Date)"
Write-Output "=========================================="

Stop-Transcript
