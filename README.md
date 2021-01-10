[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)

# Home Assistant Zoneminder Events

Adds Zoneminder alarm service to Home Assistant

## Installation: Manual

1. Copy the `zoneminder_events` folder to the `custom_components` folder in your Home Assistant configuration directory.
2. Restart Home Assistant to allow the required packages to be installed.
3. Add the following minimum code in your `configuration.yaml` file. See Configuration for more advanced options:
```
zoneminder_events:
 - name: default
   host: "localhost:8223"
```
4. Restart Home Assistant one final time.


## Installation: HACS

This method assumes you have HACS already installed.
1. In the HACS Store, search for `Zoneminder Events` integration and install it.
2. Restart Home Assistant to allow the required packages to be installed.
3. Add the following code in your `configuration.yaml` file. See Configuration for more advanced options:
```
zoneminder_events:
 - name: default
   host: "localhost:8223"
```
4. Restart Home Assistant one final time.


## Configuration


Similar config options as [Zoneminder integration](https://www.home-assistant.io/integrations/zoneminder/)

```
zoneminder_events:
 - name: default
   host: "localhost:8223"
   ssl: false
   username: some_user
   password: some_password

```
