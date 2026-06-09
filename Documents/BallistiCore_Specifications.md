# BallistiCore Firearms Register System - Functional Specifications

## Overview
BallistiCore is a comprehensive firearms register management system designed to track security guard firearms, ensure compliance with South African Police Service (SAPS) regulations, and prevent double-booking of firearms. The system supports dual permit delivery (print + WhatsApp) and maintains full audit trails.

## Core Requirements from Voice Notes

### 1. Permit Distribution Enhancement
**Current State:** Permits are printed on Epson printers
**Required Enhancement:** When permits are issued, they must also be sent via WhatsApp to CRT (Cash-in-Transit) vehicle cell phones

**Technical Requirements:**
- Integration with WhatsApp API or messaging service
- Automatic notification upon permit issuance
- CRT vehicle contact database integration

### 2. Firearms Register Management System

#### Purpose
- Track which security guard has which firearm
- Prevent double-booking of firearms (traditional paper registers allow this)
- Maintain auditable records for SAPS compliance

#### User Types
1. **Superusers (Admin Users)**
   - Can capture/manage security guards
   - Can also be security guards themselves
   - Full system access

2. **Security Guards**
   - End users who carry firearms
   - Limited access based on permissions

#### Database Structure

##### Firearms Section
- Serial numbers for all firearms
- Make, type, calibre information
- Firearm license numbers and issue dates

##### Superusers Section
- Admin user management
- System access controls

##### Security Guards Section
- **Personal Information:**
  - Name, surname
  - ID number
  - Cell phone number
  - Email address
  - Physical address
- **Firearm Permissions:**
  - Which firearms they are allowed to carry
  - Which firearms they are NOT allowed to carry
- **Location Assignment:** Guards can be assigned to specific locations
- **Soft Deletion:** When guards leave company, records are retained (not deleted) to allow reinstatement

#### Firearm Issuance Process
1. **Input Requirements:**
   - Which firearm is being issued
   - To which guard is receiving it

2. **Validation Logic:**
   - Check if guard is authorized to carry that firearm type
   - Verify firearm is available (not currently issued to another guard)

3. **Issuance Flow:**
   - If authorized and available: Issue firearm
   - If not authorized: Block issuance
   - If unavailable: Show "firearm with another guard" message

4. **Audit Trail:**
   - All issuances recorded in firearms register history
   - Information retained for SAPS auditing
   - Weekly/monthly reporting capabilities

#### Key Features
- **Availability Tracking:** Real-time status of all firearms
- **Permission Matrix:** Guard-to-firearm authorization mapping
- **Audit Compliance:** Full history for SAPS requirements
- **Soft Deletion:** Personnel records preserved for re-hiring
- **Location Management:** Guards assignable to specific sites

## Technical Architecture (Based on Excel Analysis)

### Worksheets/Modules
- **Main Menu:** Dashboard with activity counters and logs
- **Permit/Mini Permit:** Dual permit formats (full/condensed)
- **Register:** Current firearm assignments
- **Register History:** Complete audit trail
- **Guards:** Personnel database with permissions
- **Lists:** Firearm inventory management
- **Database:** Structured data for reporting
- **System Admin:** User/role management

### Integration Points
- WhatsApp API for permit notifications
- SAPS audit data export
- Printer integration (Epson)
- Cell phone database for CRT vehicles

### Security & Compliance
- Role-based access control
- Audit logging for all actions
- SAPS-compliant record retention
- Permission validation before firearm issuance

## Success Criteria
- Zero double-booked firearms
- Complete audit trail for SAPS inspections
- Efficient permit distribution with dual delivery
- Intuitive user interface for all user types
- Reliable WhatsApp notification system
- Comprehensive reporting capabilities