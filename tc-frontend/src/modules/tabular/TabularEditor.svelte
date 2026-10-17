<script lang="ts">
    import { Button, Table } from "@sveltestrap/sveltestrap";
    import Stack from "../../components/ui/Stack.svelte";
    import { untrack } from "svelte";
    import type { EditorProps } from "../registry";

    interface ChannelDef {
        name: string
        id_name: string
    }

    interface RowDef {
        id_idx: string
        time: number
    }

    interface RawRow {
        id_idx?: string | null
        time?: number | string | null
        value?: number | string | null
    }

    interface RawChannel {
        name?: string | null
        id_name?: string | null
        data?: RawRow[] | null
    }

    interface InitialState {
        rows: RowDef[]
        columns: ChannelDef[]
        values: (number | null)[][]
    }

    function toNumber(value: unknown): number | null {
        if (typeof value === "number") return Number.isFinite(value) ? value : null;
        if (typeof value === "string" && value.trim() !== "") {
            const parsed = Number(value);
            return Number.isFinite(parsed) ? parsed : null;
        }
        return null;
    }

    function idValue(value: unknown): string {
        if (typeof value === "string") return value.trim();
        if (typeof value === "number" && Number.isFinite(value)) return String(value);
        return "";
    }

    function rowKey(raw: RawRow, channelIndex: number, rowIndex: number): string {
        const id = idValue(raw?.id_idx);
        const time = toNumber(raw?.time);
        if (id) return time !== null ? `id:${id}:time:${time}` : `id:${id}`;
        if (time !== null) return `time:${time}`;
        return `idx:${channelIndex}:${rowIndex}`;
    }

    function loadInitial(initial: Record<string, any> | null | undefined): InitialState {
        const rawChannels: RawChannel[] = Array.isArray(initial?.channels)
            ? initial.channels
            : [];

        if (rawChannels.length === 0) {
            return {
                rows: [
                    { id_idx: "r0", time: 0 },
                    { id_idx: "r1", time: 1 },
                ],
                columns: [
                    { name: "Channel A", id_name: "channel_a" },
                    { name: "Channel B", id_name: "channel_b" },
                ],
                values: [
                    [null, null],
                    [null, null],
                ],
            };
        }

        const columns: ChannelDef[] = rawChannels.map((ch, i) => ({
            name: typeof ch?.name === "string" && ch.name ? ch.name : `Channel ${i + 1}`,
            id_name: typeof ch?.id_name === "string" ? ch.id_name : "",
        }));

        const rows: RowDef[] = [];
        const rowIndex = new Map<string, number>();

        rawChannels.forEach((ch, ci) => {
            const data: RawRow[] = Array.isArray(ch?.data) ? ch.data : [];
            data.forEach((raw, ri) => {
                const key = rowKey(raw, ci, ri);
                if (!rowIndex.has(key)) {
                    rowIndex.set(key, rows.length);
                    rows.push({
                        id_idx: idValue(raw?.id_idx),
                        time: toNumber(raw?.time) ?? 0,
                    });
                }
            });
        });

        if (rows.length === 0) {
            rows.push({ id_idx: "r0", time: 0 }, { id_idx: "r1", time: 1 });
        }

        const values: (number | null)[][] = columns.map(() =>
            Array(rows.length).fill(null),
        );

        rawChannels.forEach((ch, ci) => {
            const data: RawRow[] = Array.isArray(ch?.data) ? ch.data : [];
            data.forEach((raw, ri) => {
                const idx = rowIndex.get(rowKey(raw, ci, ri));
                if (idx !== undefined) {
                    values[ci][idx] = toNumber(raw?.value);
                }
            });
        });

        return { rows, columns, values };
    }

    let { initial }: EditorProps = $props();
    const initialState = loadInitial(untrack(() => initial));

    let rows: RowDef[] = $state(initialState.rows)
    let columns: ChannelDef[] = $state(initialState.columns)
    let values: (number | null)[][] = $state(initialState.values)

    $effect(() => {
        while (values.length < columns.length) {
            values = [...values, Array(rows.length).fill(null)]
        }
        while (values.length > columns.length) {
            values = values.slice(0, columns.length)
        }
        for (let i = 0; i < values.length; i++) {
            while (values[i].length < rows.length) {
                const newVals = [...values[i], null]
                values = values.map((col, ci) => ci === i ? newVals : col)
            }
            while (values[i].length > rows.length) {
                const newVals = values[i].slice(0, rows.length)
                values = values.map((col, ci) => ci === i ? newVals : col)
            }
        }
    })

    export function getContent() {
        const channels = columns.map((col, colIdx) => ({
            name: col.name,
            id_name: col.id_name || null,
            data: rows.map((row, rowIdx) => {
                return { id_idx: row.id_idx || null, time: row.time, value: values[colIdx]?.[rowIdx] ?? null }
            }).filter(d => d.value !== null),
        }))
        return { channels }
    }

    function addColumn() {
        columns = [...columns, { name: `Channel ${columns.length + 1}`, id_name: "" }]
    }

    function removeColumn(colIdx: number) {
        columns = columns.filter((_, i) => i !== colIdx)
        values = values.filter((_, i) => i !== colIdx)
    }

    function addRow() {
        const idx = rows.length
        rows = [...rows, { id_idx: `r${idx}`, time: 0 }]
    }

    function removeRow(rowIdx: number) {
        rows = rows.filter((_, i) => i !== rowIdx)
    }

    function updateRowField(rowIdx: number, field: "id_idx" | "time", val: string) {
        rows = rows.map((r, i) => {
            if (i !== rowIdx) return r
            if (field === "id_idx") return { ...r, id_idx: val }
            return { ...r, time: parseFloat(val) || 0 }
        })
    }

    function updateColumnField(colIdx: number, field: "name" | "id_name", val: string) {
        columns = columns.map((c, i) => {
            if (i !== colIdx) return c
            return { ...c, [field]: val }
        })
    }

    function updateValue(colIdx: number, rowIdx: number, valStr: string) {
        const num = valStr.trim() === "" ? null : parseFloat(valStr)
        values = values.map((col, ci) => {
            if (ci !== colIdx) return col
            const newCol = [...col]
            newCol[rowIdx] = isNaN(num as number) && num !== null ? col[rowIdx] : num
            return newCol
        })
    }

    function fmt(v: number | null): string {
        return v === null ? "" : String(v)
    }
</script>

<Stack gap={2}>
    <div class="d-flex gap-2">
        <Button size="sm" color="outline-secondary" onclick={addColumn}>+ Column (channel)</Button>
        <Button size="sm" color="outline-secondary" onclick={addRow}>+ Row</Button>
    </div>

    <Table bordered size="sm" responsive class="align-middle">
        <thead>
            <tr>
                <th>id_idx</th>
                <th>time</th>
                {#each columns as col, colIdx}
                    <th class="col-header">
                        <div class="d-flex flex-column gap-1">
                            <input
                                type="text"
                                value={col.name}
                                oninput={(e: Event) => updateColumnField(colIdx, "name", (e.target as HTMLInputElement).value)}
                                class="form-control form-control-sm name-input"
                            />
                            <input
                                type="text"
                                value={col.id_name}
                                oninput={(e: Event) => updateColumnField(colIdx, "id_name", (e.target as HTMLInputElement).value)}
                                placeholder="id_name"
                                class="form-control form-control-sm id-input"
                            />
                        </div>
                        {#if columns.length > 1}
                            <Button
                                size="sm"
                                color="link"
                                class="text-danger px-1 mt-1"
                                onclick={() => removeColumn(colIdx)}
                            >×</Button>
                        {/if}
                    </th>
                {/each}
                <th></th>
            </tr>
        </thead>
        <tbody>
            {#each rows as row, rowIdx}
                <tr>
                    <td class="bg-body-tertiary">
                        <input
                            type="text"
                            value={row.id_idx}
                            oninput={(e: Event) => updateRowField(rowIdx, "id_idx", (e.target as HTMLInputElement).value)}
                            class="form-control form-control-sm id-cell"
                        />
                    </td>
                    <td class="bg-body-tertiary">
                        <input
                            type="number"
                            value={row.time}
                            oninput={(e: Event) => updateRowField(rowIdx, "time", (e.target as HTMLInputElement).value)}
                            class="form-control form-control-sm time-cell"
                        />
                    </td>
                    {#each columns as _, colIdx}
                        <td>
                            <input
                                type="number"
                                value={fmt(values[colIdx]?.[rowIdx] ?? null)}
                                oninput={(e: Event) => updateValue(colIdx, rowIdx, (e.target as HTMLInputElement).value)}
                                class="form-control form-control-sm val-cell"
                                placeholder="null"
                            />
                        </td>
                    {/each}
                    <td class="p-0 text-center">
                        {#if rows.length > 1}
                            <Button
                                size="sm"
                                color="link"
                                class="text-danger px-1"
                                onclick={() => removeRow(rowIdx)}
                            >×</Button>
                        {/if}
                    </td>
                </tr>
            {/each}
        </tbody>
    </Table>
</Stack>

<style>
    .col-header {
        min-width: 100px;
    }
    .name-input,
    .id-input {
        width: 100px;
    }
    .id-cell {
        width: 80px;
    }
    .time-cell {
        width: 70px;
    }
    .val-cell {
        width: 80px;
    }
</style>
