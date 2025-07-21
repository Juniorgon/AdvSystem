"""
WhatsApp Business API Service for sending payment reminders
"""

from datetime import datetime, timedelta
import httpx
from typing import List, Dict, Any
import logging
import os
from motor.motor_asyncio import AsyncIOMotorDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WhatsAppService:
    def __init__(self):
        # Em produção, você usaria a WhatsApp Business API real
        # Por enquanto, vamos simular o envio de mensagens
        self.whatsapp_api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:3001")
        self.is_enabled = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"
    
    async def send_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Envia uma mensagem via WhatsApp Business API
        """
        if not self.is_enabled:
            logger.info(f"WhatsApp desabilitado - Simulando envio para {phone_number}: {message}")
            return {"success": True, "simulated": True}
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.whatsapp_api_url}/send",
                    json={
                        "phone_number": phone_number,
                        "message": message
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    logger.info(f"Mensagem enviada com sucesso para {phone_number}")
                    return {"success": True, "data": response.json()}
                else:
                    logger.error(f"Falha ao enviar mensagem para {phone_number}: {response.status_code}")
                    return {"success": False, "error": f"HTTP {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem WhatsApp: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def send_payment_reminder(self, client_name: str, phone_number: str, 
                                  contract_title: str, installment_value: float,
                                  due_date: datetime) -> Dict[str, Any]:
        """
        Envia lembrete de pagamento de parcela
        """
        message = self._format_payment_reminder_message(
            client_name, contract_title, installment_value, due_date
        )
        return await self.send_message(phone_number, message)
    
    async def send_overdue_notice(self, client_name: str, phone_number: str,
                                contract_title: str, installment_value: float,
                                days_overdue: int) -> Dict[str, Any]:
        """
        Envia aviso de parcela em atraso
        """
        message = self._format_overdue_notice_message(
            client_name, contract_title, installment_value, days_overdue
        )
        return await self.send_message(phone_number, message)
    
    def _format_payment_reminder_message(self, client_name: str, contract_title: str,
                                       installment_value: float, due_date: datetime) -> str:
        """
        Formata mensagem de lembrete de pagamento
        """
        formatted_value = f"R$ {installment_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        formatted_date = due_date.strftime("%d/%m/%Y")
        
        return f"""🏢 *GB & N.Comin Advocacia*

Olá *{client_name}*! 👋

📋 Lembrete de pagamento:
• Contrato: {contract_title}
• Valor da parcela: {formatted_value}
• Vencimento: {formatted_date}

💰 Para evitar atrasos, realize o pagamento até a data de vencimento.

📞 Em caso de dúvidas, entre em contato conosco pelo +55 54 99710-2525.

Atenciosamente,
GB & N.Comin Advocacia"""
    
    def _format_overdue_notice_message(self, client_name: str, contract_title: str,
                                     installment_value: float, days_overdue: int) -> str:
        """
        Formata mensagem de parcela em atraso
        """
        formatted_value = f"R$ {installment_value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return f"""🏢 *GB & N.Comin Advocacia*

Olá *{client_name}*! 👋

🚨 *PARCELA EM ATRASO*

📋 Informações da parcela:
• Contrato: {contract_title}
• Valor: {formatted_value}
• Dias em atraso: {days_overdue}

💰 *É importante regularizar o pagamento o quanto antes.*

📞 Entre em contato conosco para negociar ou esclarecer dúvidas.

Atenciosamente,
GB & N.Comin Advocacia"""


class PaymentReminderService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.whatsapp = WhatsAppService()
    
    async def check_and_send_reminders(self):
        """
        Verifica parcelas pendentes e envia lembretes via WhatsApp
        """
        # Buscar transações financeiras pendentes
        transactions_collection = self.db.financial_transactions
        clients_collection = self.db.clients
        contracts_collection = self.db.contracts
        
        # Data de hoje
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Buscar transações pendentes que vencem em 3 dias ou estão vencidas
        reminder_date = today + timedelta(days=3)
        
        pending_transactions = await transactions_collection.find({
            "status": "pendente",
            "due_date": {"$lte": reminder_date}
        }).to_list(length=100)
        
        logger.info(f"Encontradas {len(pending_transactions)} transações para verificar")
        
        for transaction in pending_transactions:
            try:
                # Buscar dados do cliente
                if "client_id" not in transaction:
                    continue
                    
                client = await clients_collection.find_one({"id": transaction["client_id"]})
                if not client or not client.get("phone"):
                    logger.warning(f"Cliente não encontrado ou sem telefone para transação {transaction.get('id')}")
                    continue
                
                # Calcular dias até vencimento ou dias de atraso
                due_date = transaction["due_date"]
                if isinstance(due_date, str):
                    due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                
                days_difference = (due_date.date() - today.date()).days
                
                if days_difference >= 0:
                    # Lembrete antes do vencimento
                    if days_difference <= 3:
                        result = await self.whatsapp.send_payment_reminder(
                            client_name=client["name"],
                            phone_number=client["phone"],
                            contract_title=transaction.get("description", "Pagamento"),
                            installment_value=transaction["value"],
                            due_date=due_date
                        )
                        
                        if result["success"]:
                            logger.info(f"Lembrete enviado para {client['name']} - {client['phone']}")
                        else:
                            logger.error(f"Falha ao enviar lembrete para {client['name']}: {result.get('error')}")
                
                else:
                    # Aviso de atraso
                    days_overdue = abs(days_difference)
                    result = await self.whatsapp.send_overdue_notice(
                        client_name=client["name"],
                        phone_number=client["phone"],
                        contract_title=transaction.get("description", "Pagamento"),
                        installment_value=transaction["value"],
                        days_overdue=days_overdue
                    )
                    
                    if result["success"]:
                        logger.info(f"Aviso de atraso enviado para {client['name']} - {client['phone']}")
                    else:
                        logger.error(f"Falha ao enviar aviso para {client['name']}: {result.get('error')}")
                        
            except Exception as e:
                logger.error(f"Erro ao processar transação {transaction.get('id')}: {str(e)}")
                continue
    
    async def send_manual_reminder(self, transaction_id: str) -> Dict[str, Any]:
        """
        Envia lembrete manual para uma transação específica
        """
        transactions_collection = self.db.financial_transactions
        clients_collection = self.db.clients
        
        # Buscar transação
        transaction = await transactions_collection.find_one({"id": transaction_id})
        if not transaction:
            return {"success": False, "error": "Transação não encontrada"}
        
        # Buscar cliente
        client = await clients_collection.find_one({"id": transaction.get("client_id")})
        if not client or not client.get("phone"):
            return {"success": False, "error": "Cliente não encontrado ou sem telefone"}
        
        # Enviar lembrete
        due_date = transaction["due_date"]
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
        
        result = await self.whatsapp.send_payment_reminder(
            client_name=client["name"],
            phone_number=client["phone"],
            contract_title=transaction.get("description", "Pagamento"),
            installment_value=transaction["value"],
            due_date=due_date
        )
        
        return result