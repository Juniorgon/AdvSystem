#!/bin/bash

# Law Firm Management System - Security Installation Script
# Simple and practical cybersecurity setup

echo "=================================================="
echo "🔐 INSTALAÇÃO DE SEGURANÇA - SISTEMA ADVOCACIA"
echo "=================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "❌ Este script deve ser executado como root (use sudo)"
   exit 1
fi

echo "🔧 Iniciando configuração de segurança..."

# 1. Update system packages
echo "📦 Atualizando pacotes do sistema..."
apt update -y
apt upgrade -y

# 2. Install fail2ban for intrusion prevention
echo "🛡️  Instalando Fail2ban..."
apt install fail2ban -y

# Create fail2ban configuration
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 1800
findtime = 600
maxretry = 5
backend = auto

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-req-limit]
enabled = true
filter = nginx-req-limit
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
findtime = 600
bantime = 7200
EOF

# Start and enable fail2ban
systemctl enable fail2ban
systemctl start fail2ban

# 3. Configure UFW Firewall
echo "🔥 Configurando firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# Allow necessary ports
ufw allow 22/tcp     # SSH
ufw allow 80/tcp     # HTTP
ufw allow 443/tcp    # HTTPS
ufw allow 3000/tcp   # Frontend (if direct access needed)
ufw allow 8001/tcp   # Backend API

# Enable firewall
ufw --force enable

# 4. Setup log monitoring
echo "📋 Configurando monitoramento de logs..."
mkdir -p /var/log/law-firm-security

# Create log rotation configuration
cat > /etc/logrotate.d/law-firm-security << EOF
/var/log/law-firm-security/*.log /var/log/security_events.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 root root
}
EOF

# 5. Install and configure ClamAV antivirus
echo "🦠 Instalando antivírus ClamAV..."
apt install clamav clamav-daemon clamav-freshclam -y

# Update virus definitions
freshclam

# Start ClamAV daemon
systemctl enable clamav-daemon
systemctl start clamav-daemon

# 6. Setup automatic security updates
echo "🔄 Configurando atualizações automáticas..."
apt install unattended-upgrades apt-listchanges -y

# Configure automatic updates
cat > /etc/apt/apt.conf.d/50unattended-upgrades << EOF
Unattended-Upgrade::Allowed-Origins {
    "\${distro_id}:\${distro_codename}-security";
    "\${distro_id}ESMApps:\${distro_codename}-apps-security";
    "\${distro_id}ESM:\${distro_codename}-infra-security";
};

Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

# Enable automatic updates
cat > /etc/apt/apt.conf.d/20auto-upgrades << EOF
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
APT::Periodic::AutocleanInterval "7";
EOF

# 7. Secure SSH configuration
echo "🔑 Configurando SSH seguro..."
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.backup

# Apply secure SSH settings
sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config
sed -i 's/X11Forwarding yes/X11Forwarding no/' /etc/ssh/sshd_config
sed -i 's/#MaxAuthTries 6/MaxAuthTries 3/' /etc/ssh/sshd_config

echo "Protocol 2" >> /etc/ssh/sshd_config
echo "ClientAliveInterval 300" >> /etc/ssh/sshd_config
echo "ClientAliveCountMax 2" >> /etc/ssh/sshd_config

# Restart SSH service
systemctl restart ssh

# 8. Setup backup directory with proper permissions
echo "💾 Configurando diretório de backup..."
mkdir -p /var/backups/law-firm
chmod 700 /var/backups/law-firm

# 9. Create security monitoring script
cat > /usr/local/bin/security-monitor.sh << 'EOF'
#!/bin/bash

LOG_FILE="/var/log/law-firm-security/monitor.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# Monitor failed login attempts
FAILED_LOGINS=$(grep "Failed password" /var/log/auth.log | wc -l)

# Monitor suspicious process activity
SUSPICIOUS_PROCESSES=$(ps aux | grep -E "(nc|netcat|telnet)" | grep -v grep | wc -l)

# Monitor disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')

echo "[$DATE] Failed logins: $FAILED_LOGINS, Suspicious processes: $SUSPICIOUS_PROCESSES, Disk usage: $DISK_USAGE%" >> $LOG_FILE

# Alert if disk usage > 90%
if [ $DISK_USAGE -gt 90 ]; then
    echo "[$DATE] WARNING: Disk usage above 90%" >> $LOG_FILE
fi

# Alert if too many failed logins
if [ $FAILED_LOGINS -gt 50 ]; then
    echo "[$DATE] WARNING: High number of failed login attempts" >> $LOG_FILE
fi
EOF

chmod +x /usr/local/bin/security-monitor.sh

# Add to crontab to run every hour
(crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/security-monitor.sh") | crontab -

# 10. Setup PostgreSQL security
echo "🐘 Configurando segurança PostgreSQL..."

# Update PostgreSQL configuration for security
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oP '\d+\.\d+' | head -1)
PG_CONFIG="/etc/postgresql/$PG_VERSION/main/postgresql.conf"
PG_HBA="/etc/postgresql/$PG_VERSION/main/pg_hba.conf"

if [ -f "$PG_CONFIG" ]; then
    # Secure PostgreSQL settings
    sed -i "s/#log_connections = off/log_connections = on/" $PG_CONFIG
    sed -i "s/#log_disconnections = off/log_disconnections = on/" $PG_CONFIG
    sed -i "s/#log_failed_connections = off/log_failed_connections = on/" $PG_CONFIG
    
    # Restart PostgreSQL
    systemctl restart postgresql
fi

# 11. Create security status check script
cat > /usr/local/bin/security-status.sh << 'EOF'
#!/bin/bash

echo "🔐 SISTEMA DE SEGURANÇA - STATUS"
echo "=================================="

echo "🛡️  Fail2ban Status:"
fail2ban-client status

echo ""
echo "🔥 Firewall Status:"
ufw status

echo ""
echo "🦠 ClamAV Status:"
systemctl is-active clamav-daemon

echo ""
echo "📊 Últimos eventos de segurança:"
tail -10 /var/log/security_events.log 2>/dev/null || echo "Nenhum evento registrado ainda"

echo ""
echo "💾 Uso do disco:"
df -h / | tail -1

echo ""
echo "🔄 Atualizações disponíveis:"
apt list --upgradable 2>/dev/null | wc -l
EOF

chmod +x /usr/local/bin/security-status.sh

# 12. Final setup
echo "⚙️  Finalizando configuração..."

# Restart services
systemctl restart fail2ban
systemctl restart ufw

echo ""
echo "✅ INSTALAÇÃO DE SEGURANÇA CONCLUÍDA!"
echo "=================================="
echo ""
echo "📋 RESUMO DAS MEDIDAS IMPLEMENTADAS:"
echo "   ✅ Fail2ban - Proteção contra ataques de força bruta"
echo "   ✅ UFW Firewall - Controle de acesso de rede"
echo "   ✅ ClamAV - Proteção antivírus"
echo "   ✅ Atualizações automáticas de segurança"
echo "   ✅ SSH seguro configurado"
echo "   ✅ Monitoramento de logs"
echo "   ✅ PostgreSQL seguro"
echo ""
echo "🔧 COMANDOS ÚTEIS:"
echo "   - Verificar status: /usr/local/bin/security-status.sh"
echo "   - Logs de segurança: tail -f /var/log/security_events.log"
echo "   - Status do Fail2ban: fail2ban-client status"
echo "   - Status do Firewall: ufw status"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   - Configure chaves SSH antes de reiniciar (PasswordAuthentication desabilitado)"
echo "   - Monitore os logs regularmente"
echo "   - Mantenha backups atualizados"
echo ""
echo "🎯 Sistema pronto para uso em produção com segurança avançada!"
EOF