# Kismet Alerts
```
PUT kismet_alerts
{
  "mappings": {
    "dynamic": true,
    "numeric_detection": true,
    "properties": {
      "kismet_alert_channel": {
        "type":   "integer"
      },
      "kismet_alert_frequency": {
        "type":   "double"
      },
      "kismet_alert_location": {
        "type":"nested",
        "properties": {
          "kismet_common_location_geopoint": {
          "type":   "geo_point"
          }
        }
      }
    }
  }
}
```

# Kismet Device Activity
```
PUT kismet_device_activity
{
  "settings": {
    "index.mapping.ignore_malformed": true 
  },
  "mappings": {
    "dynamic": true,
    "numeric_detection": true,
    "properties": {
      "kismet_device_base_location_avg_geopoint": {
        "type": "geo_point"
      },
      "kismet_device_base_location": {
        "type": "nested",
        "properties": {
          "kismet_common_location_avg_loc": {
            "type": "nested",
            "properties": {
              "kismet_common_location_geopoint": {
                "type": "geo_point"
              }
            }
          }
        }
      },
      "kismet_device_base_tags": {
        "type": "nested",
        "properties": {
          "notes": {
            "type":"text"
          }
        }
      }
    }
  }
}
```
