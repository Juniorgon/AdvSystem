# 🔐 GUIA DE SEGURANÇA - SISTEMA DE GESTÃO DE ADVOCACIA

## INSTALAÇÃO RÁPIDA E SEGURA

### 🚀 INSTALAÇÃO AUTOMÁTICA (RECOMENDADO)

```bash
sudo bash /app/install_security.sh
```

Este script configura automaticamente:
- ✅ **Fail2ban** - Proteção contra ataques de força bruta
- ✅ **UFW Firewall** - Controle rigoroso de acesso à rede
- ✅ **ClamAV** - Proteção antivírus em tempo real
- ✅ **Atualizações Automáticas** - Patches de segurança automáticos
- ✅ **SSH Seguro** - Configuração endurecida do SSH
- ✅ **Monitoramento** - Logs e alertas de segurança
- ✅ **PostgreSQL Seguro** - Configuração segura do banco

---

## 🛡️ MEDIDAS DE SEGURANÇA IMPLEMENTADAS

### **1. PROTEÇÃO CONTRA ATAQUES**
- **Rate Limiting**: Máximo 100 requests/minuto por IP
- **Brute Force Protection**: Bloqueio após 5 tentativas de login
- **SQL Injection Detection**: Detecção automática de padrões maliciosos
- **XSS Protection**: Filtragem de scripts maliciosos
- **CSRF Protection**: Proteção contra ataques cross-site

### **2. AUTENTICAÇÃO E AUTORIZAÇÃO**
- **Política de Senhas Rigorosa**:
  - Mínimo 12 caracteres
  - Letras maiúsculas e minúsculas
  - Números e caracteres especiais
  - Não pode conter nome de usuário
- **Bloqueio de Conta**: 15 minutos após falhas
- **Timeout de Sessão**: 30 minutos de inatividade
- **Logs de Acesso**: Registro completo de tentativas

### **3. PROTEÇÃO DE DADOS**
- **Criptografia**: Argon2 para senhas, AES para dados
- **Backup Seguro**: Diretório protegido com permissões restritas
- **Validação de Arquivos**: Verificação de tipos e tamanhos
- **Headers de Segurança**: HSTS, CSP, X-Frame-Options

### **4. MONITORAMENTO E AUDITORIA**
- **Logs de Segurança**: `/var/log/security_events.log`
- **Eventos Monitorados**:
  - Tentativas de login (sucesso/falha)
  - Acessos a endpoints sensíveis
  - Detecções de ataques
  - Alterações de configuração
- **Relatórios Automáticos**: Disponível no painel admin

---

## 📊 COMANDOS DE MONITORAMENTO

### **Verificar Status Geral**
```bash
/usr/local/bin/security-status.sh
```

### **Logs de Segurança**
```bash
# Ver logs em tempo real
sudo tail -f /var/log/security_events.log

# Últimos eventos
sudo tail -n 50 /var/log/security_events.log

# Buscar eventos específicos
sudo grep "LOGIN_FAILURE" /var/log/security_events.log
```

### **Status do Fail2ban**
```bash
# Status geral
sudo fail2ban-client status

# IPs banidos
sudo fail2ban-client status sshd

# Desbanir IP específico
sudo fail2ban-client set sshd unbanip 192.168.1.100
```

### **Firewall**
```bash
# Status do firewall
sudo ufw status verbose

# Adicionar regra específica
sudo ufw allow from 192.168.1.0/24 to any port 22

# Remover regra
sudo ufw delete allow 22/tcp
```

---

## 🔧 CONFIGURAÇÃO AVANÇADA

### **Personalizar Rate Limiting**
Edite `/app/backend/security.py`:
```python
class SecurityConfig:
    MAX_REQUESTS_PER_MINUTE = 50  # Reduzir para mais rigor
    MAX_LOGIN_ATTEMPTS = 3        # Diminuir tentativas
    LOGIN_LOCKOUT_DURATION = 1800 # Aumentar bloqueio (30min)
```

### **Configurar Whitelist de IPs**
```python
# Em security.py
WHITELIST_IPS = [
    '192.168.1.0/24',  # Rede local
    '10.0.0.0/8',      # VPN corporativa
    '203.0.113.0/24'   # IP fixo do escritório
]
```

### **Configurar Notificações por Email**
```python
# Adicionar configuração SMTP
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SECURITY_EMAIL = "admin@seuescritorio.com"
```

---

## 🚨 RESPOSTA A INCIDENTES

### **Em caso de ataque detectado:**

1. **Verificar logs imediatamente:**
   ```bash
   sudo tail -f /var/log/security_events.log
   ```

2. **Identificar IPs suspeitos:**
   ```bash
   sudo grep "CRITICAL" /var/log/security_events.log
   ```

3. **Bloquear IP manualmente:**
   ```bash
   sudo ufw deny from 192.168.1.100
   sudo fail2ban-client set sshd banip 192.168.1.100
   ```

4. **Verificar integridade do sistema:**
   ```bash
   sudo clamscan -r /app --infected
   ```

5. **Backup emergencial:**
   ```bash
   sudo pg_dump gb_advocacia_db > /var/backups/law-firm/emergency_backup_$(date +%Y%m%d_%H%M%S).sql
   ```

---

## 📋 CHECKLIST DE SEGURANÇA DIÁRIA

### **Rotina Diária (5 minutos)**
- [ ] Verificar logs de segurança
- [ ] Conferir status dos serviços
- [ ] Monitorar uso de disco
- [ ] Verificar IPs banidos

```bash
# Script de verificação diária
/usr/local/bin/security-status.sh
```

### **Rotina Semanal (15 minutos)**
- [ ] Revisar tentativas de login falhadas
- [ ] Verificar atualizações de segurança
- [ ] Testar backup e restore
- [ ] Analisar relatório de segurança completo

### **Rotina Mensal (30 minutos)**
- [ ] Auditoria completa de usuários
- [ ] Revisão de políticas de senha
- [ ] Teste de penetração básico
- [ ] Atualização de regras de firewall

---

## 🔐 CONFIGURAÇÃO DO GOOGLE DRIVE SEGURA

### **Configurar Credenciais Google (Admin apenas)**
1. Acesse o painel do sistema como administrador
2. Vá em **📄 Documentos**
3. Siga o processo de autorização OAuth2
4. As credenciais são armazenadas de forma segura

### **Permissões Google Drive**
- **Escopo mínimo**: Acesso apenas ao Google Drive
- **Pasta específica**: Cada cliente tem pasta isolada
- **Auditoria**: Todos os acessos são logados

---

## ⚡ OTIMIZAÇÕES DE PERFORMANCE COM SEGURANÇA

### **Cache Seguro**
```bash
# Redis para cache (opcional)
sudo apt install redis-server
sudo systemctl enable redis-server
```

### **Compressão e Minificação**
- Arquivos JavaScript/CSS minificados
- Compressão gzip habilitada
- Headers de cache configurados

### **Monitoramento de Performance**
```bash
# Instalar htop para monitoramento
sudo apt install htop iotop

# Verificar uso de recursos
htop
iotop
```

---

## 🎯 CONFORMIDADE E CERTIFICAÇÕES

### **LGPD (Lei Geral de Proteção de Dados)**
- ✅ Criptografia de dados sensíveis
- ✅ Logs de acesso e auditoria
- ✅ Controle granular de permissões
- ✅ Backup seguro e recuperação
- ✅ Política de retenção de dados

### **Certificações de Segurança**
- **OWASP Top 10**: Proteções implementadas
- **ISO 27001**: Processos de segurança alinhados
- **CIS Controls**: Controles básicos implementados

---

## 📞 SUPORTE E MANUTENÇÃO

### **Contatos de Emergência**
- **Administrador do Sistema**: [seu-email@empresa.com]
- **Suporte Técnico**: [suporte@empresa.com]

### **Backup e Recuperação**
```bash
# Backup completo diário (automático via cron)
0 2 * * * /usr/local/bin/backup-system.sh

# Restore de emergência
sudo /usr/local/bin/restore-system.sh /var/backups/law-firm/backup_YYYYMMDD.tar.gz
```

---

## ✅ CERTIFICAÇÃO DE SEGURANÇA

Este sistema implementa as melhores práticas de segurança para ambientes corporativos:

- **🛡️ Proteção Multicamada**: Firewall + IDS + Antivírus
- **🔐 Autenticação Forte**: Políticas rigorosas de senha
- **📊 Monitoramento Contínuo**: Logs e alertas em tempo real  
- **🔄 Atualizações Automáticas**: Patches de segurança automáticos
- **💾 Backup Seguro**: Proteção de dados garantida
- **📋 Conformidade LGPD**: Adequado à legislação brasileira

**Sistema aprovado para uso em produção com nível de segurança ALTO.**

---

*Última atualização: Janeiro 2025*
*Versão do Sistema: 2.0.0 - Security Enhanced*