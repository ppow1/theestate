# Hardware Acquisition Record — Dell / Toshiba MG04ACA400NY 4 TB HDD

Status: Ordered  
Classification: Estate Internal  
Acquisition date: 2026-08-10  
Source: eBay  
Repository branch: main

## Item

- Product: Dell-branded Toshiba MG04ACA400NY enterprise-class hard disk drive
- Capacity: 4 TB
- Form factor: 3.5 inch
- Interface: SATA 6 Gb/s
- Rotation speed: 7,200 RPM
- Cache: 128 MB according to the listing
- Model: MG04ACA400NY
- Dell part number visible on label: 095M6K
- Condition: Used
- Quantity: 1
- Manufacture date visible on label: 2018-09-21

## Transaction

- Seller: crazy_about_dogs
- Seller feedback shown at capture: 100% positive
- eBay item number: 267750497890
- Listing URL: https://www.ebay.com/itm/267750497890
- Order date: 2026-08-10
- Actual order total: USD 50.00
- Shipping: Free FedEx Ground / FedEx Home Delivery
- Estimated delivery at capture: 2026-08-14 through 2026-08-21
- Returns shown as accepted through 2026-09-20

Note: the listing page later displayed USD 70.00, but the captured completed order shows the actual purchase total was USD 50.00.

## Seller / SMART Evidence at Purchase

The listing described the drive as `VERY GOOD, 100% HEALTH` and included a Hard Disk Sentinel screenshot for a Toshiba MG04ACA400NY showing:

- Health: 100%
- Performance: 100%
- Temperature: 30 C
- Power-on time: 1,965 days, 2 hours
- Total start/stop count: 52
- Reported status: no problematic/weak sectors and no spin-up or data-transfer errors

This is seller-provided pre-purchase evidence and must not be treated as Estate validation. Re-check SMART and surface condition after arrival before relying on the drive.

## Acquisition Purpose

Low-cost near-line / cold storage to create immediate capacity headroom for local AI work, especially model files, model variants, test artifacts, and other large assets that do not require NVMe-class latency.

The Estate was approaching the remaining capacity limit across current storage, and expected Grace/model testing will increase storage churn substantially. This 4 TB drive is intended as breathing room rather than a final storage architecture or NAS replacement.

Expected role after validation:

- cold/offload storage for AI models and model variants not currently active;
- archival copies of large local-AI assets that can be reloaded to faster storage when needed;
- non-latency-sensitive working archives and test artifacts;
- capacity relief for existing SSD/NVMe volumes.

Do not treat this single used HDD as the sole authoritative backup of irreplaceable Estate data.

## Validation Required on Arrival

Before putting the drive into service:

- Confirm model and serial identity against the physical label.
- Confirm SATA link negotiation and full 4 TB-class capacity.
- Read complete SMART data directly from the drive.
- Check reallocated, pending, uncorrectable, CRC, command-timeout, and other relevant SMART attributes.
- Record power-on hours and start/stop count from the drive itself and compare with seller evidence.
- Run a SMART short test.
- Run a SMART extended/long test before trusting the drive with cold-storage data.
- Perform a bounded full-surface read/write or equivalent destructive validation while the disk is still empty, if practical within the return window.
- Confirm sustained temperature under load and adequate chassis airflow.
- Record installed host, SATA port, drive letter/mount point, filesystem, and validation result in a follow-up asset record.

## Storage Policy Note

This acquisition is intended to relieve immediate capacity pressure. It does not replace the longer-term need for additional fast NVMe capacity and larger-capacity backup/archive storage.

Large AI models that are actively used should remain on faster storage where practical. This HDD is appropriate for models and artifacts that can tolerate being staged back to NVMe before active use.

## Evidence

Purchase/order details and listing information were supplied by the Steward on 2026-08-10. The seller supplied photographs of the drive label and a Hard Disk Sentinel health screenshot showing the drive as a Toshiba MG04ACA400NY with 100% reported health at the time of the listing.

Sensitive payment and delivery-address details from the order page were intentionally not copied into this repository record.
