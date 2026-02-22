# EmmeTI Febos webapp integration for Home Assistant
Home Assistant custom component for EmmeTI Febos webapp.

**Summary**
- Provides a UI-based integration that connects to Febos using a username and password.
- Configuration is done via the Home Assistant Integrations UI (no YAML required).

**Features**
- Add your Febos account via the config flow (username + password)
- Creates entities and devices (managed by the integration)
- Supports multiple accounts in case you have many Febos Crono

**Requirements**
- Home Assistant 2025.12
- This is a custom component; all external Python package requirements are declared in `manifest.json`.

**Installation**
1. Copy the `febos` directory into your Home Assistant `custom_components` folder, i.e. `config/custom_components/febos/`.
2. Restart Home Assistant
3. Go to Settings → Devices & Services → Add integration → search for "EmmeTI Febos" and follow the prompts.

**Configuration (Config Flow)**
- The integration prompts for `username` and `password` through the UI.
- The config flow is implemented in `config_flow.py` and sets the config entry unique ID to the provided username.

**Troubleshooting**
- Enable debug logging for `custom_components.febos` to see detailed messages in the Home Assistant log.
- Ensure credentials are correct and that the Febos service is reachable from your Home Assistant host.

**Contributing**
- Pull requests and improvements are welcome — follow the repository's contribution guidelines.

**License**
- See the enclosing repository license for terms.
