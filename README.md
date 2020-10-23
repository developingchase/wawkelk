# Wireless Analysis With Kismet and ELK
A project for analyzing Kismet data in the ELK stack. 

Presented at Bsides Boise 2020.

# Zero to Hero
1. Download the Bitnami VM (https://bitnami.com/stack/elk/virtual-machine)
2. Configure the network interface as appropriate, then start the Bitnami VM
3. Note the IP address and Kibana username and password
4. Log in and change the default Linux password (bitnami/bitnami)
5. (If you want to use SSH) Remove the SSH blocker: rm /etc/ssh/ssh_to_not_be_run
6. (If you want to use SSH) Start the SSH server: sudo systemctl enable ssh && systemctl start ssh 
7. Copy the two Logstash pipeline files into /opt/bitnami/logstash/pipeline/
8. Change the URL and username/passwords in each file to match your own settings
9. Launch Kibana in web browser
10. Navigate to Management > Dev Tools
11. Using the values in mappings.md, create the kismet_alerts and kismet_device_activity mappings
12. Restart Logstash ```sudo /opt/bitnami/ctlscript.sh restart logstash```
13. Navigate to Management > Stack Management > Index Patterns
14. Wait until data has been populated (based on the timers in the Logstash pipeline files)
15. Click Create Index Pattern
16. Create an index pattern for each index
17. Navigate to Discover, select an index pattern, and browse the data
18. Create visualizations for the data
19. Create dashboards of the visualizations
20. Use the kismetdevices_to_elk.py to push already collected kismetdb files to Elasticsearch

# Bitnami ELK Stack VM Notes
```/home/bitnami/bitnami_credentials``` < File containing the username/password for Kibana/ELK/etc 

```/opt/bitnami/logstash/pipeline/``` < Place pipeline conf files in here then restart Logstash

```sudo /opt/bitnami/ctlscript.sh status``` < Check status of services

```sudo /opt/bitnami/ctlscript.sh restart logstash``` < Restart logstash (or other services)

  
# Elasticsearch

There are two provided Elasticsearch Index/Mappings in mappings.md. Use the Dev Console in Kibana for passing commands to Elasticsearch.

- To delete an index with funky characters, you'll need to replace the special characters
  - % → %25
  - { → %7B
  - } → %7D

# Logstash
There are two provided Logstash pipeline files.
* kismet_alerts.conf - For pulling Kismet Alerts
* kismet_device_activity.conf - For pulling all Kismet devices observed in the last X minutes

## Logstash notes
- Test pipeline config changes via: 
```sudo /opt/bitnami/logstash/bin/logstash -f /opt/bitnami/logstash/pipeline --config.test_and_exit```
- If using the .ekjson end point, set ```codec => "json_lines"```
- If using the .json end point, set ```codec => "json"```
- Content type is important; some issue with Manticore defaulting to an encoded type which broke Kismet
-- ```headers => { "Accept" => "application/json" "Content-Type" => "application/x-www-form-urlencoded" }```
- Set the time to be an appropriate value (pulling too often results in more data captured than necessary)
- document_id is used by Elasticsearch to deconflict documents (Primary key of sorts); if you want to do temporal analysis, add a timestamp value to the document ID; if you want to only have one document per device, then use the base_key or MAC address as the document ID
- Add "```stdout { codec => rubydebug }```" in the output section when debugging
- Logstash combines all the pipeline files so if you use multiple pipeline conf files, ensure your filters sections are looking at the index first, otherwise they will attempt to apply to all pipelines
- Triple check syntax; look for missing "}" values
- Monitor the log file ```tail -f /opt/bitnami/logstash/log/logstash.log``` 

# Kibana

## Maps
* Great resource for WMS options: https://www.elastic.co/blog/custom-basemaps-for-region-and-coordinate-maps-in-kibana
* If you use Maptiler, here are the settings for the Kibana Coordinates Visualization:
  - Options > Base layer settings
    - Enable WMS map server
    - WMS url: https://api.maptiler.com/maps/streets/{z}/{x}/{y}.png?key=<your key>
    - WMS layers: 1
    - WMS version: 1.3.0
    - WMS format: image/jpg
    - WMS attribution: "&#xA9; [OpenMapTiles](http://www.openmaptiles.org/)|&#xA9; [OpenStreetMap contributors](http://www.openstreetmap.org/copyright)"
    - WMS styles: default


## Dev Tools Console Helpful Commands

### To delete an index
```
DELETE kismet_devices
```
### To Reindex...
Push the current documents to a temp index
```
PUT temp_new_mapping_index
{
  "settings": {
    "index.mapping.ignore_malformed": true 
  }
}
POST _reindex
{
  "source": {
    "index": "original_index"
  },
  "dest": {
    "index": "temp_new_mapping_index"
  }
}
```
Erase the original index
```
DELETE original_index
```
Recreate the original index with the intended mappings
```
PUT original_index
{
  "settings": {
    "index.mapping.ignore_malformed": true 
  }
}
```
Now reindex the original data into the newly creating index with updated mappings
```
POST _reindex
{
  "source": {
    "index": "temp_new_mapping_index"
  },
  "dest": {
    "index": "original_index"
  }
}
```
Delete the temp index
```
DELETE temp_new_mapping_index
```
