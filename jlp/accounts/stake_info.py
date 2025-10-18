import typing
from dataclasses import dataclass
from solders.pubkey import Pubkey
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
import borsh_construct as borsh
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.error import AccountInvalidDiscriminator
from anchorpy.utils.rpc import get_multiple_accounts
from anchorpy.borsh_extension import BorshPubkey
from ..program_id import PROGRAM_ID


class StakeInfoJSON(typing.TypedDict):
    pool: str
    stake_account: str
    current_staked_amount_lamports: int
    total_staking_rewards_lamports: int
    last_updated_at: int
    deactivating: bool
    stake_account_index: int
    bump: int


@dataclass
class StakeInfo:
    discriminator: typing.ClassVar = b"B>DFl\xb3\xb7\xeb"
    layout: typing.ClassVar = borsh.CStruct(
        "pool" / BorshPubkey,
        "stake_account" / BorshPubkey,
        "current_staked_amount_lamports" / borsh.U64,
        "total_staking_rewards_lamports" / borsh.U64,
        "last_updated_at" / borsh.I64,
        "deactivating" / borsh.Bool,
        "stake_account_index" / borsh.U64,
        "bump" / borsh.U8,
    )
    pool: Pubkey
    stake_account: Pubkey
    current_staked_amount_lamports: int
    total_staking_rewards_lamports: int
    last_updated_at: int
    deactivating: bool
    stake_account_index: int
    bump: int

    @classmethod
    async def fetch(
        cls,
        conn: AsyncClient,
        address: Pubkey,
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.Optional["StakeInfo"]:
        resp = await conn.get_account_info(address, commitment=commitment)
        info = resp.value
        if info is None:
            return None
        if info.owner != program_id:
            raise ValueError("Account does not belong to this program")
        bytes_data = info.data
        return cls.decode(bytes_data)

    @classmethod
    async def fetch_multiple(
        cls,
        conn: AsyncClient,
        addresses: list[Pubkey],
        commitment: typing.Optional[Commitment] = None,
        program_id: Pubkey = PROGRAM_ID,
    ) -> typing.List[typing.Optional["StakeInfo"]]:
        infos = await get_multiple_accounts(conn, addresses, commitment=commitment)
        res: typing.List[typing.Optional["StakeInfo"]] = []
        for info in infos:
            if info is None:
                res.append(None)
                continue
            if info.account.owner != program_id:
                raise ValueError("Account does not belong to this program")
            res.append(cls.decode(info.account.data))
        return res

    @classmethod
    def decode(cls, data: bytes) -> "StakeInfo":
        if data[:ACCOUNT_DISCRIMINATOR_SIZE] != cls.discriminator:
            raise AccountInvalidDiscriminator(
                "The discriminator for this account is invalid"
            )
        dec = StakeInfo.layout.parse(data[ACCOUNT_DISCRIMINATOR_SIZE:])
        return cls(
            pool=dec.pool,
            stake_account=dec.stake_account,
            current_staked_amount_lamports=dec.current_staked_amount_lamports,
            total_staking_rewards_lamports=dec.total_staking_rewards_lamports,
            last_updated_at=dec.last_updated_at,
            deactivating=dec.deactivating,
            stake_account_index=dec.stake_account_index,
            bump=dec.bump,
        )

    def to_json(self) -> StakeInfoJSON:
        return {
            "pool": str(self.pool),
            "stake_account": str(self.stake_account),
            "current_staked_amount_lamports": self.current_staked_amount_lamports,
            "total_staking_rewards_lamports": self.total_staking_rewards_lamports,
            "last_updated_at": self.last_updated_at,
            "deactivating": self.deactivating,
            "stake_account_index": self.stake_account_index,
            "bump": self.bump,
        }

    @classmethod
    def from_json(cls, obj: StakeInfoJSON) -> "StakeInfo":
        return cls(
            pool=Pubkey.from_string(obj["pool"]),
            stake_account=Pubkey.from_string(obj["stake_account"]),
            current_staked_amount_lamports=obj["current_staked_amount_lamports"],
            total_staking_rewards_lamports=obj["total_staking_rewards_lamports"],
            last_updated_at=obj["last_updated_at"],
            deactivating=obj["deactivating"],
            stake_account_index=obj["stake_account_index"],
            bump=obj["bump"],
        )
