import ctypes
import json
from typing import Callable

from utils import logger

GOLANG_ANALYSIS_LIBRARY = ctypes.cdll.LoadLibrary("/analysers/golang/main.so")
GOLANG_ANALYSER: Callable[[bytes, bytes], bytes] = GOLANG_ANALYSIS_LIBRARY.AnalyseCGOWrapper
GOLANG_ANALYSER.argtypes = [ctypes.c_char_p, ctypes.c_char_p]  # type: ignore
GOLANG_ANALYSER.restype = ctypes.c_void_p  # type: ignore


def analyse_golang(file_path: str, get_file_contents: Callable[[], str]) -> tuple[set[str], dict[str, dict]]:
    if not file_path.endswith(".go"):
        return (set(), {})

    response_json_ptr = GOLANG_ANALYSER(file_path.encode("utf-8"), get_file_contents().encode("utf-8"))
    loaded_response = json.loads(ctypes.string_at(response_json_ptr))

    if "error" in loaded_response:
        logger.critical(f"Golang static analysis failed on '{file_path}', error: {loaded_response['error']}")
        return set(), {}

    frameworks_identified = loaded_response["frameworks_identified"]
    openapi_specs = loaded_response["openapi_specs"]

    return set(frameworks_identified), openapi_specs
