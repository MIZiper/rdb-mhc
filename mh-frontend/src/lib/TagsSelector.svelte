<script lang="ts">
    import { onMount } from 'svelte';
    import type { Tag } from '../schema';
    
    export let width: number = 600;
    export let height: number = 400;
    
    let tags: Tag[] = $state([]);
    
    onMount(async () => {
        tags = await fetchTagsGraph();
    });
</script>