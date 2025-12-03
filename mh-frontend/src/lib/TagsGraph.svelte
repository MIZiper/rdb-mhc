<script lang="ts">
    import { onMount } from "svelte";
    import type { Tag } from "../schema";
    import {
        forceSimulation,
        forceManyBody,
        forceCenter,
        forceLink,
    } from "d3-force";

    interface TagNode extends Tag {
        x: number;
        y: number;
        depth: number;
        weight: number;
        fx?: number | null;
        fy?: number | null;
        vy?: number;
    }
    type TagRelation = { source: TagNode; target: TagNode };

    let { tags, selectedTag }: { tags: Tag[]; selectedTag: Tag | null } =
        $props();
    let canvas: HTMLCanvasElement;
    let ctx: CanvasRenderingContext2D | null;
    let simulation: any;

    const nodeW = 100,
        nodeH = 40;
    const canvasWidth = 1000,
        canvasHeight = 600;

    let nodes: TagNode[] = [];
    let links: TagRelation[] = [];
    let dragging: TagNode | null = null;
    let dragOffset = { x: 0, y: 0 };
    // Pan/zoom state
    let transform = { x: 0, y: 0, k: 1 };
    let isPanning = false;
    let panStart = { x: 0, y: 0 };
    let lastTransform = { x: 0, y: 0 };
    // Ctrl / reparenting state
    let ctrlHeld = false;
    let isReparenting = false;

    function startSimulation() {
        if (simulation) simulation.stop();

        // Custom force to maintain vertical hierarchy
        const forceVertical = () => {
            return () => {
                nodes.forEach((node) => {
                    // Push nodes toward their hierarchical level
                    const targetY = 100 + node.depth * 150;
                    const dy = targetY - node.y;
                    node.vy = (node.vy || 0) + dy * 0.1;
                });
            };
        };

        simulation = forceSimulation(nodes)
            .force(
                "charge",
                forceManyBody().strength((n: TagNode) => -300 * n.weight),
            )
            .force("center", forceCenter(canvasWidth / 2, canvasHeight / 2))
            .force(
                "link",
                forceLink(links)
                    .distance(
                        (l: TagRelation) =>
                            100 +
                            50 * Math.min(l.source.weight, l.target.weight),
                    )
                    .strength(
                        (l: TagRelation) => 0.8 / Math.min(l.source.weight, l.target.weight),
                    ),
            )
            .force("vertical", forceVertical())
            .velocityDecay(0.6)
            .on("tick", () => {
                if (ctx) draw();
            });
    }

    function applyTransform() {
        if (!ctx) return;
        ctx.setTransform(
            transform.k,
            0,
            0,
            transform.k,
            transform.x,
            transform.y,
        );
    }

    function draw() {
        if (!ctx) return;

        ctx.save();
        ctx.setTransform(1, 0, 0, 1, 0, 0); // reset
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        applyTransform();

        // Draw parent-child lines with arrows
        links.forEach((link) => {
            const source = link.source;
            const target = link.target;
            if (source && target && ctx) {
                ctx.save();
                ctx.strokeStyle = "#888";
                ctx.lineWidth = 2;
                ctx.beginPath();
                ctx.moveTo(source.x, source.y);
                ctx.lineTo(target.x, target.y);
                ctx.stroke();

                // Draw arrowhead at the center of the line
                const dx = target.x - source.x;
                const dy = target.y - source.y;
                const angle = Math.atan2(dy, dx);
                const arrowSize = 12;

                // Find the midpoint between source and target
                const mx = source.x + dx / 2;
                const my = source.y + dy / 2;

                ctx.beginPath();
                ctx.moveTo(mx, my);
                ctx.lineTo(
                    mx - arrowSize * Math.cos(angle - Math.PI / 6),
                    my - arrowSize * Math.sin(angle - Math.PI / 6),
                );
                ctx.lineTo(
                    mx - arrowSize * Math.cos(angle + Math.PI / 6),
                    my - arrowSize * Math.sin(angle + Math.PI / 6),
                );
                ctx.closePath();
                ctx.fillStyle = "#888";
                ctx.fill();
                ctx.restore();
            }
        });

        // Draw tag nodes
        nodes.forEach((tag) => {
            if (!ctx) return;

            ctx.save();
            ctx.beginPath();
            ctx.rect(tag.x - nodeW / 2, tag.y - nodeH / 2, nodeW, nodeH);
            ctx.fillStyle = tag.exposed ? "#ffe4ef" : "#fff";
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = tag.exposed ? "#e91e63" : "#888";
            ctx.stroke();
            ctx.font = "16px sans-serif";
            ctx.fillStyle = "#222";
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            ctx.fillText(tag.name, tag.x, tag.y);
            ctx.restore();
        });

        ctx.restore();
    }

    function invertTransform(x: number, y: number) {
        // Convert screen coords to graph coords
        return {
            x: (x - transform.x) / transform.k,
            y: (y - transform.y) / transform.k,
        };
    }

    function handleKeyDown(e: KeyboardEvent) {
        if (e.key === "Control") {
            ctrlHeld = true;
            if (dragging && simulation) {
                // Pause simulation and enter reparenting mode
                simulation.stop();
                isReparenting = true;
            }
        }
    }

    function handleKeyUp(e: KeyboardEvent) {
        if (e.key === "Control") {
            ctrlHeld = false;
            // don't auto-resume simulation here; resume on mouseup or when leaving reparenting
            isReparenting = false;
        }
    }

    function getNodeAt(
        x: number,
        y: number,
        excludeNode: TagNode | null = null,
    ) {
        const pt = invertTransform(x, y);
        for (const tag of nodes) {
            if (tag === excludeNode) continue;
            if (
                pt.x >= tag.x - nodeW / 2 &&
                pt.x <= tag.x + nodeW / 2 &&
                pt.y >= tag.y - nodeH / 2 &&
                pt.y <= tag.y + nodeH / 2
            ) {
                return tag;
            }
        }
        return null;
    }

    function handleMouseDown(e: MouseEvent) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const node = getNodeAt(x, y);
        if (node) {
            dragging = node;
            const pt = invertTransform(x, y);
            dragOffset.x = pt.x - node.x;
            dragOffset.y = pt.y - node.y;
            // If Control is held when starting the drag, pause simulation and enter reparent mode.
            if (e.ctrlKey || ctrlHeld) {
                isReparenting = true;
                if (simulation) simulation.stop();
            } else {
                isReparenting = false;
                simulation.alphaTarget(0.3).restart();
            }
        } else {
            isPanning = true;
            panStart.x = x;
            panStart.y = y;
            lastTransform.x = transform.x;
            lastTransform.y = transform.y;
        }
    }

    function handleMouseMove(e: MouseEvent) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        if (dragging) {
            const pt = invertTransform(x, y);
            if (isReparenting) {
                // Move node directly while simulation is paused
                dragging.x = pt.x - dragOffset.x;
                dragging.y = pt.y - dragOffset.y;
                draw();
            } else {
                dragging.fx = pt.x - dragOffset.x;
                dragging.fy = pt.y - dragOffset.y;
                simulation.alphaTarget(0.3).restart();
            }
        } else if (isPanning) {
            transform.x = lastTransform.x + (x - panStart.x);
            transform.y = lastTransform.y + (y - panStart.y);
            draw();
        }
    }

    async function handleMouseUp(e: MouseEvent) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        if (dragging) {
            if (isReparenting) {
                // Check for a drop target other than the dragged node
                const target = getNodeAt(x, y, dragging);
                if (target && target !== dragging) {
                    // Update local parent_id and send patch to backend
                    dragging.parent_id = target.id;
                    try {
                        await fetch(`/api/tags/${dragging.id}`, {
                            method: "PATCH",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({ parent_id: target.id }),
                        });
                    } catch (err) {
                        console.error("Failed to update parent on server", err);
                    }
                    // Rebuild links from nodes' parent_id
                    links = nodes
                        .filter((c) => c.parent_id)
                        .map((c) => ({
                            source: nodes.find((n) => n.id === c.parent_id),
                            target: nodes.find((n) => n.id === c.id),
                        }));
                }
                // resume physics
                isReparenting = false;
                if (simulation) startSimulation();
            } else {
                dragging.fx = null;
                dragging.fy = null;
                simulation.alphaTarget(0);
            }
            dragging = null;
        }
        isPanning = false;
    }

    function handleWheel(e: WheelEvent) {
        e.preventDefault();
        const rect = canvas.getBoundingClientRect();
        const mouseX = e.clientX - rect.left;
        const mouseY = e.clientY - rect.top;
        const scale = Math.exp(-e.deltaY * 0.001);
        const { x: gx, y: gy } = invertTransform(mouseX, mouseY);

        transform.k *= scale;
        transform.x = mouseX - gx * transform.k;
        transform.y = mouseY - gy * transform.k;
        draw();
    }

    // Double click logic
    let lastClickTime = 0;
    async function handleClick(e: MouseEvent) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const node = getNodeAt(x, y);
        const now = Date.now();
        if (node && now - lastClickTime < 300) {
            node.exposed = !node.exposed;
            draw();
            await fetch(`/api/tags/${node.id}`, {
                method: "PATCH",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ exposed: node.exposed }),
            });
        }

        // selectedTag = node;
        lastClickTime = now;
    }

    $effect(() => {
        if (ctx && nodes.length) draw();

        // Calculate hierarchy depth for each node
        const getDepth = (node: any): number => {
            const parent = tags.find((c) => c.id === node.parent_id);
            return parent ? getDepth(parent) + 1 : 0;
        };

        nodes = tags.map((c) => ({
            ...c,
            x: canvasWidth / 2 + Math.random() * 100 - 50,
            y: canvasHeight / 2 + Math.random() * 100 - 50,
            depth: getDepth(c),
            weight: 1, // Will be set based on depth
        }));

        // Set weights based on depth (root nodes have highest weight)
        const maxDepth = Math.max(...nodes.map((n) => n.depth));
        nodes.forEach((node) => {
            node.weight = Math.pow(2, maxDepth - node.depth); // exponential weight decrease
        });

        links = tags
            .filter((c) => c.parent_id)
            .map((c) => ({
                source: nodes.find((n) => n.id === c.parent_id),
                target: nodes.find((n) => n.id === c.id),
            }));
        startSimulation();
    });

    onMount(() => {
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        ctx = canvas.getContext("2d");
        // Initial zoom out to fit more nodes
        transform = { x: 0, y: 0, k: 0.7 };
        draw();
        canvas.addEventListener("mousedown", handleMouseDown);
        window.addEventListener("mousemove", handleMouseMove);
        window.addEventListener("mouseup", handleMouseUp);
        window.addEventListener("keydown", handleKeyDown);
        window.addEventListener("keyup", handleKeyUp);
        canvas.addEventListener("click", handleClick);
        canvas.addEventListener("wheel", handleWheel, { passive: false });
        return () => {
            canvas.removeEventListener("mousedown", handleMouseDown);
            window.removeEventListener("mousemove", handleMouseMove);
            window.removeEventListener("mouseup", handleMouseUp);
            window.removeEventListener("keydown", handleKeyDown);
            window.removeEventListener("keyup", handleKeyUp);
            canvas.removeEventListener("click", handleClick);
            canvas.removeEventListener("wheel", handleWheel);
            if (simulation) simulation.stop();
        };
    });
</script>

<div class="tags-graph">
    <canvas bind:this={canvas}></canvas>
</div>

<style>
    canvas {
        border: 2px dashed gray;
    }
</style>
