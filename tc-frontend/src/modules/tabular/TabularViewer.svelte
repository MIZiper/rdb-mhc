<script lang="ts">
    import { Table } from "@sveltestrap/sveltestrap";
    import type { ViewerProps } from "../registry";

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

    let allIdIdxs: string[] = $derived.by(() => {
        const seen = new Set<string>()
        for (const ch of channels) {
            for (const row of ch.data) {
                if (row.id_idx) seen.add(row.id_idx)
            }
        }
        return [...seen].sort()
    })

    let idxTimeMap = $derived.by(() => {
        const m = new Map<string, number>()
        for (const ch of channels) {
            for (const row of ch.data) {
                if (row.id_idx && !m.has(row.id_idx)) {
                    m.set(row.id_idx, row.time)
                }
            }
        }
        return m
    })

    let channelValueMaps = $derived.by(() => {
        return channels.map(ch => {
            const m = new Map<string, number>()
            for (const row of ch.data) {
                if (row.id_idx) m.set(row.id_idx, row.value)
            }
            return m
        })
    })

    interface SortState {
        col: number  // -1=id_idx, -2=time, 0+=channel index
        asc: boolean
    }

    let sort: SortState = $state({ col: -1, asc: true })

    let visibleRows = $derived.by(() => {
        const rows = allIdIdxs.map(idIdx => {
            const vals = channelValueMaps.map((m, ci) => m.get(idIdx) ?? null)
            return { id_idx: idIdx, time: idxTimeMap.get(idIdx) ?? 0, values: vals }
        })

        if (sort.col < -1) return rows

        return [...rows].sort((a, b) => {
            let va: number | string, vb: number | string
            if (sort.col === -1) {
                va = a.id_idx; vb = b.id_idx
            } else if (sort.col === -2) {
                va = a.time; vb = b.time
            } else {
                va = a.values[sort.col] ?? (sort.asc ? Infinity : -Infinity)
                vb = b.values[sort.col] ?? (sort.asc ? Infinity : -Infinity)
            }
            if (va < vb) return sort.asc ? -1 : 1
            if (va > vb) return sort.asc ? 1 : -1
            return 0
        })
    })

    function setSort(col: number) {
        if (sort.col === col) {
            sort = { col, asc: !sort.asc }
        } else {
            sort = { col, asc: true }
        }
    }

    function sortIcon(col: number): string {
        if (sort.col !== col) return ""
        return sort.asc ? " ▲" : " ▼"
    }

    function fmt(n: number): string {
        return Number.isFinite(n) ? n.toFixed(4).replace(/\.?0+$/, "") : String(n)
    }
</script>

{#if channels.length === 0}
    <p class="text-muted">No table data</p>
{:else}
    <Table bordered hover size="sm" responsive class="small align-middle">
        <thead>
            <tr>
                <th class="sortable" onclick={() => setSort(-1)}>
                    id_idx{sortIcon(-1)}
                </th>
                <th class="sortable" onclick={() => setSort(-2)}>
                    time{sortIcon(-2)}
                </th>
                {#each channels as ch, ci}
                    <th class="sortable" onclick={() => setSort(ci)}>
                        <span>{ch.name}</span>
                        {#if ch.id_name}
                            <span class="small text-secondary">({ch.id_name})</span>
                        {/if}
                        {sortIcon(ci)}
                    </th>
                {/each}
            </tr>
        </thead>
        <tbody>
            {#each visibleRows as row}
                <tr>
                    <td class="small text-secondary">{row.id_idx}</td>
                    <td class="font-monospace">{fmt(row.time)}</td>
                    {#each row.values as val, _ci}
                        <td class="font-monospace">
                            {#if val !== null}
                                {fmt(val)}
                            {:else}
                                <span class="text-secondary fst-italic">—</span>
                            {/if}
                        </td>
                    {/each}
                </tr>
            {/each}
        </tbody>
    </Table>
{/if}

<style>
    .sortable {
        cursor: pointer;
        user-select: none;
    }
</style>
