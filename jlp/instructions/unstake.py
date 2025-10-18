from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.sysvar import CLOCK
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class UnstakeAccounts(typing.TypedDict):
    operator: Pubkey
    perpetuals: Pubkey
    pool: Pubkey
    custody: Pubkey
    transfer_authority: Pubkey
    stake_account: Pubkey
    stake_info: Pubkey
    stake_program: Pubkey


def unstake(
    accounts: UnstakeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["operator"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["perpetuals"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["pool"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["custody"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["transfer_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["stake_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["stake_info"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["stake_program"], is_signer=False, is_writable=False
        ),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"Z_k*\xcd|2\xe1"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
