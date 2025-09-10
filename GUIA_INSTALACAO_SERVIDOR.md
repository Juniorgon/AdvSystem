# 🖥️ Guia de Instalação em Servidor - Sistema Jurídico GB Advocacia

## 📋 Requisitos do Servidor

### Especificações Mínimas
- **OS:** Ubuntu 20.04+ ou CentOS 8+
- **RAM:** 4GB (recomendado 8GB)
- **CPU:** 2 cores (recomendado 4 cores)
- **Armazenamento:** 50GB SSD
- **Rede:** Conexão estável, IP fixo recomendado

### Especificações Recomendadas (Produção)
- **OS:** Ubuntu 22.04 LTS
- **RAM:** 16GB
- **CPU:** 4-8 cores
- **Armazenamento:** 200GB SSD NVMe
- **Rede:** Banda mínima 100Mbps

---

## 🚀 1. Preparação do Servidor

### 1.1 Atualização do Sistema

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y
sudo apt install -y curl wget git htop nano

# CentOS/RHEL
sudo yum update -y
sudo yum install -y curl wget git htop nano
```

### 1.2 Criar Usuário do Sistema

```bash
# Criar usuário dedicado
sudo adduser advocacia
sudo usermod -aG sudo advocacia
sudo su - advocacia
```

### 1.3 Configurar Firewall

```bash
# Ubuntu (UFW)
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw allow 3000  # Frontend (temporário)
sudo ufw allow 8001  # Backend (temporário)

# CentOS (firewalld)
sudo systemctl enable firewalld
sudo systemctl start firewalld
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https
sudo firewall-cmd --reload
```

---

## 🐳 2. Instalação Docker (Método Recomendado)

### 2.1 Instalar Docker

```bash
# Ubuntu
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker advocacia
sudo systemctl enable docker

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2.2 Criar Estrutura do Projeto

```bash
cd /home/advocacia
mkdir gb-advocacia-sistema
cd gb-advocacia-sistema

# Clonar ou copiar arquivos do sistema
# Se usando Git:
git clone SEU_REPOSITORIO .

# Ou copiar arquivos manualmente via SCP/SFTP
```

### 2.3 Criar docker-compose.yml

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15
    container_name: advocacia_postgres
    environment:
      POSTGRES_DB: gb_advocacia_db
      POSTGRES_USER: advocacia_user
      POSTGRES_PASSWORD: advocacia_pass_PROD_2024
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backup:/backup
    ports:
      - "5432:5432"
    restart: unless-stopped

  backend:
    build: ./backend
    container_name: advocacia_backend
    environment:
      - DATABASE_URL=postgresql://advocacia_user:advocacia_pass_PROD_2024@postgres:5432/gb_advocacia_db
      - JWT_SECRET_KEY=sua_chave_jwt_super_segura_aqui_2024
      - GOOGLE_DRIVE_ENABLED=true
      - WHATSAPP_ENABLED=true
    volumes:
      - ./backend:/app
      - ./logs:/var/log/supervisor
    ports:
      - "8001:8001"
    depends_on:
      - postgres
    restart: unless-stopped

  frontend:
    build: ./frontend
    container_name: advocacia_frontend
    environment:
      - REACT_APP_BACKEND_URL=https://api.gbadvocacia.com
    ports:
      - "3000:3000"
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    container_name: advocacia_nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## ⚙️ 3. Instalação Manual (Alternativa)

### 3.1 Instalar Dependências

```bash
# Python 3.9+
sudo apt install -y python3 python3-pip python3-venv

# Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Nginx
sudo apt install -y nginx

# Supervisor (gerenciamento de processos)
sudo apt install -y supervisor
```

### 3.2 Configurar PostgreSQL

```bash
sudo -u postgres psql

-- No PostgreSQL:
CREATE DATABASE gb_advocacia_db;
CREATE USER advocacia_user WITH PASSWORD 'advocacia_pass_PROD_2024';
GRANT ALL PRIVILEGES ON DATABASE gb_advocacia_db TO advocacia_user;
\q
```

### 3.3 Configurar Backend

```bash
cd /home/advocacia/gb-advocacia-sistema/backend

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt

# Configurar .env para produção
nano .env
```

### 3.4 Configurar Frontend

```bash
cd /home/advocacia/gb-advocacia-sistema/frontend

# Instalar dependências
npm install

# Build para produção
npm run build
```

---

## 🌐 4. Configuração Nginx

### 4.1 Criar Configuração Nginx

```bash
sudo nano /etc/nginx/sites-available/gbadvocacia
```

```nginx
# /etc/nginx/sites-available/gbadvocacia
server {
    listen 80;
    server_name gbadvocacia.com www.gbadvocacia.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name gbadvocacia.com www.gbadvocacia.com;

    # SSL Configuration
    ssl_certificate /etc/ssl/certs/gbadvocacia.crt;
    ssl_certificate_key /etc/ssl/private/gbadvocacia.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend (React)
    location / {
        root /home/advocacia/gb-advocacia-sistema/frontend/build;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Logs
    access_log /var/log/nginx/gbadvocacia_access.log;
    error_log /var/log/nginx/gbadvocacia_error.log;
}
```

### 4.2 Ativar Configuração

```bash
sudo ln -s /etc/nginx/sites-available/gbadvocacia /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo systemctl enable nginx
```

---

## 🔐 5. SSL/HTTPS - Let's Encrypt

### 5.1 Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 5.2 Gerar Certificado

```bash
sudo certbot --nginx -d gbadvocacia.com -d www.gbadvocacia.com
```

### 5.3 Configurar Renovação Automática

```bash
# Testar renovação
sudo certbot renew --dry-run

# Adicionar ao crontab
sudo crontab -e
# Adicionar linha:
0 12 * * * /usr/bin/certbot renew --quiet
```

---

## 📊 6. Configuração Supervisor

### 6.1 Configurar Backend Service

```bash
sudo nano /etc/supervisor/conf.d/advocacia-backend.conf
```

```ini
[program:advocacia-backend]
command=/home/advocacia/gb-advocacia-sistema/backend/venv/bin/python -m uvicorn server:app --host 0.0.0.0 --port 8001
directory=/home/advocacia/gb-advocacia-sistema/backend
user=advocacia
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/advocacia-backend.log
environment=PATH="/home/advocacia/gb-advocacia-sistema/backend/venv/bin"
```

### 6.2 Configurar Frontend Service (se não usar Nginx para static)

```bash
sudo nano /etc/supervisor/conf.d/advocacia-frontend.conf
```

```ini
[program:advocacia-frontend]
command=npx serve -s build -l 3000
directory=/home/advocacia/gb-advocacia-sistema/frontend
user=advocacia
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/supervisor/advocacia-frontend.log
```

### 6.3 Ativar Serviços

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start advocacia-backend
sudo supervisorctl status
```

---

## 📈 7. Monitoramento e Logs

### 7.1 Configurar Logrotate

```bash
sudo nano /etc/logrotate.d/advocacia
```

```
/var/log/supervisor/advocacia-*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 advocacia advocacia
    postrotate
        supervisorctl restart advocacia-backend
    endscript
}
```

### 7.2 Monitoramento Básico

```bash
# Script de monitoramento
nano /home/advocacia/monitor.sh
```

```bash
#!/bin/bash
# Monitor básico do sistema

echo "=== Status dos Serviços ==="
sudo systemctl status nginx postgresql supervisor

echo "=== Uso de Recursos ==="
free -h
df -h
top -bn1 | head -10

echo "=== Logs Recentes ==="
tail -n 20 /var/log/supervisor/advocacia-backend.log
```

---

## 🛡️ 8. Segurança Adicional

### 8.1 Configurar Fail2Ban

```bash
sudo apt install -y fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 5

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
```

### 8.2 Configurar Backup Automático

```bash
nano /home/advocacia/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/advocacia/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup PostgreSQL
pg_dump -h localhost -U advocacia_user gb_advocacia_db > $BACKUP_DIR/db_$DATE.sql

# Backup arquivos
tar -czf $BACKUP_DIR/files_$DATE.tar.gz \
    /home/advocacia/gb-advocacia-sistema \
    --exclude=node_modules \
    --exclude=venv

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

### 8.3 Configurar Crontab para Backup

```bash
crontab -e
# Adicionar:
0 2 * * * /home/advocacia/backup.sh >> /var/log/backup.log 2>&1
```

---

## 🔧 9. Variáveis de Ambiente de Produção

### 9.1 Backend .env

```bash
# /home/advocacia/gb-advocacia-sistema/backend/.env
DATABASE_URL="postgresql://advocacia_user:advocacia_pass_PROD_2024@localhost/gb_advocacia_db"
JWT_SECRET_KEY="jwt_secret_super_seguro_producao_2024_gbadvocacia"
MONGO_URL="mongodb://localhost:27017/backup_db"

# Google Drive
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_FILE=/home/advocacia/gb-advocacia-sistema/backend/google_drive_credentials.json
GOOGLE_CLIENT_ID="seu_google_client_id"
GOOGLE_CLIENT_SECRET="seu_google_client_secret"
GOOGLE_REDIRECT_URI="https://gbadvocacia.com/auth/google/callback"

# WhatsApp Business
WHATSAPP_ENABLED=true
WHATSAPP_API_URL="https://graph.facebook.com/v18.0"
WHATSAPP_TOKEN="seu_whatsapp_access_token"
WHATSAPP_PHONE_ID="seu_phone_number_id"
WHATSAPP_VERIFY_TOKEN="gb_advocacia_webhook_2024"

# Segurança
CORS_ORIGINS="https://gbadvocacia.com,https://www.gbadvocacia.com"
ENVIRONMENT="production"
DEBUG=false
```

### 9.2 Frontend .env

```bash
# /home/advocacia/gb-advocacia-sistema/frontend/.env
REACT_APP_BACKEND_URL=https://gbadvocacia.com
REACT_APP_ENVIRONMENT=production
GENERATE_SOURCEMAP=false
```

---

## 🚀 10. Deploy e Inicialização

### 10.1 Checklist Pré-Deploy

```bash
✅ Servidor configurado e atualizado
✅ PostgreSQL instalado e configurado
✅ Nginx configurado com SSL
✅ Supervisor configurado
✅ Backup automático configurado
✅ Firewall configurado
✅ Domínio apontando para servidor
✅ Certificado SSL ativo
✅ Variáveis de ambiente configuradas
✅ APIs Google e WhatsApp configuradas
```

### 10.2 Comandos de Deploy

```bash
# 1. Parar serviços
sudo supervisorctl stop all

# 2. Atualizar código
cd /home/advocacia/gb-advocacia-sistema
git pull origin main  # se usando Git

# 3. Atualizar backend
cd backend
source venv/bin/activate
pip install -r requirements.txt

# 4. Atualizar frontend
cd ../frontend
npm install
npm run build

# 5. Reiniciar serviços
sudo supervisorctl start all
sudo systemctl restart nginx

# 6. Verificar status
sudo supervisorctl status
curl -k https://gbadvocacia.com/api/dashboard
```

### 10.3 Comandos de Manutenção

```bash
# Verificar logs
sudo tail -f /var/log/supervisor/advocacia-backend.log
sudo tail -f /var/log/nginx/gbadvocacia_access.log

# Reiniciar serviços específicos
sudo supervisorctl restart advocacia-backend
sudo systemctl restart nginx

# Verificar banco de dados
sudo -u postgres psql gb_advocacia_db -c "SELECT COUNT(*) FROM clients;"

# Status geral do sistema
systemctl status nginx postgresql supervisor
```

---

## 📞 11. Suporte Pós-Instalação

### 11.1 Contatos
- **Admin Sistema:** admin@gbadvocacia.com
- **Suporte Técnico:** +55 54 99710-2525
- **Emergência:** 24h via WhatsApp

### 11.2 Documentação
- **Manual do Usuário:** Disponível no sistema
- **API Docs:** https://gbadvocacia.com/docs
- **Status:** https://gbadvocacia.com/status

### 11.3 Atualizações
- **Frequência:** Mensal ou conforme necessário
- **Janela:** Sábados 22h às 02h
- **Notificação:** 48h de antecedência

---

**🎉 SISTEMA INSTALADO E PRONTO PARA PRODUÇÃO!**

*Sistema Jurídico GB & N.Comin Advocacia - Versão Produção*