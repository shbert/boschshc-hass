"""Platform for cover integration."""
from boschshcpy import (
    SHCSession,
    SHCShutterControl,
    SHCMicromoduleShutterControl,
    SHCMicromoduleBlinds,
)
from boschshcpy.device import SHCDevice

from homeassistant.components.cover import (
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    SUPPORT_CLOSE,
    SUPPORT_CLOSE_TILT,
    SUPPORT_OPEN,
    SUPPORT_OPEN_TILT,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
    SUPPORT_STOP_TILT,
    CoverDeviceClass,
    CoverEntity,
)
from homeassistant.const import Platform
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_SESSION, DOMAIN
from .entity import SHCEntity, async_migrate_to_new_unique_id


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the SHC cover platform."""
    entities = []
    session: SHCSession = hass.data[DOMAIN][config_entry.entry_id][DATA_SESSION]

    for cover in (
        session.device_helper.shutter_controls
        + session.device_helper.micromodule_shutter_controls
    ):
        await async_migrate_to_new_unique_id(hass, Platform.COVER, device=cover)
        entities.append(
            ShutterControlCover(
                device=cover,
                parent_id=session.information.unique_id,
                entry_id=config_entry.entry_id,
            )
        )

    for blind in session.device_helper.micromodule_blinds:
        await async_migrate_to_new_unique_id(hass, Platform.COVER, device=blind)
        entities.append(
            BlindsControlCover(
                device=blind,
                parent_id=session.information.unique_id,
                entry_id=config_entry.entry_id,
            )
        )

    if entities:
        async_add_entities(entities)


class ShutterControlCover(SHCEntity, CoverEntity):
    """Representation of a SHC shutter control device."""

    def __init__(
        self,
        device: SHCShutterControl | SHCMicromoduleShutterControl,
        parent_id: str,
        entry_id: str,
    ) -> None:
        """Initialize a SHC blinds cover."""
        super().__init__(device, parent_id, entry_id)
        self._attr_device_class = CoverDeviceClass.SHUTTER
        self._attr_supported_features = (
            SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION
        )

    @property
    def current_cover_position(self):
        """Return the current cover position."""
        return round(self._device.level * 100.0)

    def stop_cover(self, **kwargs):
        """Stop the cover."""
        self._device.stop()

    @property
    def is_closed(self):
        """Return if the cover is closed or not."""
        return self.current_cover_position == 0

    @property
    def is_opening(self):
        """Return if the cover is opening or not."""
        return (
            self._device.operation_state
            == SHCShutterControl.ShutterControlService.State.OPENING
        )

    @property
    def is_closing(self):
        """Return if the cover is closing or not."""
        return (
            self._device.operation_state
            == SHCShutterControl.ShutterControlService.State.CLOSING
        )

    def open_cover(self, **kwargs):
        """Open the cover."""
        self._device.level = 1.0

    def close_cover(self, **kwargs):
        """Close cover."""
        self._device.level = 0.0

    def set_cover_position(self, **kwargs):
        """Move the cover to a specific position."""
        position = kwargs[ATTR_POSITION]
        self._device.level = position / 100.0


class BlindsControlCover(ShutterControlCover, CoverEntity):
    """Representation of a SHC blinds cover device."""

    def __init__(
        self,
        device: SHCMicromoduleBlinds,
        parent_id: str,
        entry_id: str,
    ) -> None:
        """Initialize a SHC blinds cover."""
        super().__init__(device, parent_id, entry_id)
        self._attr_device_class = CoverDeviceClass.BLIND
        self._attr_supported_features = (
            SUPPORT_OPEN
            | SUPPORT_CLOSE
            | SUPPORT_STOP
            | SUPPORT_SET_POSITION
            | SUPPORT_OPEN_TILT
            | SUPPORT_CLOSE_TILT
            | SUPPORT_SET_TILT_POSITION
        )

    @property
    def current_cover_tilt_position(self):
        """Return the current cover tilt position."""
        return round(self._device.current_angle * 100.0)

    def open_cover_tilt(self, **kwargs):
        """Open the cover tilt."""
        self._device.target_angle = 1.0

    def close_cover_tilt(self, **kwargs):
        """Close cover tilt."""
        self._device.target_angle = 0.0

    def set_cover_tilt_position(self, **kwargs):
        """Move the cover tilt to a specific position."""
        tilt_position = kwargs[ATTR_TILT_POSITION]
        self._device.target_angle = tilt_position / 100.0
