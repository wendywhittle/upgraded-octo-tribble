from datetime import datetime, timedelta, timezone
import pytest
from pydantic import ValidationError
from app.cre_evidence import CREEvidenceProvenance, build_cre_evidence, validate_cre_evidence
NOW=datetime(2026,9,11,15,0,tzinfo=timezone.utc)
def p(): return CREEvidenceProvenance(source="source",source_type="external_source",source_reference="SRC",observed_at=NOW-timedelta(minutes=5),effective_at=NOW-timedelta(minutes=5),retrieved_at=NOW-timedelta(minutes=2),point_in_time=True)
def test_boundary():
 x=build_cre_evidence(evidence_id="E",opportunity_id="O",category="listing",field_name="occupancy",observed_value=.94,source_content="94%",provenance=p(),created_at=NOW); assert x.opportunity_id=="O"; assert x.investment_authority=="none"
def test_invalid_time():
 with pytest.raises(ValidationError): build_cre_evidence(evidence_id="E",opportunity_id="O",category="listing",field_name="x",provenance=CREEvidenceProvenance(source="s",observed_at=NOW,retrieved_at=NOW-timedelta(minutes=1)),created_at=NOW)
def test_validation_adapter(): assert validate_cre_evidence(build_cre_evidence(evidence_id="E",opportunity_id="O",category="listing",field_name="x",observed_value=1,provenance=p(),created_at=NOW),now=NOW)["decision_usable"]
