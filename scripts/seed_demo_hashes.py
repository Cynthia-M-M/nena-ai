"""Re-key synthetic seed patient and device identifiers in Supabase using the local APP_HMAC_SECRET."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import db
from app.core.security import keyed_hash


async def main():
    print("Re-keying synthetic seed patient references and device fingerprints...")
    await db.patch("patient_tokens", {"id": "eq.60000000-0000-4000-8000-000000000001"},
                   {"patient_ref_hash": keyed_hash("DEMO-PATIENT-001", "patient-reference")})
    await db.patch("patient_tokens", {"id": "eq.60000000-0000-4000-8000-000000000002"},
                   {"patient_ref_hash": keyed_hash("DEMO-PATIENT-002", "patient-reference")})
    await db.patch("patient_tokens", {"id": "eq.60000000-0000-4000-8000-000000000003"},
                   {"patient_ref_hash": keyed_hash("DEMO-PATIENT-EXPIRED", "patient-reference")})

    await db.patch("registered_devices", {"id": "eq.50000000-0000-4000-8000-000000000001"},
                   {"device_fingerprint_hash": keyed_hash("DEMO-DEVICE-FINGERPRINT-001", "device-fingerprint")})
    await db.patch("registered_devices", {"id": "eq.50000000-0000-4000-8000-000000000002"},
                   {"device_fingerprint_hash": keyed_hash("DEMO-DEVICE-FINGERPRINT-002", "device-fingerprint")})

    await db.close()
    print("Successfully synchronized demo hashes with local APP_HMAC_SECRET.")


if __name__ == "__main__":
    asyncio.run(main())
