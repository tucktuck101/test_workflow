from fastapi import HTTPException, status

ERROR_MAPPING = {
    "invalid_coordinates": (status.HTTP_400_BAD_REQUEST, "Invalid coordinates"),
    "duplicate_move": (status.HTTP_400_BAD_REQUEST, "Duplicate move"),
    "invalid_payload": (status.HTTP_400_BAD_REQUEST, "Invalid payload"),
    "game_not_found": (status.HTTP_404_NOT_FOUND, "Game not found"),
    "game_finished": (status.HTTP_409_CONFLICT, "Game already finished"),
    "capacity_exceeded": (status.HTTP_429_TOO_MANY_REQUESTS, "Capacity exceeded"),
    "rate_limited": (status.HTTP_429_TOO_MANY_REQUESTS, "Rate limited"),
    "model_not_ready": (status.HTTP_503_SERVICE_UNAVAILABLE, "Model not ready"),
    "no_available_moves": (status.HTTP_400_BAD_REQUEST, "No available moves"),
    "inference_failed": (status.HTTP_503_SERVICE_UNAVAILABLE, "Inference failed"),
}


def raise_http(error_code: str, details: dict | None = None, headers: dict | None = None) -> None:
    status_code, message = ERROR_MAPPING.get(
        error_code, (status.HTTP_400_BAD_REQUEST, "Invalid request")
    )
    raise HTTPException(
        status_code=status_code,
        detail={"error_code": error_code, "message": message, "details": details},
        headers=headers,
    )
