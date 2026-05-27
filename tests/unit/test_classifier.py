# pyrefly: ignore [missing-import]
from src.core.classifier import DocumentClassifier

# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType


def test_classifier_invoice():
    classifier = DocumentClassifier()
    assert classifier.classify("Tax Invoice No 123") == DocumentType.INVOICE
    assert classifier.classify("FAKTURA VAT") == DocumentType.INVOICE


def test_classifier_receipt():
    classifier = DocumentClassifier()
    assert classifier.classify("PARAGON FISKALNY") == DocumentType.RECEIPT
    assert classifier.classify("KASA FISKALNA") == DocumentType.RECEIPT


def test_classifier_form():
    classifier = DocumentClassifier()
    assert classifier.classify("Application Form 2024") == DocumentType.FORM
    assert classifier.classify("Wniosek o urlop") == DocumentType.FORM


def test_classifier_unknown():
    classifier = DocumentClassifier()
    assert classifier.classify("Random text without markers") == DocumentType.UNKNOWN
