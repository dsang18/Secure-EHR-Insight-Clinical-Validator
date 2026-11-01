from presidio_analyzer import (
    AnalyzerEngine,
    PatternRecognizer,
    Pattern,
)

from presidio_anonymizer import AnonymizerEngine


class ClinicalPIIRedactor:

    def __init__(self):

        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()

        # Additional SSN detection.
        ssn_pattern = Pattern(
            name="custom_ssn",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.95,
        )

        ssn_recognizer = PatternRecognizer(
            supported_entity="US_SSN",
            patterns=[ssn_pattern],
        )

        self.analyzer.registry.add_recognizer(
            ssn_recognizer
        )

        # Hospital-specific recognition.
        hospital_recognizer = PatternRecognizer(
            supported_entity="ORGANIZATION",
            deny_list=[
                "Massachusetts General Hospital",
                "Mayo Clinic",
                "Cleveland Clinic",
            ],
            deny_list_score=0.95,
        )

        self.analyzer.registry.add_recognizer(
            hospital_recognizer
        )

        self.target_entities = [
            "PERSON",
            "PHONE_NUMBER",
            "EMAIL_ADDRESS",
            "US_SSN",
            "LOCATION",
            "ORGANIZATION",
            "DATE_TIME",
            "IP_ADDRESS",
            "URL",
        ]

    def redact_clinical_context(self,raw_text: str,) -> str:

        if not raw_text:
            return ""

        try:

            results = self.analyzer.analyze(
                text=raw_text,
                entities=self.target_entities,
                language="en",
                score_threshold=0.35,
            )

            anonymized = self.anonymizer.anonymize(
                text=raw_text,
                analyzer_results=results,
            )

            return anonymized.text

        except Exception as exc:
            # Never return unredacted content after a failure.
            raise RuntimeError(
                "Clinical data redaction failed."
            ) from exc