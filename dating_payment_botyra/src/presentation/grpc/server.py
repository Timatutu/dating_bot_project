import logging

import grpc
from grpc import aio

from src.generated import payment_pb2_grpc
from src.presentation.grpc.servicer import PaymentServicer

logger = logging.getLogger(__name__)

GRPC_PORT = 50051


async def create_grpc_server() -> aio.Server:
    server = aio.server()
    payment_pb2_grpc.add_PaymentServiceServicer_to_server(PaymentServicer(), server)
    server.add_insecure_port(f"[::]:{GRPC_PORT}")
    return server


async def start_grpc_server() -> aio.Server:
    server = await create_grpc_server()
    await server.start()
    logger.info("gRPC server started on port %d", GRPC_PORT)
    return server


async def stop_grpc_server(server: aio.Server) -> None:
    await server.stop(grace=5)
    logger.info("gRPC server stopped")
