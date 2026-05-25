<script lang="ts">
    import type { ViewerProps } from "../lib/processor";

    interface DataRow {
        id_idx?: string | null
        time: number
        value: number
    }

    interface Channel {
        name: string
        id_name?: string | null
        data: DataRow[]
    }

    let { content_in }: ViewerProps = $props();

    let channels: Channel[] = $derived((content_in?.channels as Channel[]) || [])
    let selectedChannelIdx: number = $state(0)
    let sortField: "id_idx" | "time" | "value" | null = $state(null)
    let sortAsc: boolean = $state(true)

    let sortedData = $derived.by(() => {
        const ch = channels[selectedChannelIdx]
        if (!ch) return []
        const field = sortField
        if (!field) return ch.data
        const rows = [...ch.data]
        rows.sort((a, b) => {
            const va = a[field] ?? ""
            const vb = b[field] ?? ""
            if (va < vb) return sortAsc ? -1 : 1
            if (va > vb) return sortAsc ? 1 : -1
            return 0
        })
        return rows
    })

    function toggleSort(field: "id_idx" | "time" | "value") {
        if (sortField === field) {
            sortAsc = !sortAsc
        } else {
            sortField = field
            sortAsc = true
        }
    }

    function fmt(val: number): string {
        return Number.isFinite(val) ? val.toFixed(4).replace(/\.?0+$/, "") : String(val)
    }

    function sortIndicator(field: string): string {
        if (sortField !== field) return ""
        return sortAsc ? " ▲" : " ▼"
    }
</script>

{#if channels.length === 0}
    <p class="text-muted">无表格数据</p>
{:else}
    <div class="channel-tabs">
        {#each channels as ch, idx}
            <button class="tab" class:active={idx === selectedChannelIdx} onclick={() => { selectedChannelIdx = idx }}>
                {ch.name || `通道${idx + 1}`}
                {#if ch.id_name}
                    <span class="id-name">({ch.id_name})</span>
                {/if}
            </button>
        {/each}
    </div>

    {#if channels[selectedChannelIdx]}
        <table>
            <thead>
                <tr>
                    <th>#</th>
                    <th class="sortable" onclick={() => toggleSort("id_idx")}>id_idx{sortIndicator("id_idx")}</th>
                    <th class="sortable" onclick={() => toggleSort("time")}>time{sortIndicator("time")}</th>
                    <th class="sortable" onclick={() => toggleSort("value")}>value{sortIndicator("value")}</th>
                </tr>
            </thead>
            <tbody>
                {#each sortedData as row, rowIdx}
                    <tr>
                        <td class="row-num">{rowIdx}</td>
                        <td>{row.id_idx ?? ""}</td>
                        <td>{fmt(row.time)}</td>
                        <td class="val">{fmt(row.value)}</td>
                    </tr>
                {/each}
            </tbody>
        </table>
    {/if}
{/if}

<style>
    .channel-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-bottom: 8px;
    }
    .tab {
        padding: 4px 10px;
        border: 1px solid #ccc;
        border-radius: 4px;
        background: #f0f0f0;
        cursor: pointer;
        font-size: 0.9em;
    }
    .tab.active {
        background: #49a9a7;
        color: white;
        border-color: #49a9a7;
    }
    .id-name {
        font-size: 0.8em;
        opacity: 0.7;
    }
    table {
        border-collapse: collapse;
        width: 100%;
    }
    th, td {
        padding: 4px 8px;
        border: 1px solid #e0e0e0;
        text-align: left;
    }
    th {
        background: #f7f7f8;
        font-size: 0.85em;
    }
    th.sortable {
        cursor: pointer;
        user-select: none;
    }
    th.sortable:hover {
        background: #e8e8ea;
    }
    .row-num {
        color: #999;
        font-size: 0.8em;
        width: 30px;
    }
    .val {
        font-family: monospace;
    }
</style>
