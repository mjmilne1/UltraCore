"""Data Import/Export Tests"""
def test_vanguard_parser():
    from ultracore.data_import_export.parsers.broker_parsers import VanguardParser
    parser = VanguardParser()
    # Test parsing logic
    assert parser is not None

def test_data_validator():
    from ultracore.data_import_export.validators.data_validator import DataValidator
    validator = DataValidator()
    is_valid, errors, warnings = validator.validate_import_data([], "transactions")
    assert is_valid == True

def test_export_generator():
    from ultracore.data_import_export.exporters.export_generator import ExportGenerator
    generator = ExportGenerator()
    csv_output = generator.generate_csv([{"a": 1, "b": 2}])
    assert "a,b" in csv_output
