"""
Scheduler service para verificação automática de parcelas pendentes
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import logging
from whatsapp_service import PaymentReminderService
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class PaymentScheduler:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.scheduler = AsyncIOScheduler()
        self.payment_service = PaymentReminderService(db)
        self.setup_jobs()
    
    def setup_jobs(self):
        """
        Configura os jobs de verificação de pagamentos
        """
        # Verificar todos os dias às 9:00 da manhã
        self.scheduler.add_job(
            func=self.check_payments,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_payment_check',
            name='Verificação diária de pagamentos',
            replace_existing=True
        )
        
        # Verificação adicional às 14:00 (tarde)
        self.scheduler.add_job(
            func=self.check_payments,
            trigger=CronTrigger(hour=14, minute=0),
            id='afternoon_payment_check',
            name='Verificação vespertina de pagamentos',
            replace_existing=True
        )
        
        logger.info("Jobs de verificação de pagamento configurados")
    
    async def check_payments(self):
        """
        Executa verificação de pagamentos
        """
        try:
            logger.info(f"Iniciando verificação de pagamentos às {datetime.now()}")
            await self.payment_service.check_and_send_reminders()
            logger.info("Verificação de pagamentos concluída")
        except Exception as e:
            logger.error(f"Erro na verificação de pagamentos: {str(e)}")
    
    def start(self):
        """
        Inicia o scheduler
        """
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Scheduler de pagamentos iniciado")
    
    def stop(self):
        """
        Para o scheduler
        """
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler de pagamentos parado")
    
    def get_jobs_status(self):
        """
        Retorna status dos jobs
        """
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        return jobs