# TODO

APIsse:

- list_bin_sensors (params all)
- list_parameter_sensors -> name,val
- list_temp_sensors -> name,val
- get_notifications

HAsse:

- Binary sensors separately
- Every zone -> Climate
- Relays -> Switches
- Notifications ->?

### Installation

Copy this folder to `<config_dir>/custom_components/airpatrol/`.

Add the following entry in your `configuration.yaml`:

```yaml
airpatrol:
  username: your-username (email) in airpatrol
  password: your-password
```
