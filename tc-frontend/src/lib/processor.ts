import type { Component } from "svelte";

export interface EditorExports {
    getContent: () => Record<string, any>
}

export interface ViewerProps {
    content_in: Record<string, any>,
}

export class BaseProcessor {
    constructor(public type: string, public name: string, public viewer: Component<ViewerProps> | null, public editor: Component<{}, EditorExports> | null) { }
}

class ProcessorRegistry {
    private processors = new Map<string, BaseProcessor>();

    register(processor: BaseProcessor) {
        this.processors.set(processor.type, processor);
    }

    getProcessor(type: string): BaseProcessor | null {
        return this.processors.get(type) || null;
    }

    allProcessors(): Array<{ type: string; name: string }> {
        return Array.from(this.processors.values()).map((p) => ({
            type: p.type,
            name: p.name,
        }));
    }

    allEditors(): Array<{ type: string; name: string }> {
        return Array.from(this.processors.values()).filter((p) => p.editor).map((p) => ({
            type: p.type,
            name: p.name,
        }));
    }
}

export const registry = new ProcessorRegistry();