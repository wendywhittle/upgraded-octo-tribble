# User Data and Privacy Boundary

## Purpose

The public application accepts information submitted directly by users through the deal-intake interface. This boundary governs that information independently of the analytical and human-authority boundaries.

The system is designed to support responsible handling of user-submitted information and applicable privacy, security, and data-governance obligations. Applicable legal requirements depend on jurisdiction, users, data categories, business model, and actual implementation.

## Core Principle

**USER SUBMISSION ≠ AUTHORIZATION**

Submission of information to the system does not authorize an investment, transaction, external action, movement of capital, brokerage activity, custody, representation of the user, communication on the user's behalf, or action over the user's assets or affairs.

The analytical processing of submitted information does not create authority to act.

## Information That May Be Submitted

Users may provide information including:

- property information
- deal information
- financial and underwriting assumptions
- business information
- company information
- contact information
- confidential or proprietary information

The system must distinguish, where practical, among:

1. information required for the stated analytical purpose
2. personal information
3. confidential or proprietary business information
4. financial or deal information
5. system-generated analytical information
6. institutional memory or derived learning

Information does not become verified merely because it was submitted.

## Data Minimization

The system should collect only information reasonably necessary for its stated product purpose.

Users should not be encouraged to submit highly sensitive information that the application does not require, including:

- passwords
- authentication secrets
- brokerage credentials
- banking credentials
- payment-card information
- Social Security numbers
- other sensitive identifiers

These items are not part of the current deal-intake form.

## Purpose Limitation

User-submitted information is collected for the application's stated analytical and underwriting purposes.

Submission does not establish unrestricted permission for unrelated secondary uses.

Any additional uses must be governed by applicable policy, user notice, contractual terms where applicable, and law.

## Security

User-submitted information should be protected through appropriate technical and organizational controls, including where applicable:

- access control
- least privilege
- secure transmission
- secure storage
- credential and secret separation
- auditability
- protection against unnecessary exposure
- security-incident handling

This document distinguishes architectural requirements from implemented controls. A requirement described here must not be represented as an implemented control unless the implementation has been verified.

## Retention and Disposal

Information should not be retained indefinitely without a legitimate purpose.

The system should distinguish among:

- operational data
- records retained for legitimate business or legal purposes
- analytical outputs
- institutional learning
- information subject to deletion or disposal

No retention period is established by this architectural boundary.

No deletion capability is implied unless separately implemented and verified.

## Third-Party Processing

Infrastructure and service providers may process or store submitted information as part of operating the application.

The architecture must not represent third-party infrastructure as unable to access submitted information unless that limitation has been technically established.

Specific vendor privacy or security commitments must not be inferred from this document.

## Privacy Notice

Public users should receive an appropriate privacy notice describing, as applicable:

- information collected
- purposes of collection
- processing and use
- storage
- retention
- applicable disclosures
- applicable user rights
- methods for submitting privacy requests

This architectural boundary is not itself a legal Privacy Policy.

## Confidential and Proprietary Information

Users may submit information that is confidential or proprietary.

The system must not assume that submitted information is public merely because it was entered into the application.

The architecture must not make unsupported promises of absolute confidentiality.

## Data Provenance

Where practical, information should be distinguishable by origin:

- **USER-SUBMITTED**
- **SYSTEM-GENERATED**
- **EXTERNALLY-SOURCED**
- **DERIVED / ANALYTICAL**

User assumptions must not silently become verified facts.

## Analytical and Authority Boundaries

The data-processing chain is:

**USER SUBMISSION → DATA PROCESSING → ANALYSIS**

The consequential-decision chain remains:

**ANALYSIS → RECOMMENDATION → AUTHORIZATION → EXECUTION**

These chains are separate.

In particular:

- submitted data is not an investment instruction
- an analytical result is not authorization
- readiness is not authorization
- authorization is not execution

The human remains the decision authority.

## Prohibited Autonomous Consequences

Nothing in this boundary authorizes:

- trading
- brokerage orders
- capital transfers
- asset transfers
- custody
- contract execution
- autonomous acquisition
- autonomous disposition
- autonomous communication as the user

Existing financial, trading, execution, and human-authority restrictions remain in force.

## Uncertainty and Data Quality

If the system cannot establish whether information is available, reliable, authorized for a particular use, or sufficiently complete, it should preserve the uncertainty rather than fabricate certainty.

Incomplete information remains incomplete.

## Governance and Incident Response

Material handling of user-submitted information should be observable and reconstructable where practical.

Security incidents involving submitted information should be handled through an established incident-response process appropriate to the system and applicable obligations.

This boundary does not itself define operational incident procedures.

## Implementation Status

This document establishes architectural requirements. It does not claim that every requirement is currently implemented.

Implementation status must be established from the actual application, infrastructure, configuration, and operational controls.

## Relationship to the Charter

This boundary operates under CHARTER.md and does not modify or supersede it.

Human authority, evidence integrity, uncertainty, least privilege, auditability, financial/trading restrictions, and the separation of analysis, recommendation, authorization, and execution remain governed by the Charter.
