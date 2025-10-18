from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import CLOCK
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class WithdrawStakeAccounts(typing.TypedDict):
    keeper: Pubkey
    perpetuals: Pubkey
    pool: Pubkey
    custody: Pubkey
    custody_token_account: Pubkey
    transfer_authority: Pubkey
    stake_account: Pubkey
    stake_info: Pubkey
    stake_history: Pubkey
    stake_program: Pubkey


def withdraw_stake(
    accounts: WithdrawStakeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["keeper"], is_signer=True, is_writable=True),
        AccountMeta(pubkey=accounts["perpetuals"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["pool"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["custody"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["custody_token_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["transfer_authority"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["stake_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["stake_info"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=CLOCK, is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["stake_history"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["stake_program"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=SYS_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x99\x08\x16\x8ai\xb0WB"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
