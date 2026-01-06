<powershell>
# ==============================================================================
# AD DOMAIN CONTROLLER BOOTSTRAP SCRIPT
# ==============================================================================
# Minimal UserData script that sets up prerequisites and downloads the full
# setup script from S3 for execution. This pattern keeps UserData small and
# allows updates to the setup script without recreating instances.
# ==============================================================================

$ErrorActionPreference = "Stop"
Start-Transcript -Path "C:\bootstrap.log" -Append

Write-Output "=========================================="
Write-Output "AD Domain Controller Bootstrap Starting"
Write-Output "$(Get-Date)"
Write-Output "=========================================="

# Parameters from Terraform template
$SecretArn = "${secret_arn}"
$AwsRegion = "${aws_region}"
$ScriptsBucket = "${scripts_bucket}"
$SetupScriptKey = "${setup_script_key}"
$DomainName = "${domain_name}"
$NetbiosName = "${netbios_name}"
$CreateSampleData = "${create_sample_data}"
$OktaAgentToken = "${okta_agent_token}"
$OktaOrgUrl = "${okta_org_url}"

# Store configuration for setup script
$ConfigPath = "C:\ad-config.json"
$Config = @{
    SecretArn = $SecretArn
    AwsRegion = $AwsRegion
    DomainName = $DomainName
    NetbiosName = $NetbiosName
    CreateSampleData = $CreateSampleData
    OktaAgentToken = $OktaAgentToken
    OktaOrgUrl = $OktaOrgUrl
} | ConvertTo-Json
$Config | Out-File -FilePath $ConfigPath -Encoding UTF8

Write-Output "Configuration saved to $ConfigPath"

# Install AWS CLI if not present
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Output "Installing AWS CLI..."
    $CliUrl = "https://awscli.amazonaws.com/AWSCLIV2.msi"
    $CliPath = "C:\AWSCLIV2.msi"
    Invoke-WebRequest -Uri $CliUrl -OutFile $CliPath
    Start-Process msiexec.exe -Wait -ArgumentList "/i $CliPath /quiet"
    $env:Path += ";C:\Program Files\Amazon\AWSCLIV2"
    Write-Output "AWS CLI installed"
}

# Download and execute setup script from S3 if bucket is specified
if ($ScriptsBucket -ne "") {
    Write-Output "Downloading setup script from S3..."
    $SetupScriptPath = "C:\setup-ad.ps1"

    try {
        aws s3 cp "s3://$ScriptsBucket/$SetupScriptKey" $SetupScriptPath --region $AwsRegion

        if (Test-Path $SetupScriptPath) {
            Write-Output "Executing setup script..."
            & $SetupScriptPath
        } else {
            Write-Output "Setup script not found, falling back to inline setup"
            # Fall through to inline setup
        }
    } catch {
        Write-Output "Failed to download setup script: $_"
        Write-Output "Falling back to inline setup"
    }
} else {
    Write-Output "No S3 bucket specified, using inline setup"
}

# ==============================================================================
# INLINE SETUP (Used when S3 script not available)
# ==============================================================================

# Check if AD DS is already installed
$ADFeature = Get-WindowsFeature -Name AD-Domain-Services
if ($ADFeature.Installed) {
    Write-Output "AD Domain Services already installed"

    # Check if domain is configured
    try {
        $Domain = Get-ADDomain -ErrorAction Stop
        Write-Output "Domain already configured: $($Domain.DNSRoot)"
        Stop-Transcript
        exit 0
    } catch {
        Write-Output "AD DS installed but domain not configured yet"
    }
}

# Get credentials from Secrets Manager
Write-Output "Retrieving credentials from Secrets Manager..."
$SecretValue = aws secretsmanager get-secret-value --secret-id $SecretArn --region $AwsRegion --query SecretString --output text | ConvertFrom-Json
$AdminPassword = ConvertTo-SecureString $SecretValue.admin_password -AsPlainText -Force
$SafeModePassword = ConvertTo-SecureString $SecretValue.safe_mode_password -AsPlainText -Force

# Install AD DS role
Write-Output "Installing AD Domain Services..."
Install-WindowsFeature -Name AD-Domain-Services -IncludeManagementTools

# Install DNS
Write-Output "Installing DNS Server..."
Install-WindowsFeature -Name DNS -IncludeManagementTools

# Configure the domain
Write-Output "Configuring AD Forest: $DomainName"
try {
    Install-ADDSForest `
        -DomainName $DomainName `
        -DomainNetbiosName $NetbiosName `
        -SafeModeAdministratorPassword $SafeModePassword `
        -InstallDns:$true `
        -Force:$true `
        -NoRebootOnCompletion:$false
} catch {
    Write-Output "Forest installation initiated (server will reboot): $_"
}

Write-Output "Bootstrap complete - server will reboot to complete AD configuration"
Stop-Transcript
</powershell>
