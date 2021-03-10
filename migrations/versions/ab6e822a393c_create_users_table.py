"""Create users table

Revision ID: ab6e822a393c
Revises: 
Create Date: 2021-03-10 13:20:10.146357

"""
from alembic import op
import sqlalchemy


# revision identifiers, used by Alembic.
revision = 'ab6e822a393c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'users',
        sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
        sqlalchemy.Column("username", sqlalchemy.String),
        sqlalchemy.Column("password", sqlalchemy.String),
    )


def downgrade():
    op.drop_table('users')
