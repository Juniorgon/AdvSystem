# 📅 Guia de Integração - Google Calendar e Email

## 🎯 Visão Geral
Este guia explica como configurar as integrações de Google Calendar (para advogados) e Email (para administradores) no sistema jurídico.

---

## 📅 CONFIGURAÇÃO GOOGLE CALENDAR

### 1. Criar Projeto Google Cloud Console

1. **Acesse:** https://console.cloud.google.com/
2. **Criar Projeto:**
   ```
   ➤ Clique "Select a project" → "NEW PROJECT"
   ➤ Nome: "GB-Advocacia-Calendar"
   ➤ Clique "CREATE"
   ```

### 2. Habilitar Google Calendar API

```
➤ APIs & Services → Library
➤ Pesquise "Google Calendar API"
➤ Clique "ENABLE"
```

### 3. Criar Credenciais de Serviço

```
➤ APIs & Services → Credentials
➤ CREATE CREDENTIALS → Service Account
➤ Nome: "gb-advocacia-calendar"
➤ Role: Editor
➤ CREATE KEY → JSON
➤ Salvar como: /app/backend/calendar_credentials.json
```

### 4. Configurar Variáveis de Ambiente

Adicione no `/app/backend/.env`:
```env
# Google Calendar Integration
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_CREDENTIALS_FILE=/app/backend/calendar_credentials.json
GOOGLE_CALENDAR_DEFAULT_TIMEZONE=America/Sao_Paulo
```

### 5. Compartilhar Calendários

Cada advogado deve:
1. Criar um Google Calendar específico para o escritório
2. Compartilhar com a conta de serviço (email da service account)
3. Informar o Calendar ID no sistema

---

## 📧 CONFIGURAÇÃO EMAIL/SMTP

### Opção A: Gmail SMTP

1. **Ativar 2FA na conta Gmail**
2. **Gerar App Password:**
   ```
   ➤ Google Account → Security → App Passwords
   ➤ Gerar senha para "Mail"
   ➤ Copiar a senha gerada
   ```

3. **Configurar .env:**
```env
# Email Configuration
EMAIL_ENABLED=true
EMAIL_PROVIDER=gmail
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=administrador@gbadvocacia.com
SMTP_PASSWORD=sua_app_password_aqui
EMAIL_FROM=administrador@gbadvocacia.com
```

### Opção B: SendGrid

1. **Criar conta:** https://sendgrid.com/
2. **Obter API Key:**
   ```
   ➤ Settings → API Keys → Create API Key
   ➤ Copiar a chave gerada
   ```

3. **Configurar .env:**
```env
# Email Configuration  
EMAIL_ENABLED=true
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=sua_api_key_aqui
EMAIL_FROM=administrador@gbadvocacia.com
```

---

## 🔧 IMPLEMENTAÇÃO NO SISTEMA

### 1. Funcionalidades que Serão Integradas

**Google Calendar:**
- ✅ Criação automática de eventos para tarefas
- ✅ Sincronização de prazos processuais
- ✅ Lembretes de audiências
- ✅ Atualização automática de status

**Email Notifications:**
- ✅ Notificações de novas tarefas para admin
- ✅ Relatórios diários de atividades
- ✅ Alertas de prazos vencendo
- ✅ Resumos semanais/mensais

### 2. Arquivos que Serão Modificados

```
/app/backend/
├── calendar_service.py      # Serviço Google Calendar
├── email_service.py         # Serviço de Email
├── notification_service.py  # Coordenador de notificações
├── scheduler.py             # Tarefas agendadas
└── server.py               # Endpoints de integração
```

### 3. Novos Endpoints da API

```
GET  /api/calendar/status           # Status da integração
POST /api/calendar/sync-tasks       # Sincronizar tarefas
GET  /api/calendar/events          # Listar eventos

GET  /api/email/status             # Status do email
POST /api/email/send-notification  # Enviar notificação
POST /api/email/test               # Testar configuração
```

---

## 📋 CHECKLIST DE CONFIGURAÇÃO

### Pré-requisitos:
- [ ] Projeto Google Cloud criado
- [ ] Calendar API habilitada
- [ ] Service Account criada e arquivo JSON baixado
- [ ] Conta de email configurada (Gmail/SendGrid)
- [ ] Credenciais de email obtidas

### Configuração:
- [ ] Arquivo calendar_credentials.json copiado para backend
- [ ] Variáveis de ambiente configuradas no .env
- [ ] Calendários dos advogados compartilhados
- [ ] Teste de envio de email realizado
- [ ] Teste de criação de evento no calendar realizado

### Pós-Configuração:
- [ ] Verificar logs do sistema
- [ ] Testar criação de tarefa → evento no calendar
- [ ] Testar notificação por email
- [ ] Configurar agendamento automático (scheduler)

---

## 🚨 SOLUÇÃO DE PROBLEMAS

### Google Calendar
- **Erro 403:** Verificar se Calendar API está habilitada
- **Erro 404:** Verificar se Calendar ID está correto
- **Erro 401:** Verificar credenciais do service account

### Email
- **Erro SMTP:** Verificar servidor e porta
- **Erro 535:** Verificar usuário e senha
- **Gmail rejeitando:** Verificar se App Password foi usado

---

## 📞 SUPORTE

Após implementação, o sistema terá:
- Interface para configurar calendários dos advogados
- Painel de status das integrações
- Logs detalhados de operações
- Testes automáticos de conectividade

**Contato técnico:** suporte@gbadvocacia.com