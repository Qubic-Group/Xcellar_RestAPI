from celery import shared_task
from django.db import transaction as db_transaction
from django.db.models import Q, F
from django.utils import timezone
from django.conf import settings
from decimal import Decimal
import logging

from apps.payments.models import Transaction, Notification
from apps.payments.services.paystack_client import PaystackClient
from apps.accounts.models import UserProfile, CourierProfile

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_dva_deposit(self, event_data):
    """
    Process DVA deposit from Paystack webhook asynchronously.
    
    This task:
    1. Extracts transaction data from webhook
    2. Finds user by email/customer_code
    3. Checks for duplicate transactions (idempotency)
    4. Creates Transaction record
    5. Adds balance to user profile atomically
    6. Creates notification
    7. Logs the transaction
    
    Args:
        event_data: Paystack webhook event data containing transaction details
        
    Returns:
        dict: Result of processing
    """
    try:
        data = event_data.get('data', {})
        reference = data.get('reference')
        amount = data.get('amount', 0) / 100  # Convert from kobo to NGN
        customer_email = data.get('customer', {}).get('email')
        channel = data.get('channel', '')
        paystack_transaction_id = str(data.get('id', ''))
        
        # Validate required fields
        if not reference or not customer_email:
            logger.error(f"Missing required fields in webhook data: {event_data}")
            return {'status': 'error', 'message': 'Missing required fields'}
        
        # Find user by email
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            user = User.objects.get(email=customer_email)
        except User.DoesNotExist:
            logger.error(f"User not found for email: {customer_email}")
            # Retry in case user is created later
            raise self.retry(exc=Exception(f"User not found: {customer_email}"), countdown=300)
        
        # Use database transaction to ensure atomicity
        with db_transaction.atomic():
            # Check if transaction already exists (idempotency check)
            # Note: select_for_update() doesn't work with exists(), so we use get() in a try-except
            try:
                existing_transaction = Transaction.objects.select_for_update().get(
                    Q(reference=reference) | Q(paystack_reference=reference)
                )
                logger.info(f"Transaction already exists: {reference} (Status: {existing_transaction.status})")
                return {
                    'status': 'skipped',
                    'message': 'Transaction already processed',
                    'reference': reference,
                    'current_status': existing_transaction.status
                }
            except Transaction.DoesNotExist:
                pass  # Transaction doesn't exist, proceed with creation
            
            # Determine payment method
            payment_method = 'DVA' if channel == 'dedicated_nuban' else 'BANK_TRANSFER'
            
            # Create transaction record
            transaction_obj = Transaction.objects.create(
                user=user,
                transaction_type='DEPOSIT',
                status='PENDING',  # Will be updated to SUCCESS after balance update
                payment_method=payment_method,
                amount=Decimal(str(amount)),
                fee=Decimal('0.00'),
                net_amount=Decimal(str(amount)),
                reference=reference,
                paystack_transaction_id=paystack_transaction_id,
                paystack_reference=reference,
                description=f'Deposit via {channel}',
                metadata=data,
            )
            
            # Add balance to user profile atomically
            try:
                if user.user_type == 'USER':
                    profile = user.user_profile
                elif user.user_type == 'COURIER':
                    profile = user.courier_profile
                else:
                    logger.error(f"Unknown user type: {user.user_type}")
                    raise ValueError(f"Unknown user type: {user.user_type}")
                
                # Atomic balance update with F() expression
                updated = profile.__class__.objects.filter(
                    pk=profile.pk
                ).update(
                    balance=F('balance') + Decimal(str(amount)).quantize(Decimal('0.01'))
                )
                
                if updated != 1:
                    raise ValueError(f"Balance update failed: expected 1 row updated, got {updated}")
                
                # Refresh from database
                profile.refresh_from_db()
                
                # Update transaction status to SUCCESS
                transaction_obj.status = 'SUCCESS'
                transaction_obj.completed_at = timezone.now()
                transaction_obj.save()
                
                # Create notification
                Notification.objects.create(
                    user=user,
                    notification_type='DEPOSIT_RECEIVED',
                    title='Deposit Received',
                    message=f'You received ₦{amount:,.2f} via {channel}',
                    related_transaction=transaction_obj,
                    metadata={'channel': channel, 'sync_method': 'webhook'}
                )
                
                logger.info(
                    f"Deposit processed successfully: {reference} for user {user.email}. "
                    f"Amount: ₦{amount:,.2f}, New Balance: ₦{profile.balance:,.2f}"
                )
                
                return {
                    'status': 'success',
                    'message': 'Deposit processed successfully',
                    'reference': reference,
                    'amount': float(amount),
                    'user_email': user.email,
                    'new_balance': float(profile.balance)
                }
                
            except Exception as e:
                logger.error(f"Error updating balance for {user.email}: {e}", exc_info=True)
                # Update transaction status to FAILED
                transaction_obj.status = 'FAILED'
                transaction_obj.save()
                raise
        
    except Exception as e:
        logger.error(f"Error processing DVA deposit: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (2 ** self.request.retries))


@shared_task
def verify_dva_transaction(reference):
    """
    Verify a DVA transaction by calling Paystack API.
    
    This task can be used to verify transaction status
    if webhook processing fails or needs verification.
    
    Args:
        reference: Transaction reference to verify
        
    Returns:
        dict: Verification result
    """
    try:
        paystack_client = PaystackClient()
        response = paystack_client.verify_transaction(reference)
        
        if not response.get('status'):
            logger.warning(f"Transaction verification failed: {reference}")
            return {'status': 'error', 'message': response.get('message', 'Verification failed')}
        
        transaction_data = response.get('data', {})
        paystack_status = transaction_data.get('status', '').lower()  # Paystack returns lowercase
        amount = transaction_data.get('amount', 0) / 100
        
        # Map Paystack status to our Transaction model status
        status_mapping = {
            'success': 'SUCCESS',
            'failed': 'FAILED',
            'pending': 'PENDING',
            'reversed': 'REVERSED',
        }
        mapped_status = status_mapping.get(paystack_status, 'PENDING')
        
        # Find transaction in database
        try:
            transaction_obj = Transaction.objects.get(reference=reference)
            
            # Update status if different
            if transaction_obj.status != mapped_status:
                transaction_obj.status = mapped_status
                if mapped_status == 'SUCCESS':
                    transaction_obj.completed_at = timezone.now()
                transaction_obj.save()
                
                logger.info(f"Transaction {reference} status updated to {mapped_status} (Paystack: {paystack_status})")
            
            return {
                'status': 'success',
                'reference': reference,
                'paystack_status': paystack_status,
                'mapped_status': mapped_status,
                'amount': float(amount)
            }
            
        except Transaction.DoesNotExist:
            logger.warning(f"Transaction not found in database: {reference}")
            return {'status': 'error', 'message': 'Transaction not found'}
        
    except Exception as e:
        logger.error(f"Error verifying transaction {reference}: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}


@shared_task
def sync_pending_dva_transactions():
    """
    Periodic task to sync pending DVA transactions.
    
    This task:
    1. Finds transactions in PENDING status older than 30 seconds
    2. Verifies them with Paystack API
    3. Updates status accordingly
    
    This handles cases where webhooks are missed or delayed.
    
    Runs every 10 seconds via Celery Beat.
    """
    try:
        from datetime import timedelta
        
        # Find pending transactions older than 30 seconds
        # This prevents checking very recent transactions that might still be processing
        cutoff_time = timezone.now() - timedelta(seconds=30)
        pending_transactions = Transaction.objects.filter(
            transaction_type='DEPOSIT',
            status='PENDING',
            created_at__lt=cutoff_time
        )[:50]  # Process max 50 at a time
        
        logger.info(f"Syncing {pending_transactions.count()} pending transactions")
        
        paystack_client = PaystackClient()
        synced_count = 0
        
        for transaction in pending_transactions:
            try:
                # Verify transaction with Paystack
                response = paystack_client.verify_transaction(transaction.reference)
                
                if response.get('status'):
                    transaction_data = response.get('data', {})
                    paystack_status = transaction_data.get('status', '').lower()  # Paystack returns lowercase
                    
                    # Map Paystack status to our Transaction model status
                    status_mapping = {
                        'success': 'SUCCESS',
                        'failed': 'FAILED',
                        'pending': 'PENDING',
                        'reversed': 'REVERSED',
                    }
                    mapped_status = status_mapping.get(paystack_status, 'PENDING')
                    
                    if mapped_status == 'SUCCESS' and transaction.status == 'PENDING':
                        # Transaction was successful, update it
                        with db_transaction.atomic():
                            # Check again to avoid race condition
                            transaction.refresh_from_db()
                            if transaction.status != 'PENDING':
                                logger.info(f"Transaction {transaction.reference} already processed, skipping")
                                continue
                            
                            # Re-process the transaction
                            amount = Decimal(str(transaction_data.get('amount', 0) / 100))
                            
                            # Add balance
                            user = transaction.user
                            if user.user_type == 'USER':
                                profile = user.user_profile
                            elif user.user_type == 'COURIER':
                                profile = user.courier_profile
                            else:
                                continue
                            
                            profile.__class__.objects.filter(pk=profile.pk).update(
                                balance=F('balance') + amount.quantize(Decimal('0.01'))
                            )
                            
                            # Update transaction
                            transaction.status = 'SUCCESS'
                            transaction.completed_at = timezone.now()
                            transaction.metadata.update({'sync_method': 'periodic_sync'})
                            transaction.save()
                            
                            # Create notification if not exists
                            if not Notification.objects.filter(
                                related_transaction=transaction,
                                notification_type='DEPOSIT_RECEIVED'
                            ).exists():
                                Notification.objects.create(
                                    user=user,
                                    notification_type='DEPOSIT_RECEIVED',
                                    title='Deposit Received',
                                    message=f'You received ₦{amount:,.2f}',
                                    related_transaction=transaction,
                                    metadata={'sync_method': 'periodic_sync'}
                                )
                            
                            synced_count += 1
                            logger.info(f"Synced transaction {transaction.reference} via periodic sync")
                            
                    elif mapped_status == 'FAILED':
                        transaction.status = 'FAILED'
                        transaction.save()
                        logger.info(f"Transaction {transaction.reference} marked as failed")
                        
            except Exception as e:
                logger.error(f"Error syncing transaction {transaction.reference}: {e}", exc_info=True)
                continue
        
        logger.info(f"Periodic sync completed. Synced {synced_count} transactions")
        return {
            'status': 'success',
            'synced_count': synced_count,
            'total_checked': pending_transactions.count()
        }
        
    except Exception as e:
        logger.error(f"Error in periodic sync task: {e}", exc_info=True)
        return {'status': 'error', 'message': str(e)}

