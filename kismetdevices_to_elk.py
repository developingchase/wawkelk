# python file to take as input a kismetdb file, dump devices, then
# process the devices and extract certain fields
# finally shove the devices into elasticsearch

version = "1.0"
print("""
 __    __   ____  __    __  __  _    ___  _      __  _ 
|  |__|  | /    ||  |__|  ||  |/ ]  /  _]| |    |  |/ ]
|  |  |  ||  o  ||  |  |  ||  ' /  /  [_ | |    |  ' / 
|  |  |  ||     ||  |  |  ||    \ |    _]| |___ |    \ 
|  `  '  ||  _  ||  `  '  ||     ||   [_ |     ||     |
 \      / |  |  | \      / |  .  ||     ||     ||  .  |
  \_/\_/  |__|__|  \_/\_/  |__|\_||_____||_____||__|\_|
                                                       
""")
print("Version " + str(version))

try:
    print("[+] Loading libraries")
    from elasticsearch import Elasticsearch
    from elasticsearch.helpers import bulk
    import json
    import argparse
    import subprocess
    import csv
    import datetime
except:
  print("Imports failed. You probably need:")
  print("python3 -m pip install elasticsearch")
  exit(0)

device_arr = {}

# given file input from command line
parser = argparse.ArgumentParser(description='Parse kismetdb files to ELK')
parser.add_argument('-i',dest='input', action='store',help='Name of input *.kismet file(s)\n', required=True)
parser.add_argument('-e',dest='es', action='store',help='Elasticsearch IP address; default is localhost\n', required=False,default='localhost')
parser.add_argument('-u',dest='username', action='store',help='Elasticsearch username; default is user\n', required=False,default='user')
parser.add_argument('-p',dest='password', action='store',help='Elasticsearch password\n', required=True)
args = parser.parse_args()


def es_connect():
    host = str(args.es)
    port = 9200
    es_username = str(args.username)
    es_password = str(args.password)
    es = Elasticsearch([host],http_auth=(es_username,es_password))
    if es.ping():
        print("[+] Connection established to Elasticsearch")
    else:
        print("[!] Connect to Elasticsearch failed")
        print("Host: " + str(host) + ", Port: " + str(port) + ", Username: " + es_username + ", Password: " + es_password)
        exit(0)
    return es

def es_create_index(es,es_index_name='test_index'):
    created = False
    # index settings
    settings = {
        "settings": {
            "index.mapping.depth.limit": 20
        },
        "mappings": {
            "dynamic": "true",
            "numeric_detection": False,
            "properties": {
                "@timestamp": {
                    "type": "date",
                    "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
                },
                "kismet_device_base_location_avg_geopoint": {
                    "type":"geo_point"
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
                        },
                        "kismet_common_location_last": {
                            "type": "nested",
                            "properties": {
                                "kismet_common_location_geopoint": {
                                    "type": "geo_point"
                                }
                            }
                        },
                        "kismet_common_location_max_loc": {
                            "type": "nested",
                            "properties": {
                                "kismet_common_location_geopoint": {
                                    "type": "geo_point"
                                }
                            }
                        },
                        "kismet_common_location_min_loc": {
                            "type": "nested",
                            "properties": {
                                "kismet_common_location_geopoint": {
                                    "type": "geo_point"
                                }
                            }
                        }
                    }
                },
                "kismet_device_base_signal": {
                    "type": "nested",
                    "properties": {
                        "kismet_common_signal_peak_loc": {
                            "type": "nested",
                            "properties": {
                                "kismet_common_location_geopoint": {
                                    "type": "geo_point"
                                }
                            }
                        }
                    }
                },
                "dot11_device": {
                    "type": "nested",
                    "properties": {
                        "dot11_device_advertised_ssid_map": {
                            "type": "nested",
                            "properties": {
                                "advertisedssid" : {
                                    "type": "nested",
                                    "properties": {
                                        "wps_model_number": {
                                            "type": "text"
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    try:
        if not es.indices.exists(es_index_name):
            es.indices.create(index=es_index_name, body=settings)
            print('[+] Created ES index named ' + str(es_index_name))
        created = True
    except Exception as ex:
        print(str(ex))
    finally:
        return created

def convert_kismetdbtojson(dbfile):
    try:
        process = subprocess.Popen(['kismetdb_dump_devices','--in',dbfile,'--out','-','-s','-j' ],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
    except:
        print("Problem with running kismetdb_dump_devices - do you have this installed?")
        exit(0)

    stdout, stderr = process.communicate()
    #print(stdout)
    if stderr:
        print("[!] Error with parsing " + str(dbfile) + " -- " + str(stderr))
        return False
    else:
        jsonoutput = json.loads(stdout)
        #for x in jsontest:
        #    print(x['kismet_device_base_type'])
        return jsonoutput

def process_json(records,filename):
    # two options - take everything minus some fields, or only take certain fields
    # currently doing everything minus
    # remember the transition from "." to "_" field notation!
    #fields_we_want = ["kismet.device.base.type","kismet.device.base.location","kismet.device.base.tags","kismet.device.base.manuf","kismet.device.base.num_alerts","kismet.device.base.server_uuid","kismet.device.base.last_time","kismet.device.base.frequency","kismet.device.base.channel","kismet.device.base.crypt","kismet.device.base.commonname","kismet.device.base.name","kismet.device.base.phyname","kismet.device.base.macaddr","kismet.device.base.key","kismet.device.base.key","kismet.device.base.packets.rx","kismet.device.base.packets.tx"]
    #fields_we_want = ["kismet.device.base.type"]
    fields_we_dont_want = ['kismet_device_base_freq_khz_map','kismet_device_base_datasize_rrd','kismet_device_base_location_cloud','kismet_device_base_packet_bin_250']
    new_devices = []
    for x in records:
        #print(x.keys())
        for y in list(x.keys()): #cast to list to get around iterator
            new_row = x
            if y in fields_we_dont_want:
                del new_row[y]
        if 'kismet_device_base_location' in list(x.keys()):
            if 'kismet_common_location_avg_loc' in list(x['kismet_device_base_location'].keys()):
                new_row["kismet_device_base_location_avg_geopoint"] = x['kismet_device_base_location']['kismet_common_location_avg_loc']['kismet_common_location_geopoint']
        new_devices.append(new_row)
    return new_devices

records_count = 0
def es_set_data(records,es_index_name):
    global records_count
    for record in records:
        # get timestamp value
        timestamp = datetime.datetime.fromtimestamp(record['kismet_device_base_last_time']).strftime('%Y-%m-%d %H:%M:%S')

        doc_id = record['kismet_device_base_key']
        record['@timestamp'] = timestamp
        yield {
            "_index": es_index_name,
            "_id": doc_id,
            "_source": record
        }
        records_count+=1

def es_load(es,records,es_index_name,**kwargs):
    success, _ = bulk(es,es_set_data(records,es_index_name,**kwargs))
    # stats_only=True is an option here
    return success

if __name__ == ("__main__"):
    print("[+] Attempting to load the provided file " + str(args.input))
    records = convert_kismetdbtojson(args.input)
    if records == False:
        print("[!] Skipping " + str(args.input))
    else:
        print("[+] Parsing " + str(args.input) + ".")
        new_records = process_json(records,args.input)
    if len(new_records) > 0:
        es = es_connect()
        if es_create_index(es,'kismet_devices'):
            print("[+] Let's put some data in our index...")
            try:
                es_load_results = es_load(es,new_records,'kismet_devices')
            except Exception as ex:
                print(ex)
            #TODO Determine better method for validating documents loaded and presenting any errors
            print("[+] Allegedly loaded " + str(records_count) + " entries.")
