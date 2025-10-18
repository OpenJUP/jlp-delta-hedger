from __future__ import annotations
import typing
from solders.pubkey import Pubkey
from solders.system_program import ID as SYS_PROGRAM_ID
from solders.sysvar import RENT, CLOCK
from spl.token.constants import TOKEN_PROGRAM_ID
from solders.instruction import Instruction, AccountMeta
import borsh_construct as borsh
from .. import types
from ..program_id import PROGRAM_ID


class CreateAndDelegateStakeAccountArgs(typing.TypedDict):
    params: (
        types.create_and_delegate_stake_account_params.CreateAndDelegateStakeAccountParams
    )


layout = borsh.CStruct(
    "params"
    / types.create_and_delegate_stake_account_params.CreateAndDelegateStakeAccountParams.layout
)


class CreateAndDelegateStakeAccountAccounts(typing.TypedDict):
    keeper: Pubkey
    perpetuals: Pubkey
    pool: Pubkey
    custody: Pubkey
    custody_token_account: Pubkey
    transfer_authority: Pubkey
    stake_account: Pubkey
    stake_info: Pubkey
    validator_vote_account: Pubkey
    stake_config: Pubkey
    wsol_mint: Pubkey
    temp_wsol_account: Pubkey
    stake_history: Pubkey
    stake_program: Pubkey


def create_and_delegate_stake_account(
    args: CreateAndDelegateStakeAccountArgs,
    accounts: CreateAndDelegateStakeAccountAccounts,
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
            pubkey=accounts["transfer_authority"], is_signer=False, is_writable=False
        ),
        AccountMeta(
            pubkey=accounts["stake_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=accounts["stake_info"], is_signer=False, is_writable=True),
        AccountMeta(
            pubkey=accounts["validator_vote_account"],
            is_signer=False,
            is_writable=False,
        ),
        AccountMeta(
            pubkey=accounts["stake_config"], is_signer=False, is_writable=False
        ),
        AccountMeta(pubkey=accounts["wsol_mint"], is_signer=False, is_writable=False),
        AccountMeta(
            pubkey=accounts["temp_wsol_account"], is_signer=False, is_writable=True
        ),
        AccountMeta(pubkey=RENT, is_signer=False, is_writable=False),
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
    identifier = b"b\xd1z\x1b\xde\x89^\x86"
    encoded_args = layout.build(
        {
            "params": args["params"].to_encodable(),
        }
    )
    data = identifier + encoded_args
    return Instruction(program_id, data, keys)
