"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/Badge";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { Tabs } from "@/components/ui/Tabs";

import type { DatasetTable } from "../types";
import { DataTable } from "./DataTable";

/** Left-panel reference data: the candidate sees ALL rows of every table, since
 *  the problems require joining across them (so it can't be hand-computed). */
export function DatasetTables({ datasets }: { datasets: DatasetTable[] }) {
  const [active, setActive] = useState(datasets[0]?.name ?? "");
  const table = datasets.find((d) => d.name === active) ?? datasets[0];
  if (!table) return null;

  return (
    <div>
      <div className="flex items-center justify-between">
        <SectionLabel>데이터셋</SectionLabel>
        <Badge tone="neutral">{table.rows.length.toLocaleString()} 행</Badge>
      </div>
      <Tabs
        className="mt-2"
        active={active}
        onChange={setActive}
        tabs={datasets.map((d) => ({ id: d.name, label: d.name }))}
      />
      <div className="mt-2">
        <DataTable columns={table.columns} rows={table.rows} maxHeightClass="max-h-80" />
      </div>
    </div>
  );
}
