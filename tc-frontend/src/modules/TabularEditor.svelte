<script lang="ts">
    interface DataRow {
        id_idx: string
        time: number
        value: number
    }

    interface Channel {
        name: string
        id_name: string
        data: DataRow[]
    }

    let channels: Channel[] = $state([
        { name: "通道A", id_name: "channel_a", data: [{ id_idx: "r0", time: 0, value: 0 }] }
    ])

    let selectedChannelIdx: number = $state(0)

    export function getContent() {
        return {
            channels: channels.map(ch => ({
                name: ch.name,
                id_name: ch.id_name || null,
                data: ch.data.map(row => ({
                    id_idx: row.id_idx || null,
                    time: row.time,
                    value: row.value,
                })),
            })),
        }
    }

    function addChannel() {
        const idx = channels.length
        channels = [...channels, { name: `通道${idx + 1}`, id_name: "", data: [{ id_idx: "r0", time: 0, value: 0 }] }]
        selectedChannelIdx = channels.length - 1
    }

    function removeChannel(index: number) {
        channels = channels.filter((_, i) => i !== index)
        if (selectedChannelIdx >= channels.length) selectedChannelIdx = Math.max(0, channels.length - 1)
    }

    function addRow(chIdx: number) {
        channels = channels.map((ch, i) => {
            if (i !== chIdx) return ch
            const rowIdx = ch.data.length
            return { ...ch, data: [...ch.data, { id_idx: `r${rowIdx}`, time: 0, value: 0 }] }
        })
    }

    function removeRow(chIdx: number, rowIdx: number) {
        channels = channels.map((ch, i) => {
            if (i !== chIdx) return ch
            return { ...ch, data: ch.data.filter((_, j) => j !== rowIdx) }
        })
    }

    function updateChannelField(chIdx: number, field: "name" | "id_name", value: string) {
        channels = channels.map((ch, i) => {
            if (i !== chIdx) return ch
            return { ...ch, [field]: value }
        })
    }

    function updateRowField(chIdx: number, rowIdx: number, field: "id_idx" | "time" | "value", value: string) {
        channels = channels.map((ch, i) => {
            if (i !== chIdx) return ch
            const newData = ch.data.map((row, j) => {
                if (j !== rowIdx) return row
                const val = field === "id_idx" ? value : parseFloat(value) || 0
                return { ...row, [field]: val }
            })
            return { ...ch, data: newData }
        })
    }
</script>

<div id="main">
    <div class="channel-tabs">
        {#each channels as ch, idx}
            <div
                class="tab"
                class:active={idx === selectedChannelIdx}
                role="button"
                tabindex="0"
                onkeydown={(e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") selectedChannelIdx = idx }}
                onclick={() => { selectedChannelIdx = idx }}
            >
                {ch.name || `通道${idx + 1}`}
                {#if channels.length > 1}
                    <button class="tab-close-btn" onclick={(e: MouseEvent) => { e.stopPropagation(); removeChannel(idx) }}>×</button>
                {/if}
            </div>
        {/each}
        <button class="tab add-tab" onclick={addChannel}>+ 通道</button>
    </div>

    {#if channels[selectedChannelIdx]}
        {@const ch = channels[selectedChannelIdx]}
        <div class="channel-form">
            <label>名称 <input type="text" value={ch.name} oninput={(e: Event) => updateChannelField(selectedChannelIdx, "name", (e.target as HTMLInputElement).value)} /></label>
            <label>id_name <input type="text" value={ch.id_name} oninput={(e: Event) => updateChannelField(selectedChannelIdx, "id_name", (e.target as HTMLInputElement).value)} placeholder="跨item关联用，留空则用name匹配" /></label>
        </div>

        <table>
            <thead>
                <tr>
                    <th>id_idx</th>
                    <th>time</th>
                    <th>value</th>
                    <th></th>
                </tr>
            </thead>
            <tbody>
                {#each ch.data as row, rowIdx}
                    <tr>
                        <td><input type="text" value={row.id_idx} oninput={(e: Event) => updateRowField(selectedChannelIdx, rowIdx, "id_idx", (e.target as HTMLInputElement).value)} /></td>
                        <td><input type="number" value={row.time} oninput={(e: Event) => updateRowField(selectedChannelIdx, rowIdx, "time", (e.target as HTMLInputElement).value)} /></td>
                        <td><input type="number" value={row.value} oninput={(e: Event) => updateRowField(selectedChannelIdx, rowIdx, "value", (e.target as HTMLInputElement).value)} /></td>
                        <td>
                            {#if ch.data.length > 1}
                                <button class="btn-del" onclick={() => removeRow(selectedChannelIdx, rowIdx)}>×</button>
                            {/if}
                        </td>
                    </tr>
                {/each}
            </tbody>
        </table>
        <button class="btn-add-row" onclick={() => addRow(selectedChannelIdx)}>+ 行</button>
    {/if}
</div>

<style>
    #main {
        display: flex;
        flex-direction: column;
        gap: 8px;
    }
    .channel-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
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
    .tab.add-tab {
        background: transparent;
        border-style: dashed;
    }
    .tab-close-btn {
        margin-left: 6px;
        opacity: 0.6;
        border: none;
        background: none;
        cursor: pointer;
        padding: 0;
        font-weight: bold;
        font-size: 1em;
        color: inherit;
    }
    .tab-close-btn:hover {
        opacity: 1;
    }
    .channel-form {
        display: flex;
        gap: 12px;
    }
    .channel-form label {
        font-size: 0.85em;
        color: #555;
    }
    .channel-form input {
        display: block;
        margin-top: 2px;
        padding: 2px 6px;
        border: 1px solid #ccc;
        border-radius: 3px;
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
    td input {
        width: 80px;
        padding: 2px 4px;
        border: 1px solid #ddd;
        border-radius: 3px;
        font-size: 0.9em;
    }
    .btn-del {
        border: none;
        background: none;
        color: #c00;
        cursor: pointer;
        font-weight: bold;
        font-size: 1.1em;
    }
    .btn-add-row {
        align-self: flex-start;
        padding: 4px 12px;
        border: 1px dashed #999;
        border-radius: 4px;
        background: transparent;
        cursor: pointer;
        font-size: 0.85em;
    }
</style>
