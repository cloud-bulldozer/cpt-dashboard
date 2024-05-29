from fastapi import APIRouter
import app.api.v1.commons.hasher as hasher

router = APIRouter()

@router.get("/api/v1/telco/graph/{uuid}/{encryptedData}")
async def graph(uuid: str, encryptedData: str):
   bytesData = encryptedData.encode("utf-8")
   decrypted_data = hasher.decrypt_unhash_json(uuid, bytesData)
   json_data = decrypted_data["data"]
   return await process_json(json_data)

async def process_json(json_data: dict):
   function_mapper = {
      "ptp": process_ptp,
      "oslat": process_oslat,
      "reboot": process_reboot,
      "cpu_util": process_cpu_util,
      "rfc-2544": process_rfc_2544,
      "cyclictest": process_cyclictest,
      "deployment": process_deployment,
   }
   mapped_function = function_mapper.get(json_data["test_type"])
   return mapped_function(json_data)

def process_ptp(json_data: str):
   nic = json_data["nic"]
   ptp4l_max_offset = json_data["ptp4l_max_offset"]
   if "mellanox" in nic.lower():
      defined_offset_threshold = 200
   else:
      defined_offset_threshold = 100
   minus_offset = 0
   if ptp4l_max_offset > defined_offset_threshold:
      minus_offset = ptp4l_max_offset - defined_offset_threshold
   
   return {
      "ptp": [
         {
            "name": "Data Points",
            "x": ["ptp4l_max_offset"],
            "y": [ptp4l_max_offset],
            "mode": "markers",
            "marker": {
               "size": 10,
            },
            "error_y": {
               "type": "data",
               "symmetric": "false",
               "array": [0],
               "arrayminus": [minus_offset]
            },
            
         },
         {
            "name": "Threshold",
            "x": ["ptp4l_max_offset"],
            "y": [defined_offset_threshold],
            "mode": "lines+markers",
            "line": {
               "dash": 'dot',
               "width": 3,
            },
            "marker": {
               "size": 15,
            },
            "type": "scatter",
         }
      ]
   }
   

def process_reboot(json_data: str):
   max_minutes = 0.0
   avg_minutes = 0.0
   minus_max_minutes = 0.0
   minus_avg_minutes = 0.0
   defined_threshold = 20
   reboot_type = json_data["reboot_type"]
   for each_iteration in json_data["Iterations"]:
      max_minutes = max(max_minutes, each_iteration["total_minutes"])
      avg_minutes += each_iteration["total_minutes"]
   avg_minutes /= len(json_data["Iterations"])
   if max_minutes > defined_threshold:
      minus_max_minutes = max_minutes - defined_threshold
   if avg_minutes > defined_threshold:
      minus_avg_minutes = avg_minutes - defined_threshold

   return {
      "reboot": [
         {
            "name": "Data Points",
            "x": [reboot_type + "_" + "max_minutes", reboot_type + "_" + "avg_minutes"],
            "y": [max_minutes, avg_minutes],
            "mode": "markers",
            "marker": {
               "size": 10,
            },
            "error_y": {
               "type": "data",
               "symmetric": "false",
               "array": [0, 0],
               "arrayminus": [minus_max_minutes, minus_avg_minutes]
            },
            "type": "scatter",
         },
         {
            "name": "Threshold",
            "x": [reboot_type + "_" + "max_minutes", reboot_type + "_" + "avg_minutes"],
            "y": [defined_threshold, defined_threshold],
            "mode": "lines+markers",
            "marker": {
               "size": 15,
            },
            "line": {
               "dash": "dot",
               "width": 3,
            },
            "type": "scatter",
         }
      ]
   }

def process_cpu_util(json_data: str):
   total_max_cpu = 0.0
   total_avg_cpu = 0.0
   minus_max_cpu = 0.0
   minus_avg_cpu = 0.0
   defined_threshold = 3.0
   for each_scenario in json_data["scenarios"]:
      if each_scenario["scenario_name"] == "steadyworkload":
         for each_type in each_scenario["types"]:
            if each_type["type_name"] == "total":
               total_max_cpu = each_type["max_cpu"]
               break
         total_avg_cpu = each_scenario["avg_cpu_total"]
         break
   if total_max_cpu > defined_threshold:
      minus_max_cpu = total_max_cpu - defined_threshold
   if total_avg_cpu > defined_threshold:
      minus_avg_cpu = total_avg_cpu - defined_threshold

   return {
      "cpu_util": [
         {
            "name": "Data Points",
            "x": ["total_max_cpu", "total_avg_cpu"],
            "y": [total_max_cpu, total_avg_cpu],
            "mode": "markers",
            "marker": {
               "size": 10,
            },
            "error_y": {
               "type": "data",
               "symmetric": "false",
               "array": [0, 0],
               "arrayminus": [minus_max_cpu, minus_avg_cpu]
            },
            "type": "scatter",
         },
         {
            "name": "Threshold",
            "x": ["total_max_cpu", "total_avg_cpu"],
            "y": [defined_threshold, defined_threshold],
            "mode": "lines+markers",
            "marker": {
               "size": 15,
            },
            "line": {
               "dash": "dot",
               "width": 3,
            },
            "type": "scatter",
         }
      ]
   }

def process_rfc_2544(json_data: str):
   max_delay = json_data["max_delay"]
   defined_delay_threshold = 30.0
   minus_max_delay = 0.0
   if max_delay > defined_delay_threshold:
      minus_max_delay = max_delay - defined_delay_threshold
   
   return {
      "rfc-2544": [
         {
            "x": ["max_delay"],
            "y": [max_delay],
            "mode": "markers",
            "marker": {
               "size": 10,
            },
            "name": "Data Points",
            "error_y": {
               "type": "data",
               "symmetric": "false",
               "array": [0],
               "arrayminus": [minus_max_delay]
            },
            "type": "scatter",
         },
         {
            "x": ["max_delay"],
            "y": [defined_delay_threshold],
            "name": "Threshold",
            "mode": "lines+markers",
            "marker": {
               "size": 15,
            },
            "line": {
               "dash": "dot",
               "width": 3,
            },
            "type": "scatter"
         }
      ]
   }
   
def process_oslat(json_data: str):
   return {
      "oslat": get_oslat_or_cyclictest(json_data)
   }

def process_cyclictest(json_data: str):
   return {
      "cyclictest": get_oslat_or_cyclictest(json_data)
   }

def process_deployment(json_data: str):
   total_minutes = json_data["total_minutes"]
   reboot_count = json_data["reboot_count"]
   defined_total_minutes_threshold = 180
   defined_total_reboot_count = 3
   minus_total_minutes = 0.0
   minus_total_reboot_count = 0.0
   if total_minutes > defined_total_minutes_threshold:
      minus_total_minutes = total_minutes - defined_total_minutes_threshold
   if reboot_count > defined_total_reboot_count:
      minus_total_reboot_count = reboot_count - defined_total_reboot_count
   
   return {
      "deployment": {
         "total_minutes": [
            {
               "name": "Data Points",
               "x": ["total_minutes"],
               "y": [total_minutes],
               "mode": "markers",
               "marker": {
                  "size": 10,
               },
               "error_y": {
                  "type": "data",
                  "symmetric": "false",
                  "array": [0],
                  "arrayminus": [minus_total_minutes]
               },
               "type": "scatter",
            },
            {
               "name": "Threshold",
               "x": ["total_minutes"],
               "y": [defined_total_minutes_threshold],
               "mode": "lines+markers",
               "marker": {
                  "size": 15,
               },
               "line": {
                  "dash": "dot",
                  "width": 3,
               },
               "type": "scatter",
            }
         ],
         "total_reboot_count": [
            {
               "name": "Data Points",
               "x": ["reboot_count"],
               "y": [reboot_count],
               "mode": "markers",
               "marker": {
                  "size": 10,
               },
               "error_y": {
                  "type": "data",
                  "symmetric": "false",
                  "array": [0],
                  "arrayminus": [minus_total_reboot_count]
               },
               "type": "scatter",
            },
            {
               "name": "Threshold",
               "x": ["reboot_count"],
               "y": [defined_total_reboot_count],
               "mode": "lines+markers",
               "marker": {
                  "size": 15,
               },
               "line": {
                  "dash": "dot",
                  "width": 3,
               },
               "type": "scatter",
            }
         ]
      }
   }

def get_oslat_or_cyclictest(json_data: str):
   min_number_of_nines = 10000
   max_latency = 0
   minus_max_latency = 0
   defined_latency_threshold = 20
   defined_number_of_nines_threshold = 100
   for each_test_unit in json_data["test_units"]:
      max_latency = max(max_latency, each_test_unit["max_latency"])
      min_number_of_nines = min(min_number_of_nines, each_test_unit["number_of_nines"])
   if max_latency > defined_latency_threshold:
      minus_max_latency = max_latency - defined_latency_threshold

   return {
         "number_of_nines": [
            {
               "name": "Data Points",
               "x": ["min_number_of_nines"],
               "y": [min_number_of_nines],
               "mode": "markers",
               "marker": {
                  "size": 10,
               },
               "error_y": {
                  "type": "data",
                  "symmetric": "false",
                  "array": [0],
                  "arrayminus": [min_number_of_nines - defined_number_of_nines_threshold]
               },
               "type": "scatter",
            },
            {
               "name": "Threshold",
               "x": ["min_number_of_nines"],
               "y": [defined_number_of_nines_threshold],
               "mode": "lines+markers",
               "marker": {
                  "size": 15,
               },
               "line": {
                  "dash": "dot",
                  "width": 3,
               },
               "type": "scatter",
            }
         ],
         "max_latency": [
            {
               "name": "Data Points",
               "x": ["max_latency"],
               "y": [max_latency],
               "mode": "markers",
               "marker": {
                  "size": 10,
               },
               "error_y": {
                  "type": "data",
                  "symmetric": "false",
                  "array": [0],
                  "arrayminus": [minus_max_latency]
               },
               "type": "scatter",
            },
            {
               "name": "Threshold",
               "x": ["max_latency"],
               "y": [defined_latency_threshold],
               "mode": "lines+markers",
               "marker": {
                  "size": 15,
               },
               "line": {
                  "dash": "dot",
                  "width": 3,
               },
               "type": "scatter",
            }
         ]
      }
