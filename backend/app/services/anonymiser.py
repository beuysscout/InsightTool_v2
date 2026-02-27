"""PII anonymisation service using Microsoft Presidio.

Runs locally before any LLM call. Detects PII in transcript turns
and replaces with standardised tokens.
"""

from __future__ import annotations

from app.models.session import AnonymisationLog, PiiDetection, Turn

# Presidio imports are deferred to handle missing spacy models gracefully
_analyzer = None
_anonymizer = None

# Map Presidio entity types to our replacement tokens
PII_TOKEN_MAP = {
    "PERSON": "[NAME]",
    "EMAIL_ADDRESS": "[EMAIL]",
    "PHONE_NUMBER": "[PHONE]",
    "LOCATION": "[LOCATION]",
    "ORGANIZATION": "[COMPANY]",  # mapped from ORG
    "ORG": "[COMPANY]",
}

# Entity types that are auto-redacted (high confidence)
AUTO_REDACT_TYPES = {"EMAIL_ADDRESS", "PHONE_NUMBER"}

# Confidence threshold for auto-redaction of other types
AUTO_REDACT_THRESHOLD = 0.85


def _get_analyzer():
    global _analyzer
    if _analyzer is None:
        from presidio_analyzer import AnalyzerEngine

        _analyzer = AnalyzerEngine()
    return _analyzer


def _get_anonymizer():
    global _anonymizer
    if _anonymizer is None:
        from presidio_anonymizer import AnonymizerEngine

        _anonymizer = AnonymizerEngine()
    return _anonymizer


def scan_turns_for_pii(
    turns: list[Turn],
    interviewer_name: str | None = None,
    participant_name: str | None = None,
) -> list[PiiDetection]:
    """Scan transcript turns for PII. Returns detections for review.

    Args:
        turns: List of parsed transcript turns.
        interviewer_name: If known, used to detect interviewer references.
        participant_name: If known, used to detect participant references.
    """
    analyzer = _get_analyzer()
    detections: list[PiiDetection] = []

    for turn in turns:
        results = analyzer.analyze(
            text=turn.text,
            language="en",
            entities=[
                "PERSON",
                "EMAIL_ADDRESS",
                "PHONE_NUMBER",
                "LOCATION",
                "ORGANIZATION",
            ],
        )

        for result in results:
            original = turn.text[result.start : result.end]
            entity_type = result.entity_type
            confidence = result.score

            # Determine replacement token
            if participant_name and original.lower() == participant_name.lower():
                token = "[PARTICIPANT]"
            elif interviewer_name and original.lower() == interviewer_name.lower():
                token = "[INTERVIEWER]"
            else:
                token = PII_TOKEN_MAP.get(entity_type, "[REDACTED]")

            # Auto-redact high-confidence items
            if (
                entity_type in AUTO_REDACT_TYPES
                or confidence >= AUTO_REDACT_THRESHOLD
            ):
                status = "redacted"
            else:
                status = "pending"

            detections.append(
                PiiDetection(
                    original_text=original,
                    replacement_token=token,
                    pii_type=entity_type,
                    confidence=confidence,
                    start_offset=result.start,
                    end_offset=result.end,
                    turn_index=turn.turn_index,
                    status=status,
                )
            )

    return detections


def apply_redactions(
    turns: list[Turn], detections: list[PiiDetection]
) -> tuple[list[Turn], AnonymisationLog]:
    """Apply confirmed redactions to transcript turns.

    Only applies detections with status 'redacted'.
    Returns new list of turns with PII replaced and an anonymisation log.
    """
    # Group detections by turn index
    by_turn: dict[int, list[PiiDetection]] = {}
    for d in detections:
        if d.status == "redacted":
            by_turn.setdefault(d.turn_index, []).append(d)

    auto_count = 0
    reviewed_count = 0
    excluded_count = 0

    anonymised_turns: list[Turn] = []
    for turn in turns:
        turn_detections = by_turn.get(turn.turn_index, [])
        if not turn_detections:
            anonymised_turns.append(turn.model_copy())
            continue

        # Sort detections by offset descending so replacements don't shift positions
        sorted_dets = sorted(turn_detections, key=lambda d: d.start_offset, reverse=True)
        text = turn.text
        for det in sorted_dets:
            text = text[: det.start_offset] + det.replacement_token + text[det.end_offset :]
            auto_count += 1

        anonymised_turns.append(
            turn.model_copy(update={"text": text})
        )

    for d in detections:
        if d.status == "kept":
            reviewed_count += 1
        elif d.status == "excluded":
            excluded_count += 1

    log = AnonymisationLog(
        auto_redacted=auto_count,
        researcher_reviewed=reviewed_count,
        exclusions=excluded_count,
        detections=detections,
    )

    return anonymised_turns, log
