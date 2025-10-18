from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.instruction import Instruction, AccountMeta
from ..program_id import PROGRAM_ID


class RedeemStakeAccounts(typing.TypedDict):
    keeper: Pubkey
    perpetuals: Pubkey
    pool: Pubkey
    custody: Pubkey
    stake_account: Pubkey
    stake_info: Pubkey


def redeem_stake(
    accounts: RedeemStakeAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["keeper"], is_signer=True, is_writable=False),
        AccountMeta(pubkey=accounts["perpetuals"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["pool"], is_signer=False, is_writable=True),
        AccountMeta(pubkey=accounts["custody"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["stake_account"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["stake_info"], is_signer=False, is_writable=True),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\xb2\xcb\xfai\x85v\xffE"
    encoded_args = b""
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
