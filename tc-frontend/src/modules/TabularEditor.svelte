<script lang="ts">
    interface ChannelDef {
        name: string
        id_name: string
    }

    interface RowDef {
        id_idx: string
        time: number
    }

    let rows: RowDef[] = $state([
        { id_idx: "r0", time: 0 },
        { id_idx: "r1", time: 1 },
    ])
    let columns: ChannelDef[] = $state([
        { name: "通道A", id_name: "channel_a" },
        { name: "通道B", id_name: "channel_b" },
    ])
    let values: (number | null)[][] = $state([
        [null, null],
        [null, null],
    ])

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
        columns = [...columns, { name: `通道${columns.length + 1}`, id_name: "" }]
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

<div id="main">
    <div class="meta-row">
        <button class="btn-sm" onclick={addColumn}>+ 列 (通道)</button>
        <button class="btn-sm" onclick={addRow}>+ 行</button>
    </div>

    <div class="table-wrap">
        <table>
            <thead>
                <tr>
                    <th class="row-header">id_idx</th>
                    <th class="row-header">time</th>
                    {#each columns as col, colIdx}
                        <th class="col-header">
                            <div class="col-name">
                                <input
                                    type="text"
                                    value={col.name}
                                    oninput={(e: Event) => updateColumnField(colIdx, "name", (e.target as HTMLInputElement).value)}
                                    class="th-input name-input"
                                />
                                <input
                                    type="text"
                                    value={col.id_name}
                                    oninput={(e: Event) => updateColumnField(colIdx, "id_name", (e.target as HTMLInputElement).value)}
                                    placeholder="id_name"
                                    class="th-input id-input"
                                />
                            </div>
                            {#if columns.length > 1}
                                <button class="btn-del-th" onclick={() => removeColumn(colIdx)}>×</button>
                            {/if}
                        </th>
                    {/each}
                    <th class="spacer"></th>
                </tr>
            </thead>
            <tbody>
                {#each rows as row, rowIdx}
                    <tr>
                        <td class="row-header-cell">
                            <input
                                type="text"
                                value={row.id_idx}
                                oninput={(e: Event) => updateRowField(rowIdx, "id_idx", (e.target as HTMLInputElement).value)}
                                class="cell-input id-cell"
                            />
                        </td>
                        <td class="row-header-cell">
                            <input
                                type="number"
                                value={row.time}
                                oninput={(e: Event) => updateRowField(rowIdx, "time", (e.target as HTMLInputElement).value)}
                                class="cell-input time-cell"
                            />
                        </td>
                        {#each columns as _, colIdx}
                            <td>
                                <input
                                    type="number"
                                    value={fmt(values[colIdx]?.[rowIdx] ?? null)}
                                    oninput={(e: Event) => updateValue(colIdx, rowIdx, (e.target as HTMLInputElement).value)}
                                    class="cell-input val-cell"
                                    placeholder="null"
                                />
                            </td>
                        {/each}
                        <td class="row-del">
                            {#if rows.length > 1}
                                <button class="btn-del" onclick={() => removeRow(rowIdx)}>×</button>
                            {/if}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>

<style>
    #main {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .meta-row {
        display: flex;
        gap: 8px;
    }
    .btn-sm {
        padding: 2px 10px;
        border: 1px solid #999;
        border-radius: 4px;
        background: #fff;
        cursor: pointer;
        font-size: 0.85em;
    }
    .table-wrap {
        overflow-x: auto;
    }
    table {
        border-collapse: collapse;
    }
    th, td {
        padding: 2px 4px;
        border: 1px solid #e0e0e0;
        white-space: nowrap;
    }
    th {
        background: #f7f7f8;
        vertical-align: top;
    }
    .row-header {
        min-width: 60px;
    }
    .col-header {
        min-width: 80px;
        position: relative;
    }
    .col-name {
        display: flex;
        flex-direction: column;
        gap: 2px;
    }
    .th-input {
        border: 1px solid #ddd;
        border-radius: 3px;
        padding: 1px 4px;
        font-size: 0.8em;
    }
    .name-input {
        width: 70px;
    }
    .id-input {
        width: 70px;
        font-size: 0.75em;
        opacity: 0.7;
    }
    .btn-del-th {
        border: none;
        background: none;
        color: #c00;
        cursor: pointer;
        font-weight: bold;
        font-size: 0.85em;
        padding: 0 2px;
        position: absolute;
        top: 0;
        right: 0;
    }
    .cell-input {
        border: 1px solid #eee;
        border-radius: 2px;
        padding: 2px 4px;
        font-size: 0.85em;
        width: 100%;
        box-sizing: border-box;
    }
    .id-cell {
        width: 70px;
    }
    .time-cell {
        width: 60px;
    }
    .val-cell {
        width: 70px;
    }
    .row-header-cell {
        background: #fafafa;
    }
    .row-del {
        padding: 0;
        width: 20px;
    }
    .btn-del {
        border: none;
        background: none;
        color: #c00;
        cursor: pointer;
        font-weight: bold;
        font-size: 1em;
        padding: 2px 4px;
    }
    .spacer {
        border: none;
        min-width: 0;
        width: 20px;
    }
</style>
