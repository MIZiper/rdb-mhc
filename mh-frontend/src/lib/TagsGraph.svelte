<script lang="ts">
    import type { Tag } from '../schema';
    let canvas: HTMLCanvasElement;
    let { tags, selectedTag } : { tags: Tag[], selectedTag: Tag | null} = $props();
</script>

<div class="tags-graph">
    <canvas bind:this={canvas}></canvas>
</div>