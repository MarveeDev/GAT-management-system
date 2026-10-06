"""add REVIEW SMS status

Revision ID: a1b2c3d4e5f6
Revises: 7d2c9a5e1b4f
Create Date: 2026-10-06 00:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '7d2c9a5e1b4f'
branch_labels = None
depends_on = None


def upgrade():
    # Adds a REVIEW status for SMS logs whose delivery outcome is unknown
    # (stale PENDING resolved manually). These must not be auto-retried.
    with op.batch_alter_table('sms_logs', schema=None) as batch_op:
        batch_op.drop_constraint('ck_sms_logs_status', type_='check')
        batch_op.create_check_constraint(
            'ck_sms_logs_status',
            "status IN ('PENDING', 'SENT', 'FAILED', 'REVIEW')",
        )


def downgrade():
    with op.batch_alter_table('sms_logs', schema=None) as batch_op:
        batch_op.drop_constraint('ck_sms_logs_status', type_='check')
        batch_op.create_check_constraint(
            'ck_sms_logs_status',
            "status IN ('PENDING', 'SENT', 'FAILED')",
        )
