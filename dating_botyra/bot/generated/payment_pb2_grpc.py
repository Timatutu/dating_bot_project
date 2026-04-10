
import grpc
import warnings

from bot.generated import payment_pb2 as payment__pb2

GRPC_GENERATED_VERSION = '1.80.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + ' but the generated code in payment_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class PaymentServiceStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CreatePayment = channel.unary_unary(
                '/payment.PaymentService/CreatePayment',
                request_serializer=payment__pb2.CreatePaymentRequest.SerializeToString,
                response_deserializer=payment__pb2.CreatePaymentResponse.FromString,
                _registered_method=True)
        self.ConfirmPayment = channel.unary_unary(
                '/payment.PaymentService/ConfirmPayment',
                request_serializer=payment__pb2.ConfirmPaymentRequest.SerializeToString,
                response_deserializer=payment__pb2.ConfirmPaymentResponse.FromString,
                _registered_method=True)
        self.GetSubscription = channel.unary_unary(
                '/payment.PaymentService/GetSubscription',
                request_serializer=payment__pb2.GetSubscriptionRequest.SerializeToString,
                response_deserializer=payment__pb2.GetSubscriptionResponse.FromString,
                _registered_method=True)
        self.CreateCryptoPayment = channel.unary_unary(
                '/payment.PaymentService/CreateCryptoPayment',
                request_serializer=payment__pb2.CreateCryptoPaymentRequest.SerializeToString,
                response_deserializer=payment__pb2.CreateCryptoPaymentResponse.FromString,
                _registered_method=True)
        self.CheckCryptoPayment = channel.unary_unary(
                '/payment.PaymentService/CheckCryptoPayment',
                request_serializer=payment__pb2.CheckCryptoPaymentRequest.SerializeToString,
                response_deserializer=payment__pb2.CheckCryptoPaymentResponse.FromString,
                _registered_method=True)


class PaymentServiceServicer(object):
    """Missing associated documentation comment in .proto file."""

    def CreatePayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def ConfirmPayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetSubscription(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CreateCryptoPayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def CheckCryptoPayment(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_PaymentServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CreatePayment': grpc.unary_unary_rpc_method_handler(
                    servicer.CreatePayment,
                    request_deserializer=payment__pb2.CreatePaymentRequest.FromString,
                    response_serializer=payment__pb2.CreatePaymentResponse.SerializeToString,
            ),
            'ConfirmPayment': grpc.unary_unary_rpc_method_handler(
                    servicer.ConfirmPayment,
                    request_deserializer=payment__pb2.ConfirmPaymentRequest.FromString,
                    response_serializer=payment__pb2.ConfirmPaymentResponse.SerializeToString,
            ),
            'GetSubscription': grpc.unary_unary_rpc_method_handler(
                    servicer.GetSubscription,
                    request_deserializer=payment__pb2.GetSubscriptionRequest.FromString,
                    response_serializer=payment__pb2.GetSubscriptionResponse.SerializeToString,
            ),
            'CreateCryptoPayment': grpc.unary_unary_rpc_method_handler(
                    servicer.CreateCryptoPayment,
                    request_deserializer=payment__pb2.CreateCryptoPaymentRequest.FromString,
                    response_serializer=payment__pb2.CreateCryptoPaymentResponse.SerializeToString,
            ),
            'CheckCryptoPayment': grpc.unary_unary_rpc_method_handler(
                    servicer.CheckCryptoPayment,
                    request_deserializer=payment__pb2.CheckCryptoPaymentRequest.FromString,
                    response_serializer=payment__pb2.CheckCryptoPaymentResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'payment.PaymentService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('payment.PaymentService', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class PaymentService(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def CreatePayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/payment.PaymentService/CreatePayment',
            payment__pb2.CreatePaymentRequest.SerializeToString,
            payment__pb2.CreatePaymentResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def ConfirmPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/payment.PaymentService/ConfirmPayment',
            payment__pb2.ConfirmPaymentRequest.SerializeToString,
            payment__pb2.ConfirmPaymentResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def GetSubscription(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/payment.PaymentService/GetSubscription',
            payment__pb2.GetSubscriptionRequest.SerializeToString,
            payment__pb2.GetSubscriptionResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def CreateCryptoPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/payment.PaymentService/CreateCryptoPayment',
            payment__pb2.CreateCryptoPaymentRequest.SerializeToString,
            payment__pb2.CreateCryptoPaymentResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def CheckCryptoPayment(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/payment.PaymentService/CheckCryptoPayment',
            payment__pb2.CheckCryptoPaymentRequest.SerializeToString,
            payment__pb2.CheckCryptoPaymentResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
