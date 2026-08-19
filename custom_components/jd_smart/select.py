"""Select platform for JD Smart."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import JdSmartConfigEntry
from .entity import JdSmartEntity


@dataclass(frozen=True, kw_only=True)
class JdSmartSelectDescription(SelectEntityDescription):
    """JD Smart select description."""

    stream_id: str
    option_to_value: dict[str, str]


SELECTS: tuple[JdSmartSelectDescription, ...] = (
    JdSmartSelectDescription(
        key="hordir",
        stream_id="hordir",
        translation_key="horizontal_direction",
        options=["swing", "direct"],
        option_to_value={"swing": "0", "direct": "1"},
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: JdSmartConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up JD Smart selects."""
    async_add_entities(
        JdSmartSelect(coordinator, description)
        for coordinator in entry.runtime_data.coordinators.values()
        for description in SELECTS
    )


GREE_OPTION_TO_VALUE = {
    "direct": "0",
    "swing": "1",
    "left_20": "2",
    "left_10": "3",
    "mid": "4",
    "right_10": "5",
    "right_20": "6",
}
GREE_VALUE_TO_OPTION = {v: k for k, v in GREE_OPTION_TO_VALUE.items()}


class JdSmartSelect(JdSmartEntity, SelectEntity):
    """JD Smart stream select."""

    entity_description: JdSmartSelectDescription

    def __init__(
        self,
        coordinator,
        description: JdSmartSelectDescription,
    ) -> None:
        """Initialize select."""
        super().__init__(coordinator, description.key)
        self.entity_description = description
        self._attr_translation_key = description.translation_key
        self._value_to_option = {
            value: option for option, value in description.option_to_value.items()
        }

    @property
    def is_gree(self) -> bool:
        """Duck type to detect Gree protocol."""
        return "Mod" in self.streams

    @property
    def stream_id(self) -> str:
        if self.is_gree and self.entity_description.key == "hordir":
            return "SwingLfRig"
        return self.entity_description.stream_id

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return super().available and self.stream_id in self.streams

    @property
    def options(self) -> list[str]:
        """Return the list of available options."""
        if self.is_gree and self.entity_description.key == "hordir":
            return list(GREE_OPTION_TO_VALUE)
        return self.entity_description.options

    @property
    def current_option(self) -> str | None:
        """Return selected option."""
        value = self.streams.get(self.stream_id, "")
        if self.is_gree and self.entity_description.key == "hordir":
            return GREE_VALUE_TO_OPTION.get(value)
        return self._value_to_option.get(value)

    async def async_select_option(self, option: str) -> None:
        """Select option."""
        if self.is_gree and self.entity_description.key == "hordir":
            val = int(GREE_OPTION_TO_VALUE[option])
        else:
            val = int(self.entity_description.option_to_value[option])
            
        try:
            await self.coordinator.async_control_streams({self.stream_id: val})
        except Exception as err:
            raise HomeAssistantError("Unable to control JD Smart") from err
