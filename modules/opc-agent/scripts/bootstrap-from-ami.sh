#!/bin/bash
# OPC Agent Bootstrap (Pre-built AMI) - ${connector_type} #${instance_number}
# This script is used when deploying from the pre-built OPC Agent AMI
# which already has sftd, Java, and SSM pre-installed.
set -e
exec > >(tee /var/log/opc-bootstrap.log) 2>&1
echo "=== OPC Bootstrap (AMI): ${agent_name} | $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# JDBC driver (if specified)
if [ -n "${jdbc_driver_url}" ]; then
  F=$(basename "${jdbc_driver_url}")
  curl -fSL -o "/installers/jdbc/$F" "${jdbc_driver_url}" && \
    ln -sf "/installers/jdbc/$F" /installers/jdbc/driver.jar || \
    echo "WARN: JDBC download failed"
fi

# Connector config
case "${connector_type}" in
  "generic-db")
    cat > /installers/connection-info.txt << 'EOF'
DATABASE_TYPE=PostgreSQL
DATABASE_HOST=${database_host}
DATABASE_PORT=${database_port}
JDBC_URL=jdbc:postgresql://${database_host}:${database_port}/okta_connector
JDBC_DRIVER_CLASS=org.postgresql.Driver
JDBC_DRIVER_PATH=/installers/jdbc/driver.jar
EOF
    ;;
  "oracle-ebs")
    curl -fSL -o /installers/jdbc/ucp.jar \
      "https://repo1.maven.org/maven2/com/oracle/database/jdbc/ucp/19.9.0.0/ucp-19.9.0.0.jar" 2>/dev/null || true
    cat > /installers/connection-info.txt << 'EOF'
DATABASE_TYPE=Oracle
DATABASE_HOST=${database_host}
DATABASE_PORT=${database_port}
DATABASE_SID=EBSDB
JDBC_URL=jdbc:oracle:thin:@//${database_host}:${database_port}/EBSDB
JDBC_DRIVER_CLASS=oracle.jdbc.driver.OracleDriver
JDBC_DRIVER_PATH=/installers/jdbc
EOF
    ;;
  "sap")
    cat > /installers/connection-info.txt << 'EOF'
DATABASE_TYPE=SAP
DATABASE_HOST=${database_host}
DATABASE_PORT=${database_port}
JDBC_DRIVER_PATH=/installers/jdbc/driver.jar
EOF
    ;;
esac
chmod 644 /installers/connection-info.txt

# Connectivity test
curl -s -o /dev/null -w "%%{http_code}" "${okta_org_url}" | grep -q "200\|301\|302" && echo "Okta: OK" || echo "Okta: WARN"
[ -n "${database_host}" ] && nc -zv "${database_host}" "${database_port}" 2>&1 | grep -q "succeeded\|open" && echo "DB: OK" || true

# Auto-enroll with OPA if token provided
if [ -n "${opa_enrollment_token}" ]; then
  echo ">>> Auto-enrolling with OPA..."
  /usr/local/bin/opc-enroll.sh "${opa_enrollment_token}"
fi

# Start SSM Agent (should already be enabled)
systemctl start amazon-ssm-agent || true

cat > /installers/SETUP.md << 'EOF'
# OPC Setup - ${agent_name} (Pre-built AMI)

## sftd Status
The sftd agent should already be enrolled if opa_enrollment_token was provided.
Check status: sudo systemctl status sftd

## Install Okta Provisioning Agent
1. Download from Okta Admin > Settings > Downloads
2. Upload to /installers/opc/
3. Run: sudo yum localinstall /installers/opc/OktaProvisioningAgent*.rpm -y
4. Configure: sudo /opt/OktaProvisioningAgent/configure_agent.sh

## Logs
- Bootstrap: /var/log/opc-bootstrap.log
- OPA: /opt/OktaProvisioningAgent/logs/
- sftd: journalctl -u sftd
EOF
chmod 644 /installers/SETUP.md

echo "=== Bootstrap Complete (AMI): ${agent_name} ==="
