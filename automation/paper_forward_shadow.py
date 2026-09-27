    started_at = _candle_record(ordered[0])["timestamp"]
    run_id = _fingerprint(
        {
            "candidate_fingerprint": candidate_fingerprint,
            "started_at_utc": started_at,
        }
    )
    state = _snapshot(
        candidate, parameters, ordered, run_id, candidate_fingerprint, started_at, "RUNNING"
    )
    state["candidate"] = candidate
    _atomic_write(path, state)
    return state


def update_session(
    state_path: str | Path,
    candles: Sequence[Candle],
    *,
    feed_receipt_fingerprint: str | None = None,
    feed_candle_fingerprint: str | None = None,
    feed_fetch_fingerprint: str | None = None,
) -> dict[str, Any]:
    _assert_safety()
    path = Path(state_path)
    state, candidate, parameters, existing = _read_session(path)
    if state.get("status") != "RUNNING":
        raise PaperForwardShadowError("Only a RUNNING session can be updated.")
    incoming = _validate_candles(candles, candidate["interval"])
    existing_records = [_candle_record(candle) for candle in existing]
    incoming_records = [_candle_record(candle) for candle in incoming]
    existing_by_timestamp = {record["timestamp"]: record for record in existing_records}

    new_candles: list[Candle] = []
    existing_first = _timestamp(existing[0].timestamp, "timestamp")
    existing_last = _timestamp(existing[-1].timestamp, "timestamp")
    interval = _INTERVALS[candidate["interval"]]

    for candle, record in zip(incoming, incoming_records):
        timestamp = _timestamp(candle.timestamp, "timestamp")
        if record["timestamp"] in existing_by_timestamp:
            if existing_by_timestamp[record["timestamp"]] != record:
                raise PaperForwardShadowError(
                    "Previously observed candle changed; historical input cannot be rewritten."
                )
            continue

        # The public market endpoint returns a window larger than our persisted
        # state. Candles strictly before the retained window are historical
        # context and cannot be appended to the state again.
        if timestamp <= existing_last:
            if timestamp < existing_first:
                continue
            raise PaperForwardShadowError(
                "Incoming candle falls inside the retained state but is missing from persisted history."
            )

        new_candles.append(candle)

    if new_candles:
        new_candles.sort(key=lambda item: item.timestamp)
        if _timestamp(new_candles[0].timestamp, "timestamp") - existing_last != interval:
            raise PaperForwardShadowError(
                "New data must append contiguously after the last candle."
            )
        _validate_candles((*existing[-1:], *new_candles), candidate["interval"])
        combined = (*existing, *new_candles)
    else:
        combined = existing

    updated = _snapshot(
        candidate,
        parameters,
        combined,
        state["run_id"],
        state["candidate_fingerprint"],
        state["started_at_utc"],
        "RUNNING",
        feed_receipt_fingerprint=(
            feed_receipt_fingerprint
            if feed_receipt_fingerprint is not None
            else state.get("feed_receipt_fingerprint")
        ),
        feed_candle_fingerprint=(
            feed_candle_fingerprint
            if feed_candle_fingerprint is not None
            else state.get("feed_candle_fingerprint")
        ),
        feed_fetch_fingerprint=(
            feed_fetch_fingerprint
            if feed_fetch_fingerprint is not None
            else state.get("feed_fetch_fingerprint")
        ),