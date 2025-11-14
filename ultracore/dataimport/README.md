# Data Import/Export Module

## Overview
Complete Capsules architecture for data import/export with broker format support.

## Components

### Event Schemas (11 types)
- ImportJobCreatedEvent
- ImportJobValidationStartedEvent
- ImportJobValidationCompletedEvent
- ImportJobProcessingStartedEvent
- ImportJobRowProcessedEvent
- ImportJobCompletedEvent
- ImportJobFailedEvent
- ExportJobCreatedEvent
- ExportJobCompletedEvent
- ExportJobFailedEvent
- DataMappingCreatedEvent

### Aggregates
- **ImportJobAggregate** - Event-sourced import job
- **ExportJobAggregate** - Event-sourced export job

### Data Mesh
- **DataImportExportDataProduct** - Analytics and ASIC compliance

### AI Agent
- **ImportMapperAgent** - Automatic field mapping

### ML Model
- **DataQualityModel** - Data quality prediction

### MCP Tools
- start_import_job()
- get_import_status()
- export_portfolio_data()

## Usage

```python
from ultracore.dataimport.aggregates import ImportJobAggregate
from ultracore.dataimport.events import ImportJobCreatedEvent

# Create import job
job = ImportJobAggregate("import_001")
event = ImportJobCreatedEvent(...)
job.apply_event(event)
```
