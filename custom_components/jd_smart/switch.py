"""Switch platform for JD Smart."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import JdSmartConfigEntry
from .entity import JdSmartEntity


@dataclass(frozen=True, kw_only=True)
class JdSmartSwitchDescription(SwitchEntityDescription):
    """JD Smart switch description."""

    stream_id: str


SWITCHES: tuple[JdSmartSwitchDescription, ...] = (
    JdSmartSwitchDescription(
        key="power", stream_id="power", translation_key="power"
    ),
    JdSmartSwitchDescription(
        key="bglight", stream_id="bglight", translation_key="backlight"
    ),
    JdSmartSwitchDescription(
        key="scrdispaly", stream_id="scrdispaly", translation_key="display"
    ),
    JdSmartSwitchDescription(
        key="ecomode", stream_id="ecomode", translation_key="powerful"
    ),
    JdSmartSwitchDescription(
        key="quiet", stream_id="Quiet", translation_key="quiet"
    ),
    JdSmartSwitchDescription(
        key="ptcheat", stream_id="ptcheat", translation_key="aux_heat"
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JdSmartConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up JD Smart switches."""
    async_add_entities(
        JdSmartSwitch(coordinator, description)
        for coordinator in entry.runtime_data.coordinators.values()
        for description in SWITCHES
    )


class JdSmartSwitch(JdSmartEntity, SwitchEntity):
    """JD Smart stream switch."""

    entity_description: JdSmartSwitchDescription

    def __init__(
        self,
        coordinator,
        description: JdSmartSwitchDescription,
    ) -> None:
        """Initialize switch."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_translation_key = description.translation_key

    @property
    def is_gree(self) -> bool:
        """Duck type to detect Gree protocol."""
        return "Mod" in self.streams

    @property
    def stream_id(self) -> str:
        """Return dynamic stream ID based on protocol."""
        key = self.entity_description.key
        if self.is_gree:
            if key == "ecomode":
                return "Tur"
            if key == "bglight":
                return "Blo"
            if key == "quiet":
                return "Quiet"
        return self.entity_description.stream_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.stream_id in self.streams

    @property
    def is_on(self) -> bool | None:
        """Return switch state."""
        value = self.streams.get(self.stream_id)
        if value in (None, ""):
            return None
        # For Gree Quiet mode, it uses "2" for on, "0" for off
        if self.is_gree and self.entity_description.key == "quiet":
            return value == "2"
        return value == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn switch on."""
        if self.is_gree and self.entity_description.key == "quiet":
            # Gree Quiet mode requires Tur=0
            await self._control_multiple({"Quiet": 2, "Tur": 0})
        else:
            await self._control(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn switch off."""
        if self.is_gree and self.entity_description.key == "quiet":
            await self._control(0)
        else:
            await self._control(0)

    async def _control(self, value: int) -> None:
        """Control helper."""
        await self._control_multiple({self.stream_id: value})

    async def _control_multiple(self, commands: dict[str, object]) -> None:
        """Control multiple streams."""
        try:
            await self.coordinator.async_control_streams(commands)
        except Exception as err:
            raise HomeAssistantError("Unable to control JD Smart") from err
