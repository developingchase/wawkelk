 # Wireless Analysis With Kismet and ELK
A project for analyzing Kismet data in the ELK stack. 

Presented at Bsides Idaho 2020 (https://www.youtube.com/watch?v=MU3hu3WuRA0). Slides in repo (Wireless Analysis with Kismet and ELK (WAWKELK).pdf).

NEW - Updated in 2023 for the new version of ELK that had some breaking changes. I've updated the readme and the Python script for uploading an captured Kismet file to ES. However, I haven't tested this exhaustively so you may find issues. Feel free to open issues and I'll get to them as I can.

# Zero to Hero
1. Download the Bitnami VM (https://bitnami.com/stack/elk/virtual-machine)
2. Configure the network interface as appropriate, then start the Bitnami VM
3. Note the IP address and Kibana username and password
4. Log in and change the default Linux password (bitnami/bitnami)
5. (If you want to use SSH) Remove the SSH blocker: sudo rm -f /etc/ssh/sshd_to_not_be_run
6. (If you want to use SSH) Start the SSH server: sudo systemctl enable ssh && systemctl start ssh
7. There are two options - key-based or password based auth - read here for more details - https://docs.bitnami.com/virtual-machine/faq/get-started/enable-ssh-keys/ & https://docs.bitnami.com/virtual-machine/faq/get-started/enable-ssh-password/ 
8. Copy the two Logstash pipeline files into /opt/bitnami/logstash/pipeline/
9. Change the URL and username/passwords in each file to match your own settings
10. Launch Kibana in web browser (Click "Explore on my own")
11. Navigate the menu to Management > Dev Tools
12. Using the values in mappings.md, create the kismet_alerts and kismet_device_activity mappings
13. Restart Logstash ```sudo /opt/bitnami/ctlscript.sh restart logstash```; wait for ~2-3 minutes for data to reach Elasticsearch
14. In Kibana 8.x or greater, create data viewsCreate data view
15. Provide a Name, then enter the "kismet_alerts" index
16. Select @timestamp for the Timestamp field
17. Save data view to Kibana
18. Repeat for the "kismet_device_activity" index
19. Navigate to Discover, select a data view pattern, and browse the data
20. Create visualizations for the data
21. Create dashboards of the visualizations
22. Use the kismetdevices_to_elk.py to push already collected kismetdb files to Elasticsearch
23. You'll need to change network settings for ES to enable direct connection to port 9200. 
24. Edit /opt/bitnami/elasticsearch/config/elasticsearch.yml and change the addresses in network to 0.0.0.0. (https://docs.bitnami.com/virtual-machine/apps/elasticsearch/administration/connect-remotely/)
25. I also had to open port 9200 on my firewall (https://docs.bitnami.com/virtual-machine/faq/administration/use-firewall/)
26. Warning - this opens up your ELK stack to potential network abuse, so be careful when/where you do this. ES has added a lot of new security features I haven't tested yet. I test this on a local protected network. Please follow ES's guidance for properly securing your stack if using this anywhere other than a local test environment. 
27.  python3 kismetdevices_to_elk.py -i Kismet-file.kismet -e http://<ELKIP>:9200 -u user -p <password>
28. This will put the historic devices into a "kismet_devices" index. You'll need to follow the steps in 13-18 to add a new data view for this index. Pro tip - adding a data view for "kismet_device*" will allow you to see data from both live and historic Kismet data sources. :) 

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
- Monitor the log file ```tail -f /opt/bitnami/logstash/logs/logstash-plain.log``` 

# Kibana

## Maps (Update! Kibana 8.x has better builtin support for maps, with improved zoom layers and a default street map, so unless you want to mess around with imagery, you don't need to do this. I'll leave it here for those that may still need it.)
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
