import json
import pickle
import struct
import time

import pytest

from hades import Event, Process
from hades.core.hades import deserialize_event, serialize_event


def json_serialize_event(process: Process, event: Event, event_index: int) -> str:
    return json.dumps(
        {
            "target_process": process.process_name,
            "target_process_instance": process.instance_identifier,
            "event": event.name,
            "event_index": event_index,
        }
    )


def json_deserialize_event(serialized_event: str) -> tuple[str, int, str, int]:
    event_details = json.loads(serialized_event)
    return (
        event_details["target_process"],
        event_details["target_process_instance"],
        event_details["event"],
        event_details["event_index"],
    )


def split_serialization(process, event, event_index):
    return ",".join([process.process_name, str(process.instance_identifier), event.name, str(event_index)])


def split_deserialization(ev):
    a, b, c, d = ev.split(",")
    return a, b, c, int(d)


def pickle_serialization(process: Process, event: Event, event_index: int) -> bytes:
    return pickle.dumps(
        (
            process.process_name,
            process.instance_identifier,
            event.name,
            event_index,
        ),
        protocol=pickle.HIGHEST_PROTOCOL,
    )


def pickle_deserialization(serialized_event: bytes) -> tuple[str, int, str, int]:
    return pickle.loads(serialized_event)


def struct_serialize(process: Process, event: Event, event_index: int) -> bytes:
    process_name = process.process_name.encode("utf-8")
    instance_identifier = process.instance_identifier.encode("utf-8")
    event_name = event.name.encode("utf-8")

    packed_header = struct.pack("<IIII", len(process_name), len(instance_identifier), len(event_name), event_index)
    return packed_header + process_name + instance_identifier + event_name


def struct_deserialize(serialized_event: bytes) -> tuple[str, str, str, int]:
    process_name_len, instance_identifier_len, event_name_len, event_index = struct.unpack_from(
        "<IIII", serialized_event
    )

    offset = 16
    process_name = serialized_event[offset : offset + process_name_len].decode("utf-8")
    offset += process_name_len
    instance_identifier = serialized_event[offset : offset + instance_identifier_len].decode("utf-8")
    offset += instance_identifier_len
    event_name = serialized_event[offset : offset + event_name_len].decode("utf-8")

    return (
        process_name,
        instance_identifier,
        event_name,
        event_index,
    )


@pytest.mark.parametrize(
    "alternative_serialize, alternative_deserialize",
    (
        (struct_serialize, struct_deserialize),
        (split_serialization, split_deserialization),
        (pickle_serialization, pickle_deserialization),
        (json_serialize_event, json_deserialize_event),
    ),
)
def test_event_detail_serialization_performance_is_superior_to_considered_alternatives(
    alternative_serialize, alternative_deserialize
):
    event = Event(t=1)
    process = Process()

    total_time_actual = 0
    total_time_alternative = 0

    for _ in range(1_000_000):
        start_actual = time.time()
        serialized_event_actual = serialize_event(process, event, 1)
        deserialize_event_actual = deserialize_event(serialized_event_actual)
        end_actual = time.time()

        start_alternative = time.time()
        serialized_event_alternative = alternative_serialize(process, event, 1)
        deserialize_event_alternative = alternative_deserialize(serialized_event_alternative)
        end_alternative = time.time()

        total_time_actual += end_actual - start_actual
        total_time_alternative += end_alternative - start_alternative

        assert deserialize_event_actual == deserialize_event_alternative

    assert total_time_actual < total_time_alternative, (
        f"alternative {alternative_serialize}/{alternative_deserialize} gave {total_time_alternative}! better than"
        f" {total_time_actual}"
    )
