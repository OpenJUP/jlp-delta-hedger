from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class SwapWithTokenLedgerArgs(typing.TypedDict):
    params: types.swap_with_token_ledger_params.SwapWithTokenLedgerParams


layout = borsh.CStruct(
    "params" / types.swap_with_token_ledger_params.SwapWithTokenLedgerParams.layout
)


class SwapWithTokenLedgerAccounts(typing.TypedDict):
    owner: Pubkey
    funding_account: Pubkey
    receiving_account: Pubkey
    transfer_authority: Pubkey
    perpetuals: Pubkey
    pool: Pubkey
    receiving_custody: Pubkey
    receiving_custody_doves_price_account: Pubkey
    receiving_custody_token_account: Pubkey
    dispensing_custody: Pubkey
    dispensing_custody_doves_price_account: Pubkey
    dispensing_custody_token_account: Pubkey
    token_ledger: Pubkey
    instruction: Pubkey
    event_authority: Pubkey
    program: Pubkey


def swap_with_token_ledger(
    args: SwapWithTokenLedgerArgs,
    accounts: SwapWithTokenLedgerAccounts,
    program_id: Pubkey = PROGRAM_ID,
    remaining_accounts: typing.Optional[typing.List[AccountMeta]] = None,
) -> Instruction:
    keys: list[AccountMeta] = [
        AccountMeta(pubkey=accounts["owner"], is_signer=True, is_writable=False),
        AccountMeta(
            pubkey=accounts["funding_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["receiving_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["transfer_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["perpetuals"], is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["pool"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["receiving_custody"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["receiving_custody_doves_price_account"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["receiving_custody_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["dispensing_custody"], is_signer=False, is_writable=True
        ),
        AccountMeta(
            pubkey=accounts["dispensing_custody_doves_price_account"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["dispensing_custody_token_account"],
            is_signer=False,
            is_writable=True,
        ),
        AccountMeta(
            pubkey=accounts["token_ledger"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=TOKEN_PROGRAM_ID, is_signer=False, is_writable=False),
        AccountMeta(pubkey=accounts["instruction"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["event_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["program"], is_signer=False, is_writable=False),
    ]
    if remaining_accounts is not None:
        keys += remaining_accounts
    identifier = b"\x8b\x8d\xee\xc5)\xd3\xac\x13"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
