"""
Pydantic V2 Schemas for Construction Contract Administration
Derived from Ontario MTO Daily Work Record (DWR) format.

These schemas enforce structured output from the LLM extraction layer.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date
from enum import Enum


# ============================================================
# Enums for controlled vocabularies
# ============================================================

class DocumentSource(str, Enum):
    CA = "CA"                # Contract Administrator (Inspector)
    CONTRACTOR = "Contractor"


class ReconciliationStatus(str, Enum):
    MATCH = "MATCH"          # Within 5% variance
    FLAG = "FLAG"            # Exceeds 5% variance
    NEW = "NEW"              # Present in one report only
    MISSING = "MISSING"      # Expected but absent


# ============================================================
# Layer 2: LLM Extraction Schemas
# ============================================================

class DWRHeader(BaseModel):
    """Metadata extracted from DWR header section"""
    contract_no: str = Field(..., description="Contract number e.g. 2020-4091")
    record_id: str = Field(..., description="DWR Record ID e.g. 2020-4091-DWR-7")
    contractor: str = Field(..., description="Contractor company name")
    created_by: str = Field(..., description="Person who created the DWR")
    dwr_date: str = Field(..., description="Work date in format DD-Mon-YY e.g. 05-Aug-21")
    from_time: str = Field(..., description="Start time in 24hr format e.g. 12:00")
    to_time: str = Field(..., description="End time in 24hr format e.g. 14:00")
    status: str = Field(default="Draft", description="DWR status: Draft, Reviewed, etc.")
    change_order: Optional[str] = Field(None, description="Linked Change Order e.g. 2020-4091-CO-21")
    highway: Optional[str] = Field(None, description="Highway number")
    region: Optional[str] = Field(None, description="Region name")


class WeatherRecord(BaseModel):
    """Weather conditions at time of work"""
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    wind_speed: Optional[str] = Field(None, description="Wind speed description")
    precipitation: Optional[str] = Field(None, description="Precipitation condition")
    visibility: Optional[str] = Field(None, description="Visibility condition")
    road_conditions: Optional[str] = Field(None, description="Road surface conditions")
    time: Optional[str] = Field(None, description="Time of weather observation")


class LabourLineItem(BaseModel):
    """Single labour entry from DWR"""
    classification: str = Field(..., min_length=1, description="Role: Foreman, Skilled Labourer, Driver/Teamster, Operator, etc.")
    number: int = Field(..., ge=0, description="Number of workers")
    hours_each: float = Field(..., ge=0, le=24, description="Hours worked per person")
    total_man_hours: float = Field(..., ge=0, description="Total = number x hours_each")
    reconciled_number: Optional[int] = Field(None, ge=0, description="Inspector-reconciled count")
    reconciled_hours: Optional[float] = Field(None, ge=0, description="Inspector-reconciled hours each")
    reconciled_man_hours: Optional[float] = Field(None, ge=0, description="Inspector-reconciled total")
    remarks: Optional[str] = Field(None, description="Worker names or notes")
    status: Optional[str] = Field(None, description="T&M, blank, etc.")

    @field_validator('total_man_hours')
    @classmethod
    def validate_total(cls, v, info):
        """Flag impossible totals but don't reject — LLM might extract as-is"""
        if v > 100:
            raise ValueError(f"Total man hours {v} exceeds reasonable maximum")
        return v


class EquipmentLineItem(BaseModel):
    """Single equipment entry from DWR"""
    equipment_name: str = Field(..., min_length=1, description="Equipment identifier e.g. '10 CAT 420 BACKHOE'")
    rented_or_owned: Optional[str] = Field(None, description="Rented or Owned")
    hours_worked: float = Field(..., ge=0, le=24, description="Hours equipment operated")
    hours_standby: Optional[float] = Field(0.0, ge=0, description="Standby hours")
    down_time: Optional[float] = Field(0.0, ge=0, description="Downtime hours")
    operator_included: Optional[bool] = Field(None, description="Operator included in equipment rate")
    remarks: Optional[str] = Field(None, description="Asset numbers, descriptions")
    reconciled_hours_worked: Optional[float] = Field(None, ge=0, description="Inspector-reconciled hours")
    reconciled_hours_standby: Optional[float] = Field(None, ge=0)
    reconciled_down_time: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None, description="T&M, blank, etc.")


class MaterialLineItem(BaseModel):
    """Single material entry from DWR"""
    material: str = Field(..., min_length=1, description="Material category")
    material_description: Optional[str] = Field(None, description="Detailed description")
    units: Optional[str] = Field(None, description="Unit of measure: EA, m, tonne, etc.")
    quantity: Optional[float] = Field(None, ge=0, description="Quantity used")
    new_or_used: Optional[str] = Field(None, description="New or Used")
    remarks: Optional[str] = Field(None)
    reconciled_quantity: Optional[float] = Field(None, ge=0)
    status: Optional[str] = Field(None)


class DWRComment(BaseModel):
    """Comment/description entry from DWR"""
    comment_text: str = Field(..., min_length=1, description="The comment or DWR description")
    user: Optional[str] = Field(None, description="Who wrote the comment")
    date: Optional[str] = Field(None, description="Date of comment")


class DWRReport(BaseModel):
    """Complete structured extraction from a single DWR PDF"""
    header: DWRHeader
    weather: Optional[WeatherRecord] = None
    labour: List[LabourLineItem] = Field(default_factory=list)
    equipment: List[EquipmentLineItem] = Field(default_factory=list)
    materials: List[MaterialLineItem] = Field(default_factory=list)
    comments: List[DWRComment] = Field(default_factory=list)


# ============================================================
# Layer 3: Reconciliation Schemas
# ============================================================

class ReconciliationLineItem(BaseModel):
    """Single line item comparison between CA and Contractor"""
    category: str = Field(..., description="Labour, Equipment, or Material")
    description: str = Field(..., description="Item description for matching")
    ca_value: Optional[float] = Field(None, description="CA (Inspector) reported value")
    contractor_value: Optional[float] = Field(None, description="Contractor reported value")
    unit: str = Field(default="hours", description="Unit of measure")
    variance_pct: Optional[float] = Field(None, description="Percentage difference")
    status: ReconciliationStatus = Field(..., description="MATCH, FLAG, NEW, or MISSING")
    notes: Optional[str] = Field(None, description="Explanation of discrepancy")


class ReconciliationReport(BaseModel):
    """Complete reconciliation between CA and Contractor DWRs"""
    change_order: str = Field(..., description="Change Order number")
    work_date: str = Field(..., description="Date of work")
    ca_record_id: str = Field(..., description="CA DWR Record ID")
    contractor_record_id: str = Field(..., description="Contractor DWR Record ID")
    ca_created_by: str
    contractor_created_by: str
    line_items: List[ReconciliationLineItem] = Field(default_factory=list)
    total_ca_labour_hours: float = 0.0
    total_contractor_labour_hours: float = 0.0
    total_ca_equipment_hours: float = 0.0
    total_contractor_equipment_hours: float = 0.0
    flags_count: int = 0
    matches_count: int = 0
    new_items_count: int = 0


# ============================================================
# Change Order Schema (for reference document extraction)
# ============================================================

class ChangeOrderSummary(BaseModel):
    """Extracted summary from Change Order PDF"""
    record_id: str = Field(..., description="e.g. 2020-4091-CO-1")
    title: str = Field(..., description="Change order title")
    contract_no: str
    category: Optional[str] = Field(None)
    change_order_type: Optional[str] = Field(None)
    basis_of_payment: Optional[str] = Field(None)
    description_of_work: str = Field(..., description="Full description")
    lumpsum_value: Optional[float] = Field(None, description="Dollar value")
    status: Optional[str] = Field(None, description="Approved, Draft, etc.")
    related_ir: Optional[str] = Field(None, description="Related IR number")
    created_by: Optional[str] = Field(None)
    created_date: Optional[str] = Field(None)


# ============================================================
# Information Request Schema
# ============================================================

class InformationRequestSummary(BaseModel):
    """Extracted summary from IR PDF"""
    record_id: str = Field(..., description="e.g. 2020-4091-IR-31")
    title: str
    contract_no: str
    reason: str = Field(..., description="Reason for the IR")
    details: str = Field(..., description="Description of the request")
    response: Optional[str] = Field(None, description="Official response if available")
    response_date: Optional[str] = Field(None)
    issued_by: Optional[str] = Field(None)
    status: Optional[str] = Field(None)
