<script lang="ts">
    import { acquireBlobUrl, releaseBlobUrl } from "../lib/imageStore";

    let {
        src,
        alt = "",
        className = "",
        style = "",
    }: {
        src: string;
        alt?: string;
        className?: string;
        style?: string;
    } = $props();

    let objectUrl: string | null = $state(null);
    let loading: boolean = $state(true);
    let error: boolean = $state(false);

    $effect(() => {
        const target = src;
        if (!target) {
            loading = false;
            return;
        }
        let active = true;
        let released = false;

        const release = () => {
            if (!released) {
                released = true;
                releaseBlobUrl(target);
            }
        };

        loading = true;
        error = false;
        objectUrl = null;

        acquireBlobUrl(target)
            .then((url) => {
                if (!active) {
                    release();
                    return;
                }
                objectUrl = url;
                loading = false;
            })
            .catch(() => {
                if (!active) {
                    release();
                    return;
                }
                error = true;
                loading = false;
                release();
            });

        return () => {
            active = false;
            release();
        };
    });
</script>

{#if objectUrl}
    <img src={objectUrl} {alt} class={className} {style} loading="lazy" />
{:else if error}
    <div class="placeholder {className}" {style} title={alt}>
        <span>图片加载失败</span>
    </div>
{:else if loading}
    <div class="placeholder {className}" {style}>
        <span class="spinner"></span>
    </div>
{/if}

<style>
    img {
        display: block;
        max-width: 100%;
    }
    .placeholder {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 60px;
        min-height: 60px;
        background: #f2f4f4;
        color: #aaa;
        font-size: 0.78em;
        border-radius: 4px;
    }
    .spinner {
        width: 18px;
        height: 18px;
        border: 2px solid #ddd;
        border-top-color: #49a9a7;
        border-radius: 50%;
        animation: spin 0.8s linear infinite;
    }
    @keyframes spin {
        to {
            transform: rotate(360deg);
        }
    }
</style>
