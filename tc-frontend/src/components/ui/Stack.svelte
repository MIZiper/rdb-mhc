<script lang="ts">
    import type { Snippet } from "svelte";

    let {
        gap = 2,
        class: className = "",
        children,
    }: {
        gap?: number;
        class?: string;
        children?: Snippet;
    } = $props();
</script>

<div class="d-flex flex-column gap-{gap} {className}">
    {@render children?.()}
</div>
