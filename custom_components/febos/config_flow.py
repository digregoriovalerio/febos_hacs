"""Config flow for the EmmeTI Febos integration."""

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): TextSelector(
            TextSelectorConfig(type=TextSelectorType.TEXT, autocomplete="username")
        ),
        vol.Required(CONF_PASSWORD): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.PASSWORD, autocomplete="current-password"
            )
        ),
    }
)


class FebosConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for EmmeTI Febos integration.

    This flow manages user configuration and validation for connecting
    to the Febos smart home management system using username and password.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial user setup step.

        This step prompts the user for their Febos username and password,
        validates the credentials, and creates a config entry.

        Args:
            user_input: Dictionary containing username and password from the form.

        Returns:
            A config flow result with either the entry creation or the form.
        """
        LOGGER.debug("Step user started")
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_USERNAME])
            self._abort_if_unique_id_configured()
            result = self.async_create_entry(
                title=f"EmmeTI Febos - {user_input[CONF_USERNAME]}", data=user_input
            )
            LOGGER.debug(f"Step user for '{user_input[CONF_USERNAME]}' terminated")
            return result
        result = self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors={},
        )
        LOGGER.debug("Step user terminated with form")
        return result
