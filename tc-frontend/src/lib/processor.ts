import type { Component } from "svelte";

export class BaseProcessor {
    constructor(public type: string, public name: string, public viewer: Component, public editor: Component) { }
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
}

export const registry = new ProcessorRegistry();