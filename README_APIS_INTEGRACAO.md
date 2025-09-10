# 🔧 README - Configuração de APIs e Integrações

## Sistema Jurídico GB & N.Comin Advocacia
### Guia Completo de Integração: Google Drive, Google Calendar e WhatsApp Business

---

## 📋 Visão Geral

Este guia fornece instruções detalhadas para configurar as integrações finais do sistema:
- **Google Drive API** - Para geração e armazenamento de documentos (procurações)
- **Google Calendar API** - Para sincronização de tarefas e agendas dos advogados
- **WhatsApp Business API** - Para notificações automáticas de cobrança

---

## 🚀 Pré-requisitos

- Sistema jurídico funcionando (PostgreSQL, FastAPI, React)
- Conta Google Workspace ou Gmail
- Número WhatsApp Business verificado
- Acesso de administrador ao sistema

---

## 📂 1. GOOGLE DRIVE API - Configuração Completa

### 1.1 Criar Projeto no Google Cloud Console

```bash
# 1. Acesse: https://console.cloud.google.com/
# 2. Crie um novo projeto ou selecione existente
Nome do Projeto: "GB-Advocacia-Integracao"
```

### 1.2 Habilitar APIs Necessárias

```bash
# No Google Cloud Console:
1. Vá para "APIs & Services" > "Library"
2. Pesquise e HABILITE as seguintes APIs:
   - Google Drive API
   - Google Docs API
   - Google Sheets API (opcional)
```

### 1.3 Criar Conta de Serviço

```bash
# 1. APIs & Services > Credentials
# 2. CREATE CREDENTIALS > Service Account
Nome: gb-advocacia-service
ID: gb-advocacia-service@seu-projeto.iam.gserviceaccount.com
Role: Editor

# 3. Criar e baixar chave JSON
- Clique na conta criada
- Aba "Keys" > ADD KEY > Create new key
- Tipo: JSON
- Salvar como: google_drive_credentials.json
```

### 1.4 Configurar Estrutura de Pastas no Google Drive

```
📁 GB Advocacia - Sistema/
├── 📁 Templates/
│   ├── 📄 Template Procuração.docx
│   ├── 📄 Template Contrato.docx
│   └── 📄 Template Petição.docx
├── 📁 Clientes/
│   ├── 📁 [Nome Cliente 1]/
│   ├── 📁 [Nome Cliente 2]/
│   └── ...
└── 📁 Documentos Gerados/
    ├── 📁 Procurações/
    ├── 📁 Contratos/
    └── 📁 Petições/
```

### 1.5 Compartilhar Pastas com Conta de Serviço

```bash
# Para cada pasta criada:
1. Clique direito > Compartilhar
2. Adicionar email: gb-advocacia-service@seu-projeto.iam.gserviceaccount.com
3. Permissão: Editor
4. Copiar ID da pasta (da URL): https://drive.google.com/drive/folders/ID_DA_PASTA
```

### 1.6 Instalar Arquivo de Credenciais

```bash
# Copiar arquivo para o servidor
cp google_drive_credentials.json /app/backend/
chmod 600 /app/backend/google_drive_credentials.json
```

### 1.7 Configurar Variáveis de Ambiente

```bash
# Editar /app/backend/.env
nano /app/backend/.env

# Adicionar as seguintes linhas:
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_CREDENTIALS_FILE=/app/backend/google_drive_credentials.json
GOOGLE_DRIVE_FOLDER_TEMPLATES=ID_PASTA_TEMPLATES
GOOGLE_DRIVE_FOLDER_CLIENTS=ID_PASTA_CLIENTES
GOOGLE_DRIVE_FOLDER_DOCUMENTS=ID_PASTA_DOCUMENTOS
```

---

## 📅 2. GOOGLE CALENDAR API - Configuração Completa

### 2.1 Habilitar Google Calendar API

```bash
# No mesmo projeto Google Cloud:
1. APIs & Services > Library
2. Pesquise "Google Calendar API"
3. Clique ENABLE
```

### 2.2 Usar a Mesma Conta de Serviço

```bash
# A conta de serviço criada anteriormente já pode acessar Calendar
# Apenas adicione as permissões necessárias:
1. IAM & Admin > IAM
2. Encontre: gb-advocacia-service@seu-projeto.iam.gserviceaccount.com
3. Edit > Add Another Role > "Calendar API Service Agent"
```

### 2.3 Configurar Calendários dos Advogados

```bash
# Para cada advogado:
1. Criar calendário específico no Google Calendar
   Nome: "Escritório - [Nome do Advogado]"
   
2. Compartilhar calendário com conta de serviço:
   - Configurações do calendário
   - Compartilhar com pessoas específicas
   - Email: gb-advocacia-service@seu-projeto.iam.gserviceaccount.com
   - Permissão: "Fazer alterações nos eventos"
   
3. Copiar ID do calendário:
   - Configurações do calendário > Integrar calendário
   - Copiar "ID do calendário"
```

### 2.4 Configurar Variáveis Calendar

```bash
# Adicionar ao .env
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_CREDENTIALS_FILE=/app/backend/google_drive_credentials.json
GOOGLE_CALENDAR_TIMEZONE=America/Sao_Paulo

# IDs dos calendários (um para cada advogado)
CALENDAR_ADVOGADO_1=calendario1@group.calendar.google.com
CALENDAR_ADVOGADO_2=calendario2@group.calendar.google.com
# Adicione conforme necessário
```

---

## 📱 3. WHATSAPP BUSINESS API - Configuração Completa

### 3.1 Opção A: Meta Business (Recomendado)

#### 3.1.1 Criar Conta Meta Business

```bash
# 1. Acesse: https://business.facebook.com/
# 2. Criar conta empresarial
Nome da Empresa: "GB & N.Comin Advocacia"
```

#### 3.1.2 Configurar WhatsApp Business API

```bash
# 1. Acesse: https://developers.facebook.com/
# 2. Meus Apps > Criar App
Tipo: Business
Nome: "GB Advocacia WhatsApp"

# 3. Adicionar produto WhatsApp
- No painel do app > Adicionar produto
- Selecionar "WhatsApp" > Configurar
```

#### 3.1.3 Verificar Número de Telefone

```bash
# No painel WhatsApp Business API:
1. Números de telefone > Adicionar número
2. Inserir: +55 54 99710-2525 (ou seu número)
3. Método de verificação: SMS ou chamada
4. Inserir código recebido
```

#### 3.1.4 Obter Credenciais

```bash
# Após configuração:
1. WhatsApp > Introdução
2. Copiar informações:
   - Phone Number ID: 123456789012345
   - Access Token: EAAXXXXXXXXXXXXXXXXXXXX
   - App ID: 987654321
   - App Secret: abcdef1234567890
```

### 3.2 Opção B: Provedor Terceirizado (Alternativa)

#### 3.2.1 Twilio WhatsApp API

```bash
# 1. Criar conta: https://www.twilio.com/
# 2. Console > Messaging > Try it out > Send a WhatsApp message
# 3. Obter credenciais:
Account SID: ACxxxxxxxxxxxxxxxxxxxx
Auth Token: your_auth_token_here
WhatsApp Number: +14155238886
```

### 3.3 Configurar Variáveis WhatsApp

```bash
# Opção A - Meta Business (adicionar ao .env)
WHATSAPP_ENABLED=true
WHATSAPP_PROVIDER=meta
WHATSAPP_API_URL=https://graph.facebook.com/v18.0
WHATSAPP_ACCESS_TOKEN=SEU_ACCESS_TOKEN
WHATSAPP_PHONE_NUMBER_ID=SEU_PHONE_NUMBER_ID
WHATSAPP_APP_SECRET=SEU_APP_SECRET
WHATSAPP_VERIFY_TOKEN=gb_advocacia_2024

# Opção B - Twilio (alternativo)
# WHATSAPP_ENABLED=true
# WHATSAPP_PROVIDER=twilio
# TWILIO_ACCOUNT_SID=SEU_ACCOUNT_SID
# TWILIO_AUTH_TOKEN=SEU_AUTH_TOKEN
# TWILIO_WHATSAPP_NUMBER=+14155238886
```

---

## 🛠️ 4. Instalação e Configuração Final

### 4.1 Instalar Dependências Python

```bash
cd /app/backend

# Adicionar ao requirements.txt
echo "google-api-python-client==2.111.0" >> requirements.txt
echo "google-auth-httplib2==0.1.1" >> requirements.txt
echo "google-auth-oauthlib==1.1.0" >> requirements.txt
echo "google-auth==2.23.4" >> requirements.txt

# Instalar dependências
pip install -r requirements.txt
```

### 4.2 Criar Serviços de Integração

```bash
# Arquivo já existe: /app/backend/google_drive_service.py
# Arquivo já existe: /app/backend/whatsapp_service.py

# Criar novo arquivo para Calendar
nano /app/backend/google_calendar_service.py
```

### 4.3 Exemplo de Arquivo Calendar Service

```python
# /app/backend/google_calendar_service.py
import os
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import logging

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self):
        self.credentials_file = os.environ.get('GOOGLE_CALENDAR_CREDENTIALS_FILE')
        self.timezone = os.environ.get('GOOGLE_CALENDAR_TIMEZONE', 'America/Sao_Paulo')
        self.service = None
        
    def authenticate(self):
        """Authenticate with Google Calendar API"""
        try:
            if not os.path.exists(self.credentials_file):
                return False
                
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=['https://www.googleapis.com/auth/calendar']
            )
            
            self.service = build('calendar', 'v3', credentials=credentials)
            return True
            
        except Exception as e:
            logger.error(f"Calendar authentication error: {e}")
            return False
    
    def create_task_event(self, calendar_id, task_title, task_description, due_date, lawyer_email):
        """Create calendar event for task"""
        if not self.service:
            if not self.authenticate():
                return {"success": False, "error": "Authentication failed"}
        
        try:
            event = {
                'summary': f'📋 {task_title}',
                'description': task_description,
                'start': {
                    'dateTime': due_date.isoformat(),
                    'timeZone': self.timezone,
                },
                'end': {
                    'dateTime': (due_date + timedelta(hours=1)).isoformat(),
                    'timeZone': self.timezone,
                },
                'attendees': [
                    {'email': lawyer_email}
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 min before
                    ],
                },
            }
            
            created_event = self.service.events().insert(
                calendarId=calendar_id, 
                body=event
            ).execute()
            
            return {
                "success": True, 
                "event_id": created_event.get('id'),
                "event_url": created_event.get('htmlLink')
            }
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"success": False, "error": str(e)}
```

### 4.4 Atualizar Backend Principal

```python
# Adicionar ao /app/backend/server.py
from google_calendar_service import GoogleCalendarService

# Instanciar serviço
calendar_service = GoogleCalendarService()

# Adicionar endpoint de teste
@api_router.get("/calendar/status")
async def get_calendar_status(current_user: User = Depends(get_current_user)):
    """Get Calendar integration status"""
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    authenticated = calendar_service.authenticate()
    
    return {
        "configured": authenticated,
        "timezone": os.environ.get('GOOGLE_CALENDAR_TIMEZONE'),
        "service_available": True
    }
```

---

## ✅ 5. Testes e Verificação

### 5.1 Testar Google Drive

```bash
# No sistema web:
1. Login como admin
2. Aba Documentos
3. Verificar status: "Google Drive integration is ready"
4. Criar cliente e gerar procuração
5. Verificar se documento aparece no Google Drive
```

### 5.2 Testar Google Calendar

```bash
# No sistema web:
1. Aba Tarefas
2. Criar nova tarefa para advogado
3. Verificar se evento aparece no Google Calendar do advogado
4. Confirmar notificações por email
```

### 5.3 Testar WhatsApp

```bash
# No sistema web:
1. Aba WhatsApp
2. Status deve mostrar "production" (não "simulation")
3. Enviar mensagem de teste
4. Verificar recebimento no WhatsApp
5. Testar lembrete de pagamento
```

### 5.4 Comandos de Teste Direct API

```bash
# Testar Google Drive
curl -X GET "http://localhost:8001/api/google-drive/status" \
     -H "Authorization: Bearer SEU_TOKEN"

# Testar Calendar
curl -X GET "http://localhost:8001/api/calendar/status" \
     -H "Authorization: Bearer SEU_TOKEN"

# Testar WhatsApp
curl -X GET "http://localhost:8001/api/whatsapp/status" \
     -H "Authorization: Bearer SEU_TOKEN"
```

---

## 🔐 6. Segurança e Melhores Práticas

### 6.1 Proteger Credenciais

```bash
# Definir permissões corretas
chmod 600 /app/backend/google_drive_credentials.json
chown backend-user:backend-group /app/backend/.env

# Adicionar ao .gitignore
echo "google_drive_credentials.json" >> .gitignore
echo ".env" >> .gitignore
```

### 6.2 Backup das Configurações

```bash
# Criar backup das configurações
cp /app/backend/.env /app/backend/.env.backup
tar -czf integracao_backup.tar.gz \
    /app/backend/google_drive_credentials.json \
    /app/backend/.env
```

### 6.3 Monitoramento

```bash
# Logs das integrações
tail -f /var/log/supervisor/backend.*.log | grep -E "google|whatsapp|calendar"

# Verificar uso das APIs (Google Console)
# Monitoring > Metrics Explorer
# Resource: consumed_api
```

---

## 🚨 7. Solução de Problemas

### 7.1 Problemas Comuns Google APIs

**Erro 403 - Forbidden:**
```bash
# Verificar:
1. API está habilitada no Google Console?
2. Conta de serviço tem permissões corretas?
3. Pasta/calendário foi compartilhado com a conta de serviço?
```

**Erro 404 - Not Found:**
```bash
# Verificar:
1. IDs de pasta/calendário estão corretos?
2. Recursos foram deletados ou movidos?
```

### 7.2 Problemas WhatsApp

**Mensagens não enviadas:**
```bash
# Verificar:
1. Access Token está válido?
2. Número está verificado no Meta Business?
3. Número destinatário tem WhatsApp?
4. Não excedeu limite de mensagens?
```

### 7.3 Logs Detalhados

```bash
# Habilitar debug no backend
export LOG_LEVEL=DEBUG

# Ver logs específicos
tail -f /var/log/supervisor/backend.*.log | grep -A5 -B5 "ERROR"
```

---

## 📞 8. Suporte e Contatos

### 8.1 Documentação Oficial
- Google Drive API: https://developers.google.com/drive/api
- Google Calendar API: https://developers.google.com/calendar/api
- WhatsApp Business API: https://developers.facebook.com/docs/whatsapp

### 8.2 Limites e Quotas
- Google APIs: 10,000 requests/dia (padrão)
- WhatsApp: 1,000 mensagens/mês (gratuito)
- Upgrade conforme necessidade

### 8.3 Contato Técnico
- Email: admin@gbadvocacia.com
- Sistema: Aba Configurações > Suporte
- WhatsApp: +55 54 99710-2525

---

## 🎯 9. Checklist Final

```bash
✅ Projeto Google Cloud criado
✅ APIs habilitadas (Drive, Calendar)
✅ Conta de serviço criada e configurada
✅ Arquivo de credenciais instalado
✅ Estrutura de pastas no Google Drive criada
✅ Calendários dos advogados configurados
✅ WhatsApp Business configurado e verificado
✅ Variáveis de ambiente configuradas
✅ Dependências Python instaladas
✅ Serviços backend atualizados
✅ Testes realizados em todas as integrações
✅ Sistema em produção funcionando
```

**🚀 SISTEMA COMPLETO COM TODAS AS INTEGRAÇÕES ATIVAS!**

---

*Desenvolvido para GB & N.Comin Advocacia - Sistema Jurídico Integrado*