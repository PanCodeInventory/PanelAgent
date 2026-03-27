import csv
import shutil

import pytest


@pytest.mark.asyncio
async def test_diagnose_panels_reports_conflict_group(client, impossible_case, project_root, tmp_path):
    inventory_file = tmp_path / "impossible_inventory.csv"

    with open(inventory_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["Target", "Fluorescein", "Clone", "Brand", "Catalog Number"],
        )
        writer.writeheader()
        for marker in impossible_case["markers"]:
            antibody = impossible_case["antibodies_by_marker"][marker][0]
            writer.writerow(
                {
                    "Target": marker,
                    "Fluorescein": antibody["fluorochrome"],
                    "Clone": antibody["clone"],
                    "Brand": antibody["brand"],
                    "Catalog Number": antibody["catalog_number"],
                }
            )

    inventory_dir = project_root / "inventory"
    inventory_dir.mkdir(exist_ok=True)
    target_inventory = inventory_dir / inventory_file.name
    shutil.copyfile(inventory_file, target_inventory)

    resp = await client.post(
        "/api/v1/panels/diagnose",
        json={
            "markers": impossible_case["markers"],
            "inventory_file": inventory_file.name,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "success"
    assert isinstance(body["diagnosis"], str)
    assert body["diagnosis"]
    assert "冲突组" in body["diagnosis"]
    assert impossible_case["shared_channel"] in body["diagnosis"]
    for marker in impossible_case["markers"]:
        assert marker in body["diagnosis"]
