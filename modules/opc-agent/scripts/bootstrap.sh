#!/bin/bash
# OPC Agent Bootstrap - ${connector_type} #${instance_number}
set -e
exec > >(tee /var/log/opc-bootstrap.log) 2>&1
echo "=== OPC Bootstrap: ${agent_name} | $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# SSM Agent
dnf install -y https://s3.amazonaws.com/ec2-downloads-windows/SSMAgent/latest/linux_amd64/amazon-ssm-agent.rpm || true
systemctl enable --now amazon-ssm-agent

# System packages
dnf update -y
dnf install -y java-11-openjdk java-11-openjdk-devel wget curl unzip nc jq

# Java config
export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
echo "export JAVA_HOME=$JAVA_HOME" > /etc/profile.d/java.sh
echo "export PATH=\$JAVA_HOME/bin:\$PATH" >> /etc/profile.d/java.sh

# Directories
mkdir -p /installers/{jdbc,opc} /opt/okta
chmod 755 /installers /opt/okta

# JDBC driver
if [ -n "${jdbc_driver_url}" ]; then
  F=$(basename "${jdbc_driver_url}")
  curl -fSL -o "/installers/jdbc/$F" "${jdbc_driver_url}" && ln -sf "/installers/jdbc/$F" /installers/jdbc/driver.jar || echo "WARN: JDBC download failed"
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
    curl -fSL -o /installers/jdbc/ucp.jar "https://repo1.maven.org/maven2/com/oracle/database/jdbc/ucp/19.9.0.0/ucp-19.9.0.0.jar" 2>/dev/null || true
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

# Firewall (if active)
systemctl is-active --quiet firewalld && { firewall-cmd --permanent --add-service=https --add-port=9090/tcp; firewall-cmd --reload; }

# Connectivity test
curl -s -o /dev/null -w "%%{http_code}" "${okta_org_url}" | grep -q "200\|301\|302" && echo "Okta: OK" || echo "Okta: WARN"
[ -n "${database_host}" ] && nc -zv "${database_host}" "${database_port}" 2>&1 | grep -q "succeeded\|open" && echo "DB: OK" || true

# Setup instructions
cat > /installers/SETUP.md << 'EOF'
# OPC Setup - ${agent_name}
1. Download OPA from Okta Admin > Settings > Downloads
2. Install: sudo yum localinstall /installers/opc/OktaProvisioningAgent*.rpm -y
3. Configure: sudo /opt/OktaProvisioningAgent/configure_agent.sh
4. sftd enrollment: echo '<token>' | sudo tee /var/lib/sftd/enrollment.token && sudo systemctl enable --now sftd
5. Logs: /var/log/opc-bootstrap.log, /opt/OktaProvisioningAgent/logs/, journalctl -u sftd
EOF
chmod 644 /installers/SETUP.md

# OPA PAM sftd
rpm --import https://dist.scaleft.com/GPG-KEY-OktaPAM-2023
cat > /etc/yum.repos.d/oktapam-stable.repo << 'EOF'
[oktapam-stable]
name=Okta PAM Stable - RHEL 8
baseurl=https://dist.scaleft.com/repos/rpm/stable/rhel/8/$basearch
gpgcheck=1
repo_gpgcheck=1
enabled=1
gpgkey=https://dist.scaleft.com/GPG-KEY-OktaPAM-2023
EOF
dnf makecache -y
dnf install -y scaleft-server-tools || echo "WARN: sftd install failed"

echo "=== Bootstrap Complete: ${agent_name} | See /installers/SETUP.md ==="
