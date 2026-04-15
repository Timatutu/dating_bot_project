from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.UniqueConstraint("email", name="uq_customers_email"),
    )

    op.create_table(
        "products",
        sa.Column("product_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
    )

    op.create_table(
        "orders",
        sa.Column("order_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("order_date", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("total_amount", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.customer_id"], ondelete="RESTRICT"),
    )

    op.create_table(
        "order_items",
        sa.Column("order_item_id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.Numeric(14, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.order_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.product_id"], ondelete="RESTRICT"),
    )


def downgrade() -> None:
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("customers")
