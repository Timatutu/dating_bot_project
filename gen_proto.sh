#!/usr/bin/env bash

set -e

PROTO_DIR="proto"
PROTO_FILE="$PROTO_DIR/payment.proto"

PAYMENT_OUT="dating_payment_botyra/src/generated"
BOT_OUT="dating_botyra/bot/generated"

mkdir -p "$PAYMENT_OUT" "$BOT_OUT"

python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  --python_out="$PAYMENT_OUT" \
  --grpc_python_out="$PAYMENT_OUT" \
  "$PROTO_FILE"

python -m grpc_tools.protoc \
  -I "$PROTO_DIR" \
  --python_out="$BOT_OUT" \
  --grpc_python_out="$BOT_OUT" \
  "$PROTO_FILE"

sed -i 's/^import payment_pb2/from bot.generated import payment_pb2/' \
  "$BOT_OUT/payment_pb2_grpc.py"

sed -i 's/^import payment_pb2/from src.generated import payment_pb2/' \
  "$PAYMENT_OUT/payment_pb2_grpc.py"

echo "Done. Stubs written to:"
echo "  $PAYMENT_OUT"
echo "  $BOT_OUT"
