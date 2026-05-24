from .base import SuiService, GroupInfo, ProfileInfo, AddressInfo, ActiveState


class RealSuiService(SuiService):
    """Real pysui service implementation -- arrives in Sprint 3."""

    async def active_state(self) -> ActiveState:
        raise NotImplementedError("RealSuiService ships in Sprint 3")

    async def list_groups(self) -> list[GroupInfo]:
        raise NotImplementedError("RealSuiService ships in Sprint 3")

    async def list_profiles(self, group_name: str) -> list[ProfileInfo]:
        raise NotImplementedError("RealSuiService ships in Sprint 3")

    async def list_addresses(self, group_name: str) -> list[AddressInfo]:
        raise NotImplementedError("RealSuiService ships in Sprint 3")
