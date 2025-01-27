from fastapi import APIRouter
import app.api.v1.commons.hasher as hasher

router = APIRouter()


@router.get("/api/v1/telco/graph/{uuid}/{encryptedData}")
async def graph(uuid: str, encryptedData: str):
    bytesData = encryptedData.encode("utf-8")
    decrypted_data = hasher.decrypt_unhash_json(uuid, bytesData)
    json_data = decrypted_data["data"]
    return await process_json(json_data, False)


async def process_json(json_data: dict, is_row: bool):
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
    return mapped_function(json_data, is_row)


def process_ptp(json_data: str, is_row: bool):
    nic = json_data["nic"]
    ptp4l_max_offset = json_data.get("ptp4l_max_offset") or 0
    if "mellanox" in nic.lower():
        defined_offset_threshold = 200
    else:
        defined_offset_threshold = 100
    minus_offset = 0
    if ptp4l_max_offset > defined_offset_threshold:
        minus_offset = ptp4l_max_offset - defined_offset_threshold

    if is_row:
        return minus_offset
    else:
        return {
            "ptp": [
                {
                    "name": "Data Points",
                    "x": ["-inf", "ptp4l_max_offset", "inf"],
                    "y": [0, ptp4l_max_offset, 0],
                    "mode": "markers",
                    "marker": {
                        "size": 10,
                    },
                    "error_y": {
                        "type": "data",
                        "symmetric": "false",
                        "array": [0, 0, 0],
                        "arrayminus": [0, minus_offset, 0],
                    },
                },
                {
                    "name": "Threshold",
                    "x": ["-inf", "ptp4l_max_offset", "inf"],
                    "y": [
                        defined_offset_threshold,
                        defined_offset_threshold,
                        defined_offset_threshold,
                    ],
                    "mode": "lines",
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "marker": {
                        "size": 15,
                    },
                    "type": "scatter",
                },
            ]
        }


def process_reboot(json_data: str, is_row: bool):
    max_minutes = 0.0
    avg_minutes = 0.0
    minus_max_minutes = 0.0
    minus_avg_minutes = 0.0
    defined_threshold = 20
    reboot_type = json_data["reboot_type"]
    for each_iteration in json_data["Iterations"]:
        max_minutes = max(max_minutes, each_iteration.get("total_minutes") or 0)
        avg_minutes += each_iteration.get("total_minutes") or 0
    avg_minutes /= max(len(json_data["Iterations"]), 1)
    if max_minutes > defined_threshold:
        minus_max_minutes = max_minutes - defined_threshold
    if avg_minutes > defined_threshold:
        minus_avg_minutes = avg_minutes - defined_threshold

    if is_row:
        return 1 if (minus_avg_minutes != 0 or minus_max_minutes != 0) else 0
    else:
        return {
            "reboot": [
                {
                    "name": "Data Points",
                    "x": [
                        reboot_type + "_" + "max_minutes",
                        reboot_type + "_" + "avg_minutes",
                    ],
                    "y": [max_minutes, avg_minutes],
                    "mode": "markers",
                    "marker": {
                        "size": 10,
                    },
                    "error_y": {
                        "type": "data",
                        "symmetric": "false",
                        "array": [0, 0],
                        "arrayminus": [minus_max_minutes, minus_avg_minutes],
                    },
                    "type": "scatter",
                },
                {
                    "name": "Threshold",
                    "x": [
                        reboot_type + "_" + "max_minutes",
                        reboot_type + "_" + "avg_minutes",
                    ],
                    "y": [defined_threshold, defined_threshold],
                    "mode": "lines",
                    "marker": {
                        "size": 15,
                    },
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "type": "scatter",
                },
            ]
        }


def process_cpu_util(json_data: str, is_row: bool):
    total_max_cpu = 0.0
    total_avg_cpu = 0.0
    minus_max_cpu = 0.0
    minus_avg_cpu = 0.0
    defined_threshold = 3.0
    for each_scenario in json_data["scenarios"]:
        if each_scenario["scenario_name"] == "steadyworkload":
            for each_type in each_scenario["types"]:
                if each_type["type_name"] == "total":
                    total_max_cpu = each_type.get("max_cpu") or 0
                    break
            total_avg_cpu = each_scenario.get("avg_cpu_total") or 0
            break
    if total_max_cpu > defined_threshold:
        minus_max_cpu = total_max_cpu - defined_threshold
    if total_avg_cpu > defined_threshold:
        minus_avg_cpu = total_avg_cpu - defined_threshold

    if is_row:
        return 1 if (minus_avg_cpu != 0 or minus_max_cpu != 0) else 0
    else:
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
                        "arrayminus": [minus_max_cpu, minus_avg_cpu],
                    },
                    "type": "scatter",
                },
                {
                    "name": "Threshold",
                    "x": ["total_max_cpu", "total_avg_cpu"],
                    "y": [defined_threshold, defined_threshold],
                    "mode": "lines",
                    "marker": {
                        "size": 15,
                    },
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "type": "scatter",
                },
            ]
        }


def process_rfc_2544(json_data: str, is_row: bool):
    max_delay = json_data.get("max_delay") or 0
    defined_delay_threshold = 30.0
    minus_max_delay = 0.0
    if max_delay > defined_delay_threshold:
        minus_max_delay = max_delay - defined_delay_threshold

    if is_row:
        return minus_max_delay
    else:
        return {
            "rfc-2544": [
                {
                    "x": ["-inf", "max_delay", "inf"],
                    "y": [0, max_delay, 0],
                    "mode": "markers",
                    "marker": {
                        "size": 10,
                    },
                    "name": "Data Points",
                    "error_y": {
                        "type": "data",
                        "symmetric": "false",
                        "array": [0, 0, 0],
                        "arrayminus": [0, minus_max_delay, 0],
                    },
                    "type": "scatter",
                },
                {
                    "x": ["-inf", "max_delay", "inf"],
                    "y": [
                        defined_delay_threshold,
                        defined_delay_threshold,
                        defined_delay_threshold,
                    ],
                    "name": "Threshold",
                    "mode": "lines",
                    "marker": {
                        "size": 15,
                    },
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "type": "scatter",
                },
            ]
        }


def process_oslat(json_data: str, is_row: bool):
    result = get_oslat_or_cyclictest(json_data, is_row)
    return result if is_row else {"oslat": result}


def process_cyclictest(json_data: str, is_row: bool):
    result = get_oslat_or_cyclictest(json_data, is_row)
    return result if is_row else {"cyclictest": result}


def process_deployment(json_data: str, is_row: bool):
    total_minutes = json_data.get("total_minutes") or 0
    reboot_count = json_data.get("reboot_count") or 0
    defined_total_minutes_threshold = 180
    defined_total_reboot_count = 3
    minus_total_minutes = 0.0
    minus_total_reboot_count = 0.0
    if total_minutes > defined_total_minutes_threshold:
        minus_total_minutes = total_minutes - defined_total_minutes_threshold
    if reboot_count > defined_total_reboot_count:
        minus_total_reboot_count = reboot_count - defined_total_reboot_count

    if is_row:
        return 1 if (minus_total_minutes != 0 or minus_total_reboot_count != 0) else 0
    else:
        return {
            "deployment": {
                "total_minutes": [
                    {
                        "name": "Data Points",
                        "x": ["-inf", "total_minutes", "inf"],
                        "y": [0, total_minutes, 0],
                        "mode": "markers",
                        "marker": {
                            "size": 10,
                        },
                        "error_y": {
                            "type": "data",
                            "symmetric": "false",
                            "array": [0, 0, 0],
                            "arrayminus": [0, minus_total_minutes, 0],
                        },
                        "type": "scatter",
                    },
                    {
                        "name": "Threshold",
                        "x": ["-inf", "total_minutes", "inf"],
                        "y": [
                            defined_total_minutes_threshold,
                            defined_total_minutes_threshold,
                            defined_total_minutes_threshold,
                        ],
                        "mode": "lines",
                        "marker": {
                            "size": 15,
                        },
                        "line": {
                            "dash": "dot",
                            "width": 3,
                        },
                        "type": "scatter",
                    },
                ],
                "total_reboot_count": [
                    {
                        "name": "Data Points",
                        "x": ["-inf", "reboot_count", "inf"],
                        "y": [0, reboot_count, 0],
                        "mode": "markers",
                        "marker": {
                            "size": 10,
                        },
                        "error_y": {
                            "type": "data",
                            "symmetric": "false",
                            "array": [0, 0, 0],
                            "arrayminus": [0, minus_total_reboot_count, 0],
                        },
                        "type": "scatter",
                    },
                    {
                        "name": "Threshold",
                        "x": ["-inf", "reboot_count", "inf"],
                        "y": [
                            defined_total_reboot_count,
                            defined_total_reboot_count,
                            defined_total_reboot_count,
                        ],
                        "mode": "lines",
                        "marker": {
                            "size": 15,
                        },
                        "line": {
                            "dash": "dot",
                            "width": 3,
                        },
                        "type": "scatter",
                    },
                ],
            }
        }


def get_oslat_or_cyclictest(json_data: str, is_row: bool):
    min_number_of_nines = 10000
    max_latency = 0
    minus_max_latency = 0
    defined_latency_threshold = 20
    defined_number_of_nines_threshold = 100
    for each_test_unit in json_data["test_units"]:
        max_latency = max(max_latency, each_test_unit.get("max_latency") or 0)
        min_number_of_nines = min(
            min_number_of_nines, each_test_unit.get("number_of_nines") or 0
        )
    if max_latency > defined_latency_threshold:
        minus_max_latency = max_latency - defined_latency_threshold

    if is_row:
        return (
            1
            if (
                (min_number_of_nines - defined_number_of_nines_threshold) != 0
                or minus_max_latency != 0
            )
            else 0
        )
    else:
        return {
            "number_of_nines": [
                {
                    "name": "Data Points",
                    "x": ["-inf", "min_number_of_nines", "inf"],
                    "y": [0, min_number_of_nines, 0],
                    "mode": "markers",
                    "marker": {
                        "size": 10,
                    },
                    "error_y": {
                        "type": "data",
                        "symmetric": "false",
                        "array": [0, 0, 0],
                        "arrayminus": [
                            0,
                            min_number_of_nines - defined_number_of_nines_threshold,
                            0,
                        ],
                    },
                    "type": "scatter",
                },
                {
                    "name": "Threshold",
                    "x": ["-inf", "min_number_of_nines", "inf"],
                    "y": [
                        defined_number_of_nines_threshold,
                        defined_number_of_nines_threshold,
                        defined_number_of_nines_threshold,
                    ],
                    "mode": "lines",
                    "marker": {
                        "size": 15,
                    },
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "type": "scatter",
                },
            ],
            "max_latency": [
                {
                    "name": "Data Points",
                    "x": ["-inf", "max_latency", "inf"],
                    "y": [0, max_latency, 0],
                    "mode": "markers",
                    "marker": {
                        "size": 10,
                    },
                    "error_y": {
                        "type": "data",
                        "symmetric": "false",
                        "array": [0, 0, 0],
                        "arrayminus": [0, minus_max_latency, 0],
                    },
                    "type": "scatter",
                },
                {
                    "name": "Threshold",
                    "x": ["-inf", "max_latency", "inf"],
                    "y": [
                        defined_latency_threshold,
                        defined_latency_threshold,
                        defined_latency_threshold,
                    ],
                    "mode": "lines",
                    "marker": {
                        "size": 15,
                    },
                    "line": {
                        "dash": "dot",
                        "width": 3,
                    },
                    "type": "scatter",
                },
            ],
        }
