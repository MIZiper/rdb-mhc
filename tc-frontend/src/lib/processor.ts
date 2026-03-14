export class BaseProcessor {
    constructor(public type: string) {}
}

class ProcessorRegistry {
    private processors = new Map<string, BaseProcessor>();

    register(processor: BaseProcessor) {
        this.processors.set(processor.type, processor);
    }

    getProcessor(type: string): BaseProcessor | null {
        return this.processors.get(type) || null;
    }
}

export const registry = new ProcessorRegistry();