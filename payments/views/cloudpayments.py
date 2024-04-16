import json
import logging

from django.http import HttpResponse

from payments.cloudpayments import CLOUDPAYMENTS_PRODUCTS, CloudPaymentsService, TransactionStatus
from payments.models import Payment
from users.models.user import User

log = logging.getLogger()


def cloudpayments_webhook(request):
    pay_service = CloudPaymentsService()
    is_verified = pay_service.verify_webhook(request)

    if not is_verified:
        # TODO: на время начальной работы игнорируем ошибки верификации
        log.error("Request is not verified %r", request.POST)

    action = request.GET["action"]
    payload = request.POST

    status, answer = pay_service.accept_payment(action, payload)

    if status == TransactionStatus.APPROVED:
        payment = Payment.finish(
            reference=payload["InvoiceId"],
            status=Payment.STATUS_SUCCESS,
            data=payload,
        )

        product = CLOUDPAYMENTS_PRODUCTS[payment.product_code]
        product["activator"](product, payment, payment.user)

        # if payment.user.moderation_status != User.MODERATION_STATUS_APPROVED:
        #     send_payed_email(payment.user)

    return HttpResponse(json.dumps(answer))
